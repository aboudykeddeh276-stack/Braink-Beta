import pytest
from PIL import Image, ImageDraw, ImageFont

from braink_reasoning.registers.screen_reader import read_text_from_image

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _render_text_image(tmp_path, text: str, filename: str = "rendered.png"):
    image = Image.new("RGB", (600, 100), color="white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_PATH, 32)
    draw.text((10, 25), text, fill="black", font=font)
    path = tmp_path / filename
    image.save(path)
    return path


def test_read_text_from_a_real_rendered_image(tmp_path):
    path = _render_text_image(tmp_path, "Hello Braink")
    result = read_text_from_image(path)

    assert "Hello" in result["text"]
    assert "Braink" in result["text"]
    assert result["word_count"] >= 2


def test_result_includes_real_per_word_confidence(tmp_path):
    path = _render_text_image(tmp_path, "Confidence Test")
    result = read_text_from_image(path)

    assert all(0 <= w["confidence"] <= 100 for w in result["words"])
    assert result["mean_confidence"] > 0


def test_blank_image_yields_no_words(tmp_path):
    image = Image.new("RGB", (200, 100), color="white")
    path = tmp_path / "blank.png"
    image.save(path)

    result = read_text_from_image(path)

    assert result["text"] == ""
    assert result["word_count"] == 0
    assert result["mean_confidence"] == 0.0


def test_extracted_text_changes_with_different_input(tmp_path):
    path_a = _render_text_image(tmp_path, "Alpha", "a.png")
    path_b = _render_text_image(tmp_path, "Zebra", "b.png")

    result_a = read_text_from_image(path_a)
    result_b = read_text_from_image(path_b)

    assert "Alpha" in result_a["text"]
    assert "Zebra" in result_b["text"]
    assert result_a["text"] != result_b["text"]
