"""The validity operator (SEC-04 / WP04):

    Valid(Delta) = ContractPreserved AND Executed AND TestsPassed
                   AND EvidenceBound AND LineageCommitted
"""

from __future__ import annotations

from dataclasses import dataclass

from braink_cognition.ledger import HistoricalLedger
from braink_cognition.learning_chain import LearningArtifact


@dataclass(frozen=True)
class ValidityResult:
    contract_preserved: bool
    executed: bool
    tests_passed: bool
    evidence_bound: bool
    lineage_committed: bool

    @property
    def valid(self) -> bool:
        return (
            self.contract_preserved
            and self.executed
            and self.tests_passed
            and self.evidence_bound
            and self.lineage_committed
        )


def check_validity(artifact: LearningArtifact, ledger: HistoricalLedger) -> ValidityResult:
    """Evaluate each of the five predicates independently, so a caller can
    see exactly which one failed rather than a single opaque bool.

    `contract_preserved` reads the pre/postcondition results the caller
    already recorded on the delta at their real execution boundaries — it
    never re-evaluates a live predicate here, which would check current
    state instead of the state that existed when the delta actually ran.

    `lineage_committed` requires both ledger membership AND a verified
    hash chain: an artifact "in" a ledger whose chain has been tampered
    with elsewhere is not trustworthy lineage, even if that artifact's own
    entry wasn't the one altered.
    """
    delta = artifact.candidate_delta
    return ValidityResult(
        contract_preserved=delta.precondition_held and delta.postcondition_held,
        executed=artifact.execution.ran,
        tests_passed=artifact.test.all_passed,
        evidence_bound=artifact.evidence.matches(artifact.execution, artifact.test),
        lineage_committed=(artifact in ledger) and ledger.verify_chain(),
    )
