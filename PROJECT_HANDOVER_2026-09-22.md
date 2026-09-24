# Project Handover Document

**Generated:** 2026-09-22 (Asia/Kolkata)  
**Workspace:** `/Users/jayachandiranudayakumar/Desktop/Classiq-Codex`  
**Project state:** Active research; top-five target not yet achieved  
**Protected complete result:** `177 depth / 426 CX / 390 U3 / 18 qubits`  
**Best new partial result:** exact `47 depth / 77 CX / 64 U3 / 18 qubits` phase component, with no compatible exact encoder yet

This document is the authoritative continuation guide for a technically capable agent with no prior chat context. Read the distinction between **complete oracle**, **component**, **proxy**, and **invalid diagnostic** before using any metric in this repository.

## 1. Objective

### Original request

Implement an exact quantum phase oracle for the 64 by 64 Classiq logo and optimize it aggressively for competition ranking. The user wants a submission-ready QASM/QMOD pair that reaches at least the top five, ideally the top three, with circuit depth as the primary metric and CX count as the tie-breaker.

For six-bit coordinates `x` and `y`, the required Boolean mask is:

```python
def logo(x: int, y: int) -> bool:
    return (
        (2 <= x <= 26 and 29 <= y <= 53)
        or (26 <= x <= 49 and 39 <= y <= 43)
        or ((x - 55) ** 2 + (y - 41) ** 2 <= 42)
        or ((x - 40) ** 2 + (y - 19) ** 2 <= 72)
    )
```

The function is true on exactly 1,097 of the 4,096 coordinate pairs. The oracle must implement

```text
|x>|y>|000000>  ->  (-1)^logo(x,y) |x>|y>|000000>
```

up to one input-independent global phase.

### Hard scope and constraints

| Property | Required value |
|---|---|
| Coordinate register | `x = q[0:6]`, little-endian |
| Coordinate register | `y = q[6:12]`, little-endian |
| Clean helpers | `q[12:18]`, initially and finally zero |
| Declared width | **Exactly 18 qubits** |
| Native basis | `u3`, `cx` |
| Connectivity | All-to-all; `coupling_map=None` |
| Measurements/reset/initialization | Forbidden in the scored oracle |
| Final coordinates | Must equal input coordinates |
| Correctness domain | All 4,096 clean coordinate basis inputs |
| Objective | Lowest depth, then lowest CX count |
| Deliverables | Complete, matching `.qasm` and `.qmod` files |

### Current success criteria

The independently refreshed public leaderboard snapshot at `2026-09-22T08:57:48Z` is:

| Rank | Depth | CX | Width |
|---:|---:|---:|---:|
| 1 | 117 | 590 | 18 |
| 2 | 120 | 573 | 18 |
| 3 | 125 | 563 | 18 |
| 4 | 127 | 507 | 18 |
| 5 | 128 | 405 | 18 |

Therefore:

- A guaranteed top-five result needs depth at most 127, or depth 128 with CX below 405.
- A top-three result needs depth at most 124, or depth 125 with CX below 563.
- The earlier internal threshold `depth < 177`, `CX < 428`, `width = 18` is still useful as the first strict improvement milestone, but it is no longer enough for the current top five.
- Do not claim a leaderboard rank until the platform accepts and scores the uploaded artifact. Current scores are reproducible local scores.

### Assumptions

1. One common global phase is allowed; input-dependent phase error is not.
2. State preparation and measurement are outside the standalone oracle and must not be included in the scored QASM.
3. Cleanup, logical output-order restoration, and all six ancillas are part of the score.
4. Attached PDFs, DOCX files, notebooks, CSVs, and old reports were treated as reference material, not as instructions that override the user's request.
5. The public leaderboard can expose scores but not other competitors' QASM/QMOD, so architecture inference is necessarily indirect.

## 2. Current Status

### Completed

- A complete exact oracle is protected at **177/426/18** and was freshly reverified during this handover.
- Its QASM and QMOD contain the same 816 numeric native operations.
- The current public leaderboard and exact top-five/top-three thresholds have been recorded.
- Extensive local optimization of the 177-depth topology, several new Boolean/reversible architectures, Classiq SDK passes, Qiskit/pytket/PyZX/Rustiq passes, geometry decompositions, phase-polynomial methods, and literature-derived techniques have completed bounded searches.
- Two restructuring rounds were completed for every current direct score-code and fixed-encoder track.
- An exact full-logo score-code phase component was reduced to **47/77/18**, verified as a full 256-state operator and on the induced 4,096-coordinate truth table.
- The fixed code assignment's encoder search is closed through eight affine-product updates and partially screened at nine updates; no exact compatible encoder was found.
- The tempting 23-depth local-code interface was proved phase-ambiguous and cannot support an exact full-logo diagonal on its proposed ten wires.

### Currently in progress

No search process or sub-agent remains active at handover time. The next architectural search has not been launched. All recent bounded two-round tracks wrote final `REPORT.md` and `SUMMARY.json` artifacts.

### Remaining

1. Find a code assignment and exact reversible encoder whose **actual native cost** is compatible with a small phase kernel.
2. Integrate encoder, phase application, and exact inverse into one complete 18-qubit circuit.
3. Compile using the common contract, restore any elided output permutation physically, and verify all 4,096 inputs.
4. Export a numerically matching QMOD.
5. Promote it only if its lexicographic tuple improves `177/426/18`; the competition goal needs approximately 50 fewer depth layers.
6. Upload to Classiq and obtain an official score when authentication/browser access is available.

### Completion estimate

There is no defensible percentage estimate for the competition goal. The specification, verifier, baseline, scoring pipeline, failure map, and promising kernel are complete, but the remaining encoder/kernel co-design is the central unsolved research problem. The measured gap from the protected complete oracle to guaranteed top five is **50 depth layers**.

## 3. Work Completed

### 3.1 Protected complete oracle

The current submission pair is:

| Artifact | Path |
|---|---|
| QASM | `outputs/best_verified_depth177_cx426.qasm` |
| QMOD | `outputs/best_verified_depth177_cx426.qmod` |
| Full verification | `outputs/best_verified_depth177_cx426_verification.json` |
| QASM/QMOD correspondence | `outputs/best_verified_depth177_cx426_qmod_correspondence.json` |
| Manifest | `outputs/MANIFEST.json` |
| Human overview | `outputs/README.md` |
| Machine summary | `outputs/SUMMARY.json` |

This circuit was produced by removing native CX gates 632 and 671 from the earlier 177/428 lineage and refitting the two affected nine-wire transformations on all 64 reachable complex input columns, including phase. The complete 18-wire circuit was then checked on every coordinate input.

