"""Feature trace of a u3/cx oracle: after each gate, find wires that are classical on every input
(all basis states in the support agree on that bit) and record the Boolean function they hold
whenever it changes.  Functions are identified as affine forms of inputs where possible, else
by their ANF over the inputs (degree, #monomials)."""
import sys, math, json
import numpy as np
sys.path.insert(0, '/home/user/classiq-codex/arch_search')
from grader import parse_u3cx, qasm_metrics

def u3mat(th, ph, la):
    c, s = math.cos(th / 2), math.sin(th / 2)
    return (c, -np.exp(1j * la) * s, np.exp(1j * ph) * s, np.exp(1j * (ph + la)) * c)

def anf(tt):
    a = tt.astype(np.uint8).copy(); n = 12; h = 1
    while h < 4096:
        a = a.reshape(-1, 2 * h); a[:, h:] ^= a[:, :h]; a = a.reshape(-1); h *= 2
    mons = np.nonzero(a)[0]
    deg = max((bin(m).count('1') for m in mons), default=0)
    return deg, len(mons), mons

NAMES = [f'x{i}' for i in range(6)] + [f'y{i}' for i in range(6)]
def describe(tt):
    deg, nm, mons = anf(tt)
    if deg <= 1:
        return 'aff:' + ('1+' if 0 in mons else '') + '+'.join(NAMES[(int(m)).bit_length() - 1] for m in mons if m)
    if nm <= 6:
        return f'deg{deg}:' + ' ^ '.join('*'.join(NAMES[b] for b in range(12) if (m >> b) & 1) or '1' for m in mons)
    return f'deg{deg}/{nm}mon'

if __name__ == '__main__':
    src = open(sys.argv[1]).read()
    W, gates = parse_u3cx(src)
    inp = np.arange(4096, dtype=np.int64); bas = inp.copy(); amp = np.ones(4096, complex)
    last = {w: None for w in range(W)}
    events = []
    for gi, g in enumerate(gates):
        if g[0] == 'cx':
            c, t = g[1], g[2]; bas = bas ^ (((bas >> c) & 1) << t); touched = [t]
        else:
            q = g[2]; a, b, cc, d = u3mat(*g[1]); bit = (bas >> q) & 1; b0 = bas & ~(1 << q)
            a0 = np.where(bit == 0, a, b) * amp; a1 = np.where(bit == 0, cc, d) * amp
            key = np.concatenate([(inp << 18) | b0, (inp << 18) | (b0 | (1 << q))]); val = np.concatenate([a0, a1])
            o = np.argsort(key, kind='stable'); key = key[o]; val = val[o]
            uk, st = np.unique(key, return_index=True); sv = np.add.reduceat(val, st); keep = np.abs(sv) > 1e-12
            uk = uk[keep]; sv = sv[keep]; inp = uk >> 18; bas = uk & ((1 << 18) - 1); amp = sv; touched = [q]
        for w in touched:
            bits = (bas >> w) & 1
            mn = np.full(4096, 2); mx = np.full(4096, -1)
            np.minimum.at(mn, inp, bits); np.maximum.at(mx, inp, bits)
            if np.all(mn == mx):
                tt = mn.astype(bool)
                key_ = tt.tobytes()
                if last[w] != key_:
                    last[w] = key_
                    events.append((gi, w, describe(tt)))
    for gi, w, desc in events:
        if w >= 12 or not desc.startswith('aff:') or True:
            print(f'{gi:4d} q{w:<2d} {desc}')
