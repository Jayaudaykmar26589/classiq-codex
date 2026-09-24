#!/usr/bin/env python3
"""Adapter from the expanded raw screen to the external full-circuit descent.

Typical use in ``round4_expand_edge_gauges.py``::

    from structure_subagent.expanded_candidate_pool import core_proposals
    for raw, params in core_proposals(side, a, b):
        q = core.strict(block_build(values, **params))

The returned pool is deterministic and includes raw-score, helper-load and
individual-wire-load alternatives. Every parameter dictionary is accepted by
``tracks.multitrack_rx.compiler.build``; in particular it includes the newly
searched ``offsets`` argument.
"""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
CACHE = HERE / "expanded_descent_cache.json"


def edge_key(side: str, a: int, b: int) -> str:
    high, low = sorted((int(a), int(b)), reverse=True)
    return f"{side}|{high}|{low}"


def load_cache(path: Path = CACHE) -> dict:
    return json.loads(path.read_text())


def rows_for_edge(side: str, a: int, b: int, *, pool: str = "descent_pool", path: Path = CACHE):
    data = load_cache(path)
    record = data["edges"][edge_key(side, a, b)]
    if pool == "descent_pool":
        return record["descent_pool"]
    if pool == "pareto":
        return record["pareto"]
    if pool in ("best_raw_score", "best_helper_at_or_below_old_depth"):
        return [record[pool]]
    raise ValueError(pool)


def params_from_row(row: dict) -> dict:
    return {
        "low": list(row["low"]),
        "high": list(row["high"]),
        "reverse": bool(row["reverse"]),
        "offsets": list(row["offsets"]),
    }


def core_proposals(side: str, a: int, b: int, *, pool: str = "descent_pool", path: Path = CACHE):
    """Return ``((raw_depth, raw_cx), params)`` rows expected by Round 4."""

    return [
        ((int(row["depth"]), int(row["cx"])), params_from_row(row))
        for row in rows_for_edge(side, a, b, pool=pool, path=path)
    ]


if __name__ == "__main__":
    data = load_cache()
    print(
        json.dumps(
            {
                "edges": len(data["edges"]),
                "candidates": sum(len(record["descent_pool"]) for record in data["edges"].values()),
                "cache": str(CACHE),
            },
            indent=2,
        )
    )
