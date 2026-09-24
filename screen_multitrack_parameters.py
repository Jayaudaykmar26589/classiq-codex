#!/usr/bin/env python3
"""Pure-Python exact-identity parameter screen for the four-track RX blocks.

This does not transpile or claim a whole-oracle score.  It enumerates only
parameter choices accepted by ``tracks.multitrack_rx.compiler.build`` and
measures the resulting raw U3/CX program with the challenge's unit-duration
ASAP convention.  Every candidate has the same controlled-RX identity by the
compiler derivation; the screen changes Gray traversal orders and their
assignment to the four parity tracks.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


def apply_rows(rows: tuple[int, ...], word: int) -> int:
    return sum((((row & word).bit_count() & 1) << index) for index, row in enumerate(rows))


def walsh(values: tuple[int, ...]) -> list[int]:
    result = list(map(int, values))
    step = 1
    while step < len(result):
        for base in range(0, len(result), 2 * step):
            for index in range(step):
                left, right = result[base + index], result[base + index + step]
                result[base + index], result[base + index + step] = left + right, left - right
        step *= 2
    return result


def raw_metrics(
    coeff: list[int],
    low: tuple[int, int],
    high: tuple[int, ...],
    reverse: bool,
    offsets: tuple[int, ...],
) -> dict[str, object]:
    """Mirror compiler.build, replacing H/P by one U3 each."""

    a, b = low
    operations: list[tuple[str, tuple[int, ...]]] = [("u3", (6,))]
    preparation = ((6, a), (b, 7), (6, b), (a, 7))
    operations.extend(("cx", wires) for wires in preparation)
    queues: list[list[tuple[str, tuple[int, ...]]]] = []
    for target, base, offset in zip(
        (6, a, b, 7), (0, 1 << a, 1 << b, (1 << a) | (1 << b)), offsets, strict=True
    ):
        sequence = []
        for index in range(16):
            gray = index ^ (index >> 1)
            mask = sum(((gray >> k) & 1) << high[(k + offset) % 4] for k in range(4))
            if coeff[mask | base]:
                sequence.append(mask)
        if reverse:
            sequence.reverse()
        queue: list[tuple[str, tuple[int, ...]]] = []
        previous = 0
        for mask in sequence:
            for bit in high:
                if ((previous ^ mask) >> bit) & 1:
                    queue.append(("cx", (bit, target)))
            queue.append(("u3", (target,)))
            previous = mask
        for bit in high:
            if (previous >> bit) & 1:
                queue.append(("cx", (bit, target)))
        queues.append(queue)

    # Preserve each queue, using the same earliest-ready merge as the source.
    ready = [0] * 9
    for _, wires in operations:
        end = max(ready[wire] for wire in wires) + 1
        for wire in wires:
            ready[wire] = end
    positions = [0] * 4
    while any(positions[k] < len(queues[k]) for k in range(4)):
        _, lane = min(
            (max(ready[w] for w in queues[k][positions[k]][1]), k)
            for k in range(4)
            if positions[k] < len(queues[k])
        )
        operation = queues[lane][positions[lane]]
        operations.append(operation)
        _, wires = operation
        end = max(ready[wire] for wire in wires) + 1
        for wire in wires:
            ready[wire] = end
        positions[lane] += 1
    operations.extend(("cx", wires) for wires in reversed(preparation))
    operations.append(("u3", (6,)))

    ready = [0] * 9
    loads = [0] * 9
    for _, wires in operations:
        end = max(ready[wire] for wire in wires) + 1
        for wire in wires:
            ready[wire] = end
            loads[wire] += 1
    return {
        "depth": max(ready),
        "cx": sum(name == "cx" for name, _ in operations),
        "u3": sum(name == "u3" for name, _ in operations),
        "loads": loads,
        "helper_load": loads[7],
        "max_load": max(loads),
    }


def canonical_parameter_space():
    """Yield all 4,320 inequivalent parameter tuples.

    The literal space has 15*24*2*24 = 17,280 tuples. A common cyclic
    rotation of ``high`` can be absorbed into all four offsets, so fixing the
    first high bit to the minimum representative removes exactly a factor of
    four without removing a circuit.
    """

    for low in itertools.combinations(range(6), 2):
        remaining = tuple(bit for bit in range(6) if bit not in low)
        for high in (order for order in itertools.permutations(remaining) if order[0] == min(remaining)):
            for reverse in (False, True):
                for offsets in itertools.permutations(range(4)):
                    yield low, high, reverse, offsets


def expanded_candidates(coeff: list[int]) -> list[dict[str, object]]:
    result = []
    for low, high, reverse, offsets in canonical_parameter_space():
        metrics = raw_metrics(coeff, low, high, reverse, offsets)
        result.append(
            {
                **metrics,
                "low": list(low),
                "high": list(high),
                "reverse": reverse,
                "offsets": list(offsets),
            }
        )
    return result


def descent_pool(candidates: list[dict[str, object]], old_depth: int) -> list[dict[str, object]]:
    """Keep deterministic, wire-load-diverse candidates for whole-circuit descent."""

    selected: dict[tuple[object, ...], dict[str, object]] = {}

    def add(rows):
        for row in rows:
            key = (
                tuple(row["low"]),
                tuple(row["high"]),
                bool(row["reverse"]),
                tuple(row["offsets"]),
            )
            selected.setdefault(key, row)

    add(
        sorted(
            candidates,
            key=lambda row: (
                row["depth"],
                row["cx"],
                row["max_load"],
                row["helper_load"],
                tuple(row["loads"]),
            ),
        )[:64]
    )
    eligible = [row for row in candidates if int(row["depth"]) <= old_depth + 1]
    add(sorted(eligible, key=lambda row: (row["helper_load"], row["depth"], row["cx"], tuple(row["loads"])))[:32])
    for wire in range(8):
        add(
            sorted(
                eligible,
                key=lambda row: (row["loads"][wire], row["depth"], row["cx"], row["helper_load"]),
            )[:8]
        )
    return list(selected.values())


def pareto(rows: list[dict[str, object]], fields: tuple[str, ...]) -> list[dict[str, object]]:
    # Parameter symmetries produce many identical metric vectors.  One
    # representative is sufficient and keeps the dominance pass small.
    unique: dict[tuple[int, ...], dict[str, object]] = {}
    for row in rows:
        vector = tuple(int(row[field]) for field in fields)
        unique.setdefault(vector, row)
    kept: list[dict[str, object]] = []
    for row in sorted(unique.values(), key=lambda item: tuple(int(item[field]) for field in fields)):
        vector = tuple(int(row[field]) for field in fields)
        if any(
            all(int(other[field]) <= value for field, value in zip(fields, vector, strict=True))
            and any(int(other[field]) < value for field, value in zip(fields, vector, strict=True))
            for other in kept
        ):
            continue
        kept = [
            other
            for other in kept
            if not (
                all(value <= int(other[field]) for field, value in zip(fields, vector, strict=True))
                and any(value < int(other[field]) for field, value in zip(fields, vector, strict=True))
            )
        ]
        kept.append(row)
    return sorted(kept, key=lambda item: tuple(int(item[field]) for field in fields))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = json.loads((args.snapshot / "tracks/multitrack_affine_refine/best.report.json").read_text())
    physical = json.loads((args.snapshot / "tracks/closed_phase_stream/factor_truths.json").read_text())["physical"]
    transformed: dict[str, list[tuple[int, ...]]] = {}
    for side in ("x", "y"):
        rows, shift = report["common_affine"][side]
        transformed[side] = [
            tuple(vector[apply_rows(tuple(rows), z) ^ shift] for z in range(64))
            for vector in physical[side]
        ]

    summaries = []
    for index, update in enumerate(report["updates"]):
        side, start, stop = update["side"], update["a"], update["b"]
        values = tuple(a ^ b for a, b in zip(transformed[side][start], transformed[side][stop], strict=True))
        coeff = walsh(values)
        old = update["params"]
        old_metrics = raw_metrics(
            coeff,
            tuple(old["low"]),
            tuple(old["high"]),
            bool(old["reverse"]),
            (0, 1, 2, 3),
        )
        candidates = expanded_candidates(coeff)
        best_score = min(candidates, key=lambda row: (row["depth"], row["cx"], row["helper_load"], row["max_load"]))
        best_helper_at_old_depth = min(
            (row for row in candidates if int(row["depth"]) <= int(old_metrics["depth"])),
            key=lambda row: (row["helper_load"], row["depth"], row["cx"], row["max_load"]),
        )
        frontier = pareto(candidates, ("depth", "cx", "helper_load", "max_load"))
        summaries.append(
            {
                "index": index,
                "lane": update["lane"],
                "side": side,
                "from": start,
                "to": stop,
                "inverse": update["inverse"],
                "saved_strict": {"depth": update["depth"], "cx": update["cx"], "params": old},
                "old_raw": {**old_metrics, "offsets": [0, 1, 2, 3]},
                "best_raw_score": best_score,
                "best_helper_at_or_below_old_depth": best_helper_at_old_depth,
                "pareto_count": len(frontier),
                "pareto": frontier[:30],
                "descent_pool": descent_pool(candidates, int(old_metrics["depth"])),
                "enumerated": len(candidates),
            }
        )
        print(
            index,
            side,
            start,
            stop,
            "old",
            (old_metrics["depth"], old_metrics["cx"], old_metrics["helper_load"]),
            "best",
            (best_score["depth"], best_score["cx"], best_score["helper_load"]),
            "helper",
            (
                best_helper_at_old_depth["depth"],
                best_helper_at_old_depth["cx"],
                best_helper_at_old_depth["helper_load"],
            ),
            flush=True,
        )

    aggregate = {
        "updates": len(summaries),
        "enumerated_per_update": summaries[0]["enumerated"] if summaries else 0,
        "old_raw_depth_sum": sum(row["old_raw"]["depth"] for row in summaries),
        "best_raw_depth_sum": sum(row["best_raw_score"]["depth"] for row in summaries),
        "old_raw_cx_sum": sum(row["old_raw"]["cx"] for row in summaries),
        "best_raw_cx_sum": sum(row["best_raw_score"]["cx"] for row in summaries),
        "old_helper_load_sum": sum(row["old_raw"]["helper_load"] for row in summaries),
        "best_score_helper_load_sum": sum(row["best_raw_score"]["helper_load"] for row in summaries),
        "best_helper_load_sum_at_or_below_old_depth": sum(
            row["best_helper_at_or_below_old_depth"]["helper_load"] for row in summaries
        ),
        "strict_whole_oracle_score_claimed": False,
        "literal_parameter_count_per_update": 17280,
        "cyclic_symmetry_factor": 4,
        "source_parameter_count_per_update": 60,
        "source_enumeration": "15 low pairs * 2 high orders (ascending/reversed) * 2 path directions; offsets fixed to [0,1,2,3].",
        "expanded_enumeration": "15 low pairs * 24 high permutations * 2 path directions * 24 offset permutations, canonicalized by the fourfold common cyclic rotation symmetry.",
        "identity_scope": "Parameters preserve the source compiler's exact four-track controlled-RX construction.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"aggregate": aggregate, "updates": summaries}, indent=2))
    print(json.dumps(aggregate, indent=2))


if __name__ == "__main__":
    main()
