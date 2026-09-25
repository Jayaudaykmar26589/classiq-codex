"""In-place scheduling of a fixed XAG blueprint (subspace pebbling game).

Formal space: bits 1..n = inputs, n+1..n+k = AND outputs g_1..g_k (bit 0 = constant, ignored:
negations are free).  The wires hold affine forms; V = span of all wire forms (read-only wires fixed).
A Toffoli computing g_i = A_i & B_i needs A_i, B_i in V (as forms of two control wires) and acts as
    V' = { u + phi(u) g_i : u in V }
for a linear functional phi on V that vanishes on A_i, B_i and on every read-only wire (target wire
is modifiable and not a control), or, if a zero wire is free, V' = V + span(g_i).
Goal: every output form in V.  IDDFS over moves with a transposition table.
"""
import sys, json, itertools

def canon(vecs):
    """fully reduced echelon basis (canonical for the span)"""
    basis = []
    for v in vecs:
        for b in basis:
            if (v >> (b.bit_length() - 1)) & 1: v ^= b
        if v:
            lead = v.bit_length() - 1
            basis = [b ^ v if (b >> lead) & 1 else b for b in basis]
            basis.append(v)
    return sorted(basis, reverse=True)

def in_span(v, basis):
    for b in basis:
        lead = b.bit_length() - 1
        if (v >> lead) & 1: v ^= b
    return v == 0

class Game:
    def __init__(self, n, k, A, B, outs, ro, nwires):
        self.n, self.k, self.A, self.B, self.outs, self.ro, self.nw = n, k, A, B, outs, ro, nwires
        self.g = [1 << (n + 1 + i) for i in range(k)]
    def moves(self, V):
        V = list(V); d = len(V)
        for i in range(self.k):
            if not (in_span(self.A[i], V) and in_span(self.B[i], V)): continue
            # free zero wire: V + g (only if g not already in V)
            if d < self.nw and not in_span(self.g[i], V):
                yield i, 'new', tuple(canon(V + [self.g[i]]))
            # functionals phi on V vanishing on A_i, B_i, ro wires: express constraints in basis coords
            cons = [self.A[i], self.B[i]] + self.ro
            # coordinates of each constraint vector in basis V
            coords = []
            for c in cons:
                x = 0; v = c
                for j, b in enumerate(V):
                    lead = b.bit_length() - 1
                    if (v >> lead) & 1: v ^= b; x |= 1 << j
                coords.append(x)
            for phi in range(1, 1 << d):
                if any(bin(phi & x).count('1') & 1 for x in coords): continue
                newV = [b ^ self.g[i] if (phi >> j) & 1 else b for j, b in enumerate(V)]
                yield i, phi, tuple(canon(newV))
    def goal(self, V):
        return all(in_span(o, list(V)) for o in self.outs)

def solve(game, V0, maxdepth, log=print):
    seen = {}
    path = []
    def dfs(V, depth):
        if game.goal(V): return True
        if depth == 0: return False
        if seen.get(V, -1) >= depth: return False
        seen[V] = depth
        for i, how, V2 in game.moves(V):
            path.append((i, how))
            if dfs(V2, depth - 1): return True
            path.pop()
        return False
    for D in range(1, maxdepth + 1):
        seen.clear()
        if dfs(V0, D): return path
        log(f'  depth {D}: no schedule ({len(seen)} states)')
    return None

def from_xag(sol, nmod_extra, ro_inputs):
    """sol: xag_sat.py json (A,B,O selectors incl. constant as last entry)."""
    n, k = sol['n'], sol['k']
    def form(sel):     # selectors over inputs then g's then constant
        v = 0
        for j, s in enumerate(sel[:-1]):
            if s: v |= 1 << (1 + j)
        return v
    A = [form(r) for r in sol['A']]; B = [form(r) for r in sol['B']]; outs = [form(r) for r in sol['O']]
    ro = [1 << (1 + j) for j in ro_inputs]
    V0 = tuple(canon([1 << (1 + j) for j in range(n)]))
    game = Game(n, k, A, B, outs, ro, n + nmod_extra)
    game.Aconst = [r[-1] for r in sol['A']]; game.Bconst = [r[-1] for r in sol['B']]
    return game, V0

if __name__ == '__main__':
    sol = json.load(open(sys.argv[1])); nanc = int(sys.argv[2]); maxd = int(sys.argv[3])
    ro = list(map(int, sys.argv[4].split(','))) if len(sys.argv) > 4 and sys.argv[4] else []
    game, V0 = from_xag(sol, nanc, ro)
    p = solve(game, V0, maxd, log=lambda s: print(s, flush=True))
    print('SCHEDULE', p)

def bfs(game, V0, maxstates=5_000_000, log=print):
    """exhaustive breadth-first search; returns shortest schedule or None (with state count)."""
    from collections import deque
    parent = {V0: None}; q = deque([V0])
    while q:
        V = q.popleft()
        if game.goal(V):
            path = []
            while parent[V] is not None:
                P, mv = parent[V]; path.append(mv); V = P
            return path[::-1], len(parent)
        for i, how, V2 in game.moves(V):
            if V2 not in parent:
                parent[V2] = (V, (i, how)); q.append(V2)
                if len(parent) > maxstates: log('state cap hit'); return None, len(parent)
        if len(parent) % 100000 < 50: pass
    return None, len(parent)
