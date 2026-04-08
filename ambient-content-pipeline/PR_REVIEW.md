# PR #7 Review Plan: Ambient Content Pipeline + Video Production Tools + Cleanup

**PR:** ambient content pipeline, video production tools, and repo cleanup #7
**Branch:** develop → main
**Stats:** 97 files changed, +12,006 / -5,146 (updated after tests push)
**Reviewer:** automated

---

## PR Overview

This PR does four things:
1. **Rename** `text-content-pipeline/` → `ambient-content-pipeline/` (tcp → acp)
2. **Major expansion** of the pipeline — 6 entirely new modules (animation, tts, video_encoder, music_gen, audio_mix, run_ace_step_pipe)
3. **Doubling+** of existing modules — cli/commands (530→1221), orchestrator (312→630), html_renderer (166→483), template_builder (159→368), defaults (83→187)
4. **Legacy cleanup** — deletes old `text-content-pipeline/` from develop
5. **Test suite** — 22 test files with 342+ tests (previously gitignored, now included)

Note: `core/`, `tools/`, `serve.py` do NOT appear in this PR diff — they were either already on develop or are in a separate PR.

---

## Review Queue

### TIER 1 — High-Impact New/Expanded Source Code (11 files)

These files contain real new logic and need full diff-based review:

| # | File | Change | Notes |
|---|------|--------|-------|
| 1 | `src/cli/commands.py` | +1221 (was 530) | More than doubled — new commands, refinement workflow |
| 2 | `src/pipeline/orchestrator.py` | +630 (was 312) | Doubled — new rendering/audio/animation orchestration |
| 3 | `src/renderer/html_renderer.py` | +483 (was 166) | Tripled — animation, video, gradient/texture support |
| 4 | `src/renderer/template_builder.py` | +368 (was 159) | More than doubled — gradient, texture, animation CSS |
| 5 | `src/renderer/animation.py` | +220 NEW | Entirely new — drift, flow, pulse, distortion, parallax |
| 6 | `src/config/defaults.py` | +187 (was 83) | More than doubled — animation, gradient, texture configs |
| 7 | `src/renderer/tts.py` | +127 NEW | Entirely new — edge-tts wrapper |
| 8 | `src/renderer/video_encoder.py` | +106 NEW | Entirely new — FFmpeg video encoding |
| 9 | `src/renderer/music_gen.py` | +104 NEW | Entirely new — ACE Step music generation |
| 10 | `scripts/run_ace_step_pipe.py` | +86 NEW | Entirely new — ACE step pipeline runner |
| 11 | `src/renderer/audio_mix.py` | +57 NEW | Entirely new — TTS + music mixing |

### TIER 1B — Test Files (22 files, ~3,500 lines of new tests)

| # | File | Change |
|---|------|--------|
| 12 | `tests/test_cli_commands.py` | +116/-2 |
| 13 | `tests/test_html_renderer.py` | +428 |
| 14 | `tests/test_template_builder.py` | +736 |
| 15 | `tests/test_e2e.py` | +409 |
| 16 | `tests/test_animation.py` | +227 |
| 17 | `tests/test_integration.py` | +221 |
| 18 | `tests/test_prompts.py` | +169 |
| 19 | `tests/test_music_gen.py` | +169 |
| 20 | `tests/test_video_encoder.py` | +155 |
| 21 | `tests/generate_bg_tests.py` | +154 |
| 22 | `tests/test_tts.py` | +142 |
| 23 | `tests/test_audio_mix.py` | +110 |
| 24 | `tests/test_config_defaults.py` | +66/-2 |
| 25 | `tests/test_orchestrator.py` | +61 |
| 26 | `tests/test_ai_generator.py` | +1/-1 |
| 27-38 | 12 test files | Pure renames (zero diff) |
| 39 | `tests/test_data_integrity.py` | +218 (repo root) |

### TIER 2 — Minor Modifications (7 files)

| # | File | Change |
|---|------|--------|
| 40 | `src/ai_generator/generator.py` | +1 line |
| 41 | `src/errors/exceptions.py` | +1/-1 |
| 42 | `acp.py` | +1/-1 (TCP→ACP docstring) |
| 43 | `pyproject.toml` | +11/-2 |
| 44 | `README.md` | +13/-13 |
| 45 | `requirements.txt` | +2 |
| 46 | `.gitignore` | +18 |

### TIER 3 — Pure Renames, Zero Diff (30 files)

Moved from `text-content-pipeline/` → `ambient-content-pipeline/` with no content changes:
- All `__init__.py` (8 files)
- `src/payload/schema.py`, `src/payload/validation.py`
- `src/slots/enum.py`, `src/slots/scheduler.py`
- `src/weekly_calendar/resolver.py`
- `src/ai_generator/prompts.py`
- `src/renderer/templates/template.html`
- Payload JSONs (6), examples (2), content-concept.conv, plan files (5), etc.

### TIER 4 — Data/Output Files (13 files)

