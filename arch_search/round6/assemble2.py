"""Assemble the staircase comparator from in-place encoders whose code bits are parities of wire sets.

Layout: x = q0..q5, y = q6..q11 (y5 = q11), ancillas q12..q17.
  swap:   y5 ^= y4 y3 y2   (ancilla a holds y4*y3 during the swap; mirrored at the end)
  x-enc:  ops over local wires [x0..x5, xanc..., h]   (h = y5' read-only)
  y-enc:  ops over local wires [y0..y4, yanc..., h]
  kernel: phase pi * K(cx, cy) where cx_j / cy_j = parity of the listed wires (constants inferred)
Everything is mirrored exactly, so relative-phase Toffolis are safe.
"""
import sys, json, math, itertools
import numpy as np
sys.path.insert(0, '/home/user/classiq-codex/arch_search/round5'); sys.path.insert(0, '/home/user/classiq-codex/arch_search')
sys.path.insert(0, '.')
from assemble_sc import rccx, inverse, lane_gates, to_qasm, U, CX, PI
from fuse import fuse
d = np.load('ferrers.npz'); LAM = d['lam']; LEV = d['lev']

def fwht(a):
    a = a.astype(float).copy(); h = 1
    while h < len(a):
        a = a.reshape(-1, 2 * h); u = a[:, :h].copy(); v = a[:, h:].copy(); a[:, :h] = u + v; a[:, h:] = u - v; a = a.reshape(-1); h *= 2
    return a

def run_ops(ops, w):
    w = list(w)
    for k, t, a, na, b, nb in ops:
        if k == 2: continue
        if k == 0: w[t] ^= w[a] ^ na
        else: w[t] ^= (w[a] ^ na) & (w[b] ^ nb)
    return w

def observed_code(enc, init, sets):
    f = run_ops(enc['ops'], init)
    return sum((sum(f[s] for s in S) & 1) << j for j, S in enumerate(sets))

def kernel_gates(xsets, ysets, Kfun, wx, wy):
    """phase pi*K(cx,cy); K given on all 64 (cx,cy) (index cx | cy<<3). Parity terms implemented naively
    (CNOT chain onto one wire, u3 phase, undo) and left to fusion/cancellation."""
    g = np.array([Kfun(i & 7, i >> 3) for i in range(64)])
    w = fwht(1 - 2 * g) / 64.0
    seq = []
    for S in range(1, 64):
        if abs(w[S]) < 1e-12: continue
        P = set()
        for j in range(3):
            if (S >> j) & 1: P ^= set(wx[q] for q in xsets[j])
            if (S >> (j + 3)) & 1: P ^= set(wy[q] for q in ysets[j])
        P = sorted(P); tgt = P[-1]
        par = [CX(q, tgt) for q in P[:-1]]
        # pi*K = pi/2 - pi/2 * sum_S w_S chi_S  -> apply exp(-i pi/2 w_S chi_S) = phase e^{+i pi w_S} on chi=1 (up to global)
        seq += par + [U(0, 0, PI * w[S], tgt)] + par[::-1]
    return seq

