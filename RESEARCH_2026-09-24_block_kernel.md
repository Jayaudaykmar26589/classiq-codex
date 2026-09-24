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

## 5. Second round: the leaderboard, and what the leader's numbers imply

**Leaderboard.** A public repo from another participant tracks the leaderboard in its notes
([4oeuhtns/classiq-challenge-2026](https://github.com/4oeuhtns/classiq-challenge-2026),
`findings-2026-09-15.md` and `findings-2026-09-17.md`):

| When | Entry | Depth | CX | Width |
|---|---|---|---|---|
| before 2026-09-15 | best public score | 137 | 561 | 18 |
| 2026-09-15 20:07 UTC | Boopathi R. | 129 | 614 | 18 |

This repo's 176/421 is therefore far from the top. That repo's own best is about depth 998,
so it offers no competitive technique. No public write-up of the leading method was found.

**What 129 / 614 implies.**

- 614 CX over 129 layers is 4.76 CX per layer, so nearly every wire works in nearly every
  layer. The other team derives a load imbalance of at most 1.9x, against about 30x for an
  AND tree built on a shared scratch pool.
- The GF(2) rank of the logo is 10 (checked here too). 614 CX over 10 rank terms is about
  61 CX per term. That matches roughly 5 relative-phase ANDs per flag, computed and
  uncomputed, for both flags of each term.
- At most about 0.86 relative-phase ANDs start per layer on 18 wires (3 wires each, about
  7 layers on the target). About 200 AND evaluations therefore cannot fit into 129 layers
  as pure Toffolis. Part of the CX budget must be dense parity-network (phase-polynomial)
  work, or the ANDs must run in place on the coordinate registers.

The most plausible reading is two in-place lanes, one on x and one on y, that expose rank
flags one after another. CZs fire between exposed flag pairs, and everything is mirrored.
The 176/421 circuit in this repo has the same lane shape. Its flag updates, however, are
dense 64-term Walsh updates rather than cheap AND updates, which is where its depth goes.

**Negative results measured this round.**

| Test | Result |
|---|---|
| Walsh support of the logo over its 12 raw bits | 4095 of 4095 terms: a raw phase polynomial is hopeless. |
| Walsh support of the row functions (A, D, Reg, T, bar, d1e) | Exact supports 39–63. |
| Same, with don't-cares minimized (tau, Vd0–2) | 45–48. Walsh-flag updates cost about 2x support. |
| Walsh support of the S3 features over the 9 block bits | G: 194. V bits: 167–511 before don't-care optimization. |
| Disc 1 in 2D-folded coordinates (x folded at 39.5, y folded at 19.5) | Dense (1023 of 1024). Threshold shapes are only sparse in the comparator form, where V is an explicit wire. |
| Distinct 8x8 block shapes in the logo | 21 up to reflection. Two blocks (disc-1 centre) are not monotone under any fold. |
| Re-optimizing the 176 circuit with a commutation-aware peephole scheduler | Still 176/421: there is no scheduling slack. |
| Single exact 6-bit flags in place (lane annealer, affine exposure) | [2,26], [38,42], A and D all embed with 2 scratch wires at 5–6 ANDs, AND depth 3–4. With 1 scratch they mostly fail. |
| Joint stages | tau+Vd gets within 1 bit (2–3 scratch). A+D+Reg stays about 9 bits off. |

**Budget arithmetic for S3.** S3 needs about 31 ANDs, so 62 AND evaluations, plus a 45-term
kernel. That is about 3x fewer ANDs than the inferred leader design, which gives it a
theoretical floor of about 70–90 layers. The blocker remains liveness at 18 wires, not AND
count.

## 6. Tools written this round (session scratchpad; not committed)

- `lanet`: a C annealer for in-place lane programs where each target only has to be exposed
  (in the affine span of the lane wires) at some time step, not all at once. This is the
  natural objective for streamed rank flags. On all 10 nested y-flags or all 10 x-flags,
  with 2–3 scratch wires and 24–28 ops, it stays 16–23 bits off. Longer programs (44 ops)
  are running.
- A Walsh-support and don't-care minimizer, and a 2D fold analyser.
