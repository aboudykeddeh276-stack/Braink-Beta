# Roadmap

This is the master list of workplans for Braink/KEX/IL-LLM: what's done, what's actively defined, and how a new workplan gets added when something emerges mid-task. It is not a prediction of everything the project will ever need — it's a live index of *actually scoped* work, kept honest by linking every entry to something checkable in `SYSTEM_INVENTORY.md` or a real workplan doc.

## How this works

1. **A workplan is a file in `docs/workplans/`**, not a paragraph in this document. This file only lists them, their status, and their dependency order.
2. **A new workplan gets added when a real, bounded piece of work is identified** — not when a new idea or direction is merely mentioned. "We should look at X" is a candidate; it becomes a workplan once it has a stated reason, concrete steps, and done-criteria (see the three existing workplans for the shape).
3. **Emergent discoveries during any task go into `SYSTEM_INVENTORY.md` immediately**, whether or not they become a workplan. A workplan is for *work still to do*; the inventory is for *what's now known to exist*. Conflating the two is how documents like the original spreadsheet ended up mixing real data with placeholders in the same tab.
4. **Day-to-day tracking of in-flight work uses the task tracker** (`TaskCreate`/`TaskList`/`TaskUpdate` in an active session — see the 14 tasks tracked and closed during the session that produced this roadmap), not this file. This file is the durable index that survives after any one session ends; the task tracker is the live working state within a session.
5. **Priority order below is a default, not a constraint** — work the item that's actually blocking something over the item that's listed first, and say why if you deviate.

## Status

| # | Workplan | Status | Depends on |
|---|---|---|---|
| 01 | [Complete IL-LLM Drive Ingestion](docs/workplans/01-complete-il-llm-drive-ingestion.md) | Not started | Nothing — can start now |
| 02 | [Screen-Reading Decision and Build](docs/workplans/02-screen-reading-decision-and-build.md) | Blocked on a decision | A yes/no + which-approach answer from the project owner |
| 03 | [Real Media Feature Register](docs/workplans/03-real-media-feature-register.md) | Blocked on a decision | A methodology choice (computed / model-derived / human-curated) |

## Already delivered (see `SYSTEM_INVENTORY.md` for detail)

- PR #2: `workspace_control_plane` — governed mutation pipeline, 51 tests.
- PR #3: `keddeh_math` + `braink_reasoning` — verified math library, topic router, reference graph, 4 data registers, IL-LLM chain, CLI. 100 tests.
- PR #4: `il_llm` — ported from Drive, ledger hash-chaining gap closed. 14 tests.
- PR #5: `SYSTEM_INVENTORY.md` + `CLAUDE.md` — this accountability layer itself.

## Standing holds (not workplans — explicitly not to be built without new input)

- Synthetic MAC/IP device-identity generation at scale. See `SYSTEM_INVENTORY.md`.

## Adding a new workplan

Copy the shape of `docs/workplans/01-*.md`: a "Why this exists" section grounded in something specific (a file, a PR, a conversation finding — not a vague direction), numbered steps, and a "Done criteria" section that's actually checkable. Add a row to the table above. If it turns out to be speculative once written down — no concrete steps, no way to know when it's done — that's a sign it isn't a workplan yet, just a direction; note it in `SYSTEM_INVENTORY.md` instead and revisit once it's concrete.
