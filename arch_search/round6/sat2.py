"""Exact in-place level-code encoder synthesis, v2.

Gates on nmod modifiable wires (+ read-only wires): CNOT t ^= a (positive control, WLOG) or
Toffoli t ^= (a^na)&(b^nb), a<b.  After G gates, three code bits are ANY affine functions of the
final wires (the phase kernel reads parities, so no final CNOT stage is needed).  Each point's
code must lie in the allowed set of its level (fixed code->level map, up to affine equivalence).
CEGAR over points; symmetry breaking for commuting neighbours.
"""
import sys, time, json, random, itertools
import numpy as np
from pysat.solvers import Solver
from pysat.card import CardEnc

def simulate(prog, init):
    w = list(init)
    for k, t, a, na, b, nb in prog:
        if k == 0: w[t] ^= w[a]
        else: w[t] ^= (w[a] ^ na) & (w[b] ^ nb)
    return w

def affine_fit(finals, allowed, aw=None):
    """search affine maps (3 x (NW+1)) making every point's code allowed: brute force over
    code-bit forms is too big; instead test via small SAT."""
    NW = len(finals[0]); vid = [0]
    if aw is None: aw = list(range(NW))
    def nv(): vid[0] += 1; return vid[0]
    S = [[nv() for _ in range(NW + 1)] for j in range(3)]
    cls = [[-S[j][w]] for j in range(3) for w in range(NW) if w not in aw]
    for p, fv in enumerate(finals):
        outs = []
        for j in range(3):
            lits = [S[j][NW]] + [S[j][w] for w in range(NW) if fv[w]]
            o = nv(); outs.append(o)
            # o = XOR(lits)
            acc = lits[0]
            for l in lits[1:]:
                n = nv(); cls += [[-n, acc, l], [-n, -acc, -l], [n, -acc, l], [n, acc, -l]]; acc = n
            cls += [[-o, acc], [o, -acc]]
        for c in range(8):
            if c in allowed[p]: continue
            cls.append([(-outs[j] if (c >> j) & 1 else outs[j]) for j in range(3)])
    with Solver(name='cd19', bootstrap_with=cls) as s:
        if not s.solve(): return None
        m = set(l for l in s.get_model() if l > 0)
    return [[int(S[j][w] in m) for w in range(NW + 1)] for j in range(3)]

