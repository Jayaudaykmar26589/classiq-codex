"""Synthesize each Qmod model on Classiq over several random seeds, score and verify, keep the best.

Needs the Classiq SDK 1.29.1 and an authenticated session (run classiq.authenticate() once).
Follows the baseline notebook's steps exactly:
  synthesize (depth, max_width 18) -> export QASM2 -> drop the two harness hadamard_transform calls
  -> transpile (AUTO_OPTIMIZE, basis u3/cx) -> metrics -> export QASM2 -> exact 4096-input check.

Usage:  python synth_sweep.py [model ...] [--seeds N] [--timeout S] [--transpile auto|intensive|custom] [--out DIR]
Results go to <out>/<model>_seed<k>.qasm plus <out>/summary.json (default out: sweep_results/).
"""
import argparse, json, re, sys
from pathlib import Path
import classiq
from classiq import *
from classiq.interface.generator.hardware.hardware_data import CustomHardwareSettings

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / 'arch_search'))
from grader import qasm_metrics        # same metric as the notebook
from sparse_verify import verify       # exact all-4096 phase/cleanliness check
import build_models as bm
ORACLES = {'staircase_two_lut': bm.staircase_two_lut, 'staircase_or_lut': bm.staircase_or_lut,
           'xor_rectangles': bm.xor_rectangles_oracle}

TRANSPILE = {'auto': TranspilationOption.AUTO_OPTIMIZE, 'intensive': TranspilationOption.INTENSIVE,
             'custom': TranspilationOption.CUSTOM}

def strip_harness(raw_qasm):
    lines = raw_qasm.splitlines()
    idx = {i for i, l in enumerate(lines) if l.lstrip().startswith('hadamard_transform_') and 'q[' in l}
    if len(idx) != 2:
        raise RuntimeError(f'expected exactly two harness hadamard_transform calls, found {len(idx)}')
    return '\n'.join(l for i, l in enumerate(lines) if i not in idx)

def build(name, seed, timeout):
    return create_model(bm.harness(ORACLES[name]),
                        constraints=Constraints(optimization_parameter='depth', max_width=18),
                        preferences=Preferences(random_seed=seed, timeout_seconds=timeout))

def run(name, seed, timeout, topt):
    qprog = synthesize(build(name, seed, timeout))
    cand = quantum_program_from_qasm(strip_harness(export(qprog, TargetLanguage.QASM2)))
    tr = classiq.transpile(cand, preferences=Preferences(
        transpilation_option=TRANSPILE[topt], custom_hardware_settings=CustomHardwareSettings(basis_gates=['u3', 'cx'])))
    qasm = export(tr, TargetLanguage.QASM2, transpilation_config=TranspilationConfig(basis_gates=['u3', 'cx']))
    w, d, cx = qasm_metrics(qasm)
    v = verify(qasm)
    return qasm, {'width': w, 'depth': d, 'cx': cx, 'passed': v['passed'], 'max_phase_err': v['max_phase_err'], 'max_leak': v['max_leak']}

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('models', nargs='*', default=['staircase_two_lut', 'staircase_or_lut', 'xor_rectangles'])
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--timeout', type=int, default=600)
    ap.add_argument('--transpile', default='auto', choices=list(TRANSPILE))
    ap.add_argument('--out', default=str(HERE / 'sweep_results'))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    summary = []
    for m in a.models:
        for seed in range(1, a.seeds + 1):
            try:
                qasm, r = run(m, seed, a.timeout, a.transpile)
            except Exception as e:                      # keep sweeping on synthesis errors
                print(m, seed, 'ERROR', e); continue
            (out / f'{m}_seed{seed}.qasm').write_text(qasm)
            r.update(model=m, seed=seed); summary.append(r); print(r, flush=True)
    ok = sorted((r for r in summary if r['passed']), key=lambda r: (r['depth'], r['cx']))
    (out / 'summary.json').write_text(json.dumps(summary, indent=1))
    print('BEST (verified):', ok[0] if ok else None)