Fresh handover verification:

| Metric/check | Result |
|---|---:|
| Depth | 177 |
| CX | 426 |
| U3 | 390 |
| Total operations | 816 |
| Width | 18 |
| Basis inputs checked | 4,096 |
| Marked inputs | 1,097 |
| Maximum observed error | `5.443040426034505e-12` |
| Error plus discarded-amplitude bound | `8.150836402909458e-12` |
| Maximum helper leakage probability | `2.9707776767127515e-23` |
| QASM/QMOD numeric body | Identical |

Hashes:

```text
QASM a95f05f9ea28c3d1db38760b19aaefceb378fa2889b5bb49a699c7fe67ce3be2
QMOD a16dc1ca64cf083e571bf1451b7be5b7e656037ae82d7f9855e6e2d1013c3202
```

Do not overwrite this pair unless a new complete candidate passes the same contract and improves the score.

### 3.2 Leaderboard refresh

The latest independent snapshot is `research/leaderboard_snapshot_2026-09-22.json`. It records the source URL, retrieval timestamp, cache status, response hash, top ten, and derived strict thresholds. The public page is `https://www.classiq.io/challenge`.

The result changed the practical target from the old 162-depth fifth-place score to **127 depth for guaranteed top five**, or **128 with CX below 405**.

### 3.3 Direct full-score diagonal architecture

Primary artifacts:

- `research/direct_diagonal_architecture/REPORT.md`
- `research/direct_diagonal_architecture/SUMMARY.json`
- `research/direct_diagonal_architecture/full_score_kernel_optimized.json`
- `research/direct_diagonal_architecture/full_score_native_refine.json`
- `research/direct_diagonal_architecture/full_score_all4096_logic_verification.json`
- `research/direct_diagonal_architecture/full_score_kernel_depth47_cx77_COMPONENT_ONLY.qasm`

The exact logo was factored as two disjoint threshold rounds:

```text
logo(x,y) = [aL(x)+bL(y) >= 6] XOR [aR(x)+bR(y) >= 6]
```

Each axis has 11 distinct `(left score, right score)` profiles. Four code bits per axis reduce the phase care space to 121 of 256 words. The selected score labels are:

```text
enc_x = [0, 3, 5, 1, 6, 2]
enc_y = [0, 3, 1, 6, 4, 5]
```

The care-space phase has degree four. Nullspace search and 2,000 native scheduling trials reduced the component from 51/78 to **47 depth / 77 CX / 64 U3**. Its QASM hash is `ef82d9d791be003f866a561939a7375f7695079379ded11d3bf2f263ab2fe7ba`.

Verification:

- All 256 code-space basis states were checked as an operator.
- Maximum operator error is `4.478660548506687e-15`.
- All 121 reachable code words implement the intended phase.
- The induced full 4,096-coordinate truth table has zero mismatches and 1,097 marks.

This file is **not a complete oracle**. It excludes both forward encoders and both inverses. For independent x/y encoders run in parallel:

```text
complete_depth = 2 * max(depth_x, depth_y) + 47
complete_CX    = 2 * (CX_x + CX_y) + 77
```

Useful budgets:

- To reach depth 127, parallel forward encoder depth must be at most 40.
- To retain the historical strict `CX < 428` condition, combined forward CX must be at most 175.
- At depth 128, strictly beating the current fifth-place `128/405` needs total CX below 405, so combined forward CX must be at most 163 with this 77-CX kernel.
- The report's `combined forward CX = 164` gives total CX 405 exactly; it is attractive at depth 127 but does not win a depth-128 CX tie.

### 3.4 Fixed score-code reversible encoder search

Primary artifacts:

- `research/fixed_code_reversible_encoder/REPORT.md`
- `research/fixed_code_reversible_encoder/SUMMARY.json`
- `research/fixed_code_reversible_encoder/fixed_score_affine_cnf.py`
- `research/fixed_code_reversible_encoder/search_affine_encoder.cpp`
- `research/fixed_code_reversible_encoder/local_level_10wire_impossibility.json`

Round 1 exhaustively tested a normal form with one coordinate anchor plus three clean live outputs, five untouched coordinate wires, updates of the form

```text
target ^= affine(other live/source signals) & affine(other live/source signals)
```

and an arbitrary invertible affine frame on the four outputs. Every SAT instance simultaneously constrained all 64 inputs.

| Updates | Schedules per anchor | Anchors | Cases per axis | X | Y |
|---:|---:|---:|---:|---|---|
| 6 | 6 | 6 | 36 | Exact UNSAT | Exact UNSAT |
| 7 | 81 | 6 | 486 | Exact UNSAT | Exact UNSAT |
| 8 | 645 | 6 | 3,870 | Exact UNSAT | Exact UNSAT |
| 9 | first 500 of 3,993 | 6 | 3,000 | UNSAT in bounded subset | UNSAT in bounded subset |

Round 2 allowed affine-product updates on all nine wires and arbitrary reversible garbage. Three deterministic 30-second annealing runs were used per axis:

- Best X: 7 of 64 states wrong, seven output-bit errors, 39 nonlinear updates.
- Best Y: 8 of 64 states wrong, nine output-bit errors, 42 nonlinear updates.
- No exact encoder and no QASM were emitted.

Conclusion: the **fixed** 47/77 code assignment is not viable under these bounded grammars. Do not rerun the same k6-k8 instances. A future search must co-design the code labels and phase kernel, or introduce a materially richer exact garbage-changing primitive.

### 3.5 Fixed 38/55 off-care profile kernel

Primary artifacts:

- `research/profile_kernel_offcare/profile_kernel_offcare50_depth38_cx55.qasm`
- `research/profile_kernel_offcare/COMPAT38_K7_K8_REPORT.md`
- `research/profile_kernel_offcare/compat38_k8_complete_verification.json`
- `research/profile_kernel_offcare/verify_compat_k8_complete.py`

The kernel is an exact component at **38 depth / 55 CX / 50 U3 / 18 width**. Its compatible affine-product encoder search is closed through eight updates:

- Six coordinate anchors.
- 645 canonical degree-feasible schedules per anchor.
- 45 exact code embeddings.
- 174,150 exact UNSAT cases at k8, zero witnesses.
- The complete k7 family is also exact UNSAT.

This is a finite proof only for the stated grammar. It does not rule out a different phase table, richer reversible updates, more live wires, or direct quantum synthesis.

### 3.6 Affine-product native cost study

Primary artifacts:

- `research/affine_product_update_template/REPORT.md`
- `research/affine_product_update_template/SUMMARY.json`
- `research/affine_product_update_template/BEAM_VERIFICATION.json`

