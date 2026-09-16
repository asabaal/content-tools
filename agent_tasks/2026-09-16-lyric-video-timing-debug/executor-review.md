# Executor Review — Lyric-Video Timing Debug Audit and Remediation

Task: `2026-09-16-lyric-video-timing-debug`
Executor: Claude Code (ZCode agent, GLM model, Z.ai host)
Mode: plan-mode entry approved → execute; permissions: repo read/write, CPU compute,
no GPU (per task policy).
Branch: `develop`
Starting SHA: `f82c387` (planner handoff commit; planner base `6e4dfc7` was one commit
behind — a docs-only handoff commit, no code delta).

## Objective and boundaries

Empirically determine which timing defects remain between the current state and a
genuinely reliable lyric-video system, across a multi-song Prophetic Preprint corpus;
fix generalizable root causes at the correct layer with regression tests; preserve
visual design and project data; keep Dad-corpus (sermon) work unaffected. Not in
scope: renderer redesign, visual changes, GPU use, destructive data rewrites.

## Implementation paths inspected

- `src/lyrics/parser.py` — lyrics.txt → lines; blank/section handling; word split on
  whitespace.
- `src/lyrics/synchronizer.py` — line/word alignment to onset segments;
  `SyncedLine`/`SyncedWord` emission; `snap_to_nearest_beat`;
  `reconcile_region_boundaries`; `align_words_from_segments` (used by
  `realign_from_stem` transform).
- `src/lyrics/alignment_analyzer.py` — line matching, transcription coverage,
  `_recover_unmatched_lines` (onset-syllable fallback), `_count_syllables`,
  `_snap_word_starts_to_onsets`.
- `src/lyrics/onset_refiner.py` — post-alignment word-window refinement against
  onset energy peaks (TRIM_* machinery, min word duration 0.04s, breath handling).
- `src/transform/timing.py` — `realign_from_stem` → `timing_overrides`; release-group
  logic; stem selection by timestamp proximity.
- `src/render/renderer.py` — `_apply_timing_overrides` (deep-merge over synced
  lines); frame loop `t = frame_idx / fps`; `_find_active_word` (first word with
  `start <= t <= end`, inclusive both ends); `_compute_animation_progress`
  (line-span-driven enter/exit); `_draw_progressive`/`_draw_karaoke`;
  `_render_interstitial` during no-active-word spans.
- `src/render/encoder.py` — raw RGB → libx264 + AAC mux; excerpt
  `audio_start`/`audio_duration` trim + `-shortest` (fixed 2026-08-27).
- Audit tooling: `scripts/timing_dashboard.py` (HTML from audit summary.json),
  `scripts/word_timing_diagnostic.py` (waveform images), `mvp audit` (per-word
  summary.json with issue classification), `scripts/TIMING_REALIGNMENT_ANALYSIS.md`
  (blessed-the-name L3 compression case study).
- Prior session docs: `docs/TIMING_DEBUG_PROTOCOL.md`,
  `docs/timing-debug-2026-08-27-here-goes.md`.

## The active timing pipeline (as I understand it)

1. **Evidence generation**: Whisper transcription of combined/lead vocal stems →
   `vocal_transcription_*.json` (segments + words + probabilities); librosa onset
   detection → `vocal_onsets.json`.
2. **Alignment**: `synchronizer.py` matches parsed lyric lines to transcription
   segments (text + time overlap scoring), assigns word timings from transcription
   words or onset-syllable fallback; `alignment_analyzer.py` scores matches and
   recovers unmatched lines; `onset_refiner.py` trims/expands word windows against
   onset energy. Output: `lyrics_synced.json` (contiguous line spans; word spans
   inside; per-line confidence + warnings; word `source` field).
3. **Overrides (optional)**: `realign_from_stem` transform or hand edits write
   `script.json:timing_overrides` keyed by synced line index; renderer deep-merges
   over synced lines at load.
4. **Render**: per frame `t = frame_idx / fps`; `_find_active_word` returns the
   first word with `start <= t <= end` (inclusive; scan order = document order);
   `render_frame` draws progressive/karaoke reveal for the active line; spans with
   no active word render interstitial visuals; frames + full audio → ffmpeg
   (excerpts trim audio to the rendered interval).

## Prior findings re-checked against current code

- Renderer visibility latency 0–33 ms vs intended starts (Here Goes): consistent
  with current code (`t = frame_idx/fps`, inclusive `_find_active_word`). Will
  re-verify on a second song.
