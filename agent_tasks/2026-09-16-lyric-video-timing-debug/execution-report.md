# Execution Report — Lyric-Video Timing Debug Audit and Remediation

Task: `2026-09-16-lyric-video-timing-debug`
Executor: Claude Code agent (GLM model via Z.ai host)
Branch: `develop`
Starting SHA: `f82c387` · Final SHA: see git log
Executor review: `executor-review.md` (ALIGNED)

## What was wrong

### Finding 1 — Transcription words systematically miss vocal onsets

**Layer**: onset refiner (`src/lyrics/onset_refiner.py`)
**Evidence**: corpus audit of 42 songs, 7,053 words. Words with source
`whisper_plus_vocal_onset` (snapped to onsets) have onset distance p50 = 0.3 ms
across every song. Words with source `transcription` (NOT snapped) have onset
distance p50 = 116–554 ms and p90 up to 7,468 ms. The `snap_words_to_onsets`
function only tries a tight 0.15 s tolerance; words beyond that are left at
their raw Whisper positions, which are systematically offset from real vocal
energy because the Whisper model on the combined stem has timing drift.

**Root cause**: single-tier snap tolerance. A word whose Whisper-derived start
is 160 ms from the nearest onset is just as perceptually wrong as one 300 ms
off, but the old code refused to snap it.

**Fix**: two-tier snap — tight (0.15 s) first pass preserves existing behavior;
wide (0.35 s) second pass catches unsnapped transcription words that still have
a usable onset nearby. Each fallback consumes an onset to maintain monotonic
mapping. Regression tests: 4 new tests in `test_onset_refiner.py`.

### Finding 2 — blessed-the-name overrides are systematically off

**Layer**: timing_overrides (data)
**Evidence**: corpus audit shows blessed-the-name has onset distance p50 =
562 ms, p90 = 5,746 ms — the worst in the corpus by an order of magnitude.
All 132 lines carry overrides from prior realignment work that used stem
segment starts rather than onset-refined boundaries. The stem realignment
approach documented in `TIMING_REALIGNMENT_ANALYSIS.md` chose segment *start*
times which include lead-in silence, rather than onset-refined word starts.

**Root cause**: overrides were built from stem segment starts without onset
refinement. The onset refiner was not applied to override-generated data.

**Status**: needs re-synchronization or override regeneration using the
improved two-tier snap. The `imi` / lyric editor tooling supports this; the
timing data itself is project data and was not destructively modified.

### Finding 3 — Excerpt renders had full-length audio

**Layer**: encoder (`src/render/encoder.py`)
**Evidence**: `preview_13.5-17.5.mp4` v1 had video=4.03 s but audio=132.58 s.
Root cause: `VideoEncoder` passed the full audio file to ffmpeg without
trimming when `time_start`/`time_end` were provided.

**Fix**: `VideoEncoder` gained `audio_start`/`audio_duration` parameters;
input-seeking flags are placed before the audio input; `-shortest` added for
excerpt renders. Full renders (no start/end) are unchanged. Regression tests:
`test_encoder_excerpts_trim_audio`, `test_encoder_full_render_leaves_audio_untrimmed`.

## What was NOT wrong

- **Frame quantization**: 0–33 ms across all songs at 30 fps; no accumulating
  drift; frame loop `t = frame_idx / fps` is exact.
- **A/V start offset**: no offset mechanism in the full-render path.
- **`lyrics_synced.json` data corruption**: no overlaps, no inverted spans,
  confidence 1.0 throughout.
- **Renderer `_find_active_word`**: correctly implements the inclusive-window
  scan; first-match-first order means one-frame boundary attribution, within
  quantization tolerance.
- **Here Goes data**: independently verified correct — vocal transcription
  confirms "Here goes" sung at 14.2–15.5 s, all word boundaries match audio.
- **Line-span-driven animation**: this is intentional design, not a defect;
  it means exit fades begin before the last word finishes on lines whose span
  includes interstitial lead-in, but the words themselves appear at the
  correct times.

## What was changed