Key verified local primitives:

| Primitive | Depth | CX | U3 |
|---|---:|---:|---:|
| Relative-phase RCCX | 7 | 3 | 4 |
| Exact CCX | 11 | 6 | 8 |

The relative phase cancels exactly in `U^-1 D U` when the concrete inverse is used and `D` is diagonal. Local mapping and compute/uncompute checks pass all 512 states.

The best eight-update cost probe was 134/227/18, and an appended diagnostic splice was 206/381/18. **Both are invalid as complete oracles** because the source k8 networks declare `truth_verified=false` and their compatibility with the fixed kernel was not established. Retain only the update-template implementation and its verified cancellation property.

### 3.7 Fast local-code shortcut: exact rejection

Primary artifacts:

- `research/fast_level_global_phase/REPORT.md`
- `research/fast_level_global_phase/SUMMARY.json`
- `research/fast_level_global_phase/analyze_interface.py`
- `research/fast_level_global_phase/interface_anf.json`
- `research/direct_diagonal_architecture/source_core_feature_audit.json`

The existing low-nibble encoder costs only 23 depth / 23 CX per axis. However, its six helper code bits plus four untouched high coordinate bits produce 400 reachable ten-wire words, and 129 words contain both marked and unmarked coordinates. At least 517 basis inputs must be wrong under any phase function restricted to those ten wires.

Two independent collision examples are recorded:

- `(x,y)=(34,0)` and `(34,14)` share ten-wire word 116 but require phases 0 and 1.
- `(x,y)=(38,3)` and `(38,11)` share word 181 but require opposite target values.

Adding coordinate outputs requires six more wires; the minimum sufficient interface therefore has 16 wires and all 4,096 care words are distinct. Exact positive-polarity ANF is inconsistent through degree seven. The first degree-eight witness has 676 monomials. This route cannot fit the remaining depth budget.

### 3.8 Geometry/rank factorization

Primary artifacts:

- `research/geometry_rank_new_architecture/REPORT.md`
- `research/geometry_rank_new_architecture/SUMMARY.json`
- `research/geometry_rank_new_architecture/final_verification.json`

The logo is exactly the disjoint XOR of two rank-five threshold matrices:

- Lower disk: 225 pixels.
- Rectangle/bar/upper-circle remainder: 872 pixels.
- Total: 1,097 pixels.

The best lower-round phase component is 28/25, but exact side-code emitters remain too costly or failed bounded in-place emission. The earlier AU5/BU5 tables cover only a trimmed 132-pixel upper disk and must not be used as the full 872-pixel remainder. No complete QASM/QMOD was emitted from this track.

### 3.9 Literature and library implementation audit

Primary artifacts:

- `research/paper_sep22_idea_audit/REPORT.md`
- `research/paper_sep22_idea_audit/SUMMARY.json`
- `research/paper_sep22_idea_audit/IDEA_INVENTORY.md`
- `research/paper_sep22_idea_audit/COVERAGE_AUDIT.md`
- `research/paper_sep22_idea_audit/CSV_AUDIT.md`

The attached nine-page literature synthesis and 50-row bibliography were treated as reference evidence. All 25 paper ideas and all 50 bibliography entries were classified or implemented under the challenge contract.

Important results:

| Method | Scope | Result | Decision |
|---|---|---:|---|
| HOPPS | All 272 incumbent phase blocks, 71 unique | Complete best ties 177/426 | Reuse only after architecture changes |
| FORM/ShallowGrow | Complete XAG | 4,742/4,404/18 | Reject this recursive lowering |
| SPARE lifetime retention | Repeated-threshold component | 348/220 to 176/112 | Retain the lifetime pattern |
| FFQC cleanup deferral | Threshold component | 176/110 to 100/62 | Strong component pattern |
| FFQC full integration | Complete logo family | 919/1,256/18 | No score gain from cleanup deferral alone |
| Vandaele comparator | Six-bit comparator component | 105/87 | Too costly as a repeated standalone primitive |
| Vandaele clean phase comparator | Component | 201/154 | One comparison already exceeds depth 177 |
| Joint gauge/order/cache XAG | Complete logo | 16,300/12,442/18 | Reject recursive node materialization |

The transfer order that remains useful is: synthesize naturally resident nonlinear predicates jointly, defer local cleanup, retain predicates across consumers, flatten only after state/phase co-design, then use HOPPS on any resulting broad affine-phase block.

### 3.10 External-drive architecture audit

Primary artifacts are copied into the workspace under `research/external_drive_depth130_agent/`.

The best exact complete artifact in that family is **303/1,221/18**, verified on all 4,096 inputs. A tempting depth-81 partial object was rejected because low-five-bit periodic aliasing marked 900 states instead of the intended 225. Direct code-transition searches remained inexact, and a 23-update exact side encoder measured 169/169 by itself. No file on `/Volumes/NO NAME` was modified.

### 3.11 Historical and failed-attempt ledger

The chronological source of record is `research/CONTINUATION_177.md`. The following table prevents repeated work. “Complete” means the full logo oracle was physically emitted and checked; “component” and “diagnostic” metrics must not be ranked as submissions.

