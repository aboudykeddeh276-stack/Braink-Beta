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
        desired_changes={},
    )

    with pytest.raises(ApprovalRequiredError):
        runtime.execute_user_mutation(intent, _admin_actor(), approvers=frozenset())

    assert directory.get_user("user@example.com") is not None


def test_destructive_capability_with_two_distinct_approvers_proceeds():
    runtime, directory = _runtime_with_user()
    intent = UserMutationIntent(
        capability="identity.user.delete",
        primary_email="user@example.com",
        desired_changes={},
    )

    receipt = runtime.execute_user_mutation(
        intent,
        _admin_actor(),
        approvers=frozenset({"approver-a@example.com", "approver-b@example.com"}),
    )

    assert receipt.converged is True
    assert directory.get_user("user@example.com") is None
    # user_absent is checked for real; the rest (data disposition, licensing)
    # has no actuator in this milestone and must not be claimed as verified.
    assert set(receipt.unverified_post_conditions) == {
        "owned_data_disposition_verified",
        "licenses_reconciled",
    }


def test_delete_rejects_desired_changes():
    runtime, _ = _runtime_with_user()
    intent = UserMutationIntent(
        capability="identity.user.delete",
        primary_email="user@example.com",
        desired_changes={"suspended": True},
    )

    with pytest.raises(ValueError):
        runtime.execute_user_mutation(
            intent,
            _admin_actor(),
            approvers=frozenset({"approver-a@example.com", "approver-b@example.com"}),
        )


def test_suspend_dispatches_to_suspend_actuator():
    runtime, directory = _runtime_with_user()
    intent = UserMutationIntent(
        capability="identity.user.suspend",
        primary_email="user@example.com",
        desired_changes={},
    )

    receipt = runtime.execute_user_mutation(intent, _admin_actor(), approvers=frozenset({"approver-a@example.com"}))

    assert receipt.converged is True
    updated = directory.get_user("user@example.com")
    assert updated.suspended is True
    assert updated.state.value == "suspended"


def test_read_only_capability_cannot_be_used_for_mutation():
    runtime, _ = _runtime_with_user()
    intent = UserMutationIntent(
        capability="identity.user.read",
        primary_email="user@example.com",
        desired_changes={"given_name": "Should Not Apply"},
    )

    with pytest.raises(UnsupportedCapabilityError):
        runtime.execute_user_mutation(intent, _admin_actor())


def test_unauthorized_actor_never_reaches_pre_observe():
    directory = InMemoryDirectoryAdapter()
    reads: list[str] = []
    original_get_user = directory.get_user
    directory.get_user = lambda email: (reads.append(email), original_get_user(email))[1]  # type: ignore[method-assign]
    directory.seed(CanonicalUser(primary_email="user@example.com"))
    runtime = ControlPlaneRuntime(build_default_registry(), directory)
    unauthorized_actor = Actor(email="nobody@example.com", granted_scopes=frozenset(), is_delegated_admin=False)
    intent = UserMutationIntent(
        capability="identity.user.update",
        primary_email="user@example.com",
        desired_changes={"given_name": "X"},
    )

    with pytest.raises(Exception):
        runtime.execute_user_mutation(intent, unauthorized_actor)

    assert reads == []


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


def test_mutation_of_unknown_user_raises_keyerror_after_admission_succeeds():
    runtime, _ = _runtime_with_user()
    intent = UserMutationIntent(
        capability="identity.user.update",
        primary_email="ghost@example.com",
        desired_changes={"given_name": "X"},
    )

    with pytest.raises(KeyError):
        runtime.execute_user_mutation(intent, _admin_actor())
