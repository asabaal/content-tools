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
- **Execution agent:** agent-kimi
- **Model/workflow:** Kimi Code
- **Execution channel:** Local repository + vikunja-task CLI
- **Vikunja root task:** #8

## Repository baseline and protected uncommitted work

`git status --short` (as of audit start):

```text
 M music-video-pipeline/benchmarks/glm47flash_music_video_v0/evidence_manifest.json
?? .opencode/
```

- `music-video-pipeline/benchmarks/glm47flash_music_video_v0/evidence_manifest.json` is modified but not staged. It is a generated benchmark manifest and is treated as Asabaal’s pre-existing uncommitted work. It was not staged, committed, or altered by this audit.
- `.opencode/` is an untracked directory at repository root, also treated as Asabaal’s pre-existing local work. It was not inspected, staged, or removed.

No other uncommitted work existed at audit start.

## Change inventory

### Summary by area

| Area | Change type | Approx. files | Notes |
|------|-------------|---------------|-------|
| `ambient-content-pipeline/` | Modified | 17 | SD3 background-image generation, Ken Burns animation, tutorial explorer rewrite, expanded tests |
| `avatar/` | Added | 4 | Standalone Blender 3D asset preview/inspection tool + design doc |
| `font-generator.md`, `font-library.nd` | Added | 2 | Documentation/design notes for font generation |
| `music-video-pipeline/` | Added | ~230 | New lyric/music video pipeline (ingest → analyze → sync → structure → design → render) |
| `projects/prophetic-preprint/` | Added | ~180 | Production workspace for 42-song batch video project |
| Root `.gitignore` | Modified | 1 | Added ignores for ZIP, MIDI, and prophetic-preprint generated artifacts |

### Purpose of the changed work

1. **ambient-content-pipeline** — Adds AI-generated background images via Stable Diffusion 3 Medium and a Ken Burns pan/zoom animation mode that can consume them. Also hardens test coverage and expands the interactive tutorial explorer.
2. **music-video-pipeline** — Introduces a wholly new pipeline for producing widescreen lyric/music videos from audio + lyrics, with browser-based editing tools and AI-assisted script generation.
3. **projects/prophetic-preprint** — First-draft production workspace that applies the music-video-pipeline to a 42-song album; contains lyrics, scripts, dashboards, and batch automation.
4. **avatar** — Standalone Blender-based 3D asset preview utility, plus a design document for a future avatar cutscene pipeline.

### Generated, temporary, experimental, or operationally important files

**Tracked files that look generated and probably should not be in version control:**

- `projects/prophetic-preprint/projects/*/data/script.json.bak` (51 tracked `.bak`/`.bak2` files)
- `projects/prophetic-preprint/projects/*/data/lyrics_synced.json.bak`, `.bak2`
- `projects/prophetic-preprint/long_line_layout_report*.html`
- `projects/prophetic-preprint/output/all-videos/prophetic-preprint-lyrics.xlsx`
- `projects/prophetic-preprint/output/dashboard/*.html`, `*.json`, `*.csv`
- `projects/prophetic-preprint/*.odt` (binary feedback documents)
- `music-video-pipeline/data/*.json` (generated analysis/ingest/sync/waveform data)
- `music-video-pipeline/data/i-never-asked-to-be-queer/data/*.json`
- `music-video-pipeline/src/render/font_registry.json` (~260 KB, generated)
- `music-video-pipeline/src/render/font_files_generated.txt` (~130 KB, generated)
- `music-video-pipeline/benchmarks/glm47flash_music_video_v0/evidence_manifest.json` (currently dirty)
- `music-video-pipeline/benchmarks/glm47flash_music_video_v0/results/*` (attempt artifacts)
- `ambient-content-pipeline/outputs/plans/temp_payload.json` (modified tracked output file)

**Ignored but present locally:**

