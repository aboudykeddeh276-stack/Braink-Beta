import dataclasses

from braink_cognition.ledger import HistoricalLedger
from braink_cognition.learning_chain import (
    CandidateDelta,
    Evidence,
    ExecutionResult,
    LearningArtifact,
    TestResult,
)
from braink_cognition.validity import check_validity


def _valid_artifact() -> LearningArtifact:
    execution = ExecutionResult(ran=True, output="did the thing")
    test = TestResult(total=4, passed=4)
    return LearningArtifact(
        context_before="C0",
        observation="something was off",
        hypothesis="X causes Y",
        candidate_delta=CandidateDelta(
            description="fix X",
            precondition_held=True,
            postcondition_held=True,
        ),
        execution=execution,
        test=test,
        evidence=Evidence.compute(execution, test),
        context_after="C1",
    )


def test_fully_valid_artifact_passes_all_five_predicates():
    ledger = HistoricalLedger()
    artifact = _valid_artifact()
    ledger.append(artifact)

    result = check_validity(artifact, ledger)

    assert result.contract_preserved is True
    assert result.executed is True
    assert result.tests_passed is True
    assert result.evidence_bound is True
    assert result.lineage_committed is True
    assert result.valid is True


def test_uncommitted_artifact_fails_lineage_committed_only():
    ledger = HistoricalLedger()
    artifact = _valid_artifact()
    # deliberately not appended

    result = check_validity(artifact, ledger)

    assert result.lineage_committed is False
    assert result.valid is False
    assert result.contract_preserved is True
    assert result.executed is True
    assert result.tests_passed is True
    assert result.evidence_bound is True


def test_unexecuted_artifact_fails_executed_and_tests_passed():
    ledger = HistoricalLedger()
    execution = ExecutionResult(ran=False)
    test = TestResult(total=0, passed=0)
    artifact = LearningArtifact(
        context_before="C0",
        observation="obs",
        hypothesis="hyp",
        candidate_delta=CandidateDelta(description="no-op"),
        execution=execution,
        test=test,
        evidence=Evidence.compute(execution, test),
        context_after="C0",
    )
    ledger.append(artifact)

    result = check_validity(artifact, ledger)

    assert result.executed is False
    assert result.tests_passed is False  # 0 tests is not "passed"
    assert result.valid is False


def test_broken_postcondition_fails_contract_preserved():
    ledger = HistoricalLedger()
    execution = ExecutionResult(ran=True, output="ran")
    test = TestResult(total=1, passed=1)
    artifact = LearningArtifact(
        context_before="C0",
        observation="obs",
        hypothesis="hyp",
        candidate_delta=CandidateDelta(
            description="broken fix",
            precondition_held=True,
            postcondition_held=False,  # the fix didn't actually achieve its goal
        ),
        execution=execution,
        test=test,
        evidence=Evidence.compute(execution, test),
        context_after="C0",
    )
    ledger.append(artifact)

    result = check_validity(artifact, ledger)

    assert result.contract_preserved is False
    assert result.valid is False


def test_tampered_evidence_fails_evidence_bound():
    ledger = HistoricalLedger()
    execution = ExecutionResult(ran=True, output="ran")
    test = TestResult(total=1, passed=1)
    # Evidence computed over DIFFERENT results than what's actually
    # attached — simulates a fabricated receipt.
    fabricated_evidence = Evidence.compute(ExecutionResult(ran=True, output="fabricated"), test)
    artifact = LearningArtifact(
        context_before="C0",
        observation="obs",
        hypothesis="hyp",
        candidate_delta=CandidateDelta(description="fix"),
        execution=execution,
        test=test,
        evidence=fabricated_evidence,
        context_after="C0",
    )
    ledger.append(artifact)

    result = check_validity(artifact, ledger)

    assert result.evidence_bound is False
    assert result.valid is False


def test_lineage_committed_fails_when_ledger_chain_is_tampered():
    # Even an artifact whose OWN entry is untouched must not be reported as
    # lineage-committed if the ledger's chain as a whole has been tampered
    # with elsewhere — "committed" is a claim about the ledger's integrity,
    # not just this one artifact's presence in a digest set.
    ledger = HistoricalLedger()
    artifact = _valid_artifact()
    ledger.append(artifact)
    ledger.append(_other_artifact())

    ledger._entries[1] = dataclasses.replace(ledger._entries[1], artifact_digest="0" * 64)
    assert ledger.verify_chain() is False

    result = check_validity(artifact, ledger)

    assert result.lineage_committed is False
    assert result.valid is False


def _other_artifact() -> LearningArtifact:
    execution = ExecutionResult(ran=True, output="something else")
    test = TestResult(total=2, passed=2)
    return LearningArtifact(
        context_before="C1",
        observation="obs2",
        hypothesis="hyp2",
        candidate_delta=CandidateDelta(description="second delta"),
        execution=execution,
        test=test,
        evidence=Evidence.compute(execution, test),
        context_after="C2",
    )