def synth(init, allowed, nmod, G, pts, budget=None, solver='cd19', maxtof=None, aw=None):
    NW = len(init[0]); vid = [0]
    def nv(): vid[0] += 1; return vid[0]
    cls = []
    TRUE = nv(); cls.append([TRUE])
    T = [[nv() for w in range(nmod)] for g in range(G)]
    A = [[nv() for w in range(NW)] for g in range(G)]
    B = [[nv() for w in range(NW)] for g in range(G)]
    NA = [nv() for g in range(G)]; NB = [nv() for g in range(G)]; TOF = [nv() for g in range(G)]
    def exactly1(lst):
        enc = CardEnc.equals(lits=lst, bound=1, top_id=vid[0]); cls.extend(enc.clauses); vid[0] = max(vid[0], enc.nv)
    def atmost1(lst):
        enc = CardEnc.atmost(lits=lst, bound=1, top_id=vid[0]); cls.extend(enc.clauses); vid[0] = max(vid[0], enc.nv)
    for g in range(G):
        exactly1(T[g]); exactly1(A[g]); atmost1(B[g])
        cls.append([-TOF[g]] + B[g])                 # Toffoli <-> some B
        for w in range(NW): cls.append([TOF[g], -B[g][w]])
        cls += [[TOF[g], -NA[g]], [TOF[g], -NB[g]]]   # CNOT: positive control, no b-polarity
        for w in range(nmod): cls += [[-T[g][w], -A[g][w]], [-T[g][w], -B[g][w]]]
        for wa in range(NW):
            for wb in range(wa + 1):
                cls.append([-A[g][wa], -B[g][wb]])     # a < b
    if maxtof is not None:
        enc = CardEnc.atmost(lits=TOF, bound=maxtof, top_id=vid[0]); cls.extend(enc.clauses); vid[0] = max(vid[0], enc.nv)
    # symmetry: consecutive commuting gates with distinct targets must have increasing target index
    for g in range(G - 1):
        for u in range(nmod):
            for v in range(u):
                # gate g targets u, gate g+1 targets v (v<u): forbidden if they commute
                cls.append([-T[g][u], -T[g + 1][v], A[g + 1][u], B[g + 1][u], A[g][v], B[g][v]])
        # same target, commuting: order by A index (weak)
        for u in range(nmod):
            for a1 in range(NW):
                for a2 in range(a1):
                    cls.append([-T[g][u], -T[g + 1][u], -A[g][a1], -A[g + 1][a2], A[g + 1][u], B[g + 1][u], A[g][u], B[g][u]])
    # no immediate identical repeat (cancels)  -- implied mostly by ordering; skip
    # affine output selectors
    S = [[nv() for _ in range(NW + 1)] for j in range(3)]
    if aw is None: aw = list(range(NW))
    def add_point(p):
        val = [TRUE if b else -TRUE for b in init[p]]
        for g in range(G):
            av = nv(); bv = nv()
            for w in range(NW):
                x = val[w]
                cls.extend([[-A[g][w], -x, av], [-A[g][w], x, -av], [-B[g][w], -x, bv], [-B[g][w], x, -bv]])
            la = nv(); lb = nv()
            cls.extend([[-la, av, NA[g]], [-la, -av, -NA[g]], [la, -av, NA[g]], [la, av, -NA[g]]])
            cls.extend([[-lb, bv, NB[g]], [-lb, -bv, -NB[g]], [lb, -bv, NB[g]], [lb, bv, -NB[g]]])
            pr = nv()   # pr = la & (lb | !TOF)
            cls.extend([[-pr, la], [-pr, lb, -TOF[g]], [pr, -la, -lb], [pr, -la, TOF[g]]])
            new = list(val)
            for w in range(nmod):
                o = val[w]; n_ = nv(); t = T[g][w]
                cls.extend([[t, -o, n_], [t, o, -n_], [-t, -pr, -o, -n_], [-t, -pr, o, n_], [-t, pr, -o, n_], [-t, pr, o, -n_]])
                new[w] = n_
            val = new
        outs = []
        for j in range(3):
            acc = S[j][NW]
            for w in aw:
                tmp = nv(); cls.extend([[-tmp, S[j][w]], [-tmp, val[w]], [tmp, -S[j][w], -val[w]]])
                n = nv(); cls.extend([[-n, acc, tmp], [-n, -acc, -tmp], [n, -acc, tmp], [n, acc, -tmp]]); acc = n
            outs.append(acc)
        for c in range(8):
            if c in allowed[p]: continue
            cls.append([(-outs[j] if (c >> j) & 1 else outs[j]) for j in range(3)])
    for p in pts: add_point(p)
    s = Solver(name=solver, bootstrap_with=cls)
    if budget: s.conf_budget(budget); r = s.solve_limited()
    else: r = s.solve()
    if not r: s.delete(); return r, None
    m = set(l for l in s.get_model() if l > 0); s.delete()
    prog = []
    for g in range(G):
        t = [w for w in range(nmod) if T[g][w] in m][0]; a = [w for w in range(NW) if A[g][w] in m][0]
        if TOF[g] in m:
            b = [w for w in range(NW) if B[g][w] in m][0]; prog.append((1, t, a, int(NA[g] in m), b, int(NB[g] in m)))
        else: prog.append((0, t, a, 0, 0, 0))
    return True, prog

