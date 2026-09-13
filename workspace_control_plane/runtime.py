"""Runtime: the single transaction model every mutating operation goes
through.

    INTENT -> PRE OBSERVE -> CANDIDATE STATE -> DELTA -> ADMISSION
    -> (APPROVAL) -> ACTUATOR -> POST OBSERVE -> VERIFY -> RECEIPT

No caller mutates a Workspace resource directly; every mutation is
expressed as an intent and executed through ``ControlPlaneRuntime``,
which is the only object that holds an actuator.

Generic over resource type via ``ResourceActuator[ResourceT]``: the same
runtime class runs a Directory mutation (``CanonicalUser``) and a
Licensing mutation (``CanonicalLicenseAssignment``) identically, because
nothing here reaches for a resource-specific field or method name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic

from workspace_control_plane.actuators.base import ActuatorKind, ResourceActuator, ResourceT
from workspace_control_plane.admission import Actor, AdmissionGate
from workspace_control_plane.candidate import diff_models
from workspace_control_plane.capability_registry import CapabilityRegistry
from workspace_control_plane.exceptions import ApprovalRequiredError
from workspace_control_plane.observer import Observer
from workspace_control_plane.receipts import Receipt, ReceiptChain, hash_state
from workspace_control_plane.verification import verify_delta


@dataclass(frozen=True)
class MutationIntent:
    capability: str
    resource_id: str
    desired_changes: dict[str, Any]


class ControlPlaneRuntime(Generic[ResourceT]):
    """Executes mutation intents against a single actuator of any resource type."""

    def __init__(
        self,
        registry: CapabilityRegistry,
        actuator: ResourceActuator[ResourceT],
        receipt_chain: ReceiptChain | None = None,
    ) -> None:
        self._admission = AdmissionGate(registry)
        self._actuator = actuator
        self._observer: Observer[ResourceT] = Observer(actuator)
        self._receipt_chain = receipt_chain if receipt_chain is not None else ReceiptChain()

    def execute_mutation(
        self,
        intent: MutationIntent,
        actor: Actor,
        approval_granted: bool = False,
    ) -> Receipt:
        # PRE OBSERVE
        pre_state = self._observer.snapshot(intent.resource_id)
        if pre_state is None:
            raise KeyError(f"no such resource: {intent.resource_id}")

        # DERIVE CANDIDATE STATE + COMPUTE DELTA
        desired_state = pre_state.model_copy(update=intent.desired_changes)
        delta = diff_models(intent.resource_id, pre_state, desired_state)

        # ADMISSION + POLICY GATE
        decision = self._admission.admit(intent.capability, actor, approval_granted)
        if not decision.approval_satisfied:
            raise ApprovalRequiredError(decision.reason)

        if delta.is_noop:
            after_state: ResourceT | None = pre_state
        else:
            # ACTUATOR BOUNDARY -> GOOGLE WORKSPACE API
            self._actuator.update(intent.resource_id, delta.changed_fields)
            # POST OBSERVE (same read path as PRE, via the same Observer)
            after_state = self._observer.snapshot(intent.resource_id)

        # VERIFY DESIRED ~= OBSERVED
        result = verify_delta(delta, pre_state, after_state)

        # RECEIPT
        # actuator_kind is read off the actuator instance, not passed in by the
        # caller: an actor cannot claim LIVE provenance for a SIMULATED run.
        actuator_kind = getattr(self._actuator, "kind", ActuatorKind.SIMULATED)
        receipt = Receipt(
            capability=intent.capability,
            actor=actor.email,
            delegated_identity=actor.email if actor.is_delegated_admin else None,
            scopes_used=tuple(sorted(decision.approved_scopes)),
            resource_id=intent.resource_id,
            before_state_hash=hash_state(pre_state),
            after_state_hash=hash_state(after_state),
            converged=result.converged,
            actuator_kind=actuator_kind.value,
            previous_receipt_hash=self._receipt_chain.next_previous_hash(),
            unexpected_fields=result.unexpected_fields,
        )
        return self._receipt_chain.record(receipt)
