"""Shared status lanes for IL-LLM governance."""

STATUS_LANES = {
    "authored_definition",
    "internal_coherence",
    "theorem_state",
    "simulation_support",
    "empirical_validation",
    "pending",
    "blocked",
}


def is_valid_status(status: str) -> bool:
    """Return True when a claim/evidence status is part of the governance contract."""
    return status in STATUS_LANES

