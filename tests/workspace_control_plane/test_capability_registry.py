import pytest

from workspace_control_plane.capability_registry import (
    CapabilityDefinition,
    CapabilityRegistry,
    RegistrySealedError,
    SupportState,
    build_default_registry,
)


def test_default_registry_is_sealed():
    registry = build_default_registry()

    assert registry.is_sealed is True


def test_registering_onto_a_sealed_registry_raises():
    registry = build_default_registry()

    with pytest.raises(RegistrySealedError):
        registry.register(
            CapabilityDefinition(
                capability="branding.custom_logo",
                adapter="none",
                support_state=SupportState.READ_WRITE,
            )
        )


def test_sealing_does_not_change_existing_entries():
    registry = build_default_registry()

    assert registry.get("branding.custom_logo").support_state is SupportState.CONSOLE_ONLY


def test_unsealed_registry_accepts_registration():
    registry = CapabilityRegistry()

    registry.register(
        CapabilityDefinition(
            capability="test.capability",
            adapter="none",
            support_state=SupportState.READ_ONLY,
        )
    )

    assert registry.is_sealed is False
    assert registry.get("test.capability").support_state is SupportState.READ_ONLY


def test_seal_returns_self_for_chaining():
    registry = CapabilityRegistry()

    result = registry.seal()

    assert result is registry
    assert registry.is_sealed is True
