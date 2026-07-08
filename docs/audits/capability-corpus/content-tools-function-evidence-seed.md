# Content Tools — Function Evidence Seed

> **Canonical corpus artifact**: `content-tools-function-evidence-seed.json`
> This Markdown report is a human-readable summary. All structured data (function records, test mappings, call graphs, coverage, git history) lives in the JSON file.

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Repository | content-tools |
| Strategy | `develop_vs_main_changed_functions` |
| Round 1 file | `music-video-pipeline/src/pipeline/models.py` |
| Functions cataloged | 31 |
| Test methods mapped | 41 (from `tests/test_models.py`) |
| Call graph edges | 25 (internal) |
| Missing test gaps | 7 |
| High risk items | 5 |
| Line coverage | 100% (227 stmts, 0 miss) |
| Git commits | 2 (`11121e2`, `61d382f`) |
| JSON size | 129 KB |
| Source code embedded | 31/31 functions (8.5 KB) |
| Documentation quality | 0 comprehensive · 0 minimal · 31 missing (31/31 have type annotations) |

---

## Key Findings

### Strengths
- **100% line coverage** on all 227 statements in `pipeline/models.py`
- **Dedicated test file** (`test_models.py`, 376 lines) with 7 test classes covering most dataclass methods
- **Full round-trip testing** for `MusicVideoProject.save()/load()` — audio_info, lyrics_info, stages, input_tier all round-trip correctly
- **Edge case coverage** for `ProjectPaths.resolve_audio/lyrics` — missing files, None paths
- **All 9 path properties** explicitly verified in a single test

### Gaps
- **`AudioInfo` and `LyricsInfo`** have no dedicated test class; only tested indirectly via `MusicVideoProject` round-trip
- **`StageStatus.mark_complete`** unknown-stage test uses a trivially-true assertion (`assert not hasattr(s, "nonexistent") or True`)
- **`MusicVideoProject._now`** — timestamp format and timezone never validated (only not-None check)
- **`MusicVideoProject.save`** — no independent JSON content validation; only tested via load round-trip
- **Branch coverage not measured** — `.coverage` only provides line-level data

### High Risks
1. **Non-atomic save** — `MusicVideoProject.save` writes directly to `mvp_project.json` without temp-file rename; corruption on crash
2. **Path property cascading crash** — `project_dir` getter raises `ValueError`; all 9 derived properties depend on it
3. **No file format validation** — `MusicVideoProject.create` accepts any file extension; unsupported formats fail later
4. **No schema migration** — `MusicVideoProject.load` has no version check or migration logic
5. **Memory-heavy file copy** — `create()` uses `read_bytes/write_bytes` for audio/lyrics files (no streaming)

### Unknowns
- Cross-file callers of `ProjectPaths.resolve_audio/lyrics` not traced
- Branch coverage data unavailable
- Git attribution is file-level, not per-function (all functions in same commit line ranges)
- Call graph limited to file-local analysis
- Assertion quality ratings are agent-inferred

---

## Processing Status

### Round 1: `pipeline/models.py` `[done]`

31 functions/methods cataloged in JSON. See `content-tools-function-evidence-seed.json` for full records.

### Rounds 2-11 `[planned]`

| Round | File | Est. functions |
|-------|------|----------------|
| 2 | `music-video-pipeline/src/audio/features.py` | 10 |
| 3 | `music-video-pipeline/src/audio/analyzer.py` | 16 |
| 4 | `music-video-pipeline/src/lyrics/parser.py` | 20 |
| 5 | `music-video-pipeline/src/lyrics/alignment_analyzer.py` | 17 |
| 6 | `music-video-pipeline/src/lyrics/synchronizer.py` | 33 |
| 7 | `music-video-pipeline/src/canvas/models.py` | 9 |
| 8 | `music-video-pipeline/src/canvas/renderer.py` | 12 |
| 9 | `music-video-pipeline/src/render/renderer.py` | 44 |
| 10 | `music-video-pipeline/src/transform/aspects.py` | 17 |
| 11 | `music-video-pipeline/src/transform/core.py` | 34 |

---

## Full Function Inventory Queue

All 69 changed `.py` files with function-level status.

### `music-video-pipeline/src/` (48 files)

