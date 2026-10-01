from __future__ import annotations

import re

from .io import read_json, write_json
from .paths import CLAIMS_PATH, OPERATORS_PATH


def classify_operator(wording: str) -> tuple[str, str, list[str]]:
    lower = wording.lower()
    if "wake" in lower or "shell" in lower:
        return "Wake-Shell Topology", "Map wake, shell, vector, medium, and residue separately.", ["body profile", "medium condition", "translation vector", "wake residue", "shell boundary"]
    if "observer" in lower:
        return "Observer-State Calibration", "Declare observer state before treating a field claim as stable.", ["observer position", "instrument frame", "field condition", "calibration reference"]
    if "contradiction" in lower or "falsifier" in lower:
        return "Contradiction Calibration", "Convert contradiction into boundary, revision, or non-regression test.", ["claim", "counterclaim", "failure mode", "next test"]
    if "validation" in lower or "proof" in lower or "evidence" in lower:
        return "Evidence Status Governance", "Separate authored definition, internal coherence, theorem-state, and empirical validation.", ["claim", "source", "evidence object", "status lane"]
    if "memory" in lower or "residue" in lower or "recursive" in lower:
        return "Recursive Field Persistence", "Track how retained residue changes the next translation cycle.", ["source condition", "translation pressure", "retained residue", "theorem-state memory"]
    if "il-llm" in lower or "governance" in lower or "runtime" in lower:
        return "Recursive Runtime Governance", "Preserve source, claim, contradiction, and tool output across cycles.", ["document state", "claim register", "contradiction ledger", "tool output"]
    return "Recursive Development Integration", "Convert dense source material into claim, operator, evidence, and teaching form.", ["source passage", "active claim", "evidence status", "next action"]


def map_claim_to_operator(claim: dict[str, object]) -> dict[str, object]:
    wording = str(claim.get("wording", ""))
    name, definition, inputs = classify_operator(wording)
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    claim_id = str(claim["id"])
    return {
        "id": f"op_{slug}_{claim_id.rsplit('_', 1)[-1]}",
        "name": name,
        "definition": definition,
        "inputs": inputs,
        "steps": [
            "Preserve the source reference and attribution.",
            "State the bounded claim in one sentence.",
            "Identify the active inputs.",
            "Apply the operator transformation.",
            "Assign evidence status and record a falsifier.",
        ],
        "outputs": ["stable teaching claim", "narrowed claim", "pending validation claim", "rejected overreach"],
        "evidence_gate": "Do not promote this operator beyond its available source, test, simulation, or evidence object.",
        "failure_modes": [
            "missing source reference",
            "unsupported empirical validation",
            "hidden contradiction",
            "operator lacks falsifier",
        ],
        "teaching_use": "Use as a process card for reducing source overhead into repeatable method.",
        "linked_claims": [claim_id],
    }


def map_operators_from_claims() -> list[dict[str, object]]:
    claims = read_json(CLAIMS_PATH, [])
    operators = [map_claim_to_operator(claim) for claim in claims]
    write_json(OPERATORS_PATH, operators)
    return operators

