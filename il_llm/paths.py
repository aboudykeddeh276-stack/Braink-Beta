from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SOURCES_DIR = DATA_DIR / "sources"
LEDGERS_DIR = DATA_DIR / "ledgers"
REPORTS_DIR = DATA_DIR / "reports"
TRACES_DIR = DATA_DIR / "traces"

CLAIMS_PATH = LEDGERS_DIR / "claims.json"
OPERATORS_PATH = LEDGERS_DIR / "operators.json"
EVIDENCE_PATH = LEDGERS_DIR / "evidence.json"
CONTRADICTIONS_PATH = LEDGERS_DIR / "contradictions.json"
RUNTIME_EVENTS_PATH = LEDGERS_DIR / "runtime_events.json"
DIGITAL_TRACE_PATH = LEDGERS_DIR / "digital_trace.json"
SOURCE_MANIFEST_PATH = DATA_DIR / "source_manifest.json"
PINOUT_PATH = TRACES_DIR / "pinout" / "file_surface_pinout.json"


def ensure_data_dirs() -> None:
    for path in [DATA_DIR, SOURCES_DIR, LEDGERS_DIR, REPORTS_DIR, TRACES_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def project_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)
