import pytest

from braink_reasoning.answer import ask
from braink_reasoning.registry import TopicStatus
from braink_reasoning.topics import build_default_registry


def test_default_registry_includes_expected_topics():
    registry = build_default_registry()
    expected = {
        "collision_probability",
        "queue_depth",
        "channel_capacity",
        "bit_erasure_power",
        "rule110_generations",
        "composite_warrant",
    }
    assert expected.issubset(set(registry.topics()))


def test_collision_probability_topic_computes_a_real_value():
    registry = build_default_registry()
    answer = ask(registry, "collision_probability", num_samples=100_000, space_size=2**32)
    assert answer.status == TopicStatus.VERIFIED
    assert answer.result == pytest.approx(0.6878, abs=1e-3)


def test_queue_depth_topic_computes_a_real_value():
    registry = build_default_registry()
    answer = ask(
        registry,
        "queue_depth",
        arrival_rate=0.033,
        mean_service_time=0.002,
        service_time_stddev=0.001,
    )
    assert answer.result == pytest.approx(2.7227e-9, rel=1e-3)


def test_composite_warrant_topic_computes_a_real_value():
    registry = build_default_registry()
    answer = ask(registry, "composite_warrant", warrants=[0.9, 0.8, 0.7])
    assert answer.result["recovered_w"] == pytest.approx(0.994, abs=1e-9)


def test_bit_erasure_power_topic_is_tagged_conceptual_not_verified():
    registry = build_default_registry()
    answer = ask(
        registry,
        "bit_erasure_power",
        bits_per_cycle=1000,
        frequency_hz=100,
        temperature_kelvin=300.0,
    )
    assert answer.status == TopicStatus.CONCEPTUAL


def test_rule110_generations_topic_computes_real_ca_steps():
    registry = build_default_registry()
    answer = ask(registry, "rule110_generations", initial_state=[0, 0, 1, 0, 0], generations=1)
    assert answer.result[1] == [0, 1, 1, 0, 0]
