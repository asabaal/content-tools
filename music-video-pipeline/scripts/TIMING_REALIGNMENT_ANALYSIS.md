# Timing Realignment: Problem & Solution

## Example: Line 3 ("Holy holy holy")

### The Problem

**Source of truth** `lyrics_synced.json` places line index 2 ("Holy holy holy") at
7.00–7.68s (a 0.68s window for three sung words). Its word-level timestamps
are even tighter:

| Word  | start  | end    | duration |
|-------|--------|--------|----------|
| Holy  | 7.04   | 7.207  | 0.167s   |
| holy  | 7.207  | 7.373  | 0.166s   |
| holy  | 7.373  | 7.540  | 0.167s   |

0.17s per sung word is unreasonably short — each word would need to be
gabbled at 350 ms per syllable, which does not match the actual performance.

### Why It Happens

The synchroniser (`lyrics/synchronizer.py`) uses audio analysis to align lyric
words to vocal onsets/offsets. When the analysis is imprecise (e.g. low
confidence in a dense harmonic passage), it compresses word timestamps into an
unrealistically narrow window.

### What the Stems Provide

The **combined** transcription covers 0.00–6.54s but has a gap from 6.54 to
10.48s — no segments exist for this range.  Line 3 falls entirely inside this
gap.

The **lead** vocal transcription does have coverage for this gap:

| segment            | text                    | words                                      |
|--------------------|-------------------------|--------------------------------------------|
| 7.34–13.02         | "2E only only you..."   | 2E 7.34–8.84, only 8.84–8.98, only 8.98–9.70, you... 9.70–13.02 |
| 13.02–30.88        | "ay yoo ee yoo..."      | (catch-all with 9.5s word spans)           |

The lead segment at 7.34–13.02 has garbled text (the transcriber heard "2E"
instead of "Holy") but its **timestamps** are driven by real vocal energy and
are more reliable than the synchroniser's guesses.

### The Solution (per line)

For each line that needs realignment:

1. **Find the best stem segment** by timestamp proximity to the line's midpoint.
   Prefer segments that overlap the line; use distance as a tiebreaker.

2. **Extract word timing** from the segment's word timestamps. If the segment
   has enough fine-grained words that overlap the line's time range, use them
   directly. Otherwise, fall back to even distribution across the overlapping
   time range.

3. **Write a `timing_overrides` entry** into `script.json`. The renderer
   applies it in `_apply_timing_overrides()`, deep-overwriting `start`, `end`,
   and `words` on the corresponding synced line.

### Applied to Line 3

Using the lead segment 7.34–13.02:

- Override **start** = 7.34 (when the lead vocal energy begins)
- Override **end** = 8.84 (end of the segment's first word, which represents
  the full sung phrase "Holy holy holy" before the next lyric begins)
- Override **words** = evenly distribute 3 words across the 1.5s window:

| Word  | start  | end    | duration |
|-------|--------|--------|----------|
| Holy  | 7.34   | 7.84   | 0.50s    |
| holy  | 7.84   | 8.34   | 0.50s    |
| holy  | 8.34   | 8.84   | 0.50s    |

This gives each word a natural sung duration (~500ms) instead of the
compressed 167ms, without requiring any changes to `lyrics_synced.json`
itself.

### General Pattern

The same pattern repeats across ~30 lines:

- `lyrics_synced.json` has compressed or broken timing (zero-duration words,
  implausibly short windows, or a line spanning 118s due to a broken end
  timestamp).
- One or more stem transcriptions have segments that overlap the line with
  better timestamps, even when the stem's recognised text is garbled.
- The fix is a `timing_overrides` entry in `script.json` using the stem's
  segment timing, with fallback to even distribution when the segment's word
  count doesn't match the lyric line's word count.

The current implementation in `realign_timing_v2.py` automates this for all
flagged lines at once, writing 30 overrides in a single pass.
