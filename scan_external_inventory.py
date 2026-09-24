from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path("research/external_classiq_oracle_1609/source_snapshot")
sys.path.insert(0, str(ROOT.resolve()))

from tracks.verification.qasm_metrics import score  # noqa: E402


rows = []
for path in sorted(ROOT.rglob("*.qasm")):
    raw = path.read_bytes()
    row = {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }
    try:
        metrics = score(path)
        row.update(
            width=metrics.width,
            depth=metrics.depth,
            cx=metrics.cx_count,
            u3=metrics.u3_count,
            gates=metrics.total_gates,
            basis_valid=metrics.basis_valid,
            width_valid=metrics.width_valid,
        )
    except Exception as exc:  # inventory malformed/non-native research artifacts too
        row["error"] = f"{type(exc).__name__}: {exc}"
    rows.append(row)

out = Path("agent_work/external_qasm_inventory.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rows, indent=2) + "\n")
print(json.dumps({
    "qasm_files": len(rows),
    "parsed": sum("error" not in r for r in rows),
    "native_18q": sum(r.get("width") == 18 and r.get("basis_valid") for r in rows),
    "errors": sum("error" in r for r in rows),
}, indent=2))
