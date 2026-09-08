"""Theorem 4: M/G/1 queue via the Pollaczek-Khinchine formula.

The correct P-K mean queue length is:

    L_q = lambda^2 * E[S^2] / (2 * (1 - rho))
        = lambda^2 * (sigma^2 + tau_bar^2) / (2 * (1 - rho))

where `tau_bar` is mean service time, `sigma` its standard deviation, and
`rho = lambda * tau_bar` is utilization. The original document's Case B
arithmetic evaluating this formula was wrong (its numerator summed to
~4.43e-9 where the correct value is ~5.45e-9); `mean_queue_length` below
computes it directly so that error class cannot recur.

`mean_queue_length` also raises if `rho >= 1` rather than silently
returning a divergent number, since an unstable queue's backlog grows
without bound and `L_q` is not a meaningful description of that — see
`unstable_backlog_growth_rate` for the right quantity in that regime.
"""

from __future__ import annotations


class UnstableQueueError(ValueError):
    """Raised when utilization rho >= 1: the queue has no steady state."""


def utilization(arrival_rate: float, mean_service_time: float) -> float:
    return arrival_rate * mean_service_time


def mean_queue_length(
    arrival_rate: float, mean_service_time: float, service_time_stddev: float
) -> float:
    """Pollaczek-Khinchine mean number waiting in queue (not in service)."""
    rho = utilization(arrival_rate, mean_service_time)
    if rho >= 1:
        raise UnstableQueueError(f"rho={rho} >= 1: queue is unstable, has no steady state")
    second_moment = service_time_stddev**2 + mean_service_time**2
    return (arrival_rate**2 * second_moment) / (2 * (1 - rho))


def unstable_backlog_growth_rate(arrival_rate: float, mean_service_time: float) -> float:
    """Requests/second of backlog growth when rho > 1 (service rate = 1/mean_service_time)."""
    service_rate = 1 / mean_service_time
    if arrival_rate <= service_rate:
        raise ValueError("queue is stable (arrival_rate <= service_rate); no backlog growth")
    return arrival_rate - service_rate
