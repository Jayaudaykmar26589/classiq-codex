"""Depth-oriented phase-polynomial (parity network) synthesis by layered beam search.

Wires hold parity masks (ints over the wire basis).  Each layer: a set of disjoint CNOTs
(control mask XORed into target) plus phase gates on idle wires whose mask is a pending term.
After all terms are applied, the frame is restored to the identity by a layered greedy CNOT
elimination.  Returns a gate list [('cx',c,t) | ('p',q,angle)] and its depth."""
import random, itertools

def restore_layers(masks):
    """greedy Gaussian elimination in parallel layers: returns list of layers of (c,t) CNOTs mapping masks -> unit vectors."""
    masks = list(masks); n = len(masks); layers = []
    # target: masks[i] == 1<<i ; do row reduction: column by column pick pivot
    ops = []
    M = list(masks)
    # plain Gauss-Jordan to identity with CNOTs (row ops): row_t ^= row_c
    for col in range(n):
        bit = 1 << col
        piv = next((r for r in range(col, n) if M[r] & bit), None)
        if piv is None: piv = next(r for r in range(n) if M[r] & bit)
        if piv != col:
            if not (M[col] & bit):
                ops.append((piv, col)); M[col] ^= M[piv]
        for r in range(n):
            if r != col and M[r] & bit:
                ops.append((col, r)); M[r] ^= M[col]
    assert all(M[i] == 1 << i for i in range(n)), M
    # pack ops into ASAP layers preserving order dependencies
    last = [0] * n; lay = {}
    for c, t in ops:
        l = max(last[c], last[t]) + 1; last[c] = last[t] = l; lay.setdefault(l, []).append((c, t))
    return [lay[k] for k in sorted(lay)], len(ops)

def synth(terms, n, width=64, seed=0, maxlayers=80):
    """terms: dict mask -> angle over n wires (mask bit i = wire i)."""
    rng = random.Random(seed)
    start = (tuple(1 << i for i in range(n)), frozenset(terms), ())
    beam = [start]; best_done = None
    for L in range(maxlayers):
        new = []
        for masks, rem, hist in beam:
            if not rem:
                new.append((masks, rem, hist)); continue
            useful = [(c, t) for c in range(n) for t in range(n) if c != t and (masks[t] ^ masks[c]) in rem]
            other = [(c, t) for c in range(n) for t in range(n) if c != t]
            for variant in range(6):
                pool = list(useful); rng.shuffle(pool)
                used = set(); layer = []
                # phases first on wires whose current mask is pending (they stay idle this layer)
                ph = [q for q in range(n) if masks[q] in rem]
                phase_now = set(q for q in ph if variant % 2 == 0 or rng.random() < 0.5)
                used |= phase_now
                for c, t in pool:
                    if c in used or t in used: continue
                    layer.append((c, t)); used |= {c, t}
                if not layer and not phase_now:
                    c, t = rng.choice(other); layer.append((c, t))
                m2 = list(masks); r2 = set(rem); gates = []
                for q in phase_now: gates.append(('p', q, terms[masks[q]])); r2.discard(masks[q])
                for c, t in layer: m2[t] ^= m2[c]; gates.append(('cx', c, t))
                new.append((tuple(m2), frozenset(r2), hist + (tuple(gates),)))
        # score: remaining terms, then how many pending masks are one CNOT away
        def score(s):
            masks, rem, hist = s
            near = sum(1 for c in range(n) for t in range(n) if c != t and (masks[t] ^ masks[c]) in rem)
            now = sum(1 for q in range(n) if masks[q] in rem)
            return (len(rem), -now, -near)
        new.sort(key=score)
        seen = set(); beam = []
        for s in new:
            k = (s[0], s[1])
            if k in seen: continue
            seen.add(k); beam.append(s)
            if len(beam) >= width: break
        done = [s for s in beam if not s[1]]
        for masks, rem, hist in done:
            rl, nops = restore_layers(masks)
            tot = len(hist) + len(rl)
            if best_done is None or tot < best_done[0]:
                best_done = (tot, hist, rl)
        if best_done and all(not s[1] for s in beam): break
    tot, hist, rl = best_done
    seq = [g for layer in hist for g in layer] + [('cx', c, t) for layer in rl for (c, t) in layer]
    return seq, tot

if __name__ == '__main__':
    import numpy as np, sys, math, json
    def fwht(a):
        a = a.astype(float).copy(); h = 1
        while h < len(a):
            a = a.reshape(-1, 2 * h); u = a[:, :h].copy(); v = a[:, h:].copy(); a[:, :h] = u + v; a[:, h:] = u - v; a = a.reshape(-1); h *= 2
        return a
    Lx = [0, 1, 0, 2, 0, 4, 3, 5]; Ly = [5, 2, 4, 7, 7, 3, 1, 5]
    g = np.array([1 if Ly[cy] <= Lx[cx] else 0 for cy in range(8) for cx in range(8)])
    w = fwht(1 - 2 * g) / 64
    terms = {S: math.pi * w[S] for S in range(1, 64) if abs(w[S]) > 1e-12}
    best = None
    for seed in range(int(sys.argv[1]) if len(sys.argv) > 1 else 4):
        seq, tot = synth(terms, 6, width=int(sys.argv[2]) if len(sys.argv) > 2 else 64, seed=seed)
        # verify
        err = 0
        ph = [0.0] * 64
        for s in range(64):
            b = [(s >> i) & 1 for i in range(6)]; tot_ph = 0.0
            for gt in seq:
                if gt[0] == 'cx': b[gt[2]] ^= b[gt[1]]
                else: tot_ph += gt[2] * b[gt[1]]
            assert b == [(s >> i) & 1 for i in range(6)]
            ph[s] = tot_ph
        for s in range(64):
            want = sum(a for S, a in terms.items() if bin(S & s).count('1') & 1)
            e = (ph[s] - want) % (2 * math.pi); err = max(err, min(e, 2 * math.pi - e))
        # depth with the grader's rule (p gates count as a layer)
        qd = [0] * 6
        for gt in seq:
            qs = (gt[1], gt[2]) if gt[0] == 'cx' else (gt[1],)
            l = max(qd[q] for q in qs) + 1
            for q in qs: qd[q] = l
        d = max(qd); cx = sum(gt[0] == 'cx' for gt in seq)
        print('seed', seed, 'depth', d, 'cx', cx, 'err', err, flush=True)
        if best is None or (d, cx) < best[:2]: best = (d, cx, seq)
    print('BEST depth', best[0], 'cx', best[1])
