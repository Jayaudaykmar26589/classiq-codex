# Current verified oracle

The current local best is **depth 176, CX 421, width 18**, with 400 U3 gates.

- `best_verified_depth176_cx421.qasm`: standalone native U3/CX oracle, without preparation or measurement.
- `best_verified_depth176_cx421.qmod`: matching 821-operation oracle body and a native QMOD main wrapper.
- `best_verified_depth176_cx421_verification.json`: exhaustive 4096-input phase, coordinate-restoration and clean-helper check.
- `best_verified_depth176_cx421_qmod_correspondence.json`: numeric gate-body comparison.

Re-checked on 2026-09-24 with an independent sparse all-4096 verifier: grader metrics (18, 176, 421), max phase error 6.6e-13, max helper leakage 3.0e-23. The QMOD oracle body matches the QASM gate for gate (821/821). Research from that session is in `RESEARCH_2026-09-24_block_kernel.md`.

## Previous best (177/426)

The previous best was **depth177, CX426, width18**, with390U3 gates.

- `best_verified_depth177_cx426.qasm`: standalone native U3/CX oracle, without preparation or measurement.
- `best_verified_depth177_cx426.qmod`: matching816-operation oracle body and a native QMOD main wrapper.
- `best_verified_depth177_cx426_verification.json`: exhaustive4096-input phase, coordinate-restoration and clean-helper check.
- `best_verified_depth177_cx426_qmod_correspondence.json`: numeric gate-body comparison.

The two six-qubit coordinate registers occupy q[0:6] and q[6:12]; q[12:18] are six initially clean helpers. Exactly1097 marked pixels receive the negative phase, up to one input-independent global phase. The score includes the complete oracle and cleanup.

This improves the previous177/428 circuit by twoCX. It does not yet satisfy depth<177, nor the supplied top-three leaderboard threshold. Original177/428 and177/429 pairs remain unchanged as historical references.

The new construction removes original nativeCX632 andCX671 and refits all one-qubit rotations in the two independent nine-wire late transformations. Each transformation was matched on all64 reachable complex input columns, including phase. The full exported oracle was then verified on all4096 coordinate inputs. Details are in `../research/joint_state_phase_next/REPORT.md`.

## Classiq files

`classiq_logo_depth177_cx426_main_only.qmod` inlines the816 native gates in a single main function for the Model text editor. It uses allocate; Graphical Model compatibility is not claimed.

For synthesis experiments, `classiq_logo_depth177_cx426_sdk_superposition_probe.qmod` was built locally using Classiq SDK1.29.1. Its oracle body matches QASM exactly, and main prepares the12 coordinate qubits withH gates. These12 preparation gates are outside the standalone submission oracle. The SDK model uses max_width18, depth optimization and a U3/CX hardware basis. Model precision is16 digits, and QMOD text was exported with32 decimal places.

No new Classiq cloud synthesis or official leaderboard score is claimed. `CLASSIQ_UPLOAD.md` explains the distinction between the standalone oracle and the synthesis probe.
