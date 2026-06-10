# Timing Issues Guide

Generated: 2026-06-10 (updated 2026-06-10)
Pipeline version: music-video-pipeline (whisper fallback: small → medium → large-v3)

## Overview

After running the full 42-song collection through the updated pipeline, there are **1,993 timing issues** remaining across all songs. This document explains what each category means with concrete examples.

**Previous milestones:**
- Whisper fallback (small → medium → large-v3) reduced issues from 2,731 → 2,623
- Text overflow fix (multi-row word positioning) eliminated 630 layout issues: 2,623 → 1,993

---

## Issue Categories

### 1. Duration Overflow — 999 issues

**What it is**: A single word is assigned too much time. The word would appear on screen for way longer than a human would actually say it. Any word with a duration greater than 1.5 seconds is flagged.

**Why it happens**: The onset detector finds the start of a word (e.g., "A" at 28s) but the next detected vocal event isn't until much later (e.g., 34.7s). The word stretches to fill the entire gap because there's no better evidence of where it should end.

**Real example**:
- Song: `a-word`, Line 0: "A word,"
- Word **"A"**: timestamps 28.011 → 34.752 = **6.7 seconds** for a single syllable
- Source: `vocal_onset_only` — the onset detector found the start but not the end
- Repair: cap the duration to a reasonable maximum

**Real example**:
- Song: `a-word`, Line 3: "A meditation,"
- Word **"meditation,"**: timestamps 114.395 → 117.990 = **3.6 seconds**
- Source: `whisper_plus_vocal_onset` — even the best source sometimes assigns long durations when there's a pause after a word
- Repair: manual review

**Sub-categories**:
- `onset_only_overflow` (336): Word has only onset evidence, no end boundary. Fix: cap duration.
- `unknown_overflow` (663): Word has Whisper timing but it's still too long. Fix: investigate per case.

---

### 2. Duration Undersize — 823 issues

**What it is**: A word gets assigned too little time. It would flash on screen impossibly fast — literally invisible to the viewer. Any word with a duration under 0.04 seconds is flagged.

**Why it happens**: When multiple words need to fit into a short time window (e.g., 6 words in 0.24 seconds), the interpolation formula divides the time evenly, producing near-zero durations per word. This happens when onset segments are too narrow or when many words are assigned to a single short segment.

**Real example**:
- Song: `a-word`, Line 5: "Taste what you hear"
- Word **"Taste"**: timestamps 124.405 → 124.445 = **0.040 seconds** (4 hundredths of a second)
- Source: `whisper_plus_vocal_onset` — even the best source produces this when words are crammed together
- You would never see this word on screen

**Real example**:
- Song: `a-word`, Line 30: "Yes, he is"
- Word **"is"**: timestamps 237.080 → 237.120 = **0.040 seconds**
- Source: `transcription` — small word, tight gap between other words
- Repair: redistribute time across the line's words more evenly

**Sub-categories**:
- `interpolated_undersize` (253): Word had no transcription match at all, was interpolated into a tiny gap. These remain because even medium/large whisper models couldn't find them.
- `unknown_undersize` (570): Word had a timing source (Whisper, onset, etc.) but still ended up too short. These need investigation.

**Words under 0.04s across the collection**: 120 words (down from 344 before the whisper fallback)

---

### 3. Gap from Prev — 171 issues

**What it is**: There's a gap between two consecutive words that's too large. There's dead space where nothing is shown on screen but something should be. Any gap over 0.5 seconds is flagged.

**Why it happens**: The line boundary reconciliation (`_reconcile_boundaries`) sometimes produces timestamp inversions where line N ends after line N+1 starts. Or the word-level timing leaves a gap between the end of one word and the start of the next within a line.

**Real example**:
- Song: `a-word`, Line 20: "Who are you, human being, child of God"
- Word **"child"**: gap of **0.58 seconds** from the previous word
- The word "of" ends, then nothing for over half a second, then "child" starts
- Source: `transcription`

