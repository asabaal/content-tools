# Pre-PR Audit: develop → main

## Scope and comparison basis

- **Repository:** `/mnt/storage/repos/content-tools`
- **Current branch:** `develop`
- **Current HEAD:** `bf553b148d2a52266c91395e33d12fea8484b97`
- **Target branch:** `main`
- **main commit:** `e282b12ed8aab7cc0136cab8e41eceaa15e465e7`
- **Merge base:** `e282b12ed8aab7cc0136cab8e41eceaa15e465e7` (`main` is a direct ancestor of `develop`; fast-forward merge is possible)
- **Commits unique to develop:** 84
- **Files changed:** 433
- **Lines:** ~1,070,443 insertions, ~59 deletions
- **Authorized by:** Asabaal Horan
- **Vikunja creator identity:** agent-kimi
- **Execution agent:** agent-kimi
- **Model/workflow:** Kimi Code
- **Execution channel:** Local repository + vikunja-task CLI
- **Vikunja root task:** #8
- **Prior audit artifact:** `docs/audits/pre-pr-develop-vs-main-2026-07-06.md`

## Repository baseline and protected uncommitted work

`git status --short` (as of audit start):

```text
 M music-video-pipeline/benchmarks/glm47flash_music_video_v0/evidence_manifest.json
?? .opencode/
?? docs/
```

- `music-video-pipeline/benchmarks/glm47flash_music_video_v0/evidence_manifest.json` is modified but not staged. It is a generated benchmark manifest and is treated as Asabaal’s pre-existing uncommitted work. It was not staged, committed, or altered by this audit.
- `.opencode/` is an untracked directory at repository root, treated as Asabaal’s pre-existing local work. It was not inspected, staged, or removed.
- `docs/` is the directory where this audit artifact is written. Only files created by this audit are staged; pre-existing content is left untouched.

## Change inventory

### Summary by area

| Area | Change type | Approx. files | Notes |
|------|-------------|---------------|-------|
| `ambient-content-pipeline/` | Modified | 17 | SD3 background-image generation, Ken Burns animation, CLI flags, expanded tests |
| `avatar/` | Added | 4 | Standalone Blender 3D asset preview/inspection tool + design doc |
| `font-generator.md`, `font-library.nd` | Added | 2 | Documentation/design notes for font generation and font library |
| `music-video-pipeline/` | Added | ~230 | New lyric/music video pipeline (ingest → analyze → sync → structure → design → render) |
| `projects/prophetic-preprint/` | Added | ~180 | Production workspace for a multi-song batch video project |
| Root `.gitignore` | Modified | 1 | Added ignores for ZIP, MIDI, notebook checkpoints, and prophetic-preprint generated artifacts |

### Purpose of the changed work

1. **ambient-content-pipeline** — Adds AI-generated background images via Stable Diffusion 3 Medium and a Ken Burns pan/zoom animation mode, plus expanded test coverage.
2. **music-video-pipeline** — Introduces a new pipeline for producing widescreen lyric/music videos from audio + lyrics, with browser-based editing tools and AI-assisted script generation.
3. **projects/prophetic-preprint** — Production workspace applying the music-video-pipeline to a batch of songs; contains lyrics, scripts, dashboards, and batch automation.
4. **avatar** — Standalone Blender-based 3D asset preview utility, plus a design document for a future avatar cutscene pipeline.

### Generated, temporary, experimental, or operationally important files

**Tracked files that appear generated and may not belong in version control:**

- `projects/prophetic-preprint/projects/*/data/script.json.bak` (many tracked `.bak`/`.bak2` files)
- `projects/prophetic-preprint/projects/*/data/lyrics_synced.json.bak`, `.bak2`
- `projects/prophetic-preprint/output/dashboard/*`
- `projects/prophetic-preprint/output/all-videos/*.xlsx`
- `music-video-pipeline/data/*.json` (generated analysis/ingest/sync/waveform data)
- `music-video-pipeline/data/i-never-asked-to-be-queer/data/*.json`
- `music-video-pipeline/src/render/font_registry.json` (generated)
- `music-video-pipeline/src/render/font_files_generated.txt` (generated)
- `music-video-pipeline/benchmarks/glm47flash_music_video_v0/results/*`
- `ambient-content-pipeline/outputs/plans/temp_payload.json` (modified tracked output file)

