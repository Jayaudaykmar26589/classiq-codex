# Classiq model files for the177/426 oracle

Use `classiq_logo_depth177_cx426_sdk_superposition_probe.qmod` for a Classiq synthesis experiment in the **Model text editor**. The local Classiq SDK accepted this model with18-qubit maximum width and depth optimization; its hardware basis is U3/CX. The816-operation oracle body matches `best_verified_depth177_cx426.qasm` gate for gate.

The probe prepares the12 coordinate qubits with Hadamards before calling the oracle. That preparation ensures all coordinates are represented in the synthesis harness. It is not part of the standalone submission circuit. Any newly synthesized export needs oracle extraction and another all4096-input verification; preparation may move during compilation, so blindly deleting apparent leadingHadamards is unsafe.

`best_verified_depth177_cx426.qmod` contains a separate oracle function plus main. `classiq_logo_depth177_cx426_main_only.qmod` inlines its exact native gates into main. Both use allocate and start from allocated states; a bare zero-state main can allow synthesis to simplify phase behavior. Prefer the superposition probe when investigating synthesis.

The user previously confirmed that Graphical Model→Upload Model rejects allocate. These files target the Model text editor; removing allocation does not provide a initialized18-qubit output, and Graphical Model compatibility is not asserted.

The verified standalone artifact for scoring is `best_verified_depth177_cx426.qasm`: depth177, CX426, width18. Its1097 marked phases and helper cleanup pass all4096 inputs. This is a local score, not a new official platform score. No cloud synthesis was performed for these files.

The Classiq SDK probe uses machine_precision16 and32-decimal text export to preserve the supplied angles. Its companion `.synthesis_options.json` records the settings. The older428/429 files remain available for historical comparison.
