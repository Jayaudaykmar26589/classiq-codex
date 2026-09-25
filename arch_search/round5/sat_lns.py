"""Large-neighbourhood search with exact SAT: keep a near-exact in-place encoder, free a window of K ops,
fix prefix (as constants) and suffix (as fixed-wiring gates), and ask SAT for window gates that make the
designated code wires level-consistent on every input.  Code->level map is free (pairwise inequality)."""
import sys, json, time, numpy as np
from pysat.solvers import Solver
from pysat.card import CardEnc
d = np.load('ferrers.npz'); lev = d['lev']; lam = d['lam']

def run_ops(w, ops):
    for k, t, a, na, b, nb in ops:
        if k == 2: continue
        A = w[a] ^ na
        if k == 0: w[t] ^= A
        else: w[t] ^= A & (w[b] ^ nb)
    return w

def lns(side, J, i0, K, tlimit):
    nanc = J['nanc']; cw = J['cw']; ops = [o for o in J['ops'] if o[0] != 2]
    if side == 'y':
        NP = 64; nmod = 5 + nanc
        init = lambda v: [(v >> b) & 1 for b in range(5)] + [0] * nanc + [(v >> 5) & 1]; want = [int(lev[v]) for v in range(64)]
    else:
        NP = 128; nmod = 6 + nanc
        init = lambda v: [((v & 63) >> b) & 1 for b in range(6)] + [0] * nanc + [v >> 6]; want = [int(lam[v & 63, v >> 6]) for v in range(128)]
    NW = nmod + 1
    pre = ops[:i0]; suf = ops[i0 + K:]
    vid = [0]
    def nv(): vid[0] += 1; return vid[0]
    cls = []; TRUE = nv(); cls.append([TRUE])
    T = [[nv() for _ in range(nmod)] for g in range(K)]; A = [[nv() for _ in range(NW)] for g in range(K)]; B = [[nv() for _ in range(NW)] for g in range(K)]
    PA = [nv() for g in range(K)]; PB = [nv() for g in range(K)]; ISX = [nv() for g in range(K)]; NOP = [nv() for g in range(K)]
    for g in range(K):
        for lst in (T[g], A[g], B[g]):
            enc = CardEnc.equals(lits=lst, bound=1, top_id=vid[0]); cls += enc.clauses; vid[0] = max(vid[0], enc.nv)
        for w in range(nmod): cls += [[-T[g][w], -A[g][w]], [-T[g][w], -B[g][w]]]
        for w in range(NW): cls.append([-A[g][w], -B[g][w]])
    finals = []
    for p in range(NP):
        w0 = run_ops(init(p), pre)
        val = [TRUE if b else -TRUE for b in w0]
        for g in range(K):
            av = nv(); bv = nv(); la = nv(); lb = nv(); pr = nv()
            for w in range(NW):
                x = val[w]; cls += [[-A[g][w], -x, av], [-A[g][w], x, -av], [-B[g][w], -x, bv], [-B[g][w], x, -bv]]
            for (o, i, pp) in ((la, av, PA[g]), (lb, bv, PB[g])):
                cls += [[-o, i, pp], [-o, -i, -pp], [o, -i, pp], [o, i, -pp]]
            # pr <-> !NOP & la & (lb | ISX)
            cls += [[-pr, la], [-pr, lb, ISX[g]], [-pr, -NOP[g]], [pr, NOP[g], -la, -lb], [pr, NOP[g], -la, -ISX[g]]]
            new = list(val)
            for w in range(nmod):
                o = val[w]; n_ = nv(); t = T[g][w]
                cls += [[t, -o, n_], [t, o, -n_], [-t, -pr, -o, -n_], [-t, -pr, o, n_], [-t, pr, -o, n_], [-t, pr, o, -n_]]
                new[w] = n_
            val = new
        for k, t, a, na, b, nb in suf:          # fixed gates on symbolic values
            if k == 2: continue
            x = val[a] if not na else -val[a]
            if k == 0: prod = x
            else:
                y = val[b] if not nb else -val[b]; prod = nv(); cls += [[-prod, x], [-prod, y], [prod, -x, -y]]
            o = val[t]; n_ = nv(); cls += [[-n_, o, prod], [-n_, -o, -prod], [n_, -o, prod], [n_, o, -prod]]
            val = list(val); val[t] = n_
        finals.append([val[w] for w in cw])
    for p in range(NP):
        for q in range(p + 1, NP):
            if want[p] == want[q]: continue
            ds = []
            for a_, b_ in zip(finals[p], finals[q]):
                dd = nv(); cls += [[-dd, a_, b_], [-dd, -a_, -b_]]; ds.append(dd)
            cls.append(ds)
    with Solver(name='cd19', bootstrap_with=cls) as s:
        s.conf_budget(tlimit)
        r = s.solve_limited()
        if not r: return r, None
        m = set(l for l in s.get_model() if l > 0)
    win = []
    for g in range(K):
        if NOP[g] in m: win.append([2, 0, 0, 0, 0, 0]); continue
        t = [w for w in range(nmod) if T[g][w] in m][0]; a = [w for w in range(NW) if A[g][w] in m][0]; b = [w for w in range(NW) if B[g][w] in m][0]
        win.append([0 if ISX[g] in m else 1, t, a, int(PA[g] in m), b, int(PB[g] in m)])
    return True, ops[:i0] + win + suf

if __name__ == '__main__':
    side = sys.argv[1]; J = json.load(open(sys.argv[2])); K = int(sys.argv[3]); budget = int(sys.argv[4])
    ops = [o for o in J['ops'] if o[0] != 2]; L = len(ops)
    starts = list(range(0, max(1, L - K + 1), max(1, K // 2)))
    for i0 in starts:
        t0 = time.time(); r, newops = lns(side, J, i0, K, budget)
        print(f'window {i0}+{K}: {"SAT" if r else ("UNSAT" if r is False else "budget")} {time.time()-t0:.1f}s', flush=True)
        if r:
            out = dict(J); out['ops'] = newops
            fn = sys.argv[2].replace('.json', f'_lns{i0}_{K}.json'); json.dump(out, open(fn, 'w')); print('EXACT ->', fn); break
