"""Keddeh Workspace Control Plane.

A governed management layer over Google Workspace's administrative APIs.

This package intentionally does not claim coverage of every Google
Workspace Admin Console function — Google does not expose all of them
through a public, programmable API, and that surface changes over time.
Instead every operation is registered as a named *capability* in
``capability_registry`` with an honest support state
(``READ_WRITE`` / ``READ_ONLY`` / ``CONSOLE_ONLY`` / ``UNSUPPORTED``), and
only ``READ_WRITE`` / ``READ_ONLY`` capabilities get a runnable actuator.
Nothing here fakes an actuator for a console-only setting.

Every mutation goes through one transaction model, implemented in
``runtime.ControlPlaneRuntime``::

    INTENT -> PRE OBSERVE -> CANDIDATE STATE -> DELTA -> ADMISSION
    -> (APPROVAL) -> ACTUATOR -> POST OBSERVE -> VERIFY -> RECEIPT

This is the R1 milestone: canonical user model, Observer(2), admission
gate, a Directory adapter (Google-backed and in-memory), verification,
and receipts. Reports, Data Transfer, Licensing, Alert Center, Drive and
Calendar adapters are future milestones and are not implemented yet.
"""

from workspace_control_plane.models import CanonicalGroup, CanonicalOrgUnit, CanonicalUser, UserState
from workspace_control_plane.runtime import ControlPlaneRuntime, UserMutationIntent

__all__ = [
    "CanonicalUser",
    "CanonicalGroup",
    "CanonicalOrgUnit",
    "UserState",
    "ControlPlaneRuntime",
    "UserMutationIntent",
]
