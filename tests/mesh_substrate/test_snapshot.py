import dataclasses

import pytest

from mesh_substrate.node import Node
from mesh_substrate.seed import NodeSeed
from mesh_substrate.snapshot import SnapshotIntegrityError, flatten, hash_state, rehydrate


def _make_node(identity="alice", config="cfg-1", host="127.0.0.1", port=9001):
    seed = NodeSeed(identity_seed=identity, config_seed=config)
    return Node(seed=seed, host=host, port=port)


def test_flatten_then_rehydrate_round_trips():
    node = _make_node()

    snapshot = flatten(node)
    rehydrated = rehydrate(snapshot)

    assert rehydrated == node


def test_flatten_records_node_id():
    node = _make_node()

    snapshot = flatten(node)

    assert snapshot.node_id == node.node_id


def test_first_snapshot_has_no_predecessor():
    node = _make_node()

    snapshot = flatten(node)

    assert snapshot.previous_snapshot_hash is None


def test_snapshot_chains_to_previous_hash():
    node = _make_node()
    first = flatten(node)

    updated = node.model_copy(update={"port": 9999})
    second = flatten(updated, previous_snapshot_hash=first.snapshot_hash)

    assert second.previous_snapshot_hash == first.snapshot_hash


def test_rehydrate_rejects_altered_state():
    node = _make_node()
    snapshot = flatten(node)

    tampered = dataclasses.replace(snapshot, state={**snapshot.state, "port": 1})

    with pytest.raises(SnapshotIntegrityError):
        rehydrate(tampered)


def test_rehydrate_rejects_seed_swapped_for_a_different_node():
    node = _make_node()
    other_node = _make_node(identity="mallory")
    snapshot = flatten(node)

    # Attacker swaps in a different node's state but keeps the original
    # node_id/state_hash label, hoping rehydrate() trusts the label.
    other_state = other_node.model_dump()
    forged = dataclasses.replace(
        snapshot,
        state=other_state,
        state_hash=hash_state(other_state),
    )

    with pytest.raises(SnapshotIntegrityError):
        rehydrate(forged)
