"""braink_cognition: a runnable implementation of the formalizable parts of
SEC-03 (Semantic Foundations & Bounded Cognition) and SEC-04 (Dynamic
Codebases & Causal Thinking Chains) from the KEX/BRAINK Master Control
Specification.

Scope note: this package implements only the parts of SEC-03/SEC-04 that
are concrete, well-defined algorithms and data structures — the LCA tree
metric, signed Hebbian edge reinforcement, the causal learning artifact
L_t, an append-only hash-chained ledger, and the five-part Valid(Delta)
operator. It does NOT implement or certify the physics/quantum-computing
material elsewhere in the specification (three-body mechanics, symplectic
drift benchmarks, the workbook runtime, or the forensic receipts corpus).
Those are not concrete, runnable specifications, and nothing here should
be read as verifying them.
"""

from braink_cognition.hebbian import HebbianGraph, Polarity
from braink_cognition.ledger import HistoricalLedger, LedgerEntry
from braink_cognition.learning_chain import (
    CandidateDelta,
    Evidence,
    ExecutionResult,
    LearningArtifact,
    TestResult,
)
from braink_cognition.lexicon import LexicalNode, LexicalTree
from braink_cognition.validity import ValidityResult, check_validity

__all__ = [
    "LexicalNode",
    "LexicalTree",
    "HebbianGraph",
    "Polarity",
    "CandidateDelta",
    "ExecutionResult",
    "TestResult",
    "Evidence",
    "LearningArtifact",
    "HistoricalLedger",
    "LedgerEntry",
    "ValidityResult",
    "check_validity",
]
