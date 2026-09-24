# Project Handover — 2026-09-22 (evening)

**Supersedes:** `handoffs/PROJECT_HANDOVER_2026-09-22.md` (morning). That
document remains accurate for everything before this session; this one records
the host migration, four new research tracks, several corrections to earlier
claims, and the current job state.

**Workspace:** `E:\Classiq-Codex\Classiq-Codex` (Windows 11, x86-64)
**Best result:** `177 depth / 425 CX / 18 qubits` — `outputs/best_verified_depth177_cx425.{qasm,qmod}`
(promoted late in the session; see the ADDENDUM at the end. The earlier 177/426
pair is kept unchanged.)
**Current target:** depth 100-115 via AND width — see ADDENDUM.
**Challenge closes:** 2026-09-30 (8 days out)

---

## 0. Read this first: three corrections to earlier claims

Each of these was asserted during this session and then found to be wrong.
They are recorded so the next agent does not re-inherit them.

1. **`kissat404` segfaults on this host.** The Windows `python-sat 1.9.dev15`
   build crashes (exit 139) on real instances. An earlier "kissat404 usable"
   check only fed it one trivial clause and was too weak. Use `cadical195`
   (fastest), `glucose42`, or `minisat22`. **Anything in this repository that
   invokes `kissat404` will crash here.**

2. **Classiq credentials DO exist on this machine.** The morning handover and a
   research agent both reported authentication unavailable. Synthesis in fact
   succeeds after an expired-token refresh; `research/builtin_primitive_bench/`
   contains results from real cloud synthesis calls.

3. **Borrowed/dirty-ancilla work is NOT new to this project.** A research agent
   claimed no such track existed, based on grepping only the handover summary.
   The full tree has 390 files mentioning borrow/dirty/conditionally-clean, plus
   dedicated tracks (`agent_coordinate_borrowed_cache_architecture` 1,392 depth;
   `agent_ancilla_dynamic_architecture` 6,566/2,734;
   `agent_ancilla_fanout_depth_tradeoff` no improvement). **Always grep
   `research/`, not just `handoffs/`, before calling an idea new.**

---

## 1. Environment (changed — the morning handover's is unusable)

The project moved from macOS/arm64 to Windows/x86-64. The documented venv and
the prebuilt verifier binary do not run here.

**Contract-pinned interpreter:**
```
research/claude_runs/20260922_windows_x86/venv/Scripts/python.exe
```
All eleven documented packages match the morning handover's table exactly:
qiskit 2.5.2, qiskit-aer 0.17.2, classiq 1.29.1, numpy 2.5.3, scipy 1.18.1,
python-sat 1.9.dev15, networkx 3.6.1, pyzx 0.10.6, pytket 2.18.3, bqskit 1.2.1,
z3-solver 5.1.0.0. Plus `cupy-cuda12x` 14.2.0 for GPU.
Lock: `research/windows_host_port/requirements_windows_x86_lock.txt`.

**Only deviation:** Python 3.12.7, not 3.13 (host base interpreter). Every
pinned package resolved to its documented version on 3.12; not isolated as a
variable.

**Verifier.** `research/verify_native_all4096` is a Mach-O arm64 binary and
cannot run here; there is no C++ toolchain. It was ported to NumPy at
`research/verify_native_all4096_numpy.py`, and
`verify_native_all4096_safe.py` now falls back to it automatically via
`run_engine()`. All the wrapper's protections are retained.

Port validated three ways: reproduces the documented C++ figures to ~11
significant figures (max error 5.442974e-12 vs 5.443040e-12, leakage
2.97091e-23 vs 2.97078e-23, 1097 marked); a negative control (one CX deleted)
gives `passed:false` / error 1.707 / leakage 0.5; and QASM/QMOD correspondence
is intact at 816 operations.

**GPU:** NVIDIA RTX 4060 Laptop, 8 GiB, CUDA 13.2. `cupy-cuda13x` does **not**
work (missing curand; the `nvidia-*-cu13` runtime wheels have no Windows
builds). Use `cupy-cuda12x[ctk]` — the `[ctk]` extra is mandatory or every array
op raises "Failed to find CUDA headers".

---

## 2. Status of the deliverable

`outputs/best_verified_depth177_cx426.{qasm,qmod}` is unchanged and re-verified
on this host: 177/426/390/18, 1097 marked, all 4,096 inputs pass, helpers clean.

```
QASM a95f05f9ea28c3d1db38760b19aaefceb378fa2889b5bb49a699c7fe67ce3be2
QMOD a16dc1ca64cf083e571bf1451b7be5b7e656037ae82d7f9855e6e2d1013c3202
```

**OPEN ISSUE — submission has not registered.** The user submitted the 177 pair
during this session. Hours later the public leaderboard still shows the old
entry: rank 13, `181 / 426`, submitted 2026-09-14 (confirmed in raw server HTML,
`data-depth="181"`, not a cache artefact). Either grading is heavily queued or
the upload did not take. **The next agent should re-check and, if still 181,
have the user confirm the upload was accepted.** Expected on success: rank 13 →
12 (177 beats 178/782; 174/341 stays ahead). No prize impact — the five awards
are equal and begin at rank 5.

Leaderboard top five unchanged all session: 117/590, 120/573, 125/563, 127/507,
128/405. Target remains **depth ≤127**, or 128 with CX <405.
Fresh snapshot: `research/leaderboard_snapshot_2026-09-22T1800Z.json`.

---

## 3. What this session established

### 3.1 The separable architecture is closed (3 exhaustive proofs)