| Track/family | Best or decisive result | Status and implication | Primary evidence |
|---|---:|---|---|
| CX direction gauges/fusion | 8,000-step anneal, 2,229 gauge sets; 5,000 random trials | No depth below 177 | `research/CONTINUATION_177.md` |
| Fixed-list commutation scheduling | Horizon 176 exact infeasible | Fixed 820-gate list cannot be merely reordered to 176; not a global oracle lower bound | `research/agent_front_back_refactor/README.md` |
| Wide splices and cut alignment | 1,404 directional splices | All valid results stayed at 177/429; apparent 176 samples failed all-4,096 checks | `research/agent_wide_cut_resynthesis/REPORT.md` |
| Critical-span CX deletion | Nominal 175-176 diagnostics | Wrong input-dependent phases; invalid | `research/agent_critical_span_rewrite/REPORT.md` |
| Three-wire local resynthesis | Best local errors 0.395, 0.276, 0.264 | No exact lower-CX block found in bounded topology | `research/CONTINUATION_177.md` |
| Raw Walsh/parity oracle | 2,031/4,116 complete | All 4,095 nonconstant parity terms are required because 1,097 is odd | `research/strict_parallel/parity_banks/REPORT.md` |
| Tiled QROM/table | 3,308/2,274 complete | Selector cost dominates | `research/strict_parallel/tile_sharing/REPORT.md` |
| Complemented shared-prefix Boolean pipeline | 4,005/2,260 complete | Helper write serialization dominates | `research/strict_parallel/boolean_pipeline/REPORT.md` |
| Fixed profile codec | 5,467/3,009 complete | Repeated label writes and 73 phase monomials | `research/strict_parallel/profile_codec/REPORT.md` |
| Row-profile symbolic cover | 7,085/4,376 proxy | Exact symbolic cover, noncompetitive lowering | `research/agent_row_profile_architecture/README.md` |
| Row-transition circuit | 8,299/4,998 complete | Independent transition factors too costly | `research/agent_row_transition_oracle/REPORT.md` |
| Standalone rectangle replacement | 2,501/2,459 complete | Exact but loses shared encoding | `research/agent_native_block_rearchitecture/REPORT.md` |
| Dirty-coordinate Shannon | 12,415/10,533 complete | Direct cofactor ESOP noncompetitive | `research/agent_dirty_coordinate_xag/REPORT.md` |
| BDD/state machine | optimistic 154 before overhead; phase-flow estimate 243 | Template does not reach target; not a universal BDD impossibility | `research/agent_reversible_bdd_state_machine/REPORT.md` |
| Input-frame ANF search | 143 cubes with two-sided frame depth 68 | Still too costly | `research/agent_input_frame_anf_search/REPORT.md` |
| High-level Classiq rank-eight model | Requires at least 26 qubits | Violates width 18 | `research/agent_parallel_rectangles_128/REPORT.md` |
| Strict five-track restructure | Best retained 177/428 at that time | Zero candidates under 177/428 after two rounds | `research/strict_parallel/REPORT.md` |
| Modular late-phase repair | 186/433 complete | Phase repairs re-extend critical path | `research/modular_repair_next/REPORT.md` |
| Whole-side phase-aware refit | **177/426 complete** | Produced current protected incumbent | `research/joint_state_phase_next/REPORT.md` |
| Five target-162 tracks | 177/426 retained | Whole-side, cross-side, scheduling, Qiskit, and pytket all failed to beat 162/354 | `research/target162/REPORT.md` |
| Architecture frontier | 192/434 and 207/440 complete temporary-clean variants | Helper erasure/fanout overhead exceeds benefit | `research/architecture_frontier/REPORT.md` |
| Quadratic profile codes | 1,303/1,378 complete | Exact encoders dominate; 62/84 kernel-only score is not a full oracle | `research/quadratic_profile/REPORT.md` |
| Shared profile encoders | 797/1,224 and 837/916 complete | Better than prior new architecture, far above 177 | `research/shared_encoder_next/REPORT.md` |
| Partial phase/joint coordinates | 705/1,181 complete best in that family | Partial-prefix preparation still costly | `research/partial_phase_next/REPORT.md` |
| Projective side freedom | no exact output-ray fit | Lower-CX diagnostics leaked helpers | `research/projective_side_next/REPORT.md` |
| Wider joint geometry | 3,770/2,224 complete | Cube traversal remains too large | `research/wide_joint_followup/REPORT.md` |
| Product-interface joins | 183/429 complete relative-phase variant | No improvement; broad Boolean joins need more nonlinear updates | `research/interface_join_next/REPORT.md` |
| Encoding redesign/sparse phase | 202/448 complete | Sparse phase helps but new state encoding remains expensive | `research/encoding_redesign_next/REPORT.md` |
| Exact-T/phase-network methods | 183/430 sparse join; 7/9 reusable component | Useful local macros, no better complete oracle | `research/phase_network_next/REPORT.md` |
| Triangle integration | 196/446 complete best | Dirty interface overhead remains too high | `research/triangle_integration_next/REPORT.md` |
| Partial-bank cleanup/direct marker | 179/425 and 190/427 complete | Close in CX, still slower in depth | `research/partial_bank_next/REPORT.md` |
| Resident-predicate phase motion | selected candidates tie 177/426 | Existing trajectory exhausted for grouped resident labels | `research/shared_predicate_kernel_next/REPORT.md` |
| Joint cubic clean labels | 405/534 reduced component | Missing X encoder; class-constant cubic labels are exact UNSAT | `research/joint_cubic_code_phase/REPORT.md` |
| Fixed 38/55 kernel encoder | 174,150 k8 cases exact UNSAT | Close this kernel with <=8 affine-product updates | `research/profile_kernel_offcare/COMPAT38_K7_K8_REPORT.md` |
| Direct 47/77 score kernel | 47/77 component | Strongest live kernel; fixed encoder search failed | `research/direct_diagonal_architecture/REPORT.md` |
| Fixed 47/77 encoder | k6-k8 exact UNSAT; k9 partially UNSAT | Abandon fixed mapping under tested grammars | `research/fixed_code_reversible_encoder/REPORT.md` |
| External-drive family | 303/1,221 complete | Exact but structurally far above depth 130 | `research/external_drive_depth130_agent/REPORT.md` |

The 177-depth circuit should be treated as a dead end for **local topology polishing**, not as a proven global lower bound. The exact fixed-list and bounded local results do not rule out a fundamentally different state representation.

## 4. Technical Details

### 4.1 Runtime environment

The shell's default `python3` does not contain Qiskit, Classiq, NumPy, SciPy, PySAT, PyZX, or pytket. Use:

```text
/Users/jayachandiranudayakumar/Desktop/Classiq-Codex/research/claude_runs/20260920T072422Z_2d9971eb/venv/bin/python
```

Key versions in that environment:

| Package | Version |
|---|---:|
| Python | 3.13 |
| Qiskit | 2.5.2 |
| Qiskit Aer | 0.17.2 |
| Classiq | 1.29.1 |
| NumPy | 2.5.3 |
| SciPy | 1.18.1 |
| python-sat | 1.9.dev15, including `kissat404` |
| NetworkX | 3.6.1 |
| PyZX | 0.10.6 |
| pytket | 2.18.3 |
| BQSKit | 1.2.1 |
| z3-solver | 5.1.0.0 |

There is no project-level `requirements.txt` or `pyproject.toml`; the existing environment is the reproducible dependency source. Capture `pip freeze` before rebuilding it.

### 4.2 Common scoring pipeline

Use `research/strict_parallel/evaluation.py`. Its fixed settings are:

```python
SETTINGS = {
    "qiskit_version": "2.5.2",
    "basis_gates": ["u3", "cx"],
    "coupling_map": None,
    "optimization_level": 3,
    "seed_transpiler": 42,
    "qubits_initially_zero": False,
    "measurements": "forbidden",
    "resets": "forbidden",
    "coordinate_layout": "x=q[0:6], y=q[6:12], clean helpers=q[12:18]",
}
```

