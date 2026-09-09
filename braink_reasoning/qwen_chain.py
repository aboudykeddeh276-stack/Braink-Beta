"""The Qwen-derived realised chain from the source report:

    repository -> model -> tokenizer -> chat_template -> tensorize
    -> generate -> decode -> response

Every step function here is a deterministic state-transformation
stand-in over a plain dict. `generate` is explicitly marked
`is_proxy=True`: it does not run Qwen, or any model, inference. This
carries the source report's own stated boundary forward verbatim into
running code -- the point of this chain is to prove the addressing/
transition/receipt/rehydration mechanic works, not to claim model
inference happened. Real model-weight execution would be a separate,
not-yet-realised binding to the `generate` address.
"""

from __future__ import annotations


def _repository(state: dict) -> dict:
    return {**state, "repository": "resolved"}


def _model(state: dict) -> dict:
    return {**state, "model": "loaded"}


def _tokenizer(state: dict) -> dict:
    return {**state, "tokenizer": "attached"}


def _chat_template(state: dict) -> dict:
    return {**state, "chat_template": "applied"}


def _tensorize(state: dict) -> dict:
    return {**state, "tensorize": "stand-in tensor shape recorded"}


def _generate(state: dict) -> dict:
    # PROXY: deterministic state transformation, not Qwen tensor inference.
    return {**state, "generate": "proxy transition executed"}


def _decode(state: dict) -> dict:
    return {**state, "decode": "stand-in token stream decoded"}


def _response(state: dict) -> str:
    return "knowledge becomes thinking and action"


QWEN_DERIVED_STEP_REGISTRY = {
    "repository": _repository,
    "model": _model,
    "tokenizer": _tokenizer,
    "chat_template": _chat_template,
    "tensorize": _tensorize,
    "generate": _generate,
    "decode": _decode,
    "response": _response,
}

QWEN_DERIVED_CHAIN_DEFINITION = {
    "chain_id": "qwen-derived-v1",
    "steps": [
        {"name": "repository", "is_proxy": False, "proxy_note": ""},
        {"name": "model", "is_proxy": False, "proxy_note": ""},
        {"name": "tokenizer", "is_proxy": False, "proxy_note": ""},
        {"name": "chat_template", "is_proxy": False, "proxy_note": ""},
        {"name": "tensorize", "is_proxy": False, "proxy_note": ""},
        {
            "name": "generate",
            "is_proxy": True,
            "proxy_note": (
                "Deterministic state-transformation proxy, not Qwen tensor "
                "inference. Real model-weight execution is a separate, "
                "not-yet-realised binding to this address."
            ),
        },
        {"name": "decode", "is_proxy": False, "proxy_note": ""},
        {"name": "response", "is_proxy": False, "proxy_note": ""},
    ],
}


def build_qwen_derived_chain():
    from braink_reasoning.chain import Chain

    return Chain.from_definition(QWEN_DERIVED_CHAIN_DEFINITION, QWEN_DERIVED_STEP_REGISTRY)
