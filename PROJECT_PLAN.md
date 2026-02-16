# Content Tools - Video Editing Pipeline

**Created**: February 13, 2026
**Purpose**: Browser-based tools for transcript-based video editing

---

## Overview

This project provides a complete video editing pipeline that works with transcribed content. Instead of traditional NLE timeline editing, you work with text - editing transcripts, grouping clips, selecting takes - then export a final assembly plan.

---

## Pipeline

```
┌───────────────────────────────────────────────────────────────────────────┐
│                      CONTENT TOOLS PIPELINE                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  STEP 1           STEP 2           STEP 3           STEP 4               │
│  INGEST           REVIEW+ASSIGN    SELECT           ASSEMBLE              │
│                                                                           │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐          │
│  │ raw/    │      │ Watch   │      │ Compare │      │ Order   │          │
│  │ ├video1 │─────►│ + Group │─────►│ Takes   │─────►│ + Export│──► EDL  │
│  │ ├video2 │      │ into    │      │ Pick    │      │ Timeline│          │
│  │ └video3 │      │ Clips   │      │ Best    │      │         │          │
│  └─────────┘      └─────────┘      └─────────┘      └─────────┘          │
│       │                │                │                │               │
│       ▼                ▼                ▼                ▼               │
│  video files     project.json    selections.json    assembly.edl        │
│                  (with clips)    (best take per                       │
│                                   clip)                                │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
content-tools/
├── tools/                          # One tool per workflow step
│   ├── 01-transcribe/              # Generate transcripts from video (Whisper)
│   ├── 02-review/                  # Watch + Sync + Group segments into clips
│   ├── 03-select/                  # Choose best takes per clip
│   └── 04-assemble/                # Order clips, export final timeline
│
├── core/                           # Shared Python modules
│   ├── models.py                   # Data classes (Segment, Clip, Take, etc.)
│   ├── io.py                       # Load/save JSON
│   └── utils.py                    # Time formatting, etc.
│
├── data/                           # Working directory
│   ├── raw/                        # Input video files
│   │   ├── 20251008_150255.mp4
│   │   ├── 20251008_150325.mp4
│   │   └── ...
│   ├── transcripts/                # Generated transcripts (one per video)
│   ├── project.json                # Current project state (clips, selections)
│   └── output/                     # Final exports (EDL, etc.)
│
├── _archived/                      # Previous implementation (for reference)
│
└── PROJECT_PLAN.md                 # This file
```

---

## Tool Specifications

### Tool 01: TRANSCRIBE
**Type**: Python CLI
**Purpose**: Generate transcript JSON from video files using Whisper

**Usage**:
```bash
python tools/01-transcribe/transcribe.py data/raw/*.mp4
```

**Output**: `data/transcripts/{video_name}.json`

**Transcript Format** (Whisper-compatible):
```json
{
  "video_id": "20251008_150255",
  "duration": 45.2,
  "segments": [
    {
      "id": "seg_0",
      "text": "Where there was not God's book...",
      "start": 1.68,
      "end": 6.7,
      "words": [
        {"text": "Where", "start": 1.68, "end": 2.285},
        {"text": "there", "start": 2.325, "end": 2.507}
      ]
    }
  ]
}
```

**Status**: ✅ DONE

---

### Tool 02: REVIEW & ASSIGN
**Type**: Single HTML file
**Purpose**: Watch video with synced transcript AND organize segments into clips

**Features:**
- Video player with transcript sidebar
- Word-level highlighting during playback
- Click segment → video jumps to timestamp
- **Clips panel** - manage clip groups (create, rename, delete)
- **Assign segments** - add segments to clips
- **Edit mode** - edit text, split/merge/delete segments
- **Auto-assign** - create clips for all unassigned segments
- **Persistent state** - saves to project.json

**Input**: 
- `data/video_combined.mp4`
- `data/transcript_combined.json`

**Output**: 
- `data/project.json` with clip assignments and edited transcript

**Status**: ✅ DONE

---

### Tool 03: SELECT
**Type**: Single HTML file  
**Purpose**: Choose the best take for each clip

**Features:**
- **Clips list** - organized by multi-take (needs selection) vs single-take
- **Video grid** - side-by-side comparison of all takes
- **Transcript comparison** - text view of each take
- **Select take** - mark the best version per clip
- **Visual indicators** - green checkmark for selected clips

**Output**: Updates `project.json` with `selected_segment` per clip
```json
{
  "clips": [
    {
      "id": "clip_1",
      "selected_segment": {"video_id": "20251008_150325", "segment_id": "seg_0"}
    }
  ]
}
```

**Status**: ✅ DONE

---

### Tool 04: ASSEMBLE
**Type**: Single HTML file + Python waveform generator
**Purpose**: Order selected clips into final timeline, trim boundaries, split clips

**Features:**
- **Clip pool** (left sidebar) - clips not yet in timeline, click [+] to add
- **Timeline view** - horizontal strip of draggable clip cards
- **Drag to reorder** - reposition clips in timeline
- **Add/remove from timeline** - move clips between pool and timeline
- **Toggle on/off** - include/exclude clips from final output
- **Video preview** - single player for selected clip or full timeline
- **Waveform display** - visual audio waveform for trim editing
- **Trim start/end** - drag handles on waveform, video updates on release
- **Split clips** - at playhead position, creates two independent clips
- **Preview all** - seamless playback of all enabled clips in order
- **Export EDL** - generate EDL file for kdenlive/blender
- **Manual save** - explicit save button

