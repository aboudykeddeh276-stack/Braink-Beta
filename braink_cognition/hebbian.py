"""Signed Hebbian edge routing over a directed graph (SEC-03 / WP01).

"Co-occurring concepts reinforce directed topological edges via signed
Hebbian plasticity, making learning a process of structural network
routing rather than opaque weight matrix tuning."

Edge weights are bounded to (-1, 1) and never collapse sign information:
reinforcing a POSITIVE co-occurrence and a NEGATIVE (inhibitory)
co-occurrence push the weight in opposite directions rather than both
being folded into an unsigned magnitude.
"""

from __future__ import annotations

from enum import Enum


class Polarity(Enum):
    POSITIVE = 1
    NEGATIVE = -1


class HebbianGraph:
    """Directed, signed, bounded-weight graph updated by Hebbian reinforcement."""

    def __init__(self, learning_rate: float = 0.1) -> None:
        if not 0 < learning_rate <= 1:
            raise ValueError("learning_rate must be in (0, 1]")
        self._learning_rate = learning_rate
        self._weights: dict[tuple[str, str], float] = {}

    def weight(self, source: str, target: str) -> float:
        return self._weights.get((source, target), 0.0)

    def reinforce(self, source: str, target: str, polarity: Polarity) -> float:
        """Move the directed edge source->target toward +1 (POSITIVE) or
        -1 (NEGATIVE), asymptotically, so repeated reinforcement saturates
        rather than diverging. Returns the new weight.
        """
        current = self.weight(source, target)
        target_value = float(polarity.value)
        updated = current + self._learning_rate * (target_value - current)
        self._weights[(source, target)] = updated
        return updated

    def edges(self) -> dict[tuple[str, str], float]:
        return dict(self._weights)
