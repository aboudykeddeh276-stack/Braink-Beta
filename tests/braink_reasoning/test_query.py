import pytest

from braink_reasoning.query import explain
from braink_reasoning.registry import TopicStatus
from braink_reasoning.topics import build_default_registry


def test_explain_combines_prerequisites_and_answer():
    registry = build_default_registry()
    result = explain(registry, "chemistry.compound", name="water")

    assert result["topic"] == "chemistry.compound"
    assert result["prerequisites"] == ["periodic_table.element"]
    assert result["status"] == TopicStatus.VERIFIED.value
    assert result["result"]["formula"] == "H2O"


def test_explain_has_empty_prerequisites_for_a_topic_with_no_references():
    registry = build_default_registry()
    result = explain(registry, "periodic_table.element", identifier="Au")
    assert result["prerequisites"] == []


def test_explain_raises_on_unknown_topic():
    from braink_reasoning.registry import UnknownTopicError

    registry = build_default_registry()
    with pytest.raises(UnknownTopicError):
        explain(registry, "nonexistent")


def test_explain_raises_on_missing_params():
    registry = build_default_registry()
    with pytest.raises(TypeError):
        explain(registry, "periodic_table.element")
