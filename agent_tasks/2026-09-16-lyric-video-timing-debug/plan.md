# Agent Task — Lyric-Video Timing Debug Audit and Remediation

Task ID: `2026-09-16-lyric-video-timing-debug`
Repository: `asabaal/content-tools`
Primary subsystem: `music-video-pipeline`
Requested by: Asabaal
Planner / handoff author: ChatGPT
Date: 2026-09-16
Base branch: `develop`
Observed handoff-time base SHA: `6e4dfc7db4df1c60756a64a7b3730dfc5980b177`

## Objective

Use the newly available high-capability coding model / reasoning budget and available compute to perform a fresh, evidence-driven debugging pass on the lyric-video timing system.

The goal is not merely to make one song look better. Determine what timing defects remain in the current system, identify their actual layer(s), fix generalizable root causes where justified, and demonstrate improvement across a representative Prophetic Preprint corpus without regressing already-correct behavior.

This is explicitly authorized as a deep debugging task. Favor careful measurement, instrumentation, reproducibility, and cross-song evidence over speed.

## Required inter-agent alignment protocol

This task uses the repository inter-agent protocol. Before any consequential code or data edits:

1. Independently inspect the repository and this plan. Do not assume the planner's diagnosis is correct.
2. Create `agent_tasks/2026-09-16-lyric-video-timing-debug/executor-review.md`.
3. The executor review must record:
   - your understanding of the objective and boundaries;
   - the current implementation paths you inspected;
   - what you believe the active timing pipeline actually is;
   - assumptions and uncertainties;
   - risks and likely failure modes;
   - proposed diagnostic / execution plan;
   - planned tests and evidence artifacts;
   - execution environment: executor identity, model, provider/host if applicable, mode/reasoning profile, permissions, branch/worktree, and actual starting commit SHA.
4. End the executor review with exactly one standalone status line:

   `ALIGNED`

   or

   `REALIGNMENT_REQUIRED`

5. Do not make consequential implementation changes before the executor review concludes `ALIGNED`.
6. If the review concludes `REALIGNMENT_REQUIRED`, stop after documenting the concrete mismatch/questions. Do not silently reinterpret the task.
7. If a material assumption becomes false during execution, return the task to `REALIGNMENT_REQUIRED`, document why, and stop before expanding/reinterpreting scope.

After successful execution, create `agent_tasks/2026-09-16-lyric-video-timing-debug/execution-report.md` with the evidence and results described below.

## Current repository state to inspect first

Start from latest `develop`; do not assume the handoff-time SHA is still current. Record the actual base SHA in the executor review.

Read these before proposing changes:

- `music-video-pipeline/docs/TIMING_DEBUG_PROTOCOL.md`
- `music-video-pipeline/docs/timing-debug-2026-08-27-here-goes.md`
- `music-video-pipeline/scripts/TIMING_REALIGNMENT_ANALYSIS.md`
- `music-video-pipeline/scripts/timing_dashboard.py`
- `music-video-pipeline/scripts/word_timing_diagnostic.py`
- `music-video-pipeline/src/lyrics/alignment_analyzer.py`
- `music-video-pipeline/src/lyrics/onset_refiner.py`
- `music-video-pipeline/src/lyrics/synchronizer.py`
- `music-video-pipeline/src/render/renderer.py`
- `music-video-pipeline/src/render/encoder.py`
- `music-video-pipeline/src/transform/timing.py`
- timing/alignment/render tests under `music-video-pipeline/tests/`, especially `test_alignment_analyzer.py`, `test_onset_refiner.py`, `test_synchronizer.py`, `test_render.py`, and `test_transform_timing.py`.

Also inspect relevant commit history before deciding that an apparent oddity is a bug. Recover intent where possible instead of reasoning only from the present snapshot.

## Important prior findings — evidence, not assumptions

The 2026-08-27 `Here Goes` session found, for that song/window:

- renderer visibility latency tracked intended word starts within normal 30 fps quantization (0–33 ms) with no accumulating frame-loop drift;
- no obvious A/V start-offset mechanism was found in the full-render path;
- an excerpt-render muxing bug was found and fixed (`audio_start` / `audio_duration` plus `-shortest` for excerpts);
- line-span-driven animation windows and word-span-driven visibility were identified as distinct semantics;
- substantial interstitial gaps were real consequences of no active lyric word, not necessarily timing errors;
- human review of selected `Here Goes` preview windows agreed that renderer timing matched the stored sync data;
- the investigation therefore pivoted from renderer-vs-data toward **stored timing data vs actual sung audio**;
- `word_timing_diagnostic.py` was created to visualize claimed word boundaries against waveform / vocal-onset evidence;
- later realignment work documented cases where synchronizer output can compress or corrupt word windows and where stem timing can provide stronger timing evidence even when recognized text is imperfect.

