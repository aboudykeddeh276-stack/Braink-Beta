from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .extract import extract_claims_from_manifest
from .ingest import ingest_many
from .ledger import add_digital_trace_event, add_runtime_event, init_ledgers, ledger_counts
from .mirror import mirror_external_sources
from .operators import map_operators_from_claims
from .pinout import write_pinout
from .prove import prove_empirical_claim_links
from .report import generate_markdown_report
from .substrate import substrate_check
from .validate import validate_ledgers


def emit(data: object) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="il-llm", description="IL-LLM infrastructure CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create empty ledger directories and files")

    ingest = sub.add_parser("ingest", help="Ingest source files")
    ingest.add_argument("paths", nargs="+", help="Source files to ingest")
    ingest.add_argument("--attribution", default="A. Keddeh")

    claims = sub.add_parser("extract-claims", help="Extract claim candidates from ingested sources")
    claims.add_argument("--limit-per-source", type=int, default=25)

    sub.add_parser("map-operators", help="Map extracted claims to operator cards")
    sub.add_parser("validate", help="Validate source, claim, operator, and trace ledgers")
    sub.add_parser("report", help="Generate markdown report")
    sub.add_parser("status", help="Show ledger counts")
    sub.add_parser("pinout", help="Write substrate pinout artifact")
    sub.add_parser("prove", help="Run proof scaffolds (no falsifier execution)")
    substrate = sub.add_parser("substrate-check", help="Silent substrate drift check")
    substrate.add_argument("--json", action="store_true", help="Emit JSON even on pass")
    mirror = sub.add_parser("mirror", help="Copy external sources into unlocked mirror tree")
    mirror.add_argument("paths", nargs="+", help="External file paths to mirror under data/mirrors")

    runtime = sub.add_parser("runtime-event", help="Record runtime drift or continuity event")
    runtime.add_argument("--observed-change", required=True)
    runtime.add_argument("--user-report", required=True)
    runtime.add_argument("--impact", required=True)
    runtime.add_argument("--affected-process", required=True)
    runtime.add_argument("--mitigation", required=True)
    runtime.add_argument("--unresolved-risk", required=True)

    trace = sub.add_parser("digital-trace", help="Record digital trace inspection state")
    trace.add_argument("--artifact", required=True)
    trace.add_argument("--trace-marker", required=True)
    trace.add_argument("--target-surface", required=True)
    trace.add_argument("--inspection-method", required=True)
    trace.add_argument("--result", required=True, choices=["present", "absent", "not_inspected"])
    trace.add_argument("--evidence-pointer", default="")
    trace.add_argument("--unresolved-gap", default="")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "init":
        init_ledgers()
        emit({"ok": True, "counts": ledger_counts()})
        return 0
    if args.command == "ingest":
        records = ingest_many([Path(path) for path in args.paths], attribution=args.attribution)
        emit({"ingested": records})
        return 0
    if args.command == "extract-claims":
        claims = extract_claims_from_manifest(limit_per_source=args.limit_per_source)
        emit({"claims": len(claims)})
        return 0
    if args.command == "map-operators":
        operators = map_operators_from_claims()
        emit({"operators": len(operators)})
        return 0
    if args.command == "validate":
        errors = validate_ledgers()
        emit({"passed": not errors, "errors": errors})
        return 1 if errors else 0
    if args.command == "report":
        emit({"report": generate_markdown_report()})
        return 0
    if args.command == "status":
        emit({"counts": ledger_counts()})
        return 0
    if args.command == "pinout":
        path = write_pinout()
        emit({"pinout": str(path)})
        return 0
    if args.command == "prove":
        result = prove_empirical_claim_links()
        emit({"prove_empirical_links": result})
        return 1 if not result.get("passed") else 0
    if args.command == "substrate-check":
        result = substrate_check()
        if args.json or not result.get("ok"):
            emit(result)
        return 0 if result.get("ok") else 2
    if args.command == "mirror":
        result = mirror_external_sources(args.paths)
        emit({"mirrored": result.mirrored, "skipped": result.skipped, "manifest": result.manifest_path})
        return 0
    if args.command == "runtime-event":
        emit(add_runtime_event(
            observed_change=args.observed_change,
            user_report=args.user_report,
            impact=args.impact,
            affected_process=args.affected_process,
            mitigation=args.mitigation,
            unresolved_risk=args.unresolved_risk,
        ))
        return 0
    if args.command == "digital-trace":
        emit(add_digital_trace_event(
            artifact=args.artifact,
            trace_marker=args.trace_marker,
            target_surface=args.target_surface,
            inspection_method=args.inspection_method,
            result=args.result,
            evidence_pointer=args.evidence_pointer,
            unresolved_gap=args.unresolved_gap,
        ))
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    sys.exit(main())
