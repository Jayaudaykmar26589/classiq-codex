"""BFS over the pebbling game keeping ALL shortest-path parents, then sample many shortest schedules,
beam-compile each (frame choice), fuse u3s and keep the lowest-depth encoder.
usage: peb_multi.py blueprint.json nanc samples beamwidth [ro]"""
import sys, json, random, time
from collections import deque
sys.path.insert(0, '.')
from pebble import from_xag
from compile_beam import beam_compile
from compile_peb import expand, run
sys.path.insert(0, '/home/user/classiq-codex/arch_search/round5'); sys.path.insert(0, '/home/user/classiq-codex/arch_search')
from assemble_sc import lane_gates, to_qasm
from grader import qasm_metrics
from fuse import fuse

def bfs_all(game, V0, cap=30_000_000):
    dist = {V0: 0}; par = {V0: []}; q = deque([V0]); goals = []; gd = None
    while q:
        V = q.popleft(); d = dist[V]
        if gd is not None and d >= gd: break
        for i, how, V2 in game.moves(V):
            if V2 not in dist:
                dist[V2] = d + 1; par[V2] = [(V, (i, how))]; q.append(V2)
                if game.goal(V2):
                    gd = d + 1; goals.append(V2)
                if len(dist) > cap: raise MemoryError('cap')
            elif dist[V2] == d + 1:
                par[V2].append((V, (i, how)))
                if game.goal(V2) and V2 not in goals: goals.append(V2)
    return goals, par, len(dist)

def sample(goals, par, rng):
    V = rng.choice(goals); path = []
    while par[V]:
        P, mv = rng.choice(par[V]); path.append(mv); V = P
    return path[::-1]

if __name__ == '__main__':
    sol = json.load(open(sys.argv[1])); nanc = int(sys.argv[2]); ns = int(sys.argv[3]); bw = int(sys.argv[4])
    ro = list(map(int, sys.argv[5].split(','))) if len(sys.argv) > 5 and sys.argv[5] else []
    game, V0 = from_xag(sol, nanc, ro); nw = sol['n'] + nanc
    t0 = time.time(); goals, par, nst = bfs_all(game, V0)
    print('states', nst, 'goal states', len(goals), '%.0fs' % (time.time() - t0), flush=True)
    rng = random.Random(1); seen = set(); best = None
    for s in range(ns):
        sched = sample(goals, par, rng)
        key = tuple(sched)
        if key in seen: continue
        seen.add(key)
        beam = beam_compile(game, sched, nw, ro, bw)
        for cost, ops, forms in beam[:20]:
            seq = fuse(lane_gates(ops, list(range(nw))))
            m = qasm_metrics(to_qasm(seq))
            if best is None or (m[1], m[2]) < (best[0][1], best[0][2]):
                best = (m, sched, ops, forms); print('best', m, 'cnots', cost, 'sched', sched, flush=True)
    m, sched, ops, forms = best
    outsel = [sorted(expand(o, forms, list(range(nw)))) for o in game.outs]
    json.dump({'ops': ops, 'outsel': outsel, 'nanc': nanc, 'n': sol['n'], 'map': sol['map'], 'side': sol.get('side'),
               'metrics': m, 'schedule': sched}, open(sys.argv[1].replace('.json', f'_multi{nanc}.json'), 'w'))
    print('distinct schedules tried', len(seen), 'final', m, 'outsel', outsel)
