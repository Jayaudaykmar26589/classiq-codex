"""Merge consecutive single-qubit u3 gates per wire (exact), drop identities."""
import numpy as np, math
def m3(t, p, l):
    c, s = math.cos(t / 2), math.sin(t / 2)
    return np.array([[c, -np.exp(1j * l) * s], [np.exp(1j * p) * s, np.exp(1j * (p + l)) * c]])
def to_u3(M):
    # remove global phase so that M[0,0] is real >= 0
    a = M[0, 0]; ph = np.angle(a) if abs(a) > 1e-12 else np.angle(-M[0, 1])
    if abs(a) > 1e-12: M = M * np.exp(-1j * np.angle(a))
    else: M = M * np.exp(-1j * np.angle(-M[0, 1]))  # then M[0,1] = -|.|
    t = 2 * math.atan2(abs(M[1, 0]), abs(M[0, 0]))
    if abs(M[1, 0]) < 1e-12: p = 0.0; l = float(np.angle(M[1, 1]))
    elif abs(M[0, 0]) < 1e-12: p = float(np.angle(M[1, 0])); l = float(np.angle(-M[0, 1]))
    else: p = float(np.angle(M[1, 0])); l = float(np.angle(-M[0, 1]))
    return t, p, l
def fuse(seq):
    out = []; pend = {}
    def flush(q):
        if q in pend:
            M = pend.pop(q)
            if np.allclose(M / M[0, 0] if abs(M[0, 0]) > 1e-9 else M, np.eye(2), atol=1e-10) and abs(abs(M[0, 0]) - 1) < 1e-9: return
            out.append(('u3', q, None, to_u3(M)))
    for g in seq:
        if g[0] == 'cx':
            flush(g[1]); flush(g[2]); out.append(g)
        else:
            q = g[1]; M = m3(*g[3]); pend[q] = M @ pend[q] if q in pend else M
    for q in list(pend): flush(q)
    return out
