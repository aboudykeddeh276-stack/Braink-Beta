# Workplan 02: Screen-Reading ("RGB"/OCR) Capability — Decide, Then Build or Shelve

**Status**: blocked on a decision. **Depends on**: nothing technical; needs one decision from the project owner. **Grounded in**: `SYSTEM_INVENTORY.md`'s "AI Chat Bot" entry, task #10 from this session's tracker.

## Why this exists

A spreadsheet section described as letting the system "learn to read a screen" was reviewed this session. What was actually there: a garbled sample output (repeated-triplet character decoding that doesn't cleanly spell anything) and a placeholder "Test Movie Title" row. Conclusion at the time: unfinished mockup, not working functionality. This workplan exists so that conclusion doesn't quietly become permanent by default — it names the fork explicitly instead of leaving it to erode.

## The decision this needs first

Is a real screen/pixel-reading capability (something that takes rendered screen content — pixels, or a structured DOM/canvas description — and extracts characters or state from it) actually wanted as a Braink capability, or was the spreadsheet section itself just an early sketch that shouldn't be built toward as specified?

This is a real technical fork, not busywork:
- **If real screen-reading is wanted**: this is a computer-vision/OCR problem (or, if the "screen" is always a known structured format like an HTML canvas or a spreadsheet grid, a much simpler structured-extraction problem — worth clarifying which, since the two have very different implementations and neither should be assumed).
- **If the mockup's specific design (repeated-triplet sampling, `HD_CONFIRM` grid coordinates) is meant to be the actual approach**: that specific design needs to be understood well enough to reproduce correctly, not guessed at from one garbled sample.

## Steps once the decision is made

1. **If shelved**: mark it explicitly retired in `SYSTEM_INVENTORY.md` rather than leaving it ambiguous, so a future agent doesn't rediscover the same mockup and re-open this question from zero.
2. **If pursued as real OCR/CV**: scope a minimal version first — e.g., given a rendered image of a known, small character set (not an open-ended screen), extract the characters correctly and prove it against a held-out test image, before generalizing. Use an existing, well-tested library rather than hand-rolling pixel classification.
3. **If pursued as structured extraction** (the "screen" is always a canvas/grid the system already has structured access to, so no actual image processing is needed): this is much closer to what `braink_reasoning`'s existing registers already do — the "reading" is really just a new topic/register over already-structured data, not a vision problem at all. Confirm which case this is before writing any code, since building CV machinery for a problem that's actually structured-data lookup would be pure waste.

## Braink constraint check

Structured extraction (case 3 above) fits the Braink answer-path constraint directly: it's a new register/topic over already-structured data, no generation involved. Real OCR/CV (case 2) also fits *if* its output is a discrete, storable value (extracted characters/state) that becomes a register lookup — it does not fit if "reading the screen" ends up meaning "have a model describe what's on the screen in prose" at answer time. Whichever case this turns out to be, keep the boundary where `CLAUDE.md` draws it: extraction/computation, not narration.

## Done criteria

- A decision is recorded (built, or explicitly shelved) — not left ambiguous.
- If built: a minimal, tested version exists that passes a concrete extraction test on real input, not a mockup with a garbled sample output standing in for a result.