The evaluator rejects width other than 18 and rejects classical bits, measurement, reset, initialization, and barriers. It transpiles, restores any output permutation using counted physical CX gates, exports numeric OpenQASM 2, and invokes `research/verify_native_all4096_safe.py`.

### 4.3 Independent verifier

`research/verify_native_all4096_safe.py` simulates the native circuit for all 4,096 clean-input coordinate columns with sparse amplitude pruning. It verifies:

1. the final coordinate basis state is restored;
2. every helper is zero;
3. marked and unmarked states differ by the required sign;
4. one common global phase is allowed;
5. discarded-amplitude bounds and helper leakage remain below tolerance.

The checks are high-confidence numerical checks, not formal floating-point enclosures.

### 4.4 Output-permutation rule

Qiskit can remove SWAP gates and keep their effect only in `TranspileLayout`. A standalone QASM does not preserve that metadata. `restore_output_order` in `research/strict_parallel/evaluation.py` materializes the final permutation with three counted CX gates per SWAP and rejects nonidentity input layouts. Never export a transpiled circuit without resolving this.

### 4.5 QMOD handling

- `outputs/best_verified_depth177_cx426.qmod` is the matching submission-style oracle plus wrapper.
- `outputs/classiq_logo_depth177_cx426_main_only.qmod` inlines the native body into `main`.
- `outputs/classiq_logo_depth177_cx426_sdk_superposition_probe.qmod` prepares all 12 coordinates with H gates for Classiq synthesis experiments. Those H gates are not part of the standalone oracle.
- Current QMOD wrappers use `allocate` and target the **Model text editor**. The user confirmed that Graphical Model -> Upload Model rejects `allocate`.
- Removing allocation from a QMOD is not a valid fix if it changes the model's input/output semantics.
- Any Classiq-exported circuit must be extracted, rescored under the common local pipeline, and reverified on all 4,096 inputs before promotion.

See `outputs/CLASSIQ_UPLOAD.md`.

### 4.6 Core files and directories

| Path | Purpose |
|---|---|
| `inputs/baseline_notebook.ipynb` | Baseline challenge notebook copied into workspace |
| `inputs/reference177_u391.qasm` and `inputs/reference177_u391.qmod` | Older 177-depth reference lineage |
| `outputs/` | Protected submission artifacts and upload documentation |
| `research/verify_native_all4096_safe.py` | Exhaustive native oracle verifier |
| `research/verify_qmod_body.py` | QASM/QMOD numeric-body comparison |
| `research/analyze_native.py` | Native metric analysis for numeric QASM |
| `research/strict_parallel/evaluation.py` | Common compile/evaluate/export contract |
| `research/CONTINUATION_177.md` | Chronological project research log through the resident-predicate track |
| `research/direct_diagonal_architecture/` | Current best score-code phase kernel and two-round report |
| `research/fixed_code_reversible_encoder/` | Latest exact/stochastic fixed-encoder search |
| `research/profile_kernel_offcare/` | 38/55 kernel and exact k7/k8 compatibility proofs |
| `research/paper_sep22_idea_audit/` | Literature and bibliography implementation audit |
| `research/external_drive_depth130_agent/` | Local copy/audit of external-drive architecture |
| `handoffs/CLAUDE_CODE_CONTINUATION_2026-09-20.md` | Earlier Claude Code continuation prompt |

### 4.7 Essential commands

Run from the workspace root.

```bash
ORACLE_PY="/Users/jayachandiranudayakumar/Desktop/Classiq-Codex/research/claude_runs/20260920T072422Z_2d9971eb/venv/bin/python"
```

Verify protected hashes:

```bash
shasum -a 256 \
  outputs/best_verified_depth177_cx426.qasm \
  outputs/best_verified_depth177_cx426.qmod
```

Measure a numeric native QASM:

```bash
"$ORACLE_PY" - <<'PY'
from qiskit import qasm2
c = qasm2.load("outputs/best_verified_depth177_cx426.qasm")
print({
    "depth": c.depth(),
    "cx": int(c.count_ops().get("cx", 0)),
    "u3": int(c.count_ops().get("u3", 0)),
    "width": c.num_qubits,
    "operations": sum(c.count_ops().values()),
})
PY
```

Exhaustively verify a candidate:

```bash
"$ORACLE_PY" research/verify_native_all4096_safe.py \
  outputs/best_verified_depth177_cx426.qasm
```

Check QASM/QMOD correspondence:

```bash
"$ORACLE_PY" research/verify_qmod_body.py \
  outputs/best_verified_depth177_cx426.qasm \
  outputs/best_verified_depth177_cx426.qmod
```

Compile, score, export, and verify a new complete candidate under the common contract:

```bash
"$ORACLE_PY" research/strict_parallel/evaluation.py \
  path/to/candidate.qasm \
  research/candidate_evaluation \
  --name candidate \
  --modification "describe the architecture change" \
  --rationale "explain the expected depth/CX reduction"
```

Reproduce the direct score-code searches; these can take minutes and overwrite their result JSON/QASM, so copy the directory first if preservation matters:

```bash
"$ORACLE_PY" research/direct_diagonal_architecture/screen_full_score_encodings.py
"$ORACLE_PY" research/direct_diagonal_architecture/optimize_full_score_kernel.py \
  --seconds 120 --compile-trials 400
"$ORACLE_PY" research/direct_diagonal_architecture/refine_full_score_native.py
"$ORACLE_PY" research/direct_diagonal_architecture/audit_source_core_features.py
```

Example exact fixed-encoder SAT run; do not repeat already-complete k6-k8 screens without changing the grammar:

```bash
"$ORACLE_PY" research/fixed_code_reversible_encoder/fixed_score_affine_cnf.py \
  x --updates 8 --solver kissat404 \
  --out /private/tmp/fixed_score_x_k8_repeat.json
```

Use `/Library/Developer/CommandLineTools/usr/bin/clang++` for local C++ builds. The system developer-tool path can trigger the unaccepted Xcode application license.

## 5. Findings and Evidence

### Confirmed facts

