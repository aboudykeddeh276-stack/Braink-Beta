"""Default topic registrations wrapping keddeh_math's verified computations.

This is the first register in the system: six topics, each backed
directly by a tested function in `keddeh_math`. Future registers (a
lexicon, a manuscript-derived register, etc.) are added the same way --
build a `TopicRegistry`, call `.register(...)` with real callables, and
merge it into whatever registry `ask()` is called against. Nothing here
is a placeholder or a stub function; every handler is the same code
exercised by `keddeh_math`'s test suite.
"""

from __future__ import annotations

from keddeh_math.landauer import power as _landauer_power
from keddeh_math.q32_32 import composite_warrant_q32_32 as _composite_warrant_q32_32
from keddeh_math.queueing import mean_queue_length as _mean_queue_length
from keddeh_math.rule110 import run as _rule110_run
from keddeh_math.search_partition import (
    collision_probability_exact as _collision_probability_exact,
)
from keddeh_math.shannon import channel_capacity_bps as _channel_capacity_bps

from braink_reasoning.registry import TopicHandler, TopicRegistry, TopicStatus


def build_default_registry() -> TopicRegistry:
    registry = TopicRegistry()

    registry.register(
        TopicHandler(
            topic="collision_probability",
            function=_collision_probability_exact,
            status=TopicStatus.VERIFIED,
            description="Exact birthday-bound collision probability for num_samples over space_size.",
            required_params=("num_samples", "space_size"),
        )
    )
    registry.register(
        TopicHandler(
            topic="queue_depth",
            function=_mean_queue_length,
            status=TopicStatus.VERIFIED,
            description="M/G/1 Pollaczek-Khinchine mean queue length.",
            required_params=("arrival_rate", "mean_service_time", "service_time_stddev"),
        )
    )
    registry.register(
        TopicHandler(
            topic="channel_capacity",
            function=_channel_capacity_bps,
            status=TopicStatus.VERIFIED,
            description="Shannon-Hartley channel capacity in bits/second.",
            required_params=("bandwidth_hz", "snr_linear"),
        )
    )
    registry.register(
        TopicHandler(
            topic="bit_erasure_power",
            function=_landauer_power,
            status=TopicStatus.CONCEPTUAL,
            description=(
                "Landauer-limit power draw for a given bits-per-cycle and frequency. "
                "CONCEPTUAL: bits_per_cycle is caller-supplied, not measured from a real system."
            ),
            required_params=("bits_per_cycle", "frequency_hz", "temperature_kelvin"),
        )
    )
    registry.register(
        TopicHandler(
            topic="rule110_generations",
            function=_rule110_run,
            status=TopicStatus.VERIFIED,
            description="Runs the Rule 110 cellular automaton for N generations from an initial state.",
            required_params=("initial_state", "generations"),
        )
    )
    registry.register(
        TopicHandler(
            topic="composite_warrant",
            function=_composite_warrant_q32_32,
            status=TopicStatus.VERIFIED,
            description="Q32.32 fixed-point composite warrant across independent witnesses.",
            required_params=("warrants",),
        )
    )

    return registry
