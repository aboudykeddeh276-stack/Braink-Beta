"""Licensing adapter.

The second adapter against ``ResourceActuator``, deliberately chosen to
be a different real Google API surface than the Directory adapter (the
Enterprise License Manager API, not the Admin SDK Directory API) so it
actually tests whether the pipeline generalizes rather than being
implicitly fit to one API's shape.

Same two-implementation split as the Directory adapter:

* ``InMemoryLicensingAdapter`` — deterministic stand-in used by tests.
* ``GoogleLicensingAdapter`` — the real actuator; not exercised here.
"""

from __future__ import annotations

from workspace_control_plane.actuators.base import ActuatorKind
from workspace_control_plane.models import CanonicalLicenseAssignment


class InMemoryLicensingAdapter:
    """In-memory ``ResourceActuator[CanonicalLicenseAssignment]``."""

    kind = ActuatorKind.SIMULATED

    def __init__(self) -> None:
        self._assignments: dict[str, CanonicalLicenseAssignment] = {}

    def seed(self, assignment: CanonicalLicenseAssignment) -> None:
        """Preload an assignment, bypassing the create pipeline. Test helper only."""
        self._assignments[assignment.user_email] = assignment.model_copy(deep=True)

    def get(self, resource_id: str) -> CanonicalLicenseAssignment | None:
        assignment = self._assignments.get(resource_id)
        return assignment.model_copy(deep=True) if assignment else None

    def create(self, resource: CanonicalLicenseAssignment) -> CanonicalLicenseAssignment:
        if resource.user_email in self._assignments:
            raise ValueError(f"license assignment already exists for: {resource.user_email}")
        stored = resource.model_copy(deep=True)
        self._assignments[resource.user_email] = stored
        return stored.model_copy(deep=True)

    def update(self, resource_id: str, changes: dict) -> CanonicalLicenseAssignment:
        existing = self._require(resource_id)
        updated = existing.model_copy(update=changes)
        self._assignments[resource_id] = updated
        return updated.model_copy(deep=True)

    def delete(self, resource_id: str) -> None:
        self._require(resource_id)
        del self._assignments[resource_id]

    def _require(self, resource_id: str) -> CanonicalLicenseAssignment:
        assignment = self._assignments.get(resource_id)
        if assignment is None:
            raise KeyError(f"no such license assignment: {resource_id}")
        return assignment


class GoogleLicensingAdapter:
    """Real actuator backed by the Enterprise License Manager API.

    Not exercised in this repository — no live Workspace credentials are
    configured here — but implements the identical contract as
    ``InMemoryLicensingAdapter`` so the rest of the pipeline runs
    unchanged against either.
    """

    kind = ActuatorKind.LIVE

    def __init__(self, delegated_credentials: object) -> None:
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise ImportError(
                "google-api-python-client is required for GoogleLicensingAdapter; "
                "install the 'google' extra."
            ) from exc
        self._service = build("licensing", "v1", credentials=delegated_credentials)

    def get(self, resource_id: str) -> CanonicalLicenseAssignment | None:
        # The real API lists assignments per-product/SKU rather than
        # per-user; a live implementation would enumerate the org's SKUs
        # and collect the ones assigned to resource_id. Not implemented,
        # since this adapter is never exercised in this milestone.
        raise NotImplementedError("GoogleLicensingAdapter.get is not implemented in this milestone")

    def create(self, resource: CanonicalLicenseAssignment) -> CanonicalLicenseAssignment:
        raise NotImplementedError(
            "GoogleLicensingAdapter.create is not implemented in this milestone"
        )

    def update(self, resource_id: str, changes: dict) -> CanonicalLicenseAssignment:
        raise NotImplementedError(
            "GoogleLicensingAdapter.update is not implemented in this milestone"
        )

    def delete(self, resource_id: str) -> None:
        raise NotImplementedError(
            "GoogleLicensingAdapter.delete is not implemented in this milestone"
        )