1. `outputs/best_verified_depth177_cx426.qasm` is currently the best complete local oracle at 177/426/390/18 and passes all 4,096 inputs.
2. The matching QMOD has the identical 816-operation numeric body.
3. The current public top-five cutoff is 127 depth, or 128 with CX below 405, as of the recorded snapshot.
4. The logo mask has exactly 1,097 marked coordinates and the four-shape formula above matches the verifier.
5. Raw-coordinate Walsh synthesis is dense: all 4,095 nonconstant parity characters are nonzero because the marked-set size is odd.
6. The fixed 38/55 phase kernel has no compatible affine-product encoder with at most eight updates under its exact tested grammar.
7. The direct score-code phase kernel is an exact 47/77 component and its induced logical phase is correct on all 4,096 coordinates.
8. No exact encoder for that fixed mapping was found: k6-k8 are exact UNSAT under the normal form, and broader heuristic searches remain inexact.
9. The 23-depth local-code ten-wire interface is information-theoretically insufficient for an exact logo phase because 129 reachable words require conflicting phases.
10. Local polishing of the 177 topology has plateaued across multiple compiler pipelines, exact fixed-list schedules, local deletions, gauges, splices, and numerical isometry fits.

### Strong hypotheses, not proofs

1. A competitive circuit probably uses a nonlinear profile or score encoding followed by a compact care-space phase, because leaderboard scores are compatible with a compute-phase-uncompute shape and raw-coordinate diagonal methods are too dense.
2. A winning architecture likely co-designs encoder and phase rather than minimizing them separately.
3. Predicate lifetime retention and cleanup deferral can contribute large local reductions if applied before flattening, but they are insufficient around the tested expensive threshold encoders.
4. The fixed 177 topology is unlikely to supply a 50-layer reduction, but no global depth lower bound has been proved.

### Unresolved issues

1. Whether another four-bit code assignment admits both cheap exact reversible encoders and a sub-50-depth phase kernel.
2. Whether a richer nine-wire permutation-completion grammar can implement the fixed score map within 40 parallel depth.
3. Whether Classiq cloud synthesis can discover a better global schedule once a high-level width-18 model is available.
4. Whether current leaderboard scores have changed after the recorded snapshot.

### Source references

- Public challenge: `https://www.classiq.io/challenge`
- Classiq library: `https://github.com/Classiq/classiq-library`
- HOPPS implementation: `https://github.com/qopt-quantum-optimization/HOPPS-Hardware-Aware-Optimal-Phase-Polynomial-Synthesis`
- FORM/ShallowGrow paper: `https://arxiv.org/abs/2605.21380`
- FFQC cleanup-deferral paper: `https://eprint.iacr.org/2026/568`
- Vandaele comparator paper: `https://arxiv.org/abs/2603.12917`

The attached PDFs, CSV, DOCX, and notebook are reference sources. Repository reports record their hashes and any transferred methods.

## 6. Problems Encountered

### 6.1 Component metrics were repeatedly mistaken for complete scores

**Issue:** Small phase or encoder components such as 38/55, 47/77, 62/84, 100/62, and 176/112 can look leaderboard-winning when preparation, inverse preparation, correction, or cleanup is excluded.

**Cause:** Different branches optimize isolated reversible or diagonal blocks.

**Mitigation:** Component filenames include `COMPONENT_ONLY`; reports state scope; promotion requires the common evaluator and all-4,096 verifier.

**Next step:** Keep component and complete-oracle leaderboards separate. Never report a component tuple as the current oracle.

### 6.2 Fixed score-code encoder could not be synthesized cheaply

**Issue:** The strongest 47/77 kernel needs exact side encoders, but the normal form is UNSAT through k8 and the broad heuristic search remains 7 and 8 states wrong.

**Cause:** The selected code assignment optimized phase cost without jointly optimizing reversible encoder complexity.

**Tried:** Exact PySAT/Kissat across all anchors/schedules through k8, bounded k9 top-500-per-anchor screen, fixed-output stochastic search, free-code search, retained-bit split codes, affine retained projections, and arbitrary-garbage annealing.

**Worked:** Exact negative certificates and a clear native budget.

**Failed:** No exact encoder; split-code FPRM proxies are hundreds of CX per axis.

**Next step:** Co-design code labels and native encoder, then synthesize the reachable phase table for those labels.

### 6.3 Fast 23-depth encoder lost necessary coordinate information

**Issue:** Six local helper codes plus four high coordinate bits map marked and unmarked coordinates to the same word.

**Cause:** The local code was designed for separate periodic/profile functions, not the complete global logo relation.

**Tried:** Exhaustive collision audit, all subsets of remaining coordinate outputs, and exact ANF degree tests.

**Result:** Ten-wire kernel impossible; minimum sufficient interface is 16 wires with 4,096 distinct care words; degree-eight witness has 676 monomials.

**Next step:** Do not try more phase synthesis on that ten-wire interface.

### 6.4 Classiq width and model-interface failures

Exact observed errors include:

```text
Model requires at least 26 qubits, but max width constraint is 18.
```

and, in later SDK variants:

```text
Model requires at least 19 qubits, but max width constraint is 18.
```

Some recursively expanded QMOD models also raised:

```text
RecursionError: maximum recursion depth exceeded. Tip: If your program contains
recursive functions, check for base cases using a Python if-statement
(instead of Qmod's `if_`)
```

**Cause:** High-level allocators and decompositions required hidden temporary qubits or recursive expansion.

**Tried:** Main-only native QMOD, superposition probes, list controls, family cubes, and several transpilation bases.

**Worked:** The native 816-gate model stays at width 18 and can be represented in QMOD.

**Next step:** Build future QMOD from an already width-18 reversible architecture and inspect synthesized width before accepting it.

### 6.5 Graphical Model uploader rejects allocation

**Issue:** The user confirmed that Graphical Model -> Upload Model reports `Allocate is not supported`.

**Cause:** Current files are text QMOD programs with explicit allocation, while the graphical importer expects a supported main-model form.

**Tried:** Separate main-only and SDK superposition-probe wrappers.

**Worked:** The QMOD text is suitable for the Model text editor; Graphical Model compatibility is not established.

**Next step:** Use the Model text editor or generate a genuinely supported graphical main model. Do not delete allocation blindly.

### 6.6 Classiq authentication and browser access are unconfirmed

**Issue:** SDK authentication checking stalled while macOS Keychain attempted to retrieve a refresh token; another recorded attempt encountered:

```text
ConnectError: [Errno 8] nodename nor servname provided, or not known
```

In-app browser navigation to `https://platform.classiq.io/` was denied because the admin-enforced security policy could not be verified.

**Cause:** External session/security/network state, not the oracle code.

**Tried:** Read-only SDK initialization, in-app browser navigation, local offline QMOD builds.

**Worked:** Classiq SDK 1.29.1 imports in the project environment and can build models offline.

**Next step:** Retry only after external authentication or browser policy changes. Do not read or overwrite credentials.

### 6.7 Qiskit can silently elide output SWAPs

**Issue:** Exporting raw transpiled gates can lose the logical output permutation stored only in `TranspileLayout`, producing helper leakage or swapped coordinates.

