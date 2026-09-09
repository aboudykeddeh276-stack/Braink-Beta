"""Topic reference graph: literal mechanics for "to understand X, first understand Y and Z".

This is deterministic graph traversal over each topic's declared
`references` -- not similarity search, not inference about what might be
related. A topic either declares what it references or it doesn't; this
walks exactly those declared edges and nothing else. The natural real
use case is a dictionary/lexicon register, where a definition uses other
words that may themselves need defining -- same mechanism, no special
casing for that data once it's registered as topics with `references`.
"""

from __future__ import annotations

from braink_reasoning.registry import TopicRegistry


class CircularReferenceError(ValueError):
    """Raised when a topic's reference chain loops back on itself."""


def resolve_understanding_path(registry: TopicRegistry, topic: str) -> list[str]:
    """Return topics in the order they should be understood.

    Prerequisites come before the topics that reference them; `topic`
    itself is always last. A topic referenced from multiple places
    appears exactly once, at the earliest point its prerequisites are
    satisfied (diamond dependencies collapse rather than duplicate).
    Raises `UnknownTopicError` (via `registry.get`) for any referenced
    topic that isn't registered, and `CircularReferenceError` if a
    reference chain loops back on a topic still being resolved.
    """
    order: list[str] = []
    resolved: set[str] = set()
    in_progress: set[str] = set()

    def visit(name: str, path: tuple[str, ...]) -> None:
        if name in resolved:
            return
        if name in in_progress:
            cycle = " -> ".join((*path, name))
            raise CircularReferenceError(f"circular topic reference: {cycle}")
        handler = registry.get(name)
        in_progress.add(name)
        for reference in handler.references:
            visit(reference, (*path, name))
        in_progress.discard(name)
        resolved.add(name)
        order.append(name)

    visit(topic, ())
    return order
