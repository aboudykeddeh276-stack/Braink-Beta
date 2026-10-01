"""Command-line entry point for braink_reasoning.

Usage:
    python -m braink_reasoning.cli <topic> [key=value ...]

Examples:
    python -m braink_reasoning.cli periodic_table.element identifier=Au
    python -m braink_reasoning.cli chemistry.compound name=water
    python -m braink_reasoning.cli composite_warrant warrants=0.9,0.8,0.7
    python -m braink_reasoning.cli lexicon.concept_tags term=brain

Unregistered topics and missing parameters print an honest error and a
list of known topics -- this CLI never fabricates an answer for a topic
it doesn't have.
"""

from __future__ import annotations

import json
import sys

from braink_reasoning.query import explain
from braink_reasoning.registry import UnknownTopicError
from braink_reasoning.topics import build_default_registry


def _coerce(value: str):
    if "," in value:
        return [_coerce(v) for v in value.split(",")]
    for caster in (int, float):
        try:
            return caster(value)
        except ValueError:
            continue
    return value


def parse_params(args: list[str]) -> dict:
    params = {}
    for arg in args:
        if "=" not in arg:
            raise ValueError(f"expected key=value, got {arg!r}")
        key, _, value = arg.partition("=")
        params[key] = _coerce(value)
    return params


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: python -m braink_reasoning.cli <topic> [key=value ...]", file=sys.stderr)
        return 2

    topic, *param_args = argv
    registry = build_default_registry()

    try:
        params = parse_params(param_args)
        result = explain(registry, topic, **params)
    except UnknownTopicError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
