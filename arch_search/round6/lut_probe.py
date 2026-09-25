import sys, numpy as np
sys.path.insert(0, '/home/user/classiq-codex/arch_search')
import classiq
from classiq import *
from classiq.interface.generator.hardware.hardware_data import CustomHardwareSettings
from grader import qasm_metrics
d = np.load('ferrers.npz'); lev = d['lev']
# y-side level code (numeric map 1..5 -> 0..4 ; empty -> 6)
LY = [int(min(l - 1, 6)) if l != 7 else 6 for l in lev]
@qfunc
def main(x: Output[QNum[6]], y: Output[QNum[6]]) -> None:
    allocate(x); allocate(y)
    hadamard_transform(x); hadamard_transform(y)
    cy = QNum('cy')
    within_apply(lambda: assign(subscript(LY, y), cy),
                 lambda: phase(cy, 0.3))
for w in (18, 24):
    try:
        qp = synthesize(create_model(main, constraints=Constraints(optimization_parameter='depth', max_width=w),
                                     preferences=Preferences(random_seed=1, timeout_seconds=300)))
        tr = classiq.transpile(qp, preferences=Preferences(transpilation_option=TranspilationOption.AUTO_OPTIMIZE,
                               custom_hardware_settings=CustomHardwareSettings(basis_gates=['u3', 'cx'])))
        q = export(tr, TargetLanguage.QASM2, transpilation_config=TranspilationConfig(basis_gates=['u3', 'cx']))
        print('max_width', w, 'metrics (incl. 12 H)', qasm_metrics(q), flush=True)
    except Exception as e:
        print('max_width', w, 'ERROR', str(e)[:300], flush=True)
