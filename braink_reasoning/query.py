"""Single entry point tying the registry, reference graph, and answer
execution together into one usable call.

`explain` is what makes this a system instead of three separate APIs a
caller has to know how to combine: given a topic and its parameters, it
resolves what needs to be understood first (`resolve_understanding_path`),
executes the real computation (`ask`), and returns both -- the same
information a human would want when asking "what is X and what do I
need to know first," produced mechanically rather than composed by hand
each time.
"""

from __future__ import annotations

from typing import Any

from braink_reasoning.answer import ask
from braink_reasoning.graph import resolve_understanding_path
from braink_reasoning.registry import TopicRegistry


def explain(registry: TopicRegistry, topic: str, **params: Any) -> dict:
    """Resolve prerequisites and execute `topic`, in one call.

    Raises the same errors `ask` and `resolve_understanding_path` would
    (UnknownTopicError, CircularReferenceError, TypeError for missing
    params) -- this function composes them, it doesn't hide their
    failure modes.
    """
    prerequisites = resolve_understanding_path(registry, topic)[:-1]  # exclude topic itself
    answer = ask(registry, topic, **params)
    return {
        "topic": topic,
        "prerequisites": prerequisites,
        "status": answer.status.value,
        "computed_by": answer.computed_by,
        "result": answer.result,
    }