def problem(side, ly_or_lx, nanc):
    d = np.load('ferrers.npz')
    lev, lam = d['lev'], d['lam']
    if side == 'y':
        init = [[(v >> b) & 1 for b in range(5)] + [0] * nanc + [(v >> 5) & 1] for v in range(64)]
        levels = [int(lev[v]) for v in range(64)]; nmod = 5 + nanc
    else:
        init = [[((v & 63) >> b) & 1 for b in range(6)] + [0] * nanc + [v >> 6] for v in range(128)]
        levels = [int(lam[v & 63, v >> 6]) for v in range(128)]; nmod = 6 + nanc
    if side in ('xh0', 'xh1'):
        h = int(side[-1])
        init = [[(v >> b) & 1 for b in range(6)] + [0] * nanc + [h] for v in range(64)]
        levels = [int(lam[v, h]) for v in range(64)]; nmod = 6 + nanc
    if side in ('yh0', 'yh1'):
        h = int(side[-1])
        init = [[(v >> b) & 1 for b in range(5)] + [0] * nanc + [h] for v in range(32)]
        levels = [int(lev[v + 32 * h]) for v in range(32)]; nmod = 5 + nanc
    allowed = [set(c for c in range(8) if ly_or_lx[c] == l) for l in levels]
    return init, allowed, nmod

def cegar(side, cmap, nanc, G, seed=0, budget=None, maxtof=None, start=12, log=print, aw=None):
    init, allowed, nmod = problem(side, cmap, nanc)
    NP = len(init); rng = random.Random(seed)
    pts = rng.sample(range(NP), start)
    it = 0
    while True:
        it += 1; t0 = time.time()
        r, prog = synth(init, allowed, nmod, G, pts, budget=budget, maxtof=maxtof, aw=aw)
        if not r:
            log(f'  G={G} pts={len(pts)} -> {"UNSAT" if r is False else "budget"} ({time.time()-t0:.1f}s)'); return r, None
        finals = [simulate(prog, init[p]) for p in range(NP)]
        fit = affine_fit(finals, allowed, aw)
        if fit is not None:
            log(f'  G={G} pts={len(pts)} -> EXACT after {it} rounds ({time.time()-t0:.1f}s)'); return True, (prog, fit)
        # add counterexamples: points whose code under the best subset fit is wrong
        sub = affine_fit([finals[p] for p in pts], [allowed[p] for p in pts], aw)
        bad = []
        for p in range(NP):
            if p in pts: continue
            fv = finals[p] + [1]
            code = sum((sum(sub[j][w] * fv[w] for w in range(len(fv))) & 1) << j for j in range(3))
            if code not in allowed[p]: bad.append(p)
        if not bad: bad = [p for p in range(NP) if p not in pts]
        add = rng.sample(bad, min(len(bad), 3)); pts += add
        log(f'  G={G} round {it}: pts={len(pts)} bad={len(bad)} ({time.time()-t0:.1f}s)')

if __name__ == '__main__':
    side = sys.argv[1]; cmap = list(map(int, sys.argv[2].split(','))); nanc = int(sys.argv[3])
    G0, G1 = map(int, sys.argv[4].split('-')); seed = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    budget = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6] != '0' else None
    mode = sys.argv[7] if len(sys.argv) > 7 else 'all'
    _, _, nmod = problem(side, cmap, nanc); NWt = nmod + 1
    aw = None if mode == 'all' else list(range(nmod - 3, nmod)) + [nmod]
    for G in range(G0, G1 + 1):
        r, res = cegar(side, cmap, nanc, G, seed=seed, budget=budget, log=lambda s: print(s, flush=True), aw=aw)
        if r:
            prog, fit = res
            print('PROG', prog); print('FIT', fit)
            json.dump({'side': side, 'map': cmap, 'nanc': nanc, 'ops': prog, 'fit': fit},
                      open(f'sat2_{side}_{"".join(map(str,cmap))}_{nanc}_{G}.json', 'w'))
            break
