import dataclasses

from mesh_substrate.lineage import verify_lineage
from mesh_substrate.node import Node
from mesh_substrate.seed import NodeSeed
from mesh_substrate.snapshot import flatten


def _build_lineage(n: int, identity="alice", config="cfg-1") -> list:
    seed = NodeSeed(identity_seed=identity, config_seed=config)
    node = Node(seed=seed, host="127.0.0.1", port=9000)
    snapshots = []
    previous_hash = None
    for i in range(n):
        node = node.model_copy(update={"port": 9000 + i})
        snap = flatten(node, previous_snapshot_hash=previous_hash)
        snapshots.append(snap)
        previous_hash = snap.snapshot_hash
    return snapshots


def test_verify_lineage_accepts_untampered_chain():
    result = verify_lineage(_build_lineage(4))

    assert result.valid is True


def test_verify_lineage_accepts_empty_sequence():
    assert verify_lineage([]).valid is True


def test_verify_lineage_rejects_first_snapshot_with_a_predecessor():
    snapshots = _build_lineage(2)
    forged_first = dataclasses.replace(snapshots[0], previous_snapshot_hash="sha256:bogus")

    result = verify_lineage([forged_first, snapshots[1]])

    assert result.valid is False
    assert result.broken_at_index == 0


def test_verify_lineage_detects_a_snapshot_deleted_from_the_middle():
    snapshots = _build_lineage(4)
    tampered = [snapshots[0], snapshots[2], snapshots[3]]

    result = verify_lineage(tampered)

    assert result.valid is False
    assert result.broken_at_index == 1


def test_verify_lineage_detects_content_altered_after_the_fact():
    snapshots = _build_lineage(3)
    altered_middle = dataclasses.replace(snapshots[1], state={**snapshots[1].state, "port": 1})
    tampered = [snapshots[0], altered_middle, snapshots[2]]

    result = verify_lineage(tampered)

    assert result.valid is False
    assert result.broken_at_index == 2


def test_verify_lineage_detects_a_snapshot_from_a_different_node():
    own = _build_lineage(2, identity="alice")
    other = _build_lineage(1, identity="mallory")

    result = verify_lineage([own[0], other[0]])

    assert result.valid is False
    assert result.broken_at_index == 1
