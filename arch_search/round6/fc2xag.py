"""Convert an exact featchain solution into an XAG blueprint json (A, B, O selectors) for pebble.py.
The code bits are a basis of the annihilator of a subspace K (codim NB) avoiding all difference
vectors between points of different level."""
import sys, json, numpy as np
d = np.load('ferrers.npz'); lam = d['lam']; lev = d['lev']
J = json.load(open(sys.argv[1])); side = J['side']; NF = J['NF']; NB = 3
if side == 'y':
    NP = 64; nin = 6; inp = [[(v >> b) & 1 for b in range(6)] for v in range(NP)]; want = [int(lev[v]) for v in range(NP)]
else:
    NP = 128; nin = 7; inp = [[((v & 63) >> b) & 1 for b in range(6)] + [v >> 6] for v in range(NP)]; want = [int(lam[v & 63, v >> 6]) for v in range(NP)]
F = []
for p in range(NP):
    f = list(inp[p])
    for (ma, ca), (mb, cb) in J['fac']:
        a = (sum(x * y for x, y in zip(ma, f)) + ca) & 1; b = (sum(x * y for x, y in zip(mb, f)) + cb) & 1
        f.append(a & b)
    F.append(f)
n = nin + NF
vec = [sum(b << i for i, b in enumerate(f)) for f in F]
D = set(vec[p] ^ vec[q] for p in range(NP) for q in range(p + 1, NP) if want[p] != want[q])
target = n - NB
allowed = [v for v in range(1, 1 << n) if v not in D]
best = [None]
def dfs(span, basis, start):
    if len(basis) >= target: best[0] = list(basis); return True
    for i in range(start, len(allowed)):
        v = allowed[i]
        if v in span: continue
        new = span | {s ^ v for s in span} | {v}
        if all(u not in D for u in new):
            if dfs(new, basis + [v], i + 1): return True
    return False
dfs(set(), [], 0)
assert best[0] is not None, 'no subspace'
K = best[0]
# annihilator: all w with <w, k> = 0 for k in K; pick NB independent
ann = [w for w in range(1, 1 << n) if all(bin(w & k).count('1') % 2 == 0 for k in K)]
basis = []
for w in ann:
    r = w
    for b in basis:
        if (r >> (b.bit_length() - 1)) & 1: r ^= b
    if r:
        lead = r.bit_length() - 1; basis = [b ^ r if (b >> lead) & 1 else b for b in basis] + [r]
    if len(basis) == NB: break
# check level consistency of code
codes = {}
for p in range(NP):
    c = tuple(bin(w & vec[p]).count('1') & 1 for w in basis); codes.setdefault(c, set()).add(want[p])
assert all(len(s) == 1 for s in codes.values()), codes
out = {'n': nin, 'k': NF, 'side': side,
       'A': [list(ma) + [0] * 0 + [ca] for (ma, ca), _ in J['fac']],
       'B': [list(mb) + [cb] for _, (mb, cb) in J['fac']],
       'O': [[(w >> i) & 1 for i in range(n)] + [0] for w in basis],
       'codemap': {''.join(map(str, c)): sorted(s)[0] for c, s in codes.items()}}
json.dump(out, open(sys.argv[2], 'w')); print('ok', len(codes), 'codes', out['codemap'])
