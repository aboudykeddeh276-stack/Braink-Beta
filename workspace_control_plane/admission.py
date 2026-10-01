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


class AdmissionGate:
    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def admit(
        self,
        capability_name: str,
        actor: Actor,
        approval_granted: bool = False,
    ) -> AdmissionDecision:
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

        missing_scopes = set(definition.required_scopes) - actor.granted_scopes
        if missing_scopes:
            raise AdmissionDeniedError(
                f"{actor.email} is missing required scopes for {capability_name!r}: "
                f"{sorted(missing_scopes)}"
            )

        approval_satisfied = definition.approval_mode == ApprovalMode.NONE or approval_granted
        if not approval_satisfied:
            return AdmissionDecision(
                capability=definition,
                approved_scopes=frozenset(definition.required_scopes),
                approval_satisfied=False,
                reason=(
                    f"{capability_name!r} requires approval "
                    f"(mode={definition.approval_mode.value}) before it can be actuated"
                ),
            )

        return AdmissionDecision(
            capability=definition,
            approved_scopes=frozenset(definition.required_scopes),
            approval_satisfied=True,
        )