- `projects/prophetic-preprint/output/all-videos/*.mp4` (~13–68 MB each)
- `projects/prophetic-preprint/projects/*/output/*.mp4` and `*.mp4.bak`
- `projects/prophetic-preprint/projects/*/data/*.wav`, `* Stems *.zip`, `* MIDI.zip`
- `projects/prophetic-preprint/projects/*/data/cache/`
- `music-video-pipeline/renders/*.mp4`
- `music-video-pipeline/data/i-never-asked-to-be-queer/*.zip`, `*.wav`
- `music-video-pipeline/data/cache/stems/*.wav`
- `music-video-pipeline/fonts/*.ttf`

## Code and architecture findings

### ambient-content-pipeline

**Fit:** Changes are consistent with the existing project structure. The SD3 bridge follows the same subprocess-outsource pattern already used for AceStep.

**Verified defects / risks:**

1. **Hard-coded absolute paths** in `src/config/defaults.py`:
   - `ACE_STEP_PYTHON = "/mnt/storage/python_env/ace_step_env/bin/python"` (line 144)
   - `SD3_PYTHON = "/mnt/storage/python_env/sd3_env/bin/python"` (line 158)
   - `SD3_MODEL_PATH = "/mnt/storage/models/sd3-medium/sd3_medium_incl_clips_t5xxlfp8.safetensors"` (line 163)
   - These defaults are host-specific and will fail on other machines. They are environment-overridable but not documented as such.

2. **SD3 failure aborts entire pipeline** — `orchestrator.py` has no graceful fallback if background-image generation fails.

3. **`file://` background URLs** — `template_builder.py` and `html_renderer.py` emit `url('file:///...')` for background images. This can be blocked or behave inconsistently in sandboxed Chromium/Playwright contexts and breaks if the output HTML is moved.

4. **Missing dependency declaration** — `run_sd3_pipe.py` needs `torch`, `diffusers`, and `transformers`, but these are not listed in `pyproject.toml` or `requirements*.txt` (intentionally isolated in a separate venv, but not documented).

5. **Tautological test** — `tests/test_animation.py::test_ken_burns_zoom_progression` contains `assert c0 != c1 or True`, which can never fail.

6. **Code quality** — `tutorial_explorer.py` has unused imports, duplicated constants, and is ~1,400 lines of mixed logic + inline HTML/CSS/JS.

### music-video-pipeline

**Fit:** The new directory is self-contained and mirrors the top-level autonomy of `ambient-content-pipeline`.

**Verified defects / risks:**

1. **Namespace collision** — `pyproject.toml` discovers packages from `src/`, so modules will be installed as top-level names: `audio`, `canvas`, `cli`, `lyrics`, `pipeline`, `render`, `scriptgen`, `sections`, `transform`, `visual`, `assistant`. These generic names will conflict with other installed packages.

2. **Failing tests (logic bugs):**
   - `tests/test_assistant_benchmark.py::TestAPIRunner::test_requires_api_key_for_live` — expects an error when `api_key=""` and `dry_run=False`, but `ZAIAPIRunner.call()` does not validate the key and attempts a real network request.
   - `tests/test_render.py::TestGetBgForSection::test_caches_bg` — cache key includes `line_idx` (`renderer.py:1246`), so two lines in the same section produce different `Image` objects; `bg1 is bg2` fails.

3. **Hard-coded `/mnt/storage` paths** in:
   - `download_fonts.py:11` — `REPO_DIR = Path("/mnt/storage/tmp/opencode/google-fonts")`
   - `scripts/apply_slate_v2.py:25` — project base path
   - `scripts/apply_recipe_all.py` — imports `batch_videos` from `projects/prophetic-preprint`
   - `scripts/render_catalog.py:33` — renders directory
   - `recipes/reality_signal_slate_v2.json:9-10` — absolute image/logo paths
   - `recipes/asabaal_interstitials.json:11` — absolute image path
   - `data/*.json` and benchmark fixtures — absolute paths to WAV/MIDI/cache files

4. **Hard-coded branding** — `src/render/renderer.py` and `src/transform/branding.py` embed "A Reality Signal" / "Asabaal Horan" defaults.

5. **`_frame_is_unique()` always returns `True`** (`src/render/renderer.py:509-517`), making the frame-reuse branch dead code.

6. **Duplicated rendering logic** — `_render_text_on_bg()` (`renderer.py:1150-1232`) largely duplicates `render_frame()` (`renderer.py:1061-1148`).

