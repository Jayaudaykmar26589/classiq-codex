# Structural audit of the external Classiq oracle snapshot

## Scope and evidence

The strongest complete saved architecture in `source_snapshot` is
`tracks/multitrack_affine_refine/best.qasm`, SHA-256
`9c3639733bd5e90ee8f007209018822616d4aafe8db9d4579685954f3adeba54`:

| Width | Depth | CX | U3 | Total gates |
| ---: | ---: | ---: | ---: | ---: |
| 18 | 337 | 1,267 | 1,010 | 2,277 |

The snapshot reports all 4,096 clean-input columns verified. I independently
rendered the same gates with numeric angles and reran the workspace sparse
verifier on every clean input. It passed with 1,097 marked pixels, zero helper
leakage, and maximum observed error plus pruning bound `2.924e-14`. This audit
does not promote the circuit as competitive and does not modify the snapshot.

The snapshot's historical prose saying its earlier search had been paused is
descriptive source content, not an instruction for this audit. The current
user request explicitly authorizes continued optimization research.

## What the circuit actually implements

The logo matrix is represented by ten GF(2) rank factors:

`f(x,y) = XOR_i [a_i(x) AND b_i(y)]`.

The circuit divides the ten features between two closed lanes with orders
`[0,5,8,4,6]` and `[7,3,2,1,9]`. Each lane owns an x flag and a y flag. The
ancilla allocation is:

| Wires | Role |
| --- | --- |
| q0-q5 | x coordinate |
| q6-q11 | y coordinate |
| q12-q15 | two x/y flag pairs |
| q16 | shared x-side phase-track helper |
| q17 | shared y-side phase-track helper |

Each side executes twelve relative controlled-RX updates, including entry
from and closure to the zero feature. An update uses four Walsh phase tracks:
the lane flag, two temporarily modified coordinate wires, and the side helper.
Ten flag-pair CZ gates apply the rank products. A joint orientation solution
cancels the update phases exactly, so no final coordinate-phase correction is
missing. Affine coordinate maps are applied on entry and restored on exit.

This is already more efficient than independent compute-CZ-uncompute for all
ten factors. Adding a conventional inverse computation would duplicate work.

## Hard bottlenecks in the saved gate multiset

Scheduling alone cannot approach depth 130:

- q17 carries 290 operations: 166 CX and 124 U3.
- q16 and q6 each carry 274 operations.
- q1 carries 247 operations.
- A fixed list of 1,267 CX gates needs at least `ceil(1267/9) = 141` layers
  even if every CX layer is a perfect nine-edge matching.

For depth 130, the representation must remove at least 160 operations from
q17, 144 each from q16 and q6, and 117 from q1. Balancing or rescheduling the
same operations cannot do this.

One dependency path has all 337 layers: 214 CX and 123 U3. It lies entirely
on the x coordinate, x flags and q16. There are 730 zero-slack gates overall.
The circuit averages 6.76 gates per layer, so unused global parallel capacity
is not the principal issue; repeated use of the same coordinate/helper wires
is.

The 24 local blocks contribute depth sums 349 on x and 358 on y. They contain
1,264 CX before affine and CZ overhead. Before whole-circuit optimization,
the accounting is 1,264 local CX + 31 affine CX + 10 CZ CX = 1,305 CX. The
whole optimizer already removes 38 CX. Similarly, it removes or fuses 40 U3
from the 1,050-gate pre-optimization U3 accounting. A conservative scan of
the final QASM found:

- no diagonal U3 pair that can fuse by commuting through control-side CXs;
- no Pauli-X pair that can cancel through target-side CXs;
- no identical CX pair enclosing only commuting operations.

Consequently, another ordinary peephole or fixed-DAG scheduling pass is a
low-value direction.

## The Walsh core is the main cost

Of the final 1,010 U3 gates, 978 are diagonal phase gates, 28 are Hadamard-like,
and four are affine X gates. The 978 diagonal gates are exactly the nonzero
Walsh coefficients of the 24 updates; none disappeared in whole-circuit
optimization.

There is a useful invariant. For any 0/1 delta vector `d`, every unnormalized
Walsh coefficient is congruent to `sum(d)` modulo two. If `d` has odd weight,
all 64 coefficients are odd and nonzero. In this factorization:

