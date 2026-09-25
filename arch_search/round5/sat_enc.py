"""Exact SAT synthesis of an in-place LEVEL-CONSISTENT encoder.

Wires: W modifiable (inputs first, then ancillas = 0) + read-only wires.  G gates, each either
  t ^= la            (CNOT with optional negation)
  t ^= la & lb       (Toffoli, controls with polarity)
where t is a modifiable wire and a, b are any other wires.  After G gates the designated code wires must
separate every pair of points with different wanted levels.  Optional AND-level bound per wire.
"""
import sys, itertools, time, json, numpy as np
from pysat.solvers import Solver
from pysat.card import CardEnc

def synth(points, init_vals, nmod, want, codew, G, maxlev=None, timeout=None, solver='cd19', allow_cx=True):
    NP = len(points); NW = len(init_vals[0]); vid = [0]
    def nv(): vid[0] += 1; return vid[0]
    cls = []
    # selection vars
    T = [[nv() for w in range(nmod)] for g in range(G)]
    A = [[nv() for w in range(NW)] for g in range(G)]
    B = [[nv() for w in range(NW)] for g in range(G)]
    PA = [nv() for g in range(G)]; PB = [nv() for g in range(G)]; ISX = [nv() for g in range(G)]   # ISX: gate is CNOT
    for g in range(G):
        for lst in (T[g], A[g], B[g]):
            enc = CardEnc.equals(lits=lst, bound=1, top_id=vid[0]); cls += enc.clauses; vid[0] = max(vid[0], enc.nv)
        for w in range(nmod):
            cls.append([-T[g][w], -A[g][w]]); cls.append([-T[g][w], -B[g][w]])
        for w in range(NW): cls.append([-A[g][w], -B[g][w]])
        if not allow_cx: cls.append([-ISX[g]])
        # symmetry: for Toffoli, index(a) < index(b)
        for wa in range(NW):
            for wb in range(wa):
                cls.append([ISX[g], -A[g][wa], -B[g][wb]])
    # values
    val = [[[None] * NW for _ in range(G + 1)] for p in range(NP)]
    TRUE = nv(); cls.append([TRUE])
    for p in range(NP):
        for w in range(NW): val[p][0][w] = TRUE if init_vals[p][w] else -TRUE
    for p in range(NP):
        for g in range(G):
            av = nv(); bv = nv(); pr = nv()
            for w in range(NW):
                x = val[p][g][w]
                cls.append([-A[g][w], -x, av]); cls.append([-A[g][w], x, -av])
                cls.append([-B[g][w], -x, bv]); cls.append([-B[g][w], x, -bv])
            # la = av xor PA ; lb = bv xor PB ; pr = la & (lb or ISX)
            la = nv(); lb = nv()
            for (o, i, pp) in ((la, av, PA[g]), (lb, bv, PB[g])):
                cls += [[-o, i, pp], [-o, -i, -pp], [o, -i, pp], [o, i, -pp]]
            # pr <-> la & (lb | ISX)
            cls += [[-pr, la], [-pr, lb, ISX[g]], [pr, -la, -lb], [pr, -la, -ISX[g]]]
            for w in range(NW):
                old = val[p][g][w]
                if w >= nmod: val[p][g + 1][w] = old; continue
                new = nv(); val[p][g + 1][w] = new
                # new = old xor (T & pr)
                t = T[g][w]
                cls += [[t, -old, new], [t, old, -new],
                        [-t, -pr, -old, -new], [-t, -pr, old, new], [-t, pr, -old, new], [-t, pr, old, -new]]
    # level consistency on code wires
    for p in range(NP):
        for q in range(p + 1, NP):
            if want[p] == want[q]: continue
            ds = []
            for w in codew:
                d = nv(); x = val[p][G][w]; y = val[q][G][w]
                cls += [[-d, x, y], [-d, -x, -y]]     # d -> x != y
                ds.append(d)
            cls.append(ds)
    t0 = time.time()
    with Solver(name=solver, bootstrap_with=cls) as s:
        ok = s.solve()
        if not ok: return None, time.time() - t0, len(cls)
        m = set(l for l in s.get_model() if l > 0)
    prog = []
    for g in range(G):
        t = [w for w in range(nmod) if T[g][w] in m][0]; a = [w for w in range(NW) if A[g][w] in m][0]; b = [w for w in range(NW) if B[g][w] in m][0]
        prog.append((0 if ISX[g] in m else 1, t, a, int(PA[g] in m), b, int(PB[g] in m)))
    return prog, time.time() - t0, len(cls)

if __name__ == '__main__':
    d = np.load('ferrers.npz'); lam = d['lam']; lev = d['lev']
    side = sys.argv[1]; nanc = int(sys.argv[2]); G = int(sys.argv[3])
    if side == 'y':
        pts = list(range(64)); nmod = 5 + nanc
        init = [[(v >> b) & 1 for b in range(5)] + [0] * nanc + [(v >> 5) & 1] for v in pts]
        want = [int(lev[v]) for v in pts]
    else:
        pts = list(range(128)); nmod = 6 + nanc
        init = [[((v & 63) >> b) & 1 for b in range(6)] + [0] * nanc + [v >> 6] for v in pts]
        want = [int(lam[v & 63, v >> 6]) for v in pts]
    codew = list(range(nmod - 3, nmod))
    prog, dt, nc = synth(pts, init, nmod, want, codew, G)
    print(side, 'nanc', nanc, 'G', G, 'clauses', nc, 'time %.1f' % dt, 'SAT' if prog else 'UNSAT', flush=True)
    if prog:
        print(prog); json.dump({'ops': prog, 'cw': codew, 'nanc': nanc}, open(f'satenc_{side}_{nanc}_{G}.json', 'w'))
