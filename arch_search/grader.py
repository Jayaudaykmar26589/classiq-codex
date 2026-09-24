"""Grader-exact metrics (verbatim logic from baseline_notebook.ipynb cell 16) and
an exact all-4096-input verifier for u3/cx QASM oracles."""
import re, math
import numpy as np

GRID = 64

def logo_pixel(x, y):
    return ((2 <= x <= 26 and 29 <= y <= 53) or (26 <= x <= 49 and 39 <= y <= 43)
            or (x - 55) ** 2 + (y - 41) ** 2 <= 42 or (x - 40) ** 2 + (y - 19) ** 2 <= 72)

TARGET = np.array([logo_pixel(i & 63, i >> 6) for i in range(4096)], dtype=bool)
assert TARGET.sum() == 1097

def qasm_metrics(source):
    statements = [s.strip() for s in re.sub(r"//[^\n]*", "", source).split(";") if s.strip()]
    if statements[:2] != ["OPENQASM 2.0", 'include "qelib1.inc"']:
        raise ValueError("header")
    m = re.fullmatch(r"qreg\s+q\s*\[\s*(\d+)\s*\]", statements[2])
    width = int(m.group(1))
    if not 12 <= width <= 18:
        raise ValueError("width")
    qd = [0] * width
    cx = 0
    for st in statements[3:]:
        u = re.fullmatch(r"u3\s*\([^,]+,[^,]+,[^,]+\)\s+q\s*\[\s*(\d+)\s*\]", st)
        c = re.fullmatch(r"cx\s+q\s*\[\s*(\d+)\s*\]\s*,\s*q\s*\[\s*(\d+)\s*\]", st)
        if u:
            qs = (int(u.group(1)),)
        elif c:
            qs = tuple(map(int, c.groups())); cx += 1
        else:
            raise ValueError("Unsupported: " + st)
        if len(set(qs)) != len(qs) or any(q >= width for q in qs):
            raise ValueError("operands")
        layer = max(qd[q] for q in qs) + 1
        for q in qs:
            qd[q] = layer
    return width, max(qd), cx

def parse_u3cx(source):
    """Return width and list of ('u3',(th,ph,la),q) / ('cx',c,t)."""
    src = re.sub(r"//[^\n]*", "", source)
    width = int(re.search(r"qreg\s+q\s*\[\s*(\d+)\s*\]", src).group(1))
    gates = []
    def ev(s):
        return float(eval(s.replace("pi", str(math.pi)), {"__builtins__": {}}, {}))
    for st in src.split(";"):
        st = st.strip()
        if st.startswith("u3"):
            m = re.fullmatch(r"u3\s*\(([^,]+),([^,]+),([^,]+)\)\s+q\s*\[\s*(\d+)\s*\]", st)
            gates.append(("u3", (ev(m.group(1)), ev(m.group(2)), ev(m.group(3))), int(m.group(4))))
        elif st.startswith("cx"):
            m = re.fullmatch(r"cx\s+q\s*\[\s*(\d+)\s*\]\s*,\s*q\s*\[\s*(\d+)\s*\]", st)
            gates.append(("cx", int(m.group(1)), int(m.group(2))))
    return width, gates

def u3mat(th, ph, la):
    c, s = math.cos(th / 2), math.sin(th / 2)
    return np.array([[c, -np.exp(1j * la) * s], [np.exp(1j * ph) * s, np.exp(1j * (ph + la)) * c]])

def simulate(width, gates, psi):
    """psi: array shape (batch, 2**width); little-endian qubit q = bit q of index."""
    n = width
    psi = psi.reshape((-1,) + (2,) * n)  # axes: batch, then bit n-1 ... bit 0
    for g in gates:
        if g[0] == "u3":
            U = u3mat(*g[1]); q = g[2]; ax = n - q
            psi = np.moveaxis(np.tensordot(U, psi, axes=([1], [ax])), 0, ax)
        else:
            c, t = g[1], g[2]; ac, at = n - c, n - t
            idx = [slice(None)] * (n + 1); idx[ac] = 1
            sub = psi[tuple(idx)]
            at2 = at if at < ac else at - 1
            sub = np.flip(sub, axis=at2)
            psi = psi.copy(); psi[tuple(idx)] = sub
    return psi.reshape(psi.shape[0], -1)

def verify_all(source, chunk=256, tol=1e-9):
    """Exact check on all 4096 coordinate basis inputs (helpers start |0>)."""
    width, gates = parse_u3cx(source)
    N = 1 << width
    worst = 0.0; leak = 0.0; gphase = None
    for start in range(0, 4096, chunk):
        idx = np.arange(start, min(4096, start + chunk))
        psi = np.zeros((len(idx), N), dtype=np.complex128)
        psi[np.arange(len(idx)), idx] = 1.0
        out = simulate(width, gates, psi)
        diag = out[np.arange(len(idx)), idx]
        leak = max(leak, float(np.max(1 - np.abs(diag) ** 2)))
        exp = np.where(TARGET[idx], -1.0, 1.0)
        ph = diag * exp
        if gphase is None:
            gphase = ph[0] / abs(ph[0])
        worst = max(worst, float(np.max(np.abs(ph - gphase))))
    return {"passed": bool(worst < tol and leak < tol), "max_phase_err": worst, "max_leak": leak}

def notebook_check(source, seeds=3, rng=None):
    """Grader-style check: random product-phase states, full statevector."""
    width, gates = parse_u3cx(source)
    rng = rng or np.random.default_rng()
    basis = np.arange(4096)
    tp = np.where(TARGET, -1.0, 1.0)
    errs = []; g0 = None
    for _ in range(seeds):
        phases = rng.uniform(-np.pi, np.pi, 12)
        bp = np.zeros(4096)
        for q, p in enumerate(phases):
            bp += ((basis >> q) & 1) * p
        psi = np.zeros((1, 1 << width), dtype=np.complex128)
        psi[0, :4096] = np.exp(1j * bp) / 64
        out = simulate(width, gates, psi)[0]
        expv = np.zeros(1 << width, dtype=np.complex128); expv[:4096] = np.exp(1j * bp) / 64 * tp
        if g0 is None:
            ov = np.vdot(expv, out); g0 = ov / abs(ov)
        errs.append(float(np.max(np.abs(out - g0 * expv))))
    return max(errs)

if __name__ == "__main__":
    import sys
    s = open(sys.argv[1]).read()
    print(qasm_metrics(s))
    if len(sys.argv) > 2:
        print(verify_all(s))
        print("notebook-style err", notebook_check(s))
