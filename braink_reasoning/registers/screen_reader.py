"""Real OCR/CV text extraction from images -- Workplan 02's "real OCR/CV" branch.

Uses Tesseract (via pytesseract), a deterministic computer-vision
library, to extract actual text from an image. This is extraction, not
narration: the output is a discrete, storable value (recognized text
plus Tesseract's own per-word confidence scores), never a language
model describing what it thinks is on screen. Fits the Braink
answer-path constraint in CLAUDE.md the same way every other register
in this package does -- a real function executes and returns its
actual result.

This replaces the "AI Chat Bot" screen-reading mockup noted in
SYSTEM_INVENTORY.md (garbled sample output, no real extraction) with an
actual, tested extraction pipeline.

Requires the Tesseract system binary, not just the Python packages
(`pytesseract` is a wrapper, not an implementation) -- install via
`apt-get install tesseract-ocr` or equivalent on any environment this
runs in.
"""

from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image


def read_text_from_image(image_path: str | Path) -> dict:
    """Extract text from an image file using Tesseract OCR.

    Returns the extracted text plus word-level results with Tesseract's
    own reported confidence per word (0-100, or -1 for non-text
    regions, filtered out here) -- not a fabricated certainty score.
    """
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    words = [
        {"text": word, "confidence": int(conf)}
        for word, conf in zip(data["text"], data["conf"])
        if word.strip() and int(conf) >= 0
    ]

    return {
        "text": text.strip(),
        "words": words,
        "word_count": len(words),
        "mean_confidence": (sum(w["confidence"] for w in words) / len(words)) if words else 0.0,
    }
