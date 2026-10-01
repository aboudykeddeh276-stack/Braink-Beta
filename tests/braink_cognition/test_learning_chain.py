from braink_cognition.learning_chain import Evidence, ExecutionResult, TestResult


def test_test_result_all_passed_requires_at_least_one_test():
    assert TestResult(total=0, passed=0).all_passed is False
    assert TestResult(total=3, passed=3).all_passed is True
    assert TestResult(total=3, passed=2).all_passed is False


def test_evidence_matches_the_exact_results_it_was_computed_from():
    execution = ExecutionResult(ran=True, output="ok")
    test = TestResult(total=3, passed=3)
    evidence = Evidence.compute(execution, test)
    assert evidence.matches(execution, test) is True


def test_evidence_does_not_match_different_results():
    execution = ExecutionResult(ran=True, output="ok")
    test = TestResult(total=3, passed=3)
    evidence = Evidence.compute(execution, test)
    tampered_test = TestResult(total=3, passed=2)
    assert evidence.matches(execution, tampered_test) is False


def test_evidence_is_deterministic():
    execution = ExecutionResult(ran=True, output="ok")
    test = TestResult(total=1, passed=1)
    assert Evidence.compute(execution, test).digest == Evidence.compute(execution, test).digest