7. **`serve.py` writes uploaded JSON directly to disk** with paths derived from URL; no traversal validation.

8. **`requirements.txt` vs `pyproject.toml` mismatch** — `requirements.txt` includes `tqdm>=4.60.0`, which is missing from `pyproject.toml` dependencies.

9. **Empty / stub modules** — `src/visual/` and `src/sections/` contain only empty `__init__.py`. `src/pipeline/` only has `models.py`; the orchestrator described in `DESIGN.md` does not exist.

10. **No local `.gitignore`** — generated JSONs, `font_registry.json`, `font_files_generated.txt`, `evidence_manifest.json`, renders, and font files are not excluded by a local ignore file (some are covered by root `.gitignore`, many are not).

### projects/prophetic-preprint

**Fit:** A sibling project workspace that uses the music-video-pipeline. It is logically separate.

**Verified defects / risks:**

1. **51 tracked `.bak`/`.bak2` files** across song directories; these are backup files and should not be version-controlled.
2. **`generate_form.py`** is unrelated to the project and hardcodes output to `/home/asabaal/Downloads/self_employment_form_fillable.pdf`.
3. **`batch_videos.py`** hardcodes the sibling pipeline path and writes to project directories.
4. **`lyrics_timing_workbench.py`** has hardcoded absolute paths and imports internal pipeline modules; not portable.
5. **Generated dashboards/spreadsheets/reports** tracked in `output/dashboard/` and `output/all-videos/`.

### avatar

**Fit:** Clean, standalone, well-documented.

**Risks:**
- `scripts/render_asset_preview.py` and `scripts/inspect_3d_asset.py` require Blender 4.0+ in background mode; this is documented.
- `outputs/` directory is ignored, which is correct.

### Secrets risks

- **No hardcoded API keys, passwords, tokens, or private keys** were found in changed source files.
- `music-video-pipeline/src/assistant/flash_music_video_benchmark.py` reads `ZAI_API_KEY` from the environment and has redaction/validation helpers; no key is committed.
- Ollama is assumed on `http://localhost:11434` with no authentication.

## Tests, coverage, and results

### Test infrastructure

| Project | Framework | Test files | Collected tests | Coverage config |
|---------|-----------|------------|-----------------|-----------------|
| `ambient-content-pipeline` | pytest, pytest-asyncio | 24 modules | 472 | `pytest-cov` in dev extras; no `.coveragerc` |
| `music-video-pipeline` | pytest | 42 modules + `conftest.py` | 2,382 | None declared; `pytest-cov` available in env |
| Root | pytest | `tests/test_data_integrity.py`, `core/test_core.py`, `tools/01-transcribe/test_transcribe.py` | 22 | None |

### Commands run and outcomes

#### ambient-content-pipeline

```bash
python -m pytest --collect-only
# 472 tests collected, exit 0

python -m pytest -q -m "not integration and not e2e" --ignore=tests/test_e2e.py
# 448 passed, 8 deselected, 1 warning, 1 failed
# Failed: tests/test_html_renderer.py::test_render_text_to_image_with_background_image
# Reason: PermissionError executing Playwright bundled Node binary
#   /mnt/storage/python_env/devtools/lib/python3.12/site-packages/playwright/driver/node

python -m pytest -q -m "not integration and not e2e" --ignore=tests/test_html_renderer.py
# 427 passed, 23 deselected, 1 warning in 18.04s

python -m pytest -q --cov=src --cov-report=term
# 14 failed, 458 passed, 1 warning
# Failures are the e2e module + the single Playwright permission failure
# Coverage: 99%
```

#### music-video-pipeline

```bash
python -m pytest --collect-only
# 2,382 tests collected, exit 0

python -m pytest -q
# 2,380 passed, 2 failed, 4 warnings in 61.34s
# Failed:
#   tests/test_assistant_benchmark.py::TestAPIRunner::test_requires_api_key_for_live
#   tests/test_render.py::TestGetBgForSection::test_caches_bg

python -m pytest -q --cov=src --cov-report=term
# 2,380 passed, 2 failed, 4 warnings
# Coverage: 92%
```