Generated outputs and plan JSONs. Review for secrets/PII only:
- 8 `output_*.json` (+47 each)
- 2 plan JSONs (+277, +274)
- 2 texts JSONs (+30 each)
- 1 temp_payload.json (+15), 1 2026-02_texts.json (+5)

### TIER 5 — Documentation & Prompts (5 files)

- `DESIGN.md` (+342/-2)
- `IMPLEMENTATION.md` (+276)
- `bg-prompt.txt` (+169)
- `animate-mode-prompt.txt` (+146)
- `animate-mode-prompt2.txt` (+112)

### TIER 6 — Deletions to Verify (19 files)

Old `text-content-pipeline/` being removed:
- 11 test files (-3,614 lines) — replaced by new `ambient-content-pipeline/tests/`
- 5 source files (-1,250 lines) — old versions replaced by expanded new versions
- 1 IMPLEMENTATION.md (-196)
- 1 temp_payload.json (-16)
- 1 tests/__init__.py (empty)

---

## Resolved Issues

1. ~~**Tests not in PR**~~: FIXED — removed `tests/` from `.gitignore`, committed and pushed 22 test files.
2. **Output files committed**: 8 `output_*.json` and plan JSONs contain generated data. Should these be in `.gitignore` instead?
3. **`outputs/202604 (Copy)/`**: Directory name has "Copy" — appears to be a filesystem artifact accidentally committed.

---

## Review Progress

| # | File | Status | Verdict |
|---|------|--------|---------|
| 1 | `src/cli/commands.py` | DONE | NEEDS WORK |
| 2 | `src/pipeline/orchestrator.py` | DONE | NEEDS WORK |
| 3 | `src/renderer/html_renderer.py` | DONE | NEEDS WORK |
| 4 | `src/renderer/template_builder.py` | DONE | NEEDS WORK |
| 5 | `src/renderer/animation.py` | DONE | NEEDS WORK |
| 6 | `src/config/defaults.py` | DONE | NEEDS WORK |
| 7 | `src/renderer/tts.py` | DONE | NEEDS WORK |
| 8 | `src/renderer/video_encoder.py` | DONE | NEEDS WORK |
| 9 | `src/renderer/music_gen.py` | DONE | NEEDS WORK |
| 10 | `scripts/run_ace_step_pipe.py` | DONE | NEEDS WORK |
| 11 | `src/renderer/audio_mix.py` | DONE | NEEDS WORK |
| 12-39 | Test files | PENDING | — |
| 40 | `src/ai_generator/generator.py` | DONE | PASS |
| 41 | `src/errors/exceptions.py` | DONE | PASS |
| 42 | `acp.py` | DONE | PASS |
| 43 | `pyproject.toml` | DONE | PASS |
| 44 | `README.md` | DONE | PASS |
| 45 | `requirements.txt` | DONE | NEEDS WORK |
| 46 | `.gitignore` | DONE | PASS |
| — | Pure renames (30) | DONE | PASS |
| — | Data/output (13) | DONE | NEEDS WORK |
| — | Docs/prompts (5) | PENDING | — |
| — | Deletions (19) | DONE | PASS |

---

## File Reviews

---

FILE: ambient-content-pipeline/src/cli/commands.py

CHANGE SUMMARY: 1221 lines, entirely new from main's perspective. Diff against old text-content-pipeline version shows only branding changes (3 docstring lines: "text content pipeline" → "ambient content pipeline", "tcp" → "acp" in examples). All 1221 lines of logic were already developed pre-rename.

PURPOSE: Click CLI with 9 commands: `init-month`, `validate`, `resolve-calendar`, `run-all`, `list-presets`, `show-preset`, `inspect-plan`, `demo`, `rerender`, `refine-posts`. Orchestrates the entire ACP pipeline end-to-end: payload creation → calendar resolution → AI text generation → HTML/image/video rendering.

ISSUES:
- `run_all()` function (line 292) shadows the CLI group's `run_all()` inner async helper (line 994). The name collision is confusing though Python scoping handles it correctly — the inner `run_all` at line 994 is a closure inside `rerender()`, not the Click command.
- `_refine_post_with_ai()` (line 1019) calls `generator._call_ollama()` — a private method prefixed with underscore. This is fragile coupling; if the generator's internal API changes, this breaks silently.
- `rerender()` command (lines 614-999) is ~385 lines of business logic inside a Click handler. Contains file I/O, async music generation, TTS generation, audio mixing, video rendering — this should be extracted into a service/orchestrator function. Currently untestable without mocking the entire Click context.
- `refine_posts()` command (lines 1047-1217) is ~170 lines with interactive `click.prompt()` loops baked directly into the command. The AI refinement + interactive loop logic should be separated from the CLI layer for testability.
- Line 354: `payload_path = Path("outputs/plans/temp_payload.json")` — hardcoded relative path. If CLI is run from a different working directory, this writes to an unexpected location.
- Lines 792-803: `NamedTemporaryFile(delete=False)` creates temp files that are never explicitly cleaned up. The `rerender_tts_paths` dict accumulates paths but no cleanup code exists. Same pattern at lines 900-911.
- Lines 820-827: Mutates the plan file on disk during re-render to save music config. This is a side effect buried in a nested async function — if the process crashes between the plan update and completing all renders, the plan file is in an inconsistent state.
- Lines 654, 661: `plan_files[0]` and `texts_files[0]` — takes the first match from glob. If multiple plan files exist (which they often do given the `outputs/202604 (Copy)/` directory), the wrong file could be selected silently.
- Line 1019: `_call_ollama` doesn't validate the response. If the AI returns empty or malformed output, it propagates directly as the "refined post."
- Line 333: `if not theme` — treats empty string `""` as falsy and triggers the error, which is correct behavior but confusing since Click already provides a non-None empty string.

