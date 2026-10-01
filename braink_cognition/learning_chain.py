"""The causal learning artifact L_t (SEC-04 / WP04).

    L_t = (C_t, Observation_t, Hypothesis_t, CandidateDelta_t,
           Execution_t, Test_t, Evidence_t, C_{t+1})

Evidence is never a bare claim: `Evidence.compute` hashes the actual
execution/test results it attests to, and `Evidence.matches` re-derives
that hash to check it — so an artifact carrying evidence for results
other than the ones it's actually attached to is detectable, not just
assumed honest.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateDelta:
    """A proposed change, and the contract results already observed for it.

    `precondition_held` / `postcondition_held` are booleans the caller
    records at the moment each check actually happens — precondition
    immediately before execution, postcondition immediately after — not
    re-evaluated later against whatever state happens to exist when the
    artifact is checked. A delta whose precondition depends on mutable
    external state (e.g. "resource does not exist yet") would otherwise be
    checked against the wrong state if a callable were re-invoked at
    validation time instead of at its real execution boundary.
    """

    description: str
    precondition_held: bool = True
    postcondition_held: bool = True


@dataclass(frozen=True)
class ExecutionResult:
    """What actually happened when the candidate delta was run."""

    ran: bool
    output: str = ""


@dataclass(frozen=True)
class TestResult:
    """Real test counts, not a bare pass/fail flag."""

    __test__ = False  # not a pytest test class, despite the name

    total: int
    passed: int

    @property
    def all_passed(self) -> bool:
        return self.total > 0 and self.passed == self.total


@dataclass(frozen=True)
class Evidence:
    """A hash computed over the execution/test results it attests to."""

    digest: str

    @staticmethod
    def compute(execution: ExecutionResult, test: TestResult) -> "Evidence":
        payload = f"{execution.ran}|{execution.output}|{test.total}|{test.passed}"
        return Evidence(digest=hashlib.sha256(payload.encode("utf-8")).hexdigest())

    def matches(self, execution: ExecutionResult, test: TestResult) -> bool:
        return self.digest == Evidence.compute(execution, test).digest


@dataclass(frozen=True)
class LearningArtifact:
    """One immutable causal step: L_t."""

    context_before: str
    observation: str
    hypothesis: str
    candidate_delta: CandidateDelta
    execution: ExecutionResult
    test: TestResult
    evidence: Evidence
    context_after: str
