import pytest

from workspace_control_plane.admission import Actor, AdmissionGate
from workspace_control_plane.capability_registry import build_default_registry
from workspace_control_plane.exceptions import AdmissionDeniedError, UnsupportedCapabilityError

USER_SCOPE = "https://www.googleapis.com/auth/admin.directory.user"


def test_console_only_capability_is_rejected_before_actor_checks():
    gate = AdmissionGate(build_default_registry())
    actor = Actor(email="admin@example.com", granted_scopes=frozenset(), is_delegated_admin=True)

    with pytest.raises(UnsupportedCapabilityError):
        gate.admit("branding.custom_logo", actor)


def test_non_delegated_actor_is_denied():
    gate = AdmissionGate(build_default_registry())
    actor = Actor(email="nobody@example.com", granted_scopes=frozenset({USER_SCOPE}), is_delegated_admin=False)

    with pytest.raises(AdmissionDeniedError):
        gate.admit("identity.user.update", actor)


def test_missing_scope_is_denied():
    gate = AdmissionGate(build_default_registry())
    actor = Actor(email="admin@example.com", granted_scopes=frozenset(), is_delegated_admin=True)

    with pytest.raises(AdmissionDeniedError):
        gate.admit("identity.user.update", actor)


def test_capability_without_approval_mode_is_admitted_immediately():
    gate = AdmissionGate(build_default_registry())
    actor = Actor(email="admin@example.com", granted_scopes=frozenset({USER_SCOPE}), is_delegated_admin=True)

    decision = gate.admit("identity.user.update", actor)

    assert decision.approval_satisfied is True


def test_destructive_capability_without_approval_is_held():
    gate = AdmissionGate(build_default_registry())
    actor = Actor(email="admin@example.com", granted_scopes=frozenset({USER_SCOPE}), is_delegated_admin=True)

    decision = gate.admit("identity.user.delete", actor, approval_granted=False)

    assert decision.approval_satisfied is False
    assert "two_person" in decision.reason


def test_destructive_capability_with_approval_is_admitted():
    gate = AdmissionGate(build_default_registry())
    actor = Actor(email="admin@example.com", granted_scopes=frozenset({USER_SCOPE}), is_delegated_admin=True)

    decision = gate.admit("identity.user.delete", actor, approval_granted=True)

    assert decision.approval_satisfied is True
