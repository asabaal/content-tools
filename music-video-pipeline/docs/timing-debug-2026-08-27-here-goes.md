# Timing Debug Session Log — "Here Goes" — 2026-08-27

Reference song: `projects/prophetic-preprint/projects/here-goes` (126 BPM, `HERE GOES.wav`).
Protocol: `docs/TIMING_DEBUG_PROTOCOL.md`. GPU: unavailable (Ava) — CPU-only diagnostics.

## Hypotheses & findings (initial static analysis)

- **H1 frame-quantization/drift**: DISPROVEN as a major factor. Word visibility
  latency vs intended start is 0–33 ms across all 111 words (pure 30 fps
  quantization; no drift — frame loop uses `t = frame_idx / fps` exactly).
- **H2 A/V start mismatch**: no offset mechanism found (audio muxed from 0,
  video from frame 0; first word at 0.192 s matches data).
- **H3 localized timestamp corruption**: none in `lyrics_synced.json` — word
  times are contiguous within lines, no overlaps, confidence 1.0 throughout.
  Notable: line 1's span is 1.17–16.02 (14.85 s) while its words occupy only
  14.43–16.02 — spans include lead-in/instrumental by construction.
- **H4 animation-window behavior**: SUPPORTED. `_compute_animation_progress`
  derives enter/exit from the LINE span. Because line spans are contiguous and
  include silences, the exit fade begins 0.09–1.38 s BEFORE the last word ends
  on nearly every line (words fade out while still being sung), and entrance
  windows expire during instrumental lead-ins (e.g. L1: at its first word's
  appearance the line is already 89 % through its span, so no entrance runs and
  exit starts 1.38 s later while "goes" is still being sung).
- **H5 interstitial gaps**: 38 gap periods totaling **51.6 s (~40 % of the
  song)** render with NO lyrics (interstitial frames) — including 13.3 s,
  8.2 s, 6.1 s, 5.8 s holes — because `_find_active_word` returns −1 whenever
  t is outside every word span. Lyrics vanish between phrases.
- **H6 rendering-path-specific**: the frame-reuse optimization is dead code
  (`_frame_is_unique` unconditionally returns True → every frame re-rendered).
  No timing impact; performance only.

## Working theory

Word on/off times are frame-accurate to the sync data. The perceptual
complaints, if any, most likely come from (a) lyrics vanishing during
between-phrase gaps, and (b) line-span-driven exit fades clipping sung words —
both caused by treating the contiguous LINE span as the display/animation
window instead of the word span.

## Changes made

- **Bug #1 (confirmed, fixed, verified)**: interval/excerpt renders muxed the
  FULL audio track. `preview_13.5-17.5.mp4` v1 had video=4.03 s but
  audio=132.58 s (container 2 m12 s: 4 s of video, then frozen frame over the
  whole song). Root cause: `VideoEncoder` passed the complete `audio_path` to
  ffmpeg with no trim. Fix: `VideoEncoder` gained `audio_start`/`audio_duration`
  (input-seeking options placed before the audio input) plus `-shortest` for
  excerpt renders; `renderer.render()` now passes `time_start`/`time_end`
  through. Full renders (no explicit start/end) are byte-identical in behavior.
  Regression tests added (excerpt trims audio + `-shortest`; full render does
  not). 236/237 render tests pass (remaining failure `test_caches_bg`
  pre-exists all session work).
- Session note: my grayscale brightness heuristic for "text present" was
  inverted (gap interstitials are BRIGHT); frames were verified by direct
  visual inspection instead.

## Renders for review

- **Render 1 (v2, verified by me before handoff): CPU excerpt 13.5–17.5 s**,
  960×540 @30fps, 4.00 s/4.00 s A/V, 1.5 MB. Frame-checked at four timestamps:
  - 14.0 s → interstitial gap, no lyrics (correct; words start 14.432)
  - 14.7 s → "Here goes" on screen, active-word highlight ("goes" brighter)
  - 15.5 s → "Here goes" still on screen, mid exit-fade (consistent with H4)
  - 17.1 s → "What'll" alone (progressive reveal; word active 16.853–17.140)
  Path: `projects/prophetic-preprint/projects/here-goes/output/preview_13.5-17.5.mp4`

## Human feedback

- User (v1 render): length wrong and not the actual preview excerpt → led
  directly to Bug #1. Fix committed (1286928).
- User (v2 render): **"we're in alignment regarding the preview"** — the
  13.5–17.5 s excerpt (L1 words after the 13.3 s instrumental, exit fade,
  0.83 s gap, L2 entrance) renders correctly at the expected moments. H3
  (data corruption) disproven for this window; H4/H5 behaviors present but
  not objectionable here. Next: stress window with the most extreme
  line-span/word-span mismatches (L36/L37 + the 8.2 s hole).

## Render 2 — stress window 105.5–123.0 s (verified, awaiting review)

Frame-checked at five points, all consistent with the sync data:
- 107.5 s → "Heh-heh-…" full line visible (word span 107.349–108.23) ✓
- 109.0 s → **interstitial**: lyrics cut ABRUPTLY the instant the last word
  ended (108.23) even though the line nominally runs to 110.71 (2.48 s tail)
- 110.0 s → same interstitial, continuing through the 8.2 s hole (to 116.41)
- 117.0 s → "Here" alone — correct progressive reveal ("goes" starts 117.707)
- (118.5 s frame also extracted: L37 tail)

**Refinement to H4/H5 understanding:** the line does not fade through its
tail — `_find_active_word` returns −1 the moment the last word ends, so the
text is cut hard to interstitial. The only "fade" ever visible is during the
FINAL word itself (exit window overlapping the word span). So the perceptual
model is: text visible [first-word-start → last-word-end], hard cut, then
interstitial until the next line's first word — with the exit fade eating
into that final word.

## Human feedback

- User (v2 render): **"we're in alignment regarding the preview"** — timing in
  that window is correct. Pivots the investigation to **data-vs-audio audit**:
  "the issue is the audio and the lyrics are not synced" — diagnostics must now
  show the AUDIO evidence per lyric (waveform region around each word's
  claimed timestamp).
- Built `scripts/word_timing_diagnostic.py`: renders per-line waveform images
  (claimed word boundaries + vocal onsets + line span + time axis + Δonset
  annotations) → `<project>/output/timing-diag/line-NNN.png` + index.html.

## Data-vs-audio audit (pass 1)

- **L1 "Here goes" (14.43–16.02)**: transcription confirms vocals exactly
  there (14.20–15.52 "Here goes") plus 0.0–0.8 for L0. Onsets at 6.87–12.34
  are instrumental (drums) — no vocals 1–14 s. L1 sync CORRECT; the 13.3 s
  blank screen is a genuine instrumental intro.
- **L2 "What'll happen I don't know" (16.85–18.76)**: every word boundary
  lands on an energy transient with Δonset 0.00 s. Sync CORRECT.
- Remaining: lines 3–38 unaudited — user to scan `timing-diag/index.html`
  and flag lines where cyan boundaries miss the audible vocal.

## Human feedback

- (pending on waveform audit)

## Unresolved

- Which failure mode the user actually perceives as "bad timing" (H4 fade, H5
  gaps, or data-level word timing).
- fps of prior production renders (assumed 30).
