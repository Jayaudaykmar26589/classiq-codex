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

## 7. Third round: controlled architecture search (plateau protocol)

This round follows a fixed protocol:

- **Scoring.** Every candidate is scored by the notebook's `qasm_metrics` on native u3/cx QASM, plus an exact all-4096 verifier. The ranking key is S = 10^6·depth + CX.
- **Plateau rule.** A family that gets three candidates without a depth improvement is closed. CX gains at equal depth do not reset the counter.
- **Tabu list.** A tabu list records why each closed family failed.

The tools are in `arch_search/`: `score.py` (scorer with longest-path report), `results.csv` (every candidate), `corner.py` and `rankbasis.py`.

**Measured structure** (matches the independent analysis): 1097 pixels, 68 corners of the mixed difference Δxy f, 19 distinct x-thresholds and 20 y-thresholds, each threshold in at most 4 corners. GF(2) rank is 10 for both the corner matrix C and the logo.

| id | Family | Valid | W | Depth | CX | Note |
|---|---|---|---|---|---|---|
| E00 | separable encoder + kernel (incumbent) | yes | 18 | **176** | 421 | critical path: q12–q14 (x-side helpers) carry 164 of 176 gates |
| C1 | rank-10, interval basis, compute–CZ–uncompute per term | yes | 18 | 1094 | 1378 | each term 61–157 layers |
| C2 | rank-10, lane over a GL(10,2)-searched basis | screened out | – | – | – | differences between lane states are as complex as the factors (proxy 49.9 vs 42.1) |
| C3 | corner + comparator kernel (x_low thresholds in one phase kernel) | yes | 60 | 413 | 700 | exact, but only on 60 wires |
| F1 | BQSKit 3-qubit partition + LEAP resynthesis of E00 | yes | 18 | 176 | 421 | identical circuit returned |

**Why the corner/rank family plateaus (type D/C, ancilla-limited serialization).**

- Rank 10 forces at least 10 separate x-flag/y-flag products.
- Every factor, in any basis found (a GL(10,2) anneal over 30k moves), has algebraic degree 4–6. That means at least 3–5 ANDs at AND-depth 3.
- Exact narrow-control XAGs (control support ≤ 2) give 21–34 layers per flag compute.
- On 18 wires a degree-5/6 flag needs 4–5 live wires, so terms cannot overlap. Some need staging (compute, copy, uncompute), which is where 61–157 layers per term come from.
- No basis change removes the ≥ 10 serial compute/uncompute steps.

**Tabu (do not retry without new evidence):**

- Generic Walsh synthesis (4095 of 4095 terms).
- Raw ANF (886 monomials, degree 12).
- Closed Walsh-update lanes (the 337 family).
- Affine-product encoders for fixed 4-bit class codes (earlier sessions).
- Rank-10 compute–CZ–uncompute (C1).
- Rank-10 lanes (C2).
- Flag-based comparator hybrids (C3, S3 on 49 wires).
- XAGs with wide affine controls: 28–65 CNOTs per 5-AND flag, so control support is always capped at 2.
- Exact SAT for in-place lanes beyond 3 gates.

**Batch D/F follow-up (same round).**

- Hybrid-K2 with every flag narrow (control support ≤ 2) is still depth 313 on 60 wires.
  - Each degree-5/6 flag costs 27–38 layers to compute: 3 AND levels at about 7 layers each (relative-phase Toffoli), plus control-forming and gather CNOTs. Every compute/uncompute pair therefore costs about 60 layers.
  - The kernel features chain Y5 → m → G is 5 AND levels deep.
  - So this family cannot reach 110–115, and 18 wires only adds pebbling overhead.
- In-place lanes: the annealer found an exact 6+2-wire lane that makes the disc code W affine (10 ANDs, level 4). The lanes for A,B (best 1 wrong bit) and for X_R,X_E (best 2 wrong bits) did not close.
- BQSKit 3-qubit resynthesis of E00 returned the identical circuit.

**Later attempts (same round).**

- **F2 (BQSKit, 4-qubit blocks).** Returned the identical 176/421 circuit. Block resynthesis of E00 is exhausted.
- **Separable 4-bit class codes.** The best code pair gives an 8-bit class kernel with only 32 phase terms (LP estimate; angles ±π/4, ±π/8). The in-place encoders, however, stay 14–16 bits wrong (6+3 wires, 28 ops). This reproduces the earlier sessions' encoder barrier.
- **Joint (x_hi, y) in-place lane for the block-kernel features.** Target: G, κ, V, O over 512 patterns on 9+5 wires, which would make the whole logo a single x_low kernel at an estimated depth of about 115. Best result is 50 wrong bits of about 1300 cared bits at 62 ops; not exact. Tools: `jlane.c` and `jlane_run.py` (scratchpad).
- **Notebook definition check.** The small disc (x−55)²+(y−41)² ≤ 42 spans [49,61] on rows 39–43. So the bar is only [26,49]×[39,43], and the right end of the bar belongs to the disc. A simplified hybrid-K3 formulation was verified exact.

