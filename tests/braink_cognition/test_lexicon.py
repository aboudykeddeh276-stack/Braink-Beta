import pytest

from braink_cognition.lexicon import LexicalTree


def _animal_tree() -> LexicalTree:
    tree = LexicalTree()
    tree.add_root("animal", definition="a living organism")
    tree.add_child("mammal", parent="animal")
    tree.add_child("reptile", parent="animal")
    tree.add_child("dog", parent="mammal")
    tree.add_child("cat", parent="mammal")
    return tree


def test_depth_of_root_is_zero():
    tree = _animal_tree()
    assert tree.depth("animal") == 0


def test_depth_increases_with_each_level():
    tree = _animal_tree()
    assert tree.depth("mammal") == 1
    assert tree.depth("dog") == 2


def test_lca_of_siblings_is_their_parent():
    tree = _animal_tree()
    assert tree.lca("dog", "cat") == "mammal"


def test_lca_of_cousins_is_the_shared_grandparent():
    tree = _animal_tree()
    assert tree.lca("dog", "reptile") == "animal"


def test_distance_formula_matches_lca_depth_relation():
    tree = _animal_tree()
    # d_T(x, y) = depth(x) + depth(y) - 2 * depth(LCA(x, y))
    assert tree.distance("dog", "cat") == 2
    assert tree.distance("dog", "reptile") == 3


def test_distance_to_self_is_zero():
    tree = _animal_tree()
    assert tree.distance("dog", "dog") == 0


def test_distance_is_symmetric():
    tree = _animal_tree()
    assert tree.distance("dog", "reptile") == tree.distance("reptile", "dog")


def test_unknown_symbol_raises_keyerror():
    tree = _animal_tree()
    with pytest.raises(KeyError):
        tree.depth("unicorn")
    with pytest.raises(KeyError):
        tree.lca("dog", "unicorn")


def test_duplicate_symbol_raises_valueerror():
    tree = _animal_tree()
    with pytest.raises(ValueError):
        tree.add_child("dog", parent="reptile")


def test_child_with_missing_parent_raises_keyerror():
    tree = LexicalTree()
    with pytest.raises(KeyError):
        tree.add_child("orphan", parent="nobody")


def test_disjoint_trees_have_no_common_ancestor():
    tree = LexicalTree()
    tree.add_root("animal")
    tree.add_root("mineral")
    with pytest.raises(ValueError):
        tree.lca("animal", "mineral")
