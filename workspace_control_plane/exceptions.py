"""Exceptions raised by the Workspace Control Plane."""

from __future__ import annotations


class ControlPlaneError(Exception):
    """Base exception for the Workspace Control Plane."""


class AdmissionDeniedError(ControlPlaneError):
    """Raised when an intent is rejected by the admission gate."""


class ApprovalRequiredError(ControlPlaneError):
    """Raised when an intent requires approval that has not been granted."""


class VerificationFailedError(ControlPlaneError):
    """Raised when observed state does not converge with the requested delta."""


class UnsupportedCapabilityError(ControlPlaneError):
    """Raised when a capability has no supported, runnable actuator."""
