# Music Video Pipeline -- Design Specification

**Created**: May 6, 2026
**Status**: APPROVED -- Stages 1-3 implemented
**Location**: `music-video-pipeline/` (new top-level directory in content-tools)

---

## 1. Overview

A new pipeline for producing widescreen music/lyric videos from audio files + lyrics files, with AI image generation for visual design. Lives as a fully autonomous top-level directory, like the ambient-content-pipeline.

**Inputs**: Audio file (MP3/WAV/FLAC) + optional lyrics file (SRT/LRC/TXT with section markers) + optional stems (ZIP) + optional MIDI (ZIP)
**Output**: Rendered widescreen music video (1920x1080, MP4)

**Key principle**: All capabilities reimplemented natively within this pipeline. Code from asabaal-utils may be copied/adapted, but there is no import dependency on it.

---

## 2. Pipeline Stages

```
  STAGE 1          STAGE 2          STAGE 3          STAGE 4          STAGE 5          STAGE 6
  INGEST           ANALYZE          SYNC             STRUCTURE        DESIGN           RENDER

┌──────────┐   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Discover │──>│ Extract  │──> │ Align    │──> │ Define   │──> │ Generate │──> │ Compose  │
│ catalog  │   │ features │    │ lyrics   │    │ sections │    │ visuals  │    │ + encode │
│ all      │   │ from all │    │ to audio │    │          │    │ + style  │    │ final    │
│ inputs   │   │ inputs   │    │          │    │          │    │          │    │ video    │
└──────────┘   └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │              │               │               │               │               │
     ▼              ▼               ▼               ▼               ▼               ▼
 ingest.json    analysis.json   synced_lyrics  structure.json  visual_plan +   final_video.mp4
                stems_analysis  (word-level    (section map)   styled_lyrics
                waveforms.json   timestamps)
                lyrics_raw.json
                midi_notes.json
```

Stages 1-2 are CLI. Stage 3 is CLI initial pass + browser review. Stages 4-5 are browser tools. Stage 6 is CLI triggered from browser.

---

## 3. Input Tiers

The pipeline gracefully degrades based on available inputs:

| Input tier | Available inputs | Capabilities |
|---|---|---|
| **Basic** | Full mix audio only | Beat/onset detection, energy analysis |
| **Standard** | Full mix + lyrics | Above + lyrics parsing, section markers from TXT |
| **Enhanced** | Full mix + lyrics + stems | Above + per-stem energy profiles, vocal onset isolation |
| **Full** | Full mix + lyrics + stems + MIDI | Above + exact tempo, per-instrument note maps, syllable timing |

### Degradation pathways

| Stage | Basic (audio only) | Standard (+lyrics) | Enhanced (+stems) | Full (+MIDI) |
|---|---|---|---|---|
| Ingest | Detect audio | + detect lyrics | + detect/extract stems | + detect/extract MIDI |
| Analyze | Full mix only | + lyrics parse (section markers) | + per-stem analysis | + MIDI tempo, note maps |
| Sync | Skip (instrumental) | Onset heuristic | Vocal stem onsets | MIDI note alignment |
| Structure | Audio-based detection | + lyric section hints | + energy-based detection | + section markers from lyrics |
| Design | Generic profiles | Generic profiles | Per-instrument reactivity | Per-instrument reactivity |
| Render | Same engine, uses whatever data is available |

---

## 4. Directory Structure

