"""Observer(2): independent PRE and POST state acquisition.

The control plane never trusts an actuator call's own return value as
proof of effect. It reads authoritative state before acting (PRE) and
reads it again afterwards (POST) through the same read path, so the
verification engine compares what actually happened in Workspace, not
what the actuator call claimed to have done.
"""

from __future__ import annotations

from typing import Protocol

from workspace_control_plane.models import CanonicalUser


class UserReader(Protocol):
    """Read-path used by the observer. Actuator adapters implement this directly."""

    def get_user(self, primary_email: str) -> CanonicalUser | None: ...


class Observer:
    """Takes PRE/POST snapshots of a resource via its adapter's read path."""

    def __init__(self, reader: UserReader) -> None:
        self._reader = reader

    def snapshot_user(self, primary_email: str) -> CanonicalUser | None:
        return self._reader.get_user(primary_email)
