# ENGINEERED INIT (A.keddeh, K-SYSTEMS):
# - discover repo root from current working directory
# - scour IL-LLM pin surface before other actions
# - execute only via named/resolved blocks (smart_manager) when applicable
# Source: /Users/ak/Documents/ENGINEERING BY DESIGN/PINNED.md

from __future__ import annotations

from .extract import validate_claim_statuses
from .io import read_json, verify_ledger_chain
from .paths import (
    CLAIMS_PATH,
    DIGITAL_TRACE_PATH,
    OPERATORS_PATH,
    RUNTIME_EVENTS_PATH,
    SOURCE_MANIFEST_PATH,
)


def validate_ledgers() -> list[str]:
    """Note on scope: this remains a post-hoc check, run on demand via
    `il-llm validate` -- it reads already-written ledger files and
    reports problems in them. It does not intercept or block a write
    before it happens. The hash-chain check added here catches tampering
    with past entries; it does not make writes themselves governed."""
    errors: list[str] = []
    sources = read_json(SOURCE_MANIFEST_PATH, [])
    claims = read_json(CLAIMS_PATH, [])
    operators = read_json(OPERATORS_PATH, [])
    digital_traces = read_json(DIGITAL_TRACE_PATH, [])

    for path in (RUNTIME_EVENTS_PATH, DIGITAL_TRACE_PATH):
        valid, reason = verify_ledger_chain(path)
        if not valid:
            errors.append(f"{path.name}: hash chain broken -- {reason}")

    if not sources:
        errors.append("source manifest is empty; run ingest first")
    errors.extend(validate_claim_statuses(claims))

    for operator in operators:
        oid = operator.get("id")
        for field in ["inputs", "steps", "outputs", "failure_modes"]:
            if not operator.get(field):
                errors.append(f"{oid}: missing {field}")
        if not operator.get("evidence_gate"):
            errors.append(f"{oid}: missing evidence_gate")
        if not operator.get("teaching_use"):
            errors.append(f"{oid}: missing teaching_use")

    for trace in digital_traces:
        if trace.get("result") not in {"present", "absent", "not_inspected"}:
            errors.append(f"{trace.get('id')}: invalid digital trace result")
        if trace.get("result") == "present" and not trace.get("evidence_pointer"):
            errors.append(f"{trace.get('id')}: present trace requires evidence_pointer")

    return errors