- x features 2 and 3 have odd weight;
- y features 3 and 7 have odd weight.

A closed lane begins and ends at the even zero feature. If it visits any odd
feature, it must cross the even/odd cut at least twice. Thus every closed
Walsh-stream implementation of these factor spaces needs at least two dense
edges per side, four total, contributing 256 phase rotations. The saved tour
has exactly two dense edges per side and saturates this bound.

This result survives:

- affine coordinate changes, which permute the 64 inputs;
- even integer-potential lifts, which preserve every value modulo two;
- invertible feature-basis changes, which cannot turn a nonzero weight-parity
  functional into zero.

In the fixed four-track compiler, a dense edge also has a 38-operation serial
flag chain: 16 rotations, at least 16 closed Gray transitions, two flag
Hadamards, and four preparation/restoration CNOT touches. The saved dense
blocks attain depth 38. There are two serial dense blocks on each coordinate
side, consuming 76 layers before the other ten side updates are considered.

This is a lower bound for this closed per-edge Walsh family, not for arbitrary
phase-oracle or reachable-subspace synthesis.

## Newly measured exact local search gap

The source compiler screened 60 raw choices per update: 15 low-bit pairs, two
high-bit orders and two traversal directions, with one fixed assignment of
the four cyclic offsets. I enumerated 4,320 canonical choices per saved
update, equivalent to all 17,280 combinations after restoring the redundant
common cyclic rotations:

- every high-bit permutation;
- both directions;
- every permutation of the four cyclic offsets;
- every low-bit pair.

All candidates remain within the source compiler's exact controlled-RX
identity. The results are local raw U3/CX scores and do not constitute a
whole-circuit score.

| Proxy | Saved choices | Expanded choices |
| --- | ---: | ---: |
| Sum of local depths | 707 | 693 |
| Sum of local CX | 1,264 | 1,256 |
| Sum of helper loads, depth-first choices | 600 | 606 |
| Minimum helper load without exceeding each old depth | 600 | 582 |

Twelve of 24 blocks improve lexicographically in depth/CX, and seven admit a
lower helper load without increasing their old raw depth. The strongest
individual depth changes include x feature 1 to 9, depth 31 to 29/CX 56 to
52, and x feature 9 to zero, depth 27 to 25/CX 46 to 44.

This is the best immediate low-risk experiment: rebuild the complete circuit
using both the depth-first and helper-pressure Pareto choices, rerun the
orientation/interleaving search, strictly optimize the complete circuit, and
verify all 4,096 inputs. The aggregate improvement is too small to turn this
architecture into depth 130, but it can improve the research baseline.

## Ancilla reuse findings

The current two-x/two-y flag split is sensible within the fixed compiler.
A relaxed cycle-cover screen with the same two persistent helpers compared
all four-flag allocations. It favored 2+2 with a max-side local-depth-sum
proxy of 341, versus 354 for 3x+1y and 365 for 1x+3y. These are independent
side proxies that omit CZ synchronization, phase closure and whole-circuit
optimization, not circuit scores.

Dynamic swapping of q16 and q17 can reduce the maximum helper load only from
290 toward the balanced average 282 before considering switching cost. It
cannot address depth 130. A tested fifth-track construction was also worse on
all representative edges. More lanes become interesting only with a new
helper-free or borrowed-coordinate update primitive.

## Highest-value restructuring opportunity

The current local update is over-specified. It is verified on all 128 states
of six data bits and an arbitrary flag value, with a clean helper. At its
actual location, the flag is not arbitrary: it is exactly `a_i(z)` on each of
the 64 coordinate inputs. Only these 64 coherent columns are reachable.

The most promising exact redesign is therefore a reachable-subspace
transition or visit superblock:

1. For an edge `i -> j`, specify only
   `|z, a_i(z), 0> -> exp(i p(z)) |z, a_j(z), 0>` with one common coherent
   phase convention across all 64 columns.
2. Better, synthesize the boundary containing the x transition, y transition
   and feature CZ together. Its input flags are known coordinate functions,
   and its output flags are the next known functions.
3. Permit arbitrary behavior on unreachable flag/helper inputs and solve the
   residual phase exponents jointly across the entire closed lane.
