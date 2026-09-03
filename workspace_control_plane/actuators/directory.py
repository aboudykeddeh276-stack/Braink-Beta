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

from typing import Any

from workspace_control_plane.models import CanonicalUser, UserState

# Canonical fields GoogleDirectoryAdapter.update_user knows how to translate
# into a Directory API `users.update` request body.
_TRANSLATABLE_UPDATE_FIELDS = frozenset({"given_name", "family_name", "org_unit_path", "suspended"})


class InMemoryDirectoryAdapter:
    """In-memory ``DirectoryActuator`` with no external dependencies."""

    def __init__(self, credential_subject: str | None = None) -> None:
        self._users: dict[str, CanonicalUser] = {}
        # Identity the runtime should record on a receipt's delegated_identity
        # field. None means "fall back to the requesting actor's email",
        # which is what every existing caller of this in-memory adapter wants.
        self.credential_subject = credential_subject

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
        updated = existing.model_copy(update=changes)
        new_email = updated.primary_email
        if new_email != primary_email:
            if new_email in self._users:
                raise ValueError(f"user already exists: {new_email}")
            del self._users[primary_email]
        self._users[new_email] = updated
        return self.get_user(new_email)

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
        # Best-effort: record which credential subject is actually executing
        # requests, so receipts don't have to fall back to the requesting
        # actor's claimed identity. Most delegated credential objects expose
        # this; if not, the runtime falls back to the actor's email.
        self.credential_subject = getattr(delegated_credentials, "service_account_email", None)

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
        # The Directory API requires a password (or an invited-user flow) and
        # non-null given/family names to create an account. CanonicalUser has
        # no field for a password and allows both names to be None, so this
        # adapter cannot yet build a valid creation request — refuse rather
        # than send a payload the API is guaranteed to reject or, worse, that
        # silently omits a required security field.
        raise NotImplementedError(
            "GoogleDirectoryAdapter.create_user is not implemented: user creation needs "
            "a dedicated creation input (password/invitation, required given/family name) "
            "that CanonicalUser does not model yet."
        )

    def update_user(self, primary_email: str, changes: dict) -> CanonicalUser:
        unsupported = set(changes) - _TRANSLATABLE_UPDATE_FIELDS
        if unsupported:
            raise NotImplementedError(
                f"GoogleDirectoryAdapter cannot translate these canonical fields to the "
                f"Directory API yet: {sorted(unsupported)}"
            )

        body: dict[str, Any] = {}
        name: dict[str, str] = {}
        if "given_name" in changes:
            name["givenName"] = changes["given_name"]
        if "family_name" in changes:
            name["familyName"] = changes["family_name"]
        if name:
            body["name"] = name
        if "org_unit_path" in changes:
            body["orgUnitPath"] = changes["org_unit_path"]
        if "suspended" in changes:
            body["suspended"] = changes["suspended"]

        result = self._service.users().update(userKey=primary_email, body=body).execute()
        return self._from_api(result)

    def suspend_user(self, primary_email: str) -> CanonicalUser:
        return self.update_user(primary_email, {"suspended": True})

    def delete_user(self, primary_email: str) -> None:
        self._service.users().delete(userKey=primary_email).execute()

    @staticmethod
    def _from_api(body: dict) -> CanonicalUser:
        name = body.get("name", {})
        if body.get("archived"):
            state = UserState.ARCHIVED
        elif body.get("suspended"):
            state = UserState.SUSPENDED
        else:
            state = UserState.ACTIVE
        return CanonicalUser(
            primary_email=body["primaryEmail"],
            given_name=name.get("givenName"),
            family_name=name.get("familyName"),
            org_unit_path=body.get("orgUnitPath", "/"),
            suspended=body.get("suspended", False),
            state=state,
            is_admin=body.get("isAdmin", False),
            aliases=body.get("aliases", []),
        )