```
music-video-pipeline/
├── src/
│   ├── audio/                  # Audio analysis (librosa) + ingest + MIDI
│   │   ├── __init__.py
│   │   ├── analyzer.py         # Beat detection, onset, RMS, spectral, per-stem analysis
│   │   ├── features.py         # AudioFeatures, BeatInfo, StemFeatures dataclasses
│   │   ├── ingest.py           # Input discovery, ZIP extraction, tier detection
│   │   └── midi.py             # MIDI analysis (tempo, notes) via pretty_midi
│   │
│   ├── lyrics/                 # Lyrics parsing + synchronization
│   │   ├── __init__.py
│   │   ├── parser.py           # SRT/LRC/TXT → LyricLine/LyricWord/LyricSection
│   │   ├── synchronizer.py     # Align lyrics to audio beats/onsets
│   │   └── processor.py        # Facade combining parser + synchronizer
│   │
│   ├── sections/               # Song structure management
│   │   ├── __init__.py
│   │   ├── types.py            # 18 section types enum (verse, chorus, bridge, etc.)
│   │   ├── manager.py          # Section detection, per-section visual profiles
│   │   └── loader.py           # Parse structure files (JSON/YAML/text)
│   │
│   ├── visual/                 # Visual design + image generation
│   │   ├── __init__.py
│   │   ├── image_gen.py        # SD3 subprocess bridge (from ACP pattern)
│   │   ├── backgrounds.py      # Background source management (image, gradient, procedural)
│   │   └── style_profiles.py   # Per-section visual defaults
│   │
│   ├── render/                 # Rendering engine
│   │   ├── __init__.py
│   │   ├── compositor.py       # Frame-by-frame layer composition
│   │   ├── text_renderer.py    # Lyric text rendering with effects
│   │   ├── effects.py          # Motion effects, audio-reactive modulation
│   │   ├── animations.py       # 14 animation types, 7 easing functions
│   │   ├── encoder.py          # FFmpeg streaming encoder + audio mux
│   │   └── fonts.py            # Font management, bespoke styles
│   │
│   ├── pipeline/               # Pipeline orchestration
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # Stage sequencing, plan persistence
│   │   └── models.py           # Project state data models
│   │
│   └── cli/                    # CLI entry points
│       ├── __init__.py
│       └── commands.py         # Click CLI with ingest/analyze/sync/render commands
│
├── scripts/
│   └── run_sd3_pipe.py         # SD3 image generation subprocess (from ACP)
│
├── templates/                  # Built-in visual templates
│   ├── default.json
│   ├── elegant.json
│   ├── modern.json
│   ├── energetic.json
│   ├── dynamic.json
│   └── extreme.json
│
├── tools/                      # Browser-based interactive tools
│   ├── 03-sync/               # Lyrics sync editor (index.html)
│   ├── 04-structure/           # Song structure editor (index.html)
│   ├── 05-visual-design/       # Visual design + lyric styling (index.html)
│   └── shared/                 # Shared JS/CSS for browser tools
│       ├── audio-player.js     # Audio playback component
│       ├── waveform.js         # Waveform visualization
│       └── timeline.js         # Shared timeline component
│
├── tests/
│   ├── conftest.py             # Shared fixtures (audio, lyrics, data dirs)
│   ├── test_models.py          # Models, paths, stages
│   ├── test_features.py        # AudioFeatures, BeatInfo, StemFeatures
│   ├── test_analyzer.py        # AudioAnalyzer, per-stem analysis
│   ├── test_ingest.py          # Input discovery, ZIP extraction, tier detection
│   ├── test_midi.py            # MIDI analysis
│   ├── test_parser.py          # Lyrics parsing (SRT/LRC/TXT with sections)
│   ├── test_synchronizer.py    # Auto-sync algorithm (beat snapping, onset alignment)
│   ├── test_serve.py           # HTTP server API endpoints
│   ├── test_cli.py             # CLI commands (init, analyze, sync, serve, info)
│   └── test_coverage_gaps.py   # Edge cases and integration scenarios
│
├── data/                       # Dev data (canonical example)
│   └── i-never-asked-to-be-queer/
│
├── mvp.py                      # CLI entry point
├── serve.py                    # HTTP server for browser tools
├── pyproject.toml
├── requirements.txt
├── README.md
├── DESIGN.md                   # This file
├── STAGE1_PLAN.md              # Stage 1 (Ingest) + Stage 2 (Analyze) plan
└── STAGE3_PLAN.md              # Stage 3 (Sync) plan
```

---

## 5. Stage Specifications

### Stage 1: Ingest

**Type**: CLI (`mvp init`)
**Input**: Data directory or explicit file paths
**Output**: `data/ingest.json`

```bash
# From a Suno output directory (auto-discovery):
mvp init --name "Song" --data-dir ./song-data

# From explicit files:
mvp init --name "Song" --audio song.mp3 --lyrics lyrics.srt
```

**Steps**:
1. Scan data directory for available inputs:
   - Full mix audio (WAV preferred, falls back to MP3/FLAC)
   - Lyrics file (SRT/LRC/TXT)
   - Stem archives (ZIPs with "Stems" in name)
   - MIDI archives (ZIPs with "MIDI" in name)
2. Extract ZIP archives to `data/cache/stems/` and `data/cache/midi/`
3. Detect tempo-locked stems (filenames with "(NNNBPM)")
4. Determine input tier (basic/standard/enhanced/full)
5. Write `ingest.json` with catalog of all discovered inputs