RISKS:
- HIGH: `rerender()` is 385 lines of untestable business logic in a Click handler. Any change to rendering config, music generation, or audio mixing requires manual end-to-end testing.
- MEDIUM: Temp file leaks. Multiple `NamedTemporaryFile(delete=False)` calls create files in the images directory that are never cleaned up, even after successful renders.
- MEDIUM: Hardcoded `outputs/plans/temp_payload.json` path means the CLI only works when run from the project root directory.
- LOW: Private API coupling via `generator._call_ollama()`.
- LOW: `inspect_plan` (line 472) uses hardcoded `outputs/plans/` path — same working directory assumption.

ARCHITECTURE NOTES:
- The file mixes CLI presentation, business logic, file I/O, and async orchestration in one file. The pattern of embedding large async functions as closures inside Click commands prevents unit testing of the core logic.
- `run-all` and `rerender` have significant parameter overlap (20+ click options each for gradient, texture, animation, audio). This option sprawl suggests a config-file approach might be more maintainable.
- The `validate` command correctly delegates to `schema.py` + `validation.py` — good separation. `init-month` is also clean. These simpler commands show what the architecture should look like.
- `demo` (line 500) uses `CliRunner` to invoke `run_all` programmatically — this is a reasonable approach for a demo but means the demo is only as reliable as `CliRunner`'s simulation.

VERDICT: NEEDS WORK

Primary concerns: (1) `rerender()` and `refine_posts()` contain too much business logic for Click handlers and need extraction into testable service functions, (2) temp file cleanup needed, (3) hardcoded relative paths. No data-correctness bugs found in the logic itself.

---

FILE: ambient-content-pipeline/src/pipeline/orchestrator.py

CHANGE SUMMARY: 630 lines, identical to pre-rename version. Pure move from `text-content-pipeline/` to `ambient-content-pipeline/`. All logic was already developed before the rename commit.

PURPOSE: Core pipeline orchestrator. Runs 6 stages: calendar resolution → AI subtheme derivation → AI subtitle generation → slot planning → AI text generation → TTS/music/audio rendering. Two public entry points: `run_full_pipeline()` and `validate_and_run()`.

ISSUES:
- Lines 87-91: Mutates `defaults.DEFAULT_AI_MODEL` global state via module-level import. This is not thread-safe and makes the function impure. If `run_full_pipeline` is called concurrently, model settings will interfere.
- Lines 101, 106, 114, 117, 126, etc.: Uses `print()` instead of Python's `logging` module. No log levels, no structured output, cannot be silenced or redirected in production use.
- Lines 213-226: `NamedTemporaryFile(delete=False)` creates temp TTS files that are never cleaned up. Same pattern at lines 326-329 and 343-346. Accumulates `.mp3` files in the images directory.
- Lines 264-271: Mutates the plan file on disk mid-pipeline to save music config. If the pipeline crashes after this write but before all renders complete, the plan file is inconsistent. Should write music config atomically or at the end.
- Line 333: `monthly_music_path or ""` — if `monthly_music_path` is None (no music generated), this passes empty string to `prepare_slot_audio()`, which would likely fail. However, this code path is guarded by the `bg_music and slot.date in tts_paths` condition on line 317, so `monthly_music_path` should always be set. Still, the `or ""` is misleading.
- Line 436: `_save_plan()` parameter `calendar` has no type annotation — just a comment `# ResolvedCalendar`. Same for `schedule` on line 438.
- Lines 579-589: `validate_and_run()` duplicates the first 6 parameters of `run_full_pipeline()` instead of just passing them through `**kwargs`. The gradient/texture params are listed explicitly but animation/audio/music params go through `**kwargs` — inconsistent API surface.
- Lines 172-183: Text generation accumulates `previous_texts` to avoid duplication, but on failure (line 187), an empty string is added to `generated_texts` but NOT to `previous_texts`. This means subsequent slots don't see the failed slot as "previously generated", which could lead to duplicate themes in edge cases.
- Line 191: When `skip_text_generation=True`, all texts are set to `"[PLACEHOLDER]"`. If `skip_rendering=False`, the renderer will attempt to render images with literal "[PLACEHOLDER]" text.

