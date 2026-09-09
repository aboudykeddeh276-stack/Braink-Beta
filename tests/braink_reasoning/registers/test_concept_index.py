import pytest

from braink_reasoning.registers.concept_index import CONCEPT_INDEX, get_concept_tags


def test_lookup_is_case_insensitive():
    assert get_concept_tags("Brain") == ["process:cognition", "system:brain"]
    assert get_concept_tags("BRAIN") == get_concept_tags("brain")


def test_unknown_term_raises_key_error():
    with pytest.raises(KeyError):
        get_concept_tags("nonexistent")


def test_all_13_transcribed_terms_present():
    assert set(CONCEPT_INDEX) == {
        "wood", "plant", "tree", "human", "brain", "fear", "carbon",
        "hydrogen", "oxygen", "cellulose", "lignin", "animal", "feeling",
    }


def test_element_tagged_terms_match_periodic_table_symbols():
    # carbon/hydrogen/oxygen tag as element:C / element:H / element:O --
    # cross-check those symbols actually resolve in the periodic table register.
    from braink_reasoning.registers.periodic_table import get_element

    for term, symbol in (("carbon", "C"), ("hydrogen", "H"), ("oxygen", "O")):
        tag = get_concept_tags(term)[0]
        assert tag == f"element:{symbol}"
        assert get_element(symbol)["symbol"] == symbol
