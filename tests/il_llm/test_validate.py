from il_llm import ledger, paths
from il_llm.io import read_json, write_json
from il_llm.validate import validate_ledgers


def test_validate_passes_on_untampered_ledgers(isolated_ledgers):
    ledger.add_runtime_event(
        observed_change="x", user_report="y", impact="z",
        affected_process="p", mitigation="m", unresolved_risk="r",
    )
    write_json(paths.SOURCE_MANIFEST_PATH, [{"source": "placeholder"}])
    errors = validate_ledgers()
    assert not any("hash chain" in e for e in errors)


def test_validate_reports_a_broken_hash_chain(isolated_ledgers):
    ledger.add_runtime_event(
        observed_change="x", user_report="y", impact="z",
        affected_process="p", mitigation="m", unresolved_risk="r",
    )
    ledger.add_runtime_event(
        observed_change="x2", user_report="y2", impact="z2",
        affected_process="p2", mitigation="m2", unresolved_risk="r2",
    )
    write_json(paths.SOURCE_MANIFEST_PATH, [{"source": "placeholder"}])

    records = read_json(paths.RUNTIME_EVENTS_PATH, [])
    records[0]["observed_change"] = "tampered"  # stale record_hash now
    write_json(paths.RUNTIME_EVENTS_PATH, records)

    errors = validate_ledgers()
    assert any("runtime_events.json" in e and "hash chain" in e for e in errors)


def test_validate_is_post_hoc_not_a_write_time_gate(isolated_ledgers):
    # The tampered write above succeeds regardless of validate() -- this
    # documents, rather than hides, that validate_ledgers() only reports
    # problems after the fact. It does not intercept the write in
    # test_validate_reports_a_broken_hash_chain; that write already
    # landed on disk before validate_ledgers() was ever called.
    ledger.add_runtime_event(
        observed_change="x", user_report="y", impact="z",
        affected_process="p", mitigation="m", unresolved_risk="r",
    )
    records = read_json(paths.RUNTIME_EVENTS_PATH, [])
    records[0]["observed_change"] = "tampered"
    write_json(paths.RUNTIME_EVENTS_PATH, records)  # nothing prevents this write
    assert read_json(paths.RUNTIME_EVENTS_PATH, [])[0]["observed_change"] == "tampered"
