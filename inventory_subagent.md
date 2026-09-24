# Inventory of `external_classiq_oracle_1609/source_snapshot`

## Result

The strongest trustworthy **complete** strict 18-qubit oracle in this snapshot is:

`artifacts/independent_affine_multitrack_candidate/logo_oracle.qasm`

- measured directly from the saved file: **depth 337, CX 1,267, U3 1,010, 2,277 gates, width 18**;
- QASM SHA-256: `9c3639733bd5e90ee8f007209018822616d4aafe8db9d4579685954f3adeba54`;
- QMOD SHA-256: `f5bba74d8697bb1e1bf59716147244f3dd81a74beb8ca13732fa10fa5668b129`;
- manifest hashes and all four metrics match the current bytes;
- QASM/QMOD gate correspondence is claimed exact with maximum angle error 0;
- both the source and packaged QASM passed a floating-point numerical check of all 4,096 clean-input columns with one common global phase, zero logical-data mismatches, maximum column residual `1.694695570557978e-14`, residual plus discarded-entry bound `1.719188506540925e-14`, and reported operator-error upper estimate `9.264664170244606e-13`;
- it also passed three random full-support state tests. This is strong numerical evidence, not symbolic or interval-arithmetic proof.

There is **no complete 18-qubit candidate below depth 337** in the snapshot. The only strict file below 337 is `tracks/caterpillar/custom_factor0_strict.qasm` at 227/200/130, but it implements only factor 0 of the ten-factor oracle. It is a component, not a submission. Consequently this snapshot contains no 120–130-depth candidate and does not improve the separately known 177-depth circuit.

## Exhaustive scan

I did not modify `source_snapshot`. I parsed and independently scored every QASM with the snapshot's strict parser and recomputed every QASM SHA-256:

- 304 QASM files total;
- 257 parse as strict OpenQASM 2 `u3`/`cx` circuits;
- 168 are strict width-18 files;
- those 168 files contain 147 unique byte hashes;
- source reports describe 146 paths / 130 unique hashes as complete phase-oracle or reference-circuit variants;
- 3 paths are components, 8 compute an ordinary Boolean output rather than a phase oracle, 4 are explicitly uncorrected, and 7 TKET exports are explicitly invalid because of an omitted `q[9] <-> q[11]` output permutation.

The complete per-file inventory is in `agent_work/external_native18_classified.json`. It records path, full SHA-256, width/depth/CX/U3/gate count, semantic class, and the strongest hash-bound verification claim found. `agent_work/external_qasm_inventory.json` also includes every non-18-qubit and unparsable QASM. `agent_work/external_candidate_claims.json` joins hash-bound metadata to stored QASM bytes. These machine-readable files are the exhaustive answer for duplicated and postprocessed variants; the tables below give the frozen packages and one representative leader per complete architecture.

## Frozen complete width-18 packages

All six saved QASM and QMOD hashes below match their manifests, as do width/depth/CX/U3. The seventh package, `independent_multitrack_candidate`, is a complete width-16 circuit (372/1,199/955) and is excluded from this exact-width table.

| Package | Depth | CX | U3 | QASM SHA-256 | QMOD SHA-256 | Verification claimed |
|---|---:|---:|---:|---|---|---|
| affine multitrack | 337 | 1,267 | 1,010 | `9c3639733bd5e90ee8f007209018822616d4aafe8db9d4579685954f3adeba54` | `f5bba74d8697bb1e1bf59716147244f3dd81a74beb8ca13732fa10fa5668b129` | all 4,096 saved-QASM clean columns + 3 random states; pass |
| parallel multitrack | 343 | 1,267 | 1,011 | `8f4230227f3f7d096bd91eb728d48de6eff49bfaa6c53c05c93d7454c6470cb6` | `7ff50aa23053b5de4716b16832b6b3d4dd7040ccf4606210b778c68af2217d52` | all 4,096 saved-QASM clean columns + 3 random states; pass |
| oriented rotation | 525 | 1,411 | 1,071 | `cd4b36b8b81f6e1522b14a27c98b76e3a797601d9ebcee64a991d39ab32c866a` | `41eb91cf52f6d5bafa3d55fce9c7c9e8f14be4474f987118af7bbb42bf16cdc1` | all 4,096 saved-QASM clean columns + 3 random states; pass |
| closed rotation | 576 | 1,388 | 1,067 | `e190588c16f63573d3b6dbc20e408cd12b2b41a17d59ba93499cbce29217c4a5` | `cf08e3d52cdb984fc1181cb829b6330a42561e2e9bf7078b16f808ae981219b5` | all 4,096 saved-QASM clean columns + 3 random states; pass |
| relative-LUT hybrid | 726 | 1,109 | 770 | `af77261a95679c96c14cd6957280d9979d814bb4f7db9d34881c4fc1b344c824` | `447c86b46bcd09c85082ef2a9fd0b405743409620962f27894abb233887c9c94` | exhaustive 4,096-input logical monomial check + 3 random saved-QASM states; no all-column QASM claim |
| early hybrid phase | 746 | 1,168 | 846 | `a0ac895bf2d3b4cdd256a4df75cc281db397ecddac7c23f420e2005435910bac` | `77905347427984eb090b20f9523bfe3a927a4bdc28c1deaf8c45c565b61ce718` | random saved-QASM states pass; package manifest has no exhaustive-verification field |