RISKS:
- MEDIUM: Global state mutation for model override (lines 87-91). Not safe for concurrent use.
- MEDIUM: Temp file leaks from TTS generation. No cleanup mechanism.
- LOW: Missing type annotations on key parameters.
- LOW: `print()` instead of `logging` — no control over output verbosity.

ARCHITECTURE NOTES:
- Good separation of stages with clear sequential flow.
- `_save_plan()` and `_save_texts()` are well-structured helper functions.
- The TTS → music → audio mix → render pipeline (stages 4.5-5) is complex but correctly ordered.
- The same `NamedTemporaryFile(delete=False)` pattern appears in both `commands.py` and `orchestrator.py` — should be extracted to a shared utility with cleanup.

VERDICT: NEEDS WORK

Primary concerns: (1) Global state mutation for model override, (2) temp file leaks, (3) `print()` instead of `logging`. Logic is correct and well-structured otherwise.

---

FILE: ambient-content-pipeline/src/renderer/html_renderer.py

CHANGE SUMMARY: 483 lines, entirely new from main's perspective. Pure rename from old text-content-pipeline version with zero content changes. Implements HTML-to-image/video rendering via Playwright, animated video generation using frame-by-frame compositing, and optional audio muxing.

PURPOSE: Core rendering pipeline — converts text content into styled PNG images or animated MP4 videos with gradient backgrounds and animation effects.

ISSUES:
- Lines 144, 311: Browser resource leak — `browser` is not guarded by `try/finally`. If `page.set_content()` or `screenshot()` throws, `browser.close()` is never called and a Chromium process leaks.
- Lines 456-481: Temp file not cleaned up on crash — if the process dies between VideoEncoder writing `.video_only.mp4` and `unlink()`, the temp file is orphaned.
- Lines 471, 480-481: Silent fallback on missing audio — if `audio_path` points to a nonexistent file, it silently produces a video without audio with no error/warning.
- Lines 166-204, 207-245: Duplicated functions — `get_output_path` and `get_video_output_path` are nearly identical (differ only in extension). `sanitize()` is copy-pasted verbatim.
- Lines 84-89, 386-391: Duplicated aspect ratio logic — `1080x1350` hardcoded dimensions repeated in two functions.
- Lines 74-77, 286-289: Duplicated style_preset validation — identical validation block appears twice.
- Lines 409, 413, 415, 452, 469, 479: Uses `print()` instead of `logging` — no log levels, no structured output.
- Lines 265-278: Misleading docstring — says gradient/texture params are "ignored, transparent" but they're all still passed to `build_html()`.
- No parameter validation for `anim_intensity` (0.0-0.5), `anim_speed` (0.1-2.0), `anim_loop` documented ranges.

RISKS:
- MEDIUM: Browser process leak on error — each failed render leaves a Chromium zombie process.
- MEDIUM: Silent audio loss — caller provides `audio_path` pointing to nonexistent file, gets video without audio, no error.
- LOW: No concurrency guard — multiple concurrent renders each launch their own browser.

ARCHITECTURE NOTES:
- Mixes rendering orchestration and path generation in one file. Path utilities should be extracted.
- `_render_text_layer_to_pil` is well-designed. VideoEncoder context manager usage is good practice.
- Same browser lifecycle management issue as temp file cleanup in orchestrator.

VERDICT: NEEDS WORK

---

FILE: ambient-content-pipeline/src/renderer/template_builder.py

CHANGE SUMMARY: 368 lines, entirely new from main's perspective. Pure rename with zero content changes. Builds complete HTML documents for rendering with configurable gradients, texture overlays, and text styling via f-string composition.

PURPOSE: Generates parameterized HTML strings for headless browser rendering of social-media-style content images.

ISSUES:
- Line 342: Duplicate `font-size` property in `.subtheme-pill` — declared twice.
- Lines 28-30: Division by zero — when `num_colors == 1`, line 30 computes `i / (1 - 1)`. Guard on line 210 in caller protects it, but `_build_gradient_css` itself has no guard.
- Line 49: `direction_map[gradient_direction]` raises `KeyError` on unexpected string with no fallback.
- Line 361: **XSS risk** — `text` is interpolated directly into HTML without escaping. Same for `monthly_theme` (259), `display_subtheme` (265), `subtheme_subtitle`, `subtheme`. If sourced from user input or LLM, this is an injection vector.
- Line 200: `gradient_colors[0]` used as reference background for auto-contrast — picks only first gradient color, may produce poor contrast on overall gradient.
- Line 56: Stale docstring — says "Returns: Tuple of (css_string, html_string)" but there are three items described.
- Line 329: Extra double-space in `rgba(255, 255,  255, 0.2)` — minor cosmetic.

