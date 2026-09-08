import pytest

from braink_reasoning.registry import TopicHandler, TopicRegistry, TopicStatus, UnknownTopicError


def _handler(topic: str, fn=lambda: None):
    return TopicHandler(
        topic=topic, function=fn, status=TopicStatus.VERIFIED, description="", required_params=()
    )


def test_register_and_get_returns_the_same_handler():
    registry = TopicRegistry()
    handler = _handler("double", lambda x: x * 2)
    registry.register(handler)
    assert registry.get("double") is handler
    assert "double" in registry


def test_unknown_topic_raises_with_known_topics_listed():
    registry = TopicRegistry()
    registry.register(_handler("known"))
    with pytest.raises(UnknownTopicError, match="known"):
        registry.get("unknown")


def test_registry_is_not_sealed_and_can_grow_at_runtime():
    registry = TopicRegistry()
    registry.register(_handler("a"))
    assert registry.topics() == ["a"]
    registry.register(_handler("b"))
    assert registry.topics() == ["a", "b"]


def test_registering_same_topic_twice_replaces_the_handler():
    registry = TopicRegistry()
    registry.register(_handler("x", lambda: 1))
    registry.register(_handler("x", lambda: 2))
    assert registry.get("x").function() == 2
