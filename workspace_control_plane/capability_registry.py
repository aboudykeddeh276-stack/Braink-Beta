"""Capability registry: the single source of truth for what the control
plane is allowed to do, which adapter performs it, and what governs it.

Callers request a named *capability* (e.g. ``"identity.user.suspend"``);
they never receive a raw Workspace API client or unrestricted OAuth
credential. Each entry records an honest ``SupportState`` — Google does
not expose every Admin Console setting through a public API, and this
registry is where that gap is made explicit rather than silently faked.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SupportState(str, Enum):
    """Whether Google exposes a supported, programmable actuator for this capability."""

    READ_WRITE = "read_write"
    READ_ONLY = "read_only"
    CONSOLE_ONLY = "console_only"
    UNSUPPORTED = "unsupported"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    DESTRUCTIVE = "destructive"


class ApprovalMode(str, Enum):
    NONE = "none"
    SINGLE = "single"
    TWO_PERSON = "two_person"


@dataclass(frozen=True)
class CapabilityDefinition:
    """One row of the capability matrix."""

    capability: str
    adapter: str
    support_state: SupportState
    required_scopes: tuple[str, ...] = ()
    risk: RiskLevel = RiskLevel.LOW
    pre_observation_required: bool = True
    approval_mode: ApprovalMode = ApprovalMode.NONE
    post_conditions: tuple[str, ...] = ()

    def requires_approval(self) -> bool:
        return self.approval_mode is not ApprovalMode.NONE


class RegistrySealedError(Exception):
    """Raised when a capability is registered after the registry was sealed.

    The capability matrix is bootstrap-time configuration, not something a
    running control plane can change about itself. Sealing after startup
    means no code path reachable at runtime — an adapter, an admitted
    intent, a compromised dependency — can promote a capability's support
    state (e.g. CONSOLE_ONLY -> READ_WRITE) after the fact.
    """


class CapabilityRegistry:
    """In-memory capability matrix, keyed by capability name."""

    def __init__(self) -> None:
        self._capabilities: dict[str, CapabilityDefinition] = {}
        self._sealed = False

    def register(self, definition: CapabilityDefinition) -> None:
        if self._sealed:
            raise RegistrySealedError(
                f"registry is sealed; cannot register {definition.capability!r} at runtime"
            )
        self._capabilities[definition.capability] = definition

    def seal(self) -> "CapabilityRegistry":
        """Freeze the registry against further registration. Returns self for chaining."""
        self._sealed = True
        return self

    @property
    def is_sealed(self) -> bool:
        return self._sealed

    def get(self, capability: str) -> CapabilityDefinition:
        try:
            return self._capabilities[capability]
        except KeyError as exc:
            raise KeyError(f"Unknown capability: {capability!r}") from exc

    def is_actuatable(self, capability: str) -> bool:
        definition = self.get(capability)
        return definition.support_state in (SupportState.READ_WRITE, SupportState.READ_ONLY)

    def __iter__(self):
        return iter(self._capabilities.values())

    def __len__(self) -> int:
        return len(self._capabilities)


def build_default_registry() -> CapabilityRegistry:
    """Build the starting capability matrix for the Directory and Licensing
    adapters (R1 + the licensing extension).

    This is deliberately small and honest rather than exhaustive: it
    covers the API surfaces this milestone actually implements, plus one
    CONSOLE_ONLY example (custom branding has no Admin SDK actuator) to
    show how the registry represents a real gap rather than hiding it.
    """
    registry = CapabilityRegistry()

    registry.register(
        CapabilityDefinition(
            capability="identity.user.read",
            adapter="directory",
            support_state=SupportState.READ_ONLY,
            required_scopes=("https://www.googleapis.com/auth/admin.directory.user.readonly",),
            risk=RiskLevel.LOW,
        )
    )
    registry.register(
        CapabilityDefinition(
            capability="identity.user.create",
            adapter="directory",
            support_state=SupportState.READ_WRITE,
            required_scopes=("https://www.googleapis.com/auth/admin.directory.user",),
            risk=RiskLevel.MODERATE,
            approval_mode=ApprovalMode.SINGLE,
            post_conditions=("user_present",),
        )
    )
    registry.register(
        CapabilityDefinition(
            capability="identity.user.update",
            adapter="directory",
            support_state=SupportState.READ_WRITE,
            required_scopes=("https://www.googleapis.com/auth/admin.directory.user",),
            risk=RiskLevel.LOW,
        )
    )
    registry.register(
        CapabilityDefinition(
            capability="identity.user.suspend",
            adapter="directory",
            support_state=SupportState.READ_WRITE,
            required_scopes=("https://www.googleapis.com/auth/admin.directory.user",),
            risk=RiskLevel.MODERATE,
            approval_mode=ApprovalMode.SINGLE,
            post_conditions=("user_suspended",),
        )
    )
    registry.register(
        CapabilityDefinition(
            capability="identity.user.delete",
            adapter="directory",
            support_state=SupportState.READ_WRITE,
            required_scopes=("https://www.googleapis.com/auth/admin.directory.user",),
            risk=RiskLevel.DESTRUCTIVE,
            approval_mode=ApprovalMode.TWO_PERSON,
            post_conditions=(
                "user_absent",
                "owned_data_disposition_verified",
                "licenses_reconciled",
            ),
        )
    )
    registry.register(
        CapabilityDefinition(
            capability="branding.custom_logo",
            adapter="none",
            support_state=SupportState.CONSOLE_ONLY,
        )
    )
    registry.register(
        CapabilityDefinition(
            capability="licensing.read",
            adapter="licensing",
            support_state=SupportState.READ_ONLY,
            required_scopes=("https://www.googleapis.com/auth/apps.licensing",),
            risk=RiskLevel.LOW,
        )
    )
    registry.register(
        CapabilityDefinition(
            capability="licensing.assign",
            adapter="licensing",
            support_state=SupportState.READ_WRITE,
            required_scopes=("https://www.googleapis.com/auth/apps.licensing",),
            risk=RiskLevel.MODERATE,
            approval_mode=ApprovalMode.SINGLE,
            post_conditions=("sku_assigned",),
        )
    )
    registry.register(
        CapabilityDefinition(
            capability="licensing.revoke",
            adapter="licensing",
            support_state=SupportState.READ_WRITE,
            required_scopes=("https://www.googleapis.com/auth/apps.licensing",),
            risk=RiskLevel.MODERATE,
            approval_mode=ApprovalMode.SINGLE,
            post_conditions=("sku_revoked",),
        )
    )

    return registry.seal()