RISKS:
- HIGH: XSS via unescaped text/theme/subtheme interpolation — arbitrary HTML/JS injection possible if sourced from user input or LLM.
- MEDIUM: Division by zero in `_build_gradient_css` if called with single color list.
- LOW: No input validation on `gradient_colors` format — malformed hex values produce invalid CSS silently.

ARCHITECTURE NOTES:
- Template built via f-string interpolation — should use `html.escape()` at minimum for dynamic content.
- `_build_texture_css` has significant code duplication across 6 texture branches — could be data-driven.
- 13 parameters suggest config objects should be unpacked rather than passed individually.

VERDICT: NEEDS WORK

---

FILE: ambient-content-pipeline/src/renderer/animation.py

CHANGE SUMMARY: 220 lines, entirely new module. Pure rename with zero content changes from old text-content-pipeline version. Implements procedural animation system generating per-frame PIL images via noise sampling and coordinate transforms.

PURPOSE: Core frame-generation backend for animated video backgrounds, producing a continuous field `G(x, y, t)` where every pixel evolves smoothly over time.

ISSUES:
- Lines 35: `speed` stored with no validation or clamping — zero speed produces static image, negative reverses direction.
- Lines 29-30: `width`/`height` not validated — `width=0` or `height=0` produces empty arrays, negative values produce mangled ranges.
- Lines 63-69: `_hex_to_rgb` has no input validation — malformed hex strings cause opaque `ValueError`.
- Lines 124, 127: `_compute_gradient` with single-color list: `num_colors - 2 = -1`, `np.clip(idx, 0, -1)` returns `-1`. Works accidentally but fragile.
- Line 149: `"reactive"` maps to `_generate_pulse` with no visual differentiation — `AnimType` advertises it as distinct mode.
- Lines 183-186, 199-201: `_noise_grid_e` reused in both dx and dy distortion layers — creates correlated diagonal artifacts.
- Line 60: `_base_gradient` pre-computed (47 MB at 1080p) but only used by `_generate_pulse` — wasted memory for other modes.
- Lines 48: Full-resolution float64 coordinate grids allocated eagerly — ~180 MB at 4K with no lazy allocation.

RISKS:
- MEDIUM: Invalid hex color from config causes unhandled `ValueError` crash at runtime.
- MEDIUM: Single-color gradient list produces degenerate `np.clip` behavior.
- LOW: Memory footprint ~180 MB at 4K — problematic in constrained environments.
- LOW: `"reactive"` is a no-op alias — misleading to users.

ARCHITECTURE NOTES:
- Clean design: single class with dispatch table, bilinear noise sampling, shared gradient interpolator.
- Seeded `random.Random` for reproducibility is correct.
- Ping-pong gradient (triangle wave) guarantees seamless wrapping — good design for looping video.

VERDICT: NEEDS WORK

---

FILE: ambient-content-pipeline/src/config/defaults.py

CHANGE SUMMARY: 187 lines, expanded from 83. Pure rename with zero content changes. Added color utilities, new type aliases (GradientDirection, TextureType, TextureBlendMode, AnimType), ACE-Step config, and animation defaults.

PURPOSE: Centralize all pipeline configuration constants, type-safe literal aliases, and color math helpers.

ISSUES:
- Lines 13-14: Side effects at import time — `mkdir()` runs on every `import` of this module. Silently creates directories, breaks test isolation.
- Line 140: **Hardcoded absolute path** `"/mnt/storage/python_env/ace_step_env/bin/python"` — machine-specific, will break on any other host.
- Lines 159, 177: Silent fallback to white on invalid hex input — `len(hex_color) != 6` returns `"#FFFFFF"` with no warning.
- **Line 182: BUG** — `colorsys.rgb_to_hls` returns `(h, l, s)` but variables are named `h, s, l` — `s` receives luminance and `l` receives saturation. The multiplications on lines 184-185 (`s * 1.1`, `l * 0.9`) operate on the WRONG components.
- Line 7: `PROJECT_ROOT` assumes fixed layout — if file is moved or package installed via pip, points to wrong location.
- Lines 53-84: Presets hardcode all-white text, ignoring the `auto_contrast_color` function defined in same file.
- Line 150: `BACKGROUND_TEST_DIR` is a testing artifact leaking into production config.

RISKS:
- HIGH: Hardcoded path `ACE_STEP_PYTHON` (line 140) ties deployment to single machine.
- HIGH: `companion_color` variable-name swap bug (line 182) — luminance and saturation multiplied incorrectly.
- MEDIUM: Import-time side effects (lines 13-14) break hermetic test runs.
- LOW: `IMAGE_QUALITY = 100` is only meaningful for JPEG — PNG (line 39) ignores it.

ARCHITECTURE NOTES:
- Single monolithic defaults file reaching its limit — ACE-Step and animation blocks suggest domain-specific config submodules.
- `Literal` type aliases provide no runtime validation — invalid values only caught at render time.
- Utility functions (`auto_contrast_color`, `companion_color`) don't belong in a "defaults/constants" module.

VERDICT: NEEDS WORK

---

