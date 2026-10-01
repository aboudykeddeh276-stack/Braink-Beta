import json

import pytest

from braink_reasoning.cli import main, parse_params


def test_parse_params_coerces_int_float_and_string():
    params = parse_params(["identifier=Au", "count=3", "ratio=0.5"])
    assert params == {"identifier": "Au", "count": 3, "ratio": 0.5}


def test_parse_params_coerces_comma_separated_list():
    params = parse_params(["warrants=0.9,0.8,0.7"])
    assert params == {"warrants": [0.9, 0.8, 0.7]}


def test_parse_params_rejects_malformed_arg():
    with pytest.raises(ValueError):
        parse_params(["not-a-key-value"])


def test_main_prints_json_result_for_a_real_topic(capsys):
    exit_code = main(["periodic_table.element", "identifier=Au"])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["result"]["name"] == "Gold"


def test_main_reports_unknown_topic_without_crashing(capsys):
    exit_code = main(["nonexistent_topic"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "nonexistent_topic" in captured.err


def test_main_with_no_args_prints_usage(capsys):
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "usage" in captured.err
