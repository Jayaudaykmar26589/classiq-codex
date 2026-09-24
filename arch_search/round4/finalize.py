"""Reschedule a modified gate list with the exact SAT scheduler, emit QASM/QMOD, score and verify."""
import sys, json
sys.path.insert(0, __import__('os').path.dirname(__file__))
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__file__), '..'))
from dag import kind
from rewrite import solve
from grader import qasm_metrics
from sparse_verify import verify

def normalize(G):
    """recompute u3 kinds from parameters (commutation depends on them)"""
    out = []
    for g in G:
        if g[0] == 'u3': out.append(('u3', g[1], kind(g[3]), tuple(g[3])))
        else: out.append(g)
    return out

def emit_qasm(G):
    s = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[18];\n'
    for g in G:
        if g[0] == 'cx': s += f'cx q[{g[1]}],q[{g[2]}];\n'
        else: s += 'u3(%r,%r,%r) q[%d];\n' % (float(g[3][0]), float(g[3][1]), float(g[3][2]), g[1])
    return s

def emit_qmod(G):
    s = 'qfunc logo_phase_oracle(q: qbit[18]) {\n'
    for g in G:
        if g[0] == 'cx': s += f'  CX(q[{g[1]}], q[{g[2]}]);\n'
        else: s += '  U(%r,%r,%r, 0.0, q[%d]);\n' % (float(g[3][0]), float(g[3][1]), float(g[3][2]), g[1])
    s += '}\n\nqfunc main(output q: qbit[18]) {\n  allocate(18, q);\n  logo_phase_oracle(q);\n}\n'
    return s

def finalize(G, T, stem=None):
    G = normalize(G)
    lay, st = solve(G, T)
    if lay is None: return {'status': st}
    order = sorted(range(len(G)), key=lambda i: (lay[i], i))
    G2 = [G[i] for i in order]
    src = emit_qasm(G2)
    m = qasm_metrics(src)
    v = verify(src)
    res = {'status': 'SAT', 'metrics': m, 'verify': {k: v[k] for k in ('passed', 'max_phase_err', 'max_leak')}}
    if stem:
        open(stem + '.qasm', 'w').write(src); open(stem + '.qmod', 'w').write(emit_qmod(G2))
        json.dump(res, open(stem + '.json', 'w'), indent=1, default=str)
    return res

if __name__ == '__main__':
    from dag import load
    W, G = load(sys.argv[1]); T = int(sys.argv[2])
    print(finalize(G, T, sys.argv[3] if len(sys.argv) > 3 else None))