**Discovery logic**:
- Audio: prefers WAV over other formats
- Stems: prefers tempo-locked ZIPs over regular stem ZIPs
- MIDI: uses first MIDI ZIP found
- Lyrics: uses first lyrics file found

**ingest.json schema**:
```json
{
  "tier": "full",
  "audio_path": "/path/to/song.wav",
  "lyrics_path": "/path/to/lyrics.txt",
  "stems": [
    {"name": "Lead Vocals", "stem_type": "lead_vocals", "path": "/path/to/0 Lead Vocals.wav", "format": "wav"},
    {"name": "Drums", "stem_type": "drums", "path": "/path/to/1 Drums.wav", "format": "wav"}
  ],
  "midi_files": [
    {"name": "Song (Vocals).mid", "path": "/path/to/Song (Vocals).mid", "instrument": "Vocals", "note_count": 0, "duration": 0}
  ],
  "has_tempo_locked_stems": true
}
```

---

### Stage 2: Analyze

**Type**: CLI (`mvp analyze`)
**Input**: `data/ingest.json` + all discovered files
**Output**: `data/analysis.json`, `data/waveforms.json`, `data/lyrics_raw.json`

```bash
mvp analyze                    # analyze based on ingest tier
mvp analyze --verbose          # detailed output
```

**Steps**:
1. Load ingest.json to determine available inputs
2. Analyze full mix audio:
   - Beat detection: `librosa.beat.beat_track()` → tempo (BPM), beat times
   - Onset detection: `librosa.onset.onset_detect()` → onset times
   - RMS energy: `librosa.feature.rms()` → normalized 0-1 over time
   - Spectral centroids: `librosa.feature.spectral_centroid()` → brightness indicator
   - Zero crossing rate: `librosa.feature.zero_crossing_rate()` → percussive indicator
3. If MIDI available: extract exact tempo via `pretty_midi` (replaces librosa estimate)
4. If stems available: run per-stem analysis (energy profile, onset count per instrument)
5. If lyrics available: parse with section marker support
6. Generate waveform data (100 peaks/sec) for browser visualization

**Lyrics section markers** (TXT format):
Lines like `[Verse 2, double time, female]` are parsed as section boundaries:
- `section_type`: verse, chorus, intro, outro, etc.
- `index`: numeric suffix (Verse 2 → index=2)
- `tags`: comma-separated modifiers (double_time, female, BIG, etc.)
- Section markers are excluded from word counts and line timing
- Each lyric line gets a `section` reference pointing to its parent section

**analysis.json schema**:
```json
{
  "duration": 156.12,
  "sample_rate": 48000,
  "bpm": 103.8,
  "midi_tempo": 103.8,
  "beat_confidence": 0.34,
  "beat_times": [0.46, 0.94, ...],
  "onset_times": [0.01, 0.12, ...],
  "rms_energy": [0.0, ...],
  "spectral_centroids": [0.0, ...],
  "zero_crossing_rate": [0.0, ...],
  "frame_rate": 93.8,
  "stem_features": [
    {"stem_type": "lead_vocals", "name": "Lead Vocals", "energy": 0.297, "onset_count": 559},
    {"stem_type": "drums", "name": "Drums", "energy": 0.070, "onset_count": 401}
  ]
}
```

---

### Stage 3: Lyrics Synchronization

**Type**: CLI initial pass (`mvp sync`) + browser review (`mvp serve`)
**Input**: `data/analysis.json` + `data/lyrics_raw.json`
**Output**: `data/lyrics_synced.json`

**Degradation**:
- With MIDI vocal notes: align words to exact syllable timing
- With vocal stem onsets: use isolated vocal onsets for cleaner word boundaries
- Without either: full-mix onset heuristic alignment

**Auto-sync algorithm** (`src/lyrics/synchronizer.py`):
1. Snap line start/end to nearest beat (within 200ms tolerance)
2. Find onsets within each line's time range
3. If onsets >= words: assign each word to an onset
4. If onsets < words: interpolate between onsets
5. If no onsets: even distribution across line duration
6. Compute alignment confidence per line (ratio of onset-locked words)

**Browser tool** (`tools/03-sync/index.html`):
- Waveform display with beat markers and seek-by-click
- Lyrics timeline with section headers and confidence indicators
- Word detail panel showing source (midi/vocal_onset/onset/interpolated)
- Auto-sync button triggers `/api/auto-sync` endpoint
- Save button persists to `/api/lyrics-synced`

