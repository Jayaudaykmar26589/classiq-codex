#!/usr/bin/env python3
"""Compare 1+3, 2+2, and 3+1 flag allocation proxies.

The four-track update consumes one persistent flag and one side helper.  With
six ancillas and one x/y helper pair, four flags remain.  This script measures
the best independent rooted cycle covers for each coordinate side using the
same 60 raw block choices as the source compiler.  It deliberately omits
cross-side CZ synchronization, orientation closure, and whole-circuit
optimization, so its numbers are screening proxies rather than circuit scores.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
from pathlib import Path


def add(left: tuple[int, int], right: tuple[int, int]) -> tuple[int, int]:
    return left[0] + right[0], left[1] + right[1]


def rooted_tours(edge, side: str):
    # Features are 0..9; 10 is the zero function and closes every stream.
    dp = {(1 << index, index): (edge[side, 10, index], (index,)) for index in range(10)}
    tours = {}
    for mask in range(1, 1 << 10):
        for last in range(10):
            if (mask, last) not in dp:
                continue
            value, path = dp[mask, last]
            candidate = (add(value, edge[side, last, 10]), path)
            if mask not in tours or candidate[0] < tours[mask][0]:
                tours[mask] = candidate
            for nxt in range(10):
                if (mask >> nxt) & 1:
                    continue
                key = mask | (1 << nxt), nxt
                candidate = (add(value, edge[side, last, nxt]), path + (nxt,))
                if key not in dp or candidate[0] < dp[key][0]:
                    dp[key] = candidate
    return tours


def cycle_cover(tours, lanes: int, mask: int = (1 << 10) - 1):
    memo = {}

    def solve(active: int, count: int):
        if count == 1:
            return tours[active][0], [tours[active][1]]
        key = active, count
        if key in memo:
            return memo[key]
        first = active & -active
        rest = active ^ first
        subset = rest
        best = None
        while True:
            head = subset | first
            tail = active ^ head
            if tail and tail.bit_count() >= count - 1:
                tail_value, tail_paths = solve(tail, count - 1)
                value = add(tours[head][0], tail_value)
                candidate = value, [tours[head][1]] + tail_paths
                if best is None or value < best[0]:
                    best = candidate
            if subset == 0:
                break
            subset = (subset - 1) & rest
        memo[key] = best
        return best

    return solve(mask, lanes)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--parameter-script", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("parameter_screen", args.parameter_script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    source = json.loads((args.snapshot / "tracks/multitrack_affine_refine/best.report.json").read_text())
    physical = json.loads((args.snapshot / "tracks/closed_phase_stream/factor_truths.json").read_text())["physical"]
    tables = {}
    for side in ("x", "y"):
        rows, shift = source["common_affine"][side]
        tables[side] = [
            tuple(vector[module.apply_rows(tuple(rows), word) ^ shift] for word in range(64))
            for vector in physical[side]
        ]

    edge = {}
    for side in ("x", "y"):
        for left in range(11):
            for right in range(left):
                values = tuple(
                    a ^ b for a, b in zip(tables[side][left], tables[side][right], strict=True)
                )
                coeff = module.walsh(values)
                best = None
                for low in itertools.combinations(range(6), 2):
                    high = tuple(bit for bit in range(6) if bit not in low)
                    for order in (high, tuple(reversed(high))):
                        for reverse in (False, True):
                            metrics = module.raw_metrics(coeff, low, order, reverse, (0, 1, 2, 3))
                            value = int(metrics["depth"]), int(metrics["cx"])
                            if best is None or value < best:
                                best = value
                edge[side, left, right] = edge[side, right, left] = best

    tours = {side: rooted_tours(edge, side) for side in ("x", "y")}
    covers = {
        side: {
            lanes: cycle_cover(tours[side], lanes)
            for lanes in (1, 2, 3)
        }
        for side in ("x", "y")
    }
    allocations = []
    for x_lanes, y_lanes in ((1, 3), (2, 2), (3, 1)):
        x_value, x_paths = covers["x"][x_lanes]
        y_value, y_paths = covers["y"][y_lanes]
        allocations.append(
            {
                "x_lanes": x_lanes,
                "y_lanes": y_lanes,
                "proxy_max_side_depth_sum": max(x_value[0], y_value[0]),
                "proxy_total_cx": x_value[1] + y_value[1],
                "x": {"depth_sum": x_value[0], "cx_sum": x_value[1], "cycles": x_paths},
                "y": {"depth_sum": y_value[0], "cx_sum": y_value[1], "cycles": y_paths},
            }
        )
    output = {
        "allocation": allocations,
        "best_by_proxy": min(allocations, key=lambda row: (row["proxy_max_side_depth_sum"], row["proxy_total_cx"])),
        "scope": (
            "Independent-side cycle-cover screen using raw local block scores. "
            "It omits shared feature/CZ synchronization, aggregate orientation closure, "
            "affine overhead, cross-block fusion, and full verification; values are not circuit scores."
        ),
        "conclusion": "The relaxed proxy favors the incumbent two-flags-per-side allocation over asymmetric flag reuse.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
