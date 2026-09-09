# Workplan 01: Complete IL-LLM Drive Ingestion

**Status**: not started. **Depends on**: nothing (can start now). **Grounded in**: `SYSTEM_INVENTORY.md`, PR #4.

## Why this exists

PR #4 ported one of the real Drive folders (`1BbqO4aAd_bNu4eHJlvdDrRmIOC0VZfLG`) into this repo as `il_llm`. Two more real, non-empty locations were found during the same audit and have **not** been ported or fully inventoried:

1. Folder `1tKwAsGb9pe9VH5MOpYpssa7y98tjx60Q` ("il-llm-core") — a structured project skeleton (`worktrees/, schemas/, book_formalize_work/, il_llm/, skills/, data/, video_apex_delivery/, docs/, corpus/, tests/`, plus more not yet listed). Only a one-level directory listing exists; no file inside it has been read.
2. Folder `1632l92A5yBiwQe7dfPpRfWJwDxlts3Dc` ("il_llm" — **distinct** from the one already ported, despite the identical display name) — ~20+ Python files including `contradiction_linker.py`, `governance_instruction_set.py`, `akih.py`, `k_sys.py`, `worktree_engine.py`, `coding_braink.py`. Only `governance_instruction_set.py` has been read so far (confirmed: a static config dict + one hash of it, not a live gate).

Leaving these unread risks the exact failure mode this session already hit once: building something from scratch that duplicates real, working code sitting unread in Drive.

## Steps

1. **List folder `1tKwAsGb9pe9VH5MOpYpssa7y98tjx60Q` recursively**, not just one level. Note file counts and types per subfolder before reading contents (mirror the triage approach used for the original 7-folder pass — list first, decide what's worth opening second).
2. **Read every `.py` file in folder `1632l92A5yBiwQe7dfPpRfWJwDxlts3Dc`** the same way folder `1BbqO4aAd...` was handled in PR #4: download each file, reconstruct as a real local package, try to import and run it, look for (and run) any existing test suite.
3. **For each file, answer the same two questions asked of `ledger.py`/`validate.py` in PR #4**: does its name accurately describe what it does, and does it actually run? Do not describe charitably — if `contradiction_linker.py` doesn't actually link contradictions, or `governance_instruction_set.py` doesn't govern anything (already confirmed true for the latter), say so plainly.
4. **Check for overlap** against everything already in this repo (`workspace_control_plane`, `braink_reasoning`, `il_llm`) before deciding to port anything in. A file that duplicates existing, better-tested functionality doesn't need porting — note it in `SYSTEM_INVENTORY.md` as "superseded by X" instead.
5. **Port only what's real and non-duplicate**, following the PR #4 pattern exactly: copy source, add a test suite (none will exist, per the pattern seen twice already), fix any integrity gaps the same way `ledger.py`'s hash-chaining gap was fixed, verify end-to-end with the real CLI/entry point (not just mocked unit tests), commit, open a PR.
6. **Update `SYSTEM_INVENTORY.md`** with the folder's true contents whether or not anything gets ported, so the "unknown" status in the current table is resolved either way.

## Braink constraint check

This workplan is about discovering and porting existing code, not about Braink's answer path directly — but step 5 ("port only what's real and non-duplicate") also means: **do not port anything whose actual mechanism is generating text via a language model call at answer time.** If `contradiction_linker.py`, `akih.py`, or anything else in these folders turns out to work that way, it can still be ported as a standalone tool, but it does not get wired into `braink_reasoning`'s `TopicRegistry` as if it were a Braink capability. Note it as "found, not Braink-eligible" in `SYSTEM_INVENTORY.md` rather than silently registering it as a topic.

## Done criteria

- Both folders have a row in `SYSTEM_INVENTORY.md` describing actual (not assumed) contents.
- Anything real and non-duplicate found is ported, tested, and in an open PR.
- Anything overlapping existing repo code is explicitly noted as superseded, not silently ignored.
