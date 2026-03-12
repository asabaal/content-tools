# Data Abstraction Layer - Implementation Plan

**Created**: March 11, 2026
**Purpose**: Make the pipeline project-agnostic - specify which project at server launch, with configurable data directories.

---

## Overview

The pipeline was developed with hardcoded paths for test content (Life is Your Word, Season 0, Episode 3). This plan abstracts the data layer so any project can be processed.

### Goals

1. Specify project directory at server launch via `--project` flag
2. Configurable data directory structure per project (via project.json)
3. Automatic v1 → v2 schema migration for existing projects
4. All HTML tools get paths from server API (no hardcoded `../../data/` paths)

---

## Schema Changes

### Project JSON v2 Schema

```json
{
  "schema_version": "2.0",
  "project": {
    "name": "Life is Your Word",
    "season": 0,
    "episode": 3,
    "description": "Optional description",
    "created": "2025-10-08",
    "modified": "2026-03-11"
  },
  "paths": {
    "raw": "raw",
    "transcripts": "transcripts",
    "combined_video": "video_combined.mp4",
    "combined_transcript": "transcript_combined.json",
    "waveforms": "waveforms.json",
    "output": "output"
  },
  "videos": [...],
  "clips": [...],
  "timeline_order": [...],
  "caption_style": {...}
}
```

- All paths in `paths` are **relative to the data directory**
- Legacy projects (no `schema_version`) work via defaults + auto-migration

---

## File Changes

| Action | File | Purpose |
|--------|------|---------|
| CREATE | `core/project_config.py` | `ProjectConfig` class + migration logic |
| MODIFY | `core/io.py` | Use `ProjectConfig` for path resolution |
| MODIFY | `serve.py` | CLI args, `/api/config`, global config |
| MODIFY | `tools/02-review/index.html` | Use `/api/config` for paths |
| MODIFY | `tools/03-select/index.html` | Use `/api/config` for paths |
| MODIFY | `tools/04-assemble/index.html` | Use `/api/config` for paths |
| MODIFY | `tools/05a-capstyle/index.html` | Use `/api/config` for paths |
| MODIFY | `tools/05b-render/render.py` | Accept `--project` flag |
| MODIFY | `tools/04-assemble/generate_waveforms.py` | Accept `--project` flag |
| MODIFY | `tools/01-transcribe/transcribe.py` | Accept `--project` flag |
| CREATE | `core/__main__.py` | CLI: `python -m core.project init` |

---

## New CLI Usage

### Server

```bash
# Current behavior (backward compatible)
python serve.py

# Specify project by path
python serve.py --project /path/to/my-project

# With custom port
python serve.py --project ./episodes/ep4 --port 9000
```

### Python Tools

```bash
# All tools accept --project
python tools/05b-render/render.py --project /path/to/project
python tools/04-assemble/generate_waveforms.py --project ./data
python tools/01-transcribe/transcribe.py --project ./my-project data/raw/*.mp4

# Backward compatible (uses data/project.json)
python tools/05b-render/render.py
```

### Project Initialization

```bash
python -m core.project init --name "Episode 4" --path ./projects/ep4

# Creates:
# ./projects/ep4/
# ├── project.json
# ├── raw/
# ├── transcripts/
# └── output/
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/project` | GET | Returns full project.json |
| `/api/project` | POST | Saves project.json |
| `/api/config` | GET | Returns resolved paths for HTML tools |
| `/api/render` | POST | Triggers render (uses project config) |

### `/api/config` Response

```json
{
  "project": {
    "name": "Life is Your Word",
    "season": 0,
    "episode": 3,
    "description": ""
  },
  "paths": {
    "combined_video": "/data/video_combined.mp4",
    "combined_transcript": "/data/transcript_combined.json",
    "output_dir": "/data/output",
    "raw_dir": "/data/raw",
    "transcripts_dir": "/data/transcripts"
  }
}
```

---

## Migration: v1 → v2

When loading a v1 `project.json` (no `schema_version`):

1. Detect missing `schema_version` → treat as v1
2. Wrap existing content with new schema
3. Add default paths
4. Add project metadata (name from directory or "Migrated Project")
5. Save migrated version (one-time upgrade)
6. Log: `"Migrated project.json v1 → v2"`

---

## Implementation Order

1. **`core/project_config.py`** - Core class with migration
2. **`core/io.py`** - Update to accept ProjectConfig
3. **`serve.py`** - CLI args + /api/config + global config
4. **HTML tools** - Update 4 files to use /api/config
5. **`tools/05b-render/render.py`** - Add --project flag
6. **`tools/04-assemble/generate_waveforms.py`** - Add --project flag
7. **`tools/01-transcribe/transcribe.py`** - Add --project flag
8. **`core/__main__.py`** - Init command

---

## Backward Compatibility

| Scenario | Behavior |
|----------|----------|
| `python serve.py` | Uses `data/project.json` (current behavior) |
| `python serve.py --project ./my-project` | Uses `./my-project/project.json` |
| V1 project.json | Auto-migrates on first load |
| HTML tools | Work with both old and new server |
