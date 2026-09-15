"""Mesh substrate: deterministic, rehydratable node instances.

A node is instantiated from a ``NodeSeed`` — two independent values
(``identity_seed``, ``config_seed``) that together determine the node's
id. A node can be *flattened* to a compact, hash-verified
``NodeSnapshot`` at any point, and *rehydrated* back into a full
``Node`` later. Every flatten is appended to that node's lineage chain
(``lineage.py``), so tampering with any snapshot in the middle is
detectable the same way it is for ``workspace_control_plane``'s
receipt chain — this package does not import that one; the pattern is
duplicated deliberately because the two are independent concerns.

``NodeRegistry`` (``registry.py``) is the only object that mutates node
state: register, heartbeat, and stale-expiry all go through it, and it
records a lineage snapshot on every state change.

Out of scope for this milestone: network transport between nodes (how a
node actually reaches another node over HTTP/WebSocket/etc.) and any
payload/work protocol exchanged between them. Both need concrete answers
(deployment topology, message shape) before they can be built honestly
rather than guessed at.
"""

from mesh_substrate.node import Node, NodeStatus
from mesh_substrate.registry import NodeRegistry
from mesh_substrate.seed import NodeSeed
from mesh_substrate.snapshot import NodeSnapshot, SnapshotIntegrityError, flatten, rehydrate

__all__ = [
    "Node",
    "NodeStatus",
    "NodeRegistry",
    "NodeSeed",
    "NodeSnapshot",
    "SnapshotIntegrityError",
    "flatten",
    "rehydrate",
]