#### Root-level tests

```bash
python -m pytest tests/test_data_integrity.py tools/01-transcribe/test_transcribe.py core/test_core.py -q
# 15 passed, 1 failed, 6 errors, 4 warnings
# Failure: core/test_core.py::test_load_transcript (FileNotFoundError)
# Errors: tests/test_data_integrity.py — missing project/clip data files
```

### Coverage status

- `ambient-content-pipeline`: **99%** coverage of `src/` when measured.
- `music-video-pipeline`: **92%** coverage of `src/` when measured.
- Coverage is not configured in CI; it is run ad-hoc via CLI. No `.coveragerc` or `[tool.coverage]` config exists.
- Low-coverage modules in music-video-pipeline: `src/transform/branding.py` 44%, `src/transform/recipes.py` 76%, `src/transform/selectors.py` 82%.

### Test blockers

- Playwright Node binary is not executable in the current environment, blocking all HTML-renderer tests that launch a browser.
- Root-level tests require data files that do not exist in the checkout.

## Manual validation

### Safe CLI discovery

```bash
cd /mnt/storage/repos/content-tools/ambient-content-pipeline
python -m src.cli.commands --help
# Success: all commands listed (init-month, validate, run-all, rerender, etc.)

cd /mnt/storage/repos/content-tools/music-video-pipeline
python mvp.py --help
# Success: commands listed (analyze, audit, dashboard, info, init, render, serve, sync, transform)

python mvp.py info --help
# Success: usage shown
```

### What was deliberately not run

- No actual pipeline runs, renders, or audio analysis were executed.
- No external API calls (ZAI, Ollama, SD3, Whisper, etc.) were made.
- No browser-based editor (`serve.py`) was started.
- No paid services or production systems were invoked.
- No files outside the repository were read or written.

## Installation and operating readiness

### ambient-content-pipeline

- `README.md` exists with installation and usage instructions.
- `pyproject.toml` declares runtime and dev dependencies.
- Install command documented: `pip install -e .` and `playwright install chromium`.
- Requires Python 3.11+.
- Hidden dependency: SD3 inference requires `torch`, `diffusers`, `transformers` in a separate virtualenv at the hardcoded path; not documented.

### music-video-pipeline

- **No `README.md`** — `DESIGN.md` states README is TODO (Phase 5).
- `pyproject.toml` declares basic dependencies but omits dev/test dependencies.
- `requirements.txt` adds `tqdm`, which is missing from `pyproject.toml`.
- Entry point `mvp = "cli.commands:cli"` is declared but package namespace collision makes the project effectively un-installable alongside common Python packages.
- Requires `ffmpeg` on PATH (not documented as a dependency).
- Font loading falls back to hardcoded Linux system paths; non-Linux installs get a default bitmap font.

### projects/prophetic-preprint

- No `requirements.txt` or `pyproject.toml`.
- `batch_videos.py` depends on sibling `music-video-pipeline/` at `../../music-video-pipeline/`.
- `generate_form.py` requires `reportlab`.

### avatar

- `README.md` exists with clear Blender-based usage.
- No Python package manifest; intended to be run inside Blender.

## Findings by severity

### Blockers (should be fixed before PR)

1. **Two failing unit tests in `music-video-pipeline` are genuine logic bugs**, not environment issues:
   - `tests/test_assistant_benchmark.py::TestAPIRunner::test_requires_api_key_for_live`
   - `tests/test_render.py::TestGetBgForSection::test_caches_bg`
2. **`music-video-pipeline` package namespace collision** — installing the package pollutes the top-level Python namespace with generic module names.
3. **Tracked `.bak`/`.bak2` files in `projects/prophetic-preprint/`** — 51 backup files should be removed and ignored.
4. **`projects/prophetic-preprint/generate_form.py`** hardcodes output outside the repo and is unrelated to the project.
5. **Absolute `/mnt/storage` paths in code and recipes** make the project non-portable.
6. **Hardcoded branding** in `music-video-pipeline/src/render/renderer.py` and `src/transform/branding.py`.

### High-priority improvements

