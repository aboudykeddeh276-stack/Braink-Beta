"""Periodic table register: standard IUPAC reference data.

This is empirical/measured scientific fact, not something derived or
computed -- there is nothing to "verify" mathematically here beyond
transcription accuracy, so this module is a plain, literal lookup table:
atomic number, symbol, name, standard atomic weight (u). Radioactive
elements with no stable isotope use the mass number of their most
stable known isotope, per standard convention.
"""

from __future__ import annotations

# (atomic_number, symbol, name, atomic_weight)
_ELEMENTS: tuple[tuple[int, str, str, float], ...] = (
    (1, "H", "Hydrogen", 1.008),
    (2, "He", "Helium", 4.0026),
    (3, "Li", "Lithium", 6.94),
    (4, "Be", "Beryllium", 9.0122),
    (5, "B", "Boron", 10.81),
    (6, "C", "Carbon", 12.011),
    (7, "N", "Nitrogen", 14.007),
    (8, "O", "Oxygen", 15.999),
    (9, "F", "Fluorine", 18.998),
    (10, "Ne", "Neon", 20.180),
    (11, "Na", "Sodium", 22.990),
    (12, "Mg", "Magnesium", 24.305),
    (13, "Al", "Aluminium", 26.982),
    (14, "Si", "Silicon", 28.085),
    (15, "P", "Phosphorus", 30.974),
    (16, "S", "Sulfur", 32.06),
    (17, "Cl", "Chlorine", 35.45),
    (18, "Ar", "Argon", 39.948),
    (19, "K", "Potassium", 39.098),
    (20, "Ca", "Calcium", 40.078),
    (21, "Sc", "Scandium", 44.956),
    (22, "Ti", "Titanium", 47.867),
    (23, "V", "Vanadium", 50.942),
    (24, "Cr", "Chromium", 51.996),
    (25, "Mn", "Manganese", 54.938),
    (26, "Fe", "Iron", 55.845),
    (27, "Co", "Cobalt", 58.933),
    (28, "Ni", "Nickel", 58.693),
    (29, "Cu", "Copper", 63.546),
    (30, "Zn", "Zinc", 65.38),
    (31, "Ga", "Gallium", 69.723),
    (32, "Ge", "Germanium", 72.630),
    (33, "As", "Arsenic", 74.922),
    (34, "Se", "Selenium", 78.971),
    (35, "Br", "Bromine", 79.904),
    (36, "Kr", "Krypton", 83.798),
    (37, "Rb", "Rubidium", 85.468),
    (38, "Sr", "Strontium", 87.62),
    (39, "Y", "Yttrium", 88.906),
    (40, "Zr", "Zirconium", 91.224),
    (41, "Nb", "Niobium", 92.906),
    (42, "Mo", "Molybdenum", 95.95),
    (43, "Tc", "Technetium", 98.0),
    (44, "Ru", "Ruthenium", 101.07),
    (45, "Rh", "Rhodium", 102.906),
    (46, "Pd", "Palladium", 106.42),
    (47, "Ag", "Silver", 107.868),
    (48, "Cd", "Cadmium", 112.414),
    (49, "In", "Indium", 114.818),
    (50, "Sn", "Tin", 118.710),
    (51, "Sb", "Antimony", 121.760),
    (52, "Te", "Tellurium", 127.60),
    (53, "I", "Iodine", 126.904),
    (54, "Xe", "Xenon", 131.293),
    (55, "Cs", "Cesium", 132.905),
    (56, "Ba", "Barium", 137.327),
    (57, "La", "Lanthanum", 138.905),
    (58, "Ce", "Cerium", 140.116),
    (59, "Pr", "Praseodymium", 140.908),
    (60, "Nd", "Neodymium", 144.242),
    (61, "Pm", "Promethium", 145.0),
    (62, "Sm", "Samarium", 150.36),
    (63, "Eu", "Europium", 151.964),
    (64, "Gd", "Gadolinium", 157.25),
    (65, "Tb", "Terbium", 158.925),
    (66, "Dy", "Dysprosium", 162.500),
    (67, "Ho", "Holmium", 164.930),
    (68, "Er", "Erbium", 167.259),
    (69, "Tm", "Thulium", 168.934),
    (70, "Yb", "Ytterbium", 173.045),
    (71, "Lu", "Lutetium", 174.967),
    (72, "Hf", "Hafnium", 178.49),
    (73, "Ta", "Tantalum", 180.948),
    (74, "W", "Tungsten", 183.84),
    (75, "Re", "Rhenium", 186.207),
    (76, "Os", "Osmium", 190.23),
    (77, "Ir", "Iridium", 192.217),
    (78, "Pt", "Platinum", 195.084),
    (79, "Au", "Gold", 196.967),
    (80, "Hg", "Mercury", 200.592),
    (81, "Tl", "Thallium", 204.38),
    (82, "Pb", "Lead", 207.2),
    (83, "Bi", "Bismuth", 208.980),
    (84, "Po", "Polonium", 209.0),
    (85, "At", "Astatine", 210.0),
    (86, "Rn", "Radon", 222.0),
    (87, "Fr", "Francium", 223.0),
    (88, "Ra", "Radium", 226.0),
    (89, "Ac", "Actinium", 227.0),
    (90, "Th", "Thorium", 232.038),
    (91, "Pa", "Protactinium", 231.036),
    (92, "U", "Uranium", 238.029),
    (93, "Np", "Neptunium", 237.0),
    (94, "Pu", "Plutonium", 244.0),
    (95, "Am", "Americium", 243.0),
    (96, "Cm", "Curium", 247.0),
    (97, "Bk", "Berkelium", 247.0),
    (98, "Cf", "Californium", 251.0),
    (99, "Es", "Einsteinium", 252.0),
    (100, "Fm", "Fermium", 257.0),
    (101, "Md", "Mendelevium", 258.0),
    (102, "No", "Nobelium", 259.0),
    (103, "Lr", "Lawrencium", 266.0),
    (104, "Rf", "Rutherfordium", 267.0),
    (105, "Db", "Dubnium", 268.0),
    (106, "Sg", "Seaborgium", 269.0),
    (107, "Bh", "Bohrium", 270.0),
    (108, "Hs", "Hassium", 269.0),
    (109, "Mt", "Meitnerium", 278.0),
    (110, "Ds", "Darmstadtium", 281.0),
    (111, "Rg", "Roentgenium", 282.0),
    (112, "Cn", "Copernicium", 285.0),
    (113, "Nh", "Nihonium", 286.0),
    (114, "Fl", "Flerovium", 289.0),
    (115, "Mc", "Moscovium", 290.0),
    (116, "Lv", "Livermorium", 293.0),
    (117, "Ts", "Tennessine", 294.0),
    (118, "Og", "Oganesson", 294.0),
)

_BY_SYMBOL = {symbol.upper(): (num, symbol, name, mass) for num, symbol, name, mass in _ELEMENTS}
_BY_NAME = {name.lower(): (num, symbol, name, mass) for num, symbol, name, mass in _ELEMENTS}
_BY_NUMBER = {num: (num, symbol, name, mass) for num, symbol, name, mass in _ELEMENTS}


def element_count() -> int:
    return len(_ELEMENTS)


def get_element(identifier: str | int) -> dict:
    """Look up by symbol ('Fe'), name ('Iron', case-insensitive), or atomic number (26)."""
    if isinstance(identifier, int):
        entry = _BY_NUMBER.get(identifier)
    else:
        entry = _BY_SYMBOL.get(identifier.upper()) or _BY_NAME.get(identifier.lower())
    if entry is None:
        raise KeyError(f"no periodic table entry for {identifier!r}")
    num, symbol, name, mass = entry
    return {"atomic_number": num, "symbol": symbol, "name": name, "atomic_weight": mass}