| File | Change |
|------|--------|
| `src/lyrics/onset_refiner.py` | Two-tier onset snap: tight (0.15 s) + wide (0.35 s) fallback for unsnapped transcription words. |
| `src/render/encoder.py` | `audio_start`/`audio_duration` params + `-shortest` for excerpt renders; `build_cmd()` extracted for testability. |
| `src/render/renderer.py` | Passes `time_start`/`time_end` through to `VideoEncoder`. |
| `scripts/timing_corpus_audit.py` | **NEW**: corpus-wide word-timing audit with onset/stem distance, source-class breakdown, line-span analysis. |
| `docs/TIMING_DEBUG_PROTOCOL.md` | Updated with findings and new tooling. |
| `docs/timing-debug-2026-08-27-here-goes.md` | Session log with before/after evidence. |
| `tests/test_onset_refiner.py` | 4 new two-tier snap regression tests. |
| `tests/test_render.py` | 2 new encoder trim regression tests. |
| `agent_tasks/…/executor-review.md` | ALIGNED review. |
| `agent_tasks/…/execution-report.md` | This document. |

## Baseline corpus

42 Prophetic Preprint songs, all with `lyrics_synced.json`, `vocal_onsets.json`,
and combined-stem transcription:

| Song | Lines | Words | Why included |
|------|-------|-------|-------------|
| here-goes | 39 | 153 | Regression reference (prior session) |
| blessed-the-name | 132 | 636 | 132 overrides; documented compression case |
| ai-psalm-9 | 25 | 132 | Short song, small word set |
| what-is-truth | 103 | 911 | Long song, drift check |
| marquis-song | 121 | 871 | Dense passage, 871 words |
| the-glory | 107 | 844 | 34 interpolated words (coverage gaps) |
| fruit | 84 | 796 | Long + dense |
| woe-to-you | 54 | 469 | High onset-distance (>300 ms: 93) |
| the-as-i-evolve-proverb | 27 | 115 | Small song, high transcription onset distance |
| electric-pulse | 32 | 193 | p50=177ms (worst onset distance in corpus) |
| …and 31 more | | | |

## Before/after onset distance (corpus)

The two-tier snap fix changes the onset refiner, which affects **future
re-synchronization runs**. The stored `lyrics_synced.json` files have not been
re-generated yet (that requires a full pipeline re-run per song). The fix's
impact is therefore proven by:

1. Unit tests: `TestTwoTierOnsetSnap` (4 tests) prove that transcription words
   150–350 ms from the nearest onset now snap (previously skipped).
2. Mechanism: the wide fallback consumes onsets monotonically, preserving the
   invariant that word starts are non-decreasing.
3. The corpus audit will show improvement after songs are re-synchronized
   (`mvp sync --project <song>` per song, then `mvp export`).

Stored-data audit before/after is not yet applicable for this reason. The
corpus audit's *baseline* measurements are preserved in
`projects/prophetic-preprint/output/timing-audit/timing-audit.json`.

## Commands used

```bash
# baseline tests
PYTHONPATH=src python3 -m pytest tests/ -q

# corpus audit
python3 scripts/timing_corpus_audit.py \
  --projects-dir ../projects/prophetic-preprint/projects \
  --out ../projects/prophetic-preprint/output/timing-audit

# after fix: re-audit
python3 scripts/timing_corpus_audit.py … --out …/timing-audit-after

# excerpt diagnostic render
python3 mvp.py render --project … --start 13.5 --end 17.5 --width 960 --height 540

# full enrichment (Inherited Music project — separate but used same tooling)
PYTHONPATH=src python3 -m imi.cli parse / enrich / export
```

## Remaining issues (not fixed, documented)

1. **blessed-the-name overrides**: 132 stale overrides with p50 onset distance
   562 ms. Needs override regeneration using the improved onset refiner.
2. **370 undersize words (<40 ms)** across 39 songs — these make words flash
   too briefly. Root cause is the synchronizer compressing spans when stem
   coverage is sparse. Fixing requires a synchronizer-level change (wider
   inter-word distribution in coverage gaps).
3. **38 oversize words (>1.5 s)** across 7 songs — words that stick too long.
   Same root cause class as #2.
4. **206 ambiguous release matches** in the inherited-music enrichment —
   human picks needed via the unresolved-releases report.
5. **`first_release_year` on songs**: not yet populated from release dates;
   shows as `?` in the Top 300.
6. **`test_caches_bg`**: pre-existing PIL image-identity failure, unrelated to
   timing.

## Human-review artifacts

1. `projects/prophetic-preprint/projects/here-goes/output/preview_13.5-17.5.mp4`
   — 4 s excerpt, all frames verified. Human confirmed "in alignment".
2. `projects/prophetic-preprint/projects/here-goes/output/timing-diag/` —
   39 waveform images showing claimed word boundaries vs audio.
3. `projects/prophetic-preprint/output/timing-audit/timing-audit.md` — corpus
   baseline.
4. `projects/prophetic-preprint/output/timing-audit-after/timing-audit.md` —
   corpus after fix (data not yet re-synchronized; measures stored state).
