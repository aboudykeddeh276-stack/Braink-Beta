"""Evidence / Receipt Plane.

A receipt is generated only as the direct output of one real pipeline
run: an actual before-state hash and after-state hash computed here, the
actor and scopes actually admitted, and the actual verification result.
There is no pre-filled or hand-authored "success" receipt anywhere in
this package — every field comes from a value the runtime observed.
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
    unexpected_fields: tuple[str, ...] = ()
    # Post-conditions the capability declares (capability_registry) that this
    # milestone has no actuator/check for yet. Never silently treated as
    # verified: a receipt only claims "converged", not that these hold.
    unverified_post_conditions: tuple[str, ...] = ()
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
            "unexpected_fields": list(self.unexpected_fields),
            "unverified_post_conditions": list(self.unverified_post_conditions),
            "issued_at": self.issued_at,
        }