FILE: ambient-content-pipeline/src/renderer/tts.py

CHANGE SUMMARY: 127 lines, entirely new module. Provides async TTS generation via `edge-tts`, audio duration detection via `ffprobe`, and audio/video muxing via `ffmpeg`.

PURPOSE: Centralize all TTS and audio subprocess operations for the rendering pipeline.

ISSUES:
- Line 5: Unused import `tempfile` — dead code.
- Line 79: Unhandled `ValueError` on `float()` cast — if ffprobe returns non-numeric duration, raises untyped exception instead of `RendererError`.
- Line 78: Silent fallback to `0.0` — when duration key is absent, returns 0.0. Downstream code treats as valid zero-length audio, can produce wrong output.
- Lines 56, 116: No `timeout` on `subprocess.run` — can hang indefinitely if ffmpeg/ffprobe stalls.
- Lines 12-16: No input validation — `generate_tts` doesn't guard against empty text or verify parent directory exists.
- Lines 56-69, 116-120: Inconsistent subprocess error handling — `get_audio_duration` uses `check=True`, `mux_audio_video` manually checks returncode.
- Line 109: `-shortest` flag silently truncates — can drop content without warning.
- No logging at all — runs external processes and network calls with zero observability.

RISKS:
- HIGH: No `timeout` on `subprocess.run` — stalled ffmpeg blocks entire pipeline indefinitely.
- MEDIUM: Silent zero-duration fallback produces incorrect video/audio sync with no error signal.
- MEDIUM: Uncaught `ValueError` breaks module's error contract.

ARCHITECTURE NOTES:
- Lazy `import edge_tts` (line 31) is a good pattern — makes edge-tts optional dependency.
- Clean minimal API surface: `generate_tts`, `get_audio_duration`, `mux_audio_video`.

VERDICT: NEEDS WORK

---

FILE: ambient-content-pipeline/src/renderer/video_encoder.py

CHANGE SUMMARY: 106 lines, entirely new module. Context-manager-based FFmpeg subprocess wrapper streaming raw RGB frames via stdin pipe to produce H.264 MP4.

PURPOSE: Encapsulate the ffmpeg raw-video-pipe pattern so callers can write PIL frames without managing subprocess lifecycle.

ISSUES:
- Line 15: No input validation on `width`, `height`, `fps` — zero/negative values produce broken ffmpeg invocation.
- Lines 60-83: No dimension mismatch guard — `write_frame` silently accepts any size image. Wrong dimensions corrupt video or crash ffmpeg.
- Line 96: `self._process.wait()` has no timeout — if ffmpeg hangs, `close()` blocks indefinitely.
- Lines 79-80, 100-101: **Stderr pipe deadlock** — `self._process.stderr.read()` after `wait()` can deadlock if ffmpeg fills stderr pipe buffer (~64KB). Should use `communicate()` or `stderr=DEVNULL`.
- Lines 85-106: `close()` doesn't `kill()` process on error paths — if exception before `wait()`, process is orphaned.
- Line 33: `-y` + unvalidated `output_path` allows arbitrary file overwrite.
- No `__del__` safety net — forgotten `close()` silently leaks subprocess.

RISKS:
- HIGH: Stderr pipe deadlock — if ffmpeg emits >64KB stderr, `wait()` blocks forever.
- MEDIUM: Process orphan on unexpected exceptions before `wait()`.
- MEDIUM: Silent dimension mismatch — bugs in calling code produce corrupt output.

ARCHITECTURE NOTES:
- Command injection: SAFE — ffmpeg command built as `list[str]`, no shell invocation.
- Context manager pattern is well-chosen for the frame-writing lifecycle.
- Consistent with project conventions (uses `RendererError`).

VERDICT: NEEDS WORK

---

FILE: ambient-content-pipeline/src/renderer/music_gen.py

CHANGE SUMMARY: 104 lines, entirely new module. Auto-generates background music prompts via Ollama and invokes ACE-Step through subprocess to produce WAV files.

PURPOSE: Music generation building block — computing correct music durations from TTS lengths, prompting LLM for music description, shelling out to ACE-Step to render audio.

ISSUES:
- Lines 21-23, 26-28: Duplicate logic — `calculate_music_duration` and `calculate_slot_video_duration` are identical functions.
- Line 82: **`subprocess.run` is synchronous** — blocking call on async event loop with 600s timeout freezes entire event loop.
- Lines 69-76: No input sanitization on `prompt` or `output_path`.
- Line 97: JSON parse assumes stdout is JSON — if ACE-Step emits progress/logging before final JSON, `json.loads` fails.
- Lines 51-52: No retry logic — inconsistent with `generator.py` pattern which has proper retries.
- Line 53: No specific exception handling — `response.raise_for_status()` throws `httpx.HTTPStatusError` as unhandled generic exception, not `RendererError`.
- Line 33: `httpx` imported inside function despite being used elsewhere — should be top-level.

