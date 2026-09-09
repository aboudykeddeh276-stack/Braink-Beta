from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def append_record(path: Path, record: dict[str, Any]) -> list[dict[str, Any]]:
    """Append `record` to the JSON list at `path`, hash-chained to the
    previous entry.

    Prior to this, appended records carried no hash of any kind: a
    sequential counter ID (`len(records)+1`) was the only ordering
    signal, so deleting or reordering an entry, or editing one in place,
    left no trace. Every record now gets `previous_record_hash` (the
    prior record's `record_hash`, or None for the first) and its own
    `record_hash` computed over everything except that field itself --
    the same sha256-canonical-JSON chaining convention already used by
    `workspace_control_plane.receipts` and `braink_reasoning.chain`, so
    all three ledgers in this codebase now share one tamper-evidence
    scheme instead of three different ones.

    Same honest limit as those other two implementations: this catches
    a deleted, reordered, or edited-in-place *earlier* record, but
    nothing points forward to the newest record, so tampering with only
    the most recent entry is not detectable by this scheme alone.
    """
    records = read_json(path, [])
    previous_hash = records[-1]["record_hash"] if records else None
    # Mutate `record` in place (not a copy): callers such as
    # ledger.add_runtime_event build a dict, pass it here, and return
    # that same dict to their own caller without using this function's
    # return value -- a copy here would silently leave their returned
    # record without its chain fields.
    record["previous_record_hash"] = previous_hash
    record["record_hash"] = _hash(record)
    records.append(record)
    write_json(path, records)
    return records


def verify_ledger_chain(path: Path) -> tuple[bool, str]:
    """Recompute and check every record's hash chain. Returns (valid, reason)."""
    records = read_json(path, [])
    if not records:
        return True, ""
    if records[0].get("previous_record_hash") is not None:
        return False, "first record must have no predecessor"
    previous_hash = None
    for index, record in enumerate(records):
        if record.get("previous_record_hash") != previous_hash:
            return False, f"record {index} does not link to record {index - 1}"
        stored_hash = record.get("record_hash")
        recomputed = _hash({k: v for k, v in record.items() if k != "record_hash"})
        if stored_hash != recomputed:
            return False, f"record {index} content does not match its own record_hash"
        previous_hash = stored_hash
    return True, ""

