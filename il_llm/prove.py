# ENGINEERED INIT (A.keddeh, K-SYSTEMS):
# - discover repo root from current working directory
# - scour IL-LLM pin surface before other actions
# - execute only via named/resolved blocks (smart_manager) when applicable
# Source: /Users/ak/Documents/ENGINEERING BY DESIGN/PINNED.md

from __future__ import annotations

from .io import read_json
from .paths import CLAIMS_PATH, EVIDENCE_PATH


def prove_empirical_claim_links() -> dict[str, object]:
    """Scaffold: verify that empirically-promoted claims link to evidence records.

    This does not execute falsifiers yet. It enforces that claims in the
    empirical_validation lane are wired to evidence ledger ids.
    """
    claims = read_json(CLAIMS_PATH, [])
    evidence = read_json(EVIDENCE_PATH, [])
    evidence_ids = {record.get("id") for record in evidence if isinstance(record, dict)}

    empirical = [c for c in claims if isinstance(c, dict) and c.get("status") == "empirical_validation"]
    missing_links: list[str] = []
    broken_links: list[str] = []

    for claim in empirical:
        cid = str(claim.get("id") or "")
        linked = claim.get("evidence_ids") or []
        if not isinstance(linked, list) or not linked:
            missing_links.append(cid)
            continue
        for eid in linked:
            if eid not in evidence_ids:
                broken_links.append(f"{cid}:{eid}")

    return {
        "empirical_claims": len(empirical),
        "missing_evidence_links": missing_links,
        "broken_evidence_links": broken_links,
        "passed": not missing_links and not broken_links,
    }

