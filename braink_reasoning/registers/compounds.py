"""Chemistry compound register: transcribed from the source spreadsheet.

Data comes from two tables in the "Periodic Table" sheet of the user's
workbook (physical properties: formula, molar mass, atomic composition,
phase transitions; and classification: acid/base strength, pH, color) --
translated from Arabic and merged by compound, not fabricated or
extrapolated.

One transcription defect in the source was corrected rather than
reproduced: the source row for sodium hydroxide had "10^-22 electron
volt" (a physics unit) in its formula cell where "NaOH" belongs -- a
data-entry error, not a value to preserve. `SODIUM_HYDROXIDE_FORMULA_FIX`
documents it.
"""

from __future__ import annotations

SODIUM_HYDROXIDE_FORMULA_FIX = (
    "Source spreadsheet's 'formula' cell for sodium hydroxide read "
    "'10^-22 electron volt' -- corrected here to NaOH."
)

COMPOUNDS: dict[str, dict] = {
    "water": {
        "arabic_name": "ماء",
        "formula": "H2O",
        "molar_mass_g_per_mol": 18.015,
        "composition": {"H": 2, "O": 1},
        "phase_transitions": ["solid", "liquid", "gas"],
        "classification": "neutral",
        "ph_level": 7,
        "color": "green",
    },
    "carbon_dioxide": {
        "arabic_name": "ثاني أكسيد الكربون",
        "formula": "CO2",
        "molar_mass_g_per_mol": 44.009,
        "composition": {"C": 1, "O": 2},
        "phase_transitions": ["solid", "gas"],
        "classification": None,
        "ph_level": None,
        "color": None,
    },
    "glucose": {
        "arabic_name": "الجلوكوز",
        "formula": "C6H12O6",
        "molar_mass_g_per_mol": 180.156,
        "composition": {"C": 6, "H": 12, "O": 6},
        "phase_transitions": ["solid", "liquid"],
        "classification": None,
        "ph_level": None,
        "color": None,
    },
    "sodium_chloride": {
        "arabic_name": "كلوريد الصوديوم",
        "formula": "NaCl",
        "molar_mass_g_per_mol": 58.44,
        "composition": {"Na": 1, "Cl": 1},
        "phase_transitions": ["solid", "liquid", "gas"],
        "classification": "neutral salt",
        "ph_level": 7,
        "color": "green",
    },
    "hydrochloric_acid": {
        "arabic_name": "حمض الهيدروكلوريك",
        "formula": "HCl",
        "molar_mass_g_per_mol": 36.46,
        "composition": {"H": 1, "Cl": 1},
        "phase_transitions": ["gas", "liquid (aqueous)"],
        "classification": "strong acid",
        "ph_level": 1,
        "color": "red",
    },
    "sodium_hydroxide": {
        "arabic_name": "هيدروكسيد الصوديوم",
        "formula": "NaOH",  # see SODIUM_HYDROXIDE_FORMULA_FIX
        "molar_mass_g_per_mol": 39.997,
        "composition": {"Na": 1, "O": 1, "H": 1},
        "phase_transitions": ["solid", "liquid (aqueous)"],
        "classification": "strong base",
        "ph_level": 1,  # as recorded in the classification table
        "color": "absolute black",
    },
    "sulfuric_acid": {
        "arabic_name": "حمض الكبريتيك",
        "formula": "H2SO4",
        "molar_mass_g_per_mol": 98.079,
        "composition": {"H": 2, "S": 1, "O": 4},
        "phase_transitions": ["liquid", "gas"],
        "classification": "strong acid",
        "ph_level": 1,
        "color": "red-orange",
    },
    "ammonia": {
        "arabic_name": "الأمونيا",
        "formula": "NH3",
        "molar_mass_g_per_mol": 17.031,
        "composition": {"N": 1, "H": 3},
        "phase_transitions": ["gas", "liquid"],
        "classification": "weak base",
        "ph_level": 11,
        "color": "blue",
    },
    "acetic_acid": {
        "arabic_name": "حمض الخليك",
        "formula": "CH3COOH",
        "molar_mass_g_per_mol": None,
        "composition": {"C": 2, "H": 4, "O": 2},
        "phase_transitions": [],
        "classification": "weak acid",
        "ph_level": 3,
        "color": "orange",
    },
    "carbonic_acid": {
        "arabic_name": "حمض الكربونيك",
        "formula": "H2CO3",
        "molar_mass_g_per_mol": None,
        "composition": {"H": 2, "C": 1, "O": 3},
        "phase_transitions": [],
        "classification": "weak acid",
        "ph_level": 4,
        "color": "yellow-orange",
    },
    "potassium_hydroxide": {
        "arabic_name": "هيدروكسيد البوتاسيوم",
        "formula": "KOH",
        "molar_mass_g_per_mol": None,
        "composition": {"K": 1, "O": 1, "H": 1},
        "phase_transitions": [],
        "classification": "strong base",
        "ph_level": 13,
        "color": "indigo",
    },
    "sodium_bicarbonate": {
        "arabic_name": "بيكربونات الصوديوم",
        "formula": "NaHCO3",
        "molar_mass_g_per_mol": None,
        "composition": {"Na": 1, "H": 1, "C": 1, "O": 3},
        "phase_transitions": [],
        "classification": "weak base",
        "ph_level": 8,
        "color": "blue-green",
    },
}


def get_compound(name: str) -> dict:
    """Look up by the English slug (e.g. 'water', 'sulfuric_acid')."""
    try:
        return COMPOUNDS[name.lower().replace(" ", "_")]
    except KeyError as exc:
        raise KeyError(
            f"no compound register entry for {name!r}; known: {sorted(COMPOUNDS)}"
        ) from exc


def constituent_elements(name: str) -> list[str]:
    """Element symbols making up this compound, e.g. water -> ['H', 'O']."""
    return sorted(get_compound(name)["composition"])