---

### Stage 4: Structure Editor

**Type**: Browser tool (served via `serve.py`)
**Input**: `data/analysis.json` + `data/lyrics_synced.json` + `data/ingest.json`
**Output**: `data/structure.json`

**Degradation**:
- With section markers from lyrics: sections pre-populated from `[Verse]`/`[Chorus]` markers
- Without: audio-based section detection (energy/spectral changes)

---

### Stage 5: Visual Design + Lyric Styling

**Type**: Browser tool (served via `serve.py`)
**Input**: All previous stage outputs
**Output**: `data/visual_plan.json` + generated images in `data/assets/`

Per-instrument energy profiles (from stem analysis) enable per-instrument visual reactivity:
- Bass → background pulse
- Vocals → text glow
- Drums → beat flash
- Synth → color shift

---

### Stage 6: Render

**Type**: CLI (`mvp render`)
**Input**: All project data
**Output**: `data/output/final_video.mp4`

Same render engine regardless of input tier. Uses whatever data is available from prior stages.

---

## 6. Data Models

### Core Models (`src/pipeline/models.py`)

```python
class InputTier(Enum):
    BASIC = "basic"        # audio only
    STANDARD = "standard"  # audio + lyrics
    ENHANCED = "enhanced"  # audio + lyrics + stems
    FULL = "full"          # audio + lyrics + stems + MIDI

@dataclass
class StemInfo:
    name: str              # "Lead Vocals"
    stem_type: str         # "lead_vocals"
    path: str              # path to extracted stem file
    format: str            # "wav" or "mp3"

@dataclass
class MidiFileInfo:
    name: str
    path: str
    instrument: str
    note_count: int
    duration: float

@dataclass
class IngestResult:
    tier: str
    audio_path: Optional[str]
    lyrics_path: Optional[str]
    stems: list[StemInfo]
    midi_files: list[MidiFileInfo]
    has_tempo_locked_stems: bool

@dataclass
class ProjectPaths:
    audio: Optional[str]
    lyrics: Optional[str]
    data_dir: Optional[str]   # for --data-dir mode

@dataclass
class AudioInfo:
    duration: float
    bpm: float
    sample_rate: int
    beat_count: int
    onset_count: int
    midi_bpm: Optional[float]  # exact tempo from MIDI

@dataclass
class LyricsInfo:
    total_lines: int
    total_words: int
    format: str
    first_line_time: Optional[float]
    last_line_time: Optional[float]
    has_sections: bool        # True if TXT had [Section] markers
    section_count: int

@dataclass
class StageStatus:
    ingest: str = "pending"
    analyze: str = "pending"
    sync: str = "pending"
    structure: str = "pending"
    design: str = "pending"
    render: str = "pending"
```

### Audio Models (`src/audio/features.py`)

```python
@dataclass
class StemFeatures:
    stem_type: str
    name: str
    energy: float        # normalized 0-1
    onset_count: int

@dataclass
class AudioFeatures:
    duration: float
    sample_rate: int
    beats: BeatInfo
    onset_times: np.ndarray
    rms_energy: np.ndarray
    spectral_centroids: np.ndarray
    zero_crossing_rate: np.ndarray
    stem_features: Optional[List[StemFeatures]]
    midi_tempo: Optional[float]
```

### Lyrics Models (`src/lyrics/parser.py`)

```python
@dataclass
class LyricSection:
    raw_marker: str        # "Verse 2, double time, female"
    section_type: str      # "verse"
    index: Optional[int]   # 2
    tags: list[str]        # ["double_time", "female"]

@dataclass
class LyricLine:
    index: int
    text: str
    start: float
    end: float
    words: list[LyricWord]
    section: Optional[LyricSection]  # parent section reference
```

---

## 7. CLI Commands

```bash
# Project management
mvp init --name "Song" --data-dir ./suno-output       # auto-discover all inputs
mvp init --name "Song" --audio song.mp3               # explicit audio only
mvp init --name "Song" --audio song.mp3 --lyrics lyrics.srt

# Pipeline stages
mvp analyze                    # Stage 2: Audio analysis (based on ingest tier)
mvp sync                       # Stage 3: Lyrics synchronization (auto-align + save)
mvp render                     # Stage 6: Final render

# Server
mvp serve                      # Start HTTP server for browser tools (Stages 3-5)

# Utilities
mvp info                       # Show project info, input tier, pipeline status
```

---

## 8. Data Directory Layout

