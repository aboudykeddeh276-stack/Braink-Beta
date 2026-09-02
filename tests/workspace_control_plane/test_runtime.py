import pytest

from workspace_control_plane.actuators.directory import InMemoryDirectoryAdapter
from workspace_control_plane.admission import Actor
from workspace_control_plane.capability_registry import build_default_registry
from workspace_control_plane.exceptions import ApprovalRequiredError, UnsupportedCapabilityError
from workspace_control_plane.models import CanonicalUser
from workspace_control_plane.runtime import ControlPlaneRuntime, UserMutationIntent

USER_SCOPE = "https://www.googleapis.com/auth/admin.directory.user"


def _runtime_with_user(email: str = "user@example.com") -> tuple[ControlPlaneRuntime, InMemoryDirectoryAdapter]:
    directory = InMemoryDirectoryAdapter()
    directory.seed(CanonicalUser(primary_email=email, given_name="Original"))
    runtime = ControlPlaneRuntime(build_default_registry(), directory)
    return runtime, directory


def _admin_actor() -> Actor:
    return Actor(email="admin@example.com", granted_scopes=frozenset({USER_SCOPE}), is_delegated_admin=True)


def test_full_pipeline_updates_and_issues_receipt():
    runtime, directory = _runtime_with_user()
    intent = UserMutationIntent(
        capability="identity.user.update",
        primary_email="user@example.com",
        desired_changes={"given_name": "Updated"},
    )

    receipt = runtime.execute_user_mutation(intent, _admin_actor())

    assert directory.get_user("user@example.com").given_name == "Updated"
    assert receipt.converged is True
    assert receipt.before_state_hash != receipt.after_state_hash
    assert receipt.capability == "identity.user.update"


def test_noop_intent_does_not_call_actuator_and_hashes_match():
    runtime, _ = _runtime_with_user()
    intent = UserMutationIntent(
        capability="identity.user.update",
        primary_email="user@example.com",
        desired_changes={"given_name": "Original"},
    )

    receipt = runtime.execute_user_mutation(intent, _admin_actor())

    assert receipt.before_state_hash == receipt.after_state_hash


def test_destructive_capability_without_approval_blocks_mutation():
    runtime, directory = _runtime_with_user()
    intent = UserMutationIntent(
        capability="identity.user.delete",
        primary_email="user@example.com",
        desired_changes={"suspended": True},
    )

    with pytest.raises(ApprovalRequiredError):
        runtime.execute_user_mutation(intent, _admin_actor(), approval_granted=False)

    assert directory.get_user("user@example.com").suspended is False


def test_destructive_capability_with_approval_proceeds():
    runtime, directory = _runtime_with_user()
    intent = UserMutationIntent(
        capability="identity.user.delete",
        primary_email="user@example.com",
        desired_changes={"suspended": True},
    )

    receipt = runtime.execute_user_mutation(intent, _admin_actor(), approval_granted=True)

    assert receipt.converged is True
    assert directory.get_user("user@example.com").suspended is True


def test_console_only_capability_never_reaches_actuator():
    runtime, directory = _runtime_with_user()
    intent = UserMutationIntent(
        capability="branding.custom_logo",
        primary_email="user@example.com",
        desired_changes={"given_name": "Should Not Apply"},
    )

    with pytest.raises(UnsupportedCapabilityError):
        runtime.execute_user_mutation(intent, _admin_actor())

    assert directory.get_user("user@example.com").given_name == "Original"


def test_mutation_of_unknown_user_raises_before_admission():
    runtime, _ = _runtime_with_user()
    intent = UserMutationIntent(
        capability="identity.user.update",
        primary_email="ghost@example.com",
        desired_changes={"given_name": "X"},
    )

    with pytest.raises(KeyError):
        runtime.execute_user_mutation(intent, _admin_actor())
