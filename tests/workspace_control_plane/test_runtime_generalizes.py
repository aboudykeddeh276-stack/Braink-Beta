"""Proves ControlPlaneRuntime is genuinely generic, not fit to one adapter.

Every test here runs the exact same ControlPlaneRuntime class already
exercised against CanonicalUser/InMemoryDirectoryAdapter in
test_runtime.py, but against CanonicalLicenseAssignment/
InMemoryLicensingAdapter instead — a different canonical model, a
different actuator, a different real Google API surface (Enterprise
License Manager, not the Admin SDK Directory API). No changes to
runtime.py, verification.py, candidate.py, or receipts.py were made to
support this; if any of those files secretly assumed "user" or
"Directory", these tests would fail.
"""

import pytest

from workspace_control_plane.actuators.licensing import InMemoryLicensingAdapter
from workspace_control_plane.admission import Actor
from workspace_control_plane.capability_registry import build_default_registry
from workspace_control_plane.exceptions import ApprovalRequiredError
from workspace_control_plane.models import CanonicalLicenseAssignment
from workspace_control_plane.runtime import ControlPlaneRuntime, MutationIntent

LICENSING_SCOPE = "https://www.googleapis.com/auth/apps.licensing"


def _runtime_with_assignment(
    email: str = "user@example.com",
) -> tuple[ControlPlaneRuntime, InMemoryLicensingAdapter]:
    licensing = InMemoryLicensingAdapter()
    licensing.seed(CanonicalLicenseAssignment(user_email=email, assigned_skus=["sku-basic"]))
    runtime = ControlPlaneRuntime(build_default_registry(), licensing)
    return runtime, licensing


def _admin_actor() -> Actor:
    return Actor(
        email="admin@example.com",
        granted_scopes=frozenset({LICENSING_SCOPE}),
        is_delegated_admin=True,
    )


def test_assigning_a_sku_through_the_generic_runtime():
    runtime, licensing = _runtime_with_assignment()
    intent = MutationIntent(
        capability="licensing.assign",
        resource_id="user@example.com",
        desired_changes={"assigned_skus": ["sku-basic", "sku-premium"]},
    )

    receipt = runtime.execute_mutation(intent, _admin_actor(), approval_granted=True)

    assert receipt.converged is True
    assert receipt.actuator_kind == "simulated"
    assert licensing.get("user@example.com").assigned_skus == ["sku-basic", "sku-premium"]


def test_sku_assignment_without_approval_is_blocked():
    runtime, licensing = _runtime_with_assignment()
    intent = MutationIntent(
        capability="licensing.assign",
        resource_id="user@example.com",
        desired_changes={"assigned_skus": ["sku-basic", "sku-premium"]},
    )

    with pytest.raises(ApprovalRequiredError):
        runtime.execute_mutation(intent, _admin_actor(), approval_granted=False)

    assert licensing.get("user@example.com").assigned_skus == ["sku-basic"]


def test_revoking_a_sku_verifies_it_is_actually_gone():
    runtime, licensing = _runtime_with_assignment()
    intent = MutationIntent(
        capability="licensing.revoke",
        resource_id="user@example.com",
        desired_changes={"assigned_skus": []},
    )

    receipt = runtime.execute_mutation(intent, _admin_actor(), approval_granted=True)

    assert receipt.converged is True
    assert licensing.get("user@example.com").assigned_skus == []


def test_receipts_from_two_different_adapters_share_one_chain():
    """A single ReceiptChain can span multiple resource types/adapters,
    since chaining only depends on Receipt's own hash, not on what kind
    of resource produced it."""
    from workspace_control_plane.actuators.directory import InMemoryDirectoryAdapter
    from workspace_control_plane.models import CanonicalUser
    from workspace_control_plane.receipts import ReceiptChain, verify_chain

    chain = ReceiptChain()
    directory = InMemoryDirectoryAdapter()
    directory.seed(CanonicalUser(primary_email="user@example.com", given_name="Original"))
    licensing = InMemoryLicensingAdapter()
    licensing.seed(CanonicalLicenseAssignment(user_email="user@example.com", assigned_skus=[]))

    directory_runtime = ControlPlaneRuntime(
        build_default_registry(), directory, receipt_chain=chain
    )
    licensing_runtime = ControlPlaneRuntime(
        build_default_registry(), licensing, receipt_chain=chain
    )

    directory_actor = Actor(
        email="admin@example.com",
        granted_scopes=frozenset({"https://www.googleapis.com/auth/admin.directory.user"}),
        is_delegated_admin=True,
    )

    r1 = directory_runtime.execute_mutation(
        MutationIntent("identity.user.update", "user@example.com", {"given_name": "Updated"}),
        directory_actor,
    )
    r2 = licensing_runtime.execute_mutation(
        MutationIntent("licensing.assign", "user@example.com", {"assigned_skus": ["sku-basic"]}),
        _admin_actor(),
        approval_granted=True,
    )

    assert r2.previous_receipt_hash == r1.receipt_hash
    assert verify_chain([r1, r2]).valid is True
