"""Verification Engine.

Compares the requested delta against what the POST observer actually
saw. This is what turns "the API call returned 200" into "the resource
is provably in the state we asked for" — and separately flags any field
that changed but was never requested, so unexpected drift is visible
rather than silently accepted.
"""

from __future__ import annotations

from dataclasses import dataclass

from workspace_control_plane.candidate import StateDelta
from workspace_control_plane.exceptions import VerificationFailedError
from workspace_control_plane.models import CanonicalUser


@dataclass(frozen=True)
class VerificationResult:
    resource_id: str
    converged: bool
    unexpected_fields: tuple[str, ...] = ()


def verify_user_delta(
    requested: StateDelta,
    pre_state: CanonicalUser | None,
    post_state: CanonicalUser | None,
) -> VerificationResult:
    """Check that every requested field converged, and surface unrequested drift."""
    if post_state is None:
        raise VerificationFailedError(f"post-observe found no resource for {requested.resource_id}")

    post_fields = post_state.model_dump()
    pre_fields = pre_state.model_dump() if pre_state else {}

    unmatched = [
        change.field for change in requested.changes if post_fields.get(change.field) != change.desired
    ]
    if unmatched:
        raise VerificationFailedError(
            f"{requested.resource_id}: fields did not converge to requested values: {unmatched}"
        )

    requested_fields = {change.field for change in requested.changes}
    unexpected = tuple(
        field
        for field, value in post_fields.items()
        if pre_fields.get(field) != value and field not in requested_fields
    )

    return VerificationResult(resource_id=requested.resource_id, converged=True, unexpected_fields=unexpected)
