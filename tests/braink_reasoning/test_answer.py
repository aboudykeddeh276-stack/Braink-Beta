import pytest

from braink_reasoning.answer import ask
from braink_reasoning.registry import TopicHandler, TopicRegistry, TopicStatus


def _registry_with_add():
    registry = TopicRegistry()
    registry.register(
        TopicHandler(
            topic="add",
            function=lambda a, b: a + b,
            status=TopicStatus.VERIFIED,
            description="adds two numbers",
            required_params=("a", "b"),
        )
    )
    return registry


def test_ask_executes_the_real_function_and_returns_its_actual_result():
    registry = _registry_with_add()
    answer = ask(registry, "add", a=2, b=3)
    assert answer.result == 5
    assert answer.status == TopicStatus.VERIFIED
    assert answer.topic == "add"
    assert answer.inputs == {"a": 2, "b": 3}


def test_ask_records_which_function_actually_computed_the_result():
    registry = _registry_with_add()
    answer = ask(registry, "add", a=1, b=1)
    assert "add" in answer.computed_by or "lambda" in answer.computed_by


def test_ask_raises_on_missing_required_params():
    registry = _registry_with_add()
    with pytest.raises(TypeError):
        ask(registry, "add", a=1)


def test_ask_raises_on_unknown_topic_instead_of_guessing():
    registry = TopicRegistry()
    with pytest.raises(KeyError):
        ask(registry, "nonexistent", x=1)
