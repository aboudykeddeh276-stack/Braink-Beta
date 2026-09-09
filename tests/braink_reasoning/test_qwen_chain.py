"""Mechanically checks this implementation reproduces what
BRAINK_ILLLM_LEXICON_CHAIN_REALISATION_REPORT_V1.md documents, rather
than just asserting that it does."""

from braink_reasoning.qwen_chain import build_qwen_derived_chain


def test_chain_has_the_documented_eight_steps_in_order():
    chain = build_qwen_derived_chain()
    assert [s.name for s in chain.steps] == [
        "repository", "model", "tokenizer", "chat_template",
        "tensorize", "generate", "decode", "response",
    ]


def test_only_generate_is_marked_proxy_matching_the_reports_boundary():
    chain = build_qwen_derived_chain()
    assert chain.proxy_steps() == ["generate"]


def test_execution_reproduces_the_reports_documented_terminal_result():
    chain = build_qwen_derived_chain()
    result = chain.execute({"source": "raw input"})
    assert result.final_output == "knowledge becomes thinking and action"


def test_rehydration_summary_matches_the_reports_documented_values():
    chain = build_qwen_derived_chain()
    result = chain.execute({"source": "raw input"})
    summary = result.rehydration_summary()
    assert summary["steps"] == 8
    assert summary["unique_addresses"] is True
    assert summary["first"] == "repository"
    assert summary["terminal"] == "response"


def test_rehydrating_from_persisted_definition_reproduces_identical_receipts():
    from braink_reasoning.chain import Chain
    from braink_reasoning.qwen_chain import QWEN_DERIVED_CHAIN_DEFINITION, QWEN_DERIVED_STEP_REGISTRY

    original = build_qwen_derived_chain()
    original_result = original.execute({"source": "raw input"})

    rehydrated = Chain.from_definition(QWEN_DERIVED_CHAIN_DEFINITION, QWEN_DERIVED_STEP_REGISTRY)
    rehydrated_result = rehydrated.execute({"source": "raw input"})

    assert rehydrated_result.terminal_receipt_hash == original_result.terminal_receipt_hash
