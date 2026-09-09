import pytest

from braink_reasoning.registers.lexicon import GLOSSARY, get_term


def test_lookup_is_case_insensitive():
    assert get_term("Ollama")["node_code"] == "N-OLLAMA-001"
    assert get_term("OLLAMA")["node_code"] == "N-OLLAMA-001"


def test_unknown_term_raises_key_error():
    with pytest.raises(KeyError):
        get_term("nonexistent term")


def test_every_entry_has_a_node_code_and_hex_id():
    for term, entry in GLOSSARY.items():
        assert entry.get("node_code"), f"{term} missing node_code"
        assert entry.get("hex_id"), f"{term} missing hex_id"


def test_agent_entries_all_report_active_status():
    for term in ("coding agent", "supervisor agent", "lexicon agent", "cognition agent"):
        assert get_term(term)["status"].startswith("Active")