## 8. Fourth round: paired-bilinear lanes, permutation kernels, exact rescheduling

No circuit below 176 was found this round. The deliverable is still `best_verified_depth176_cx421.{qasm,qmod}`. Tools are in `arch_search/round4/`, and the rows are G1–G3 and L1 in `arch_search/results.csv`.

**Paired-bilinear decomposition (S2 family).**

- `s2_natural_decomposition.py` gives an exact 6-term form, f = Σ X_j(x, y5)·Y_j(y) (0 mismatches). R1 is one term. The five C2 annuli are paired with the R2/C1 layers.
- Half-space degrees (`halves.py`):
  - Every nonzero x-function in the lower column space has degree 5–6.
  - The upper x-space is mostly degree 5–6.
  - So every x-lane needs AND-depth ≥ 3.
- **Liveness bound.** A lane must stay injective. It therefore needs (number of live flags) + ⌈log2(largest class of equal flag values)⌉ modifiable wires.
  - With all 6 flags live, that is 6+4 = 10 wires on the y side and 6+5 = 11 on the x side, which is more than 18. A single block is impossible.
  - 3-term blocks sit exactly at the 18-wire limit.
- **Lane search.** `lanex.c` is new: annealed prefix plus an exact final AND level, found by quotient-space linear algebra.
  - With y5 read-only, the single flag [29,53] needs AND-depth 5 at 2 ancillas. It was not found at depth 3–4 with 3 ancillas.
  - 3-flag y blocks stay 7–11 bits wrong at depth 3–4.
  - This agrees with the earlier sessions' S2 negatives.

**Permutation-only kernels are impossible.** Take any bijective re-encoding of x and y with no ancilla. The logo weight 1097 is odd, so every Walsh coefficient is ≡ 2 (mod 4) and the phase polynomial always needs 4095 parities. An SA over 64×64 permutations confirmed this. Any kernel must use ancilla-extended features.

**Walsh hybrids are dense.** Each paired flag has a Walsh support of 32–128. Keeping one side as features and expanding the other side in parities costs about 450 parity rotations for the six terms.

**Exact rescheduling of E00 (`satsched.py`, `conflicts.py`).**

- The commutation-relaxed critical path is exactly 175.
- At T=175 the window analysis pins two commuting CX pairs to the same wire and layer:
  - the q14 fan-out to q10/q16 at layer 81;
  - the q15 fan-out to q10/q16 at layer 87.
- Both sit on the q10 chain, which alternates u3 and CX from layer 74 to 88 with zero slack.
- The fan-out rewrite CX(h→o)·CX(c→h)·CX(h→o) costs +2 CX and makes the 175 window infeasible, because the hub wires are tight too.
- 254 gates have zero slack at T=175. Depth 174 is excluded by dependencies alone.

## 9. Depth 175 by local changes to E00: closed, with an exact explanation

Tools (all in `arch_search/round4/`): `scan.py`, `whatif.py`, `paths.py`, `downset.py`, `refit.py`, `classmap.py`, `bq3.py`, and `finalize.py` (SAT reschedule, QASM/QMOD export, all-4096 verification). Results are rows L2–L5.

**Unlock scan.** At T=175, 254 gates have zero slack. Each was removed in turn and the exact schedule re-solved. Only these removals make 175 feasible:

- any gate of the spine prefix, gates 49–122 (layers 2–27, running q17 → q13 → q12 → q14 → q1 → q14);
- CX 592 (layer 124);
- CX 732 (layer 156).

**The prefix is already minimal.** The down-set window D(73) maps every classical input to a single basis state. With a = x4⊕y5 and b = x1⊕x2 it computes:

- q17 = b·¬a
- q13 = q17·x5
- a linear phase (−1)^(a⊕x5)

A clean AND needs 3 CX; a 2-CX circuit cannot give AND even up to phase. With a ready only at layer 2 (after CX(11→4)), q17 cannot finish before layer 7, and no 6-layer q17 sequence reproduces the states (residual 2−√2).

**Window re-fits fail.** Delete one spine u3 inside D(105) (11 wires, 128 inputs), then re-fit all 25 remaining u3s with analytic gradients so the window's outputs match exactly up to a global phase. The best losses are 0.050–0.146 and do not change across restarts, so this is a real obstruction rather than a bad local minimum.

**Block resynthesis fails.** The 3-qubit blocks around CX 592 (q17, q12, q8) and CX 732 (q12, q3, q15) were searched exhaustively over 3- and 4-slot templates with BQSKit instantiation. Each slot is a CX on one of 6 ordered pairs with a u3 on the idle qubit, or a full u3 layer, and boundary u3s are free. No exact equivalent exists. The original 5-slot structures are recovered to 2e-8, which validates the search.

**Conclusion.** Without changing the architecture, E00 cannot reach 175 by rescheduling or by single-window resynthesis on up to 3 qubits. This agrees with the earlier session's "one conflict left at 175".

