"""Re-transpile an existing u3/cx QASM through Classiq's transpiler at several optimization levels."""
import sys, json
sys.path.insert(0, '/home/user/classiq-codex/arch_search')
import classiq
from classiq import *
from classiq.interface.generator.hardware.hardware_data import CustomHardwareSettings
from grader import qasm_metrics
from sparse_verify import verify
src = open(sys.argv[1]).read(); tag = sys.argv[2]
print('input', qasm_metrics(src), flush=True)
qp = quantum_program_from_qasm(src)
for name in sys.argv[3:]:
    opt = getattr(TranspilationOption, name)
    try:
        tr = classiq.transpile(qp, preferences=Preferences(transpilation_option=opt,
                 custom_hardware_settings=CustomHardwareSettings(basis_gates=['u3', 'cx'])))
        q = export(tr, TargetLanguage.QASM2, transpilation_config=TranspilationConfig(basis_gates=['u3', 'cx']))
        m = qasm_metrics(q); v = verify(q)
        print(name, m, v['passed'], v['max_phase_err'], flush=True)
        open(f'{tag}_{name}.qasm', 'w').write(q)
    except Exception as e:
        print(name, 'ERROR', str(e)[:300], flush=True)