RISKS:
- HIGH: Blocking `subprocess.run` in async context — stalls event loop up to 600s, causes cascading timeouts.
- MEDIUM: No credentials/secrets risk — localhost Ollama and local subprocess, clean.
- MEDIUM: Temp file handling — partial WAV left on disk if subprocess fails mid-write.

ARCHITECTURE NOTES:
- Mixes sync and async code in same file — should be fully async with `asyncio.create_subprocess_exec`.
- Reinvents simpler Ollama interaction instead of reusing `generator.py`'s robust pattern.

VERDICT: NEEDS WORK

---

FILE: ambient-content-pipeline/scripts/run_ace_step_pipe.py

CHANGE SUMMARY: 86 lines, entirely new script. CLI entry-point wrapping ACE-Step music generation pipeline, outputs JSON to stdout, designed to be invoked as subprocess from `music_gen.py`.

PURPOSE: Provide machine-readable subprocess interface for ACE-Step inference so caller doesn't need to share Python environment.

ISSUES:
- Line 13: **Hardcoded absolute `sys.path` injection** — `/mnt/storage/python_env/ace_step_env/lib/python3.10/site-packages` breaks on any other machine.
- Lines 15-18: **Writes stub file into foreign site-packages at runtime** — race condition under concurrent invocation, corrupts package source tree.
- Line 15: No error handling around stub write — `OSError` at module level.
- Line 71: `shutil.copy2` overwrites `args.outfile` without checking first.
- Lines 73-74: Late import of `torchaudio` inside success path — if missing, broad `except` catches it and reports error, but generation actually succeeded. Caller sees `"status": "error"` for valid output.
- Lines 80-82: `str(e)` can leak internal paths/stack info in JSON output.
- Line 28: `--outfile` accepts any path — no sanitization, potential path traversal.
- Line 58: `lyrics=""` hardcoded with no way to override.

RISKS:
- HIGH: Runtime file creation in shared Python env — race condition under concurrent invocation.
- HIGH: Hardcoded absolute paths — deployment on any other machine fails immediately.
- MEDIUM: False-negative error on success — if `torchaudio` import fails after successful generation, valid output file is discarded.
- MEDIUM: Path traversal on `--outfile` — no canonicalization or allowlist.

ARCHITECTURE NOTES:
- Module-level side effects (lines 13-18) run before `main()` is called — simply importing the file mutates filesystem.
- JSON-to-stdout is reasonable subprocess contract but no schema version field.

VERDICT: NEEDS WORK

---

FILE: ambient-content-pipeline/src/renderer/audio_mix.py

CHANGE SUMMARY: 57 lines, entirely new module. Mixes TTS narration with background music using FFmpeg `filter_complex`, applying configurable TTS delay and music volume duck.

PURPOSE: Produce single mixed audio file per slot by overlaying delayed TTS onto trimmed background music at reduced volume.

ISSUES:
- Lines 14, 28: **`tts_duration` accepted but never used** — if TTS is longer than `slot_video_duration`, `amix:duration=longest` extends output beyond video, causing A/V desync.
- Line 14: No validation on `slot_video_duration` — zero or negative produces undefined FFmpeg behavior.
- Line 29: `music_volume` interpolated into filter string — if overridden with non-numeric string, FFmpeg misbehaves.
- Line 57: Return value `slot_video_duration` just echoed back unchanged — misleading, implies function computes something about duration.
- No input file existence check — missing files produce opaque FFmpeg errors.
- No logging — no way to debug production issues.

RISKS:
- HIGH: TTS longer than video → mixed audio duration exceeds video duration → A/V desync in final encode.
- MEDIUM: Zero/negative `slot_video_duration` → undefined FFmpeg behavior, possible infinite loop or empty output.
- MEDIUM: No path validation — missing input files produce opaque errors.

ARCHITECTURE NOTES:
- Cleanly single-responsibility with well-structured FFmpeg filter chain.
- VERDICT: NEEDS WORK

---

## Tier 2 — Minor Modifications

---

FILE: ambient-content-pipeline/src/ai_generator/generator.py (+1)

CHANGE SUMMARY: Byte-identical to old version. The "+1" is phantom count from rename detection.
VERDICT: PASS

---

FILE: ambient-content-pipeline/src/errors/exceptions.py (+1/-1)

CHANGE SUMMARY: Single docstring change: "text content pipeline" → "ambient content pipeline".
ISSUES: Unused `from typing import Any` import (pre-existing).
VERDICT: PASS

---

FILE: ambient-content-pipeline/acp.py (+1/-1)

CHANGE SUMMARY: Docstring change: "TCP CLI" → "ACP CLI". Pure rename.
VERDICT: PASS

---

FILE: ambient-content-pipeline/pyproject.toml (+11/-2)

CHANGE SUMMARY: Renamed package name and script entry point (tcp → acp), added pytest markers for integration/e2e tests.
ISSUES: `edge-tts>=7.0.0` is core dependency but only used in optional TTS path — should be optional.
VERDICT: PASS

