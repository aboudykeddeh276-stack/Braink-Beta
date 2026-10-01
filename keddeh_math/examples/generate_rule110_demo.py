"""Generates a runnable Rule 110 spreadsheet artifact.

Usage:
    python -m keddeh_math.examples.generate_rule110_demo [output_path]

Opening the resulting .xlsx in any spreadsheet application and forcing a
recalculation reproduces the same automaton as `keddeh_math.rule110.run`
computes in pure Python -- because every non-seed cell is a live MOD(...)
formula, not a cached value. This is deliberately not committed to the
repository as a binary artifact; regenerate it whenever you want to see it.
"""

from __future__ import annotations

import sys

from keddeh_math.rule110 import to_workbook


def main() -> int:
    output_path = sys.argv[1] if len(sys.argv) > 1 else "rule110_demo.xlsx"
    initial = [0] * 20 + [1] + [0] * 20
    generations = 30
    wb = to_workbook(initial, generations)
    wb.save(output_path)
    print(f"wrote {output_path}: {len(initial)} columns x {generations + 1} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
