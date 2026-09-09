import pytest

from il_llm import ledger, paths, validate


@pytest.fixture
def isolated_ledgers(tmp_path, monkeypatch):
    """Redirect all ledger/data paths into a tmp dir so tests never touch
    the real repo-root data/ directory the ported CLI defaults to."""
    data_dir = tmp_path / "data"
    mapping = {
        "DATA_DIR": data_dir,
        "SOURCES_DIR": data_dir / "sources",
        "LEDGERS_DIR": data_dir / "ledgers",
        "REPORTS_DIR": data_dir / "reports",
        "TRACES_DIR": data_dir / "traces",
        "CLAIMS_PATH": data_dir / "ledgers" / "claims.json",
        "OPERATORS_PATH": data_dir / "ledgers" / "operators.json",
        "EVIDENCE_PATH": data_dir / "ledgers" / "evidence.json",
        "CONTRADICTIONS_PATH": data_dir / "ledgers" / "contradictions.json",
        "RUNTIME_EVENTS_PATH": data_dir / "ledgers" / "runtime_events.json",
        "DIGITAL_TRACE_PATH": data_dir / "ledgers" / "digital_trace.json",
        "SOURCE_MANIFEST_PATH": data_dir / "source_manifest.json",
    }
    for name, value in mapping.items():
        monkeypatch.setattr(paths, name, value)

    monkeypatch.setattr(ledger, "RUNTIME_EVENTS_PATH", mapping["RUNTIME_EVENTS_PATH"])
    monkeypatch.setattr(ledger, "DIGITAL_TRACE_PATH", mapping["DIGITAL_TRACE_PATH"])
    monkeypatch.setattr(ledger, "EMPTY_LEDGERS", {
        mapping["CLAIMS_PATH"]: [], mapping["OPERATORS_PATH"]: [], mapping["EVIDENCE_PATH"]: [],
        mapping["CONTRADICTIONS_PATH"]: [], mapping["RUNTIME_EVENTS_PATH"]: [],
        mapping["DIGITAL_TRACE_PATH"]: [],
    })

    # validate.py does `from .paths import X` directly, so it holds its
    # own module-level binding of each name -- patching `paths.X` alone
    # does not reach it. Same reasoning as patching `ledger` above.
    for name in ("CLAIMS_PATH", "DIGITAL_TRACE_PATH", "OPERATORS_PATH",
                 "RUNTIME_EVENTS_PATH", "SOURCE_MANIFEST_PATH"):
        monkeypatch.setattr(validate, name, mapping[name])

    return data_dir
