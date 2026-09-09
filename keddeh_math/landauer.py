"""Theorem 3: Landauer thermodynamic limit on bit erasure.

The physics (Landauer, 1961) is real and the formula is applied correctly
here. What this module does NOT do is validate any particular system's
efficiency: `total_dissipation` and `power` take `bits_per_cycle` and
`frequency_hz` as explicit caller-supplied parameters. If those numbers
are not measured from a real, specified register layout, callers must
label the result CONCEPTUAL — this module has no way to know, and won't
pretend otherwise by hard-coding a bit count.
"""

from __future__ import annotations

import math

BOLTZMANN_CONSTANT_J_PER_K = 1.380649e-23  # exact SI value


def bit_energy(temperature_kelvin: float) -> float:
    """Minimum energy (Joules) to erase/overwrite one bit at the given temperature."""
    return BOLTZMANN_CONSTANT_J_PER_K * temperature_kelvin * math.log(2)


def total_dissipation(bits_per_cycle: int, temperature_kelvin: float) -> float:
    """Minimum energy (Joules) per cycle for a given, caller-specified bit count."""
    return bits_per_cycle * bit_energy(temperature_kelvin)


def power(bits_per_cycle: int, frequency_hz: float, temperature_kelvin: float) -> float:
    """Minimum sustained power (Watts) at a given cycle frequency."""
    return total_dissipation(bits_per_cycle, temperature_kelvin) * frequency_hz
