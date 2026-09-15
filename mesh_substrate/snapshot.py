"""Flatten / rehydrate: compact, hash-verified node snapshots.

"Flatten" takes a live ``Node`` and produces a ``NodeSnapshot`` — its
full state plus a hash of that state. "Rehydrate" takes a snapshot and
reconstructs the ``Node``, but only after checking two things:

1. The snapshot's ``state_hash`` matches a fresh hash of its own
   ``state`` (the snapshot wasn't altered after being taken).
2. The rehydrated node's ``node_id`` (recomputed from its seed) matches
   the ``node_id`` the snapshot was filed under (the seed inside the
   state wasn't swapped for a different one).

Either check failing means the snapshot cannot be trusted, and
rehydration refuses rather than silently returning a node that no
longer matches its own history.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from mesh_substrate.node import Node


class SnapshotIntegrityError(Exception):
    """Raised when a snapshot's recorded hash or node_id doesn't match its own content."""


def hash_state(state: dict[str, Any]) -> str:
    canonical = json.dumps(state, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class NodeSnapshot:
    """A flattened, hash-verified point-in-time copy of a Node's state."""

    node_id: str
    state: dict[str, Any]
    state_hash: str
    previous_snapshot_hash: str | None
    flattened_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def snapshot_hash(self) -> str:
        """This snapshot's own hash — what the next snapshot in the lineage links to."""
        payload = {
            "node_id": self.node_id,
            "state": self.state,
            "state_hash": self.state_hash,
            "previous_snapshot_hash": self.previous_snapshot_hash,
            "flattened_at": self.flattened_at,
        }
        canonical = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return "sha256:" + hashlib.sha256(canonical).hexdigest()


def flatten(node: Node, previous_snapshot_hash: str | None = None) -> NodeSnapshot:
    state = node.model_dump()
    return NodeSnapshot(
        node_id=node.node_id,
        state=state,
        state_hash=hash_state(state),
        previous_snapshot_hash=previous_snapshot_hash,
    )


def rehydrate(snapshot: NodeSnapshot) -> Node:
    if hash_state(snapshot.state) != snapshot.state_hash:
        raise SnapshotIntegrityError(
            f"snapshot for {snapshot.node_id} has been altered: state does not match state_hash"
        )

    node = Node(**snapshot.state)
    if node.node_id != snapshot.node_id:
        raise SnapshotIntegrityError(
            f"snapshot claims node_id={snapshot.node_id!r} but its seed recomputes to "
            f"{node.node_id!r}: seed was swapped after flattening"
        )
    return node
