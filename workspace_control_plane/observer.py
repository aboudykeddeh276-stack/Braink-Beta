"""Observer(2): independent PRE and POST state acquisition.

The control plane never trusts an actuator call's own return value as
proof of effect. It reads authoritative state before acting (PRE) and
reads it again afterwards (POST) through the exact same read path — this
class — so the verification engine compares what actually happened, not
what the actuator call claimed to have done.

This is generic over the resource type so one Observer implementation
serves every adapter (Directory, Licensing, ...); ``ControlPlaneRuntime``
constructs one per actuator and uses it for both the PRE and POST read,
rather than each call site invoking the actuator's read method directly
— that's what makes "same read path" a structural guarantee instead of
an accident of calling the same method twice.
"""

from __future__ import annotations

from typing import Generic

from workspace_control_plane.actuators.base import ResourceActuator, ResourceT


class Observer(Generic[ResourceT]):
    """Takes PRE/POST snapshots of a resource via its actuator's read path."""

    def __init__(self, actuator: ResourceActuator[ResourceT]) -> None:
        self._actuator = actuator

    def snapshot(self, resource_id: str) -> ResourceT | None:
        return self._actuator.get(resource_id)
