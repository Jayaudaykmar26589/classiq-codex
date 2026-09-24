from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path("research/external_classiq_oracle_1609/source_snapshot")
KEYWORDS = (
    "qasm", "sha", "depth", "cx", "width", "gate", "basis", "input", "column",
    "valid", "verify", "exact", "complete", "scope", "phase", "ancilla", "mismatch",
    "error", "pass", "status", "oracle", "marked",
)


def flatten(obj, prefix=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield from flatten(value, path)
    elif isinstance(obj, list):
        # Avoid enormous per-test or per-candidate expansions; retain compact scalars.
        if len(obj) <= 24 and all(not isinstance(v, (dict, list)) for v in obj):
            yield prefix, obj
        else:
            yield f"{prefix}.__len__", len(obj)
    else:
        yield prefix, obj


records = []
bad = []
for path in sorted(ROOT.rglob("*.json")):
    try:
        obj = json.loads(path.read_text())
    except Exception as exc:
        bad.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})
        continue
    flat = dict(flatten(obj))
    selected = {
        key: value for key, value in flat.items()
        if any(word in key.lower() for word in KEYWORDS)
    }
    # Metadata relevant to a stored circuit or verification claim.
    haystack = " ".join(selected).lower()
    if any(word in haystack for word in ("qasm", "depth", "cx", "verification", "validation", "mismatch", "exhaustive")):
        records.append({"path": str(path), "fields": selected})

Path("agent_work/external_metadata_inventory.json").write_text(
    json.dumps({"records": records, "bad": bad}, indent=2, default=str) + "\n"
)
print(json.dumps({"json": sum(1 for _ in ROOT.rglob('*.json')), "relevant": len(records), "bad": len(bad)}, indent=2))
print("top field suffixes")
counts = Counter(key.rsplit(".", 1)[-1] for rec in records for key in rec["fields"])
print(counts.most_common(40))
