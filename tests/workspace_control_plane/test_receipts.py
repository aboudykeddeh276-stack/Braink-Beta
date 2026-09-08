import dataclasses

from workspace_control_plane.models import CanonicalUser
from workspace_control_plane.receipts import Receipt, ReceiptChain, hash_state, verify_chain


def test_hash_state_is_deterministic():
    user = CanonicalUser(primary_email="a@example.com", given_name="A")

    assert hash_state(user) == hash_state(user.model_copy(deep=True))


def test_hash_state_changes_with_content():
    a = CanonicalUser(primary_email="a@example.com", given_name="A")
    b = a.model_copy(update={"given_name": "B"})

    assert hash_state(a) != hash_state(b)


def test_hash_state_of_none_is_stable():
    assert hash_state(None) == hash_state(None)


def test_receipt_to_dict_round_trips_fields():
    receipt = Receipt(
        capability="identity.user.update",
        actor="admin@example.com",
        delegated_identity="admin@example.com",
        scopes_used=("scope-a",),
        resource_id="a@example.com",
        before_state_hash="sha256:before",
        after_state_hash="sha256:after",
        converged=True,
        actuator_kind="simulated",
        previous_receipt_hash=None,
    )

    payload = receipt.to_dict()

    assert payload["capability"] == "identity.user.update"
    assert payload["scopes_used"] == ["scope-a"]
    assert payload["converged"] is True
    assert payload["actuator_kind"] == "simulated"
    assert payload["previous_receipt_hash"] is None


def _make_receipt(previous_receipt_hash, resource_id="a@example.com"):
    return Receipt(
        capability="identity.user.update",
        actor="admin@example.com",
        delegated_identity="admin@example.com",
        scopes_used=("scope-a",),
        resource_id=resource_id,
        before_state_hash="sha256:before",
        after_state_hash="sha256:after",
        converged=True,
        actuator_kind="simulated",
        previous_receipt_hash=previous_receipt_hash,
    )


def test_receipt_chain_links_consecutive_receipts():
    chain = ReceiptChain()

    r1 = chain.record(_make_receipt(chain.next_previous_hash()))
    r2 = chain.record(_make_receipt(chain.next_previous_hash()))

    assert r1.previous_receipt_hash is None
    assert r2.previous_receipt_hash == r1.receipt_hash


def test_receipt_hash_depends_on_full_content_not_just_identity():
    a = _make_receipt(None, resource_id="a@example.com")
    b = _make_receipt(None, resource_id="b@example.com")

    assert a.receipt_hash != b.receipt_hash


def test_receipt_hash_is_a_pure_function_of_stored_fields():
    """No hidden randomness (a UUID, a fresh timestamp) may leak into the hash —
    it must be independently reproducible from the receipt's own recorded fields,
    or it can't be used to verify anything after the fact."""
    kwargs = dict(
        capability="identity.user.update",
        actor="admin@example.com",
        delegated_identity="admin@example.com",
        scopes_used=("scope-a",),
        resource_id="a@example.com",
        before_state_hash="sha256:before",
        after_state_hash="sha256:after",
        converged=True,
        actuator_kind="simulated",
        previous_receipt_hash=None,
        issued_at="2026-01-01T00:00:00+00:00",
    )

    assert Receipt(**kwargs).receipt_hash == Receipt(**kwargs).receipt_hash


def _build_chain(n: int) -> list[Receipt]:
    chain = ReceiptChain()
    return [chain.record(_make_receipt(chain.next_previous_hash())) for _ in range(n)]


def test_verify_chain_accepts_an_untampered_sequence():
    result = verify_chain(_build_chain(4))

    assert result.valid is True


def test_verify_chain_accepts_empty_sequence():
    assert verify_chain([]).valid is True


def test_verify_chain_detects_a_receipt_deleted_from_the_middle():
    receipts = _build_chain(4)
    tampered = [receipts[0], receipts[2], receipts[3]]  # receipts[1] removed

    result = verify_chain(tampered)

    assert result.valid is False
    assert result.broken_at_index == 1


def test_verify_chain_detects_content_altered_after_the_fact():
    receipts = _build_chain(3)
    # An attacker edits receipt[1]'s content but doesn't (can't, without
    # recomputing everything downstream) fix up receipt[2]'s reference to it.
    altered_middle = dataclasses.replace(receipts[1], resource_id="attacker@example.com")
    tampered = [receipts[0], altered_middle, receipts[2]]

    result = verify_chain(tampered)

    assert result.valid is False
    assert result.broken_at_index == 2


def test_verify_chain_cannot_detect_tampering_with_only_the_last_receipt():
    """Documents the real, honest limit of a backward-linking chain: nothing
    points forward to the tip, so altering (or dropping) only the last entry
    is invisible to this check. This is why the tip needs an external anchor
    if it also needs tamper-evidence — verify_chain alone cannot provide it."""
    receipts = _build_chain(3)
    altered_last = dataclasses.replace(receipts[-1], resource_id="attacker@example.com")
    tampered = [receipts[0], receipts[1], altered_last]

    result = verify_chain(tampered)

    assert result.valid is True
