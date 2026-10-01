"""Candidate State Engine.

Derives a desired-state delta by diffing a canonical model against a
proposed copy of itself. This module never talks to Google — it is
mirror-only, operating entirely on already-observed state and the
caller's requested changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class FieldChange:
    field: str
    current: Any
    desired: Any


@dataclass(frozen=True)
class StateDelta:
    resource_id: str
    changes: tuple[FieldChange, ...]

    @property
    def is_noop(self) -> bool:
        return len(self.changes) == 0

    @property
    def changed_fields(self) -> dict[str, Any]:
        return {change.field: change.desired for change in self.changes}


def diff_models(resource_id: str, current: BaseModel, desired: BaseModel) -> StateDelta:
    """Compute a field-level delta between two pydantic models of the same type."""
    if type(current) is not type(desired):
        raise TypeError("current and desired must be the same resource type")

    current_fields = current.model_dump()
    desired_fields = desired.model_dump()

    changes = tuple(
        FieldChange(field=key, current=current_fields.get(key), desired=value)
        for key, value in desired_fields.items()
        if current_fields.get(key) != value
    )
    return StateDelta(resource_id=resource_id, changes=changes)
