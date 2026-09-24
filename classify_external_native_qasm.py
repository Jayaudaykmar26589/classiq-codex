from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


rows = json.loads(Path("agent_work/external_qasm_inventory.json").read_text())
claims = {
    item["sha256"]: item
    for item in json.loads(Path("agent_work/external_candidate_claims.json").read_text())
}


def classify(path: str) -> tuple[str, str]:
    """Classify semantic scope from the snapshot's own reports/readmes."""
    # Explicitly partial/local strict circuits.
    if "tracks/caterpillar/custom_factor0_strict.qasm" in path:
        return "component", "one of ten separable factors only"
    if any(
        text in path
        for text in (
            "tracks/rank_circuit/geometry_comparator_rectangles.qasm",
            "tracks/rank_circuit/geometry_prefix_rectangles.qasm",
        )
    ):
        return "component", "square-plus-bar rectangles only"

    # Full Boolean-output circuits are not phase oracles in their saved form.
    if (
        "tracks/inplace_lut_schedule/" in path
        or "tracks/lut_pebble_search/" in path
    ) and path.endswith("_output.qasm"):
        return "non_phase_output", "computes a Boolean output; root-phase sibling is the oracle"

    # Reports explicitly reject these as incorrect logo oracles.
    if "tracks/closed_phase_stream/" in path:
        return "invalid_uncorrected", "known non-global residual coordinate phase"
    if "tracks/research_phase_duality/relative_lut_rank_tket_strict.qasm" in path:
        return "invalid_implicit_permutation", "failed validation; omitted q9/q11 swap"
    if "tracks/tket_correctness_audit/" in path and any(
        marker in path for marker in ("3_FullPeepholeOptimise", "4_RemoveRedundancies2")
    ):
        return "invalid_implicit_permutation", "failed validation; omitted q9/q11 swap"

    # Every remaining strict width-18 QASM is described by its producing track
    # as a complete oracle/reference candidate.  This label does not imply that
    # its saved QASM received exhaustive numerical verification.
    return "complete_claimed", "complete phase-oracle/reference circuit according to producing track"


out = []
for row in rows:
    if row.get("width") != 18 or not row.get("basis_valid"):
        continue
    scope_class, reason = classify(row["path"])
    claim = claims.get(row["sha256"], {})
    if scope_class.startswith("invalid"):
        evidence = "failed"
    elif claim.get("has_passed_true") and claim.get("claims_4096") and claim.get("claims_exhaustive"):
        evidence = "saved_qasm_all4096_claim"
    elif claim.get("has_passed_true"):
        evidence = "saved_qasm_random_or_local_claim"
    elif claim.get("claims_4096"):
        evidence = "logical_or_model_4096_claim"
    else:
        evidence = "no_hash_bound_verification_found"
    out.append({**row, "scope_class": scope_class, "scope_reason": reason, "evidence": evidence})

Path("agent_work/external_native18_classified.json").write_text(json.dumps(out, indent=2) + "\n")
print("files", len(out))
print("scope", Counter(r["scope_class"] for r in out))
print("evidence", Counter(r["evidence"] for r in out))
unique = defaultdict(list)
for r in out:
    unique[r["sha256"]].append(r)
print("unique hashes", len(unique))
print("unique complete hashes", sum(any(r["scope_class"] == "complete_claimed" for r in rs) for rs in unique.values()))
