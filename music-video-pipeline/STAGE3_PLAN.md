# Stage 3 (Sync) Implementation Plan

**Status**: COMPLETE (backend), UI REDESIGN IN PROGRESS
**Type**: Browser tool (auto-sync via server API, human review/adjust in browser)
**CLI**: `mvp sync` runs initial auto-pass, `mvp serve` opens browser editor

---

## Overview

Sync aligns lyrics to audio timing. It auto-attempts word-level alignment, then presents the results in a browser editor where the human reviews and adjusts. This is the first human-in-the-loop stage.

---

## Components

### 1. `src/lyrics/synchronizer.py` — Auto-sync algorithm

Pure Python module. Takes lyrics_raw + analysis, produces synced lyrics with word-level timestamps.

**Algorithm (3 tiers)**:
- **MIDI available**: Map vocal MIDI note starts to word boundaries
- **Stems available**: Use vocal stem onsets for cleaner word detection
- **Full mix only**: Use full-mix onsets (heuristic)

**Core logic** (adapted from asabaal-utils):
1. Snap line start/end to nearest beat (within 200ms)
2. Find onsets within each line's time range
3. If more onsets than words: assign words to first N onsets
4. If fewer onsets than words: use onsets as anchors, interpolate between
5. If no onsets: even distribution across line duration

**Data structures**:
```python
@dataclass
class SyncedLine:
    text: str
    start: float
    end: float
    words: list[SyncedWord]
    section: Optional[LyricSection]
    alignment_confidence: float  # 0.0-1.0

@dataclass
class SyncedWord:
    text: str
    start: float
    end: float
    source: str  # "midi", "vocal_onset", "onset", "interpolated"

@dataclass
class SyncResult:
    lines: list[SyncedLine]
    source: str  # "midi", "vocal_stem", "full_mix"
    avg_confidence: float
```

### 2. `serve.py` — HTTP server

Adapted from `content-tools/serve.py` pattern (stdlib http.server, range requests).

**API endpoints**:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/project` | Return mvp_project.json |
| GET | `/api/analysis` | Return analysis.json |
| GET | `/api/waveforms` | Return waveforms.json |
| GET | `/api/lyrics-raw` | Return lyrics_raw.json |
| GET | `/api/lyrics-synced` | Return lyrics_synced.json (if exists) |
| GET | `/api/ingest` | Return ingest.json |
| POST | `/api/auto-sync` | Run auto-sync, return results |
| POST | `/api/lyrics-synced` | Save synced lyrics |

**Static files**: `/tools/*` → tools directory, `/data/*` → project data directory

**Audio range requests**: Full HTTP Range support for seeking in browser

### 3. `tools/03-sync/index.html` — Browser sync editor

Single self-contained HTML file matching content-tools UI patterns (no frameworks, no dependencies).

**Layout** (matching content-tools Tool 04 "Assemble"):
```
┌───────────────────────────────────────────────────────────────┐
│ 03 - Sync Lyrics                     [Auto-Sync] [Save]      │
├─────────────────┬─────────────────────────────────────────────┤
│                 │  Waveform + beat markers                    │
│  Transcript     │  ─────────────────────────────────────     │
│  (karaoke       │  Word Layer (draggable word boxes)          │
│   highlight)    │  ┌───┐┌──────┐┌────┐┌──────┐              │
│                 │  │I  ││never ││ask ││ed to  │              │
│  [Verse]        │  └───┘└──────┘└────┘└──────┘              │
│  I never asked  │  ─────────────────────────────────────     │
│  to be queer    │  Time axis + seek bar                       │
│  I was such a...├─────────────────────────────────────────────┤
│  ...            │  Detail panel: selected line word timing    │
│                 │  (editable start/end fields per word)       │
├─────────────────┴─────────────────────────────────────────────┤
│ [◀ 5s] [▶/⏸] [▶ 5s]  0:42 / 2:36  [Shift +0.5] [−0.5]     │
└───────────────────────────────────────────────────────────────┘
```

**Interactions** (matching content-tools Tool 04 pattern):

1. **Karaoke word highlighting**: During playback, active word highlighted cyan. Transcript auto-scrolls. Words within active line highlight one-by-one as playback progresses. Matches Tool 02/04 `.active` class pattern.

2. **Draggable word boxes on word layer**: Words positioned absolutely over waveform strip. Three drag modes (from Tool 04):
   - Drag body: move word start+end together, maintain duration
   - Drag left edge: adjust word start, shift previous word's end to fill gap
   - Drag right edge: adjust word end, shift next word's start
   - Min 0.15s word duration enforced, clamped to line bounds

3. **Waveform + word layer sync**: Word layer positioned directly below waveform, scroll together. Beat markers drawn on waveform. Playhead line on both layers.

4. **Click-to-seek**: Click on waveform or word-layer to jump audio position.

5. **Transcript panel (left)**: All lines listed with section headers. Click line to seek + select. Active line highlighted during playback. Words rendered as inline `<span>` elements with per-word highlighting.

6. **Editable timing fields**: Selected line shows in detail panel with per-word start/end number inputs. Changing a field updates the word box position on the word layer.

7. **Keyboard shortcuts**: Space: play/pause, Left/Right: ±5s, Escape: deselect

8. **Unsaved changes guard**: `beforeunload` warning when changes pending.

9. **Source badges**: Per-word source indicator (midi/onset/vocal_onset/interpolated) shown as colored badges in both word boxes and detail table.

10. **Confidence indicators**: Per-line confidence color bar: green (>0.8), yellow (0.5-0.8), red (<0.5).

**Color scheme**: Matches content-tools dark theme:
- `#0f0f1a` — darkest (waveform bg)
- `#1a1a2e` — body background
- `#16213e` — panels, headers
- `#2a2a4a` — borders, inputs
- `#4cc9f0` — primary accent (cyan), active states
- `#48bb78` — success/save (green)
- `#f6ad55` — warning/unsaved (orange)
- `#f66` — danger (red)

### 4. CLI updates

- `mvp sync` — runs auto-sync algorithm, saves initial lyrics_synced.json
- `mvp serve` — starts HTTP server, prints URL to sync editor

---

## Implementation Order

1. `src/lyrics/synchronizer.py` — pure Python, testable
2. Tests for synchronizer
3. `serve.py` — HTTP server
4. Tests for serve.py API endpoints
5. `tools/03-sync/index.html` — browser editor
6. CLI command updates (`mvp sync`, `mvp serve`)
7. Full integration test

---

## Test Plan

| Test file | What it covers |
|-----------|---------------|
| `tests/test_synchronizer.py` | Auto-sync algorithm: beat snapping, onset alignment, word interpolation, confidence scoring, all 3 tiers |
| `tests/test_serve.py` | HTTP server: API endpoints, static file serving, range requests, POST save |

---

## Design Decisions

1. **SRT/LRC already have timing**: Sync editor still shows them — user may want to adjust
2. **Section markers**: Sync editor shows sections from lyrics but doesn't create Stage 4 sections — that's Structure's job
3. **Save behavior**: Explicit Save button (matches repo convention)
4. **Tap-sync**: Deferred to future iteration — initial version has drag-to-adjust only
5. **Auto-sync is non-destructive**: Always saves to `lyrics_synced.json`, never overwrites `lyrics_raw.json`
