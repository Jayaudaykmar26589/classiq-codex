"""Compile a pebbling schedule (pebble.py) into an in-place gate list and verify it classically.

Wire forms are ints over the formal basis: bit 0 = constant, bits 1..n = inputs, bits n+1.. = ANDs.
Gate ops (lane format used elsewhere): (0, t, a, 0, 0, 0) = CNOT a->t ; (1, t, a, na, b, nb) = Toffoli.
"""
import sys, json
from pebble import from_xag, canon, bfs

LIN = lambda v: v >> 1 << 1          # drop constant bit

def expand(target, forms, allowed):
    """indices S of `allowed` wires whose linear parts XOR to LIN(target), or None."""
    basis = []
    for j in allowed:
        v = LIN(forms[j]); sset = {j}
        for bv, bs in basis:
            if (v >> (bv.bit_length() - 1)) & 1: v ^= bv; sset = sset ^ bs
        if v: basis.append((v, sset)); basis.sort(key=lambda r: -r[0])
    v = LIN(target); sset = set()
    for bv, bs in basis:
        if (v >> (bv.bit_length() - 1)) & 1: v ^= bv; sset = sset ^ bs
    return sset if v == 0 else None

def compile_schedule(game, schedule, nwires, ro):
    n = game.n; forms = [1 << (1 + j) for j in range(n)] + [0] * (nwires - n)
    ro_w = [j for j in ro]            # input indices that are read-only wires
    ops = []
    def cnot(a, t):
        ops.append((0, t, a, 0, 0, 0)); forms[t] ^= forms[a]
    V = tuple(canon([LIN(f) for f in forms if LIN(f)]))
    for i, how in schedule:
        g = game.g[i]; A, B = game.A[i], game.B[i]
        mod = [w for w in range(nwires) if w not in ro_w]
        if how == 'new':
            t = next(w for w in mod if LIN(forms[w]) == 0)
        else:
            basis = list(V)
            def phi(u):
                c = 0
                for jj, b in enumerate(basis):
                    if (u >> (b.bit_length() - 1)) & 1: u ^= b; c ^= (how >> jj) & 1
                assert u == 0
                return c
            ones = [w for w in range(nwires) if LIN(forms[w]) and phi(LIN(forms[w]))]
            assert not any(w in ro_w for w in ones)
            t = ones[0]
            for w in ones[1:]: cnot(t, w)
        # make A and B single wires (not t)
        others = [w for w in range(nwires) if w != t]
        SA = expand(A, forms, others); assert SA is not None, 'A not in span'
        ja = next((w for w in SA if w not in ro_w), None) if len(SA) > 1 else next(iter(SA))
        if len(SA) > 1:
            assert ja is not None
            for w in SA - {ja}: cnot(w, ja)
        SB = expand(B, forms, others); assert SB is not None, 'B not in span'
        cand = [w for w in SB if w != ja]
        if len(SB) == 1:
            jb = next(iter(SB)); assert jb != ja
        else:
            jb = next((w for w in cand if w not in ro_w), None); assert jb is not None
            for w in SB - {jb}: cnot(w, jb)
        assert LIN(forms[ja]) == LIN(A) and LIN(forms[jb]) == LIN(B)
        na = (forms[ja] & 1) ^ game.Aconst[i]; nb = (forms[jb] & 1) ^ game.Bconst[i]
        ops.append((1, t, ja, na, jb, nb)); forms[t] ^= g
        V = tuple(canon([LIN(f) for f in forms if LIN(f)]))
    return ops, forms

def run(ops, init):
    w = list(init)
    for k, t, a, na, b, nb in ops:
        if k == 0: w[t] ^= w[a]
        else: w[t] ^= (w[a] ^ na) & (w[b] ^ nb)
    return w

if __name__ == '__main__':
    import numpy as np
    sol = json.load(open(sys.argv[1])); nanc = int(sys.argv[2])
    ro = list(map(int, sys.argv[3].split(','))) if len(sys.argv) > 3 and sys.argv[3] else []
    game, V0 = from_xag(sol, nanc, ro)
    if len(sys.argv) > 4:
        sched = [tuple(x) for x in json.loads(sys.argv[4].replace("'", '"').replace('(', '[').replace(')', ']'))]
    else:
        sched, nst = bfs(game, V0, 20_000_000)
    print('schedule', sched)
    nw = sol['n'] + nanc
    ops, forms = compile_schedule(game, sched, nw, ro)
    print('ops', len(ops), 'toffolis', sum(o[0] == 1 for o in ops), 'cnots', sum(o[0] == 0 for o in ops))
    # verify: evaluate XAG outputs from inputs, and check each output form is an affine combination of final wires
    # (formal check) and that the code is level-consistent on real points
    d = np.load('ferrers.npz'); lam = d['lam']; lev = d['lev']
    side = sol.get('side', 'xh0'); cmap = sol['map']
    if side in ('xh0', 'xh1'):
        h = int(side[-1]); pts = [[(v >> b) & 1 for b in range(6)] for v in range(64)]; want = [int(lam[v, h]) for v in range(64)]
    elif side == 'y':
        pts = [[(v >> b) & 1 for b in range(6)] for v in range(64)]; want = [int(lev[v]) for v in range(64)]
    else:
        pts = [[((v & 63) >> b) & 1 for b in range(6)] + [v >> 6] for v in range(128)]; want = [int(lam[v & 63, v >> 6]) for v in range(128)]
    outsel = []
    for o in game.outs:
        S = expand(o, forms, list(range(nw))); assert S is not None; outsel.append(sorted(S))
    finals = [run(ops, p + [0] * nanc) for p in pts]
    assert len(set(map(tuple, finals))) == len(pts), 'not injective'
    codes = {}
    for f, wv in zip(finals, want):
        c = tuple(sum(f[s] for s in S) & 1 for S in outsel); codes.setdefault(c, set()).add(wv)
    ok = all(len(s) == 1 for s in codes.values())
    print('injective, level-consistent:', ok, {''.join(map(str, c)): sorted(s) for c, s in codes.items()})
    json.dump({'ops': ops, 'outsel': outsel, 'nanc': nanc, 'n': sol['n'], 'side': side, 'map': cmap},
              open(sys.argv[1].replace('.json', f'_inplace{nanc}.json'), 'w'))