7. Add a `music-video-pipeline/.gitignore` for generated JSONs, font registry, evidence manifest, renders, and cache.
8. Add a `README.md` to `music-video-pipeline/`.
9. Document `ffmpeg` and system-font requirements.
10. Refactor `music-video-pipeline/src/cli/commands.py` (1,903 lines) into smaller modules.
11. Deduplicate `render_frame()` / `_render_text_on_bg()` in `src/render/renderer.py`.
12. Fix `_frame_is_unique()` so it actually detects reusable frames.
13. Validate `serve.py` POST paths to prevent directory traversal.
14. Remove or relocate prophetic-preprint-specific scripts from `music-video-pipeline/scripts/`.

### Informational observations

15. `main` is a direct ancestor of `develop`; the PR will be a fast-forward.
16. The diff is dominated by generated data (scripts, JSONs, dashboards) in `projects/prophetic-preprint/` and `music-video-pipeline/data/`.
17. `ambient-content-pipeline` test coverage is strong (99%) when Playwright is executable.
18. `music-video-pipeline` test coverage is good (92%) but some modules are under-tested.
19. No committed secrets were found.

## Decisions or review requests

### [Review Needed] Decide whether to remove generated data before PR

- **Decision:** Should generated JSONs, dashboards, `.bak` files, and tracked renders/spreadsheets be removed from the PR, or is this repository intentionally an archive of production artifacts?
- **Why it matters:** The PR adds ~1M lines, most of which are generated data. This will permanently bloat the repository and complicate future diffs.
- **Recommendation:** Remove generated artifacts and add them to `.gitignore`. Keep only hand-authored lyrics, scripts, design docs, and source code. Provide a script to regenerate data locally.

### [Review Needed] Decide portability stance for hardcoded paths

- **Decision:** Should absolute `/mnt/storage` paths and hardcoded branding be replaced with configuration/CLI arguments before merge?
- **Why it matters:** The code will not run on any other machine without modification.
- **Recommendation:** Replace defaults with environment-driven configuration and document required setup.

### [Review Needed] Decide package naming for `music-video-pipeline`

- **Decision:** Should source modules be moved under a `music_video_pipeline.*` namespace before first installable release?
- **Why it matters:** Current top-level package names (`audio`, `canvas`, `cli`, `render`, etc.) conflict with common Python packages.
- **Recommendation:** Refactor to a single package namespace. This is a breaking change best made before merge.

## Known limitations and unvalidated areas

- **Playwright environment:** The Playwright Node binary is not executable in the current environment, so HTML-renderer tests could not be fully validated.
- **External APIs:** No calls to Ollama, SD3, ZAI, Whisper, or any paid service were made.
- **Long renders:** No actual video rendering, audio analysis, or SD3 image generation was performed.
- **Browser tools:** `music-video-pipeline/tools/` HTML/JS editors were inspected but not executed in a browser.
- **Root-level tests:** Six root-level tests fail because required data files are absent; not investigated further.
- **Generated content review:** Artistic lyrics and visual-design decisions were not evaluated for content policy.

## Vikunja task references

| Task ID | Title | Native creator | Assignee | Status |
|---------|-------|----------------|----------|--------|
| #8 | [Pre-PR Audit] content-tools — develop vs main | asabaal | agent-kimi | active |
| #9 | [Pre-PR Audit] Develop-vs-main change inventory and architecture review | asabaal | agent-kimi | active |
| #10 | [Pre-PR Audit] Test and coverage assessment | asabaal | agent-kimi | active |
| #11 | [Pre-PR Audit] Manual validation of changed workflows | asabaal | agent-kimi | active |
| #12 | [Pre-PR Audit] Installation and operating-readiness review | asabaal | agent-kimi | active |

## Git commit references

- **main:** `e282b12ed8aab7cc0136cab8e41eceaa15e465e7`
- **develop:** `bf553b148d2a52266c91395e33d12fea8484b97`
- **Merge base:** `e282b12ed8aab7cc0136cab8e41eceaa15e465e7`
- **Audit artifact commit:** *to be recorded after commit*

---

*Audit generated by agent-kimi using Kimi Code. Native Vikunja creator identity: asabaal.*