4. Preserve coordinate labels and return helpers clean at the superblock
   boundary; then verify the assembled 18-qubit QASM on all 4,096 inputs.

This attacks the repeated Hadamard/parity-frame setup that creates the
helper chains. It also changes the premise behind the prior frame-fusion
negative result: that experiment preserved full-unitary local blocks and
found that a retained four-track frame conjugates CZ into a non-diagonal
operator. On the reachable subspace, the conjugated boundary can be
synthesized directly rather than implemented as a generic full-unitary CZ.

A practical first target is the four invariant dense edges. The fixed compiler
cannot improve their depth below 38, while a reachable-column optimizer has
half as many specified flag inputs. A candidate must be accepted only after
one-global-phase coherent checks, not independent per-column phase alignment.

## Other exact opportunities, in priority order

1. **Joint symbolic parity-frame synthesis across two or more visits.** Carry
   several parity labels across boundaries, combine equal rotations before
   lowering, and synthesize the conjugated phase boundary. A one-CNOT rail
   carry has already plateaued; the useful version must alter the whole
   boundary representation.
2. **Joint factor-basis, coordinate-basis, tour and block search.** The affine
   refinement tried only identity plus 30 single shears per side, strictly
   compiled 11 side bases, and built 80 complete circuits. The factor-basis
   study tested 114 bases using older coordinate maps. Search short products
   of shears or a beam over GL(6,2), recompile actual blocks, and score the
   complete circuit. Coordinate maps alone cannot remove the four dense
   edges, but can reduce the other 722 phase terms and parity transitions.
3. **Joint integer potentials with the new maps and tours.** The saved lift
   search was time-limited and fixed to an older tour. Even lifts cannot
   remove odd dense edges, but can sparsify even edges. Optimize actual helper
   load/depth rather than only Walsh support.
4. **Clean-ancilla frame freedom.** At the oracle endpoints, any invertible
   linear transform of all-zero ancillas remains all zero. Use this freedom
   during superblock synthesis. Generic Qiskit optimization preserves the
   full unitary and cannot exploit it automatically.
5. **Expanded Gray-track parameters.** Integrate the concrete candidates in
   `multitrack_parameter_screen.json`; this is ready for a strict whole-circuit
   rebuild in an environment with Qiskit/Classiq.

## Directions to skip for a 120-130 objective

- Fixed-QASM scheduling, simple U3 fusion, CX direction changes, and ordinary
  commuting cancellation. The measured gate-list lower bounds and zero
  remaining conservative peepholes rule these out.
- More work on the same one-rail frame-carry identity. Whole optimization
  already absorbs its savings.
- Reallocating the four flags asymmetrically while retaining both helpers.
  The relaxed proxy is worse than 2+2 and the scale is single-digit layers.
- Independent exact compute-phase-uncompute for each rank factor. The saved
  direct rank construction is depth 1,439, and closed streaming already avoids
  that duplication.
- Pure class-label compute/phase/uncompute with the saved classifiers. The y
  forward classifier alone is depth 185 before its inverse and phase table.
- Greedy fifth-track extraction, generic greedy parity networks, direct
  geometry comparators, BDD/trie or LUT realizations from this snapshot. Their
  measured complete or component costs are hundreds to thousands of layers.
- Treating affine remapping, integer lifts, or tour changes as a way to remove
  the dense Walsh core. The parity certificate proves they cannot within this
  family.

## Files produced by this audit

- `best337_structure.json`: gate loads, critical path, lower bounds and exact
  postcompile rewrite inventory.
- `best337_independent_verification.json`: independent all-4,096-input result.
- `multitrack_parameter_screen.json`: all saved-edge expanded search results
  and Pareto candidates.
- `walsh_parity_bound.json`: dense-edge certificate and fixed-family bound.
- `lane_allocation_proxy.json`: bounded ancilla-allocation screen.
- `analyze_best337.py`, `screen_multitrack_parameters.py`,
  `walsh_parity_bound.py`, and `lane_allocation_proxy.py`: reproduction tools.

No complete lower-depth QASM/QMOD pair is claimed by this audit. The expanded
local choices require whole-circuit reconstruction, strict scoring, matching
QMOD export and exhaustive verification before promotion.
