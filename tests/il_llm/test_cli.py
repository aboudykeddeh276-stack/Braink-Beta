from il_llm import cli


def test_init_creates_empty_ledgers_and_reports_zero_counts(isolated_ledgers, capsys):
    exit_code = cli.main(["init"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert '"claims": 0' in captured.out


def test_status_reports_after_a_runtime_event(isolated_ledgers, capsys):
    cli.main(["init"])
    cli.main([
        "runtime-event",
        "--observed-change", "x", "--user-report", "y", "--impact", "z",
        "--affected-process", "p", "--mitigation", "m", "--unresolved-risk", "r",
    ])
    capsys.readouterr()  # discard prior output
    exit_code = cli.main(["status"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"runtime_events": 1' in captured.out


def test_validate_command_exit_code_reflects_pass_fail(isolated_ledgers):
    cli.main(["init"])
    assert cli.main(["validate"]) == 1  # empty source manifest -> "run ingest first" error

    from il_llm.io import write_json
    from il_llm import paths
    write_json(paths.SOURCE_MANIFEST_PATH, [{"source": "placeholder"}])
    assert cli.main(["validate"]) == 0
