"""The monotonic historical ledger (SEC-04 / WP04):

    HistoricalLedger_t (subset-or-equal) HistoricalLedger_{t+1}

An append-only, hash-chained sequence of committed LearningArtifacts.
There is deliberately no remove/replace method: the monotonic-superset
property is enforced by the class's interface, not just documented.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from braink_cognition.learning_chain import LearningArtifact

_GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class LedgerEntry:
    sequence: int
    artifact_digest: str
    previous_hash: str
    entry_hash: str


def _artifact_digest(artifact: LearningArtifact) -> str:
    payload = "|".join(
        [
            artifact.context_before,
            artifact.observation,
            artifact.hypothesis,
            artifact.candidate_delta.description,
            str(artifact.execution.ran),
            artifact.execution.output,
            str(artifact.test.total),
            str(artifact.test.passed),
            artifact.evidence.digest,
            artifact.context_after,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _chain_hash(previous_hash: str, artifact_digest: str) -> str:
    return hashlib.sha256(f"{previous_hash}|{artifact_digest}".encode("utf-8")).hexdigest()


class HistoricalLedger:
    """Append-only, hash-chained ledger of committed LearningArtifacts."""

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []
        self._digests: set[str] = set()

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, artifact: LearningArtifact) -> bool:
        return _artifact_digest(artifact) in self._digests

    def append(self, artifact: LearningArtifact) -> LedgerEntry:
        digest = _artifact_digest(artifact)
        previous_hash = self._entries[-1].entry_hash if self._entries else _GENESIS_HASH
        entry = LedgerEntry(
            sequence=len(self._entries),
            artifact_digest=digest,
            previous_hash=previous_hash,
            entry_hash=_chain_hash(previous_hash, digest),
        )
        self._entries.append(entry)
        self._digests.add(digest)
        return entry

    def verify_chain(self) -> bool:
        """Recompute the hash chain from scratch; detects any tampering."""
        previous_hash = _GENESIS_HASH
        for entry in self._entries:
            if entry.previous_hash != previous_hash:
                return False
            if entry.entry_hash != _chain_hash(previous_hash, entry.artifact_digest):
                return False
            previous_hash = entry.entry_hash
        return True

    def entries(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._entries)