`research/joint_code_encoder_kernel_next/` — REPORT.md, REPORT_ROUND2.md,
REPORT_ROUND3.md, SUMMARY.json.

A four-bit axis code must be constant on the 11 threshold profiles, so there are
exactly 2^11 = 2048 candidate code bits per axis — small enough to characterise
exhaustively rather than sample.

1. **No cheap code bits.** The only class-constant affine functions are the two
   constants. Every nonconstant code bit, on either axis, has ANF degree ≥ 4
   (x: 14 deg-4 / 1008 deg-5 / 1024 deg-6; y: 30/992/1024). This is the
   structural cause of the existing k6–k8 UNSAT certificates.
2. **Minimum total degree is exactly 19 per axis.** Degree vectors (4,4,4,4),
   (5,4,4,4), (5,5,4,4), (6,4,4,4) are all exhaustively refuted on both axes;
   19 is achieved. Forces multiplicative depth ≥ 3, so ≥21 of the 40-layer
   encoder budget goes to the nonlinear chain.
   Witnesses: x masks 7/120/849/410 (5,5,5,4); y masks 67/159/788/301 (6,5,4,4).
3. **The partition and the split are both already optimal.** The coarsest
   partition any product form `h(f(x),g(y))` can use is the distinct-column
   partition of the logo matrix — it is exactly 11/11 classes with 19/20
   boundaries, identical to what is already in use. And of all 462 balanced 6/6
   bipartitions of the 12 coordinate bits, the native x|y split is the **unique**
   one needing only 8 code bits (next best 9; 327 need 12). Across every split
   size 4/8…8/4 the minimum is always 8.

Also: every separating code must resolve all 19 (x) and 20 (y) partition
boundaries — a second invariant of the partition, not the labelling.

**Consequence: no choice of code labels, partition, or coordinate split can
improve this family.** Do not spend further effort there.

### 3.2 Why depth 177 is stuck

`research/depth_first_resynthesis/REPORT.md`.

- The schedule has **essentially no slack**: 482 of 816 gates (59%) are
  zero-slack critical, mean slack 1.03 layers, exactly one gate with slack >20.
  This independently confirms and explains the old "horizon 176 exact
  infeasible" result.
- The critical path is a **serial chain on the six helper wires**: they carry
  467 critical endpoints vs 276 for all twelve coordinate wires, and 316 of 411
  consecutive critical pairs (77%) serialise on a helper.
- Utilisation is **39%** and **uniform** (34–45% across ten bands) — there is no
  bad stage to fix; the concurrency limit is global.
- Depth 127 with our 1242 endpoints requires **9.8 endpoints/layer = 54%
  utilisation**, i.e. ~10 of 18 qubits active per layer vs ~5 today.

**Two dead ends proven here:**
- *Spend surplus CX on fanout duplication.* Requires a clean wire to copy into;
  a dirty XOR-copy yields `v XOR w` and controls on the wrong value. No clean
  wire exists mid-circuit.
- *Push work onto coordinate wires.* The maximally coordinate-side architecture
  already exists — the raw Walsh parity network, no helpers at all — and scores
  **2,031 depth**, because 1,097 is odd so all 4,095 parities are required.
  Concurrency trades against phase-term count; it is not a free variable.

**Useful framing that survives:** our CX (426) is *lower* than ranks 1–4
(590/573/563/507). CX/layer: rank1 5.04, rank4 3.99, ours **2.41**. The
leaderboard is a depth-for-CX trade curve and we sit at the low-CX end. Reaching
127 needs a decomposition with a fundamentally shallower dependency DAG —
tree-like, not chain-like. None was found.

### 3.3 Measured primitive costs (closes the last audit lead)

`research/builtin_primitive_bench/` — real cloud synthesis, re-transpiled under
the project contract.

| Primitive | Depth | CX | Width |
|---|---:|---:|---:|
| `mcx_hybrid_claudon_etal` 5 ctrl | **42** | 24 | **8** |
| Qiskit v-chain 5 ctrl | 48 | 24 | 9 |
| `mcx_hybrid_claudon_etal` 6 ctrl | **51** | 30 | **9** |
| Qiskit v-chain 6 ctrl | 60 | 30 | 11 |
| `less_than_constant_khattar_gidney` 6-bit | **75** | 43 | 9 |
| `less_than_constant_hybrid` 6-bit | **72** | 38 | 9 |

- **Comparator lead refuted.** One 6-bit comparison costs 72–75 depth = 57–59%
  of the whole 127 budget. Cheaper than the rejected Vandaele line (~105–201)
  and still hopeless. The paper's `O(log n)` does not survive translation to
  native `{u3,cx}` at n=6.
- **Claudon MCX is a real, modest win**: 12–15% shallower than the best Qiskit
  mode at identical CX and 1–2 fewer qubits. Under an 18-qubit cap the width
  saving matters. Use it as the default MCX in any future architecture. It does
  not help the current flattened incumbent.
- Caveat: the default `mcx` dispatcher returned `ClassiqAPIError: Internal
  error` at every control count; that sweep is incomplete.

### 3.4 The D: Walsh-stream family is closed by a measured floor

