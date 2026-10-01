"""Evidence / Receipt Plane.

A receipt is generated only as the direct output of one real pipeline
run: an actual before-state hash and after-state hash computed here, the
actor and scopes actually admitted, and the actual verification result.
There is no pre-filled or hand-authored "success" receipt anywhere in
this package — every field comes from a value the runtime observed.

Receipts chain: each one carries the hash of the receipt before it
(``previous_receipt_hash``), so the sequence is tamper-evident, not just
each receipt individually self-consistent. A hash of "current state" is
not the same guarantee as a hash chain over history — computing only the
former is a common mistake (an audit trail that looks append-only but
lets entries be deleted or reordered undetected, since nothing in one
entry depends on the one before it). Chaining is what actually catches
that.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def hash_state(state: Any) -> str:
    """Compute a stable sha256 over a canonical model's (or None's) contents."""
    if state is None:
        payload: Any = None
    elif hasattr(state, "model_dump"):
        payload = state.model_dump()
    else:
        payload = state
    canonical = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class Receipt:
    """Immutable operation receipt."""

    capability: str
    actor: str
    delegated_identity: str | None
    scopes_used: tuple[str, ...]
    resource_id: str
    before_state_hash: str
    after_state_hash: str
    converged: bool
    actuator_kind: str
    previous_receipt_hash: str | None
    unexpected_fields: tuple[str, ...] = ()
    issued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "capability": self.capability,
            "actor": self.actor,
            "delegated_identity": self.delegated_identity,
            "scopes_used": list(self.scopes_used),
            "resource_id": self.resource_id,
            "before_state_hash": self.before_state_hash,
            "after_state_hash": self.after_state_hash,
            "converged": self.converged,
            "actuator_kind": self.actuator_kind,
            "previous_receipt_hash": self.previous_receipt_hash,
            "unexpected_fields": list(self.unexpected_fields),
            "issued_at": self.issued_at,
        }

    @property
    def receipt_hash(self) -> str:
        """This receipt's own hash — what the *next* receipt in the chain links to.

        Excludes nothing: issued_at is part of the hash, so two otherwise-
        identical receipts issued at different times still chain distinctly.
        """
        canonical = json.dumps(self.to_dict(), sort_keys=True, default=str).encode("utf-8")
        return "sha256:" + hashlib.sha256(canonical).hexdigest()


class ReceiptChain:
    """Tracks the last-issued receipt's hash so the next one can link to it.

    One chain per audit trail you want tamper-evidence over (e.g. one per
    actuator, or one for the whole control plane) — pass the same instance
    into every pipeline run that should share a sequence.
    """

    def __init__(self) -> None:
        self._last_hash: str | None = None

    @property
    def last_hash(self) -> str | None:
        return self._last_hash

    def next_previous_hash(self) -> str | None:
        """The value the next receipt's `previous_receipt_hash` should carry."""
        return self._last_hash

    def record(self, receipt: Receipt) -> Receipt:
        """Advance the chain to `receipt` and return it, for call-site chaining."""
        self._last_hash = receipt.receipt_hash
        return receipt


@dataclass(frozen=True)
class ChainVerificationResult:
    valid: bool
    broken_at_index: int | None = None
    reason: str = ""


def verify_chain(receipts: list[Receipt]) -> ChainVerificationResult:
    """Walk a sequence of receipts and confirm each one links to the receipt before it.

    What this catches: any receipt whose stored content was altered after
    the fact, and any receipt deleted from or reordered within the middle
    of the sequence — both change what the *next* receipt's
    previous_receipt_hash should have been, so recomputing each hash and
    comparing it to what the following receipt actually recorded exposes
    the break.

    What this does NOT catch: tampering with, or truncation of, the LAST
    receipt in the sequence — nothing in this list points forward to it, so
    nothing here can notice if it's altered or simply missing. A backward-
    linking chain only proves the history *up to* its tip; the tip itself
    needs an anchor outside this sequence (publish its hash, sign it,
    checkpoint it somewhere the party who could tamper with the store does
    not control) if the most recent entry also needs tamper-evidence. Don't
    let the word "receipt" imply a stronger guarantee than this — this
    function's return value is the actual, checked claim.
    """
    if not receipts:
        return ChainVerificationResult(valid=True)

    if receipts[0].previous_receipt_hash is not None:
        return ChainVerificationResult(
            valid=False,
            broken_at_index=0,
            reason="first receipt in the sequence must have no predecessor",
        )

    for i in range(1, len(receipts)):
        expected = receipts[i - 1].receipt_hash
        if receipts[i].previous_receipt_hash != expected:
            return ChainVerificationResult(
                valid=False,
                broken_at_index=i,
                reason=f"receipt {i} does not link to receipt {i - 1}: chain broken",
            )

    return ChainVerificationResult(valid=True)