**Real example**:
- Song: `a-word`, Line 43: "Blessed is the LORD our God, King of the universe,"
- Word **"King"**: gap of **1.10 seconds** from the previous word "God,"
- A full second of dead air between words
- Source: `whisper_plus_vocal_onset`

**Real example (timestamp inversion)**:
- Song: `love-them-harder`, Lines 64-65
- Line 64 ends at 208.10s but Line 65 starts at 202.21s
- Line 65 starts *before* Line 64 ends — the boundaries are inverted
- This is a bug in the boundary reconciliation logic

**Repair**: Fix the boundary reconciliation algorithm to prevent inversions. Then redistribute gap time to adjacent words.

---

### 4. Text Overflow — RESOLVED (was 630 issues)

**What it was**: When rendered as on-screen text in the video, words extended past the visual boundary of their line. The word's visual width exceeded the available horizontal space.

**How it was fixed**: Each overflowing lyric line was split into multiple on-screen rows using the word-level `y` positioning system in the script.json files. Words are now assigned to rows at y=0.2 (top), y=0.5 (center), or y=0.8 (bottom), with each row independently auto-centered. 185 lines across 31 songs were reorganized. Font-width measurement with a 70% safety margin ensures each row fits within the canvas safe zone (1,296px of 1,727px max).

**Example fix** — `woe-to-you` Line 0 (15 words, was 351px overflow):

Before (all one row — overflowed both edges):
```
y=0.5: Woe to you, you who lack understanding! You cast out from your presence your aid.
```

After (3 rows — fits cleanly):
```
y=0.2: Woe to you, you who
y=0.5: lack understanding! You
y=0.8: cast out from your presence your aid.
```

---

## Cross-Line vs Within-Line Classification

Duration issues (overflow and undersize) can be caused by problems **within a single lyric line** or by **boundary reconciliation between lines**. This classification determines the correct repair strategy.

### Root cause: how word durations are determined

1. Each lyric line gets a **time budget** (line.start → line.end)
2. `_reconcile_boundaries` adjusts line boundaries based on vocal onset evidence — pushing a line's end later or pulling the next line's start earlier
3. Within each line's budget, `_compute_word_timings` distributes time across words based on their source (Whisper, onset, interpolated)
4. If one word takes too much time, neighboring words get squeezed

This means **a long word in line N can compress words in line N+1** by pushing the boundary between them. The squeeze effect cascades: cross-line boundary shift → compressed line budget → within-line redistribution → undersize words.

### Classification results (1,822 duration issues across 1,222 affected lines)

| Category | Lines | % | Issues | Overflow | Undersize |
|---|---|---|---|---|---|
| **within_line** | 752 | 62% | 963 | 486 | 477 |
| **cross_line** | 173 | 14% | 216 | 141 | 75 |
| **both** | 297 | 24% | 643 | 372 | 271 |

### Within-line (62% of affected lines)

The line's time budget is reasonable, but one word hogs it. Typically a `vocal_onset_only` word soaks up most of the line's duration, leaving neighboring words with near-zero time.

**Real example** — `child-of-god-who-you-be` Line 5: "I'm a child of God (who you be?)"
- Line budget: 2.35s / 8 words = 0.29s avg (reasonable)
- But: onset_only word **"you"** takes 3.3s (141% of the line!)
- Meanwhile: **"I'm"** gets 0.012s — invisible on screen
- Coefficient of variation across word durations: 1.30 (extremely uneven)
- **Fix**: cap individual word durations, redistribute the surplus

### Cross-line (14% of affected lines)

The line was given too much or too little time relative to its word count. No timestamp inversions were found — the boundaries are non-overlapping, but the budget allocation is wrong.

**Real example** — `electric-pulse` Line 15: "Embracing the unknown, letting go (ooooh)"
- Line budget: 11.55s / 6 words = 1.93s avg (stretched — nearly 2 seconds per word)
- No inversions or gaps, but the line was given far too much time
- All 6 words overflow (1.0–3.7s each), evenly spread (CV = 0.53)
- **Fix**: better boundary reconciliation to allocate time proportionally to word count