`D:\Classiq-Oracle-16.09` was investigated by a dedicated agent this session.
New files are confined to
`D:\Classiq-Oracle-16.09\tracks\multitrack_joint_tour_basis\`; no existing D:
artifact and nothing in `E:\...\outputs\` was modified.

**The working hypothesis was WRONG and was corrected by measurement.** The
hypothesis (mine) was that this family's higher CX/layer (3.69-4.03 vs our
2.41) represented deep parallelism that would survive gate-cutting. Per-wire
layer occupancy says otherwise:

| Circuit | shared rails q16/q17 | other wires | mean slack |
|---|---|---|---:|
| D: 303/1221 | **0.85 / 0.90** | 0.44-0.84 | 2.56 |
| D: 334/1267 | **0.84 / 0.88** | 0.44-0.82 | 5.69 |
| E: 177/426 | 0.59 / 0.68 | 0.12-0.69 | 1.03 |

The D: family is **resource-bound on two helper rails at 85-90% occupancy**;
the E: incumbent is **dependency-bound with no saturated resource**. The higher
CX/layer is 2-way x||y overlap that already saturates those rails, and in this
architecture gate count *is* rail traffic — so cutting gates cuts the very
concurrency that made it interesting.

Structural cause: each concurrent block needs its own flag *and* its own clean
rail. Two concurrent x-blocks need 4 helpers, plus 4 for y = 8 > 6. Both lanes
therefore share one rail per side, serialising all 12 x-blocks.

**Measured architectural floor.** Recompiling the full 110-edge cost matrix
under all 31 common-affine shears per side (62 matrices, 6,820 blocks, each
locally verified to <1e-10) and running exact Held-Karp over all one- and
two-lane partitions and orders gives a minimum block-depth sum of **342 (x) /
319 (y)**. With the measured 17.4% whole-circuit seam cancellation that is
**~284 best conceivable depth for this architecture**. Even an impossible ideal
(every block the cheapest in the 6,820-block pool) lands at ~192 after seam
cancellation — still above 177. Independently corroborated by the earlier E:
audit's noncommutation precedence bound of 284.

**Best verified circuit produced: 334 / 1267 / 18**
(`tracks\multitrack_joint_tour_basis\evaluated\joint_tour_basis_refined_334.qasm`),
independently re-measured and re-verified here: depth 334, CX 1267, u3 1013,
3.79 CX/layer, all 4,096 inputs pass, 1097 marked, helper leakage **0.0**,
error 2.8e-14. A genuine 3-layer gain on the D: repo's own best, but still 31
layers worse than the **303/1221** the earlier E: audit already extracted from
this family, and 157 worse than the incumbent.

Two further notes: the sub-200 circuits inside D: are **imported copies of the
E: line**, not native D: work (821 gates vs our 816, 4 layers deeper); and
`tracks\caterpillar\custom_factor0_strict.qasm` at 227/200 is **one of ten
factors, not an oracle**.

**Do not reopen this family.** Reaching 177 from it needs a per-block primitive
that does not consume a clean rail; reaching 127 needs a different
representation of the logo entirely.

### 3.5 Research-hub audit

`research/classiq_research_audit/REPORT.md`. The hub is 28 links, almost all
chemistry/CFD/QEC/options — essentially no oracle or depth content. Value was in
`docs.classiq.io`, the 2022 MCX competition, and the installed SDK. Note the
report contains an explicit CORRECTION block (see §0.3).

---

## 4. GPU acceleration

`research/windows_host_port/GPU_REPORT.md`.

**Scope matters more than the speedup.** GPU does *not* help the current
bottleneck: CDCL SAT is sequential (no practical GPU CDCL) and the all-4096
verifier is sparse (max support 14) so launch overhead would make it slower than
the 52 s NumPy run. The one workload that fits is heuristic encoder search.

Design: all 64 clean inputs of one axis fit in a **single uint64**, so a 9-wire
encoder is 9 words and an update `t ^= affine(others) & affine(others)` is ~20
bitwise ops, reversible by construction.

Performance: fused CUDA kernel (one thread per candidate, 9 wires in registers,
`__popcll`) took evaluation from 1.5M to 128.1M evals/s (85.6×); device-side RNG
then removed the host/PCIe bottleneck. End-to-end on identical work:
**193.1 s @ 4.07M/s → 6.5 s @ 120.7M/s (29.6×)**. The previous agent's ~35M
evaluation CPU campaign now takes 0.3 s.

**Affine-frame scorer.** The scorer now accepts any invertible affine output
frame, matching the SAT grammar (if the encoder produces `M·c+b` with `M`
invertible, the relabelling costs only CX/X). Each output must equal one of 32
affine combinations of the target words, assigned greedily subject to the linear
parts staying **independent** — that constraint is load-bearing, without it the
search collapses onto one target word. Validated: exact 0/0; invertible affine
image strict=76 rejects vs framed=0 accepts; degenerate outputs framed=72
rejects. Cost 41.5M evals/s (2.9× slower than strict).

**Results — the grammar, not compute, is the limit:**

| k | x best wrong bits | y best |
|---:|---:|---:|
| 12 | 14 | — |
| 14 | 9 | 6 |
| 16 | 5 | 8 |
| 18 | **4** | **4** |
| 20 | **6** | **4** |

**CAMPAIGN COMPLETE. No exact encoder at any update count.** The search
flatlined at 4 wrong bits on both axes, and x *regressed* at k=20 despite
15.7 G evaluations per anchor. Adding update capacity -- strictly more
expressive power -- stopped helping.

Per-anchor spread stayed wide (x k18: 8,9,9,10,12,4; y k20: 6,9,6,4,6,5), so
the "4" reflects one lucky anchor rather than a tight bound on the grammar.

Combined with the round-1 degree floor, the conclusion is that the
**affine-product grammar `t ^= affine(others) & affine(others)` cannot express
an exact encoder for these codes, and more compute will not change it.**

Scope caveat: this refutes the *grammar*, not the architecture in general.
Richer primitives (multi-output blocks, shared AND pools, three-wire updates)
remain formally untested -- but the degree floor forces >=21 of the 40-layer
encoder budget into the nonlinear chain under any grammar, so prospects there
are poor.

---

## 5. Jobs running at handover (all in background)

All paths in `research/joint_code_encoder_kernel_next/`.

### FINISHED: k7 SAT sweeps, both axes, minimum-degree codes

| Axis | Cases | unsat | unknown | sat | Status | Hours |
|---|---:|---:|---:|---:|---|---:|
| x | 486 | 450 | **36** | 0 | `inconclusive` | 1.90 |
| y | 486 | 446 | **40** | 0 | `inconclusive` | 2.23 |

**Report these as "no encoder found; ~92% of the space exhaustively refuted,
~8% unresolved" -- NOT as "k7 is UNSAT".** `exhaustive` is false on both.
By contrast k6 IS a real certificate: exhaustively UNSAT on both axes, 36/36
cases, zero unknowns.

### FINISHED: GPU campaign k=12..20, both axes, six anchors

See section 4. No exact encoder found; flatlined at 4 wrong bits.

### STILL RUNNING at handover

| Job | Output |
|---|---|
| `rerun_unknown.py x ... --conflicts 20000000` (retrying the 36 x unknowns) | `rerun_unknown_x_pass1.json` |

A second pass is still owed for the y axis (40 unknowns), and for any x
unknowns the running pass does not cover:

```
<venv-python> rerun_unknown.py y mindeg_y_k7_budgeted.json --conflicts 20000000
<venv-python> rerun_unknown.py x mindeg_x_k7_budgeted.json --conflicts 20000000
```

**Per-case budget semantics (important).** `run_mindeg_sat.py` now takes
`--conflicts`. A case that exhausts the budget is recorded as **`unknown`**,
never as unsat. The result reports `status: "unsat_exhaustive"` only when every
case returned unsat, otherwise `"inconclusive"`, with `unknown_cases`,
`unknown_schedules` and `exhaustive:false`. **Any k7 conclusion must quote
`exhaustive`/`unknown_cases`, not just "unsat".** ~7% of cases hit the 2M
ceiling, so k7 will be *inconclusive*, not a clean certificate like k6 (which is
exhaustively UNSAT on both axes, 36 cases each).

`rerun_unknown.py <axis> <log-or-json> --conflicts N` retries only the unknown
cases at a higher budget; it reads the raw per-case log so it works while the
parent sweep is still running, and it preserves the unknown≠unsat discipline.
A second pass will be needed for unknowns found after it started.

---

## 6. Operational pitfalls on this host

- **grep buffers.** Campaign pipelines like `python … | grep -viE warn | grep
  -E '"anchor"'` hold output in a 4 KB pipe buffer and only flush at process
  exit. This made a monitor expire with zero events while the work was fine.
  Use `grep --line-buffered`, or watch the result JSON files instead.
- **Process liveness.** `pgrep -f` and `ps -p` in Git Bash cannot see Windows
  command lines; a liveness check built on them produced a false "process gone"
  alarm. Use `Get-CimInstance Win32_Process -Filter "Name='python.exe'"`.
- **venv appears as anaconda.** Windows reports `base_prefix` in a process
  command line, so venv jobs *look* like `anaconda3\python.exe`. `sys.prefix`
  confirms the venv is genuinely active. Not a problem.
- **`from __future__ import annotations` breaks `@qfunc`.** Classiq needs real
  annotation classes, not strings (`TypeError: issubclass() arg 1 must be a
  class`).
- **No C++ toolchain.** `research/verify_native_all4096.cpp` and
  `search_affine_encoder.cpp` cannot be rebuilt here.

---

## 7. Honest assessment

The measured gap to a guaranteed top-five place is **50 depth layers**, and it
did not move this session. What moved is the *map*: three exhaustive proofs
closed the separable-code family (labels, partition, and split are all already
optimal), the profiling explains the 177 plateau and refuted two proposed fixes
by measurement, and the last lead from the literature audit (Khattar–Gidney
comparators) was measured and rejected.

Roughly 45 prior tracks plus four new ones have not produced a circuit under
177. Nothing measured this session suggests depth 127 is reachable in the
remaining 8 days. `177/426` should be treated as the result for this challenge
unless a genuinely new structural idea appears.

**Do not restart:** relabelling the 11 profiles; alternative threshold
decompositions; other coordinate splits; fanout duplication; coordinate-side
parity networks; per-shape helper/CZ lane architectures; more GPU hours on the
affine-product grammar; `kissat404`.

**Still genuinely open:** a decomposition with a tree-like (not chain-like)
dependency DAG reaching ~10 active wires per layer. No one has found one, and
this session produced no candidate.

---

## 8. Resume prompt

```text
Continue the Classiq logo oracle project in E:\Classiq-Codex\Classiq-Codex.

