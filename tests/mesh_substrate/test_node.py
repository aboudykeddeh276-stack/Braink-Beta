from mesh_substrate.node import Node, NodeStatus
from mesh_substrate.seed import NodeSeed


def test_node_id_delegates_to_seed():
    seed = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    node = Node(seed=seed, host="127.0.0.1", port=9001)

    assert node.node_id == seed.node_id


def test_node_defaults_to_registered_status():
    seed = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    node = Node(seed=seed, host="127.0.0.1", port=9001)

    assert node.status == NodeStatus.REGISTERED


def test_two_nodes_from_identical_seeds_have_identical_ids():
    seed_a = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    seed_b = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    node_a = Node(seed=seed_a, host="127.0.0.1", port=9001)
    node_b = Node(seed=seed_b, host="10.0.0.5", port=9999)

    assert node_a.node_id == node_b.node_id
