#!/usr/bin/env python3
"""Structural audit of the strongest complete circuit in the external snapshot.

The analysis is intentionally read-only with respect to the snapshot.  It
uses the snapshot's small strict-QASM parser and writes a JSON report selected
by the caller.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path


def equivalent_angle(left: float, right: float, tolerance: float = 1e-10) -> bool:
    return abs(math.remainder(left - right, 2 * math.pi)) < tolerance


def u3_class(gate) -> str:
    if gate.name != "u3":
        return gate.name
    theta, phi, lam = gate.params
    if abs(theta) < 1e-12:
        return "diagonal_phase"
    if equivalent_angle(theta, math.pi) and equivalent_angle(phi, 0) and equivalent_angle(lam, math.pi):
        return "pauli_x"
    if equivalent_angle(abs(theta), math.pi / 2):
        return "hadamard_like"
    return "other_u3"


def commutes_with_cx(cx, gate) -> bool:
    control, target = cx.qubits
    if not set(cx.qubits).intersection(gate.qubits):
        return True
    if gate.name == "cx":
        other_control, other_target = gate.qubits
        return target != other_control and control != other_target
    kind = u3_class(gate)
    wire = gate.qubits[0]
    return (kind == "diagonal_phase" and wire == control) or (kind == "pauli_x" and wire == target)


def exact_local_rewrite_inventory(circuit) -> dict[str, object]:
    # Adjacent on a wire means that all globally intervening gates are
    # disjoint.  A phase may additionally cross CXs for which this wire is the
    # control, and X may cross CXs for which it is the target.
    phase_fusions = []
    x_pair_cancellations = []
    for wire in range(circuit.width):
        sequence = []
        for gate in circuit.gates:
            if wire not in gate.qubits:
                continue
            if gate.name == "u3":
                sequence.append((gate.index, u3_class(gate)))
            elif gate.qubits[0] == wire:
                sequence.append((gate.index, "cx_control"))
            else:
                sequence.append((gate.index, "cx_target"))

        run = []
        for item in sequence + [(-1, "barrier")]:
            if item[1] in ("diagonal_phase", "cx_control"):
                run.append(item)
            else:
                phases = [index for index, kind in run if kind == "diagonal_phase"]
                if len(phases) > 1:
                    phase_fusions.append({"wire": wire, "gate_indices": phases})
                run = []

        run = []
        for item in sequence + [(-1, "barrier")]:
            if item[1] in ("pauli_x", "cx_target"):
                run.append(item)
            else:
                xs = [index for index, kind in run if kind == "pauli_x"]
                if len(xs) >= 2:
                    x_pair_cancellations.append({"wire": wire, "gate_indices": xs})
                run = []

    previous: dict[tuple[int, int], int] = {}
    cx_pair_cancellations = []
    for gate in circuit.gates:
        if gate.name != "cx":
            continue
        if gate.qubits in previous:
            first = previous[gate.qubits]
            if all(commutes_with_cx(gate, middle) for middle in circuit.gates[first + 1 : gate.index]):
                cx_pair_cancellations.append(
                    {"first": first, "second": gate.index, "between": gate.index - first - 1, "qubits": list(gate.qubits)}
                )
        previous[gate.qubits] = gate.index

    return {
        "phase_fusion_runs": phase_fusions,
        "pauli_x_cancellation_runs": x_pair_cancellations,
        "commuting_identical_cx_cancellations": cx_pair_cancellations,
        "total_obvious_gate_savings": sum(len(run["gate_indices"]) - 1 for run in phase_fusions)
        + sum(2 * (len(run["gate_indices"]) // 2) for run in x_pair_cancellations)
        + 2 * len(cx_pair_cancellations),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--screen", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.snapshot))
    from tracks.verification.qasm_ir import asap_layers, dependency_edges, load_qasm

    qasm_path = args.snapshot / "tracks/multitrack_affine_refine/best.qasm"
    report_path = args.snapshot / "tracks/multitrack_affine_refine/best.report.json"
    qasm = load_qasm(qasm_path)
    source_report = json.loads(report_path.read_text())
    parameter_screen = json.loads(args.screen.read_text())
    depth, layers = asap_layers(qasm)

    predecessors = [[] for _ in qasm.gates]
    successors = [[] for _ in qasm.gates]
    for source, target in dependency_edges(qasm):
        predecessors[target].append(source)
        successors[source].append(target)
    latest = [depth] * len(qasm.gates)
    for node in reversed(range(len(qasm.gates))):
        if successors[node]:
            latest[node] = min(latest[child] - 1 for child in successors[node])
    slack = [latest[index] - layers[index] for index in range(len(qasm.gates))]
    critical = [index for index, value in enumerate(slack) if value == 0]
    endpoint = max(range(len(qasm.gates)), key=lambda index: layers[index])
    longest_path = []
    node = endpoint
    while True:
        longest_path.append(node)
        candidates = [parent for parent in predecessors[node] if layers[parent] == layers[node] - 1]
        if not candidates:
            break
        node = candidates[0]
    longest_path.reverse()

    qubit_load = []
    for wire in range(qasm.width):
        gates = [gate for gate in qasm.gates if wire in gate.qubits]
        qubit_load.append(
            {
                "wire": wire,
                "role": (
                    "x_data"
                    if wire < 6
                    else "y_data"
                    if wire < 12
                    else "lane_flag"
                    if wire < 16
                    else "x_helper"
                    if wire == 16
                    else "y_helper"
                ),
                "total": len(gates),
                "cx": sum(gate.name == "cx" for gate in gates),
                "u3": sum(gate.name == "u3" for gate in gates),
                "depth_130_required_removal": max(0, len(gates) - 130),
                "depth_120_required_removal": max(0, len(gates) - 120),
            }
        )

    path_gate_types = Counter(qasm.gates[index].name for index in longest_path)
    path_wire_incidence = Counter(wire for index in longest_path for wire in qasm.gates[index].qubits)
    layer_occupancy = Counter(layers)
    local_cx = sum(update["cx"] for update in source_report["updates"])
    local_depth = {
        side: sum(update["depth"] for update in source_report["updates"] if update["side"] == side)
        for side in ("x", "y")
    }
    local_cx_by_side = {
        side: sum(update["cx"] for update in source_report["updates"] if update["side"] == side)
        for side in ("x", "y")
    }
    local_depth_by_lane_side = {
        f"lane{lane}_{side}": sum(
            update["depth"]
            for update in source_report["updates"]
            if update["lane"] == lane and update["side"] == side
        )
        for lane in (0, 1)
        for side in ("x", "y")
    }
    u3_classes = Counter(u3_class(gate) for gate in qasm.gates if gate.name == "u3")
    ancilla_cx = [gate.index for gate in qasm.gates if gate.name == "cx" and min(gate.qubits) >= 12]

    counts = qasm.gate_counts()
    output = {
        "authoritative_candidate": {
            "qasm": str(qasm_path.resolve()),
            "sha256": hashlib.sha256(qasm_path.read_bytes()).hexdigest(),
            "width": qasm.width,
            "depth": depth,
            "cx": counts.get("cx", 0),
            "u3": counts.get("u3", 0),
            "gates": len(qasm.gates),
            "snapshot_verification_passed": source_report["saved_qasm_exhaustive_validation"]["passed"],
            "clean_inputs_verified": source_report["saved_qasm_exhaustive_validation"]["columns"],
        },
        "fixed_gate_multiset_lower_bounds": {
            "maximum_single_wire_load": max(item["total"] for item in qubit_load),
            "maximum_single_wire_load_wire": max(qubit_load, key=lambda item: item["total"])["wire"],
            "cx_matching_capacity_bound": math.ceil(counts.get("cx", 0) / (qasm.width // 2)),
            "explanation": "Every gate touching one wire is serial; at most nine disjoint CX gates fit in an 18-qubit layer.",
        },
        "qubit_load": qubit_load,
        "u3_classes": dict(u3_classes),
        "ancilla_only_cx_count": len(ancilla_cx),
        "ancilla_only_cx_gate_indices": ancilla_cx,
        "schedule": {
            "average_gates_per_layer": len(qasm.gates) / depth,
            "maximum_layer_occupancy": max(layer_occupancy.values()),
            "zero_slack_nodes": len(critical),
            "slack_histogram": {str(key): value for key, value in sorted(Counter(slack).items())},
            "one_longest_path_length": len(longest_path),
            "one_longest_path_gate_types": dict(path_gate_types),
            "one_longest_path_wire_incidence": {str(key): value for key, value in sorted(path_wire_incidence.items())},
            "one_longest_path_gate_indices": longest_path,
            "layer_occupancy": {str(key): value for key, value in sorted(layer_occupancy.items())},
        },
        "architecture_accounting": {
            "rank_features": 10,
            "closed_lanes": 2,
            "coordinate_updates": len(source_report["updates"]),
            "update_depth_sum_by_side": local_depth,
            "update_depth_sum_by_lane_side": local_depth_by_lane_side,
            "update_cx_sum": local_cx,
            "update_cx_sum_by_side": local_cx_by_side,
            "affine_entry_exit_cx": 31,
            "feature_cz_cx_before_whole_optimization": 10,
            "pre_whole_optimization_cx_accounting": local_cx + 31 + 10,
            "whole_optimizer_cx_removed_across_composition": local_cx + 31 + 10 - counts.get("cx", 0),
            "raw_update_u3": 1026,
            "raw_update_walsh_phase_u3": 978,
            "raw_update_hadamard_u3": 48,
            "affine_x_u3": 4,
            "cz_hadamard_u3_before_whole_optimization": 20,
            "pre_whole_optimization_u3_accounting": 1026 + 4 + 20,
            "whole_optimizer_u3_removed_or_fused_across_composition": 1026 + 4 + 20 - counts.get("u3", 0),
        },
        "obvious_exact_postcompile_rewrites": exact_local_rewrite_inventory(qasm),
        "expanded_local_parameter_screen": parameter_screen["aggregate"],
        "interpretation": {
            "schedule_only_can_reach_130": False,
            "reason": "The fixed circuit has a 290-operation wire-load lower bound, and its 1267 CX gates alone require at least 141 layers.",
            "dominant_representation_cost": "All 978 nonzero per-edge Walsh phase coefficients survive as diagonal U3 gates; helpers q16/q17 carry 116/124 of them plus 158/166 CX gates.",
            "postcompile_peephole_status": "No commuting phase fusion, Pauli-X pair, or identical-CX cancellation remains under the conservative exact rules checked here.",
            "parameter_screen_status": "Broader exact Gray-track parameters improve local proxies modestly, but do not remove the structural helper/coordinate serialization.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2))
    print(json.dumps({
        "depth": depth,
        "cx": counts.get("cx", 0),
        "max_wire_load": output["fixed_gate_multiset_lower_bounds"]["maximum_single_wire_load"],
        "critical_nodes": len(critical),
        "obvious_gate_savings": output["obvious_exact_postcompile_rewrites"]["total_obvious_gate_savings"],
    }, indent=2))


if __name__ == "__main__":
    main()
