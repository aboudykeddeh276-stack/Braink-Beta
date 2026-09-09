"""Learning log: a hash-chained, persistent record of what Braink has
been asked and what capabilities it has been given.

This is the concrete, engineering-level answer to "learns under your
design" for a system whose answer path never generates text at query
time (see CLAUDE.md): "learning" here means two specific, loggable
events, not a metaphor --

- **learned**: a new `TopicHandler` was registered into a `TopicRegistry`.
  This is the moment a new capability exists.
- **answered**: a real `ask()` call executed and returned a result.

Both use the same sha256-canonical-JSON hash-chaining convention as
`workspace_control_plane.receipts`, `braink_reasoning.chain`, and
`il_llm.io.append_record` (see `CLAUDE.md`) -- this is the fourth place
in this project doing tamper-evident chaining, and it reuses the
convention rather than inventing a fifth. Same honest limit as the
other three: nothing points forward to the last entry, so tampering
with only the most recent one is not detectable by this scheme alone.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from braink_reasoning.answer import ask
from braink_reasoning.registry import TopicHandler, TopicRegistry


def _hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class LogEntry:
    kind: str  # "learned" or "answered"
    topic: str
    detail: dict
    previous_entry_hash: str | None
    recorded_at: str | None = None
    entry_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if self.recorded_at is None:
            object.__setattr__(self, "recorded_at", datetime.now(timezone.utc).isoformat())
        payload = {
            "kind": self.kind,
            "topic": self.topic,
            "detail": self.detail,
            "previous_entry_hash": self.previous_entry_hash,
            "recorded_at": self.recorded_at,
        }
        object.__setattr__(self, "entry_hash", _hash(payload))

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "topic": self.topic,
            "detail": self.detail,
            "previous_entry_hash": self.previous_entry_hash,
            "recorded_at": self.recorded_at,
            "entry_hash": self.entry_hash,
        }


class LearningLog:
    """In-memory, hash-chained log of learned capabilities and given answers.

    Not tied to a storage backend -- `to_json`/`from_json` persist it as
    plain text (a file, a database column, whatever the caller wants),
    matching how every register in this package leaves storage to the
    caller and only defines the data/hashing contract.
    """

    def __init__(self) -> None:
        self._entries: list[LogEntry] = []

    @property
    def entries(self) -> tuple[LogEntry, ...]:
        return tuple(self._entries)

    def _append(self, kind: str, topic: str, detail: dict) -> LogEntry:
        previous = self._entries[-1].entry_hash if self._entries else None
        entry = LogEntry(kind=kind, topic=topic, detail=detail, previous_entry_hash=previous)
        self._entries.append(entry)
        return entry

    def record_learned(self, handler: TopicHandler) -> LogEntry:
        """Log that a new capability now exists."""
        return self._append(
            kind="learned",
            topic=handler.topic,
            detail={
                "status": handler.status.value,
                "description": handler.description,
                "required_params": list(handler.required_params),
            },
        )

    def record_answer(self, topic: str, params: dict, result: Any) -> LogEntry:
        """Log that a question was actually answered."""
        return self._append(kind="answered", topic=topic, detail={"params": params, "result": result})

    def to_json(self) -> str:
        return json.dumps([e.to_dict() for e in self._entries], indent=2, default=str)

    @classmethod
    def from_json(cls, text: str) -> "LearningLog":
        log = cls()
        for raw in json.loads(text):
            entry = LogEntry(
                kind=raw["kind"],
                topic=raw["topic"],
                detail=raw["detail"],
                previous_entry_hash=raw["previous_entry_hash"],
                recorded_at=raw["recorded_at"],
            )
            log._entries.append(entry)
        return log


def verify_log_chain(log: LearningLog) -> tuple[bool, str]:
    """Recompute and check every entry's hash chain. Returns (valid, reason)."""
    entries = log.entries
    if not entries:
        return True, ""
    if entries[0].previous_entry_hash is not None:
        return False, "first entry must have no predecessor"
    previous_hash = None
    for index, entry in enumerate(entries):
        if entry.previous_entry_hash != previous_hash:
            return False, f"entry {index} does not link to entry {index - 1}"
        recomputed = _hash({
            "kind": entry.kind, "topic": entry.topic, "detail": entry.detail,
            "previous_entry_hash": entry.previous_entry_hash, "recorded_at": entry.recorded_at,
        })
        if recomputed != entry.entry_hash:
            return False, f"entry {index} content does not match its own entry_hash"
        previous_hash = entry.entry_hash
    return True, ""


def logged_register(log: LearningLog, registry: TopicRegistry, handler: TopicHandler) -> None:
    """Register a handler and log the learning event in one call."""
    registry.register(handler)
    log.record_learned(handler)


def logged_ask(log: LearningLog, registry: TopicRegistry, topic: str, **params: Any):
    """Execute ask() and log the answer in one call. Returns the same
    TopicAnswer ask() would; raises the same errors (UnknownTopicError,
    TypeError) without logging anything on failure -- only real, executed
    answers get recorded."""
    answer = ask(registry, topic, **params)
    log.record_answer(topic, params, answer.result)
    return answer
