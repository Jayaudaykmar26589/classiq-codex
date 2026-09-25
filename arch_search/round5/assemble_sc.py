"""Assemble the staircase-comparator oracle from lane programs and verify it.

Layout: x = q0..q5, y = q6..q11 (y5 = q11), ancillas q12..q17.
  swap:   y5 ^= y4 y3 y2           (via ancilla q17, relative-phase Toffolis, exact mirror)
  y-enc:  lane on [y0..y4, anc...] with read-only y5'   -> 3 code wires
  x-enc:  lane on [x0..x5, anc...] with read-only y5'   -> 3 code wires
  kernel: phase (-1)^{[Ly(cy) <= Lx(cx)]} as an exact phase polynomial on the 6 code wires
  then the exact inverse of enc and swap.
Gates are emitted in u3/cx.  Relative-phase Toffolis are safe because every compute block is mirrored exactly.
"""
import sys, json, math, numpy as np
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__file__), '..', 'round4'))
PI = math.pi
def U(t, p, l, q): return ('u3', q, None, (t, p, l))
def CX(c, t): return ('cx', c, t)
Hh = lambda q: U(PI / 2, 0, PI, q)
Xg = lambda q: U(PI, 0, PI, q)
def T(q): return U(0, 0, PI / 4, q)
def Td(q): return U(0, 0, -PI / 4, q)
def rccx(a, b, t):
    """Margolus relative-phase Toffoli (3 CX)."""
    return [Hh(t), T(t), CX(b, t), Td(t), CX(a, t), T(t), CX(b, t), Td(t), Hh(t)]
def inverse(seq):
    out = []
    for g in reversed(seq):
        if g[0] == 'cx': out.append(g)
        else:
            t, p, l = g[3]; out.append(('u3', g[1], None, (-t, -l, -p)))
    return out
def lane_gates(ops, wires):
    """ops: kind,t,a,na,b,nb over local wire indices -> gates on global qubits"""
    seq = []
    for k, t, a, na, b, nb in ops:
        if k == 2: continue
        T_, A, B = wires[t], wires[a], wires[b]
        if k == 0:
            seq.append(CX(A, T_))
            if na: seq.append(Xg(T_))
        else:
            pre = ([Xg(A)] if na else []) + ([Xg(B)] if nb else [])
            seq += pre + rccx(A, B, T_) + pre[::-1]
    return seq
def fin_gates(fin, wires):
    seq = []
    for t, a, b in fin:
        if a >= 0: seq += rccx(wires[a], wires[b], wires[t])
    return seq
def phase_poly(fvals, qubits):
    """exact phase exp(i*pi*f(z)) for f on len(qubits) bits (index bit k <-> qubits[k]) via parity rotations."""
    n = len(qubits); N = 1 << n
    s = np.array([1 - 2 * fvals[i] for i in range(N)], float)
    # pi*f = pi/2*(1-s);  s = sum_S w_S chi_S  with chi_S = (-1)^{S.z}
    w = s.copy(); h = 1
    while h < N:
        w = w.reshape(-1, 2 * h); a = w[:, :h].copy(); b = w[:, h:].copy(); w[:, :h] = a + b; w[:, h:] = a - b; w = w.reshape(-1); h *= 2
    w /= N
    seq = []
    for S in range(1, N):
        if abs(w[S]) < 1e-12: continue
        # phase -pi/2*w_S*(-1)^{S.z}: on parity bit p, (-1)^p -> Rz-type: diag(e^{-i a}, e^{+i a}) with a = pi/2*w_S
        bits = [qubits[k] for k in range(n) if S >> k & 1]; tgt = bits[-1]
        par = [CX(b, tgt) for b in bits[:-1]]
        ang = PI * w[S]          # u3(0,0,lam) = diag(1, e^{i lam}); we need relative phase e^{i*pi*w_S} on parity=1 (up to global)
        seq += par + [U(0, 0, ang, tgt)] + par[::-1]
    return seq
def build(yl, xl, Lx, Ly):
    X = list(range(6)); Y = list(range(6, 12)); A = list(range(12, 18))
    swap = rccx(Y[4], Y[3], A[5]) + rccx(A[5], Y[2], Y[5]) + inverse(rccx(Y[4], Y[3], A[5]))
    ny = yl['nanc']; nx = xl['nanc']
    ywires = Y[:5] + A[:ny] + [Y[5]]
    xwires = X + A[ny:ny + nx] + [Y[5]]
    yenc = lane_gates(yl['ops'], ywires) + fin_gates(yl.get('fin', []), ywires)
    xenc = lane_gates(xl['ops'], xwires) + fin_gates(xl.get('fin', []), xwires)
    cy = [ywires[w] for w in yl['cw']]; cx = [xwires[w] for w in xl['cw']]
    f = [1 if Ly[(i >> 3) & 7] <= Lx[i & 7] else 0 for i in range(64)]   # index bits 0-2 = cx, 3-5 = cy
    kern = phase_poly(f, cx + cy)
    comp = swap + yenc + xenc
    return comp + kern + inverse(comp)
def to_qasm(seq):
    s = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[18];\n'
    for g in seq:
        if g[0] == 'cx': s += f'cx q[{g[1]}],q[{g[2]}];\n'
        else: s += 'u3(%r,%r,%r) q[%d];\n' % (*map(float, g[3]), g[1])
    return s
if __name__ == '__main__':
    yl = json.load(open(sys.argv[1])); xl = json.load(open(sys.argv[2]))
    Lx = list(map(int, sys.argv[3].split(','))); Ly = list(map(int, sys.argv[4].split(',')))
    src = to_qasm(build(yl, xl, Lx, Ly))
    sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__file__), '..'))
    from sparse_verify import verify
    v = verify(src); print(v)
    open(sys.argv[5], 'w').write(src)
