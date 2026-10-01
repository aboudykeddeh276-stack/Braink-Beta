import pytest

from workspace_control_plane.candidate import diff_models
from workspace_control_plane.models import CanonicalUser, UserState


def test_diff_reports_only_changed_fields():
    current = CanonicalUser(primary_email="a@example.com", given_name="A")
    desired = current.model_copy(update={"given_name": "B"})

    delta = diff_models("a@example.com", current, desired)

    assert delta.changed_fields == {"given_name": "B"}
    assert delta.is_noop is False


def test_diff_with_no_changes_is_noop():
    current = CanonicalUser(primary_email="a@example.com")
    desired = current.model_copy(deep=True)

    delta = diff_models("a@example.com", current, desired)

    assert delta.is_noop is True


def test_diff_rejects_mismatched_types():
    user = CanonicalUser(primary_email="a@example.com")

    with pytest.raises(TypeError):
        diff_models("a@example.com", user, object())  # type: ignore[arg-type]


def test_diff_tracks_enum_field_changes():
    current = CanonicalUser(primary_email="a@example.com", state=UserState.ACTIVE)
    desired = current.model_copy(update={"state": UserState.SUSPENDED, "suspended": True})

    delta = diff_models("a@example.com", current, desired)

    assert delta.changed_fields == {"state": "suspended", "suspended": True}
