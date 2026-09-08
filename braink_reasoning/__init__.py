"""Braink reasoning core: answers by running verified computation, not generating text.

Given a topic and parameters, `ask` looks up a registered handler and
executes it. If nothing is registered for a topic, it raises
(`UnknownTopicError`) rather than guessing or narrating. There is no
language model, tokenizer, or generative text step anywhere in this
package -- a query either resolves to a real function that gets
executed, or it doesn't resolve at all.

`TopicRegistry` is intentionally not sealed (contrast with
`workspace_control_plane.capability_registry.CapabilityRegistry`): this
is the first of what's meant to be several registers of data and
verified computation, and is designed to be extended, not locked down.
"""

from braink_reasoning.answer import TopicAnswer, ask
from braink_reasoning.chain import (
    Chain,
    ChainExecutionResult,
    ChainStep,
    StepReceipt,
    verify_receipt_chain,
)
from braink_reasoning.graph import CircularReferenceError, resolve_understanding_path
from braink_reasoning.registry import TopicHandler, TopicRegistry, TopicStatus, UnknownTopicError
from braink_reasoning.topics import build_default_registry

__all__ = [
    "TopicAnswer",
    "ask",
    "TopicHandler",
    "TopicRegistry",
    "TopicStatus",
    "UnknownTopicError",
    "build_default_registry",
    "resolve_understanding_path",
    "CircularReferenceError",
    "Chain",
    "ChainStep",
    "ChainExecutionResult",
    "StepReceipt",
    "verify_receipt_chain",
]
