import pytest

from keddeh_math.shannon import (
    channel_capacity_bps,
    multi_hop_latency_seconds,
    snr_db_to_linear,
    transit_latency_seconds,
)


def test_snr_30db_is_1000_linear():
    assert snr_db_to_linear(30) == pytest.approx(1000.0)


def test_channel_capacity_matches_documents_figure():
    c = channel_capacity_bps(20e6, 1000)
    assert c == pytest.approx(199_344_525, rel=1e-6)


def test_transit_latency_matches_documents_figure():
    c = channel_capacity_bps(20e6, 1000)
    latency_us = transit_latency_seconds(1440, c) * 1e6
    assert latency_us == pytest.approx(7.2237, rel=1e-3)


def test_multi_hop_latency_matches_documents_figure():
    c = channel_capacity_bps(20e6, 1000)
    total_us = multi_hop_latency_seconds(1440, c, hops=11, per_hop_processing_seconds=90e-6) * 1e6
    assert total_us == pytest.approx(1069.46, rel=1e-3)
