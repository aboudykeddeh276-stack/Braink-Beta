import pytest

from braink_reasoning.learning_log import (
    LearningLog,
    logged_ask,
    logged_register,
    verify_log_chain,
)
from braink_reasoning.registry import TopicHandler, TopicRegistry, TopicStatus, UnknownTopicError


def _handler(topic="double", fn=lambda x: x * 2):
    return TopicHandler(
        topic=topic, function=fn, status=TopicStatus.VERIFIED,
        description="doubles a number", required_params=("x",),
    )


def test_record_learned_and_record_answer_chain_together():
    log = LearningLog()
    log.record_learned(_handler())
    log.record_answer("double", {"x": 3}, 6)

    assert [e.kind for e in log.entries] == ["learned", "answered"]
    assert log.entries[1].previous_entry_hash == log.entries[0].entry_hash


def test_verify_log_chain_accepts_untampered_log():
    log = LearningLog()
    log.record_learned(_handler())
    log.record_answer("double", {"x": 3}, 6)
    valid, reason = verify_log_chain(log)
    assert valid is True
    assert reason == ""


def test_verify_log_chain_accepts_empty_log():
    assert verify_log_chain(LearningLog()) == (True, "")


def test_json_round_trip_reproduces_identical_chain():
    log = LearningLog()
    log.record_learned(_handler())
    log.record_answer("double", {"x": 3}, 6)

    rehydrated = LearningLog.from_json(log.to_json())
    assert [e.entry_hash for e in rehydrated.entries] == [e.entry_hash for e in log.entries]
    assert verify_log_chain(rehydrated) == (True, "")


def test_verify_log_chain_detects_tampering_with_a_middle_entry():
    log = LearningLog()
    log.record_learned(_handler())
    log.record_answer("double", {"x": 3}, 6)
    log.record_answer("double", {"x": 4}, 8)

    tampered = LearningLog.from_json(log.to_json())
    object.__setattr__(tampered.entries[1], "detail", {"params": {"x": 999}, "result": 6})

    valid, reason = verify_log_chain(tampered)
    assert valid is False
    # Caught immediately at the tampered entry itself: its content no
    # longer matches its own (untouched, now-stale) entry_hash -- the
    # linkage check on entry 2 would also fail, but content-hash is
    # checked first within the same loop iteration for entry 1.
    assert "entry 1" in reason
    assert "does not match its own entry_hash" in reason


def test_logged_register_records_a_learned_entry():
    log = LearningLog()
    registry = TopicRegistry()
    logged_register(log, registry, _handler())

    assert "double" in registry
    assert len(log.entries) == 1
    assert log.entries[0].kind == "learned"


def test_logged_ask_executes_and_records_an_answered_entry():
    log = LearningLog()
    registry = TopicRegistry()
    logged_register(log, registry, _handler())

    answer = logged_ask(log, registry, "double", x=5)

    assert answer.result == 10
    assert log.entries[-1].kind == "answered"
    assert log.entries[-1].detail == {"params": {"x": 5}, "result": 10}


def test_logged_ask_does_not_log_on_failure():
    log = LearningLog()
    registry = TopicRegistry()
    with pytest.raises(UnknownTopicError):
        logged_ask(log, registry, "nonexistent", x=1)
    assert len(log.entries) == 0
