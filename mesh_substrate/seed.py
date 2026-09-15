"""Node seeds: the deterministic input a node instance is created from.

A seed is two independent values — ``identity_seed`` and
``config_seed`` — not one combined blob. Keeping them separate means a
node's identity and its configuration can vary independently: the same
identity_seed with a different config_seed is a different node
instance (different id), which is what makes the id a genuine function
of both rather than of a single opaque string.
"""

from __future__ import annotations

import hashlib

from pydantic import BaseModel


class NodeSeed(BaseModel):
    """Two independent deterministic values that together determine a node's id."""

    identity_seed: str
    config_seed: str

    @property
    def node_id(self) -> str:
        """Deterministic id derived from both seed values.

        Same (identity_seed, config_seed) pair always produces the same
        id; changing either value changes it. This is what "rehydrate"
        checks against later — a rehydrated node must recompute the same
        id its snapshot recorded.
        """
        digest = hashlib.sha256(f"{self.identity_seed}:{self.config_seed}".encode()).hexdigest()
        return f"node:{digest[:16]}"
