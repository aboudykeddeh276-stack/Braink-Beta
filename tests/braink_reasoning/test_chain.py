import pytest

from braink_reasoning.chain import Chain, ChainStep, verify_receipt_chain


def _double(x: dict) -> dict:
    return {**x, "n": x.get("n", 1) * 2}


def _increment(x: dict) -> dict:
    return {**x, "n": x.get("n", 1) + 1}


def test_chain_requires_at_least_one_step():
    with pytest.raises(ValueError):
        Chain(chain_id="empty", steps=[])


def test_execute_runs_steps_in_order():
    chain = Chain("c1", [ChainStep("double", _double), ChainStep("increment", _increment)])
    result = chain.execute({"n": 3})
    assert result.final_output == {"n": 7}  # (3*2)+1


def test_execute_produces_one_receipt_per_step():
    chain = Chain("c1", [ChainStep("double", _double), ChainStep("increment", _increment)])
    result = chain.execute({"n": 1})
    assert len(result.receipts) == 2
    assert [r.step_name for r in result.receipts] == ["double", "increment"]


def test_receipts_are_hash_chained():
    chain = Chain("c1", [ChainStep("double", _double), ChainStep("increment", _increment)])
    result = chain.execute({"n": 1})
    assert result.receipts[0].previous_receipt_hash is None
    assert result.receipts[1].previous_receipt_hash == result.receipts[0].receipt_hash


def test_verify_receipt_chain_accepts_untampered_receipts():
    chain = Chain("c1", [ChainStep("double", _double), ChainStep("increment", _increment)])
    result = chain.execute({"n": 1})
    assert verify_receipt_chain(result.receipts) is True


def test_verify_receipt_chain_detects_tampering_with_a_middle_receipt():
    import dataclasses

    # Tampering with the LAST receipt in a chain is the documented,
    # unavoidable blind spot of backward-linking hashes (nothing points
    # forward to it -- same limitation as workspace_control_plane's
    # verify_chain). Tampering with a MIDDLE receipt is the case that
    # must be caught: the receipt after it still points at the
    # original, now-mismatched hash.
    chain = Chain(
        "c1",
        [ChainStep("double", _double), ChainStep("increment", _increment), ChainStep("double2", _double)],
    )
    result = chain.execute({"n": 1})
    tampered = (
        result.receipts[0],
        dataclasses.replace(result.receipts[1], input_hash="sha256:fake"),
        result.receipts[2],
    )
    assert verify_receipt_chain(tampered) is False


def test_verify_receipt_chain_cannot_detect_tampering_with_only_the_last_receipt():
    # Documents the real, honest limit: nothing in the chain points
    # forward to the last receipt, so altering only it is invisible to
    # this check -- same limitation as workspace_control_plane's
    # verify_chain, and for the same structural reason.
    import dataclasses

    chain = Chain("c1", [ChainStep("double", _double), ChainStep("increment", _increment)])
    result = chain.execute({"n": 1})
    tampered = (result.receipts[0], dataclasses.replace(result.receipts[1], input_hash="sha256:fake"))
    assert verify_receipt_chain(tampered) is True


def test_addresses_are_unique_for_distinct_step_names():
    chain = Chain("c1", [ChainStep("double", _double), ChainStep("increment", _increment)])
    result = chain.execute({"n": 1})
    assert result.rehydration_summary()["unique_addresses"] is True


def test_addresses_collide_for_repeated_step_names_and_this_is_detected():
    # A malformed chain reusing the same step name twice binds two
    # executions to the same address -- unique_addresses must catch this.
    chain = Chain("c1", [ChainStep("double", _double), ChainStep("double", _increment)])
    result = chain.execute({"n": 1})
    assert result.rehydration_summary()["unique_addresses"] is False


def test_address_is_stable_across_separate_executions_of_the_same_chain():
    chain = Chain("c1", [ChainStep("double", _double)])
    r1 = chain.execute({"n": 1}).receipts[0].address
    r2 = chain.execute({"n": 5}).receipts[0].address
    assert r1 == r2  # same chain_id + step name -> same address, regardless of input


def test_address_differs_across_chains_with_different_chain_id():
    chain_a = Chain("chain-a", [ChainStep("double", _double)])
    chain_b = Chain("chain-b", [ChainStep("double", _double)])
    assert chain_a.execute({"n": 1}).receipts[0].address != chain_b.execute({"n": 1}).receipts[0].address


def test_proxy_steps_reports_only_marked_steps():
    chain = Chain(
        "c1",
        [
            ChainStep("double", _double),
            ChainStep("increment", _increment, is_proxy=True, proxy_note="not real"),
        ],
    )
    assert chain.proxy_steps() == ["increment"]


def test_rehydration_round_trip_reproduces_identical_receipts():
    original = Chain("rehydrate-test", [ChainStep("double", _double), ChainStep("increment", _increment)])
    original_result = original.execute({"n": 1})

    # Simulate "a separate process": only the definition (no function
    # objects) crosses the boundary, plus a registry to look functions
    # back up by name.
    definition = original.to_definition()
    registry = {"double": _double, "increment": _increment}
    rehydrated = Chain.from_definition(definition, registry)
    rehydrated_result = rehydrated.execute({"n": 1})

    assert [r.receipt_hash for r in rehydrated_result.receipts] == [
        r.receipt_hash for r in original_result.receipts
    ]