---

FILE: ambient-content-pipeline/README.md (+13/-13)

CHANGE SUMMARY: Global find-replace tcp → acp and Text Content Pipeline → Ambient Content Pipeline. All mechanically correct.
VERDICT: PASS

---

FILE: ambient-content-pipeline/requirements.txt (+2)

CHANGE SUMMARY: Identical to old version. Added `edge-tts` dependency in prior commit before rename.
ISSUES: (1) Duplicates pyproject.toml — dual maintenance risk, one will drift. (2) Dev deps (pytest, black, ruff, mypy) mixed with runtime deps. (3) Missing trailing newline.
VERDICT: NEEDS WORK

---

## Tier 3 — Pure Renames (30 files)

CHANGE SUMMARY: All 30 files moved from `text-content-pipeline/` to `ambient-content-pipeline/` with zero content changes. Includes all `__init__.py`, payload schema/validation, slot enum/scheduler, weekly calendar resolver, AI generator prompts, template HTML, payload JSONs, examples, and plan files.
VERDICT: PASS

---

## Tier 4 — Data/Output Files (13 files)

CHANGE SUMMARY: 8 output_param JSONs, 2 plan JSONs, 2 texts JSONs, 1 temp_payload.json, 1 2026-02_texts.json.

ISSUES:
- **No secrets or PII found** — all files contain algorithmic parameters only.
- **Should be gitignored** — `outputs/*` is in `.gitignore` but files are still tracked (likely force-added). Running `git rm --cached -r outputs/` would stop tracking.
- **`outputs/202604 (Copy)/`** — duplicated directory with "Copy" in name, appears to be filesystem artifact accidentally committed.
- **Absolute paths in plan files** — `/mnt/storage/repos/content-tools/ambient-content-pipeline/outputs/...` leaks developer machine directory structure.
- **`temp_payload.json`** — temp file that should never be committed.

VERDICT: NEEDS WORK

---

## Tier 6 — Deletions (19 files)

CHANGE SUMMARY: Old `text-content-pipeline/` removed: 11 test files (-3,614 lines), 5 source files (-1,250 lines), 1 IMPLEMENTATION.md (-196), 1 temp_payload.json (-16), 1 tests/__init__.py.

All deleted source files have been replaced by expanded versions in `ambient-content-pipeline/src/`. All deleted test files have been replaced by new test files in `ambient-content-pipeline/tests/`.
VERDICT: PASS

---

## Summary of Findings

### HIGH Severity Issues (must fix before merge)

1. **`defaults.py:182` — `companion_color` variable swap bug** — luminance and saturation multiplied on wrong components
2. **`defaults.py:140` — Hardcoded absolute path** `/mnt/storage/python_env/ace_step_env/bin/python`
3. **`template_builder.py:361` — XSS risk** — unescaped text/theme/subtheme in HTML
4. **`video_encoder.py:96-101` — Stderr pipe deadlock** — `wait()` + `stderr.read()` can deadlock if ffmpeg emits >64KB
5. **`run_ace_step_pipe.py:15-18` — Runtime filesystem mutation** — writes stub file into foreign site-packages
6. **`run_ace_step_pipe.py:13` — Hardcoded absolute path** — same machine-specific path
7. **`music_gen.py:82` — Blocking subprocess in async context** — freezes event loop up to 600s
8. **`audio_mix.py:14,28` — Unused `tts_duration` parameter** — TTS longer than video causes A/V desync

### MEDIUM Severity Issues (should fix)

9. `commands.py` — 385 lines of business logic in Click handler, untestable
10. `orchestrator.py:87-91` — Global state mutation for model override
11. `html_renderer.py` — Browser process leak on error
12. `tts.py` — No timeout on subprocess.run
13. `tts.py` — Silent zero-duration fallback
14. `animation.py` — No input validation on hex colors, dimensions, speed
15. Multiple files — `print()` instead of `logging` (orchestrator, html_renderer, commands)
16. Multiple files — Temp file leaks from `NamedTemporaryFile(delete=False)` with no cleanup
17. Data files — output JSONs should be gitignored, not tracked

### LOW Severity Issues (nice to fix)

18. `commands.py:354` — Hardcoded `outputs/plans/temp_payload.json` relative path
19. `commands.py:1019` — Calls private `generator._call_ollama()` method
20. `requirements.txt` — Dev deps mixed with runtime deps
21. `animation.py:149` — `"reactive"` mode is no-op alias for `"pulse"`

### Files Passed (no issues requiring changes)

- `acp.py`, `src/ai_generator/generator.py`, `src/errors/exceptions.py`, `pyproject.toml`, `README.md`, `.gitignore`
- All 30 pure-rename files
- All 19 deletion files

### Overall PR Verdict: **NEEDS WORK**

8 high-severity and 9 medium-severity issues must be addressed before merge. The pipeline logic is architecturally sound and well-tested (342+ tests), but the error handling, subprocess management, and input validation need hardening for production use.
