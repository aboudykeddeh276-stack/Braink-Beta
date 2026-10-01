from __future__ import annotations

from datetime import datetime, timezone

from .io import read_json
from .ledger import ledger_counts
from .paths import (
    CLAIMS_PATH,
    OPERATORS_PATH,
    REPORTS_DIR,
    SOURCE_MANIFEST_PATH,
    ensure_data_dirs,
)


def generate_markdown_report() -> str:
    ensure_data_dirs()
    sources = read_json(SOURCE_MANIFEST_PATH, [])
    claims = read_json(CLAIMS_PATH, [])
    operators = read_json(OPERATORS_PATH, [])
    counts = ledger_counts()
    lines = [
        "# IL-LLM Ledger Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Sources", ""])
    for source in sources:
        lines.append(f"- `{source['id']}`: {source.get('word_count', 0)} words, source `{source.get('source_path')}`")
    lines.extend(["", "## Claim Samples", ""])
    for claim in claims[:20]:
        lines.append(f"- `{claim['id']}` [{claim['status']}]: {claim['title']}")
    lines.extend(["", "## Operator Samples", ""])
    for operator in operators[:20]:
        lines.append(f"- `{operator['id']}`: {operator['name']}")
    report = "\n".join(lines) + "\n"
    out = REPORTS_DIR / "ledger_report.md"
    out.write_text(report, encoding="utf-8")
    return str(out)