**Ignored but present locally:**

- `projects/prophetic-preprint/output/all-videos/*.mp4`
- `projects/prophetic-preprint/projects/*/output/*.mp4`
- `projects/prophetic-preprint/projects/*/data/*.wav`, `* Stems *.zip`, `* MIDI.zip`
- `music-video-pipeline/renders/*.mp4`
- `music-video-pipeline/fonts/*.ttf`

## Code and architecture findings

### ambient-content-pipeline

**Verified defects:**

1. **CLI command name is wrong for `resolve-calendar`.**
   - `src/cli/commands.py:238` registers the command from function `resolve_calendar_cmd` without an explicit `name=`.
   - Click converts underscores to hyphens, so the actual command is `resolve-calendar-cmd`.
   - The README example `acp resolve-calendar ...` is broken.
   - **Fix:** add `name="resolve-calendar"` to `@cli.command()`.

2. **`--skip-text` does not skip all AI calls.**
   - `run_all` only skips the daily text loop; weekly subtheme derivation and slot planning still call the generator/Ollama.
   - `run-all --skip-text --skip-rendering` timed out at 120 s while Ollama was reachable.

3. **Hard-coded absolute paths in `src/config/defaults.py`.**
   - `ACE_STEP_PYTHON`, `SD3_PYTHON`, and `SD3_MODEL_PATH` point to `/mnt/storage/python_env/...` and `/mnt/storage/models/...`.
   - These are host-specific and undocumented.

4. **Missing heavy dependencies.**
   - `scripts/run_sd3_pipe.py` imports `torch` and `diffusers`.
   - `scripts/run_ace_step_pipe.py` imports `torch`, `acestep`, `torchaudio`, and manipulates `transformers`.
   - None of these are declared in `pyproject.toml` or `requirements.txt`.

