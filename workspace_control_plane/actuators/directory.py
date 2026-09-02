"""Directory adapter.

Two implementations sharing the same ``DirectoryActuator`` contract:

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

from workspace_control_plane.models import CanonicalUser, UserState


class InMemoryDirectoryAdapter:
    """In-memory ``DirectoryActuator`` with no external dependencies."""

    def __init__(self) -> None:
        self._users: dict[str, CanonicalUser] = {}

    def seed(self, user: CanonicalUser) -> None:
        """Preload a user, bypassing the create-user pipeline. Test helper only."""
        self._users[user.primary_email] = user.model_copy(deep=True)

    def get_user(self, primary_email: str) -> CanonicalUser | None:
        user = self._users.get(primary_email)
        return user.model_copy(deep=True) if user else None

    def create_user(self, user: CanonicalUser) -> CanonicalUser:
        if user.primary_email in self._users:
            raise ValueError(f"user already exists: {user.primary_email}")
        self._users[user.primary_email] = user.model_copy(deep=True)
        return self.get_user(user.primary_email)

    def update_user(self, primary_email: str, changes: dict) -> CanonicalUser:
        existing = self._require(primary_email)
        self._users[primary_email] = existing.model_copy(update=changes)
        return self.get_user(primary_email)

    def suspend_user(self, primary_email: str) -> CanonicalUser:
        return self.update_user(primary_email, {"suspended": True, "state": UserState.SUSPENDED})

    def delete_user(self, primary_email: str) -> None:
        self._require(primary_email)
        del self._users[primary_email]

    def _require(self, primary_email: str) -> CanonicalUser:
        user = self._users.get(primary_email)
        if user is None:
            raise KeyError(f"no such user: {primary_email}")
        return user


class GoogleDirectoryAdapter:
    """Real actuator backed by the Admin SDK Directory API.

    Not exercised in this repository — no live Workspace credentials are
    configured here — but implements the identical contract as
    ``InMemoryDirectoryAdapter`` so the rest of the pipeline runs
    unchanged against either.
    """

    def __init__(self, delegated_credentials: object) -> None:
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise ImportError(
                "google-api-python-client is required for GoogleDirectoryAdapter; "
                "install the 'google' extra."
            ) from exc
        self._service = build("admin", "directory_v1", credentials=delegated_credentials)

    def get_user(self, primary_email: str) -> CanonicalUser | None:
        from googleapiclient.errors import HttpError

        try:
            body = self._service.users().get(userKey=primary_email).execute()
        except HttpError as exc:
            if exc.resp.status == 404:
                return None
            raise
        return self._from_api(body)

    def create_user(self, user: CanonicalUser) -> CanonicalUser:
        body = self._service.users().insert(body=self._to_api(user)).execute()
        return self._from_api(body)

    def update_user(self, primary_email: str, changes: dict) -> CanonicalUser:
        body = self._service.users().update(userKey=primary_email, body=changes).execute()
        return self._from_api(body)

    def suspend_user(self, primary_email: str) -> CanonicalUser:
        return self.update_user(primary_email, {"suspended": True})

    def delete_user(self, primary_email: str) -> None:
        self._service.users().delete(userKey=primary_email).execute()

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
