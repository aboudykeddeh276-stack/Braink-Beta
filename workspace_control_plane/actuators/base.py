"""Actuator contracts.

Everything upstream of the Actuator Boundary (admission, candidate
state, verification) works only with canonical models and this
protocol; everything downstream of it speaks the actual Google API.

``ResourceActuator`` is generic over the canonical model it manages
(``CanonicalUser`` for the Directory adapter, ``CanonicalLicenseAssignment``
for the Licensing adapter, and so on) so ``ControlPlaneRuntime`` and the
verification/receipt machinery are written once against this one
contract rather than once per resource type. Adding a new domain means
implementing this Protocol for a new canonical model, not writing a new
runtime.

Every actuator declares a ``kind``: ``LIVE`` if it can actually reach
Google, ``SIMULATED`` otherwise. A receipt produced against a simulated
actuator is evidence the pipeline logic works, not that any Workspace
resource changed — the two must never be able to look identical in a
receipt, so ``kind`` is threaded through into every receipt at
`workspace_control_plane.runtime`. An actuator that doesn't declare a
kind is treated as ``SIMULATED``: unlabeled evidence defaults to the
weaker claim, never the stronger one.
"""

from __future__ import annotations

from enum import Enum
from typing import Protocol, TypeVar

from pydantic import BaseModel

ResourceT = TypeVar("ResourceT", bound=BaseModel)


class ActuatorKind(str, Enum):
    LIVE = "live"
    SIMULATED = "simulated"


class ResourceActuator(Protocol[ResourceT]):
    kind: ActuatorKind

    def get(self, resource_id: str) -> ResourceT | None: ...

    def create(self, resource: ResourceT) -> ResourceT: ...

    def update(self, resource_id: str, changes: dict) -> ResourceT: ...

    def delete(self, resource_id: str) -> None: ...
