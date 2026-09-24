"""Exact re-fit of a down-set window with one gate deleted.

The window D (a down-set of the precedence DAG) acts first on |x,y,0>.  Its wires S carry
classical coordinate inputs and |0> ancillas.  We delete one u3 from D and re-optimise every
other u3 in D so that, for all reachable inputs, the output states on S equal the original
ones up to a single global phase.  The rest of the circuit is untouched, so the oracle stays exact.
"""
import sys, math, numpy as np
from scipy.optimize import minimize
sys.path.insert(0, __import__('os').path.dirname(__file__))
from dag import load, precedences, wires
from downset import downset

def u3m(t, p, l):
    c, s = math.cos(t / 2), math.sin(t / 2)
    return np.array([[c, -np.exp(1j * l) * s], [np.exp(1j * p) * s, np.exp(1j * (p + l)) * c]])
def u3d(t, p, l):
    c, s = math.cos(t / 2), math.sin(t / 2)
    dt = np.array([[-s / 2, -np.exp(1j * l) * c / 2], [np.exp(1j * p) * c / 2, -np.exp(1j * (p + l)) * s / 2]])
    dp = np.array([[0, 0], [1j * np.exp(1j * p) * s, 1j * np.exp(1j * (p + l)) * c]])
    dl = np.array([[0, -1j * np.exp(1j * l) * s], [0, 1j * np.exp(1j * (p + l)) * c]])
    return dt, dp, dl

class Window:
    def __init__(self, G, D):
        order = sorted(D)                      # original relative order is a valid order for a down-set
        self.S = sorted(set(w for i in order for w in wires(G[i])))
        self.loc = {w: k for k, w in enumerate(self.S)}
        self.n = len(self.S)
        self.coords = [w for w in self.S if w < 12]
        self.gates = [G[i] for i in order]
        self.idx = order
        # initial batch: coordinates enumerate, ancillas 0
        B = 1 << len(self.coords); self.B = B
        psi = np.zeros((B,) + (2,) * self.n, dtype=complex)
        for b in range(B):
            ix = [0] * self.n
            for k, w in enumerate(self.coords): ix[self.loc[w]] = (b >> k) & 1
            psi[(b,) + tuple(ix)] = 1.0
        self.psi0 = psi
    def apply1(self, psi, M, q):
        psi = np.tensordot(M, psi, axes=([1], [q + 1]))
        return np.moveaxis(psi, 0, q + 1)
    def applycx(self, psi, c, t):
        psi = psi.copy()
        sl1 = [slice(None)] * (self.n + 1); sl1[c + 1] = 1
        sub = psi[tuple(sl1)]
        tt = t + 1 if t < c else t    # axis index inside sub (c axis removed)
        sub2 = np.flip(sub, axis=tt)
        psi[tuple(sl1)] = sub2
        return psi
    def run(self, gates, params):
        psi = self.psi0; k = 0
        for g in gates:
            if g[0] == 'cx': psi = self.applycx(psi, self.loc[g[1]], self.loc[g[2]])
            else: psi = self.apply1(psi, u3m(*params[3 * k:3 * k + 3]), self.loc[g[1]]); k += 1
        return psi
    def fit_setup(self, gates, target):
        self.fg = gates; self.T = target
    def obj(self, params):
        gates = self.fg; ops = []
        psi = self.psi0; k = 0; fw = []
        for g in gates:
            if g[0] == 'cx': psi = self.applycx(psi, self.loc[g[1]], self.loc[g[2]])
            else:
                fw.append(psi); psi = self.apply1(psi, u3m(*params[3 * k:3 * k + 3]), self.loc[g[1]]); k += 1
        z = np.vdot(self.T, psi) / self.B
        # backward
        lam = self.T; grad = np.zeros_like(params); k = len(fw) - 1
        for g in reversed(gates):
            if g[0] == 'cx': lam = self.applycx(lam, self.loc[g[1]], self.loc[g[2]])
            else:
                q = self.loc[g[1]]; p = params[3 * k:3 * k + 3]
                for j, dM in enumerate(u3d(*p)):
                    dz = np.vdot(lam, self.apply1(fw[k], dM, q)) / self.B
                    grad[3 * k + j] = -2 * np.real(np.conj(z) * dz)
                lam = self.apply1(lam, u3m(*p).conj().T, q); k -= 1
        return 1 - abs(z) ** 2, grad

def try_delete(G, prec, gen, delete, restarts=6, seed=0, verbose=True):
    D = downset(G, prec, [gen])
    assert delete in D
    Wn = Window(G, D)
    params0 = []
    for g in Wn.gates:
        if g[0] == 'u3': params0 += list(g[3])
    target = Wn.run(Wn.gates, np.array(params0))
    newg = [g for i, g in zip(Wn.idx, Wn.gates) if i != delete]
    p0 = []
    for i, g in zip(Wn.idx, Wn.gates):
        if g[0] == 'u3' and i != delete: p0 += list(g[3])
    p0 = np.array(p0)
    Wn.fit_setup(newg, target)
    rng = np.random.default_rng(seed); best = (9, None)
    for r in range(restarts):
        x0 = p0 if r == 0 else p0 + rng.normal(0, 0.3 * r, len(p0))
        res = minimize(Wn.obj, x0, jac=True, method='L-BFGS-B', options={'maxiter': 4000, 'ftol': 1e-16, 'gtol': 1e-12})
        if res.fun < best[0]: best = (res.fun, res.x)
        if verbose: print('  restart', r, 'loss %.3e' % res.fun, flush=True)
        if best[0] < 1e-13: break
    return best, Wn, newg

if __name__ == '__main__':
    path = sys.argv[1]; gen = int(sys.argv[2]); dels = list(map(int, sys.argv[3:]))
    W, G = load(path); prec, _ = precedences(G)
    for d in dels:
        (loss, x), Wn, newg = try_delete(G, prec, gen, d)
        print('window gen', gen, 'wires', Wn.n, 'inputs', Wn.B, 'delete', d, G[d][:3], 'best loss %.3e' % loss, flush=True)
