"""Lexicon register: transcribed from the "02 - Words (English Lexicon)"
and node-registry sections of the source spreadsheet.

This is the project's own glossary of internal terms (agent names, asset
codes, node identifiers) -- not a general English dictionary. Every
entry below is transcribed verbatim from a fully visible row in the
source; truncated rows encountered during extraction were re-fetched in
full rather than guessed at.
"""

from __future__ import annotations

GLOSSARY: dict[str, dict] = {
    "ollama": {
        "node_code": "N-OLLAMA-001",
        "status": "Active / Source-Verified",
        "target": "T-OLLAMA-RUNTIME",
        "hex_id": "KEX-OLLAMA-52DDCC330341",
    },
    "model": {
        "node_code": "N-OLLAMA-002",
        "status": "Active / Semantic-Bound",
        "target": "T-OLLAMA-MODEL",
        "hex_id": "KEX-MODEL-1B68637E07F8",
    },
    "context x definition mapping": {
        "node_code": "N-OLLAMA-003",
        "description": "BRAINK learns Ollama Model",
        "status": "Active / Bilateral",
        "target": "T-ILLLM-LEARNING",
        "hex_id": "KEX-OLLAMA-LEARN-01",
    },
    "layer 1 asset": {
        "node_code": "N-L1-001",
        "asset_code": "A1063",
        "status": "Active / Source-Bound",
        "target": "T-L1-ASSET",
        "hex_id": "KEX-LAYER-1-ASSET-E276B55F1498",
    },
    "live_agents": {
        "node_code": "N-L1-002",
        "asset_code": "A1064",
        "status": "Active / Immutable-Lineage",
        "target": "T-LIVE-AGENTS",
        "hex_id": "KEX-LIVE_AGENTS-B43C673D5E22",
    },
    "agent(1)": {
        "node_code": "N-L1-003",
        "asset_code": "A1065",
        "status": "Active / Address-Bound",
        "target": "T-AGENT1",
        "hex_id": "KEX-AGENT1-E82D53A96EEA",
    },
    "coding agent": {
        "node_code": "N-L1-004",
        "asset_code": "A1066",
        "status": "Active / Agent-Service",
        "target": "T-CODING-AGENT",
        "hex_id": "KEX-CODING-AGENT-695AA5D2D667",
    },
    "supervisor agent": {
        "node_code": "N-L1-005",
        "asset_code": "A1067",
        "status": "Active / Team-Supervision",
        "target": "T-SUPERVISOR-AGENT",
        "hex_id": "KEX-SUPERVISOR-AGENT-761988C1C8A6",
    },
    "lexicon agent": {
        "node_code": "N-L1-006",
        "asset_code": "A1068",
        "status": "Active / Learning-Ingress",
        "target": "T-LEXICON-AGENT",
        "hex_id": "KEX-LEXICON-AGENT-A95DA3F3B78F",
    },
    "composition agent": {
        "node_code": "N-L1-007",
        "asset_code": "A1069",
        "status": "Active / Relation-Builder",
        "target": "T-COMPOSITION-AGENT",
        "hex_id": "KEX-COMPOSITION-AGENT-F8157AD3BA39",
    },
    "cognition agent": {
        "node_code": "N-L1-008",
        "asset_code": "A1070",
        "status": "Active / Adaptive-Learning",
        "target": "T-COGNITION-AGENT",
        "hex_id": "KEX-COGNITION-AGENT-6C37C0CAB828",
    },
    "provenance agent": {
        "node_code": "N-L1-009",
        "asset_code": "A1071",
        "status": "Active / Evidence-Lineage",
        "target": "T-PROVENANCE-AGENT",
        "hex_id": "KEX-PROVENANCE-AGENT-9961DE3FFE3F",
    },
    "workflow agent": {
        "node_code": "N-L1-010",
        "asset_code": "A1072",
        "status": "Active / Service-Workflow",
        "target": "T-WORKFLOW-AGENT",
        "hex_id": "KEX-WORKFLOW-AGENT-3BEACD85B18E",
    },
    "release agent": {
        "node_code": "N-L1-011",
        "asset_code": "A1073",
        "status": "Active / Promotion-Gate",
        "target": "T-RELEASE-AGENT",
        "hex_id": "KEX-RELEASE-AGENT-FDC65D78561F",
    },
    "recovery queue": {
        "node_code": "N-L1-012",
        "asset_code": "A1074",
        "status": "Active / Rehydration",
        "target": "T-RECOVERY-QUEUE",
        "hex_id": "KEX-RECOVERY-QUEUE-2C8A90341901",
    },
}


def get_term(term: str) -> dict:
    try:
        return GLOSSARY[term.lower()]
    except KeyError as exc:
        raise KeyError(
            f"no glossary entry for {term!r}; known: {sorted(GLOSSARY)}"
        ) from exc
