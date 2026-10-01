"""Theorem 6: Q32.32 fixed-point log-domain consilience.

This is the theorem whose entire thesis is "bit-exact, no drift" — so it
is the one place where hand-derived intermediate integers are least
acceptable. Every function here is a plain, direct computation; the
associated tests assert against values computed by this same code, and
the mechanical audit (see repo history) already showed by how much the
original document's hand-typed integers were actually off:
    Q1: off by ~7,287   Q2: off by ~21,301   Q3: off by ~1,987
None of those errors were large enough to change the recovered W to
displayed precision, but "close enough by luck" is exactly what a
bit-exact-consensus theorem cannot rely on.
"""

from __future__ import annotations

import math

SCALE = 2**32  # Q32.32: 32 integer bits, 32 fractional bits


def to_q32_32(value: float) -> int:
    """Convert a float to its Q32.32 fixed-point integer representation (floor)."""
    return math.floor(SCALE * value)


def from_q32_32(fixed: int) -> float:
    return fixed / SCALE


def composite_warrant(warrants: list[float]) -> float:
    """W = 1 - product(1 - w_k) computed directly in floating point."""
    product = 1.0
    for w in warrants:
        product *= 1 - w
    return 1 - product


def composite_warrant_q32_32(warrants: list[float]) -> dict:
    """Compute the same composite warrant via Q32.32 fixed-point log-domain summation.

    Returns every intermediate value so a caller (or a report) can present
    machine-computed integers directly rather than re-deriving them by hand.
    """
    per_warrant_q = [to_q32_32(math.log(1 - w)) for w in warrants]
    total_q = sum(per_warrant_q)
    ln_one_minus_w = from_q32_32(total_q)
    recovered_w = 1 - math.exp(ln_one_minus_w)
    return {
        "per_warrant_q32_32": per_warrant_q,
        "total_q32_32": total_q,
        "ln_one_minus_w": ln_one_minus_w,
        "recovered_w": recovered_w,
    }
