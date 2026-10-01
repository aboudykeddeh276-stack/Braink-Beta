import pytest

from braink_reasoning.registers.compounds import COMPOUNDS, constituent_elements, get_compound


def test_water_matches_source_spreadsheet():
    water = get_compound("water")
    assert water["formula"] == "H2O"
    assert water["molar_mass_g_per_mol"] == pytest.approx(18.015)
    assert water["composition"] == {"H": 2, "O": 1}


def test_lookup_is_case_and_space_insensitive():
    assert get_compound("Sodium Chloride")["formula"] == "NaCl"
    assert get_compound("sodium_chloride")["formula"] == "NaCl"


def test_sodium_hydroxide_formula_was_corrected_not_reproduced():
    # Source spreadsheet had "10^-22 electron volt" in this cell -- a
    # transcription defect, not real data.
    assert get_compound("sodium_hydroxide")["formula"] == "NaOH"


def test_unknown_compound_raises_key_error_listing_known_ones():
    with pytest.raises(KeyError, match="water"):
        get_compound("unobtainium")


def test_constituent_elements_matches_composition():
    assert constituent_elements("glucose") == ["C", "H", "O"]


def test_every_registered_compound_has_a_nonempty_composition():
    for name, entry in COMPOUNDS.items():
        assert entry["composition"], f"{name} has no composition data"
