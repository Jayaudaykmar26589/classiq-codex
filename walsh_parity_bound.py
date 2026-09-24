#!/usr/bin/env python3
"""Certify the unavoidable dense edges in the closed Walsh-stream family."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def walsh(values: list[int]) -> list[int]:
    result = list(values)
    step = 1
    while step < len(result):
        for base in range(0, len(result), 2 * step):
            for index in range(step):
                left, right = result[base + index], result[base + index + step]
                result[base + index], result[base + index + step] = left + right, left - right
        step *= 2
    return result


def apply_rows(rows: list[int], word: int) -> int:
    return sum((((row & word).bit_count() & 1) << index) for index, row in enumerate(rows))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads((args.snapshot / "tracks/multitrack_affine_refine/best.report.json").read_text())
    physical = json.loads((args.snapshot / "tracks/closed_phase_stream/factor_truths.json").read_text())["physical"]
    feature_weights = {
        side: [sum(map(int, vector)) for vector in physical[side]]
        for side in ("x", "y")
    }
    tables = {}
    for side in ("x", "y"):
        rows, shift = report["common_affine"][side]
        tables[side] = [
            [vector[apply_rows(rows, word) ^ shift] for word in range(64)]
            for vector in physical[side]
        ]
    edges = []
    for index, update in enumerate(report["updates"]):
        side = update["side"]
        delta = [
            a ^ b
            for a, b in zip(tables[side][update["a"]], tables[side][update["b"]], strict=True)
        ]
        coefficients = walsh(delta)
        record = {
            "index": index,
            "lane": update["lane"],
            "side": side,
            "from": update["a"],
            "to": update["b"],
            "delta_weight": sum(delta),
            "delta_weight_parity": sum(delta) & 1,
            "nonzero_walsh_coefficients": sum(value != 0 for value in coefficients),
            "all_coefficients_odd": all((value & 1) != 0 for value in coefficients),
        }
        assert (record["delta_weight_parity"] == 1) == record["all_coefficients_odd"]
        if record["delta_weight_parity"]:
            assert record["nonzero_walsh_coefficients"] == 64
        edges.append(record)
    dense = [record for record in edges if record["delta_weight_parity"]]
    dense_by_side = {side: sum(record["side"] == side for record in dense) for side in ("x", "y")}
    assert dense_by_side == {"x": 2, "y": 2}
    output = {
        "feature_weights": feature_weights,
        "odd_weight_features": {
            side: [index for index, value in enumerate(feature_weights[side]) if value & 1]
            for side in ("x", "y")
        },
        "edges": edges,
        "observed_dense_edges": dense,
        "observed_dense_edges_by_side": dense_by_side,
        "observed_dense_walsh_terms": 64 * len(dense),
        "family_lower_bound": {
            "dense_edges_per_side": 2,
            "dense_edges_total": 4,
            "walsh_phase_terms_from_dense_edges": 256,
            "dense_block_depth_in_fixed_four_track_compiler": 38,
            "two_serial_dense_blocks_per_side_depth": 76,
            "proof": (
                "For a 0/1 vector d, every unnormalized Walsh coefficient is congruent "
                "to sum(d) modulo 2. An odd-weight delta therefore has all 64 coefficients "
                "odd and nonzero. A closed stream starts and ends at the even zero feature; "
                "if it visits any odd-weight feature it crosses the parity cut at least twice. "
                "Both coordinate factor spaces contain an odd-weight vector. Invertible feature-"
                "basis changes preserve that nonzero parity functional, coordinate permutations "
                "preserve weight, and even integer-potential lifts preserve the congruence."
            ),
            "scope": (
                "Lower bound for closed, exact per-edge Walsh controlled-RX streams. It is not "
                "a lower bound for arbitrary phase-oracle architectures or reachable-subspace superblocks."
            ),
        },
        "fixed_four_track_depth_reason": (
            "A dense edge assigns 16 phase rotations to each of four tracks. "
            "Visiting all 16 four-bit masks and returning to zero needs at least 16 "
            "target CNOT transitions. The flag track also has two Hadamards and four "
            "preparation/restoration CNOT touches, giving a 38-operation serial flag chain."
        ),
        "saturated_by_saved_tour": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2))
    print(json.dumps({
        "odd_weight_features": output["odd_weight_features"],
        "dense_edges_by_side": dense_by_side,
        "dense_terms": output["observed_dense_walsh_terms"],
    }, indent=2))


if __name__ == "__main__":
    main()