Read first:
1. handoffs/PROJECT_HANDOVER_2026-09-22_EVENING.md  (this file — start here)
2. handoffs/PROJECT_HANDOVER_2026-09-22.md          (morning; still valid for
   everything before the host migration)
3. research/joint_code_encoder_kernel_next/REPORT{,_ROUND2,_ROUND3}.md
4. research/depth_first_resynthesis/REPORT.md
5. research/builtin_primitive_bench/REPORT.md
6. research/CONTINUATION_177.md (chronological log; appended this session)

Use research/claude_runs/20260922_windows_x86/venv/Scripts/python.exe.
Use cadical195, never kissat404 (segfaults here).
Grep research/ — not just handoffs/ — before calling any idea new.

Protected incumbent: outputs/best_verified_depth177_cx426.qasm/.qmod,
177/426/390/18, QASM SHA-256 a95f05f9ea28c3d1db38760b19aaefceb378fa2889b5bb49a
699c7fe67ce3be2. Do not overwrite without a fully verified improvement scored
under research/strict_parallel/evaluation.py and passing
verify_native_all4096_safe.py on all 4,096 inputs.

First actions:
- Re-check the public leaderboard. If the entry still reads 181/426, the 177
  submission never registered; tell the user.
- Collect the finished k7 sweeps and report them as inconclusive-with-N-unknown,
  not as UNSAT. Run rerun_unknown.py for any remaining unknown cases.

