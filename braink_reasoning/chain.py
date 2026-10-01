"""IL-LLM literal thinking/acting chain, realized as executable code.

Implements the primitive described in
BRAINK_ILLLM_LEXICON_CHAIN_REALISATION_REPORT_V1.md:

    SOURCE -> LEXICON DEFINE -> IL-LLM ADDRESS -> FOLD/COLLAPSE
    -> TRANSITION -> CHAIN -> EXECUTION -> RECEIPT

A `Chain` is an ordered sequence of named, addressed `ChainStep`s.
Executing it runs each step's function in order and produces a
hash-chained `StepReceipt` per step -- the same parent-hash-linking
pattern as `workspace_control_plane.receipts.ReceiptChain`, reimplemented
standalone here since these are separate packages/branches.

Rehydration: `Chain.to_definition()` persists step names, proxy flags,
and notes (not the functions themselves -- those aren't serializable).
`Chain.from_definition()` reconstructs a chain from that definition plus
a step-function registry (a separate process only needs the registry,
not the original Chain object) and re-executing it against the same
input reproduces identical receipts, which is the actual, checkable
content of "rehydration" rather than an assertion of it.

Honesty boundary, carried over directly from the source report: a step
function is whatever the caller actually supplies. Nothing in this
module claims a step labeled "generate" performs real model inference
unless the caller's function actually does that -- `ChainStep.is_proxy`
exists specifically so a deterministic stand-in step is labeled as one,
not silently presented as equivalent to the real thing.

The source report's addresses are a 7-component (N,R,L,G,T,K,P) scheme
whose field semantics were never specified beyond the letters
themselves. Rather than invent meanings for them, `ChainStep.address`
is a deterministic hash of (chain_id, step_name) -- this satisfies what
the report actually requires ("assigned a permanent address") without
fabricating a spec that was never given.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable


def _hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class ChainStep:
    """One addressed step in a thinking/acting chain."""

    name: str
    function: Callable[[Any], Any]
    is_proxy: bool = False
    proxy_note: str = ""

    def address(self, chain_id: str) -> str:
        return _hash({"chain_id": chain_id, "name": self.name})


@dataclass(frozen=True)
class StepReceipt:
    step_name: str
    address: str
    input_hash: str
    output_hash: str
    is_proxy: bool
    previous_receipt_hash: str | None

    @property
    def receipt_hash(self) -> str:
        canonical = {
            "step_name": self.step_name,
            "address": self.address,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "is_proxy": self.is_proxy,
            "previous_receipt_hash": self.previous_receipt_hash,
        }
        return _hash(canonical)


@dataclass(frozen=True)
class ChainExecutionResult:
    chain_id: str
    receipts: tuple[StepReceipt, ...]
    final_output: Any

    @property
    def terminal_receipt_hash(self) -> str:
        return self.receipts[-1].receipt_hash

    def rehydration_summary(self) -> dict:
        addresses = [r.address for r in self.receipts]
        return {
            "chain_id": self.chain_id,
            "steps": len(self.receipts),
            "unique_addresses": len(set(addresses)) == len(addresses),
            "first": self.receipts[0].step_name,
            "terminal": self.receipts[-1].step_name,
            "terminal_receipt_hash": self.terminal_receipt_hash,
        }


def verify_receipt_chain(receipts: tuple[StepReceipt, ...]) -> bool:
    """Confirm each receipt links to the one before it (same check as
    workspace_control_plane.receipts.verify_chain, reimplemented here)."""
    if not receipts:
        return True
    if receipts[0].previous_receipt_hash is not None:
        return False
    for prev, curr in zip(receipts, receipts[1:]):
        if curr.previous_receipt_hash != prev.receipt_hash:
            return False
    return True


class Chain:
    """An ordered, executable, rehydratable sequence of addressed steps."""

    def __init__(self, chain_id: str, steps: list[ChainStep]) -> None:
        if not steps:
            raise ValueError("a chain needs at least one step")
        self.chain_id = chain_id
        self.steps = tuple(steps)

    def execute(self, initial_input: Any) -> ChainExecutionResult:
        """Run every step in order, producing a hash-chained receipt per step."""
        receipts: list[StepReceipt] = []
        value = initial_input
        previous_hash: str | None = None
        for step in self.steps:
            input_hash = _hash(value)
            value = step.function(value)
            output_hash = _hash(value)
            receipt = StepReceipt(
                step_name=step.name,
                address=step.address(self.chain_id),
                input_hash=input_hash,
                output_hash=output_hash,
                is_proxy=step.is_proxy,
                previous_receipt_hash=previous_hash,
            )
            receipts.append(receipt)
            previous_hash = receipt.receipt_hash
        return ChainExecutionResult(chain_id=self.chain_id, receipts=tuple(receipts), final_output=value)

    def proxy_steps(self) -> list[str]:
        """Step names whose function is documented as a non-real stand-in."""
        return [s.name for s in self.steps if s.is_proxy]

    def to_definition(self) -> dict:
        """Persistable form: step names and proxy metadata, not functions."""
        return {
            "chain_id": self.chain_id,
            "steps": [
                {"name": s.name, "is_proxy": s.is_proxy, "proxy_note": s.proxy_note}
                for s in self.steps
            ],
        }

    @classmethod
    def from_definition(cls, definition: dict, step_registry: dict[str, Callable]) -> "Chain":
        """Rehydrate a chain from a persisted definition plus a step-function
        registry -- this is what a separate process needs to reconstruct and
        re-execute the chain, per the source report's rehydration claim."""
        steps = [
            ChainStep(
                name=s["name"],
                function=step_registry[s["name"]],
                is_proxy=s["is_proxy"],
                proxy_note=s.get("proxy_note", ""),
            )
            for s in definition["steps"]
        ]
        return cls(chain_id=definition["chain_id"], steps=steps)