## 10. Staircase-comparator reformulation (new exact identity; encoders not found)

Tools are in `arch_search/round5/`; the rows are G4–G5.

**Identity (verified exact, 0/4096; `ferrers.py`).**

- Swap the empty rows 60–63 with rows 28–31 in place, using one gate: y5 ^= y4·y3·y2.
- After the swap, the row patterns in each y-half are nested (a Ferrers diagram).
- The whole logo is then a single comparison, f(x, y) = [ ℓ(y′) ≤ λ(x, y5′) ], where:
  - ℓ is the row level: 1–5 or empty;
  - λ is the column level: 0–5, and depends on the half.
- This replaces the rank-10 sum with one comparator between two 3-bit level codes.

**Measured costs.**

- *Kernel* (`kern6v.py`): the best placement of levels in code space is numeric order, x codes [0,0,0,1,2,3,4,5] and y codes [1,2,3,4,5,5,∅,∅]. It gives a 6-bit phase polynomial with 40 rotations.
- *Capacity:* the in-place fiber limits need 2 ancillas on the x side and 1 on the y side. That leaves 3 ancillas spare, so this reformulation is not wire-limited.
- *Code-bit degree* (`lc2.py`): best found is 5–7 on the x side (7 input variables including the half bit) and 4–5 on the y side. The encoders therefore need AND-depth 3; the hoped-for depth 2 is ruled out.
- *In-place encoders* (`lanelev.c`, a lane annealer whose cost is level consistency on designated code wires): at AND-depth 4 with 3 code ancillas per side, the best is 7 of 64 points wrong on the y side and 13 of 128 on the x side. Not exact.

**Refined (non-class-constant) separable codes** (`refcode.py`, `joint.py`). Codes that may split a class across several values break the degree-19 barrier: 5-bit codes reach degree 4 on both axes. But the 10-bit kernel then becomes dense: 136 ANF terms in the best joint search, up to degree 10.

**Status.** If exact encoders existed, the depth would project to about 100–140. Every family now fails on the same missing component: exact multi-output in-place encoders of degree ≥ 5 within the 18-wire budget.

**Round 5b: encoder synthesis for the staircase comparator (row G6).**

- *Assembler* (`assemble_sc.py`): chains the swap, the two encoders (relative-phase Toffolis, exactly mirrored) and the exact 6-bit phase-polynomial kernel. Its parts were unit-tested as follows:
  - kernel phases on single-point test functions;
  - relative-phase Toffoli and swap permutations;
  - diagonality of the mirrored block.
- *Deeper lanes* (AND-depth 5–6, 36–44 ops): still 7–8 of 64 points wrong on y and 9–11 of 128 on x.
- *Free code wires plus pair-collision cost* (`lanelev2.c`): 18–23 colliding pairs on y and about 107 on x. No improvement.
- *Exact SAT* (`sat_enc.py`, level consistency as pairwise code inequality):
  - Proving 5 gates insufficient took 573 s (UNSAT).
  - Real encoders need 10 or more gates, which is intractable at this rate.
  - This agrees with the earlier sessions' finding that exact in-place lane SAT is intractable.
- *Status:* the staircase comparator stays unbuilt. Its encoders are the bottleneck, exactly as in every other family.

**Round 5c: out-of-place feature chains (row G8, `featchain.py`).**

- *Setup:* the encoder computes AND features into ancillas and leaves the inputs untouched, so reversibility is automatic.
- *Acceptance test:* exact linear algebra. There must be a subspace of the feature space, of codimension 3, that avoids every difference vector between inputs of different levels.
- *Result:* the searches stalled at dimension 3 of 6 (y, 3 ANDs), 4 of 7 (y, 4 ANDs) and 3 of 7 (x).
- *Why:* multiplicative complexity is at least degree − 1, so k kept ANDs give degree at most k + 1. The level codes need degree 5 (y) and 7 (x), which means at least 4 + 6 = 10 live AND results. Only 6 ancillas exist.
- *Consequence:* the staircase comparator on 18 wires needs genuinely in-place encoders (or Bennett staging, which adds depth), and those encoders have not been found.

**Round 5d: more literature and one untried tool.**

- *Literature (web search).* I looked for work on the recurring blocker, exact in-place multi-output synthesis:
  - exact Toffoli-network synthesis and model-checking synthesis: practical only for about 4–5 lines;
  - ancilla-free synthesis via sorting;
  - reversible pebbling (Meuli et al.; caterpillar) and Reqomp: these trade ancillas for recomputation depth;
  - a September 2026 phase-based comparator (arXiv 2609.25262): its readout is a biased coin that needs repeated shots, so it is probabilistic and not an exact oracle.
  - None of these gives exact in-place encoders at 8–11 lines.
- *ZX rewriting of E00 (pyzx, row L6):* full_reduce gives depth 731–756; teleport_reduce gives 246–253. Both are worse than 176.
