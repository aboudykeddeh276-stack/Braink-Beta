from mesh_substrate.seed import NodeSeed


def test_same_seed_pair_produces_same_id():
    a = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    b = NodeSeed(identity_seed="alice", config_seed="cfg-1")

    assert a.node_id == b.node_id


def test_different_identity_seed_changes_id():
    a = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    b = NodeSeed(identity_seed="bob", config_seed="cfg-1")

    assert a.node_id != b.node_id


def test_different_config_seed_changes_id():
    a = NodeSeed(identity_seed="alice", config_seed="cfg-1")
    b = NodeSeed(identity_seed="alice", config_seed="cfg-2")

    assert a.node_id != b.node_id


def test_node_id_is_prefixed():
    seed = NodeSeed(identity_seed="alice", config_seed="cfg-1")

    assert seed.node_id.startswith("node:")
