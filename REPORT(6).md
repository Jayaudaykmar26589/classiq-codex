# Joint nonlinear state and phase co-synthesis: measured outcome

## Decision

**Keep the 177-layer / 429-CX reference.** This attempt implemented the requested
joint search but did not improve the protected score or reach depth 150.

| Circuit | Local U3/CX depth | CX | U3 | Width |
|---|---:|---:|---:|---:|
| Protected best |177|429|391|18|
| Original source used for semantic interfaces |181|426|395|18|
| First newly generated complete region replacement |203|454|429|18|
| Best selected joint nonlinear/oracle-phase region |199|446|415|18|

The best partial-circuit metric is never called a whole-oracle result. The 203 to
199 decrease concerns new experimental candidates only, not the protected best.

## What actually changed

The old phase-backbone experiment preserved its nonlinear data path and chose
phase actions on existing recovered snapshots. The new regional compiler removes
original operations `[0,91)` and rebuilds both the nonlinear input encoding and
that region's phase program. The original suffix is kept before native
whole-circuit algebraic cleanup and scheduling.

New computations can modify data wires as well as the six helpers. They include
`h ^= P*Q XOR L`, implemented with an invertible CNOT/X frame, a specific
relative-phase AND, and restoration of the temporary control frame. They also
include two-product detours:

    delta = p XOR q XOR L
    h ^= p
    h ^= q XOR L

The first update need not place any final required output on h. The planner
maintains all live truth functions and accumulated even-Z8 phase bitplanes. Paths
with equal Boolean states but different nonconstant phases are not silently
identified. Bounded beam quotas preserve some phase diversity; this is not
exhaustive state-space search or a proven dominance algorithm.

For every retained encoding trajectory, native forward/inverse and control-order
gauges are tested; the phase problem is solved again on that trajectory's actual
snapshot functions. The final coupled stage also changes the X/Y merge order and
rebuilds the first actual oracle phase, not just independent side corrections.

The selected path has 55 snapshots, 12 nonlinear updates, three data-target
nonlinear updates, five nonlinear updates whose result differs from the final
required value on that wire, and 30 diagonal phase actions. Those are actual
constructed operations, not a permission-only prompt change.

## Correctness equation

Let S_t(z) be the new encoded labels and Phi_new(z) their accumulated phase in
units of pi/4. The new phase dictionary contains functions m_l(S_t(z)). The solver
checks, for all 4096 z:

    Phi_new(z) + sum_l k_l*m_l(S_t_l(z)) = Phi_original_cut91(z) + c (mod 8).

The new endpoint labels match the recovered cut91 labels; c is one
input-independent constant (2 for the selected symbolic construction). All
physical basis-conversion gates are emitted and counted. Relative phases are not
assumed harmless merely because helpers are restored.

## Search accounting

Main logged work:

- 18 phase-aware nonlinear trajectory beam calls.
- 1764 side phase-cover attempts, not full-oracle evaluations.
- 588 complete-oracle evaluations associated with those retained side trials.
- 60 coupled-region phase-lift attempts: 29 produced complete emitted candidates;
  31 lifts returned no solution. The latter are not infeasibility certificates.
- Thus 617 logged main complete-oracle candidate evaluations, including repeats.
- 120 total heuristic scheduling trials across the retained assemblies (including
  32 on the final coupled-region candidate). No exact MILP scheduling optimum is
  claimed for the selected output.
- Preliminary work: 8 planner calls, 90 side phase-cover attempts, and one initial
  complete paired assembly, recorded separately.

The code also compiled selected assemblies for export/reproduction. These are not
presented as distinct search architectures. The selected result is independently
reproducible; the entire bounded search is not a global optimality certificate.

An early two-product proposal generator used an incomplete, noncanonical quotient
reduction. Returned witnesses remained exact, but valid matches could be missed.
The final public module uses a complete quotient reducer, with explicit linearity
and witness tests. As-run versions and logs distinguish these searches. This fix
did not establish a new performance improvement.

## Verification

The actual 199/446 exported QASM passed all 4096 clean-input basis columns with one
common global phase. Sparse amplitudes at most 1e-14 were pruned and discarded L2
norms accumulated per input. Maximum measured component error plus that truncation
bound was **8.468582157692425e-14**, below 1e-10. The bound does not formally enclose
floating-point roundoff.

Six additional unpruned statevector tests inspected all 262144 output amplitudes
per input. Maximum amplitude error: **1.3558364312105789e-14**. The protected 177
reference also received six fresh unpruned regressions, with maximum error
3.381877313207236e-13; its earlier exhaustive report is not counted as newly run.

Symbolic checks cover every recovered coordinate label and new phase identity,
conditional on prior numerical recovery of the original local-basis interfaces.
This is not a machine-checked algebraic proof of arbitrary decimal gate streams.

Expanded QMOD and QASM bodies correspond locally; main has no preparation
Hadamards. No Classiq SDK parsing, remote synthesis, official score, live rank,
or submission is claimed.

## Interpretation

The requested joint mutation is implemented. The new nonlinear trajectory and the
phase actions both change, and their joint correctness is checked. However, this
bounded primitive library generates a more expensive region than the highly
optimized original. Changing the search formulation did not itself produce a
competitive depth reduction.

The implementation still fixes the input/output boundary encoding of the chosen
region and preserves the rest of the nonlinear oracle. It is not a complete
unrestricted redesign of all 18-wire intermediate encodings. Failed bounded
searches do not show that a lower-depth joint architecture is impossible.

## Release validation

All 14 release tests passed. Three semantic recompilations produced byte-identical
QASM and identical 199/446/415 metrics. A fresh-directory CLI smoke search ran and
verified its unchanged 203-layer seed-derived result; that packaging smoke work
is recorded separately and excluded from the main search counts.

A separately extracted archive passed all 14 tests and reproduced the identical
199/446/415 artifact. The corresponding logs are included.
