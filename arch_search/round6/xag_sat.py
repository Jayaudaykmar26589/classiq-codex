"""Exact multiplicative complexity of a level code: XAG with k AND gates.
g_i = (affine over inputs+g_<i) & (affine over inputs+g_<i); code bit j = affine over inputs+g.
Each point's 3-bit code must lie in its allowed set (fixed code->level map, up to affine equivalence
which the free output forms absorb).  Solve for k = k0..k1."""
import sys, time, json
import numpy as np
from pysat.solvers import Solver

def build(points, allowed, n, k, maxfan=None):
    vid = [0]
    def nv(): vid[0] += 1; return vid[0]
    cls = []
    TRUE = nv(); cls.append([TRUE])
    SA = [[nv() for _ in range(n + i + 1)] for i in range(k)]   # last = constant
    SB = [[nv() for _ in range(n + i + 1)] for i in range(k)]
    SO = [[nv() for _ in range(n + k + 1)] for j in range(3)]
    # symmetry: A-form lexicographically <= B-form is hard; forbid identical selector on the top var
    def xor_chain(sel, vals):
        acc = sel[-1]    # constant bit
        for s, v in zip(sel[:-1], vals):
            if v is True:
                t = s
            elif v is False:
                continue
            else:
                t = nv(); cls.extend([[-t, s], [-t, v], [t, -s, -v]])
            n_ = nv(); cls.extend([[-n_, acc, t], [-n_, -acc, -t], [n_, -acc, t], [n_, acc, -t]]); acc = n_
        return acc
    for p, bits in enumerate(points):
        vals = [bool(b) for b in bits]
        for i in range(k):
            a = xor_chain(SA[i], vals); b = xor_chain(SB[i], vals)
            g = nv(); cls.extend([[-g, a], [-g, b], [g, -a, -b]])
            vals = vals + [g]
        outs = [xor_chain(SO[j], vals) for j in range(3)]
        for c in range(8):
            if c in allowed[p]: continue
            cls.append([(-outs[j] if (c >> j) & 1 else outs[j]) for j in range(3)])
    # each AND must be nontrivial: A and B each use some non-constant var
    for i in range(k):
        cls.append(SA[i][:-1]); cls.append(SB[i][:-1])
    return cls, SA, SB, SO

if __name__ == '__main__':
    d = np.load('ferrers.npz')
    lev, lam = d['lev'], d['lam']
    side = sys.argv[1]; cmap = list(map(int, sys.argv[2].split(','))); k0, k1 = map(int, sys.argv[3].split('-'))
    budget = int(sys.argv[4]) if len(sys.argv) > 4 else None
    if side == 'x':
        pts = [[((v & 63) >> b) & 1 for b in range(6)] + [v >> 6] for v in range(128)]; levels = [int(lam[v & 63, v >> 6]) for v in range(128)]; n = 7
    elif side == 'y':
        pts = [[(v >> b) & 1 for b in range(6)] for v in range(64)]; levels = [int(lev[v]) for v in range(64)]; n = 6
    elif side in ('xh0', 'xh1'):
        h = int(side[-1]); pts = [[(v >> b) & 1 for b in range(6)] for v in range(64)]; levels = [int(lam[v, h]) for v in range(64)]; n = 6
    allowed = [set(c for c in range(8) if cmap[c] == l) for l in levels]
    for k in range(k0, k1 + 1):
        t0 = time.time()
        cls, SA, SB, SO = build(pts, allowed, n, k)
        with Solver(name='cd19', bootstrap_with=cls) as s:
            if budget: s.conf_budget(budget); r = s.solve_limited()
            else: r = s.solve()
            print(side, 'k', k, {True: 'SAT', False: 'UNSAT', None: 'budget'}[r], '%.1fs' % (time.time() - t0), 'clauses', len(cls), flush=True)
            if r:
                m = set(l for l in s.get_model() if l > 0)
                sol = {'A': [[int(v in m) for v in row] for row in SA], 'B': [[int(v in m) for v in row] for row in SB],
                       'O': [[int(v in m) for v in row] for row in SO], 'n': n, 'k': k, 'map': cmap, 'side': side}
                json.dump(sol, open(f'xag_{side}_{k}.json', 'w')); print(sol, flush=True); break
