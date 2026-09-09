"""Executes a registered topic handler and returns the exact computed result.

`ask` never generates a description of the topic -- it runs the real
function registered for it and reports exactly what that function
returned, tagged with whether that computation is backed by a tested,
verified implementation or is explicitly conceptual/illustrative.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from braink_reasoning.registry import TopicRegistry, TopicStatus


@dataclass(frozen=True)
class TopicAnswer:
    topic: str
    status: TopicStatus
    result: Any
    computed_by: str
    inputs: dict[str, Any]


def ask(registry: TopicRegistry, topic: str, **params: Any) -> TopicAnswer:
    handler = registry.get(topic)
    missing = [p for p in handler.required_params if p not in params]
    if missing:
        raise TypeError(
            f"topic {topic!r} requires parameters {handler.required_params}; missing {missing}"
        )
    result = handler.function(**params)
    return TopicAnswer(
        topic=topic,
        status=handler.status,
        result=result,
        computed_by=f"{handler.function.__module__}.{handler.function.__qualname__}",
        inputs=params,
    )
