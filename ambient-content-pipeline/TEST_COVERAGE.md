# Test Coverage Report — ambient-content-pipeline

**Date:** 2026-05-04
**Status:** Video content pipeline is now LIVE (May 2026 = first production video month)
**Overall coverage:** 75% (1993 statements, 496 missed)
**Broken tests:** 2 (test_prompts.py — stale assertions from prompt changes)
**Target:** 100%

---

## Production Milestone

Starting May 2026, the pipeline now produces **animated video posts with TTS narration and background music** — not just static images. This is the first production month using the animated format (purple preset, flow animation, auto-generated background music). The testing gaps in the video rendering path (orchestrator animation, html_renderer video output, video_encoder, audio_mix, tts) are now production-critical.

---

## Coverage by File

### Files at 100% (no changes needed)

- `src/__init__.py`
- `src/ai_generator/__init__.py`
- `src/ai_generator/prompts.py`
- `src/cli/__init__.py`
- `src/config/__init__.py`
- `src/config/defaults.py`
- `src/errors/__init__.py`
- `src/errors/exceptions.py`
- `src/payload/__init__.py`
- `src/payload/schema.py`
- `src/payload/validation.py`
- `src/pipeline/__init__.py`
- `src/renderer/__init__.py`
- `src/renderer/music_gen.py`
- `src/slots/__init__.py`
- `src/slots/enum.py`
- `src/slots/scheduler.py`
- `src/weekly_calendar/__init__.py`
- `src/weekly_calendar/resolver.py`

### Files Below 100%

| File | Coverage | Missed | Key Gaps |
|------|----------|--------|----------|
| `src/cli/preview.py` | 13% | 76 | Entire module untested |
| `src/cli/commands.py` | 62% | 270 | preview, regen-text, refine-posts, rerender paths |
| `src/pipeline/orchestrator.py` | 63% | 84 | TTS pre-pass, music gen, animated rendering |
| `src/renderer/html_renderer.py` | 72% | 36 | Video output, text layer, audio muxing |
| `src/renderer/tts.py` | 87% | 6 | Timeout and parse error handlers |
| `src/renderer/video_encoder.py` | 88% | 8 | Validation, broken pipe, timeout |
| `src/renderer/audio_mix.py` | 89% | 2 | Duration and volume validation |
| `src/renderer/animation.py` | 95% | 6 | Input validation edge cases |
| `src/renderer/template_builder.py` | 94% | 5 | Transparent background path |
| `src/ai_generator/generator.py` | 97% | 3 | Context-rich dedup path |

---

## Broken Tests

| Test | File | Issue |
|------|------|-------|
| `test_text_generation_prompts_exist` | `tests/test_prompts.py:104` | Asserts `"Monthly theme:"` at start, but quiet_observation now starts differently |
| `test_text_generation_prompt_quiet_observation` | `tests/test_prompts.py:154` | Asserts `"No interpretation or judgment"` which was removed |