**Layout:**
```
┌──────────┬────────────────────────────────────────────────────┐
│          │                                                    │
│  CLIP    │               MAIN PANEL                           │
│  POOL    │  ┌──────────────────────────────────────────────┐  │
│          │  │              VIDEO PREVIEW                    │  │
│  (220px) │  └──────────────────────────────────────────────┘  │
│          │                                                    │
│  ┌─────┐ │  TIMELINE (draggable)                              │
│  │Clip │ │  ┌────┐ ┌────┐ ┌────┐ ┌────┐                     │
│  │ [+] │ │  │ 1  │ │ 2  │ │ 3  │ │ 4  │                     │
│  └─────┘ │  └────┘ └────┘ └────┘ └────┘                     │
│          │                                                    │
│  ┌─────┐ │  SELECTED CLIP EDITOR                              │
│  │Clip │ │  ┌──────────────────────────────────────────────┐  │
│  │ [+] │ │  │  WAVEFORM with trim handles                  │  │
│  └─────┘ │  │  [◄─────────────────────────────────────►]   │  │
│          │  └──────────────────────────────────────────────┘  │
│          │  "Transcript text..." [Split] [Toggle]             │
└──────────┴────────────────────────────────────────────────────┘
```

**Input:** 
- `data/project.json` (with clips and selected_segment per clip)
- `data/waveforms.json` (pre-generated waveform data)
- `data/video_combined.mp4`

**Output:** 
- Updated `data/project.json` with timeline data
- `data/output/assembly.edl`

**Pre-processing Required:**
```bash
python tools/04-assemble/generate_waveforms.py
```
Generates `data/waveforms.json` with audio peak data for each segment.

**Data Model Additions:**
```json
{
  "clips": [
    {
      "id": "clip_001",
      "name": "Introduction",
      "segments": [...],
      "selected_segment": {...},
      "include": true,
      
      "in_timeline": true,
      "timeline_position": 0,
      "trim_start": null,
      "trim_end": null,
      "enabled": true,
      "split_parent_id": null
    }
  ]
}
```

**Status**: ✅ DONE

---

## Data Model

### project.json (Master State)

```json
{
  "version": 1,
  "videos": [
    {
      "id": "20251008_150255",
      "path": "data/raw/20251008_150255.mp4",
      "transcript_path": "data/transcripts/20251008_150255.json"
    }
  ],
  "clips": [
    {
      "id": "clip_001",
      "name": "Introduction",
      "segments": [
        {"video_id": "20251008_150255", "segment_id": "seg_0"},
        {"video_id": "20251008_150325", "segment_id": "seg_0"}
      ],
      "selected_segment": {"video_id": "20251008_150325", "segment_id": "seg_0"},
      "include": true
    }
  ],
  "timeline_order": ["clip_001", "clip_002", "clip_003"]
}
```

---

## Test Data

Current test project: **Episode 3 - "Life is Your Word"**

| File | Size | Notes |
|------|------|-------|
| `data/raw/20251008_150255.mp4` | 45MB | Take 1 |
| `data/raw/20251008_150325.mp4` | 97MB | Take 2 |
| `data/raw/20251008_150420.mp4` | 94MB | Take 3 |
| `data/raw/20251008_150513.mp4` | 100MB | Take 4 |
| `data/raw/20251008_150622.mp4` | 52MB | Take 5 |
| `data/raw/20251008_150654.mp4` | 13MB | Take 6 |
| `data/video_combined.mp4` | 400MB | Pre-combined (for testing) |
| `data/transcript_combined.json` | 45KB | Existing transcript (Whisper format) |

---

## Build Order

| Step | What | Dependencies | Status |
|------|------|--------------|--------|
| 1 | `core/models.py` | None | ✅ DONE |
| 2 | `core/io.py` | models | ✅ DONE |
| 3 | `tools/01-transcribe/` | core | ✅ DONE |
| 4 | `tools/02-review/` | core, transcribe | ✅ DONE |
| 5 | `tools/03-select/` | review+assign | ✅ DONE |
| 6 | `tools/04-assemble/` | select | ✅ DONE |

---

## Development Principles

1. **One tool = one job** - Each tool does one thing well
2. **JSON as interface** - Tools communicate via JSON files
3. **Browser-based UI** - No server required, just open HTML
4. **Incremental enhancement** - Each tool builds on previous
5. **Test early, test often** - Verify each tool works before moving on

---

## Next Steps

1. ~~Build `core/models.py` - Define data classes~~ ✅
2. ~~Build `core/io.py` - Load/save functions~~ ✅
3. ~~Build `tools/01-transcribe/` - Whisper wrapper~~ ✅
4. ~~Build `tools/02-review/` - Video + transcript + clip assignment~~ ✅
5. ~~Build `tools/03-select/` - Take comparison and selection~~ ✅
6. ~~Build `tools/04-assemble/` - Timeline + EDL export~~ ✅

---

## Archive Notes

Previous implementations moved to `_archived/`:
- `_archived/implementation/` - Python Flask app + transcript_core module
- `_archived/reference/` - HTML tools (editors, reports, timeline components)
- `_archived/WORKFLOW_AUDIT.md` - Previous analysis

Key salvageable code:
- `transcript_core/models.py` - Data models (can be adapted)
- `transcript_core/timing.py` - Word redistribution logic
- Test coverage patterns from `implementation/tests/`
