from __future__ import annotations

import re
from pathlib import Path

from .io import read_json, write_json
from .paths import CLAIMS_PATH, SOURCE_MANIFEST_PATH, project_relative
from .status import STATUS_LANES


KEY_TERMS = [
    "claim",
    "operator",
    "validation",
    "falsifier",
    "theorem",
    "governance",
    "recursive",
    "translation",
    "residue",
    "memory",
    "observer",
    "wake",
    "field",
    "IL-LLM",
    "KEX",
    "BRAINK",
]


def sentence_candidates(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    candidates: list[str] = []
    for piece in pieces:
        clean = re.sub(r"\s+", " ", piece).strip(" -")
        if 80 <= len(clean) <= 420 and any(term.lower() in clean.lower() for term in KEY_TERMS):
            candidates.append(clean)
    return candidates


def heading_candidates(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        clean = line.strip()
        if 4 <= len(clean) <= 120 and not clean.endswith("."):
            word_count = len(clean.split())
            if 2 <= word_count <= 14 and any(term.lower() in clean.lower() for term in KEY_TERMS):
                out.append(clean)
    return out


def make_claim(source_id: str, source_path: str, index: int, wording: str, *, attribution: str) -> dict[str, object]:
    title = wording[:72].rstrip(" ,.;:")
    return {
        "id": f"claim_{source_id}_{index:04d}",
        "title": title,
        "wording": wording,
        "source_ref": source_path,
        "attribution": attribution,
        "status": "authored_definition" if "KEX" in wording or "BRAINK" in wording or "IL-LLM" in wording else "pending",
        "operator_ids": [],
        "evidence_ids": [],
        "contradiction_ids": [],
        "falsifier": "Pending: define the condition that would weaken or break this claim.",
        "notes": "Generated claim candidate; requires human review before promotion.",
    }


def extract_claims_from_manifest(limit_per_source: int = 25) -> list[dict[str, object]]:
    manifest = read_json(SOURCE_MANIFEST_PATH, [])
    claims: list[dict[str, object]] = []
    for source in manifest:
        text_path = Path(source["extracted_text_path"])
        if not text_path.is_absolute():
            text_path = Path(__file__).resolve().parents[1] / text_path
        text = text_path.read_text(encoding="utf-8", errors="ignore")
        seen = set()
        source_claims: list[str] = []
        for candidate in heading_candidates(text) + sentence_candidates(text):
            key = candidate.lower()
            if key in seen:
                continue
            seen.add(key)
            source_claims.append(candidate)
            if len(source_claims) >= limit_per_source:
                break
        for i, wording in enumerate(source_claims, 1):
            claims.append(
                make_claim(
                    str(source["id"]),
                    project_relative(text_path),
                    i,
                    wording,
                    attribution=str(source.get("attribution") or "A. Keddeh"),
                )
            )
    write_json(CLAIMS_PATH, claims)
    return claims


def validate_claim_statuses(claims: list[dict[str, object]]) -> list[str]:
    errors: list[str] = []
    for claim in claims:
        status = claim.get("status")
        if status not in STATUS_LANES:
            errors.append(f"{claim.get('id')}: invalid status {status}")
        if not claim.get("source_ref"):
            errors.append(f"{claim.get('id')}: missing source_ref")
        if "KEX" in str(claim.get("wording")) or "BRAINK" in str(claim.get("wording")) or "IL-LLM" in str(claim.get("wording")):
            if "Keddeh" not in str(claim.get("attribution")):
                errors.append(f"{claim.get('id')}: missing A. Keddeh attribution")
    return errors

