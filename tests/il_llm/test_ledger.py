import pytest

from il_llm import ledger, paths
from il_llm.io import verify_ledger_chain


def test_add_runtime_event_produces_a_chained_record(isolated_ledgers):
    ledger.add_runtime_event(
        observed_change="x", user_report="y", impact="z",
        affected_process="p", mitigation="m", unresolved_risk="r",
    )
    record = ledger.add_runtime_event(
        observed_change="x2", user_report="y2", impact="z2",
        affected_process="p2", mitigation="m2", unresolved_risk="r2",
    )
    assert record["previous_record_hash"] is not None
    valid, _ = verify_ledger_chain(paths.RUNTIME_EVENTS_PATH)
    assert valid is True


def test_add_digital_trace_event_rejects_invalid_result(isolated_ledgers):
    with pytest.raises(ValueError):
        ledger.add_digital_trace_event(
            artifact="a", trace_marker="t", target_surface="s",
            inspection_method="m", result="not-a-real-status",
        )
