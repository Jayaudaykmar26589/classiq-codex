"""List diagonal (theta~0) u3 gates of the incumbent that act on a wire in a definite basis state,
with the feature held and the angle; count how much of the phase is applied that way."""
import sys, math, numpy as np
sys.path.insert(0, '/home/user/classiq-codex/arch_search'); sys.path.insert(0, '.')
from grader import parse_u3cx
from e00_trace import u3mat, describe, anf
W, gates = parse_u3cx(open(sys.argv[1]).read())
inp = np.arange(4096, dtype=np.int64); bas = inp.copy(); amp = np.ones(4096, complex)
diag_cls = 0; diag_q = 0; nondiag = 0; rows = []
for gi, g in enumerate(gates):
    if g[0] == 'u3':
        th, ph, la = g[1]; q = g[2]
        bits = (bas >> q) & 1; mn = np.full(4096, 2); mx = np.full(4096, -1)
        np.minimum.at(mn, inp, bits); np.maximum.at(mx, inp, bits)
        classical = np.all(mn == mx)
        if abs(math.sin(th / 2)) < 1e-9:
            if classical: diag_cls += 1; rows.append((gi, q, round((ph + la) % (2 * math.pi), 4), describe(mn.astype(bool))))
            else: diag_q += 1
        else: nondiag += 1
    if g[0] == 'cx':
        c, t = g[1], g[2]; bas = bas ^ (((bas >> c) & 1) << t)
    else:
        q = g[2]; a, b, cc, d = u3mat(*g[1]); bit = (bas >> q) & 1; b0 = bas & ~(1 << q)
        a0 = np.where(bit == 0, a, b) * amp; a1 = np.where(bit == 0, cc, d) * amp
        key = np.concatenate([(inp << 18) | b0, (inp << 18) | (b0 | (1 << q))]); val = np.concatenate([a0, a1])
        o = np.argsort(key, kind='stable'); key = key[o]; val = val[o]
        uk, st = np.unique(key, return_index=True); sv = np.add.reduceat(val, st); keep = np.abs(sv) > 1e-12
        uk = uk[keep]; sv = sv[keep]; inp = uk >> 18; bas = uk & ((1 << 18) - 1); amp = sv
print('u3 total', diag_cls + diag_q + nondiag, 'diagonal on classical wire', diag_cls, 'diagonal on superposed wire', diag_q, 'non-diagonal', nondiag)
for r in rows: print(r)