Treat all of those as hypotheses/findings to re-check against the current code where relevant. Do not over-generalize one song's results to the corpus.

## Scope

### 1. Establish a reproducible baseline before fixes

Run the existing test suite relevant to timing and rendering and record failures before changing code.

Build a baseline timing audit over a representative set of Prophetic Preprint projects. At minimum, include `Here Goes` plus multiple other songs with structurally different timing demands. Known starting candidates include `AI Psalm 9` and `Blessed the Name`; discover the currently available project corpus under the local Prophetic Preprint project tree and choose additional cases based on evidence, not convenience.

Prefer a corpus that exercises:

- dense / fast lyric passages;
- sustained words and long phrases;
- repeated choruses;
- large instrumental gaps;
- short gaps between lines;
- intro/outro boundaries;
- long songs where drift would become visible;
- songs with existing timing overrides;
- songs with stem/vocal transcription evidence;
- known suspicious or historically hand-corrected timing.

Document exactly which songs/windows were used and why.

### 2. Classify timing error by layer

Do not use “timing issue” as one undifferentiated category. Test and distinguish at least:

- source lyric / transcription timing error;
- synchronizer line-span error;
- synchronizer word-span error;
- onset-refiner error;
- stem-selection / transcription-coverage failure;
- bad or stale `timing_overrides`;
- zero/negative/implausibly short word durations;
- overlaps, gaps, or broken end timestamps;
- line-span vs word-span semantic mismatch;
- renderer active-word selection behavior;
- enter/exit animation windows masking otherwise-correct word timing;
- frame-rate quantization / frame-time calculation;
- accumulating drift;
- A/V input start offset or mux/seek offset;
- audio resampling/timebase issues if present;
- excerpt/preview path vs full-production-render differences;
- editor/preview semantics vs renderer semantics;
- any other rendering-path-specific behavior discovered from evidence.

Where possible, instrument the system so each observed failure can be traced from:

`audio evidence -> source/alignment timestamp -> transformed/overridden timestamp -> renderer event time -> first/last visible frame -> encoded A/V artifact`

### 3. Make the audit independent of the data being tested

Do not validate `lyrics_synced.json` merely by confirming that the renderer follows `lyrics_synced.json`.

For data-vs-audio claims, use independent audio evidence available in the project: waveform, vocal onsets, vocal/stem transcription segments/words, and direct short rendered excerpts where useful. Where transcription text is garbled but timestamps clearly follow vocal energy, treat text identity and timing evidence separately.

Quantify uncertainty. If independent evidence is insufficient for a line, mark it uncertain rather than manufacturing precision.

### 4. Extend the audit tooling rather than hand-auditing everything

Reuse and extend the existing timing dashboard and word timing diagnostic where sensible. Prefer a repeatable corpus audit that can surface suspicious lines automatically.

Useful machine-detectable signals may include:

- word duration distribution and extreme outliers;
- zero/negative duration words;
- overlap/gap anomalies;
- line duration vs occupied word-span ratio;
- line start/end far from first/last word;
- claimed word boundary distance from nearby vocal onset/transcription boundary;
- suspicious compression/expansion relative to neighboring words and phrase duration;
- cumulative error as song time increases;
- renderer first-visible / last-visible frame error relative to its intended event time;
- override prevalence and whether overrides still correspond to current source data.

If a new audit output is added, make it both human-readable and machine-readable where practical. Keep it deterministic enough to be regression-tested.

### 5. Fix root causes, not examples

For each candidate fix:

`hypothesis -> measurement -> minimal change -> tests -> same-window re-measurement -> broader corpus check`

Prefer pipeline-level correction when multiple songs demonstrate the same failure mechanism.

Do **not** introduce a global “magic” timing offset, per-song fudge factor, or mass override merely because it makes sampled output look better. Such a correction is acceptable only if evidence proves the offset belongs to that exact timing layer and its semantics are documented/tested.

Do not overwrite a stronger source of timing truth with a weaker heuristic.

Per-song `timing_overrides` remain valid for genuinely local/ambiguous cases, but they must not hide a general synchronizer/refiner/renderer defect.

### 6. Preserve unrelated behavior

Timing work must not become a renderer redesign.