- Excerpt mux bug: fixed in current code (`audio_start`/`audio_duration`,
  `-shortest` for excerpts only). Full renders untrimmed by design (full audio IS
  the full interval).
- blessed-the-name L3 compression (0.167 s words): stem-coverage gap caused the
  synchronizer to compress; documented fix path is stem-based `timing_overrides`.
  blessed-the-name now carries 132 overrides (from the prior realignment work) —
  their consistency with current synced data needs checking (stale-override risk).
- Line spans include lead-in/interstitial by construction; animation windows are
  line-span-driven. This is semantic, not a defect per se, but it interacts with
  word visibility windows.

## Independent-evidence availability (corpus census, verified)

All **42 songs** with `lyrics_synced.json` also have `vocal_onsets.json`,
`vocal_transcription_combined_vocals.json`, and WAV audio — full independent
evidence coverage for data-vs-audio auditing. 27 also have lead-vocal stems.
Only `blessed-the-name` (132) and `asabaal` (5) carry `timing_overrides`.

## Assumptions and uncertainties

- The `mvp audit` issue classifications (duration >1.5 s / <0.04 s, gaps,
  clipping) are reasonable anomaly signals; I will validate them against actual
  data before trusting thresholds.
- `word.source` values (`whisper_plus_vocal_onset`, `transcription`,
  `interpolated`) indicate provenance quality tiers; corpus audit should segment
  signals by source class.
- `onset_refiner` TRIM_* constants (floor ×3, tail 0.10 s, cap 1.2 s) are tuned
  values whose corpus-wide behavior is unmeasured; the audit should measure the
  post-refinement duration distribution rather than assume.
- Vocal onsets in `vocal_onsets.json` include instrumental onsets (drums) — they
  are evidence of *energy*, not vocals; distance-to-onset is a soft signal.
- 30 fps is the production fps (renderer default and CLI default).

## Risks and likely failure modes (to test, not assume)

1. Synchronizer compression into narrow windows when stem coverage gaps exist
   (documented for blessed-the-name) — likely corpus-wide in songs with similar
   coverage gaps.
2. Line spans covering interstitials → long no-lyric stretches *between* lines
   where line spans are contiguous but words are absent.
3. Stale `timing_overrides` vs current synced data (blessed-the-name 132
   overrides predate possible re-syncs).
4. Zero/near-zero duration or inverted spans from refiner edge cases.
5. Onset-distance outliers: claimed boundaries far from any vocal energy.
6. Renderer boundary semantics (`<=` on both ends) — one-frame attribution at
   word boundaries; expected within quantization but must be measured, not assumed.
7. Excerpt/full render divergence (fixed but must be regression-checked across
   songs).

## Proposed diagnostic / execution plan

1. **Baseline tests**: run timing-relevant suites; record failures (expect only
   pre-existing `test_caches_bg`).
2. **Corpus audit tool** (`scripts/timing_corpus_audit.py`): for all 42 songs,
   compute layer-classified signals from stored data + independent evidence
   (onsets, stem words): zero/negative durations, extreme durations, line/word
   span ratios, lead/tail, onset-distance distribution (by word source class),
   overlap/gap anomalies, cumulative drift, override-vs-synced divergence.
   Output: machine JSON + human MD, deterministic.
3. **Classify + prioritize** failures by layer and prevalence.
4. **Root-cause fixes** at the correct layer, each with
   hypothesis → measurement → minimal change → regression test → re-measure.
   No global offsets; no per-song fudges.
5. **Renderer verification**: frame quantization and A/V duration checks on
   short CPU renders of 2–3 songs (existing excerpt-trim fix regression-checked).
6. **Re-measure corpus** after fixes; produce before/after.
7. **Human-review artifacts**: waveform images / short clips only where judgment
   is the next best evidence.

## Planned tests and evidence artifacts

- `tests/test_timing_corpus_audit.py` — audit invariants on fixture data.
- Regression tests for each fix.
- `output/timing-audit/*.json|md` per song + corpus rollup (deterministic).
- Excerpt renders + waveform images for human review windows.

## Execution environment

- Executor: Claude Code agent (GLM model via Z.ai host), ZCode CLI.
- Permissions: repo read/write, shell, no GPU.
- Branch: `develop` @ `f82c387` (planner base `6e4dfc7` + docs handoff commit).
- Worktree: `/mnt/storage/repos/content-tools` (clean aside from agent_tasks and
  unrelated untracked tooling dirs).

ALIGNED
