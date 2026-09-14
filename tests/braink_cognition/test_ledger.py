import dataclasses

from braink_cognition.ledger import HistoricalLedger
from braink_cognition.learning_chain import (
    CandidateDelta,
    Evidence,
    ExecutionResult,
    LearningArtifact,
    TestResult,
)


def _make_artifact(label: str) -> LearningArtifact:
    execution = ExecutionResult(ran=True, output=label)
    test = TestResult(total=1, passed=1)
    return LearningArtifact(
        context_before=f"before-{label}",
        observation=f"obs-{label}",
        hypothesis=f"hyp-{label}",
        candidate_delta=CandidateDelta(description=label),
        execution=execution,
        test=test,
        evidence=Evidence.compute(execution, test),
        context_after=f"after-{label}",
    )


def test_append_grows_the_ledger():
    ledger = HistoricalLedger()
    assert len(ledger) == 0
    ledger.append(_make_artifact("a"))
    assert len(ledger) == 1


def test_appended_artifact_is_a_member():
    ledger = HistoricalLedger()
    artifact = _make_artifact("a")
    ledger.append(artifact)
    assert artifact in ledger


def test_unappended_artifact_is_not_a_member():
    ledger = HistoricalLedger()
    ledger.append(_make_artifact("a"))
    assert _make_artifact("b") not in ledger


def test_ledger_has_no_removal_api():
    ledger = HistoricalLedger()
    assert not hasattr(ledger, "remove")
    assert not hasattr(ledger, "delete")
    assert not hasattr(ledger, "clear")


def test_monotonic_superset_property():
    # HistoricalLedger_t is a subset-or-equal of HistoricalLedger_{t+1}
    ledger = HistoricalLedger()
    ledger.append(_make_artifact("a"))
    snapshot_t = ledger.entries()
    ledger.append(_make_artifact("b"))
    snapshot_t_plus_1 = ledger.entries()
    assert snapshot_t_plus_1[: len(snapshot_t)] == snapshot_t
    assert len(snapshot_t_plus_1) >= len(snapshot_t)


def test_chain_verifies_when_untampered():
    ledger = HistoricalLedger()
    ledger.append(_make_artifact("a"))
    ledger.append(_make_artifact("b"))
    assert ledger.verify_chain() is True


def test_chain_detects_tampering():
    ledger = HistoricalLedger()
    ledger.append(_make_artifact("a"))
    ledger.append(_make_artifact("b"))
    # White-box: simulate a tampered digest surviving into the entry list,
    # to prove verify_chain() actually catches it rather than trusting it.
    tampered = dataclasses.replace(ledger._entries[1], artifact_digest="0" * 64)
    ledger._entries[1] = tampered
    assert ledger.verify_chain() is False
