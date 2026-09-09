# System Inventory

**Purpose**: a single, cheap-to-check manifest of what already exists and where, so any agent working on this project — human-directed or autonomous, this one or one of several running in parallel — checks here before building something new. Multiple agents independently verifying or exploring the same area is fine; multiple agents independently *building* the same thing because neither knew the other existed is the specific waste this file exists to prevent.

**Rule for any agent editing this project**: before implementing a new capability, search this file for related keywords. If you build something new, add an entry here in the same commit. If you discover something not listed here (a Drive folder, an existing script, a document), add what you found even if you don't act on it yet.

Last updated: 2026-09-09.

---

## Code in this repository (`Braink-Beta`)

| Package | Branch / PR | What it does | Status |
|---|---|---|---|
| `workspace_control_plane` | `workspace-control-plane-v2` / PR #2 | Governed mutation pipeline (intent→pre-observe→delta→admission→actuator→post-observe→verify→receipt) over Google Workspace admin APIs. Directory + Licensing adapters. Sealed capability registry. Hash-chained receipts (`ReceiptChain`, sha256-canonical-JSON). | 51 tests passing. Only in-memory/simulated actuators exercised — Google-backed ones are unexercised stubs, no live credentials used. |
| `keddeh_math` | `keddeh-math-verification` / PR #3 | Exact, tested implementations replacing hand-derived arithmetic from a "Long-Form Mathematical Derivations" document: `rule110.py` (CA + live-formula .xlsx export), `search_partition.py` (disjoint work partitioning, birthday-bound collision probability), `landauer.py`, `queueing.py` (M/G/1 Pollaczek-Khinchine), `shannon.py`, `q32_32.py` (fixed-point log-domain consilience). | 28 tests passing. |
| `braink_reasoning` | `keddeh-math-verification` / PR #3 | Topic-based "answer by computing, not generating text" system. `TopicRegistry` (not sealed, meant to grow) + `ask()` executes real functions. `resolve_understanding_path()` does literal prerequisite-graph traversal. `chain.py`/`qwen_chain.py` realize the IL-LLM thinking/acting chain concept as executable, rehydratable code. `cli.py` gives a real terminal entry point (`python -m braink_reasoning.cli <topic> key=value ...`). | 72 tests passing (part of PR #3's 100 total with keddeh_math). |
| `braink_reasoning/registers/` | same | Data registers backing the topic system: `periodic_table.py` (118-element IUPAC reference data), `compounds.py` (chemistry data transcribed from the user's source spreadsheet, one data-entry error corrected), `lexicon.py` (project glossary: agent/node names, hex IDs — transcribed from "02 - Words (English Lexicon)"), `concept_index.py` (word→concept-tag semantic index, transcribed from Drive's "LIVE_LEXICON" v18, the latest of a 19-version hash-chained history). | Same test count as above. |
| `il_llm` | `il-llm-ledger-integrity` / PR #4 | **Ported from Drive folder `1BbqO4aAd_bNu4eHJlvdDrRmIOC0VZfLG`** (see Drive section below) — not built from scratch. Claim/evidence-ledger CLI: `init/ingest/extract-claims/map-operators/validate/report/status/pinout/prove/mirror/runtime-event/digital-trace`. Ledger hash-chaining added during the port (source had none — see gap note below). | 14 tests passing (source had zero). Zero third-party dependencies. |

## Known Google Drive content (owner: aboudykeddeh276@gmail.com)

Only what's been directly opened and verified is listed. A folder or file not listed here has not been checked — absence from this table means "unknown," not "empty" or "safe to ignore."