Every package says `qmod_gate_correspondence=true`, `max_qmod_angle_error=0.0`, `remote_synthesis_performed=false`, `official_submission_performed=false`, and `beats_incumbent=false`.

## Complete architecture leaders

These are the lowest-depth representative files for the other complete families. Metrics and hashes were recomputed from the saved files. Full paths, all non-leading variants, full hashes, and attached evidence are in the exhaustive JSON inventory.

| Family / representative | Depth | CX | U3 | SHA-256 prefix | Strongest claim in snapshot |
|---|---:|---:|---:|---|---|
| changed feature basis (`multitrack_basis_search/best_changed_basis.qasm`) | 346 | 1,271 | 1,002 | `a096d862c8e55f5b` | all 4,096 saved-QASM columns pass |
| integer-potential RX (`integer_potential_lifts/best.qasm`) | 355 | 1,293 | 1,019 | `0c9aed3b36734068` | all 4,096 saved-QASM columns + random states pass |
| signed-potential RX (`signed_potential_rx/best.qasm`) | 356 | 1,331 | 1,040 | `b846082695779338` | all 4,096 saved-QASM columns pass |
| one-lane four-track tour (`multitrack_tour_search/best.qasm`) | 372 | 1,199 | 955 | `91c8f5fffd5b6165` | all 4,096 saved-QASM columns + random states pass |
| changed-basis four-track (`multitrack_basis/basis_3_complement1.qasm`) | 375 | 1,229 | 955 | `b654376ce152bf72` | all 4,096 saved-QASM columns + random states pass |
| fixed-tour four-track RX (`multitrack_rx/oracle_complement3.qasm`) | 387 | 1,289 | 1,071 | `174372c389692efa` | all 4,096 saved-QASM columns + random states pass |
| correction-free RX tour (`rotation_tour_search/best.qasm`) | 508 | 1,301 | 955 | `bed3383dd808f520` | all 4,096 saved-QASM columns + random states pass |
| parallel corrected phase (`phase_parallel_research/...tket_strict.qasm`) | 644 | 862 | 697 | `39e80574dad40119` | all 4,096 saved-QASM columns + random states pass |
| closed phase frame (`closed_phase_frame/...tket_strict.qasm`) | 708 | 851 | 670 | `4a6f532ae69caaba` | all 4,096 saved-QASM columns + random states pass |
| corrected relative-phase rails (`closed_phase_correction/...tket_strict.qasm`) | 721 | 857 | 669 | `b19e4b8b4f0c38c0` | exact 4,096-input phase bookkeeping/local operators + random saved-QASM states |
| corrected materialized TKET relative LUT | 752 | 1,094 | 756 | `59aedbf7fb9b0db7` | random saved-QASM states pass; explicit output swap retained |
| affine row-class basis | 760 | 1,154 | 823 | `11e2981e93038dc7` | exhaustive logical 4,096-input claim; no hash-bound all-column report found |
| direct rank phase | 1,439 | 995 | 991 | `4a3d814bc70b6ad4` | exact logical 4,096-input check + two saved-QASM basis inputs |
| rank trie | 1,491 | 1,042 | 1,016 | `a0eff0ca381d15c2` | exact logical construction; sampled saved-QASM evidence |
| balanced direct phase | 1,797 | 2,279 | 2,413 | `b96cc92b2314eaa2` | exact truth table + random saved-QASM states |
| affine-coset classifier | 1,895 | 2,017 | 2,294 | `6590e4e1b358854a` | exhaustive final-QASM isometry claim + random states |
| direct geometric prefix | 2,055 | 1,346 | 1,582 | `a7b5ba33911bd307` | exact logical 4,096 inputs + marked/unmarked saved-QASM samples |
| interval-native phase | 2,093 | 2,622 | 2,805 | `1ce6e7cbf6b484d1` | exhaustive cover certificate + random saved-QASM states |
| geometric XAG | 2,136 | 2,219 | 1,219 | `8fe5ecd47cb9c372` | all 4,096 saved-QASM diagonal amplitudes pass |
| shared depth-7 trie | 2,160 | 1,346 | 1,394 | `cf74aa3e9418483b` | exact logical 4,096 inputs + two saved-QASM basis states |
| folded geometry | 2,380 | 2,541 | 2,790 | `618a2c7c3a50e442` | exact logical 4,096 inputs + random saved-QASM states |
| relative-phase resynthesis | 2,790 | 2,211 | 2,395 | `d74a1147a692a4bb` | exact logical 4,096 inputs + random saved-QASM states |
| in-place LUT phase | 2,919 | 1,739 | 1,890 | `e29ca646ce3e5a83` | exact symbolic construction + random saved-QASM states |
| batched rank features | 2,937 | 2,007 | 2,306 | `a44c64a0319eb97e` | exhaustive logical monomial simulation; no all-column QASM claim |
| LUT pebble root phase | 3,250 | 1,967 | 2,163 | `7e17089f8cfd77d6` | exhaustive logical/symbolic construction + random saved-QASM states |
| isolated SAT features | 3,245 | 2,936 | 1,306 | `17319df67615bc25` | exhaustive 4,096-input logical monomial simulation |
| borrowed-prefix direct phase | 3,333 | 2,792 | 3,275 | `e93a62d07e119767` | exact model/logical checks + random saved-QASM states |
| natural one-flag stream, phase anchored | 3,899 | 1,754 | 3,566 | `6ab2764682473b4e` | simultaneous all-4,096-amplitude statevector check passes |
| geometry product cover | 4,207 | 2,185 | 2,106 | `fa01512cd060cd13` | exhaustive logical 4,096 inputs + sampled QASM checks |
| sequential rank XAG phase | 4,358 | 2,347 | 2,551 | `31c4353fc2e37bd9` | all 4,096 saved-QASM amplitudes pass |
| supplied Classiq baseline realization | 5,329 | 3,502 | 4,373 | `e229f95efa7fc255` | baseline provenance; no adjacent hash-bound verifier found |
| nonlinear ANF shear rewrite | 5,963 | 4,284 | 4,638 | `a45b097481f2eafe` | exhaustive truth table + random saved-QASM states |
| Caterpillar feature pebbling | 6,448 | 5,476 | 4,077 | `0f2aa2047cf9eb78` | exhaustive logical 4,096-input check |
| affine-searched ESOP | 7,619 | 4,152 | 4,661 | `261f321daf89906b` | exhaustive truth table; compiler-equivalence claim |
| Classiq-native rank stream | 10,006 | 5,720 | 7,216 | `9bcc99783cd391b0` | QMOD predicate checked; final QASM not exhaustively verified |
| recursive ESOP reference | 11,799 | 6,695 | 7,643 | `c8618f28339172a4` | older construction; no adjacent hash-bound verifier found |
| Classiq-native rank scratch | 15,179 | 9,054 | 11,549 | `9292b0d828bb6a7f` | QMOD predicate checked; final QASM not exhaustively verified |
| affine direct sparse XAG | 24,329 | 12,946 | 13,788 | `b7a1d97ffea6cd60` | all saved-QASM diagonal amplitudes pass |
| BDD disjoint-SOP | 34,657 | 18,964 | 21,341 | `0a0c8ef0fa2292c2` | exact BDD/cover construction; no all-column QASM claim found |

