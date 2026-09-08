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

``ControlPlaneRuntime`` is generic over resource type (``ResourceT``), so
the same runtime class drives both the Directory adapter
(``CanonicalUser``) and the Licensing adapter
(``CanonicalLicenseAssignment``) without change. Reports, Data Transfer,
Alert Center, Drive and Calendar adapters are future milestones and are
not implemented yet.
"""

from workspace_control_plane.models import (
    CanonicalGroup,
    CanonicalLicenseAssignment,
    CanonicalOrgUnit,
    CanonicalUser,
    UserState,
)
from workspace_control_plane.runtime import ControlPlaneRuntime, MutationIntent

__all__ = [
    "CanonicalUser",
    "CanonicalGroup",
    "CanonicalOrgUnit",
    "CanonicalLicenseAssignment",
    "UserState",
    "ControlPlaneRuntime",
    "MutationIntent",
]
