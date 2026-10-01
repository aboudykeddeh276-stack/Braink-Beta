"""Theorem 5: Shannon-Hartley channel capacity.

Correctly applied here, as it was in the original document. The channel
parameters (bandwidth, SNR) and any downstream latency budget are always
caller-supplied — this module makes no claim about what a real network
actually measures. Callers should tag such inputs ASSUMED unless they
come from an actual measurement.
"""

from __future__ import annotations

import math


def snr_db_to_linear(snr_db: float) -> float:
    return 10 ** (snr_db / 10)


def channel_capacity_bps(bandwidth_hz: float, snr_linear: float) -> float:
    """Shannon-Hartley capacity in bits/second."""
    return bandwidth_hz * math.log2(1 + snr_linear)


def transit_latency_seconds(frame_bits: int, capacity_bps: float) -> float:
    return frame_bits / capacity_bps


def multi_hop_latency_seconds(
    frame_bits: int, capacity_bps: float, hops: int, per_hop_processing_seconds: float
) -> float:
    """Total latency across `hops` links, each adding wire transit plus fixed processing time."""
    per_hop = transit_latency_seconds(frame_bits, capacity_bps) + per_hop_processing_seconds
    return hops * per_hop