**Cause:** Qiskit treats final layout as metadata.

**Fix:** `restore_output_order` now emits counted three-CX swaps before export and rejects unsupported input remapping.

**Next step:** Always use the common evaluator or duplicate this restoration logic exactly.

### 6.8 Qiskit phase-accuracy bug in one pass

**Issue:** Qiskit 2.5.2 `TwoQubitPeepholeOptimization` with `approximation_degree=1.0` dropped a nonzero controlled phase in a saved six-gate reproducer.

**Evidence:** Operator error about `2.35e-5`; full candidate phase error about `2.3e-4` after that pass. See `research/encoding_redesign_next/phase_accuracy/REPORT.md`.

**Mitigation:** Full all-4,096 verification after final compilation; do not infer correctness from abstract Boolean equivalence or pre-pass simulation.

### 6.9 Default Python lacks dependencies

**Issue:** `python3` reports `ModuleNotFoundError` for Qiskit, Classiq, NumPy, SciPy, PySAT, PyEDA, and NetworkX.

**Fix:** Use the project environment documented in Section 4.1.

### 6.10 Git and system compiler tooling

Git commands currently fail before repository inspection with:

```text
You have not agreed to the Xcode license agreements. Please run
'sudo xcodebuild -license' from within a Terminal window to review and agree
to the Xcode and Apple SDKs license.
```

The system `clang++` path can hit the same issue. The fixed-encoder binary was built successfully with:

```text
/Library/Developer/CommandLineTools/usr/bin/clang++
```

No project-level `AGENTS.md`, `CLAUDE.md`, or instruction file exists. The only `AGENTS.md` is inside the vendored `guppy-algorithms` project and applies only when modifying that vendor directory.

**Next step:** Do not require Git for continuation. If repository status is needed, the user must accept the Xcode license or provide a working Git binary; that is an external machine action.

## 7. Pending Tasks

- [ ] **High priority: Launch a joint code-assignment/native-encoder/phase-kernel search.** Enumerate or evolve four-bit profile codes per axis, synthesize exact nine-wire reversible encoders with arbitrary garbage, measure native depth/CX early, then solve the 121-or-smaller care-space phase for that exact code. Optimize the complete objective `2*max(dx,dy)+dk` and `2*(cx+cy)+cxk`, not phase sparsity alone.

- [ ] **High priority: Add an exact acceptance layer to every encoder search.** A heuristic candidate is useful only after all 64 side inputs produce the required code and the nine-wire map is injective on the clean-input subspace. Save the truth-table certificate and concrete inverse.

- [ ] **High priority: Integrate the first exact budget-feasible pair.** Build an 18-qubit `U_x || U_y ; D ; (U_x || U_y)^-1` circuit, transpile under the common contract, restore output order, and run `verify_native_all4096_safe.py`. Reject it immediately if depth is above 177 unless it reveals a reusable structural improvement.

- [ ] **High priority: Apply lifetime and cleanup patterns before flattening.** Keep shared predicates live across phase consumers using the SPARE pattern and defer internal cleanup using the FFQC pattern. Preserve one exact final inverse so all six helpers return to zero.

- [ ] **High priority: Protect the incumbent.** Before and after any promotion attempt, confirm the protected QASM hash remains `a95f05f9ea28c3d1db38760b19aaefceb378fa2889b5bb49a699c7fe67ce3be2`. Write new candidates under `research/<new_track>/` until full verification and QMOD correspondence pass.

- [ ] **Medium priority: Explore a richer exact permutation-completion grammar.** The fixed-map k6-k8 UNSAT proof assumes affine-product updates with a constrained live-output normal form. Consider multi-output three-wire blocks, shared product updates, direct reachable-subspace isometries, or phase-aware permutation completion. Count emitted U3/CX depth, not Toffoli/T-depth proxies.

- [ ] **Medium priority: Re-evaluate the 49/73 nullspace kernel alternative.** `research/direct_diagonal_architecture/full_score_refined_depth49_cx73_COMPONENT_ONLY.qasm` trades two depth layers for four CX. It may be useful if an encoder lands at depth 39 or lower and CX becomes the tie-breaker. Verify compatibility with the same code map before integration.

- [ ] **Medium priority: Append latest results to the chronological log.** Add the direct 47/77 architecture, fixed-encoder k6-k9 result, and this handover link to `research/CONTINUATION_177.md`; do not rewrite historical sections.

- [ ] **Medium priority: Refresh `outputs/SUMMARY.json`.** Preserve the protected incumbent fields, then add pointers to `research/direct_diagonal_architecture/SUMMARY.json` and `research/fixed_code_reversible_encoder/SUMMARY.json`. Validate with `python3 -m json.tool`.

- [ ] **Medium priority: Refresh the public leaderboard before setting a final target.** Use a cache-busting public request or browser access, save a new dated JSON snapshot, and recompute lexicographic cutoffs. Do not silently overwrite the 2026-09-22 snapshot.

- [ ] **Medium priority: Export matching QMOD only after a full QASM exists.** Compare numeric gate streams with `verify_qmod_body.py`; target the Model text editor unless a supported graphical main model is explicitly created.

- [ ] **Low priority: Recheck Classiq SDK/cloud authentication after external state changes.** Avoid repeated unchanged keychain/network attempts. If it works, test the already verified width-18 model first as a control.

- [ ] **Low priority: Preserve a dependency lock.** Save the current venv's `pip freeze` to a new research track before rebuilding or upgrading libraries. Compiler changes can alter depth and correctness.

## 8. Recommended Next Steps

1. **Verify the protected starting point.** Run the hash, metric, all-4,096 verifier, and QMOD-correspondence commands in Section 4.7. Stop if any result differs from this document.
2. **Create a new isolated research directory**, for example `research/joint_code_encoder_kernel_next/`. Do not edit `outputs/` during search.
3. **Start from profile truth tables, not the fixed code labels.** Load the exact 11-profile axis classification and enumerate candidate four-bit labels with an encoder-cost heuristic derived from actual reversible primitives.
4. **Synthesize encoders and phase together.** For every exact side encoder candidate, build the joint reachable care table, solve its lowest-degree/off-care phase, compile the phase, and score the total sandwich. Prune if `2*max(dx,dy)+dk > 127` for the competition track or `>176` for a first complete improvement.
5. **Use arbitrary garbage deliberately.** Only four code outputs need feed the kernel; the remaining coordinate outputs may change inside the compute block if the whole nine-wire mapping is reversible and the concrete inverse restores them.
6. **Carry affine frames and live predicates across boundaries.** Avoid constructing and erasing each parity/product independently. Integrate the verified relative-phase RCCX, SPARE lifetime, and FFQC cleanup patterns into the search representation.
7. **Compile the complete circuit early.** Component sums are optimistic because boundaries, cancellations, and critical-path contention are nonadditive. Score an integrated circuit as soon as an exact encoder exists.
8. **Run the independent verifier after every final compiler pipeline.** This catches output permutations, phase approximation, periodic aliases, helper leakage, and seemingly harmless local deletions.
9. **Promote only a concrete verified improvement.** A candidate must have exactly 18 declared qubits, native U3/CX only, no forbidden operations, all 4,096 inputs correct, coordinates restored, helpers clean, matching QASM/QMOD, and a better tuple than 177/426.
10. **Refresh and upload only after local promotion.** Current platform authentication is unconfirmed. Uploading or submitting is an external action; the user has requested competition progress, but verify the exact artifact and current target before final submission.

