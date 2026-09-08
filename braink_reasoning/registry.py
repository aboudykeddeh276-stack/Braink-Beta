"""Topic register: pluggable mapping from a topic string to a real computation.

This is the entry point for "answers by applying math, not generating
tokenised stories": given a topic name and parameters, the router looks
up a registered handler and executes it. It does not generate text
describing the topic, and it does not guess when nothing is registered
for a topic -- see `UnknownTopicError`.

Unlike `workspace_control_plane.capability_registry.CapabilityRegistry`,
this registry is NOT sealed. That registry protects a fixed, security-
sensitive capability matrix from runtime tampering; this one is meant to
grow as more registers of data and verified computation are added over
time (e.g. a lexicon register, a manuscript-analysis register), so
locking it at bootstrap would work against its purpose.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class TopicStatus(str, Enum):
    VERIFIED = "verified"  # backed by a mechanically executed, tested computation
    CONCEPTUAL = "conceptual"  # illustrative; inputs are assumed, not measured


@dataclass(frozen=True)
class TopicHandler:
    topic: str
    function: Callable[..., Any]
    status: TopicStatus
    description: str
    required_params: tuple[str, ...]


class UnknownTopicError(KeyError):
    """Raised when a topic has no registered handler. Never silently guessed."""


class TopicRegistry:
    """In-memory, mutable topic -> handler map. Deliberately not sealed."""

    def __init__(self) -> None:
        self._handlers: dict[str, TopicHandler] = {}

    def register(self, handler: TopicHandler) -> None:
        self._handlers[handler.topic] = handler

    def get(self, topic: str) -> TopicHandler:
        try:
            return self._handlers[topic]
        except KeyError as exc:
            raise UnknownTopicError(
                f"no registered computation for topic {topic!r}; "
                f"known topics: {self.topics()}"
            ) from exc

    def topics(self) -> list[str]:
        return sorted(self._handlers)

    def __contains__(self, topic: str) -> bool:
        return topic in self._handlers
