import pytest

from workspace_control_plane.actuators.licensing import InMemoryLicensingAdapter
from workspace_control_plane.models import CanonicalLicenseAssignment


def test_create_then_get_round_trips():
    adapter = InMemoryLicensingAdapter()
    assignment = CanonicalLicenseAssignment(user_email="new@example.com", assigned_skus=["sku-a"])

    adapter.create(assignment)

    assert adapter.get("new@example.com").assigned_skus == ["sku-a"]


def test_create_duplicate_raises():
    adapter = InMemoryLicensingAdapter()
    adapter.seed(CanonicalLicenseAssignment(user_email="dup@example.com"))

    with pytest.raises(ValueError):
        adapter.create(CanonicalLicenseAssignment(user_email="dup@example.com"))


def test_update_unknown_raises():
    adapter = InMemoryLicensingAdapter()

    with pytest.raises(KeyError):
        adapter.update("ghost@example.com", {"assigned_skus": ["sku-a"]})


def test_update_adds_a_sku():
    adapter = InMemoryLicensingAdapter()
    adapter.seed(CanonicalLicenseAssignment(user_email="u@example.com", assigned_skus=["sku-a"]))

    result = adapter.update("u@example.com", {"assigned_skus": ["sku-a", "sku-b"]})

    assert result.assigned_skus == ["sku-a", "sku-b"]


def test_delete_removes_assignment():
    adapter = InMemoryLicensingAdapter()
    adapter.seed(CanonicalLicenseAssignment(user_email="d@example.com"))

    adapter.delete("d@example.com")

    assert adapter.get("d@example.com") is None


def test_get_returns_a_copy_not_internal_state():
    adapter = InMemoryLicensingAdapter()
    adapter.seed(CanonicalLicenseAssignment(user_email="c@example.com", assigned_skus=["sku-a"]))

    snapshot = adapter.get("c@example.com")
    snapshot.assigned_skus.append("sku-b")

    assert adapter.get("c@example.com").assigned_skus == ["sku-a"]
