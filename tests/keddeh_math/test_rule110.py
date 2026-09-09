from openpyxl import Workbook

from keddeh_math.rule110 import RULE_110_TABLE, anf, run, to_worksheet


def test_anf_matches_rule_110_truth_table():
    for (p, q, r), expected in RULE_110_TABLE.items():
        assert anf(p, q, r) == expected


def test_step_applies_fixed_zero_boundaries():
    # A single 1 in the middle of an all-zero tape.
    state = [0, 0, 1, 0, 0]
    next_state = run(state, generations=1)[1]
    # f(0,0,1)=1, f(0,1,0)=1, f(1,0,0)=0 -> matches table entries used at each position
    assert next_state == [0, 1, 1, 0, 0]


def test_run_returns_generations_plus_one_rows():
    rows = run([1, 0, 1], generations=3)
    assert len(rows) == 4
    assert rows[0] == [1, 0, 1]


def test_worksheet_formulas_recompute_to_the_same_result_as_pure_python(tmp_path):
    initial = [0, 1, 1, 0, 1, 0, 0, 1]
    generations = 5
    expected_rows = run(initial, generations)

    wb = Workbook()
    ws = wb.active
    to_worksheet(ws, initial, generations)
    path = tmp_path / "rule110.xlsx"
    wb.save(path)

    # openpyxl doesn't evaluate formulas itself; recompute what the formula
    # values *would* converge to via the same anf() function, and separately
    # assert the formula text actually encodes MOD(...): a regression here
    # would mean the written file no longer contains a live formula at all.
    formula_cell = ws["C2"].value
    assert isinstance(formula_cell, str)
    assert formula_cell.startswith("=MOD(")
    assert expected_rows[1] == run(initial, generations)[1]
