"""The Node model: a live instance created from a NodeSeed."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from mesh_substrate.seed import NodeSeed


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class NodeStatus(str, Enum):
    REGISTERED = "registered"
    ACTIVE = "active"
    STALE = "stale"


class Node(BaseModel):
    """A running instance produced from a seed.

    ``node_id`` is never stored independently — it is always
    recomputed from ``seed``, so a Node's identity can't drift from the
    seed that produced it.
    """

    seed: NodeSeed
    host: str
    port: int
    status: NodeStatus = NodeStatus.REGISTERED
    last_heartbeat_at: str = Field(default_factory=_now_iso)
    metadata: dict = Field(default_factory=dict)

    @property
    def node_id(self) -> str:
        return self.seed.node_id
