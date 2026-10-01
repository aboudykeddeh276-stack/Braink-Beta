"""Theorem 2: disjoint search-space partitioning and the birthday bound it replaces.

`partition` gives every worker a non-overlapping slice of a search space by
construction (set membership, not probability) — this is the same
principle as Bitcoin Stratum's extranonce1/extranonce2 split. It is a
correct, standard technique, not a novel one.

`collision_probability` computes the birthday-bound collision probability
for the *unpartitioned* baseline, both exactly (via log1p summation, no
overflow) and via the small-x exponential approximation the original
document used, so the two can be compared directly. Note what
partitioning actually buys you: assigning disjoint index ranges makes
collision *between workers' assigned ranges* impossible by construction.
It does not make hash collisions (e.g. two distinct SHA-256 inputs
producing the same digest) impossible — that probability is bounded by
SHA-256's collision resistance (~2^-128), not zero. Never state a
cryptographic near-certainty as exactly 0.0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Partition:
    worker_id: int
    start: int
    end: int  # exclusive

    @property
    def size(self) -> int:
        return self.end - self.start


def partition(space_size: int, num_workers: int) -> list[Partition]:
    """Split `[0, space_size)` into `num_workers` disjoint, contiguous, exhaustive ranges."""
    if num_workers <= 0:
        raise ValueError("num_workers must be positive")
    if space_size < num_workers:
        raise ValueError("space_size must be at least num_workers")

    base, remainder = divmod(space_size, num_workers)
    partitions = []
    cursor = 0
    for worker_id in range(num_workers):
        size = base + (1 if worker_id < remainder else 0)
        partitions.append(Partition(worker_id=worker_id, start=cursor, end=cursor + size))
        cursor += size
    return partitions


def verify_disjoint_and_exhaustive(partitions: list[Partition], space_size: int) -> bool:
    """Mechanically confirm zero overlap and full coverage, rather than asserting it."""
    ordered = sorted(partitions, key=lambda p: p.start)
    if ordered[0].start != 0 or ordered[-1].end != space_size:
        return False
    for prev, curr in zip(ordered, ordered[1:]):
        if prev.end != curr.start:
            return False
    return True


def collision_probability_exact(num_samples: int, space_size: int) -> float:
    """Exact birthday-bound collision probability via log1p summation (no overflow).

    Uses expm1 rather than `1 - exp(x)`: for very small collision
    probabilities (e.g. a handful of samples over a 2^64 space), `exp(x)`
    rounds to exactly 1.0 in floating point, which would silently collapse
    a genuinely nonzero probability to a reported 0.0.
    """
    log_p_no_collision = sum(
        math.log1p(-k / space_size) for k in range(num_samples)
    )
    return -math.expm1(log_p_no_collision)


def collision_probability_approx(num_samples: int, space_size: int) -> float:
    """Small-x exponential approximation: 1 - exp(-n(n-1) / (2m))."""
    x = num_samples * (num_samples - 1) / (2 * space_size)
    return -math.expm1(-x)
