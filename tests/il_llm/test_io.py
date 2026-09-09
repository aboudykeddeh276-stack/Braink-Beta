import pytest

from il_llm.io import append_record, read_json, verify_ledger_chain, write_json


def test_append_record_chains_previous_record_hash(tmp_path):
    path = tmp_path / "ledger.json"
    append_record(path, {"id": "a"})
    append_record(path, {"id": "b"})
    records = read_json(path, [])

    assert records[0]["previous_record_hash"] is None
    assert records[1]["previous_record_hash"] == records[0]["record_hash"]


def test_verify_ledger_chain_accepts_untampered_records(tmp_path):
    path = tmp_path / "ledger.json"
    for i in range(4):
        append_record(path, {"id": str(i)})

    valid, reason = verify_ledger_chain(path)
    assert valid is True
    assert reason == ""


def test_verify_ledger_chain_accepts_empty_ledger(tmp_path):
    path = tmp_path / "ledger.json"
    assert verify_ledger_chain(path) == (True, "")


def test_verify_ledger_chain_detects_a_record_deleted_from_the_middle(tmp_path):
    path = tmp_path / "ledger.json"
    for i in range(4):
        append_record(path, {"id": str(i)})
    records = read_json(path, [])
    tampered = [records[0], records[2], records[3]]  # records[1] removed
    write_json(path, tampered)

    valid, reason = verify_ledger_chain(path)
    assert valid is False
    assert "record 1" in reason


def test_verify_ledger_chain_detects_content_edited_in_place(tmp_path):
    path = tmp_path / "ledger.json"
    for i in range(3):
        append_record(path, {"id": str(i)})
    records = read_json(path, [])
    records[1]["id"] = "tampered"  # content changed, record_hash left stale
    write_json(path, records)

    valid, reason = verify_ledger_chain(path)
    assert valid is False


def test_verify_ledger_chain_cannot_detect_tampering_with_only_the_last_record(tmp_path):
    # Documented, honest limit: nothing points forward to the last
    # record, so editing only it (and leaving its own record_hash
    # recomputed to match) is invisible to this check -- same limit as
    # workspace_control_plane.receipts.verify_chain and
    # braink_reasoning.chain.verify_receipt_chain.
    from il_llm.io import _hash

    path = tmp_path / "ledger.json"
    for i in range(3):
        append_record(path, {"id": str(i)})
    records = read_json(path, [])
    records[-1]["id"] = "tampered"
    records[-1]["record_hash"] = _hash(
        {k: v for k, v in records[-1].items() if k != "record_hash"}
    )
    write_json(path, records)

    valid, _ = verify_ledger_chain(path)
    assert valid is True
