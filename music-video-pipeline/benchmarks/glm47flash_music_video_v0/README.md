# GLM-4.7-Flash Music Video Scripting Benchmark v0

## Purpose

Test whether `glm-4.7-flash`, called through the general Z.AI API, can:

1. accurately inspect and map the current scripting pipeline;
2. identify only features that are actually supported by code or templates;
3. generate constrained, schema-valid candidate section-level script patches;
4. identify when a requested visual behavior cannot be guaranteed by the current scripting surface;
5. save reproducible artifacts for later human evaluation.

## Non-Goals

- This benchmark does NOT modify production scripts, renderer behavior, templates, or generation rules.
- This benchmark does NOT assess rendered visual quality.
- This benchmark is not a live assistant — it produces artifacts for human review.
- AI Psalm 9 is used only as a read-only structured fixture, not as an active production project.

## Why AI Psalm 9?

AI Psalm 9 is an existing project in the repository whose data files (`analysis.json`, `lyrics_synced.json`, `mvp_project.json`, `script.json`, and aspect-ratio variants) happen to be valid inputs for the scripting pipeline. We copy only the JSON files — never binaries, audio, or renders — and treat them as an immutable fixture.

## Setup

### Prerequisites

- Python >= 3.10
- `ZAI_API_KEY` environment variable (only needed for live runs)

### Install dependencies

```bash
pip install -r requirements.txt
```

## Commands

All commands run from the repository root.

### Prepare fixtures

```bash
python -m assistant.flash_music_video_benchmark fixtures
```

Copies only the allowlisted JSON files from `../projects/prophetic-preprint/projects/ai-psalm-9/data/` and generates `fixture/ai_psalm_9/manifest.json` with SHA-256 digests.

### Build evidence bundle

```bash
python -m assistant.flash_music_video_benchmark evidence
```

Scans the repository for source code, templates, and relevant tests. Writes `evidence_manifest.json` with file paths, SHA-256 hashes, and category annotations.

### Dry-run (no API call)

```bash
python -m assistant.flash_music_video_benchmark run --dry-run --case system_discovery
```

### Run a single case (3 attempts)

```bash
export ZAI_API_KEY="your-key-here"
python -m assistant.flash_music_video_benchmark run --case feature_ledger --attempts 3
```

### Full benchmark run

```bash
export ZAI_API_KEY="your-key-here"
python -m assistant.flash_music_video_benchmark run
```

### Run tests

```bash
python -m pytest tests/test_assistant_benchmark.py -v
```

## Artifact Locations

| Artifact | Path |
|----------|------|
| Fixture data | `benchmarks/glm47flash_music_video_v0/fixture/ai_psalm_9/` |
| Fixture manifest | `benchmarks/glm47flash_music_video_v0/fixture/ai_psalm_9/manifest.json` |
| Evidence bundle | `benchmarks/glm47flash_music_video_v0/evidence_manifest.json` |
| Result artifacts | `benchmarks/glm47flash_music_video_v0/results/{case_name}/attempt_{N}.json` |
| Run summary | `benchmarks/glm47flash_music_video_v0/results/run_summary.json` |
| Human review sheet | `benchmarks/glm47flash_music_video_v0/rubrics/human_review.md` |

## How to Review Results

1. Read the raw response JSON in each attempt file.
2. Check the `parsed_output` field for structural validity.
3. Open the `human_review.md` rubric and score each category 0–2.
4. Manually verify source citations against the actual source files.
5. For candidate patches, confirm fields exist in the confirmed-field inventory.
6. Note whether the human reviewer would route this task to Flash again.

## Limitations

- **Schema-valid ≠ factually correct.** A response may parse correctly but cite wrong files or invent behavior.
- **Source citations must be manually audited.** The model may claim evidence that doesn't actually support its claim.
- **Artistic quality remains a human judgment.** This benchmark does not assess visual aesthetics.
- **Rate limits / API availability may affect execution.** The Z.AI API has no SLA guarantees in this context.
- **This benchmark is not yet a live assistant.** It produces evaluation artifacts, not production edits.
