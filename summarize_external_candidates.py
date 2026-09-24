from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


qrows = json.loads(Path("agent_work/external_qasm_inventory.json").read_text())
metadata = json.loads(Path("agent_work/external_metadata_inventory.json").read_text())["records"]
by_hash = defaultdict(list)
for row in qrows:
    by_hash[row["sha256"]].append(row)

refs = defaultdict(list)
for record in metadata:
    fields = record["fields"]
    hashes = {
        value.lower()
        for key, value in fields.items()
        if "qasm" in key.lower()
        and isinstance(value, str)
        and re.fullmatch(r"[0-9a-fA-F]{64}", value)
    }
    for digest in hashes:
        refs[digest].append(record)


def relevant_claims(records):
    claims = []
    for record in records:
        fields = record["fields"]
        selected = {}
        for key, value in fields.items():
            low = key.lower()
            if any(
                token in low
                for token in (
                    "passed", "mismatch", "columns", "inputs", "scope", "depth",
                    "width", "gate_counts.cx", "gate_counts.u3", "max_column_l2",
                    "operator_error", "qasm_sha256", "marked_pixels", "basis_valid",
                )
            ):
                selected[key] = value
        claims.append({"path": record["path"], "fields": selected})
    return claims


summaries = []
for digest, rows in by_hash.items():
    native18 = [r for r in rows if r.get("width") == 18 and r.get("basis_valid")]
    if not native18:
        continue
    r = native18[0]
    records = refs.get(digest, [])
    blob = json.dumps(records).lower()
    summaries.append(
        {
            "sha256": digest,
            "metrics": {k: r[k] for k in ("width", "depth", "cx", "u3", "gates")},
            "paths": [x["path"] for x in native18],
            "metadata_files": [x["path"] for x in records],
            "has_passed_true": '"passed": true' in blob or '"numerical_validation_passed": true' in blob,
            "claims_4096": "4096" in blob,
            "claims_exhaustive": "exhaustive" in blob or "all clean-input columns" in blob or "every clean-ancilla input" in blob,
            "claims_randomized": "random" in blob,
            "claims": relevant_claims(records),
        }
    )

summaries.sort(key=lambda x: (x["metrics"]["depth"], x["metrics"]["cx"], x["sha256"]))
Path("agent_work/external_candidate_claims.json").write_text(json.dumps(summaries, indent=2) + "\n")
for s in summaries:
    flags = "".join(
        flag for yes, flag in (
            (s["has_passed_true"], "P"), (s["claims_4096"], "4"),
            (s["claims_exhaustive"], "E"), (s["claims_randomized"], "R"),
        ) if yes
    ) or "-"
    print(
        f"{s['metrics']['depth']:6} {s['metrics']['cx']:6} {s['metrics']['u3']:6} "
        f"{s['sha256'][:12]} {flags:4} q={len(s['paths'])} m={len(s['metadata_files'])} "
        f"{s['paths'][0]}"
    )
