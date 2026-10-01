from __future__ import annotations

from datetime import datetime, timezone

from .io import append_record, read_json, write_json
from .paths import (
    CLAIMS_PATH,
    CONTRADICTIONS_PATH,
    DIGITAL_TRACE_PATH,
    EVIDENCE_PATH,
    LEDGERS_DIR,
    OPERATORS_PATH,
    RUNTIME_EVENTS_PATH,
    ensure_data_dirs,
)


EMPTY_LEDGERS = {
    CLAIMS_PATH: [],
    OPERATORS_PATH: [],
    EVIDENCE_PATH: [],
    CONTRADICTIONS_PATH: [],
    RUNTIME_EVENTS_PATH: [],
    DIGITAL_TRACE_PATH: [],
}


def init_ledgers() -> None:
    ensure_data_dirs()
    for path, default in EMPTY_LEDGERS.items():
        if not path.exists():
            write_json(path, default)


def add_runtime_event(
    *,
    observed_change: str,
    user_report: str,
    impact: str,
    affected_process: str,
    mitigation: str,
    unresolved_risk: str,
) -> dict[str, str]:
    init_ledgers()
    records = read_json(RUNTIME_EVENTS_PATH, [])
    record = {
        "id": f"runtime_event_{len(records) + 1:04d}",
        "date": datetime.now(timezone.utc).isoformat(),
        "observed_change": observed_change,
        "user_report": user_report,
        "impact": impact,
        "affected_process": affected_process,
        "mitigation": mitigation,
        "unresolved_risk": unresolved_risk,
    }
    append_record(RUNTIME_EVENTS_PATH, record)
    return record


def add_digital_trace_event(
    *,
    artifact: str,
    trace_marker: str,
    target_surface: str,
    inspection_method: str,
    result: str,
    evidence_pointer: str = "",
    unresolved_gap: str = "",
) -> dict[str, str]:
    if result not in {"present", "absent", "not_inspected"}:
        raise ValueError("digital trace result must be present, absent, or not_inspected")
    init_ledgers()
    records = read_json(DIGITAL_TRACE_PATH, [])
    record = {
        "id": f"digital_trace_{len(records) + 1:04d}",
        "artifact": artifact,
        "trace_marker": trace_marker,
        "target_surface": target_surface,
        "inspection_method": inspection_method,
        "result": result,
        "evidence_pointer": evidence_pointer,
        "unresolved_gap": unresolved_gap,
        "date": datetime.now(timezone.utc).isoformat(),
    }
    append_record(DIGITAL_TRACE_PATH, record)
    return record


def ledger_counts() -> dict[str, int]:
    init_ledgers()
    return {
        "claims": len(read_json(CLAIMS_PATH, [])),
        "operators": len(read_json(OPERATORS_PATH, [])),
        "evidence": len(read_json(EVIDENCE_PATH, [])),
        "contradictions": len(read_json(CONTRADICTIONS_PATH, [])),
        "runtime_events": len(read_json(RUNTIME_EVENTS_PATH, [])),
        "digital_trace": len(read_json(DIGITAL_TRACE_PATH, [])),
        "ledger_files": len(list(LEDGERS_DIR.glob("*.json"))),
    }