| Location | What's actually there | Verdict |
|---|---|---|
| Spreadsheet `1DEv7OnfBQ_HLZSySVIwEdveLDqRv7WQSChJzg7ZdOXw` | ~1.9M-char multi-sheet workbook. Real chemistry compound data (formula/molar mass/composition/phase transitions/pH/classification) — now in `braink_reasoning/registers/compounds.py`. A "System Wiring Matrix" dashboard tab and an "I12 100TB Software MRAM Adapter" claim — **the 100TB figure is not physically representable**: 10M cells × 10K chars/cell tops out at 0.1–0.4TB, 250–1000x short. KEX-LN-01..06 movie/TV "analysis" tabs are templated boilerplate text with scores that are exact /60 fractions (formula-generated, not real content analysis) — treat as placeholder, not data. An "AI Chat Bot" screen-reading mockup with garbled sample OCR output and a "Test Movie Title" placeholder row — unfinished mockup, not working functionality. | Mixed: real data (compounds) + decorative naming (MRAM) + placeholders (movie scores, chat bot) in the same file. Check which part before trusting any of it. |
| 19 file IDs starting `1wX9kdFig...` etc. | **Not 19 separate things** — sequential versions (v0→v18) of one hash-chained, copy-on-write "LIVE_LEXICON" volume. Only v18 (the latest) has content worth reading; v0–v17 are its verified history. | v18 transcribed into `concept_index.py`. Don't re-open v0–v17 expecting new content. |
| Doc `1Hk2sRzlPhELNjEzLQehLmyJh3q0jyZ5NcSrTObKFCuE` ("Final Synchronised Scholarly Monograph v1") | Theory/vocabulary document (WP01–WP06 + synthesis). Real citations (Tarski, Shannon, Turing, Lamport, etc.). Explicitly self-tiers its own claims (DEFINED / IMPLEMENTATION-EVIDENCED / SIMULATION-SUPPORTED / PROPOSED THEOREM / OPEN EMPIRICAL CLAIM) and states most content isn't implemented or tested. | Not a spec of anything built. Reference for vocabulary/direction only. |
| Doc `1swaGvRs6Itiilo6lbLk8JFWF1-b1vYH1lijAah7aQQQ` ("IL-LLM SESSION") | An honest self-audit of a prior HTML prototype (R1/R2/R3): catches its own fake Bitcoin-authority string, a self-minted receipt, and admits a claimed "tensor" (`H[o,l,s,t]`) was just a plain object. | R1–R3 artifacts are explicitly unverified/failing — don't treat as working. The audit methodology (bilateral mirror/digest check) is worth reusing. |
| Folder `1V-1GIGJXD_Zbvcz4ZZuRnbmZvc6KGEMo` ("il-llm-core") | Empty. | Nothing here. |
| Folder `1H9IuuMYTPEYa_bhgP13gUoijSRDccsmF` ("il-llm-core") | One file: `README.md`, a scope stub — says the real worktree doesn't exist yet. | Planning doc only. |
| Folder `1tKwAsGb9pe9VH5MOpYpssa7y98tjx60Q` ("il-llm-core") | Real, structured project skeleton: `worktrees/, schemas/, book_formalize_work/, il_llm/, skills/, data/, video_apex_delivery/, docs/, corpus/, tests/` + more (listing not exhaustive). | Not yet fully inventoried — only a directory listing has been done, not file contents. |
| Folder `1632l92A5yBiwQe7dfPpRfWJwDxlts3Dc` ("il_llm") | ~20+ Python files including `contradiction_linker.py`, `governance_instruction_set.py`, `akih.py`, `k_sys.py`, `worktree_engine.py`, `coding_braink.py`. `governance_instruction_set.py` was read: it returns a static config dict + one sha256 hash of that static blob — **not** a per-event gate, doesn't touch any ledger. | Distinct from folder `1BbqO4aAd...` below despite the same display name — different file set. Not fully ported; only one file read so far. |
| Folder `1BbqO4aAd_bNu4eHJlvdDrRmIOC0VZfLG` ("il_llm") | The 16 files now ported as this repo's `il_llm` package (see table above). | Fully ported, tested, and fixed (PR #4). |
| Folder `1gtzdRPg3sNV-4qhGVik93d3frwUUStKu` ("il_llm") | Empty. | Nothing here. |
| Folder `1O0riz4FUpeLnL7VpWv0tK2B-lwuR_R1S` ("il_llm") | Empty. | Nothing here. |

## Standing holds

- **Synthetic MAC/IP device-identity generation at scale**: not implemented, not stubbed. Reads as a Sybil/spoofing pattern against any external system that trusts device identity (e.g. per-worker reward allocation on a mining pool), independent of any math or naming wrapped around it. Needs an explicit, specific legitimate-use answer before any code gets written — not a general go-ahead.

## Shared conventions across all four packages above

- **Tamper-evidence**: one hash-chaining scheme (sha256 over canonical JSON, each record/receipt/step carries the previous one's hash) used identically in `workspace_control_plane.receipts`, `braink_reasoning.chain`, and `il_llm.io.append_record`. All three share the same honest limitation: a backward-linking chain cannot detect tampering with only the very last entry (nothing points forward to it) — this is tested and documented in all three, not hidden.
- **Status tagging**: `VERIFIED`/`CONCEPTUAL` (braink_reasoning), `LIVE`/`SIMULATED` (workspace_control_plane actuators) — the same idea, applied consistently: a claim is either backed by an executed, tested computation, or explicitly labeled as assumed/illustrative. Never state a cryptographic near-certainty (e.g. SHA-256 collision resistance) as exactly zero.
