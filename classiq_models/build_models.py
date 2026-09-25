"""Build Classiq Qmod models for the new exact logo formulations and check each one classically on all 4096 pixels.

Run with the Classiq SDK (1.29.1):  python build_models.py
Writes <name>.qmod and <name>.synthesis_options.json next to this file.
"""
import json
from pathlib import Path
from classiq import *
from classiq.qmod.symbolic import pi, subscript

def logo_pixel(x, y):
    return ((2 <= x <= 26 and 29 <= y <= 53) or (26 <= x <= 49 and 39 <= y <= 43)
            or (x - 55) ** 2 + (y - 41) ** 2 <= 42 or (x - 40) ** 2 + (y - 19) ** 2 <= 72)

# ---------- staircase tables (row swap y5 ^= y4 y3 y2 folded into the tables) ----------
def swap(y): return y ^ (32 if (y >> 2) & 7 == 7 else 0)
EMPTY = 7
def tables():
    lev = [0] * 64; lam = [[0, 0] for _ in range(64)]
    for h in (0, 1):
        ys = [yp for yp in range(64) if yp >> 5 == h]
        pats = {}
        for yp in ys:
            y = swap(yp)                      # swap is an involution
            pats.setdefault(tuple(int(logo_pixel(x, y)) for x in range(64)), []).append(yp)
        order = sorted(pats, key=lambda p: -sum(p))
        nonempty = [p for p in order if sum(p) > 0]
        for i, p in enumerate(order):
            for yp in pats[p]: lev[yp] = (i + 1) if sum(p) > 0 else EMPTY
        for x in range(64): lam[x][h] = sum(1 for p in nonempty if p[x])
    LY0 = [0] * 64; LY1 = [0] * 64
    for y in range(64):
        yp = swap(y); h = yp >> 5
        LY0[y] = lev[yp] if h == 0 else EMPTY
        LY1[y] = lev[yp] if h == 1 else EMPTY
    LX0 = [lam[x][0] for x in range(64)]; LX1 = [lam[x][1] for x in range(64)]
    return LY0, LY1, LX0, LX1
LY0, LY1, LX0, LX1 = tables()
def check_staircase():
    bad = sum(int((LY0[y] <= LX0[x]) or (LY1[y] <= LX1[x])) != int(logo_pixel(x, y)) for x in range(64) for y in range(64))
    both = sum(int(LY0[y] <= LX0[x]) & int(LY1[y] <= LX1[x]) for x in range(64) for y in range(64))
    return bad, both

# ---------- XOR of nested rectangles (greedy corner elimination) ----------
def xor_rectangles():
    import numpy as np
    F = np.array([[int(logo_pixel(x, y)) for y in range(64)] for x in range(64)])
    # decompose: each maximal run structure -> use the 2D difference (corner) representation, then pair corners into rectangles
    D = F.copy()
    D[1:, :] ^= F[:-1, :]; D2 = D.copy(); D2[:, 1:] ^= D[:, :-1]
    corners = [(x, y) for x in range(64) for y in range(64) if D2[x, y]]
    # rectangle [x0,x1)x[y0,y1) contributes corners (x0,y0),(x1,y0),(x0,y1),(x1,y1); greedy: take top-left corner, find partner
    rects = []; C = set(corners)
    while C:
        x0, y0 = min(C)
        # choose x1: next corner on row y0 to the right; y1: next corner on column x0 upward
        xs = sorted(x for (x, y) in C if y == y0 and x > x0); ys = sorted(y for (x, y) in C if x == x0 and y > y0)
        x1 = xs[0] if xs else 64; y1 = ys[0] if ys else 64
        rects.append((x0, x1 - 1, y0, y1 - 1))
        for c in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            if c[0] < 64 and c[1] < 64: C ^= {c}
    G = np.zeros((64, 64), int)
    for x0, x1, y0, y1 in rects: G[x0:x1 + 1, y0:y1 + 1] ^= 1
    return rects, int((G != F).sum())

# ---------- Qmod models ----------
def harness(oracle):
    @qfunc
    def main(x: Output[QNum[6]], y: Output[QNum[6]]) -> None:
        allocate(x); allocate(y)
        hadamard_transform(x); hadamard_transform(y)
        oracle(x, y)
    return main

@qperm
def staircase_two_lut(x: Const[QNum[6]], y: Const[QNum[6]]) -> None:
    control(subscript(LY0, y) <= subscript(LX0, x), lambda: phase(pi))
    control(subscript(LY1, y) <= subscript(LX1, x), lambda: phase(pi))

@qperm
def staircase_or_lut(x: Const[QNum[6]], y: Const[QNum[6]]) -> None:
    control((subscript(LY0, y) <= subscript(LX0, x)) | (subscript(LY1, y) <= subscript(LX1, x)), lambda: phase(pi))

RECTS, RECT_BAD = xor_rectangles()
def _rng(v, a, b): return (v == a) if a == b else ((v >= a) & (v <= b))
@qperm
def xor_rectangles_oracle(x: Const[QNum[6]], y: Const[QNum[6]]) -> None:
    for x0, x1, y0, y1 in RECTS:
        control(_rng(x, x0, x1) & _rng(y, y0, y1), lambda: phase(pi))

if __name__ == '__main__':
    bad, both = check_staircase()
    print(f'staircase check: mismatches {bad}, overlapping terms {both}')
    print(f'xor-rectangles: {len(RECTS)} rectangles, mismatches {RECT_BAD}')
    assert bad == 0 and both == 0 and RECT_BAD == 0
    here = Path(__file__).parent
    opts = dict(constraints=Constraints(optimization_parameter='depth', max_width=18))
    for name, orc in (('staircase_two_lut', staircase_two_lut), ('staircase_or_lut', staircase_or_lut), ('xor_rectangles', xor_rectangles_oracle)):
        model = create_model(harness(orc), **opts)
        write_qmod(model, name, directory=str(here))
        print('wrote', name + '.qmod')