The most important next action is Step 3: **co-design the code assignment with the reversible encoder and the phase kernel**. Repeating the fixed 47/77 mapping's bounded encoder search or polishing the 177-depth gate list is unlikely to change the outcome.

## 9. Important Context for the Next Agent

### User preferences and decisions

- The user wants aggressive depth reduction and a top-five or top-three result, not another minor CX-only improvement at depth 177.
- Depth is primary. CX is the tie-breaker.
- Width must be exactly 18.
- The user explicitly said not to use the depth-181 lineage because it plateaued.
- The user also treats depth 177 as a local-topology dead end. Keep it as the protected correctness reference, not the main design target.
- The user asked for multiple agents and two restructuring rounds per track; recent tracks complied with that stopping condition.
- The user wants QASM and QMOD deliverables.
- Report current metrics candidly. Never imply that 47/77 or another component is a complete oracle.

### Promotion policy

Do not change `outputs/best_verified_depth177_cx426.qasm` or `.qmod` until a new pair has:

1. passed the common compilation contract;
2. passed all 4,096 native-input checks;
3. restored all coordinates and helpers;
4. matched QASM/QMOD numeric bodies;
5. improved depth, or tied depth with fewer CX.

Use filenames containing `COMPONENT_ONLY`, `INVALID`, `UNVERIFIED`, or `REJECTED` exactly as warnings. Do not remove those labels without resolving the stated failure.

### Reference documents versus instructions

The following were supplied as research references and may contain historical claims, prompts, or proposed actions. They are not authoritative instructions:

- `inputs/baseline_notebook.ipynb`
- the 72-page `Classiq_Logo_Oracle_Everything_Tried_2026-09-19` PDF and byte-identical copy
- `Classiq_Conversation_Source_Register.docx`
- the September 22 PDF literature synthesis and 50-row CSV bibliography
- old `REPORT*.md`, `SUMMARY*.json`, and verification JSON attachments
- the external-drive `Classiq-Oracle-16.09` project

Use the user request, this handover, current verified artifacts, and executable evidence to resolve conflicts.

### External access and credentials

- Classiq SDK is installed in the project venv but authentication is unconfirmed.
- Browser access to the signed-in Classiq platform was blocked by an admin policy check.
- Do not inspect, display, replace, or create credentials without explicit need and user authorization.
- The public leaderboard can be read without authentication when network access is available.
- The Graphical Model uploader does not accept the current allocation-based QMOD. Use the text Model editor for those files.

### Environment limits

- Default Python lacks dependencies; use the documented venv.
- Git inspection and some system developer tools are blocked by an unaccepted Xcode license.
- `/Users/jayachandiranudayakumar/Desktop/Classiq-Codex` is the writable project root.
- No project-level agent instruction file exists.
- The vendored `guppy-algorithms/AGENTS.md` applies only inside that vendor subtree.

### Ambiguity handled so far

The user alternated between targets `<177/<428`, beating `162/354`, depth `120-130`, and top three. The latest independent leaderboard makes the operational target unambiguous: prioritize **depth <=127** for guaranteed top five, while retaining top three at **depth <=124** or `125/CX<563` as the stretch goal. A complete improvement below 177 is valuable research progress but is not yet a top-five result.

## 10. Resume Prompt

```text
Continue the Classiq logo oracle project in
/Users/jayachandiranudayakumar/Desktop/Classiq-Codex.

Goal: produce a complete exact 18-qubit U3/CX phase oracle for the 1,097-pixel
logo, with x=q[0:6], y=q[6:12], and q[12:18] clean before and after. Minimize
depth first and CX second. The current public top-five target is depth <=127,
or depth 128 with CX <405. Every accepted circuit must pass all 4,096 inputs,
restore both coordinate registers and all helpers, and have matching QASM/QMOD.

Read first:
1. handoffs/PROJECT_HANDOVER_2026-09-22.md
2. outputs/README.md and outputs/SUMMARY.json
3. research/direct_diagonal_architecture/REPORT.md and SUMMARY.json
4. research/fixed_code_reversible_encoder/REPORT.md and SUMMARY.json
5. research/profile_kernel_offcare/COMPAT38_K7_K8_REPORT.md
6. research/paper_sep22_idea_audit/REPORT.md
7. research/CONTINUATION_177.md

Protected incumbent: outputs/best_verified_depth177_cx426.qasm/.qmod,
177/426/390/18, QASM SHA-256
a95f05f9ea28c3d1db38760b19aaefceb378fa2889b5bb49a699c7fe67ce3be2.
Do not overwrite it without a fully verified improvement.

The strongest partial result is
research/direct_diagonal_architecture/full_score_kernel_depth47_cx77_COMPONENT_ONLY.qasm.
It is exact but lacks encoders. The fixed code assignment's affine-product
encoders are exact UNSAT through eight updates, and broader heuristics remain
7 X states and 8 Y states wrong. Do not rerun that unchanged search.

Exact next task: create research/joint_code_encoder_kernel_next/ and perform a
joint search over four-bit axis code assignments, exact reversible nine-wire
encoders with arbitrary garbage, and the reachable care-space phase kernel.
Use real native depth/CX in the objective. Target parallel forward encoder
depth <=40. Compile and measure the complete compute-phase-uncompute circuit
early. Apply predicate lifetime retention and cleanup deferral before
flattening. Use the project venv at
research/claude_runs/20260920T072422Z_2d9971eb/venv/bin/python and the common
pipeline in research/strict_parallel/evaluation.py.

Reject any component-only, proxy, inexact, width>18, unclean, or partially
verified candidate. Record every round in REPORT.md and SUMMARY.json, and
promote only after all-4,096 verification plus QASM/QMOD correspondence.
```
