import pytest

from keddeh_math.queueing import (
    UnstableQueueError,
    mean_queue_length,
    unstable_backlog_growth_rate,
    utilization,
)


def test_utilization_is_arrival_rate_times_service_time():
    assert utilization(1000, 0.002) == pytest.approx(2.0)


def test_unstable_queue_raises_instead_of_returning_nonsense():
    with pytest.raises(UnstableQueueError):
        mean_queue_length(arrival_rate=1000, mean_service_time=0.002, service_time_stddev=0.001)


def test_backlog_growth_rate_for_unstable_queue():
    rate = unstable_backlog_growth_rate(arrival_rate=1000, mean_service_time=0.002)
    assert rate == pytest.approx(500.0)


def test_mean_queue_length_corrects_the_documents_arithmetic_error():
    # The original document claimed Lq ~= 2.21e-9 from a numerator it
    # computed as ~4.43e-9. The correct P-K numerator for these inputs is
    # ~5.45e-9, giving Lq ~= 2.72e-9 -- not 2.21e-9.
    lq = mean_queue_length(arrival_rate=0.033, mean_service_time=0.002, service_time_stddev=0.001)
    assert lq == pytest.approx(2.7227e-9, rel=1e-3)
    assert lq != pytest.approx(2.21e-9, rel=1e-2)


def test_mean_queue_length_is_negligible_for_low_utilization():
    lq = mean_queue_length(arrival_rate=0.033, mean_service_time=0.002, service_time_stddev=0.001)
    assert lq < 1e-8
