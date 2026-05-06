# Stage 3 (Sync) Implementation Plan

**Status**: IMPLEMENTING
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

Single self-contained HTML file following repo conventions.

**Layout**:
```
┌──────────────────────────────────────────────────────────┐
│ 03 - Sync Lyrics                            [Save]      │
├──────────────────────────────────────────────────────────┤
│ Waveform + beat markers (click to seek)                  │
│ [▶ Play] [⏸ Pause]  0:42 / 2:36                        │
├────────────────────┬─────────────────────────────────────┤
│ Lyrics Timeline    │ Word Detail                         │
│                    │                                     │
│ [Verse]            │ Line: "I never asked to be queer"   │
│ ► never asked...   │                                     │
│   0.00 ──── 3.00   │ never  [0.00]──[0.75]  (onset)    │
│ to be queer        │ asked  [0.75]──[1.50]  (onset)    │
│   3.00 ──── 6.00   │ to     [1.50]──[2.25]  (interp)   │
│                    │ be     [2.25]──[2.62]  (interp)   │
│ [Verse]            │ queer  [2.62]──[3.00]  (onset)    │
│ I was such a...   │                                     │
├────────────────────┴─────────────────────────────────────┤
│ [Auto-Sync]                                              │
└──────────────────────────────────────────────────────────┘
```

**Interactions**:
- Click waveform to seek audio position
- Audio playback with current line highlighted, words progressing in real-time
- Click word to jump to its start time
- Drag word boundary handles to adjust start/end
- "Auto-Sync" button: POST to `/api/auto-sync`, reloads with results
- Sections from lyrics shown as group headers
- Confidence color-coding: green (>0.8), yellow (0.5-0.8), red (<0.5)

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
