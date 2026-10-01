import math

import pytest

from keddeh_math.q32_32 import composite_warrant, composite_warrant_q32_32, from_q32_32, to_q32_32


def test_to_from_q32_32_round_trip_within_one_ulp():
    value = -2.302585092994046
    fixed = to_q32_32(value)
    assert from_q32_32(fixed) == pytest.approx(value, abs=1 / 2**32)


def test_composite_warrant_matches_direct_float_computation():
    warrants = [0.9, 0.8, 0.7]
    assert composite_warrant(warrants) == pytest.approx(0.994)


def test_composite_warrant_q32_32_corrects_the_documents_hand_typed_integers():
    # Mechanically executed values, contra the document's hand-derived
    # Q1=-9,889,520,384 / Q2=-6,912,504,500 / Q3=-5,171,021,833.
    result = composite_warrant_q32_32([0.9, 0.8, 0.7])
    q1, q2, q3 = result["per_warrant_q32_32"]
    assert q1 == -9_889_527_671
    assert q2 == -6_912_483_199
    assert q3 == -5_171_023_820
    assert result["total_q32_32"] == q1 + q2 + q3


def test_composite_warrant_q32_32_recovers_correct_w():
    result = composite_warrant_q32_32([0.9, 0.8, 0.7])
    assert result["recovered_w"] == pytest.approx(0.994, abs=1e-9)


def test_composite_warrant_q32_32_is_associative_regardless_of_evaluation_order():
    forward = composite_warrant_q32_32([0.9, 0.8, 0.7])["total_q32_32"]
    reversed_order = composite_warrant_q32_32([0.7, 0.8, 0.9])["total_q32_32"]
    assert forward == reversed_order
