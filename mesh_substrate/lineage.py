"""Lineage: verifying that a node's snapshot history hasn't been tampered with.

Each node accumulates a sequence of ``NodeSnapshot``s over its life
(one per registration, heartbeat, or status change). ``verify_lineage``
walks that sequence and confirms each snapshot's
``previous_snapshot_hash`` matches the hash of the snapshot before it —
the same backward-linking check ``workspace_control_plane.receipts``
uses for receipts, applied here to node snapshots instead.

Like that chain, this catches tampering with or deletion of any
snapshot *except* the last one in the sequence — nothing points forward
to the tip, so an external anchor is still needed if the most recent
snapshot itself must be tamper-evident.
"""

from __future__ import annotations

from dataclasses import dataclass

from mesh_substrate.snapshot import NodeSnapshot


@dataclass(frozen=True)
class LineageVerificationResult:
    valid: bool
    broken_at_index: int | None = None
    reason: str = ""


def verify_lineage(snapshots: list[NodeSnapshot]) -> LineageVerificationResult:
    if not snapshots:
        return LineageVerificationResult(valid=True)

    if snapshots[0].previous_snapshot_hash is not None:
        return LineageVerificationResult(
            valid=False,
            broken_at_index=0,
            reason="first snapshot in a node's lineage must have no predecessor",
        )

    node_id = snapshots[0].node_id
    for i in range(1, len(snapshots)):
        if snapshots[i].node_id != node_id:
            return LineageVerificationResult(
                valid=False,
                broken_at_index=i,
                reason=f"snapshot {i} belongs to a different node ({snapshots[i].node_id})",
            )
        expected = snapshots[i - 1].snapshot_hash
        if snapshots[i].previous_snapshot_hash != expected:
            return LineageVerificationResult(
                valid=False,
                broken_at_index=i,
                reason=f"snapshot {i} does not link to snapshot {i - 1}: lineage broken",
            )

    return LineageVerificationResult(valid=True)