### Both (24% of affected lines)

A compressed or stretched line budget **plus** uneven word distribution within it. The worst of both worlds.

**Real example** — `nothing-is-impossible` Line 10: "We can't conceive of that so it must be the devil - strike!"
- Line budget: 0.35s / 13 words = 0.027s avg (severely compressed — cross-line)
- But also: onset_only word **"strike!"** takes 0.29s = 84% of the line (within-line)
- The remaining 12 words share 0.06s = ~0.005s each
- 10 undersize issues, CV = 1.14
- **Fix**: fix the boundary first (give the line more time), then redistribute within

### Key insight: no timestamp inversions in production data

While the `love-them-harder` inversion (line 64 ends at 208.10s, line 65 starts at 202.21s) was documented during earlier analysis, the cross-line classification found **zero inversions** in the current synced data. The boundary reconciler produces clean, non-overlapping boundaries. The cross-line issues are **budget allocation problems** — lines get too much or too little time relative to their word count — not boundary bugs.

### Cross-line driver breakdown

| Driver | Count |
|---|---|
| Stretched avg (> 1.5s/word) | 206 |
| Compressed avg (< 0.15s/word) | 126 |
| Line < 0.5s with > 2 words | 95 |
| Has gap_from_prev issue | 86 |

### Within-line driver breakdown

| Driver | Count |
|---|---|
| Uneven distribution (CV > 1.0) | 469 |
| Word dominance (> 50% of line) | 462 |
| Onset-only overflow (> 2s) | 146 |
| Interpolated words squeezed | 134 |

---

## Source Labels

| Source | Meaning | Issues | % of total |
|--------|---------|--------|-----------|
| `whisper_plus_vocal_onset` | Whisper transcription matched to a vocal onset | 691 | 35% |
| `transcription` | Whisper word-level timing used directly | 536 | 27% |
| `vocal_onset_only` | Vocal onset detected the start but end was stretched | 395 | 20% |
| `interpolated` | No onset or transcription — timestamps evenly divided | 328 | 16% |
| `vocal_onset` | Vocal onset provided both start and end | 43 | 2% |

Even the best source (`whisper_plus_vocal_onset`) produces 35% of the issues — timing quality problems aren't limited to interpolated words.

---

## Whisper Fallback Results

The pipeline now tries three whisper models in order: `small` → `medium` → `large-v3`. It stops when all lyrics are matched or the largest model is reached.

| Metric | Before (small only) | After fallback | After text fix | Total Change |
|--------|---------------------|----------------|----------------|--------------|
| Total issues | 2,731 | 2,623 | 1,993 | -738 (27%) |
| Words < 0.04s | 344 | 120 | 120 | -224 (65%) |
| Interpolated issues | 556 | 338 | 328 | -228 (41%) |
| `interpolated_undersize` | 471 | 253 | 253 | -218 (46%) |
| Text overflow | 630 | 630 | 0 | -630 (100%) |

---

## Repair Priorities

Priorities are ordered by the cross-line vs within-line classification. Cross-line fixes should come first because they expand the time budget for compressed lines, which automatically improves within-line distribution.

1. **Fix cross-line budget allocation** (173 lines, 216 issues): The boundary reconciler gives some lines too much or too little time relative to word count. Fix `_reconcile_boundaries` to allocate time proportionally. This will also improve many "both" lines (297 lines, 643 issues) by giving them a proper budget first.

2. **Cap within-line duration overflow** (752 lines, 963 issues): Algorithmically cap individual word durations to a max threshold (e.g., 1.5s) when the source is onset-only, then redistribute the surplus to neighboring words. This fixes both overflow and undersize in a single pass since the squeeze effect is the root cause of undersize.

3. **Remaining interpolated** (328): These have no transcription evidence even after large-v3. Options: transcribe the combined vocals stem, or flag for manual timing.

4. **Gap from prev** (171 issues): Dead space between consecutive words. Will be partially addressed by boundary reconciliation fixes (priority 1). Remaining gaps may need manual adjustment.
