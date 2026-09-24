# Block-kernel reformulation (2026-09-24)

This session did not produce a submission-grade circuit below depth 176. The deliverable is
still `best_verified_depth176_cx421.{qasm,qmod}`, which was re-verified: all 4096 inputs pass,
and the QMOD body matches the QASM gate for gate.

It did produce an exact single-kernel formulation of the logo. That formulation builds and
verifies end to end, but only on 49 wires. This note records it and the blocker, so the next
attempt can start from here.

## 1. Every 8-pixel block is a prefix or a suffix

Split x into `hi = (x5,x4,x3)` and `low = (x2,x1,x0)`. Of the 512 (row, block) segments of the
logo, 337 are empty, 84 are full, 46 are prefixes and 45 are suffixes. None is anything else.
So the whole logo is one gated comparator:

```
f(x,y) = G * [ e + k + V <= 7 ],   e_i = x_i XOR O   (i = 0..2)
```

Here G, k, V (3 bits) and O are functions of the 9 block bits `(x3,x4,x5,y)`. The rectangles
are handled by the same kernel, with no XOR of patches.

## 2. Formulation S3 (checked exact: 0 mismatches over all 4096 pixels)

Row functions of y:

- `A = [29,53]`
- `D = [11,27] u [35,47]`
- `Reg = D \ T`, where `T = [17,21] u [39,43]`
- `tau` separates Reg from T inside D; outside D it is a don't-care.
- `Vd`, the disc code: rows 11,27 -> 5; 12,26 -> 3; 13,14,24,25 -> 1; 15,16,22,23 -> 0;
  35,47 -> 5; 36,46 -> 3; 37,38,44,45 -> 2. It only matters on Reg.

Features:

```
t  = x5 & ~(x4^y5)      s  = x5 ^ t      t' = t & tau      Rg = D & tau      T = D ^ Rg
u  = (x5^x4) & ~(x3^x4)   (= hi3 XOR hi4)                   m' = x4 & s
G  = A ^ x5&(A^D) ^ s&Rg
k  = 1 ^ x3 ^ x4 ^ u&T        (kept in place on the x3 wire)
V0 = ~x5~x4~x3 ^ t'&Vd0 ^ x4x3&(t^t') ^ m'
V1 = t'&Vd1 ^ m'
V2 = ~x5 x4 x3 ^ ~x5&(u&T) ^ t'&Vd2 ^ m'
O  = ~x3 ^ m'
```

AND counts of the row functions found by exact SAT with operand support <= 3. The counts for A and D
match the degree lower bound, so those two are minimal:

| Row function | ANDs | AND depth |
|---|---|---|
| tau | 3 | 2 |
| D | 4 | |
| A | 5 | |
| Vd (3 bits) | 4 | 2 |

The x-side and product layer adds about 15 more ANDs.

**Kernel.** It has 45 phase terms: 22 ungated terms, the same 22 gated by G, and G itself. All
ungated terms have odd weight in the (e, k, V) basis. The walker kernel has depth 21 with 2 clean
spares, 33 with 1, and 34 with none. Of the (k, V) pairs, only 13 of 16 occur when G = 1 and only
4 occur when G = 0, so the kernel has unused don't-care freedom.

**End-to-end build.** On 49 wires (47 plus 2 kernel spares) the full circuit passes the exact
check, at depth 151 with 440 CX and 40 ANDs. Compute alone is depth 67; that is dominated by contention on control wires.

## 3. Why it does not fit 18 qubits

Kernel time needs 8 wires: e (3), k, V (3) and G. That leaves 6 ancillas: 4 feature
accumulators plus 2 temporaries. All intermediate values must then live in place on the
block wires (x4, x5, y0..y5).

- An in-place XAG compiler that tracks affine spans runs out of wires at the third AND.
- An annealer over in-place lane programs, with targets affine in the final wires, gets close
  on the tau + Vd stage (1 bit wrong) but stays about 9 bits wrong on the exact A, D, Reg stage.
- Mid-program uncompute (Bennett staging) costs about 4x the lane depth, which estimates
  above 176.

This matches the conclusion of the 2026-09-22 sessions about fold/comparator plans.

## 4. Open leads

- An exact kernel with 0 spares at depth <= 18 would free 2 wires. SAT on the 45-term parity
  network is only partly explored.
- Use the kernel don't-cares from section 2 to shrink the kernel.
- Search lane programs that expose row functions one after another instead of all at once,
  with x-controlled Toffolis writing into the accumulators.
- Use dirty-ancilla computing on the x_low wires, which stay idle until the kernel.
