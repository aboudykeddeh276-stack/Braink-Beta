import pytest

from braink_cognition.hebbian import HebbianGraph, Polarity


def test_unknown_edge_weight_defaults_to_zero():
    graph = HebbianGraph()
    assert graph.weight("a", "b") == 0.0


def test_positive_reinforcement_moves_weight_toward_one():
    graph = HebbianGraph(learning_rate=0.5)
    w1 = graph.reinforce("a", "b", Polarity.POSITIVE)
    w2 = graph.reinforce("a", "b", Polarity.POSITIVE)
    assert 0 < w1 < w2 < 1


def test_negative_reinforcement_moves_weight_toward_minus_one():
    graph = HebbianGraph(learning_rate=0.5)
    w1 = graph.reinforce("a", "b", Polarity.NEGATIVE)
    w2 = graph.reinforce("a", "b", Polarity.NEGATIVE)
    assert -1 < w1 < 0
    assert w1 > w2 > -1


def test_weight_saturates_but_never_exceeds_bounds():
    graph = HebbianGraph(learning_rate=0.9)
    weight = 0.0
    for _ in range(100):
        weight = graph.reinforce("a", "b", Polarity.POSITIVE)
    assert 0 < weight <= 1


def test_sign_is_not_collapsed_across_distinct_edges():
    graph = HebbianGraph()
    graph.reinforce("a", "b", Polarity.POSITIVE)
    graph.reinforce("a", "c", Polarity.NEGATIVE)
    assert graph.weight("a", "b") > 0
    assert graph.weight("a", "c") < 0


def test_edges_are_directed():
    graph = HebbianGraph()
    graph.reinforce("a", "b", Polarity.POSITIVE)
    assert graph.weight("a", "b") != 0.0
    assert graph.weight("b", "a") == 0.0


def test_reinforcement_can_reverse_sign_over_time():
    graph = HebbianGraph(learning_rate=0.5)
    graph.reinforce("a", "b", Polarity.POSITIVE)
    graph.reinforce("a", "b", Polarity.POSITIVE)
    assert graph.weight("a", "b") > 0
    for _ in range(10):
        graph.reinforce("a", "b", Polarity.NEGATIVE)
    assert graph.weight("a", "b") < 0


def test_invalid_learning_rate_rejected():
    with pytest.raises(ValueError):
        HebbianGraph(learning_rate=0)
    with pytest.raises(ValueError):
        HebbianGraph(learning_rate=1.5)