The separable code/encoder/kernel family is closed by three exhaustive proofs;
do not reopen it. The open problem is a decomposition with a shallower
dependency DAG (~10 active wires per layer). The challenge closes 2026-09-30.
```


---

## ADDENDUM (late session) — READ BEFORE §2

### New best complete circuit: 177 depth / 425 CX

`outputs/best_verified_depth177_cx425.{qasm,qmod}` — found by the gate-count
agent (`research/gate_count_reduction/`, block `lin70`, one CX removed),
promoted after every gate passed on the contract-exported file:
contract scorer 177/425/18; the grader's own validator (verbatim from the
baseline notebook) ACCEPTED 177/425; all 4,096 inputs pass (1097 marked,
error 8.1e-12, leakage 3.0e-23); QASM/QMOD 815/815 identical.

```
QASM 7e7d3d541b1e85da38c2dd89b85b21f4e13c8f7ec6688e1ac1e64f7ebb185142
QMOD f2d71967ea873ab5f18c58d8fe7023f28e78fd603f55dc598c7e4fe73e7a6b43
```
The 177/426 pair (a95f05f9...) is kept unchanged. This is a strict
lexicographic improvement (tied depth, fewer CX). **Submit this pair**, not 426.

### The instrument that matters: AND width (supersedes CX-per-layer)

`research/shallow_dag_architecture/REPORT.md`. CX-per-layer was the wrong
metric: a saturated dependency-free AND network on 18 wires tops out near
3.0-3.1 CX/layer, and ranks 1-4 exceed that, so their extra CX is cheap linear
frame work. Measured law: depth ~= N_AND / (w/6.04) + linear_CX / 8.33, where
w = AND width. Independently re-verified: 374 of the incumbent's 390 u3 are
non-Clifford -> 93.5 ANDs + 146 linear CX at effective width ~3.2; 144 RCCX at
width 3/4/5/6 -> depth 230/200/160/138.

Predicted payoff with the incumbent's own content: width 5 -> ~126,
**width 6 -> ~108**. Rank 1 reconstructs as ~72 ANDs at width ~6 + ~374 linear
CX. **Depth 100-115 = run ~93 ANDs six wide, or ~80 ANDs five wide.**
Why it may be feasible: an AND target need not be clean (t ^= a&b is
reversible for any t), so coordinate wires are legal AND targets. Constraint:
interleaving linear CX into AND layers raised depth every time -- batch frames.

### Classiq engine route: closed

`research/classiq_engine_seeds/REPORT.md` (reconstructed after the agent was
interrupted). Width-18 synthesis now WORKS, but best output is 4,247 depth
(~24x the incumbent); timeout 10 vs 60 gave the identical circuit.

### Workstreams running at this point

| Workstream | Directory | Aim |
|---|---|---|
| AND-width scheduler (new agent) | `research/and_width_scheduler/` | place the AND network 5-6 wide with batched CNOT frames -> depth 100-115 |
| AND-count reduction (resumed gate-count agent) | `research/gate_count_reduction/` | 93.5 -> ~72-80 ANDs; C2Z phase-sink substitution; shared subexpressions |
| Internet research (new agent) | `research/web_research_oracle_depth/` | public write-ups, reversible pebbling, AND-depth/T-par, low-depth phase oracles |
| AND-network co-design (new agent) | `research/and_network_codesign/` | NEW network from scratch: <=80 ANDs AND width 5-6 together (the incumbent's serial-chain shape may cap width) |
| SAT unknown re-run pass 3 (BelowNormal priority) | `research/joint_code_encoder_kernel_next/` | x 13 + y 38 pending; all 25 resolved so far flipped to UNSAT |

If a session dies again, check those directories for partial artefacts and
resume the agents from their saved transcripts before relaunching anything.

### Promotion gate

`research/promote_candidate.py <candidate.qasm> --name N [--promote]` runs, on
the contract-exported file: contract scoring, the grader's verbatim validator,
all-4096 verification, QMOD build, and QASM/QMOD correspondence. It compares
with the best `outputs/best_verified_depth{D}_cx{C}.qasm` and promotes only a
strict lexicographic improvement, writing new files and never overwriting.
Tested: 177/425 passes all checks and is correctly refused (tie); a one-CX-deleted
mutant is rejected at contract scoring. Agents are told NOT to pass --promote.

### Verified: up to 9 concurrent ANDs on 18 wires (raises the width ceiling)

From `research/web_research_oracle_depth/REPORT.md` (F5), verified here under the
contract (opt 3, seed 42). RCCX keeps all single-qubit gates on the target and
uses controls only in CX steps (b in steps 1 and 3, a in step 2), so ANDs can
share control wires if each wire appears once per CX layer. A 9-AND ring on 18
wires (9 controls, 9 distinct targets), emitted step-interleaved: **depth 7,
27 CX**; exact (`Operator.equiv` True on the 8-qubit ring). The same ANDs emitted
one after another: depth 31. **Emission order is decisive; the transpiler will
not recover it.** Disjoint triples allowed only 6 per ~7 layers.
Other research leads worth building: F1 top-down SAT cover with CZ sinks and
MIXED x/y factors (the rank-10 minimality proof does not cover mixed factors);
F2 SAT pebbling as the liveness scheduler; F3 Maslov legality rules for
dirty-target hosting. No public write-up of this challenge by a top
participant was found.

### Gate-count / AND-count agent: finished (2026-09-23)

`research/gate_count_reduction/REPORT.md`. Contributed 177/425 (already
promoted). Could NOT lower the AND count: lowest verified AND content anywhere
in `research/` is 92.0 (177/428 lineage), 92.75 (177/425), 93.5 (177/426); none
of the 138 width-18 files below 90 units is a complete oracle. Key constraint
for the width route: the incumbent's AND network is only partly extractable
(57 of 92.75 units as clean RCCX gadgets) and those 57 sit in **13 dependency
levels with at most 7, ~4.4 on average, per level** — too narrow to sustain
width 6 by rescheduling. Why fewer ANDs is hard: 10 nonlinear feature dims per
axis (min degree 4, some forced to degree 6 by odd weight), and one axis's
features need >= 16 wires, so both axes force streaming. Implication: the
co-design route (a new, wider network) is now the main hope for 100-115.

### Linear-frame rank search: reproduces prior art

`research/linear_frame_rank_search/REPORT.md`. ~1M general linear frames: best
rank 9, always the known shear x_low ^= 31 when y5=1 — already in
`Y5_JOINT_AFFINE_FRAME_SCREEN.md` (which showed rank 9 raised cost, 76 -> 86),
and `agent_rank7_frame_search` reached rank 8 with a nonlinear frame. Rank is an
unreliable cost proxy; do not reopen.

### AND-network co-design agent: finished — BEST LEAD IN THE PROJECT (2026-09-23)

`research/and_network_codesign/REPORT.md`. New exact decomposition,
**independently re-verified by the main session (0 mismatches on all 4096)**:

    logo = D XOR R1 XOR R2' XOR E48
    D = x5 AND [x4==y5] AND valid(y) AND NOT carry3(e + V(y) + k)

x side is free and linear (fold e_i = x_i XOR NOT x3, carry-in k = NOT(x3 XOR x4);
e+k = |x-55| or |x-40| for every x >= 32). y side: V(y) = 7 - min(U(y),7), 3 bits
with don't-cares. R1=[2,26]x[29,53], R2'=[27,48]x[39,43], E48={32,48}x[17,21].
**~69.5 AND units (incumbent 93.5; rank 1 est. ~72), forward AND-depth 7.**
Predicted depth IF it fits in 18 wires: ~116-130 — top-five territory.
**Binding constraint: liveness** — one pass needs >= 19 wires; variant C2 is
exactly 18 with zero spare; the disc block alone (bound 15) did not compile
V+valid within 6 y-side spare wires. Missing capability: liveness-aware joint
synthesis of the y-side functions at the information limit.
No oracle built yet. Handed to the AND-width scheduler agent, which had
independently converged on y-side level codes (L19/L41/R19/R41) with don't-cares
via SAT + GPU and has a realiser (`research/and_width_scheduler/realize.py`)
applying the shared-control rule. Requested: disc block first, as a standalone
exact phase component, then rectangles, then compose.

### Session restart #2 (2026-09-23)

A second process restart stopped the scheduler agent mid-build and the SAT
cleanup. The scheduler had adopted the fold-chain decomposition
(`research/and_width_scheduler/discdef.py`, `blocks.py` = compute / diagonal
sink / exact mirror blocks, `fn_run.py`, `tker_sat.py`) and launched ~15 SAT
jobs (V+valid on 10-11 wires, x-flags ABC and y-flags Y1-Y3 on 9 wires, kernel
`tker_*`); all were killed before writing output except `tker_L2_U3_a0` (UNSAT,
158 s). The agent was resumed from its transcript and asked to relaunch them,
log progress periodically, and keep a PROGRESS.md. The low-priority SAT cleanup
was deliberately NOT restarted, to leave CPU for the build (it only refines a
negative certificate: x 13 + y 38 unknowns pending, all 27 resolved so far UNSAT).
If a session dies again: check `research/and_width_scheduler/PROGRESS.md`, then
resume the scheduler agent before relaunching anything.

### Route A closed by measurement (scheduler, 2026-09-23 ~03:00)

Rescheduling the incumbent's AND network cannot reach 100-115
(`research/and_width_scheduler/PROGRESS.md`, `routeA_bound.py`). Ideal schedule
of the 57 recovered units (13 levels, mean 4.38 ANDs/level, every level fully
concurrent, zero frame CX): depth 79-97 for those alone; the other 35.75 units
add >= ~36 at width 6; idealised floor ~115 before frames; realistic frames
(2.75 depth per 9-CX gap, measured) -> ~135-155. Binding constraint: AND DEPTH
(13 dependent levels), not wire count. Not buildable anyway (35.75 units have
no recoverable gadget boundaries). **Only live route: the fold-chain build.**

### PAUSED by the user (2026-09-23)

State at pause:
- **Best verified result: 177/425** (`outputs/best_verified_depth177_cx425.*`),
  still not registered on the leaderboard (shows the old 181/426).
- **Scheduler agent stopped** (transcript saved; resume it by SendMessage to its
  agent id, or re-brief a fresh agent from `research/and_width_scheduler/PROGRESS.md`).
  Last milestone (3): the plan reaches depth 109-120 only if every component
  fits in <= 3 AND layers in place; the co-design's minimum-AND XAGs for V need
  >= 12-13 y-side wires and V+valid does not embed in <= 12 wires (wide operand
  spans kill liveness); it was trying narrow-operand XAGs (support <= 2) and
  2-layer carry kernels. The agent had not yet written REPORT.md.
- **48 SAT/search processes SUSPENDED, not killed** (fn_v3.py, narrow_xag.py,
  fn_sat.py, seeded_sat.py, tker_sat.py + multiprocessing workers), PIDs in
  `research/and_width_scheduler/SUSPENDED_PIDS.txt`. Resume with
  `powershell -ExecutionPolicy Bypass -File research/and_width_scheduler/resume_suspended.ps1`.
  They do NOT survive a reboot or process restart; if gone, relaunch from the
  commands in PROGRESS.md / the log file names.
- Low-priority SAT cleanup of k7 unknowns not running (x 13 + y 38 pending).

### Pause lifted (2026-09-23)

All 48 suspended processes resumed intact (0 lost); scheduler agent resumed from its transcript and told not to relaunch them. SUSPENDED_PIDS.txt is now stale.

### Dedicated fold-chain reformulation agent (2026-09-23)

At the user's request a dedicated agent works the fold-chain route in `research/foldchain_reformulation/` (PROGRESS.md kept there). Split with the scheduler: scheduler = SYNTHESIS on the current formulation (narrow-operand XAGs + exact embedding, 2-layer carry kernels); new agent = REFORMULATION to cut y-side liveness (absorb valid into a 4-bit V, variant C2 / more don't-cares, split the two discs into sequential passes, conditional +10 mod 32 y-centre alignment, cheaper square R1). New agent limited to 4 CPU-heavy processes; GPU available to it.

### Scheduler Milestone 4 (2026-09-23): hard negatives on the fold-chain

- 2-layer in-place carry kernel c3=[e+k+V>=8] UNSAT for 6 configs (U 3-5, anc 0-2): the disc comparator needs >= 3 serial AND layers after V. The 109-120 synthetic plan assumed a 1-layer disc kernel, so the current formulation is deeper than planned.
- V+valid: no min-AND or narrow XAG combination embeds in <= 14 wires (budget 11) -- a no-uncompute bound.
- Input-CEGAR (`cegar_fn.py`) is the first method making progress (rounds 8-270 s) and may uncompute intermediates; 14400 s runs launched.
- Relayed to the reformulation agent: prioritise formulations that shorten/remove the serial carry and cut y-side live values.

### Scheduler Milestone 5 (2026-09-23): realistic fold-chain depth is ~150-160

With the REAL 3-stage Cuccaro carry kernel (synth_plan2.py, contract-measured): 3-layer components -> 150-161; 4+3 -> 155-179; 4+4 -> 188-200. The serial carry costs ~40 depth vs the idealised 1-layer kernel behind the earlier 109-120 estimate. **The current fold-chain formulation cannot reach the top five**; buildable it is ~150-160 (< 177), with 4-layer components no improvement. Top five now depends on the reformulation agent eliminating or collapsing the serial carry (its first idea: a 2-bit chain via V1'=V1^V2 plus one CCZ correction, which saves ~one stage). Incremental CEGAR (`inc_cegar.py`) running for V+valid, rect flags.

### Reformulation Milestone 1 (2026-09-23 ~08:40): carry-free PAIRED-BILINEAR design predicts 101-105

`research/foldchain_reformulation/PROGRESS.md`. Exact reformulations (0/4096), synthetic end-to-end depth under the contract (3 seeds): S0 current chain 150/152/160; S1 2-bit chain 128/124/122; S3 1-bit comparator 123/124/117; **S2 two paired-bilinear blocks x 3 terms, NO kernel: 101/105/102** (3x4 flag layers: 109/119/116). "Paired" = x-flags may depend on (x, y5); paired rank of the logo = 6 (lower half 6, upper 5). Main session independently confirmed the disc part is exactly a carry-free 5-term bilinear form over the free fold t=e+k (x-flags = disjoint intervals of t, y-flags = nested row thresholds 30/26/22/18/9 rows; 0 mismatches). Synthetic = random operands of the right shape; liveness of the REAL flags not yet shown. Handoff: reformulation agent writes exact build spec `s2_spec.json` (+ per-flag cost, liveness bound); scheduler builds S2 from it block by block. Fallbacks S1/S3/3x4 at 109-128 all beat 177.

### Reformulation Milestone 2 (2026-09-23 ~09:45) + scheduler Milestone 6

Paired rank: 6 terms minimum (lower half 6, upper 5). Liveness floor 16 per 3-term block (8 x-side + 8 y-side). **N2 = N1 + two exact XOR moves: both blocks at 16 wires (2 spare), exact**; N1 block 2 is 18 (zero spare). Depth driver = AND count per side per block: Ur=3 (<=~12 ANDs in 3 layers) -> 101-105; Ur=4 -> 109-119; Ur=5 -> 128-131; 3 blocks -> 150-162. Real N1 flags cost ~4-5 ANDs each at depth <= 3. Scheduler retargeted to S2 (synthetic 100-105 reproduced at 3 layers; flags degree 5-6 -> >= 3 AND layers per side); it was told to prefer N2. Spec generator `s2_spec.py` + checker `s2_check.py` exist; `s2_spec.json` pending N2 costing.

### S2 build spec landed and verified (2026-09-23)

`research/foldchain_reformulation/s2_spec.json` ("S2 from N2[0]"): logo = XOR_j X_j(x,y5) AND Y_j(y), 6 terms, blocks B1={0,1,2}, B2={3,4,5}, sink 3 CZ per block, liveness 16 per block. Verified by the agent's s2_check.py AND an independent main-session check from raw tables only (bit x+64*y5 / bit y): 0 mismatches / 4096, 1097 marked; one-bit-flip negative control -> 13 mismatches. Per-flag min ANDs at depth <= 3 so far (upper bounds): T0 y6 x5, T1 y5 x5, T2 y4 x4, T3 y6 -> block 1 ~14 x / ~15 y vs ~12-per-side target for 101-105; joint per-side synthesis sharing ANDs is what keeps it in the top five (else ~109-131). Scheduler told to build this spec with joint per-side synthesis.

### Reformulation agent FINISHED (2026-09-23) — honest verdict

`research/foldchain_reformulation/REPORT.md`. Chain removed exactly (S2: 6 paired rank-1 terms, 2 blocks x 3, liveness 16/16 = floor), but at measured per-flag AND counts (x ~19/19, y ~15/17 per block for V1) the design predicts **~128-155**, not the top five. Top five (<=127) needs joint in-place synthesis at <= ~12-13 ANDs per side per block; unproven. Main-session GPU cross-check: y side of N2 came within 1-2 bits (block 2 at 11 ANDs vs single-flag sum 18: real sharing); x side of V1 block 1 stuck at 13-22 of 384 bits wrong from 14 to 24 ANDs: x-side sharing not materialising. Recommended build V1 with joint per-side synthesis; fallback F_2bitC2. Nothing built; scheduler CEGAR has not converged on any side after 2+ h.

### Scheduler Milestone 8 (2026-09-23): S2 is liveness-bound — decisive negative

Exact in-place embedding (no mid-program uncompute) of block 1's merged minimum XAGs: y side NOT embeddable at 8-12 wires (budget 9), x side NOT at 9-13 (budget 10 incl. y5). Fitting needs mid-program uncompute -> ~5 layers -> synthetic 166-181, i.e. NO improvement over 177. Update-grammar CEGAR allowing uncompute: none of the 4 block-sides converged in 2-4 h (no UNSAT proof either); jobs left with 4 h limits, writing s2_N2_*.json on success (assemble with build_s2.py, check with check_s2_block.py). Main-session GPU x-side (V1 block 1): 13-22/384 bits wrong from 14 to 24 ANDs. **Assessment: no route found in this session produces a buildable circuit below 177; 177/425 is the realistic final result unless a CEGAR job lands.**

### Scheduler agent FINISHED (2026-09-23)

`research/and_width_scheduler/REPORT.md` (saved by main session). No circuit below 177. Route A capped by AND depth (~135-155 realistic, not buildable). Re-synthesis capped by liveness: no fold-chain or S2 part fits in <= 3 layers in place. Buildable fallback would be 4-layer S2 at ~133-140 only if 4-layer in-place side programs exist; ~18 CEGAR searches (4 h limits) still running and write `s2_N2_*.json` on success -> `check_s2_block.py`, then `build_s2.py NAME xB1 yB1 xB2 yB2`, then `research/promote_candidate.py`. Main session watching for those files.

### GPU joint side search finished (2026-09-23)

`research/s2_gpu_side/REPORT.md`: 52 validated runs, no exact program. y side (N2) closest 1/192 bits at 15 ANDs (block 1), 2/192 at 11 (block 2; real sharing vs single-flag sum 18). x side (V1) closest 13/384 at 20 (block 1), 8/384 at 14 (block 2), no convergence 14-24 ANDs. Agrees with the scheduler's exact embedding negative. GPU is now idle.

## ADDENDUM 2026-09-23 14:34 — new best 177/420
outputs/best_verified_depth177_cx420.{qasm,qmod} (+ _verification.json, _qmod_correspondence.json), promoted by the main
session via research/promote_candidate.py (all gates passed). QASM sha256 6ddc5494...0118, QMOD sha256 dd3156d6...b6b6.
Found by research/oob_opt177 (CX-group SAT, reachable-state window resynthesis, SAT commutation reschedule).
Depth-176 is blocked by one 190-link dependency chain on q15/q16/q17 through all 177 layers.
Round of 2026-09-23 afternoon (depth < 130 hunt): closed = CCB 3-term and 2-term/4-term, CX-dense phase polynomials
(>=151), pass-C interleave (A+B floor ~140), web intel (nothing new). Live = foldchain_phasecarry (21-rotation
carry-lookahead phase kernel) + fc_yside_code (in-place V/valid code). Classiq platform browser agent waits for the
user to sign in to platform.classiq.io in the browser pane.

## ADDENDUM 2026-09-23 16:53 — new best 176/421
outputs/best_verified_depth176_cx421.{qasm,qmod} (+ verification, correspondence), promoted by the main session;
all gates passed. Method: research/oob_opt177/relax176.py (MaxSAT: exact commutation schedule with per-wire slot
conflicts minimised) names the exact wire/layer that blocks depth D-1; a local 3-CX rewrite of that slot removes it.
Depth 175: one conflict left at 423 CX (r2/rel2g_T175_step1_cost1.qasm; q15 fanout at L73).
