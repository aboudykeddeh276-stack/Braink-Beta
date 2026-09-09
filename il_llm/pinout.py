# ENGINEERED INIT (A.keddeh, K-SYSTEMS):
# - discover repo root from current working directory
# - scour IL-LLM pin surface before other actions
# - execute only via named/resolved blocks (smart_manager) when applicable
# Source: /Users/ak/Documents/ENGINEERING BY DESIGN/PINNED.md

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .paths import (
    CLAIMS_PATH,
    DIGITAL_TRACE_PATH,
    OPERATORS_PATH,
    PINOUT_PATH,
    ROOT,
    RUNTIME_EVENTS_PATH,
    SOURCE_MANIFEST_PATH,
    ensure_data_dirs,
    project_relative,
)


@dataclass(frozen=True)
class Pin:
    pin_id: str
    pin_type: str
    terminus: str
    role: str
    allowed_actions: list[str]
    constraints: list[str]
    falsifier: str
    proof: list[str]
    edges: list[str]


def _required_pins() -> list[Pin]:
    return [
        Pin(
            pin_id="ENTRYPOINT.il_llm.cli.main",
            pin_type="ENTRYPOINT_PIN",
            terminus=project_relative(ROOT / "il_llm" / "cli.py") + ":main",
            role="entrypoint",
            allowed_actions=["execute"],
            constraints=["one_path", "deterministic_output"],
            falsifier="Import il_llm.cli:main fails or returns non-zero for status/validate.",
            proof=[
                "python3 -c \"from il_llm.cli import main; raise SystemExit(main(['status']))\"",
                "python3 -c \"from il_llm.cli import main; raise SystemExit(main(['validate']))\"",
            ],
            edges=[
                "LEDGER.data/source_manifest.json",
                "LEDGER.data/ledgers/*.json",
                "REPORT.data/reports/ledger_report.md",
            ],
        ),
        Pin(
            pin_id="LEDGER.source_manifest",
            pin_type="FILE_PIN",
            terminus=project_relative(SOURCE_MANIFEST_PATH),
            role="ledger",
            allowed_actions=["read", "write"],
            constraints=["json", "append_only_semantics"],
            falsifier="File missing or empty after ingest.",
            proof=["il-llm ingest <path> (via il_llm.cli ingest)"],
            edges=["LEDGER.claims", "LEDGER.operators"],
        ),
        Pin(
            pin_id="LEDGER.claims",
            pin_type="FILE_PIN",
            terminus=project_relative(CLAIMS_PATH),
            role="ledger",
            allowed_actions=["read", "write"],
            constraints=["json", "schema=schemas/claim.schema.json"],
            falsifier="validate fails or schema drift not enforced.",
            proof=["il-llm extract-claims", "il-llm validate"],
            edges=["LEDGER.operators"],
        ),
        Pin(
            pin_id="LEDGER.operators",
            pin_type="FILE_PIN",
            terminus=project_relative(OPERATORS_PATH),
            role="ledger",
            allowed_actions=["read", "write"],
            constraints=["json", "schema=schemas/operator.schema.json"],
            falsifier="validate fails required operator fields.",
            proof=["il-llm map-operators", "il-llm validate"],
            edges=[],
        ),
        Pin(
            pin_id="LEDGER.digital_trace",
            pin_type="FILE_PIN",
            terminus=project_relative(DIGITAL_TRACE_PATH),
            role="ledger",
            allowed_actions=["read", "write"],
            constraints=["json", "result present requires evidence_pointer"],
            falsifier="validate fails digital trace invariants.",
            proof=["il-llm digital-trace ...", "il-llm validate"],
            edges=[],
        ),
        Pin(
            pin_id="LEDGER.runtime_events",
            pin_type="FILE_PIN",
            terminus=project_relative(RUNTIME_EVENTS_PATH),
            role="ledger",
            allowed_actions=["read", "write"],
            constraints=["json"],
            falsifier="runtime-event command fails or records invalid shape.",
            proof=["il-llm runtime-event ...", "il-llm validate"],
            edges=[],
        ),
        Pin(
            pin_id="TRACE.pinout.file_surface",
            pin_type="ARTIFACT_PIN",
            terminus=project_relative(PINOUT_PATH),
            role="substrate",
            allowed_actions=["read", "write"],
            constraints=["json", "must_include_required_pins"],
            falsifier="Pinout missing or missing required pins.",
            proof=["il-llm pinout"],
            edges=[],
        ),
    ]


def generate_pinout() -> dict[str, object]:
    ensure_data_dirs()
    pinout_dir = PINOUT_PATH.parent
    pinout_dir.mkdir(parents=True, exist_ok=True)

    pins = _required_pins()
    data = {
        "id": "file_surface_pinout_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "pins": [asdict(pin) for pin in pins],
        "required_pin_ids": [pin.pin_id for pin in pins],
    }
    return data


def write_pinout() -> Path:
    from .io import write_json

    data = generate_pinout()
    write_json(PINOUT_PATH, data)
    return PINOUT_PATH

