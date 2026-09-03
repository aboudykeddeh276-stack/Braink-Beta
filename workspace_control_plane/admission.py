"""Admission / Learning Gate.

Every intent passes through here before it is allowed anywhere near the
Actuator Boundary. This module never calls a Google API — it only
decides whether an intent may proceed, and what it is still missing
(approval, specific scopes) before it can.
"""

from __future__ import annotations

from dataclasses import dataclass

from workspace_control_plane.capability_registry import (
    ApprovalMode,
    CapabilityDefinition,
    CapabilityRegistry,
    SupportState,
)
from workspace_control_plane.exceptions import AdmissionDeniedError, UnsupportedCapabilityError


@dataclass(frozen=True)
class Actor:
    """The identity requesting an operation, and what it holds."""

    email: str
    granted_scopes: frozenset[str]
    is_delegated_admin: bool = False


@dataclass(frozen=True)
class AdmissionDecision:
    capability: CapabilityDefinition
    approved_scopes: frozenset[str]
    approval_satisfied: bool
    reason: str = ""


def _scope_satisfied(required_scope: str, granted_scopes: frozenset[str]) -> bool:
    """A held write scope also authorizes the matching read of the same resource."""
    if required_scope in granted_scopes:
        return True
    if required_scope.endswith(".readonly"):
        return required_scope[: -len(".readonly")] in granted_scopes
    return False


class AdmissionGate:
    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def admit(
        self,
        capability_name: str,
        actor: Actor,
        approvers: frozenset[str] = frozenset(),
    ) -> AdmissionDecision:
        """Decide whether ``actor`` may proceed with ``capability_name``.

        ``approvers`` is the set of distinct identities (email addresses)
        that have signed off on this specific operation, separate from the
        requesting ``actor``. A SINGLE approval mode needs at least one
        approver who is not the actor; TWO_PERSON needs at least two, all
        distinct from the actor and from each other. This package does not
        yet verify that an approver identity itself holds admin authority —
        only that approval isn't the same person approving their own
        request under a different name for it.
        """
        definition = self._registry.get(capability_name)

        if definition.support_state in (SupportState.CONSOLE_ONLY, SupportState.UNSUPPORTED):
            raise UnsupportedCapabilityError(
                f"{capability_name!r} has no supported programmable actuator "
                f"(state={definition.support_state.value}); it must be performed "
                "in the Admin Console."
            )

        if not actor.is_delegated_admin:
            raise AdmissionDeniedError(
                f"{actor.email} does not hold delegated admin authority for {capability_name!r}"
            )

        missing_scopes = {
            scope for scope in definition.required_scopes
            if not _scope_satisfied(scope, actor.granted_scopes)
        }
        if missing_scopes:
            raise AdmissionDeniedError(
                f"{actor.email} is missing required scopes for {capability_name!r}: "
                f"{sorted(missing_scopes)}"
            )

        distinct_approvers = frozenset(approvers) - {actor.email}
        required_approvers = {
            ApprovalMode.NONE: 0,
            ApprovalMode.SINGLE: 1,
            ApprovalMode.TWO_PERSON: 2,
        }[definition.approval_mode]
        approval_satisfied = len(distinct_approvers) >= required_approvers

        if not approval_satisfied:
            return AdmissionDecision(
                capability=definition,
                approved_scopes=frozenset(definition.required_scopes),
                approval_satisfied=False,
                reason=(
                    f"{capability_name!r} requires {required_approvers} distinct approver(s) "
                    f"other than {actor.email} (mode={definition.approval_mode.value}); "
                    f"got {len(distinct_approvers)}"
                ),
            )

        return AdmissionDecision(
            capability=definition,
            approved_scopes=frozenset(definition.required_scopes),
            approval_satisfied=True,
        )
