import pytest

from braink_reasoning.registers.periodic_table import element_count, get_element


def test_all_118_elements_present():
    assert element_count() == 118


def test_lookup_by_symbol():
    element = get_element("Fe")
    assert element == {"atomic_number": 26, "symbol": "Fe", "name": "Iron", "atomic_weight": pytest.approx(55.845)}


def test_lookup_by_symbol_is_case_insensitive():
    assert get_element("fe")["name"] == "Iron"
    assert get_element("FE")["name"] == "Iron"


def test_lookup_by_name_is_case_insensitive():
    assert get_element("hydrogen")["symbol"] == "H"
    assert get_element("HYDROGEN")["symbol"] == "H"


def test_lookup_by_atomic_number():
    assert get_element(79)["symbol"] == "Au"


def test_unknown_identifier_raises_key_error():
    with pytest.raises(KeyError):
        get_element("Unobtainium")


def test_spot_check_well_known_atomic_weights():
    assert get_element("H")["atomic_weight"] == pytest.approx(1.008)
    assert get_element("O")["atomic_weight"] == pytest.approx(15.999)
    assert get_element("Au")["atomic_weight"] == pytest.approx(196.967)
    assert get_element("U")["atomic_weight"] == pytest.approx(238.029)
