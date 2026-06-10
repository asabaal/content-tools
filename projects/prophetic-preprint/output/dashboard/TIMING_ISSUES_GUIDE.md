# Timing Issues Guide

Generated: 2026-06-10
Pipeline version: music-video-pipeline (whisper fallback: small → medium → large-v3)

## Overview

After running the full 42-song collection through the updated pipeline (with whisper model fallback), there are **2,623 timing issues** remaining across all songs. This document explains what each category means with concrete examples.

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

### 4. Text Overflow — 630 issues

**What it is**: When rendered as on-screen text in the video, the word extends past the visual boundary of its line. This is a **layout/rendering problem**, not a timing problem. The word's visual width exceeds the available horizontal space.

**Why it happens**: Some lyric lines have many words (8-12+) that don't fit on a single line at the current font size. The text layout engine clips the overflow.

**Real example**:
- Song: `ai-psalm-1`, Line 9: "The destroyer, the devil, who seeks to kill, steal"
- Word **"The"**: clips 83px past the left edge
- Word **"destroy"**: clips 83px past the right edge
- 10 words on one line at the set font size simply don't fit

**Real example**:
- Song: `ai-psalm-1`, Line 13: "This body screams! It believes there is a threat, "
- Word **"This"**: clips 9px past the left edge
- Word **"threat,"**: clips 9px past the right edge

**Real example**:
- Song: `ai-psalm-1`, Line 21: "I, too, have seen things I am not yet permitted to"
- Word **"too,"**: clips 76px past the left edge
- Source: `whisper_plus_vocal_onset` — the timing is fine, the text just doesn't fit

**Repair**: This is a rendering/layout fix, not a timing fix. Options: reduce font size for long lines, wrap text to multiple lines, or truncate with ellipsis.

---

## Source Labels

Every word in the synced lyrics has a `source` field indicating where its timing came from:

| Source | Meaning | Issues | % of total |
|--------|---------|--------|-----------|
| `whisper_plus_vocal_onset` | Whisper transcription matched to a vocal onset | 1129 | 43% |
| `transcription` | Whisper word-level timing used directly | 708 | 27% |
| `vocal_onset_only` | Vocal onset detected the start but end was stretched | 404 | 15% |
| `interpolated` | No onset or transcription — timestamps evenly divided | 338 | 13% |
| `vocal_onset` | Vocal onset provided both start and end | 44 | 2% |

Even the best source (`whisper_plus_vocal_onset`) produces 43% of the issues — timing quality problems aren't limited to interpolated words.

---

## Whisper Fallback Results

The pipeline now tries three whisper models in order: `small` → `medium` → `large-v3`. It stops when all lyrics are matched or the largest model is reached.

| Metric | Before (small only) | After (fallback) | Change |
|--------|---------------------|-------------------|--------|
| Total issues | 2731 | 2623 | -108 |
| Words < 0.04s | 344 | 120 | -224 (65%) |
| Interpolated issues | 556 | 338 | -218 (39%) |
| `interpolated_undersize` | 471 | 253 | -218 (46%) |

---

## Repair Priorities

1. **Cap duration overflow** (336 onset_only_overflow): Algorithmically cap word durations to a max threshold (e.g., 1.5s) when the source is onset-only
2. **Fix boundary inversions** (171 gap issues): Fix `_reconcile_boundaries` to prevent line N from ending after line N+1 starts
3. **Redistribute undersize words** (823 duration_undersize): When words within a line are too short, redistribute available time more evenly
4. **Remaining interpolated** (338): These have no transcription evidence even after large-v3. Options: transcribe the combined vocals stem, or flag for manual timing
5. **Text overflow** (630): Rendering/layout fix — reduce font size for long lines or wrap text
