import pytest

from braink_reasoning.graph import CircularReferenceError, resolve_understanding_path
from braink_reasoning.registry import TopicHandler, TopicRegistry, TopicStatus, UnknownTopicError


def _topic(name: str, references: tuple[str, ...] = ()):
    return TopicHandler(
        topic=name,
        function=lambda: None,
        status=TopicStatus.VERIFIED,
        description="",
        required_params=(),
        references=references,
    )


def test_topic_with_no_references_resolves_to_just_itself():
    registry = TopicRegistry()
    registry.register(_topic("atom"))
    assert resolve_understanding_path(registry, "atom") == ["atom"]


def test_linear_chain_orders_prerequisites_before_the_target():
    # "molecule" needs "atom" needs "electron" -- understand electron first.
    registry = TopicRegistry()
    registry.register(_topic("electron"))
    registry.register(_topic("atom", references=("electron",)))
    registry.register(_topic("molecule", references=("atom",)))

    assert resolve_understanding_path(registry, "molecule") == ["electron", "atom", "molecule"]


def test_diamond_dependency_appears_exactly_once():
    #      periodic_table
    #       /          \
    #   element        atom
    #       \          /
    #        electron
    registry = TopicRegistry()
    registry.register(_topic("electron"))
    registry.register(_topic("element", references=("electron",)))
    registry.register(_topic("atom", references=("electron",)))
    registry.register(_topic("periodic_table", references=("element", "atom")))

    order = resolve_understanding_path(registry, "periodic_table")

    assert order[-1] == "periodic_table"
    assert order.count("electron") == 1
    assert order.index("electron") < order.index("element")
    assert order.index("electron") < order.index("atom")


def test_circular_reference_is_detected_not_infinite_looped():
    registry = TopicRegistry()
    registry.register(_topic("a", references=("b",)))
    registry.register(_topic("b", references=("a",)))

    with pytest.raises(CircularReferenceError, match="a -> b -> a"):
        resolve_understanding_path(registry, "a")


def test_reference_to_unregistered_topic_raises_unknown_topic_error():
    registry = TopicRegistry()
    registry.register(_topic("orphan", references=("nonexistent",)))

    with pytest.raises(UnknownTopicError):
        resolve_understanding_path(registry, "orphan")
