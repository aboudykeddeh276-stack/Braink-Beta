# ENGINEERED INIT (A.keddeh, K-SYSTEMS):
# - discover repo root from current working directory
# - scour IL-LLM pin surface before other actions
# - execute only via named/resolved blocks (smart_manager) when applicable
# Source: /Users/ak/Documents/ENGINEERING BY DESIGN/PINNED.md

from __future__ import annotations

from pathlib import Path

from .io import read_json
from .paths import PINOUT_PATH, ROOT


def substrate_check() -> dict[str, object]:
    """Calculator-like substrate check.

    Returns a structured result. Caller decides whether to print.
    """
    pinout = read_json(PINOUT_PATH, {})
    if not isinstance(pinout, dict):
        return {"ok": False, "error": "pinout unreadable", "missing": []}

    pins = pinout.get("pins", [])
    if not isinstance(pins, list) or not pins:
        return {"ok": False, "error": "pinout pins missing", "missing": []}

    missing: list[str] = []
    for pin in pins:
        if not isinstance(pin, dict):
            continue
        pin_type = str(pin.get("pin_type") or "")
        terminus = str(pin.get("terminus") or "")
        pin_id = str(pin.get("pin_id") or "")
        if not terminus or not pin_id:
            continue
        if pin_type in {"FILE_PIN", "ARTIFACT_PIN"}:
            path = Path(terminus)
            if not path.is_absolute():
                path = ROOT / path
            if not path.exists():
                missing.append(f"{pin_id}:{terminus}")

    return {"ok": not missing, "missing": missing}

