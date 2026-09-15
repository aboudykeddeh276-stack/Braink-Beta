from datetime import datetime, timedelta, timezone

import pytest

from mesh_substrate.lineage import verify_lineage
from mesh_substrate.node import NodeStatus
from mesh_substrate.registry import NodeRegistry
from mesh_substrate.seed import NodeSeed


def test_register_creates_a_node():
    registry = NodeRegistry()
    seed = NodeSeed(identity_seed="alice", config_seed="cfg-1")

    node = registry.register(seed, host="127.0.0.1", port=9001)

    assert registry.get(node.node_id) == node
    assert node.status == NodeStatus.REGISTERED


def test_register_same_seed_twice_raises():
    registry = NodeRegistry()
    seed = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    registry.register(seed, host="127.0.0.1", port=9001)

    with pytest.raises(ValueError):
        registry.register(seed, host="10.0.0.5", port=9999)


def test_heartbeat_marks_node_active_and_updates_timestamp():
    registry = NodeRegistry()
    seed = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    node = registry.register(seed, host="127.0.0.1", port=9001)

    updated = registry.heartbeat(node.node_id)

    assert updated.status == NodeStatus.ACTIVE
    assert updated.last_heartbeat_at >= node.last_heartbeat_at


def test_heartbeat_unknown_node_raises():
    registry = NodeRegistry()

    with pytest.raises(KeyError):
        registry.heartbeat("node:doesnotexist")


def test_list_active_excludes_nodes_past_ttl():
    registry = NodeRegistry(heartbeat_ttl_seconds=30)
    seed = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    registry.register(seed, host="127.0.0.1", port=9001)

    future = datetime.now(timezone.utc) + timedelta(seconds=60)

    assert registry.list_active(now=future) == []


def test_list_active_includes_nodes_within_ttl():
    registry = NodeRegistry(heartbeat_ttl_seconds=30)
    seed = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    node = registry.register(seed, host="127.0.0.1", port=9001)

    soon = datetime.now(timezone.utc) + timedelta(seconds=5)

    assert registry.list_active(now=soon) == [node]


def test_expire_stale_marks_lapsed_nodes_and_returns_them():
    registry = NodeRegistry(heartbeat_ttl_seconds=30)
    seed = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    registry.register(seed, host="127.0.0.1", port=9001)

    future = datetime.now(timezone.utc) + timedelta(seconds=60)
    expired = registry.expire_stale(now=future)

    assert len(expired) == 1
    assert expired[0].status == NodeStatus.STALE


def test_expire_stale_does_not_reexpire_already_stale_nodes():
    registry = NodeRegistry(heartbeat_ttl_seconds=30)
    seed = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    registry.register(seed, host="127.0.0.1", port=9001)

    future = datetime.now(timezone.utc) + timedelta(seconds=60)
    registry.expire_stale(now=future)
    second_pass = registry.expire_stale(now=future + timedelta(seconds=60))

    assert second_pass == []


def test_lineage_grows_with_each_mutation():
    registry = NodeRegistry()
    seed = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    node = registry.register(seed, host="127.0.0.1", port=9001)
    registry.heartbeat(node.node_id)
    registry.heartbeat(node.node_id)

    history = registry.lineage(node.node_id)

    assert len(history) == 3
    assert verify_lineage(history).valid is True


def test_rehydrate_latest_matches_current_registry_state():
    registry = NodeRegistry()
    seed = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    node = registry.register(seed, host="127.0.0.1", port=9001)
    registry.heartbeat(node.node_id)

    rehydrated = registry.rehydrate_latest(node.node_id)

    assert rehydrated == registry.get(node.node_id)


def test_rehydrate_latest_unknown_node_raises():
    registry = NodeRegistry()

    with pytest.raises(KeyError):
        registry.rehydrate_latest("node:doesnotexist")
