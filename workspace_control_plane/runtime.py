"""Runtime: the single transaction model every mutating operation goes
through.

    INTENT -> PRE OBSERVE -> CANDIDATE STATE -> DELTA -> ADMISSION
    -> (APPROVAL) -> ACTUATOR -> POST OBSERVE -> VERIFY -> RECEIPT

No caller mutates Workspace directly; every mutation is expressed as an
intent and executed through ``ControlPlaneRuntime``, which is the only
object that holds an actuator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from workspace_control_plane.actuators.base import DirectoryActuator
from workspace_control_plane.admission import Actor, AdmissionGate
from workspace_control_plane.candidate import diff_models
from workspace_control_plane.capability_registry import CapabilityRegistry
from workspace_control_plane.exceptions import ApprovalRequiredError
from workspace_control_plane.receipts import Receipt, hash_state
from workspace_control_plane.verification import verify_user_delta


@dataclass(frozen=True)
class UserMutationIntent:
    capability: str
    primary_email: str
    desired_changes: dict[str, Any]


class ControlPlaneRuntime:
    """Executes user-mutation intents against a single Directory actuator."""

    def __init__(self, registry: CapabilityRegistry, directory: DirectoryActuator) -> None:
        self._admission = AdmissionGate(registry)
        self._directory = directory

    def execute_user_mutation(
        self,
        intent: UserMutationIntent,
        actor: Actor,
        approval_granted: bool = False,
    ) -> Receipt:
        # PRE OBSERVE
        pre_state = self._directory.get_user(intent.primary_email)
        if pre_state is None:
            raise KeyError(f"no such user: {intent.primary_email}")

        # DERIVE CANDIDATE STATE + COMPUTE DELTA
        desired_state = pre_state.model_copy(update=intent.desired_changes)
        delta = diff_models(intent.primary_email, pre_state, desired_state)

        # ADMISSION + POLICY GATE
        decision = self._admission.admit(intent.capability, actor, approval_granted)
        if not decision.approval_satisfied:
            raise ApprovalRequiredError(decision.reason)

        if delta.is_noop:
            after_state = pre_state
        else:
            # ACTUATOR BOUNDARY -> GOOGLE WORKSPACE API
            self._directory.update_user(intent.primary_email, delta.changed_fields)
            # POST OBSERVE
            after_state = self._directory.get_user(intent.primary_email)

        # VERIFY DESIRED ~= OBSERVED
        result = verify_user_delta(delta, pre_state, after_state)

        # RECEIPT
        return Receipt(
            capability=intent.capability,
            actor=actor.email,
            delegated_identity=actor.email if actor.is_delegated_admin else None,
            scopes_used=tuple(sorted(decision.approved_scopes)),
            resource_id=intent.primary_email,
            before_state_hash=hash_state(pre_state),
            after_state_hash=hash_state(after_state),
            converged=result.converged,
            unexpected_fields=result.unexpected_fields,
        )
