import pytest

from workspace_control_plane.actuators.directory import InMemoryDirectoryAdapter
from workspace_control_plane.models import CanonicalUser


def test_create_then_get_round_trips():
    adapter = InMemoryDirectoryAdapter()
    user = CanonicalUser(primary_email="new@example.com", given_name="New")

    adapter.create(user)

    assert adapter.get("new@example.com").given_name == "New"


def test_create_duplicate_user_raises():
    adapter = InMemoryDirectoryAdapter()
    adapter.seed(CanonicalUser(primary_email="dup@example.com"))

    with pytest.raises(ValueError):
        adapter.create(CanonicalUser(primary_email="dup@example.com"))


def test_update_unknown_user_raises():
    adapter = InMemoryDirectoryAdapter()

    with pytest.raises(KeyError):
        adapter.update("ghost@example.com", {"given_name": "X"})


def test_suspend_user_sets_state_and_flag():
    adapter = InMemoryDirectoryAdapter()
    adapter.seed(CanonicalUser(primary_email="s@example.com"))

    result = adapter.suspend("s@example.com")

    assert result.suspended is True
    assert result.state.value == "suspended"


def test_delete_user_removes_it():
    adapter = InMemoryDirectoryAdapter()
    adapter.seed(CanonicalUser(primary_email="d@example.com"))

    adapter.delete("d@example.com")

    assert adapter.get("d@example.com") is None


def test_get_user_returns_a_copy_not_internal_state():
    adapter = InMemoryDirectoryAdapter()
    adapter.seed(CanonicalUser(primary_email="c@example.com", given_name="Orig"))

    snapshot = adapter.get("c@example.com")
    snapshot.given_name = "Mutated"

    assert adapter.get("c@example.com").given_name == "Orig"


def test_create_returns_a_copy_not_internal_state():
    adapter = InMemoryDirectoryAdapter()
    created = adapter.create(CanonicalUser(primary_email="e@example.com", given_name="Orig"))

    created.given_name = "Mutated"

    assert adapter.get("e@example.com").given_name == "Orig"