5. **README inaccuracies.**
   - Documents `acp demo --theme "..." --with-subthemes`, but `demo` has no such flag.
   - Documents `acp resolve-calendar ...` which does not work (see #1).

**Risks:**

- `rerender` background-music logic is fragile: `effective_bg_music = bg_music or bool(saved_music_path) or effective_animate` means `--animate` can enable background music even when no music file exists.
- Background image generation loads the image for all animation types but only `ken_burns` uses it.
- `file://` background URLs in HTML output may break if the rendered HTML is moved or run in a sandboxed browser context.

### music-video-pipeline

**Verified defects:**

1. **`serve.py:521` calls undefined `_project_dir()`.**
   - `POST /api/generate-script` fails with `NameError: name '_project_dir' is not defined`.
   - **Fix:** use the existing `_project_data_dir()` helper or equivalent.

2. **Section background cache bug in `src/render/renderer.py:1246`.**
   - Cache key includes `line_idx`, so two lines in the same section create two background images.
   - `test_render.py::TestGetBgForSection::test_caches_bg` fails.

3. **ZIP extraction without path sanitization in `src/audio/ingest.py:68-79`.**
   - `ZipFile.extract(...)` is a Zip Slip risk.

4. **Missing runtime dependencies.**
   - `opencv-python`, `faster-whisper`, `pretty_midi`, and `requests` are imported but not declared in `pyproject.toml` or `requirements.txt`.
   - `tqdm` is in `requirements.txt` but not `pyproject.toml`.

5. **Namespace package collision risk.**
   - `pyproject.toml` uses `[tool.setuptools.packages.find] where = ["src"]`, which installs top-level packages named `cli`, `audio`, `lyrics`, `pipeline`, etc., into the global namespace.

6. **Hard-coded external path in `serve.py:469-478`.**
   - `/api/timing-issues` walks `projects/prophetic-preprint/output/dashboard`, which may not exist.

7. **Hard-coded `hop = 512` in `src/scriptgen/generator.py`.**
   - Ignores the `hop_length` stored in `analysis.json`, which can cause indexing mismatches.

**Risks:**

- `src/sections/` and `src/visual/` are mostly empty despite being described in `DESIGN.md`.
- `DESIGN.md` still references a missing top-level `README.md`.
- Broad `except Exception` handling in `src/cli/commands.py` swallows or downgrades errors.
- Group transform in `src/canvas/renderer.py` ignores the group’s own position.
- `Font family: int = 0` typing means a string value would crash `ImageFont.truetype`.

### Root / other areas

- **No top-level `README.md`.** A new contributor has no quickstart.
- **No top-level `pyproject.toml` or `setup.py`.** The repo is a collection of sub-pipelines without unified packaging.
- **`tests/test_data_integrity.py` is a standalone script, not a pytest suite.** It passes when run directly but fails under pytest because `data`/`clips` parameters are not fixtures.
- **`projects/prophetic-preprint/` contains many tracked `.bak` files** that are transient editing artifacts.

## Tests, coverage, and results

### Root

| Command | Result |
|---------|--------|
| `python3 tests/test_data_integrity.py` | ✅ 11 checks passed |
| `python3 -m pytest tests/` | ❌ 4 passed, 6 errors (fixture issues) |

### ambient-content-pipeline

| Command | Result |
|---------|--------|
| `python3 -m pytest tests/ -q --tb=short` | ⚠️ 471 passed, 1 failed, 1 warning |
| `python3 -m pytest tests/ -q --tb=short -m "not e2e"` | ✅ 457 passed, 15 deselected, 1 warning |
| `python3 -m pytest --cov=src --cov-report=term tests/ -q --tb=short` | ✅ 472 passed, 1 warning, 99% coverage |

The single failure is `tests/test_e2e.py::test_e2e_animated_video_with_tts` due to a Playwright/Chromium headless screenshot error. It did not reproduce in the coverage run, indicating flakiness.

### music-video-pipeline

| Command | Result |
|---------|--------|
| `python3 -m pytest tests/ -q --tb=short` | ⚠️ 2368 passed, 14 failed, 5 warnings |

Failure breakdown:

- 9 failures in `tests/test_analyzer.py` — `ModuleNotFoundError: No module named 'faster_whisper'`.
- 2 failures in `tests/test_cli.py::TestAnalyze` — vocal stem transcription fails because `faster_whisper` is missing.
- 1 failure in `tests/test_render.py::TestGetBgForSection::test_caches_bg` — real cache-key bug.
- 1 failure in `tests/test_assistant_benchmark.py::TestAPIRunner::test_requires_api_key_for_live` — flaky live-network/API-key behavior.
- 1 additional analyzer-related failure tied to missing optional deps.

No coverage configuration exists for this module.

## Manual validation

### ambient-content-pipeline

| Command | Result |
|---------|--------|
| `python3 acp.py --help` | ✅ Works |
| `python3 acp.py list-presets` | ✅ Works |
| `python3 acp.py show-preset default` | ✅ Works |
| `python3 acp.py validate --theme "Test" --year 2026 --month 7` | ✅ Works |
| `python3 acp.py init-month 2099 12 --theme "Audit Test" --output /tmp/...` | ✅ Works |
| `python3 acp.py resolve-calendar ...` | ❌ Command not found (actual name: `resolve-calendar-cmd`) |
| `python3 acp.py resolve-calendar-cmd /tmp/audit_test_payload.json --output ...` | ✅ Works |
| `python3 acp.py run-all --payload /tmp/audit_test_payload.json --skip-text --skip-rendering --output-dir /tmp/audit_outputs` | ❌ Timed out at 120 s; still calls AI for subthemes/slots |

### music-video-pipeline

| Command | Result |
|---------|--------|
| `python3 music-video-pipeline/mvp.py --help` | ✅ Works |
| `python3 music-video-pipeline/mvp.py info -p music-video-pipeline` | ✅ Works |
| `python3 music-video-pipeline/mvp.py render -p music-video-pipeline --start 0 --end 1 --output /tmp/mvp_test.mp4` | ✅ Rendered 5 unique frames, wrote 3.7 MB MP4 |
| `python3 -u music-video-pipeline/serve.py --project music-video-pipeline --port 8902` | ✅ Server starts |
| `curl http://localhost:8903/api/templates` and `/api/project` | ✅ Valid JSON |
| `POST /api/generate-script` | ❌ `NameError: name '_project_dir' is not defined` |

## Installation and operating readiness

| Item | Status | Notes |
|------|--------|-------|
| Top-level README | ❌ Missing | No quickstart for the repo as a whole |
| Top-level pyproject.toml | ❌ Missing | Sub-projects package independently |
| ambient-content-pipeline pyproject.toml | ⚠️ Partial | Missing `torch`, `diffusers`, `transformers`, `torchaudio`, `acestep` |
| ambient-content-pipeline requirements.txt | ⚠️ Partial | Same missing heavy deps |
| music-video-pipeline pyproject.toml | ⚠️ Partial | Missing `opencv-python`, `faster-whisper`, `pretty_midi`, `requests`; namespace-package risk |
| music-video-pipeline requirements.txt | ⚠️ Partial | Same missing deps |
| Entry points | ⚠️ Work via scripts | `acp.py`, `mvp.py`, `serve.py` |
| FFmpeg | ✅ Available | Version 6.1.1 on this host |
| Font assets | ⚠️ Bundled | `music-video-pipeline/fonts/` exists but is not auto-downloaded at install |

## Findings by severity

### Blockers (should be fixed before PR)

1. `ambient-content-pipeline`: `resolve-calendar` CLI command name is broken; README example fails.
2. `ambient-content-pipeline`: `--skip-text` behavior is misleading or broken (still calls AI).
3. `ambient-content-pipeline`: Hard-coded absolute paths and missing heavy dependencies make SD3/ACE-Step features non-portable.
4. `music-video-pipeline`: `serve.py` `POST /api/generate-script` crashes with `NameError`.
5. `music-video-pipeline`: Missing `faster-whisper` and `pretty_midi` dependencies cause 11 test failures.
6. `music-video-pipeline`: Section background cache key bug (`test_caches_bg` fails).
7. `music-video-pipeline`: ZIP extraction path sanitization (Zip Slip risk).

### High (should be reviewed before merge)

8. `music-video-pipeline`: Namespace package collision in `pyproject.toml`.
9. No top-level `README.md` or unified install instructions.
10. `projects/prophetic-preprint/` contains many tracked `.bak` files.

### Medium

11. `music-video-pipeline`: Hard-coded `hop = 512` ignores `analysis.json` `hop_length`.
12. `music-video-pipeline`: Hard-coded external path in `/api/timing-issues`.
13. `music-video-pipeline`: Empty `src/sections/` and `src/visual/` contradict `DESIGN.md`.
14. `ambient-content-pipeline`: `rerender` background-music logic is fragile.
15. `ambient-content-pipeline`: `file://` background URLs may break in sandboxed/moved contexts.

### Low / informational

16. `ambient-content-pipeline`: `AsyncMock` warning in `test_image_gen.py`.
17. `ambient-content-pipeline`: Docstring placement issue in `tests/test_orchestrator.py:887`.
18. `music-video-pipeline`: `--start/--end` preview still prints full-duration frame count.
19. `music-video-pipeline`: `dashboard` command uses a fragile parent-parent heuristic for projects root.
20. Root `tests/test_data_integrity.py` is not a valid pytest suite.

## Decisions or review requests

1. **CLI command name:** Decide whether to rename the command to `resolve-calendar` or update README/help to match `resolve-calendar-cmd`.
2. **`--skip-text` semantics:** Decide whether `--skip-text` should skip all AI calls or be renamed/documented to reflect that it only skips daily text generation.
3. **SD3 / ACE-Step portability:** Decide whether to document the required environment variables and Python environments, or to remove the hard-coded defaults and require explicit configuration.
4. **Generated files in repo:** Decide whether to remove `.bak` files and other generated artifacts from `projects/prophetic-preprint/` and `music-video-pipeline/data/`.
5. **Missing dependencies:** Decide whether `faster-whisper`, `pretty_midi`, `opencv-python`, `requests`, and the SD3/ACE-Step heavy deps should be declared as required, optional, or documented-only.
6. **Namespace packages:** Decide whether to fix `music-video-pipeline` package discovery to avoid installing `cli`, `audio`, `lyrics`, etc. at the top level.
7. **`serve.py` generate-script endpoint:** Decide whether to fix and keep this endpoint or disable it until it is functional.

## Known limitations and unvalidated areas

- The flaky Playwright e2e screenshot failure in `ambient-content-pipeline` was not root-caused.
- `music-video-pipeline` assistant benchmark tests require `ZAI_API_KEY` and a live network endpoint; behavior was not fully validated.
- Full end-to-end music-video rendering with real audio/stems/lyrics was not attempted.
- GPU Whisper and ACE-Step / SD3 subprocess paths were not executed because the dedicated Python environments and models are host-specific.
- The prophetic-preprint batch project was not audited song-by-song; only the structure and generated-file hygiene were reviewed.

## Vikunja task references

| Task ID | Title | Native creator | Native assignee | Status |
|---------|-------|----------------|-----------------|--------|
| #8 | [Pre-PR Audit] content-tools — develop vs main | asabaal | agent-kimi | Active |
| #9 | [Pre-PR Audit] Develop-vs-main change inventory and architecture review | asabaal | agent-kimi | Active |
| #10 | [Pre-PR Audit] Test and coverage assessment | asabaal | agent-kimi | Active |
| #11 | [Pre-PR Audit] Manual validation of changed workflows | asabaal | agent-kimi | Active |
| #12 | [Pre-PR Audit] Installation and operating-readiness review | asabaal | agent-kimi | Active |

## Git commit references

- `develop` HEAD: `bf553b148d2a52266c91395e33d12fea8484b97` — "initial timing workbech also present"
- `main`: `e282b12ed8aab7cc0136cab8e41eceaa15e465e7`
- Merge base: `e282b12ed8aab7cc0136cab8e41eceaa15e465e7`

## Commands run

```bash
cd /mnt/storage/repos/content-tools
git branch --show-current
git log --oneline -1
git rev-parse main
git rev-parse develop
git merge-base main develop
git status --short
git log --oneline main..develop
git diff --stat main..develop
git diff --name-status main..develop

# ambient-content-pipeline
python3 -m pytest tests/ -q --tb=short
python3 -m pytest tests/ -q --tb=short -m "not e2e"
python3 -m pytest --cov=src --cov-report=term tests/ -q --tb=short
python3 acp.py --help
python3 acp.py list-presets
python3 acp.py show-preset default
python3 acp.py validate --theme "Test" --year 2026 --month 7
python3 acp.py resolve-calendar-cmd /tmp/audit_test_payload.json --output /tmp/audit_resolved.json

# music-video-pipeline
python3 -m pytest tests/ -q --tb=short
python3 music-video-pipeline/mvp.py --help
python3 music-video-pipeline/mvp.py info -p music-video-pipeline
python3 music-video-pipeline/mvp.py render -p music-video-pipeline --start 0 --end 1 --output /tmp/mvp_test.mp4
python3 -u music-video-pipeline/serve.py --project music-video-pipeline --port 8902

# root
python3 tests/test_data_integrity.py
python3 -m pytest tests/ -q --tb=short
```
