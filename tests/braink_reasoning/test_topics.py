import pytest

from braink_reasoning.answer import ask
from braink_reasoning.graph import resolve_understanding_path
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
        "periodic_table.element",
        "chemistry.compound",
        "lexicon.term",
        "screen.read_text",
    }
    assert expected.issubset(set(registry.topics()))


def test_periodic_table_topic_computes_a_real_lookup():
    registry = build_default_registry()
    answer = ask(registry, "periodic_table.element", identifier="Au")
    assert answer.status == TopicStatus.VERIFIED
    assert answer.result["name"] == "Gold"


def test_chemistry_compound_topic_returns_transcribed_data():
    registry = build_default_registry()
    answer = ask(registry, "chemistry.compound", name="water")
    assert answer.result["formula"] == "H2O"


def test_lexicon_topic_returns_glossary_entry():
    registry = build_default_registry()
    answer = ask(registry, "lexicon.term", term="Lexicon Agent")
    assert answer.result["node_code"] == "N-L1-006"


def test_compound_topic_declares_a_real_prerequisite_on_periodic_table():
    registry = build_default_registry()
    path = resolve_understanding_path(registry, "chemistry.compound")
    assert path == ["periodic_table.element", "chemistry.compound"]


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


def test_screen_read_text_topic_extracts_real_text(tmp_path):
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (400, 80), color="white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    draw.text((10, 20), "Topic Test", fill="black", font=font)
    path = tmp_path / "topic_test.png"
    image.save(path)

    registry = build_default_registry()
    answer = ask(registry, "screen.read_text", image_path=str(path))
    assert answer.status == TopicStatus.VERIFIED
    assert "Topic" in answer.result["text"]
