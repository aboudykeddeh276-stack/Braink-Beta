"""Runtime: the single transaction model every mutating operation goes
through.

    INTENT -> ADMISSION -> (APPROVAL) -> PRE OBSERVE -> CANDIDATE STATE
    -> DELTA -> ACTUATOR -> POST OBSERVE -> VERIFY -> RECEIPT

Admission runs before any privileged read: an actor that isn't authorized
for a capability never causes a call into the (privileged) directory
adapter, and never learns anything about whether a target resource exists.

No caller mutates Workspace directly; every mutation is expressed as an
intent and executed through ``ControlPlaneRuntime``, which is the only
object that holds an actuator. Each capability dispatches to its own
actuator method rather than a single generic "apply these changes" path,
so e.g. ``identity.user.delete`` actually deletes, ``identity.user.suspend``
can only suspend (it cannot smuggle through arbitrary other field changes),
and a READ_ONLY capability can never reach a mutation at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from workspace_control_plane.actuators.base import DirectoryActuator
from workspace_control_plane.admission import Actor, AdmissionGate
from workspace_control_plane.candidate import diff_models
from workspace_control_plane.capability_registry import CapabilityRegistry, SupportState
from workspace_control_plane.exceptions import ApprovalRequiredError, UnsupportedCapabilityError, VerificationFailedError
from workspace_control_plane.models import UserState
from workspace_control_plane.receipts import Receipt, hash_state
from workspace_control_plane.verification import VerificationResult, verify_user_delta

# Post-conditions this milestone can actually check. Everything else a
# capability declares in capability_registry is surfaced on the receipt as
# unverified rather than silently counted as satisfied — Reports, Data
# Transfer and Licensing adapters (which would check the rest) are future
# milestones.
_IMPLEMENTED_POST_CONDITIONS = frozenset({"user_absent"})


@dataclass(frozen=True)
class UserMutationIntent:
    capability: str
    primary_email: str
    desired_changes: dict[str, Any]


class ControlPlaneRuntime:
    """Executes user-mutation intents against a single Directory actuator."""

    def __init__(self, registry: CapabilityRegistry, directory: DirectoryActuator) -> None:
        self._registry = registry
        self._admission = AdmissionGate(registry)
        self._directory = directory

    def execute_user_mutation(
        self,
        intent: UserMutationIntent,
        actor: Actor,
        approvers: frozenset[str] = frozenset(),
    ) -> Receipt:
        definition = self._registry.get(intent.capability)
        if definition.support_state != SupportState.READ_WRITE:
            raise UnsupportedCapabilityError(
                f"{intent.capability!r} is not a READ_WRITE capability "
                f"(state={definition.support_state.value}); it has no mutating actuator"
            )
        if intent.capability not in ("identity.user.update", "identity.user.suspend", "identity.user.delete"):
            raise UnsupportedCapabilityError(
                f"{intent.capability!r} has no actuator dispatch implemented in this milestone"
            )

        # ADMISSION + POLICY GATE, before any privileged read of the target.
        decision = self._admission.admit(intent.capability, actor, approvers)
        if not decision.approval_satisfied:
            raise ApprovalRequiredError(decision.reason)

        # PRE OBSERVE
        pre_state = self._directory.get_user(intent.primary_email)
        if pre_state is None:
            raise KeyError(f"no such user: {intent.primary_email}")

        if intent.capability == "identity.user.update":
            desired_state = type(pre_state).model_validate({**pre_state.model_dump(), **intent.desired_changes})
            delta = diff_models(intent.primary_email, pre_state, desired_state)
            if not delta.is_noop:
                self._directory.update_user(intent.primary_email, delta.changed_fields)
            after_state = self._directory.get_user(intent.primary_email)
            result = verify_user_delta(delta, pre_state, after_state)

        elif intent.capability == "identity.user.suspend":
            if intent.desired_changes:
                raise ValueError(
                    "identity.user.suspend does not accept desired_changes "
                    f"(it can only suspend); got {sorted(intent.desired_changes)}"
                )
            desired_state = pre_state.model_copy(update={"suspended": True, "state": UserState.SUSPENDED})
            delta = diff_models(intent.primary_email, pre_state, desired_state)
            if not delta.is_noop:
                self._directory.suspend_user(intent.primary_email)
            after_state = self._directory.get_user(intent.primary_email)
            result = verify_user_delta(delta, pre_state, after_state)

        else:  # identity.user.delete
            if intent.desired_changes:
                raise ValueError(
                    "identity.user.delete does not accept desired_changes "
                    f"(it can only delete); got {sorted(intent.desired_changes)}"
                )
            self._directory.delete_user(intent.primary_email)
            after_state = self._directory.get_user(intent.primary_email)
            if after_state is not None:
                raise VerificationFailedError(f"{intent.primary_email}: still present after delete")
            result = VerificationResult(resource_id=intent.primary_email, converged=True)

        # RECEIPT — built only from what was actually observed above.
        subject = getattr(self._directory, "credential_subject", None) or actor.email
        unverified = tuple(
            pc for pc in definition.post_conditions if pc not in _IMPLEMENTED_POST_CONDITIONS
        )

        return Receipt(
            capability=intent.capability,
            actor=actor.email,
            delegated_identity=subject,
            scopes_used=tuple(sorted(decision.approved_scopes)),
            resource_id=intent.primary_email,
            before_state_hash=hash_state(pre_state),
            after_state_hash=hash_state(after_state),
            converged=result.converged,
            unexpected_fields=result.unexpected_fields,
            unverified_post_conditions=unverified,
        )
