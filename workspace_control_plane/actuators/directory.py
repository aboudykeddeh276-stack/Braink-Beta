"""Directory adapter.

Two implementations sharing the same ``ResourceActuator[CanonicalUser]``
contract:

* ``InMemoryDirectoryAdapter`` — deterministic stand-in used by tests and
  local development where no Workspace domain-wide delegation is
  configured. This is what exercises the rest of the pipeline in this
  repository, since no live Workspace credentials are available here.
* ``GoogleDirectoryAdapter`` — the real actuator, backed by the Admin SDK
  Directory API. Requires ``google-api-python-client`` (the ``google``
  extra) and a domain-wide-delegated credential scoped to exactly the
  capability being admitted.
"""

from __future__ import annotations

from workspace_control_plane.actuators.base import ActuatorKind
from workspace_control_plane.models import CanonicalUser, UserState


class InMemoryDirectoryAdapter:
    """In-memory ``ResourceActuator[CanonicalUser]`` with no external dependencies."""

    kind = ActuatorKind.SIMULATED

    def __init__(self) -> None:
        self._users: dict[str, CanonicalUser] = {}

    def seed(self, user: CanonicalUser) -> None:
        """Preload a user, bypassing the create pipeline. Test helper only."""
        self._users[user.primary_email] = user.model_copy(deep=True)

    def get(self, resource_id: str) -> CanonicalUser | None:
        user = self._users.get(resource_id)
        return user.model_copy(deep=True) if user else None

    def create(self, resource: CanonicalUser) -> CanonicalUser:
        if resource.primary_email in self._users:
            raise ValueError(f"user already exists: {resource.primary_email}")
        stored = resource.model_copy(deep=True)
        self._users[resource.primary_email] = stored
        return stored.model_copy(deep=True)

    def update(self, resource_id: str, changes: dict) -> CanonicalUser:
        existing = self._require(resource_id)
        updated = existing.model_copy(update=changes)
        self._users[resource_id] = updated
        return updated.model_copy(deep=True)

    def suspend(self, resource_id: str) -> CanonicalUser:
        return self.update(resource_id, {"suspended": True, "state": UserState.SUSPENDED})

    def delete(self, resource_id: str) -> None:
        self._require(resource_id)
        del self._users[resource_id]

    def _require(self, resource_id: str) -> CanonicalUser:
        user = self._users.get(resource_id)
        if user is None:
            raise KeyError(f"no such user: {resource_id}")
        return user


class GoogleDirectoryAdapter:
    """Real actuator backed by the Admin SDK Directory API.

    Not exercised in this repository — no live Workspace credentials are
    configured here — but implements the identical contract as
    ``InMemoryDirectoryAdapter`` so the rest of the pipeline runs
    unchanged against either.
    """

    kind = ActuatorKind.LIVE

    def __init__(self, delegated_credentials: object) -> None:
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise ImportError(
                "google-api-python-client is required for GoogleDirectoryAdapter; "
                "install the 'google' extra."
            ) from exc
        self._service = build("admin", "directory_v1", credentials=delegated_credentials)

    def get(self, resource_id: str) -> CanonicalUser | None:
        from googleapiclient.errors import HttpError

        try:
            body = self._service.users().get(userKey=resource_id).execute()
        except HttpError as exc:
            if exc.resp.status == 404:
                return None
            raise
        return self._from_api(body)

    def create(self, resource: CanonicalUser) -> CanonicalUser:
        body = self._service.users().insert(body=self._to_api(resource)).execute()
        return self._from_api(body)

    def update(self, resource_id: str, changes: dict) -> CanonicalUser:
        body = self._service.users().update(userKey=resource_id, body=changes).execute()
        return self._from_api(body)

    def suspend(self, resource_id: str) -> CanonicalUser:
        return self.update(resource_id, {"suspended": True})

    def delete(self, resource_id: str) -> None:
        self._service.users().delete(userKey=resource_id).execute()

    @staticmethod
    def _to_api(user: CanonicalUser) -> dict:
        return {
            "primaryEmail": user.primary_email,
            "name": {"givenName": user.given_name, "familyName": user.family_name},
            "orgUnitPath": user.org_unit_path,
            "suspended": user.suspended,
        }

    @staticmethod
    def _from_api(body: dict) -> CanonicalUser:
        name = body.get("name", {})
        return CanonicalUser(
            primary_email=body["primaryEmail"],
            given_name=name.get("givenName"),
            family_name=name.get("familyName"),
            org_unit_path=body.get("orgUnitPath", "/"),
            suspended=body.get("suspended", False),
            state=UserState.SUSPENDED if body.get("suspended") else UserState.ACTIVE,
            is_admin=body.get("isAdmin", False),
            aliases=body.get("aliases", []),
        )
