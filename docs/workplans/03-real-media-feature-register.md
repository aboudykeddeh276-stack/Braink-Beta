# Workplan 03: Real Media (Movie/TV) Feature Register

**Status**: not started — the placeholder it would replace has been identified but not removed. **Depends on**: a methodology decision (see below). **Grounded in**: `SYSTEM_INVENTORY.md`'s KEX-LN-01..06 entry, task #6 from this session's tracker.

## Why this exists

Early in this project, manuscripts/media were described as broken down into concrete features: writing style, emotion wording, sentence length, impact, cliffhangers, stage motion vs. wording. What actually exists in the spreadsheet under that heading (`KEX-LN-01`..`06`) is different: one template sentence with names substituted across all 100 rows per sheet, and a "Calculated Matrix Baseline" score that is, in all 6 sampled rows, an exact fraction with denominator 60 and zero rounding residue — a formula artifact, not a measurement of anything about the actual shows/films named. If a real media-feature register is still wanted, it needs to be built from the described features, not from this placeholder.

## The decision this needs first

What actually produces the feature values (writing style, emotion, sentence length, impact, cliffhangers)? Three real options, each with a different implementation:

1. **Computed directly from source text** (e.g. sentence length is a literal average over the actual script/transcript). This requires having the actual source text for each work, which is a separate, larger acquisition question (and, per the earlier discussion in this session, a copyright-sensitive one if full scripts are involved — deriving numeric features from text you analyze is very different from storing or serving the text itself, so keep it to the former).
2. **Scored by an LLM reading a synopsis/description** (i.e., an actual model call producing a style/emotion rating). This is legitimate **only as an offline data-preparation step** — the model runs once, ahead of time, to produce a value that then gets stored in the register. Per `CLAUDE.md`'s constraint on what Braink actually is (not an LLM, no tokenized generation at answer time), the *query-time* lookup must still be a plain register read of a stored value, never a live model call made in response to a question. Whatever value gets stored this way is labeled `CONCEPTUAL`/model-derived, not `VERIFIED` — a language model's rating is an opinion, not a measurement, and that distinction doesn't go away just because the call happened in advance.
3. **Manually curated** (a human rates each work on each axis). Real and honest if that's what's wanted, but slow to scale to hundreds of rows, and should be labeled as human-curated rather than "calculated."

Each path is legitimate; picking one determines whether this becomes a `keddeh_math`-style verified computation, a clearly-tagged model-opinion register, or a manually-maintained dataset. Building the register before deciding this just reproduces the original problem (a plausible-looking number nobody can trace back to a method).

## Steps once the methodology is chosen

1. Pick a small pilot set (5–10 works, not all ~600 rows across the 6 sheets) and produce real feature values for them using the chosen method.
2. Wire the pilot into `braink_reasoning` as a new register (`braink_reasoning/registers/media_features.py`), following the exact pattern of `compounds.py`: a lookup function, a status tag appropriate to the method chosen (see above), and tests.
3. Only after the pilot's values hold up to spot-checking, decide whether to scale to the remaining rows — do not batch-generate all ~600 before validating the method on a small set.
4. Retire the `KEX-LN-01..06` placeholder framing in `SYSTEM_INVENTORY.md` once real values replace it, so the two aren't confused later.

## Done criteria

- A methodology is chosen and stated explicitly (computed / model-derived / human-curated).
- A pilot register exists in `braink_reasoning` with correctly tagged status and real tests.
- The placeholder scores are no longer referenced as if they were real analysis anywhere in the repo or its docs.
