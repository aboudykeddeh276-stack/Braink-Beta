import pytest

from workspace_control_plane.actuators.directory import InMemoryDirectoryAdapter
from workspace_control_plane.admission import Actor
from workspace_control_plane.capability_registry import build_default_registry
from workspace_control_plane.exceptions import ApprovalRequiredError, UnsupportedCapabilityError
from workspace_control_plane.models import CanonicalUser
from workspace_control_plane.runtime import ControlPlaneRuntime, MutationIntent

USER_SCOPE = "https://www.googleapis.com/auth/admin.directory.user"


def _runtime_with_user(
    email: str = "user@example.com",
) -> tuple[ControlPlaneRuntime, InMemoryDirectoryAdapter]:
    directory = InMemoryDirectoryAdapter()
    directory.seed(CanonicalUser(primary_email=email, given_name="Original"))
    runtime = ControlPlaneRuntime(build_default_registry(), directory)
    return runtime, directory


def _admin_actor() -> Actor:
    return Actor(
        email="admin@example.com", granted_scopes=frozenset({USER_SCOPE}), is_delegated_admin=True
    )


def test_full_pipeline_updates_and_issues_receipt():
    runtime, directory = _runtime_with_user()
    intent = MutationIntent(
        capability="identity.user.update",
        resource_id="user@example.com",
        desired_changes={"given_name": "Updated"},
    )

    receipt = runtime.execute_mutation(intent, _admin_actor())

    assert directory.get("user@example.com").given_name == "Updated"
    assert receipt.converged is True
    assert receipt.before_state_hash != receipt.after_state_hash
    assert receipt.capability == "identity.user.update"
    assert receipt.actuator_kind == "simulated"


def test_noop_intent_does_not_call_actuator_and_hashes_match():
    runtime, _ = _runtime_with_user()
    intent = MutationIntent(
        capability="identity.user.update",
        resource_id="user@example.com",
        desired_changes={"given_name": "Original"},
    )

    receipt = runtime.execute_mutation(intent, _admin_actor())

    assert receipt.before_state_hash == receipt.after_state_hash


def test_destructive_capability_without_approval_blocks_mutation():
    runtime, directory = _runtime_with_user()
    intent = MutationIntent(
        capability="identity.user.delete",
        resource_id="user@example.com",
        desired_changes={"suspended": True},
    )

    with pytest.raises(ApprovalRequiredError):
        runtime.execute_mutation(intent, _admin_actor(), approval_granted=False)

    # nothing was mutated while approval was outstanding
    assert directory.get("user@example.com").suspended is False


def test_destructive_capability_with_approval_proceeds():
    runtime, directory = _runtime_with_user()
    intent = MutationIntent(
        capability="identity.user.delete",
        resource_id="user@example.com",
        desired_changes={"suspended": True},
    )

    receipt = runtime.execute_mutation(intent, _admin_actor(), approval_granted=True)

    assert receipt.converged is True
    assert directory.get("user@example.com").suspended is True


def test_console_only_capability_never_reaches_actuator():
    runtime, directory = _runtime_with_user()
    intent = MutationIntent(
        capability="branding.custom_logo",
        resource_id="user@example.com",
        desired_changes={"given_name": "Should Not Apply"},
    )

    with pytest.raises(UnsupportedCapabilityError):
        runtime.execute_mutation(intent, _admin_actor())

    assert directory.get("user@example.com").given_name == "Original"


def test_mutation_of_unknown_resource_raises_before_admission():
    runtime, _ = _runtime_with_user()
    intent = MutationIntent(
        capability="identity.user.update",
        resource_id="ghost@example.com",
        desired_changes={"given_name": "X"},
    )

    with pytest.raises(KeyError):
        runtime.execute_mutation(intent, _admin_actor())


def test_actuator_missing_kind_attribute_defaults_to_simulated():
    """An actuator that forgets to declare `kind` must never be trusted as LIVE."""

    class UnlabeledActuator:
        """Delegates to InMemoryDirectoryAdapter but declares no `kind`."""

        def __init__(self) -> None:
            self._inner = InMemoryDirectoryAdapter()

        def seed(self, user):
            self._inner.seed(user)

        def get(self, resource_id):
            return self._inner.get(resource_id)

        def update(self, resource_id, changes):
            return self._inner.update(resource_id, changes)

    directory = UnlabeledActuator()
    directory.seed(CanonicalUser(primary_email="user@example.com", given_name="Original"))
    runtime = ControlPlaneRuntime(build_default_registry(), directory)
    intent = MutationIntent(
        capability="identity.user.update",
        resource_id="user@example.com",
        desired_changes={"given_name": "Updated"},
    )

    receipt = runtime.execute_mutation(intent, _admin_actor())

    assert receipt.actuator_kind == "simulated"