Preserve visual design, typography, layout, animation intent, background systems, and unrelated audio behavior unless evidence shows a specific timing interaction that requires a change. Keep changes tightly scoped and explain any unavoidable cross-cutting edit.

Do not rewrite or delete original song/project timing data destructively just to create a passing demonstration. Preserve recoverability and source provenance.

## Diagnostic render / compute policy

Use the existing timing-debug protocol unless the current repository has explicitly superseded it.

- High reasoning / compute usage is authorized for analysis, tests, corpus audits, and repeated diagnostics.
- Prefer short CPU diagnostic renders at reduced resolution for iterative timing work.
- Treat GPU as unavailable unless explicitly coordinated with the operator. Do not claim/use it unilaterally.
- When a human perceptual judgment would provide materially better information than further speculation, produce the smallest useful review artifact and surface it rather than continuing to guess.

## Success tests / acceptance conditions

The task is successful when the executor can provide evidence for all of the following:

1. **Current-state map:** the actual timing path from audio/transcription through synchronization/overrides to rendered/encoded output is documented.
2. **Cross-song baseline:** multiple Prophetic Preprint songs have been audited with reproducible commands/artifacts.
3. **Remaining issues identified:** observed failures are classified by layer and supported by measurements or artifacts.
4. **Root causes addressed:** generalizable defects found during the audit are fixed at the correct layer, with regression tests.
5. **No invented offset:** fixes do not rely on unexplained global/per-song timing fudges.
6. **Renderer correctness checked:** frame quantization, drift, A/V mux/seek behavior, and preview-vs-full-render behavior are explicitly verified rather than assumed.
7. **Data correctness checked:** stored word/line timestamps are compared against independent audio evidence rather than only against renderer behavior.
8. **Regression corpus rerun:** the same baseline corpus/windows are measured again after fixes, with before/after evidence.
9. **Tests:** relevant automated tests pass, and pre-existing failures are distinguished from regressions.
10. **Human-review boundary respected:** any remaining claims requiring perceptual judgment are surfaced with concrete short artifacts and questions rather than guessed at.

Do not invent a millisecond tolerance merely to declare success. Use an existing documented tolerance if the project already defines one. Otherwise report errors in both milliseconds and frame-duration terms and justify any threshold from the renderer/audio semantics and measured corpus behavior.

## Deliverables

### Required coordination artifacts

- `agent_tasks/2026-09-16-lyric-video-timing-debug/executor-review.md`
- `agent_tasks/2026-09-16-lyric-video-timing-debug/execution-report.md`

Use `alignment.md` only if an explicit planner/operator realignment exchange becomes necessary.

### Required technical evidence

The execution report must include:

- executor/model/environment and permissions;
- starting branch + SHA and final branch + SHA/commit(s);
- files changed and why;
- exact audit/test/render commands used;
- baseline test results;
- baseline corpus and measured findings;
- root-cause hypotheses tested, including disproven hypotheses;
- each fix and the evidence linking it to a root cause;
- before/after measurements for the same corpus/windows;
- automated test results after changes;
- paths to generated diagnostic/report artifacts;
- any human-review artifacts that need operator judgment;
- remaining known issues, uncertainties, and cases not fixed;
- whether `TIMING_DEBUG_PROTOCOL.md` should be updated based on what this pass learned.

If the work changes the recommended debugging workflow, update `music-video-pipeline/docs/TIMING_DEBUG_PROTOCOL.md` in the same change and explain the change in the execution report.

## Non-goals

- Do not beautify or refactor unrelated code.
- Do not change visual style merely because a timing artifact looks visually odd.
- Do not declare sync “fixed” because tests pass without rendered/audio evidence.
- Do not declare the renderer broken because source timestamps are wrong.
- Do not declare source timestamps correct merely because renderer output agrees with them.
- Do not optimize rendering performance unless timing evidence shows performance is changing timestamps or frame delivery semantics.
- Do not consume GPU resources without explicit coordination.

## Authority and stop conditions

After an `ALIGNED` executor review, the executor is authorized to diagnose, instrument, test, and implement evidence-backed lyric-timing fixes within this task's scope, including adding regression tests and audit tooling.

Stop and return to `REALIGNMENT_REQUIRED` before:

- broad architecture replacement;
- destructive migration/rewrite of project source data;
- unrelated visual/renderer redesign;
- adopting a new source of truth that conflicts materially with current project provenance;
- uncoordinated GPU use;
- any material scope change needed to continue.

Ordinary uncertainty is not a reason to stop: investigate it and record evidence. Stop only when the uncertainty changes the authorized problem or requires an operator decision.
