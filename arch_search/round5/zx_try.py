import sys, math, pyzx as zx
sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..'))
from grader import qasm_metrics
from qiskit import QuantumCircuit, transpile
from qiskit import qasm2
src=open('/home/user/classiq-codex/best_verified_depth176_cx421.qasm').read()
qc=QuantumCircuit.from_qasm_str(src)
# pyzx cannot parse u3 directly: decompose into rz/rx/cx via qiskit basis
qb=transpile(qc,basis_gates=['rz','sx','x','cx','h'],optimization_level=0)
s=qasm2.dumps(qb)
c=zx.Circuit.from_qasm(s)
print('pyzx in: gates',len(c.gates),'2q',c.twoqubitcount())
res={}
for mode in ('full','teleport'):
    g=c.to_graph()
    if mode=='full':
        zx.full_reduce(g); c2=zx.extract_circuit(g.copy()).to_basic_gates()
    else:
        c2=zx.teleport_reduce(g) if hasattr(zx,'teleport_reduce') else None
        c2=zx.Circuit.from_graph(c2) if c2 is not None else None
    if c2 is None: continue
    c2=zx.basic_optimization(c2.split_phase_gates() if hasattr(c2,'split_phase_gates') else c2)
    q=QuantumCircuit.from_qasm_str(c2.to_qasm())
    for opt in (1,3):
        t=transpile(q,basis_gates=['u3','cx'],optimization_level=opt,seed_transpiler=42)
        m=qasm_metrics(qasm2.dumps(t)); print(mode,'opt',opt,'metrics (w,d,cx)',m,flush=True)
