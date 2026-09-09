import math

import pytest

from keddeh_math.search_partition import (
    collision_probability_approx,
    collision_probability_exact,
    partition,
    verify_disjoint_and_exhaustive,
)


def test_partition_is_disjoint_and_exhaustive_for_evenly_divisible_space():
    parts = partition(space_size=1000, num_workers=10)
    assert verify_disjoint_and_exhaustive(parts, 1000)
    assert all(p.size == 100 for p in parts)


def test_partition_distributes_remainder_across_first_workers():
    parts = partition(space_size=1003, num_workers=10)
    assert verify_disjoint_and_exhaustive(parts, 1003)
    sizes = [p.size for p in parts]
    assert sizes.count(101) == 3
    assert sizes.count(100) == 7


def test_partition_rejects_more_workers_than_space():
    with pytest.raises(ValueError):
        partition(space_size=5, num_workers=10)


def test_collision_probability_32bit_matches_known_value():
    # Mechanically reproduces the document's own 32-bit scenario:
    # N=100_000 samples over a 2^32 space.
    p = collision_probability_approx(100_000, 2**32)
    assert p == pytest.approx(0.6878085, abs=1e-4)


def test_collision_probability_exact_and_approx_agree_for_small_x():
    # For small x = n(n-1)/2m, the exponential approximation should be close
    # to the exact log1p-based computation.
    exact = collision_probability_exact(100_000, 2**64)
    approx = collision_probability_approx(100_000, 2**64)
    assert exact == pytest.approx(approx, rel=1e-3)


def test_collision_probability_is_not_literally_zero_even_for_disjoint_partitions():
    # Disjoint partitioning eliminates collision BETWEEN assigned ranges by
    # construction, but this function models the unpartitioned baseline and
    # must never report exactly 0.0 for a nonzero sample count.
    p = collision_probability_exact(2, 2**64)
    assert 0 < p < 1e-15
