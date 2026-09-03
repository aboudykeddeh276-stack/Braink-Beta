"""Actuator contracts.

Everything upstream of the Actuator Boundary (admission, candidate
state, verification) works only with canonical models and this
protocol; everything downstream of it speaks the actual Google API.
"""

from __future__ import annotations

from typing import Protocol

from workspace_control_plane.models import CanonicalUser


class DirectoryActuator(Protocol):
    def get_user(self, primary_email: str) -> CanonicalUser | None: ...

    def create_user(self, user: CanonicalUser) -> CanonicalUser: ...

    def update_user(self, primary_email: str, changes: dict) -> CanonicalUser: ...

    def suspend_user(self, primary_email: str) -> CanonicalUser: ...

    def delete_user(self, primary_email: str) -> None: ...
