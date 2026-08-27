# Lyric-Video Word-Timing Debugging Protocol

A reusable mode for investigating and improving word-level lyric timing through
an iterative engineering + human-review loop. First used 2026-08-27 with
**"Here Goes" (Prophetic Preprint)** as the reference song.

## Goal

Materially improve whether lyric words appear on screen at the correct moments
relative to the song audio — verified by rendered evidence reviewed by a human,
not by passing tests alone.

## Loop

```
inspect → hypothesis → test/measure → CPU diagnostic render → human review
        → incorporate feedback → repeat
```

Stop making speculative changes once human perceptual review would give
materially better information; surface the artifact instead.

## GPU policy

Another workload (Ava) may be using the GPU. During debugging sessions:

- Treat the GPU as **unavailable** unless explicitly coordinated.
- Diagnostic renders are **CPU-only** (PIL rendering + libx264 software encode),
  reduced resolution (e.g. 960×540), short excerpts (`--start/--end`), default fps.
- If a test genuinely requires GPU, state what/why, then ask the operator to
  coordinate availability. Never take the GPU unilaterally.

The full renderer path (frame loop, `_find_active_word`, animation state,
encoder) runs identically on CPU; only speed differs. Diagnostic renders of
5–20 s excerpts take well under a minute on CPU.

## Diagnostic tooling

- **Static timing table** (no render): compute, from `lyrics_synced.json` and
  the renderer's actual semantics, per word: intended start → first visible
  frame → visibility latency → visible-until; plus line animation-window
  analysis (enter/exit vs word span) and interstitial-gap census. This
  separates *data/timestamp* problems from *render-window animation* problems
  quantitatively.
- **Diagnostic renders**: short CPU excerpts around suspicious boundaries, plus
  (when useful) an instrumented variant that burns
  `word | intended | frame | rendered_t | error` onto frames.

## Failure modes to distinguish

constant offset · accumulating drift · frame quantization · A/V start mismatch ·
animation-window behavior (enter/exit computed from line span) · line-span vs
word-span mismatch in sync data · interstitial gaps (lyrics absent) ·
localized timestamp corruption · rendering-path-specific behavior.

## Recording findings

Each session keeps a log (this file's companion: `timing-debug-<date>-<song>.md`)
with: hypotheses tested, measurements, changes made, renders produced, human
feedback, and unresolved questions. Update the protocol itself if the workflow
improves.

## Reproducing a session

1. Pick the reference song; read its `data/lyrics_synced.json`, `script.json`,
   `analysis.json`.
2. Build the static timing table for the song.
3. Choose the most suspicious windows; render short CPU excerpts.
4. Human review → classify failure mode → targeted fix or data correction.
5. Re-render the same excerpt to confirm; only then widen scope.