```
data/
├── mvp_project.json          # Master project state
├── ingest.json               # Stage 1 output: input catalog
├── raw/                      # User inputs (copied from explicit paths)
│   ├── song.mp3
│   └── lyrics.srt
├── cache/                    # Stage 1 output: extracted archives
│   ├── stems/                # Extracted from stem ZIPs
│   │   ├── 0 Lead Vocals.wav
│   │   ├── 1 Drums.wav
│   │   └── ...
│   └── midi/                 # Extracted from MIDI ZIPs
│       ├── Song (Vocals).mid
│       └── ...
├── analysis.json             # Stage 2 output: audio features
├── waveforms.json            # Stage 2 output: waveform peaks
├── lyrics_raw.json           # Stage 2 output: parsed lyrics with sections
├── lyrics_synced.json        # Stage 3 output: synced lyrics
├── structure.json            # Stage 4 output: section map
├── visual_plan.json          # Stage 5 output: visual design
├── assets/                   # Stage 5 output: generated images
│   ├── sec_0_bg.png
│   └── sec_2_bg.png
└── output/                   # Stage 6 output
    └── final_video.mp4
```

---

## 9. Dependencies

```
# Core
librosa>=0.10.0          # Audio analysis
numpy>=1.24.0            # Array operations
Pillow>=10.0.0           # Image/text rendering
opencv-python>=4.8.0     # Video processing, text rendering
pretty_midi>=0.2.9       # MIDI analysis (optional, graceful skip)

# Encoding
ffmpeg-python>=0.2.0     # FFmpeg Python wrapper (or subprocess)

# CLI
click>=8.0.0             # CLI framework

# Optional
requests>=2.31.0         # For Ollama API calls (auto-prompt generation)
```

---

## 10. Implementation Phases

### Phase 1: Foundation (ingest + analysis) — DONE
- [x] Project scaffolding: directory structure, pyproject.toml, requirements.txt
- [x] `src/pipeline/models.py` — all data models including InputTier, StemInfo, MidiFileInfo
- [x] `src/audio/ingest.py` — input discovery, ZIP extraction, tier detection
- [x] `src/audio/analyzer.py` — full mix analysis + per-stem analysis
- [x] `src/audio/features.py` — AudioFeatures, BeatInfo, StemFeatures
- [x] `src/audio/midi.py` — MIDI tempo and note extraction
- [x] `src/lyrics/parser.py` — SRT/LRC/TXT with section marker support
- [x] `src/cli/commands.py` — init (with --data-dir), analyze, info commands
- [x] 265 tests, 100% coverage

### Phase 2: Sync — DONE
- [x] `src/lyrics/synchronizer.py` — beat/onset/MIDI alignment (3-tier degradation)
- [x] `serve.py` — HTTP server with API endpoints (auto-sync, save, static files)
- [x] `tools/03-sync/index.html` — browser sync editor
- [x] `src/cli/commands.py` — `sync` command (CLI initial pass), `serve` command
- [x] 345 tests, 100% coverage on new code

### Phase 3: Structure
- [ ] `src/lyrics/processor.py` — lyrics facade
- [ ] `src/sections/types.py` — section type enum + visual profiles
- [ ] `src/sections/manager.py` — section management
- [ ] `src/sections/loader.py` — structure file parser
- [ ] `tools/04-structure/index.html` — structure editor browser tool

### Phase 3: Visual Design
- [ ] `scripts/run_sd3_pipe.py` — SD3 subprocess bridge
- [ ] `src/visual/image_gen.py` — image generation wrapper
- [ ] `src/visual/backgrounds.py` — background source management
- [ ] `src/visual/style_profiles.py` — per-section defaults
- [ ] `src/render/animations.py` — animation types + easing
- [ ] `src/render/fonts.py` — font management
- [ ] `tools/05-visual-design/index.html` — visual design browser tool

### Phase 4: Render Engine
- [ ] `src/render/effects.py` — motion effects library
- [ ] `src/render/text_renderer.py` — lyric rendering with effects
- [ ] `src/render/compositor.py` — frame composition pipeline
- [ ] `src/render/encoder.py` — ffmpeg streaming encoder
- [ ] `src/cli/commands.py` — `render` command

### Phase 5: Polish
- [ ] `templates/` — 6 built-in templates
- [ ] Live preview in Stage 5
- [ ] Hardware acceleration auto-detection
- [ ] Export options (resolution, quality, format)
- [ ] README.md