## Files that must not be promoted

- `tracks/caterpillar/custom_factor0_strict.qasm` is the tempting 227-depth file, but it is only one factor. The other two low-depth `rank_circuit/*rectangles.qasm` files implement only square-plus-bar components (478/320 and 569/324).
- All four `tracks/closed_phase_stream/*uncorrected.qasm` files have a known input-dependent residual phase. Their depths 686/709 are not valid oracle scores.
- `tracks/research_phase_duality/relative_lut_rank_tket_strict.qasm` and the seven stage-3/stage-4 exports in `tracks/tket_correctness_audit` fail because TKET's implicit `q[9] <-> q[11]` permutation was omitted. The apparent 752/1,091 score is invalid. The repaired circuit is 752/1,094.
- Eight `*_output.qasm` files in the LUT tracks compute a Boolean output; only their `*_phase.qasm` or `*_rootphase.qasm` siblings are phase oracles.
- `tracks/compressed_phase_table/best_phase_core.qasm`, classifier-only QASMs, local RX edge QASMs, and the many small isometry/LUT blocks are components even when their local verification is exhaustive. They are not represented in the strict width-18 candidate count unless the file itself allocates 18 wires.
- Proxy values in scheduler, Walsh-support, AND-count, T-depth, LUT, or pebbling JSON are not U3/CX circuit depths. In particular, the 614-CX fingerprint study emits no strict QASM and proves no candidate at that score.

## Trust conclusion

For reuse, the 337-depth affine multitrack package is the only strongest artifact. The 343, 346, 355, 356, 372, 375, and 387 files are useful nearby architectural controls with all-input saved-QASM numerical evidence. None is competitive with depth 177, and none supplies a credible splice or component whose measured complete score approaches 120–130.
