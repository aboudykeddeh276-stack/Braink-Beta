"""Semantic concept index: transcribed from the "LIVE_LEXICON" volume,
version 18 (the latest of a 19-version, hash-chained, copy-on-write
history where each version added one or two terms).

This is a distinct thing from `lexicon.py`'s project glossary (agent and
node names): this is a word -> concept-tag index, e.g. "wood" tags to
material/organism/process namespaces. It's the closer match to "the
dictionary provides literal mechanics for understanding a word" -- a
word resolves to explicit tagged concepts, not a generated definition.

Provenance: source volume "LIVE_LEXICON", version 18,
root=sha256:77d15236e10de7d123581be041d458919113bfe5fd89b6993f9d442520f545ea
"""

from __future__ import annotations

SOURCE_VOLUME = "LIVE_LEXICON"
SOURCE_VERSION = 18
SOURCE_ROOT_HASH = "sha256:77d15236e10de7d123581be041d458919113bfe5fd89b6993f9d442520f545ea"

CONCEPT_INDEX: dict[str, list[str]] = {
    "wood": ["material:wood", "wood:oak-heartwood-dry", "wood:pine-sapwood-wet"],
    "plant": ["organism:plant", "process:plant-response"],
    "tree": ["organism:tree"],
    "human": ["organism:human"],
    "brain": ["process:cognition", "system:brain"],
    "fear": ["affect:fear"],
    "carbon": ["element:C"],
    "hydrogen": ["element:H"],
    "oxygen": ["element:O"],
    "cellulose": ["molecule:cellulose"],
    "lignin": ["molecule:lignin"],
    "animal": ["organism:animal"],
    "feeling": ["affect:adaptive-state"],
}


def get_concept_tags(term: str) -> list[str]:
    try:
        return CONCEPT_INDEX[term.lower()]
    except KeyError as exc:
        raise KeyError(
            f"no concept-index entry for {term!r}; known: {sorted(CONCEPT_INDEX)}"
        ) from exc
