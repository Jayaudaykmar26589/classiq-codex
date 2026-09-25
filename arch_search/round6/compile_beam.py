"""Beam-search compile of a pebbling schedule: choose target/control wires per step to minimise CNOTs
(frame changes), then report the u3/cx depth of the encoder alone."""
import sys, json
sys.path.insert(0, '.')
from pebble import from_xag, canon
from compile_peb import expand, LIN, run
sys.path.insert(0, '/home/user/classiq-codex/arch_search/round5'); sys.path.insert(0, '/home/user/classiq-codex/arch_search')

def step_options(game, forms, nwires, ro_w, i, how, V):
    g = game.g[i]; A, B = game.A[i], game.B[i]
    mod = [w for w in range(nwires) if w not in ro_w]
    if how == 'new':
        tcands = [(w, []) for w in mod if LIN(forms[w]) == 0]
    else:
        basis = list(V)
        def phi(u):
            c = 0
            for jj, b in enumerate(basis):
                if (u >> (b.bit_length() - 1)) & 1: u ^= b; c ^= (how >> jj) & 1
            return c
        ones = [w for w in range(nwires) if LIN(forms[w]) and phi(LIN(forms[w]))]
        tcands = [(t, [w for w in ones if w != t]) for t in ones if t not in ro_w]
    for t, fix in tcands:
        f1 = list(forms); ops1 = []
        for w in fix: ops1.append((0, w, t, 0, 0, 0)); f1[w] ^= f1[t]
        others = [w for w in range(nwires) if w != t]
        SA = expand(A, f1, others)
        if SA is None: continue
        jas = list(SA) if len(SA) == 1 else [w for w in SA if w not in ro_w]
        for ja in jas:
            f2 = list(f1); ops2 = list(ops1)
            if len(SA) > 1:
                for w in SA - {ja}: ops2.append((0, ja, w, 0, 0, 0)); f2[ja] ^= f2[w]
            SB = expand(B, f2, others)
            if SB is None: continue
            if len(SB) == 1:
                jbs = [next(iter(SB))]
                if jbs[0] == ja: continue
            else:
                jbs = [w for w in SB if w != ja and w not in ro_w]
            for jb in jbs:
                f3 = list(f2); ops3 = list(ops2)
                if len(SB) > 1:
                    for w in SB - {jb}: ops3.append((0, jb, w, 0, 0, 0)); f3[jb] ^= f3[w]
                na = (f3[ja] & 1) ^ game.Aconst[i]; nb = (f3[jb] & 1) ^ game.Bconst[i]
                ops3.append((1, t, ja, na, jb, nb)); f3[t] ^= g
                yield ops3, f3

def beam_compile(game, schedule, nwires, ro_w, width=400):
    forms0 = [1 << (1 + j) for j in range(game.n)] + [0] * (nwires - game.n)
    beam = [(0, [], forms0)]
    for i, how in schedule:
        new = []
        for cost, ops, forms in beam:
            V = tuple(canon([LIN(f) for f in forms if LIN(f)]))
            for ops3, f3 in step_options(game, forms, nwires, ro_w, i, how, V):
                c = cost + sum(o[0] == 0 for o in ops3)
                new.append((c, ops + ops3, f3))
        new.sort(key=lambda r: r[0])
        seen = set(); beam = []
        for r in new:
            key = tuple(r[2])
            if key in seen: continue
            seen.add(key); beam.append(r)
            if len(beam) >= width: break
    return beam

if __name__ == '__main__':
    from assemble_sc import lane_gates, to_qasm
    from grader import qasm_metrics
    sol = json.load(open(sys.argv[1])); nanc = int(sys.argv[2]); sched = [tuple(x) for x in json.loads(sys.argv[3])]
    ro = list(map(int, sys.argv[4].split(','))) if len(sys.argv) > 4 and sys.argv[4] else []
    game, V0 = from_xag(sol, nanc, ro); nw = sol['n'] + nanc
    beam = beam_compile(game, sched, nw, ro, int(sys.argv[5]) if len(sys.argv) > 5 else 400)
    best = None
    for cost, ops, forms in beam[:50]:
        wires = list(range(nw))
        q = to_qasm(lane_gates(ops, wires)); m = qasm_metrics(q.replace('qreg q[%d]' % nw, 'qreg q[18]') if nw < 12 else q)
        if best is None or m[1] < best[0][1]: best = (m, cost, ops, forms)
    m, cost, ops, forms = best
    print('best: cnots', cost, 'metrics', m)
    outsel = [sorted(expand(o, forms, list(range(nw)))) for o in game.outs]
    print('code bits as wire parities:', outsel)
    json.dump({'ops': ops, 'outsel': outsel, 'nanc': nanc, 'n': sol['n'], 'map': sol['map'], 'side': sol.get('side')},
              open(sys.argv[1].replace('.json', f'_beam{nanc}.json'), 'w'))
