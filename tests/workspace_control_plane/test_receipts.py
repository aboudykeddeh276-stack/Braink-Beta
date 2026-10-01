from workspace_control_plane.models import CanonicalUser
from workspace_control_plane.receipts import Receipt, hash_state


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
    )

    payload = receipt.to_dict()

    assert payload["capability"] == "identity.user.update"
    assert payload["scopes_used"] == ["scope-a"]
    assert payload["converged"] is True
