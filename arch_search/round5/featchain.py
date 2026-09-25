"""Feature-chain encoders: p_i = A_i * B_i with A_i, B_i affine over (inputs, p_1..p_{i-1}).
Inputs are untouched, so reversibility is automatic.  Success <=> there is a subspace K of the
feature space (dim nf) of codimension NB avoiding every difference vector F(p)^F(q) with level(p) != level(q);
then NB affine combinations of the features form a level-consistent code for the kernel."""
import sys, numpy as np, json
d = np.load('ferrers.npz'); lam = d['lam']; lev = d['lev']
side = sys.argv[1]; NF = int(sys.argv[2]); seed = int(sys.argv[3]); NIT = int(sys.argv[4]); NB = int(sys.argv[5]) if len(sys.argv) > 5 else 3
if side == 'y':
    NP = 64; nin = 6; inp = np.array([[(v >> b) & 1 for b in range(6)] for v in range(NP)], np.uint8); want = np.array([lev[v] for v in range(NP)])
else:
    NP = 128; nin = 7; inp = np.array([[((v & 63) >> b) & 1 for b in range(6)] + [v >> 6] for v in range(NP)], np.uint8); want = np.array([lam[v & 63, v >> 6] for v in range(NP)])
diffpairs = [(p, q) for p in range(NP) for q in range(p + 1, NP) if want[p] != want[q]]
PA = np.array([p for p, q in diffpairs]); QA = np.array([q for p, q in diffpairs])
rng = np.random.default_rng(seed)
def features(fac):
    F = inp.copy()
    for i in range(NF):
        nv = F.shape[1]; (ma, ca), (mb, cb) = fac[i]
        a = (F[:, :nv] @ ma[:nv] + ca) & 1; b = (F[:, :nv] @ mb[:nv] + cb) & 1
        F = np.concatenate([F, (a & b)[:, None].astype(np.uint8)], axis=1)
    return F
def vecs(F):
    w = (1 << np.arange(F.shape[1])); return (F.astype(np.int64) @ w)
def max_subspace(Dset, n, target):
    """largest dim of a subspace of GF(2)^n (nonzero vectors) avoiding Dset; stop at target."""
    allowed = [v for v in range(1, 1 << n) if v not in Dset]
    best = [0]; nodes = [0]
    def dfs(span, dim, start):
        nodes[0] += 1
        if dim > best[0]: best[0] = dim
        if best[0] >= target or nodes[0] > 4000: return
        for i in range(start, len(allowed)):
            v = allowed[i]
            if v in span: continue
            new = span | {s ^ v for s in span} | {v}
            if all(u not in Dset for u in new):
                dfs(new, dim + 1, i + 1)
                if best[0] >= target or nodes[0] > 4000: return
    dfs(set(), 0, 0)
    return best[0], len(allowed)
def score(fac):
    F = features(fac); V = vecs(F); D = set((V[PA] ^ V[QA]).tolist())
    n = F.shape[1]; target = n - NB
    dim, nz = max_subspace(D, n, target)
    return (target - dim) * 1000 - nz, dim, target
def rand_aff(nv): return (rng.integers(0, 2, 16).astype(np.int64), int(rng.integers(0, 2)))
fac = [(rand_aff(0), rand_aff(0)) for _ in range(NF)]
cur, dim, tgt = score(fac); best = (cur, fac, dim)
for it in range(NIT):
    T = 300 * (0.5 / 300) ** (it / NIT)
    new = [((a[0].copy(), a[1]), (b[0].copy(), b[1])) for a, b in fac]
    i = rng.integers(NF); j = rng.integers(2); nv = nin + i
    m, c = new[i][j]
    if rng.random() < 0.7: m[rng.integers(nv)] ^= 1
    else: c ^= 1
    pair = list(new[i]); pair[j] = (m, c); new[i] = tuple(pair)
    s, dm, _ = score(new)
    if s <= cur or rng.random() < np.exp((cur - s) / T): fac, cur, dim = new, s, dm
    if cur < best[0]: best = (cur, fac, dim); print(it, 'dim', dim, '/', tgt, 'score', cur, flush=True)
    if best[2] >= tgt: break
print(side, 'NF', NF, 'seed', seed, 'best subspace dim', best[2], 'target', tgt, 'EXACT' if best[2] >= tgt else '', flush=True)
out = [[(list(map(int, a[0][:nin + i])), a[1]), (list(map(int, b[0][:nin + i])), b[1])] for i, (a, b) in enumerate(best[1])]
json.dump({'side': side, 'NF': NF, 'fac': out, 'dim': best[2], 'target': tgt}, open(f'fc_{side}_{NF}_{seed}.json', 'w'))
