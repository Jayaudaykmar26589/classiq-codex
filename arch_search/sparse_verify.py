"""Sparse exact verifier: all 4096 coordinate inputs, helpers clean.
State = arrays (inp, basis, amp); u3 splits support, cx permutes bits."""
import numpy as np, math
from grader import parse_u3cx, TARGET, qasm_metrics

def u3mat(th, ph, la):
    c, s = math.cos(th / 2), math.sin(th / 2)
    return (c, -np.exp(1j * la) * s, np.exp(1j * ph) * s, np.exp(1j * (ph + la)) * c)

def run(width, gates, prune=1e-14):
    inp = np.arange(4096, dtype=np.int64)
    bas = np.arange(4096, dtype=np.int64)
    amp = np.ones(4096, dtype=np.complex128)
    maxsup = 1
    for g in gates:
        if g[0] == "cx":
            c, t = g[1], g[2]
            bas = bas ^ (((bas >> c) & 1) << t)
            continue
        q = g[2]
        a, b, cc, d = u3mat(*g[1])
        bit = (bas >> q) & 1
        # new amp on |0>: a*amp(bit0) + b*amp(bit1); on |1>: c*amp(bit0) + d*amp(bit1)
        b0 = bas & ~(1 << q)
        a0 = np.where(bit == 0, a, b) * amp
        a1 = np.where(bit == 0, cc, d) * amp
        key = np.concatenate([(inp << 18) | b0, (inp << 18) | (b0 | (1 << q))])
        val = np.concatenate([a0, a1])
        order = np.argsort(key, kind="stable")
        key = key[order]; val = val[order]
        uk, start = np.unique(key, return_index=True)
        sv = np.add.reduceat(val, start)
        keep = np.abs(sv) > prune
        uk = uk[keep]; sv = sv[keep]
        inp = uk >> 18; bas = uk & ((1 << 18) - 1); amp = sv
        maxsup = max(maxsup, int(np.max(np.bincount(inp))))
    return inp, bas, amp, maxsup

def verify(source, tol=1e-9):
    width, gates = parse_u3cx(source)
    inp, bas, amp, maxsup = run(width, gates)
    # expected: support only on bas == inp
    good = bas == inp
    leak = 0.0
    if (~good).any():
        leak = float(np.max(np.bincount(inp[~good], weights=np.abs(amp[~good]) ** 2, minlength=4096)))
    diag = np.zeros(4096, dtype=np.complex128)
    np.add.at(diag, inp[good], amp[good])
    ph = diag * np.where(TARGET, -1.0, 1.0)
    g = ph[0] / abs(ph[0])
    err = float(np.max(np.abs(ph - g)))
    return {"passed": bool(err < tol and leak < tol), "max_phase_err": err, "max_leak": leak,
            "max_support": maxsup, "metrics": qasm_metrics(source)}

if __name__ == "__main__":
    import sys, time
    for f in sys.argv[1:]:
        t = time.time()
        print(f, verify(open(f).read()), f"{time.time()-t:.1f}s")