| # | File | Status |
|---|------|--------|
| 1 | `pipeline/models.py` | `[done]` |
| 2 | `audio/features.py` | `[planned]` |
| 3 | `audio/analyzer.py` | `[planned]` |
| 4 | `audio/ingest.py` | `[pending]` |
| 5 | `audio/midi.py` | `[pending]` |
| 6 | `lyrics/parser.py` | `[planned]` |
| 7 | `lyrics/alignment_analyzer.py` | `[planned]` |
| 8 | `lyrics/synchronizer.py` | `[planned]` |
| 9 | `lyrics/onset_refiner.py` | `[pending]` |
| 10 | `canvas/models.py` | `[planned]` |
| 11 | `canvas/renderer.py` | `[planned]` |
| 12 | `canvas/geometry.py` | `[pending]` |
| 13 | `canvas/compositing.py` | `[pending]` |
| 14 | `canvas/lights.py` | `[pending]` |
| 15 | `canvas/loader.py` | `[pending]` |
| 16 | `canvas/motion.py` | `[pending]` |
| 17 | `canvas/recipes.py` | `[pending]` |
| 18 | `canvas/repetition.py` | `[pending]` |
| 19 | `canvas/text_safety.py` | `[pending]` |
| 20 | `cli/commands.py` | `[pending]` |
| 21 | `render/renderer.py` | `[planned]` |
| 22 | `render/animations.py` | `[pending]` |
| 23 | `render/audio_reactive.py` | `[pending]` |
| 24 | `render/background_video.py` | `[pending]` |
| 25 | `render/effect_presets.py` | `[pending]` |
| 26 | `render/encoder.py` | `[pending]` |
| 27 | `render/font_styles.py` | `[pending]` |
| 28 | `render/frame_effects.py` | `[pending]` |
| 29 | `render/gradients.py` | `[pending]` |
| 30 | `render/readability.py` | `[pending]` |
| 31 | `render/text_styles.py` | `[pending]` |
| 32 | `scriptgen/color_presets.py` | `[pending]` |
| 33 | `scriptgen/generator.py` | `[pending]` |
| 34 | `scriptgen/moods.py` | `[pending]` |
| 35 | `scriptgen/palette.py` | `[pending]` |
| 36 | `scriptgen/rules.py` | `[pending]` |
| 37 | `transform/aspects.py` | `[planned]` |
| 38 | `transform/core.py` | `[planned]` |
| 39 | `transform/backgrounds.py` | `[pending]` |
| 40 | `transform/branding.py` | `[pending]` |
| 41 | `transform/colors.py` | `[pending]` |
| 42 | `transform/geometric.py` | `[pending]` |
| 43 | `transform/layouts.py` | `[pending]` |
| 44 | `transform/recipes.py` | `[pending]` |
| 45 | `transform/selectors.py` | `[pending]` |
| 46 | `transform/timing.py` | `[pending]` |
| 47 | `transform/typography.py` | `[pending]` |
| 48 | `assistant/flash_music_video_benchmark.py` | `[pending]` |
| 49 | `assistant/flash_music_video_validation.py` | `[pending]` |

### `music-video-pipeline/` (root)

| # | File | Status |
|---|------|--------|
| 50 | `serve.py` | `[pending]` |

### `ambient-content-pipeline/src/` (7 files)

| # | File | Status |
|---|------|--------|
| 51 | `cli/commands.py` | `[pending]` |
| 52 | `config/defaults.py` | `[pending]` |
| 53 | `pipeline/orchestrator.py` | `[pending]` |
| 54 | `renderer/animation.py` | `[pending]` |
| 55 | `renderer/html_renderer.py` | `[pending]` |
| 56 | `renderer/image_gen.py` | `[pending]` |
| 57 | `renderer/template_builder.py` | `[pending]` |

### `ambient-content-pipeline/scripts/`

| # | File | Status |
|---|------|--------|
| 58 | `run_sd3_pipe.py` | `[pending]` |

### `avatar/scripts/`

| # | File | Status |
|---|------|--------|
| 59 | `inspect_3d_asset.py` | `[pending]` |
| 60 | `render_asset_preview.py` | `[pending]` |

---

## Commands Run

### Schema additions (Round 1.1)

The function atom schema was extended with two new fields per function record:

- **`source_code`**: The actual source text of the function, extracted from the repository using `start_line`/`end_line`. Present for all 31 functions (8.5 KB total).
- **`documentation`**: Structured metadata about internal code documentation:
  - `quality`: `comprehensive` | `minimal` | `missing`
  - `has_docstring`, `docstring_lines`, `has_type_annotations`, `comment_density`, `notes`
  - Result: 0 comprehensive, 0 minimal, 31 missing — no functions in this file have docstrings, though all 31 have type annotations.

These fields are now part of the canonical `av_capability_corpus.function_evidence.v0.1` schema.

```bash
git diff --name-status main...develop -- '*.py'
python3 -m coverage report --include='src/pipeline/models.py'
git log --oneline --follow music-video-pipeline/src/pipeline/models.py
git blame --line-porcelain music-video-pipeline/src/pipeline/models.py
git log -L 1,380:music-video-pipeline/src/pipeline/models.py --oneline
jq empty content-tools-function-evidence-seed.json
```

---

*Generated: 2026-07-08T21:00:00-05:00*
*Canonical data: `content-tools-function-evidence-seed.json`*
