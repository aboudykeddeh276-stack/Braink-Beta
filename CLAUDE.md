# Working notes for this repository

Read `SYSTEM_INVENTORY.md` before building anything new in this repo. It lists what packages, Drive folders, and documents have actually been opened and verified, and what they actually contain — check it so you don't rebuild something that already exists, or trust a claim that turned out to be decorative.

## Context that shapes how to work here

This project (Braink/KEX/IL-LLM) is developed across many parallel threads at once: multiple AI agents/sessions (not all Claude Code), a Google Drive with dozens of files and folders across several naming schemes (`il-llm-core` and `il_llm` are both used for at least 7 different folders, not interchangeably), and a long history of documents that range from working code to pure aspiration. That's a deliberate way of covering a lot of ground quickly, not disorganization — but it means no single agent or session has full context by default, and confident-sounding names are not a reliable signal of what's actually implemented.

Practical consequences:

- **A file or folder's name is not evidence of its contents.** Two Drive folders can share an exact display name and have completely different contents, or none. Two things called "lexicon" in this project are different in kind (one's a project glossary of agent/node names, one's a general word→concept-tag index). "Ledger," "governance," "validate" have all been used on this project for code that didn't do what the name implies until checked and, where needed, fixed. Open it and check before assuming.
- **A precise-looking number is not evidence it's real.** This project has produced confident, many-decimal-place figures that turned out to be formula artifacts (exact denominator-60 fractions, not analysis) or physically impossible given the substrate (a spreadsheet claiming 100TB capacity when its own cell/character limits cap out around 0.1–0.4TB). Recompute before trusting a number that matters.
- **Duplicate effort is the main risk of the parallel-agent approach**, not error — the audits in this session mostly held up. Before implementing a capability, search `SYSTEM_INVENTORY.md` and, if nothing turns up there, search the actual Drive/repo for related names before writing new code from scratch.

## Working standard established in this codebase (apply it to new work too)

- Tag every non-trivial claim: something is either backed by an executed, tested computation (`VERIFIED` / `LIVE`), or it's an assumed/illustrative input (`CONCEPTUAL` / `SIMULATED`) — never blur the two, and never state a cryptographic near-certainty as literally zero.
- When a source document defines something with unspecified internal structure (e.g. an addressing scheme with lettered fields but no stated meaning for the letters), don't invent semantics for it. Either implement something that satisfies the actual stated requirement without the fabrication, or leave it as an open question.
- Hash-chain anything meant to be tamper-evident (sha256 over canonical JSON, each record carries the previous one's hash) — this repo has one consistent convention for it across `workspace_control_plane.receipts`, `braink_reasoning.chain`, and `il_llm.io.append_record`; reuse it rather than inventing a fourth. Document its one honest limitation (can't detect tampering with only the very last entry) rather than overselling it.
- Run the code before claiming it works. Every package in this repo has a real test suite exercised via `pytest`; add tests for new work in the same style, and update `SYSTEM_INVENTORY.md` in the same commit.
