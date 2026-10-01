"""Canonical resource models for the Workspace Control Plane.

These are the control plane's own representation of Workspace resources,
independent of any single Google API's response shape. Adapters translate
to and from these models at the Actuator Boundary; everything upstream of
that boundary (candidate state, admission, verification, receipts) works
only with canonical models.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class ResourceKind(str, Enum):
    USER = "user"
    GROUP = "group"
    ORG_UNIT = "org_unit"


class UserState(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class CanonicalUser(BaseModel):
    """Control-plane representation of a Workspace user."""

    resource_kind: ResourceKind = ResourceKind.USER
    primary_email: str
    given_name: str | None = None
    family_name: str | None = None
    org_unit_path: str = "/"
    state: UserState = UserState.ACTIVE
    is_admin: bool = False
    suspended: bool = False
    aliases: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _derive_state_from_suspension(self) -> "CanonicalUser":
        # `suspended` and `state` describe the same account status; keep them
        # in sync so callers can't produce e.g. an ACTIVE-but-suspended user.
        # ARCHIVED is a distinct lifecycle stage and is left untouched here.
        if self.suspended and self.state == UserState.ACTIVE:
            self.state = UserState.SUSPENDED
        elif not self.suspended and self.state == UserState.SUSPENDED:
            self.state = UserState.ACTIVE
        return self


class CanonicalGroup(BaseModel):
    """Control-plane representation of a Workspace group."""

    resource_kind: ResourceKind = ResourceKind.GROUP
    email: str
    name: str | None = None
    description: str | None = None
    member_emails: list[str] = Field(default_factory=list)


class CanonicalOrgUnit(BaseModel):
    """Control-plane representation of a Workspace organisational unit."""

    resource_kind: ResourceKind = ResourceKind.ORG_UNIT
    org_unit_path: str
    name: str
    parent_org_unit_path: str | None = None
