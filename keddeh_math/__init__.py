"""Keddeh Math Verification package.

Replaces the hand-derived arithmetic in the "Long-Form Mathematical
Derivations" document with exact, machine-executed, tested implementations.

Each module corresponds to one theorem from that document and is written
to satisfy the document's own stated standard: no numeric claim without a
mechanically executed proof. Where the original document's conclusion
overreached what the math actually established (e.g. calling a bounded
workbook "Turing-equivalent", or a cryptographic near-certainty "exactly
zero"), the docstrings here say so explicitly rather than repeating the
overclaim.

Modules:
    rule110           -- Theorem 1: Rule 110 ANF + spreadsheet-formula CA
    search_partition  -- Theorem 2: disjoint work partitioning / birthday bound
    landauer          -- Theorem 3: Landauer thermodynamic bit-erasure limit
    queueing          -- Theorem 4: M/G/1 Pollaczek-Khinchine queue depth
    shannon           -- Theorem 5: Shannon-Hartley channel capacity
    q32_32            -- Theorem 6: Q32.32 fixed-point log-domain consilience
"""
