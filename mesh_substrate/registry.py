"""NodeRegistry: the only object that mutates node state.

Every mutation (register, heartbeat, expiry) records a lineage
snapshot, so a node's full history is always reconstructable and
tamper-evident via ``lineage.verify_lineage`` even though the registry
itself only keeps the current ``Node`` in memory.

In-memory only, single process. Distributing this across machines (a
real mesh) is the next milestone and needs its own transport design —
this class is the substrate that transport would sit on top of, not a
network service itself.
"""

from __future__ import annotations

from datetime import datetime, timezone

from mesh_substrate.node import Node, NodeStatus
from mesh_substrate.seed import NodeSeed
from mesh_substrate.snapshot import NodeSnapshot, flatten, rehydrate


class NodeRegistry:
    def __init__(self, heartbeat_ttl_seconds: float = 30.0) -> None:
        self._nodes: dict[str, Node] = {}
        self._lineage: dict[str, list[NodeSnapshot]] = {}
        self._heartbeat_ttl_seconds = heartbeat_ttl_seconds

    def register(
        self, seed: NodeSeed, host: str, port: int, metadata: dict | None = None
    ) -> Node:
        node_id = seed.node_id
        if node_id in self._nodes:
            raise ValueError(f"node already registered: {node_id}")

        node = Node(seed=seed, host=host, port=port, metadata=metadata or {})
        self._nodes[node_id] = node
        self._record_snapshot(node)
        return node

    def heartbeat(self, node_id: str) -> Node:
        node = self._require(node_id)
        updated = node.model_copy(
            update={
                "status": NodeStatus.ACTIVE,
                "last_heartbeat_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._nodes[node_id] = updated
        self._record_snapshot(updated)
        return updated

    def get(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def list_active(self, now: datetime | None = None) -> list[Node]:
        now = now or datetime.now(timezone.utc)
        return [node for node in self._nodes.values() if self._is_within_ttl(node, now)]

    def expire_stale(self, now: datetime | None = None) -> list[Node]:
        """Mark nodes whose heartbeat has lapsed as STALE. Returns the newly-expired nodes."""
        now = now or datetime.now(timezone.utc)
        expired: list[Node] = []
        for node_id, node in list(self._nodes.items()):
            if node.status != NodeStatus.STALE and not self._is_within_ttl(node, now):
                updated = node.model_copy(update={"status": NodeStatus.STALE})
                self._nodes[node_id] = updated
                self._record_snapshot(updated)
                expired.append(updated)
        return expired

    def lineage(self, node_id: str) -> list[NodeSnapshot]:
        """This node's full flatten history, oldest first."""
        return list(self._lineage.get(node_id, ()))

    def rehydrate_latest(self, node_id: str) -> Node:
        """Reconstruct the node from its most recent lineage snapshot alone,
        independent of the in-memory `_nodes` dict — proving the lineage
        itself carries enough information to recover current state."""
        chain = self._lineage.get(node_id)
        if not chain:
            raise KeyError(f"no lineage recorded for {node_id}")
        return rehydrate(chain[-1])

    def _record_snapshot(self, node: Node) -> None:
        chain = self._lineage.setdefault(node.node_id, [])
        previous_hash = chain[-1].snapshot_hash if chain else None
        chain.append(flatten(node, previous_snapshot_hash=previous_hash))

    def _is_within_ttl(self, node: Node, now: datetime) -> bool:
        last_heartbeat = datetime.fromisoformat(node.last_heartbeat_at)
        return (now - last_heartbeat).total_seconds() <= self._heartbeat_ttl_seconds

    def _require(self, node_id: str) -> Node:
        node = self._nodes.get(node_id)
        if node is None:
            raise KeyError(f"no such node: {node_id}")
        return node
