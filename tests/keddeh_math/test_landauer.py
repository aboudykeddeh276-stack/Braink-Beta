import pytest

from keddeh_math.landauer import bit_energy, power, total_dissipation


def test_bit_energy_at_300k_matches_known_value():
    assert bit_energy(300.0) == pytest.approx(2.870978885e-21, rel=1e-6)


def test_total_dissipation_scales_linearly_with_bit_count():
    single = bit_energy(300.0)
    assert total_dissipation(1000, 300.0) == pytest.approx(single * 1000, rel=1e-12)


def test_power_scales_with_frequency():
    dissipation = total_dissipation(102_400_000, 300.0)
    assert power(102_400_000, 100.0, 300.0) == pytest.approx(dissipation * 100, rel=1e-12)


def test_higher_temperature_increases_bit_energy():
    assert bit_energy(310.0) > bit_energy(300.0)