def build(xenc, yenc, Lx=None, Ly=None):
    X = list(range(6)); Y = list(range(6, 12)); A = list(range(12, 18))
    nx, ny = xenc['nanc'], yenc['nanc']
    assert nx + ny <= 5, 'one ancilla is reserved for the swap product'
    swap_anc = A[5]
    swap = rccx(Y[4], Y[3], swap_anc) + rccx(swap_anc, Y[2], Y[5])
    wx = X + A[:nx] + [Y[5]]
    wy = Y[:5] + A[nx:nx + ny] + [Y[5]]
    xs, ys = xenc['outsel'], yenc['outsel']
    # infer code -> level tables from the actual encoders
    tabx = {}; taby = {}
    for v in range(128):
        x, h = v & 63, v >> 6
        init = [(x >> b) & 1 for b in range(6)] + [0] * nx + [h]
        tabx.setdefault(observed_code(xenc, init, xs), set()).add(int(LAM[x, h]))
    for yv in range(64):
        init = [(yv >> b) & 1 for b in range(5)] + [0] * ny + [(yv >> 5) & 1]
        taby.setdefault(observed_code(yenc, init, ys), set()).add(int(LEV[yv]))
    assert all(len(s) == 1 for s in tabx.values()) and all(len(s) == 1 for s in taby.values()), (tabx, taby)
    tx = {c: next(iter(s)) for c, s in tabx.items()}; ty = {c: next(iter(s)) for c, s in taby.items()}
    # unobserved codes: choose values minimising kernel support (small search over fills)
    ux = [c for c in range(8) if c not in tx]; uy = [c for c in range(8) if c not in ty]
    best = None
    for fx in itertools.product(range(6), repeat=len(ux)):
        for fy in itertools.product([1, 2, 3, 4, 5, 7], repeat=len(uy)):
            TX = dict(tx); TX.update(zip(ux, fx)); TY = dict(ty); TY.update(zip(uy, fy))
            g = np.array([1 if TY[cy] <= TX[cx] else 0 for cy in range(8) for cx in range(8)])
            s = int((np.abs(fwht(1 - 2 * g)) > 1e-9).sum())
            if best is None or s < best[0]: best = (s, TX, TY)
    _, TX, TY = best
    K = lambda cx, cy: 1 if TY[cy] <= TX[cx] else 0
    xe = lane_gates(xenc['ops'], wx); ye = lane_gates(yenc['ops'], wy)
    comp = swap + xe + ye
    kern = kernel_gates(xs, ys, K, wx, wy)
    return comp + kern + inverse(comp), best[0] - 1

if __name__ == '__main__':
    from grader import qasm_metrics
    from sparse_verify import verify
    xenc = json.load(open(sys.argv[1])); yenc = json.load(open(sys.argv[2]))
    seq, kterms = build(xenc, yenc)
    q = to_qasm(fuse(seq))
    v = verify(q)
    print('kernel terms', kterms, 'metrics', qasm_metrics(q), 'passed', v['passed'], v['max_phase_err'], v['max_leak'])
    if len(sys.argv) > 3: open(sys.argv[3], 'w').write(q)

def kernel_gates_gray(xsets, ysets, Kfun, wx, wy, section_size=None):
    """same phase as kernel_gates, synthesized with GraySynth (Amy-Azimzadeh-Mosca) + PMH restore."""
    from qiskit.synthesis import synth_cnot_phase_aam
    g = np.array([Kfun(i & 7, i >> 3) for i in range(64)])
    w = fwht(1 - 2 * g) / 64.0
    terms = []
    for S in range(1, 64):
        if abs(w[S]) < 1e-12: continue
        P = set()
        for j in range(3):
            if (S >> j) & 1: P ^= set(wx[q] for q in xsets[j])
            if (S >> (j + 3)) & 1: P ^= set(wy[q] for q in ysets[j])
        terms.append((frozenset(P), PI * w[S]))
    W = sorted(set().union(*[P for P, _ in terms]))
    n = len(W)
    ss = section_size or next(s for s in (3, 2, 1) if n % s == 0)
    cn = [[1 if W[r] in P else 0 for (P, _) in terms] for r in range(n)]
    # Qiskit reduces numeric angles mod pi (bug); pass index tags in (0, pi) and substitute afterwards
    tags = [(j + 1) * 1e-4 for j in range(len(terms))]
    qc = synth_cnot_phase_aam(cn, list(tags), section_size=ss)
    seq = []
    for ins in qc.data:
        qs = [qc.find_bit(q).index for q in ins.qubits]
        if ins.operation.name == 'cx': seq.append(CX(W[qs[0]], W[qs[1]]))
        elif ins.operation.name == 'p':
            j = int(round(float(ins.operation.params[0]) / 1e-4)) - 1
            seq.append(U(0, 0, terms[j][1], W[qs[0]]))
        else: raise ValueError(ins.operation.name)
    return seq
