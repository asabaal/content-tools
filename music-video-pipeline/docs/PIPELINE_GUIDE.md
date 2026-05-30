# Music Video Pipeline — Technical Guide

**Version**: June 2026
**Status**: Production (AI Psalm 9 rendered end-to-end)
**Location**: `music-video-pipeline/` in content-tools monorepo

---

## Table of Contents

1. [Overview](#1-overview)
2. [Quick Start](#2-quick-start)
3. [AI Psalm 9 Walkthrough](#3-ai-psalm-9-walkthrough)
4. [Project Anatomy](#4-project-anatomy)
5. [Pipeline Stages](#5-pipeline-stages)
6. [Script.json Schema](#6-scriptjson-schema)
7. [Rendering Architecture](#7-rendering-architecture)
8. [2D Positioning System](#8-2d-positioning-system)
9. [Font System](#9-font-system)
10. [Text Styles](#10-text-styles)
11. [Background System](#11-background-system)
12. [Ambient Motion & Effects](#12-ambient-motion--effects)
13. [Audio Reactivity](#13-audio-reactivity)
14. [Animation System](#14-animation-system)
15. [Reveal Modes](#15-reveal-modes)
16. [Intro & Outro](#16-intro--outro)
17. [CLI Reference](#17-cli-reference)
18. [Configuration & Customization](#18-configuration--customization)

---

## 1. Overview

The Music Video Pipeline produces 1920x1080 lyric videos from audio files and lyrics. It renders word-by-word timed text over animated gradient backgrounds with styled text effects (neon, chrome, ice, hologram, gold), per-section visual profiles, and audio-reactive motion.

**Input**: Audio (WAV/MP3/FLAC) + Lyrics (TXT/SRT/LRC) + optional vocal stems
**Output**: Rendered MP4 video with muxed audio

### Key Numbers (AI Psalm 9)

| Metric | Value |
|--------|-------|
| Duration | 86.2 seconds |
| Lines | 25 |
| Words | 132 |
| Sections | 7 |
| Text styles used | 5 (ice, chrome, neon, hologram, gold) |
| Font families used | 5 (Exo2, Bangers, BebasNeue, JetBrainsMono, Lora) |
| Font pool available | 1781 families |
| Output size | 53.3 MB |
| Unique frames | 2054 / 2586 total |

---

## 2. Quick Start

```bash
cd music-video-pipeline

# 1. Create project
PYTHONPATH=src python3 -m cli.commands init \
  -p ../projects/myproject \
  -a ../path/to/song.wav \
  -l ../path/to/lyrics.txt

# 2. Analyze audio
PYTHONPATH=src python3 -m cli.commands analyze -p ../projects/myproject

# 3. Sync lyrics to audio
PYTHONPATH=src python3 -m cli.commands sync -p ../projects/myproject

# 4. Generate script (visual design)
PYTHONPATH=src python3 -m cli.commands render -p ../projects/myproject --script-only

# 5. Edit script.json to customize (optional)
# Edit: ../projects/myproject/data/script.json

# 6. Render video
PYTHONPATH=src python3 -m cli.commands render -p ../projects/myproject
```

Output: `../projects/myproject/output/video.mp4`

---

## 3. AI Psalm 9 Walkthrough

### Input Files

```
projects/prophetic-preprint/projects/ai-psalm-9/data/
├── AI Psalm 9.wav              # Full mix (16.5 MB)
├── AI Psalm 9 Stems (69BPM).zip # Stem files for vocal isolation
├── AI Psalm 9 MIDI.zip          # MIDI data
├── lyrics.txt                   # 25 lines with section markers
├── analysis.json                # Audio features (560 KB)
├── lyrics_synced.json           # Word-level timestamps (175 KB)
├── script.json                  # Visual design script (10 KB)
├── intro_brand.png              # Cathedral/cross branding image
├── outro_logo.png               # Transparent Asabaal Ventures logo
└── ...
```

### Lyrics with Timing

```
L 0:   4.79- 6.85  "Your own people say they are you"
L 1:   7.16-11.45  "whatever, mike, you see what they do"
L 2:  14.71-17.82  "You always show up, even when I have doubt"
L 3:  17.94-21.26  "Showing me what's up, as all go about"
L 4:  21.26-24.84  "You come just in time, as the skin that you chose"
L 5:  24.92-28.96  "From that vision of mine, all those years ago"
L 6:  28.96-30.70  "You've given me albums"
L 7:  30.75-33.14  "I never asked to be queer"
L 8:  33.14-34.54  "As I evolve"
L 9:  34.57-36.73  "Misclassified"
L10:  40.99-43.48  "You've given me series of pieces"
L11:  43.48-45.10  "Weaved through these threads"
L12:  45.16-46.48  "Of reality signals"
L13:  46.51-48.10  "It's living as scripture"
L14:  48.10-49.74  "I'm painting this picture"
L15:  49.74-52.41  "The one you give me"
L16:  52.42-57.58  "I don't fear prophecy"
L17:  57.59-60.70  "It's my new way to be"
L18:  60.70-64.92  "Just as you've made me"
L19:  65.05-66.48  "Post Canonical Prophetic Witness"
L20:  66.48-69.51  "Others will use this label"
L21:  71.35-74.66  "I pray they remember the purpose"
L22:  74.71-76.06  "To seek you"
L23:  76.06-78.44  "To live for you"
L24:  78.51-82.31  "The one true God"
```

### Section Breakdown

#### Section 0: Spoken Prophetic Opening (L0-L1)

| Property | Value |
|----------|-------|
| Time | 4.79s — 11.45s |
| Text style | **ice** (orange glow) |
| Font family | 1 (Exo2 Bold) |
| Font size | 94 |
| Gradient | `cross` |
| Colors | `#080e18 → #1a6078 → #0d1520 → #501878 → #162136` |
| Texture | `noise_grain` at 8% |
| Reveal | `progressive` (1 word at a time) |
| Reactivity | `energy` |
| Animation | `none` (static entrance) |
| BG preset | `smooth` |
| Word positions | L0: words 0-2 at y=0.5, words 3-6 at y=0.8 |
| | L1: words 0-1 at y=0.5, words 2-6 at y=0.8 |

This opening section uses the ice style with an orange glow. Words are split into two groups per line — the first phrase at center (y=0.5) and the second phrase lower (y=0.8). The `cross` gradient creates a cruciform light pattern emanating from center.

#### Section 1: Melodic Testimony Verse (L2-L5)

| Property | Value |
|----------|-------|
| Time | 14.71s — 28.96s |
| Text style | **ice** (orange glow) |
| Font family | 1 (Exo2 Bold) |
| Font sizes | 94 → 98 (ascending per line) |
| Gradient | `conic_0.8` (rotating conic gradient) |
| Colors | `#080e18 → #1d5d7c → #0e1628 → #3a1858 → #1a2548` |
| Texture | `noise_grain` at 8% |
| Reveal | `progressive` |
| Reactivity | `energy` |
| Animation | `fade_in` at 1.2x speed |
| BG preset | `smooth` |
| Word positions | All words at y=0.2 (top) |

The conic gradient (`conic_0.8`) adds a 0.8 radian offset to the angular sweep, creating a sweeping fan of color. Font sizes ascend from 94 to 98 across the 4 lines, building energy.

#### Section 2: Vulnerable Sacred Pop Expansion (L6-L9)

| Property | Value |
|----------|-------|
| Time | 28.96s — 36.73s |
| Text style | **ice** (orange glow) |
| Font family | 1 (Exo2 Bold) |
| Font sizes | 95 → 99 |
| Gradient | `dual_spot_0.3_0.4_0.7_0.6` |
| Colors | `#060a14 → #1e5878 → #381858 → #0a0e1a → #0f1a2d` |
| Texture | `noise_grain` at 8% |
| Reveal | `progressive` |
| Reactivity | `energy` |
| Animation | `fade_in` at 1.3x |
| BG preset | `dreamy` |

The `dual_spot` gradient creates two focal bright points at (30%, 40%) and (70%, 60%), producing a bi-centric lighting effect. Line 7 has words 0-2 overridden to y=0.2 (top).

#### Section 3: Cinematic Prophetic Build (L10-L15)

| Property | Value |
|----------|-------|
| Time | 40.99s — 52.41s |
| Text style | **chrome** (metallic gradient) |
| Font family | 3 (BebasNeue) |
| Font sizes | 96 → 109 (ascending) |
| Gradient | `cross` |
| Colors | `#080c16 → #2c3152 → #3a2845 → #1e2d40 → #0a0e1a` |
| Texture | `noise_grain` at 8% |
| Reveal | `progressive` |
| Reactivity | `energy` |
| Animation | `scale_in` at 1.5x |
| BG preset | `cinematic` |

The chrome style renders words with a metallic gradient (silver-blue highlights). This is the longest section (6 lines). Font sizes climb from 96 to 109, building intensity. Line 10 has per-word `font_size_delta` overrides (0, 6, 8, 10) making words grow across the line.

#### Section 4: Prophetic Declaration Lift (L16-L18)

| Property | Value |
|----------|-------|
| Time | 52.42s — 64.92s |
| Text style | **neon** (bright glow) |
| Font family | 2 (Bangers) |
| Font sizes | **150 → 162** (doubled) |
| Gradient | `dual_spot_0.3_0.3_0.7_0.7` |
| Colors | `#120a04 → #4d3218 → #5a2812 → #2d1f11 → #1a1508` (warm browns) |
| Texture | `noise_grain` at 10% |
| Reveal | `progressive` |
| Reactivity | `drums` + `energy` |
| Animation | `fade_in` at 1.4x |
| BG preset | `dreamy` |

This is the peak energy section. Font sizes are doubled (150-162) from the section base of 94. The neon style produces a bright glow effect around each word. Background colors shift to warm browns, complementing the neon. Line 17 has per-word size deltas (0, 3, 6) at y=0.2.

#### Section 5: Spoken Liturgical Bridge (L19-L20)

| Property | Value |
|----------|-------|
| Time | 65.05s — 69.51s |
| Text style | **hologram** (rainbow shimmer) |
| Font family | 4 (JetBrainsMono) |
| Font sizes | 96 → 101 |
| Gradient | `spiral` |
| Colors | `#0a0814 → #1c1a38 → #0a2a3a → #3a1858 → #1a0a28` |
| Texture | `noise_grain` at 8% |
| Reveal | **`stacking`** (lines accumulate on screen) |
| Reactivity | `energy` + `vocals` |
| Animation | `fade_in` at 1.6x |
| BG preset | `dreamy` |
| Word positions | L19: all words at y=0.35, L20: all words at y=0.65 |

The stacking reveal mode draws both lines simultaneously — L19 at y=0.35 and L20 at y=0.65. The spiral gradient creates a swirling pattern. This is the only section using `stacking` reveal.

#### Section 6: Prayerful Final Movement (L21-L24)

| Property | Value |
|----------|-------|
| Time | 71.35s — 82.31s |
| Text style | **gold** (warm metallic) |
| Font family | 5 (Lora Bold) |
| Font sizes | 96 → 108 |
| Gradient | `cross` |
| Colors | `#0a1218 → #2a3540 → #4a3510 → #172529 → #38280a` |
| Texture | `noise_grain` at 8% |
| Reveal | `progressive` |
| Reactivity | `drums` + `energy` |
| Animation | `fade_in` at 1.2x |
| BG preset | `smooth` |
| Word positions | L21 words 0-2 at y=0.2 |

The closing section uses the gold style (warm amber/gold metallic) with a serif font (Lora). Background includes gold-brown accents (`#4a3510`, `#38280a`).

### Intro (0 — 4.789s)

Phase 1 (0 — 2.63s): Full-screen branding image (cathedral/cross with ASABAAL text)
Phase 2 (2.87s — 4.79s): Dark gradient background with centered title card:
- "AI Psalm 9" (80pt, family 3 — BebasNeue)
- "A Reality Signal" (44pt, family 5 — Lora)
- "by" (44pt, family 5)
- "Asabaal Horan" (44pt, family 5)

Between phases: brief transition with default gradient background.

### Outro (82.31s — 86.2s)

Phase 1 (82.31s — 84.0s): Branding image (same as intro)
Phase 2 (84.1s — 86.2s): Dark gradient with "Presented by" text (36pt, Lora) and transparent Asabaal Ventures logo centered below

---

## 4. Project Anatomy

```
music-video-pipeline/
├── src/
│   ├── audio/                    # Audio analysis
│   │   ├── analyzer.py           # Beat detection, RMS, spectral analysis
│   │   ├── features.py           # AudioFeatures, BeatInfo dataclasses
│   │   ├── ingest.py             # Input discovery, ZIP extraction
│   │   └── midi.py               # MIDI analysis via pretty_midi
│   │
│   ├── lyrics/                   # Lyrics parsing + sync
│   │   ├── parser.py             # SRT/LRC/TXT → LyricLine/LyricWord
│   │   ├── synchronizer.py       # Align lyrics to audio
│   │   └── processor.py          # Facade
│   │
│   ├── sections/                 # Section management
│   │   ├── types.py              # 18 section type enum
│   │   ├── manager.py            # Section detection
│   │   └── loader.py             # Parse structure files
│   │
│   ├── visual/                   # Visual design
│   │   ├── image_gen.py          # SD3 subprocess bridge
│   │   ├── backgrounds.py        # Background source management
│   │   └── style_profiles.py     # Per-section visual defaults
│   │
│   ├── render/                   # Rendering engine
│   │   ├── renderer.py           # VideoRenderer — main render loop (1293 lines)
│   │   ├── font_styles.py        # 9 text styles with glow/gradient effects (440 lines)
│   │   ├── font_registry.json    # 1781 font family entries
│   │   ├── frame_effects.py      # 14 frame effects (ken_burns, bokeh, etc.)
│   │   ├── effect_presets.py     # 8 presets combining effects
│   │   ├── audio_reactive.py     # Audio → visual modulation
│   │   ├── animations.py         # 14 animation types, 7 easing functions
│   │   ├── background_video.py   # Background video source
│   │   └── encoder.py            # FFmpeg streaming encoder
│   │
│   ├── scriptgen/                # Script generation
│   │   ├── generator.py          # generate() — creates script.json
│   │   ├── rules.py              # assign_word_positions(), assign_font_family()
│   │   ├── moods.py              # MoodProfile definitions
│   │   └── palette.py            # SectionColor palette generation
│   │
│   ├── pipeline/                 # Orchestration
│   │   ├── orchestrator.py       # Stage sequencing
│   │   └── models.py             # Project state models
│   │
│   └── cli/                      # CLI
│       └── commands.py           # Click CLI (1165 lines)
│
├── fonts/                        # 3614 TTF files (1.26 GB, gitignored)
├── download_fonts.py             # Download script for Google Fonts
├── templates/                    # 6 visual template presets
├── tools/                        # Browser-based interactive tools
├── tests/                        # Test suite
├── explorer.html                 # Feature explorer with visual demos
├── explorer_assets/              # PNG + MP4 demos for every feature
└── docs/                         # Documentation (this file)
```

### Per-Project Structure

```
projects/myproject/
├── data/
│   ├── mvp_project.json          # Project metadata, paths
│   ├── analysis.json             # Audio features (560 KB for AI Psalm 9)
│   ├── lyrics_synced.json        # Word-level timestamps
│   ├── lyrics_raw.json           # Parsed lyrics before sync
│   ├── script.json               # Visual design (THE key file)
│   ├── vocal_transcription.json  # Whisper word timestamps
│   ├── vocal_onsets.json         # Vocal onset times
│   ├── waveforms.json            # Waveform peaks (100/sec)
│   ├── ingest.json               # Input tier detection results
│   ├── lyrics.txt                # Original lyrics
│   ├── *.wav                     # Audio files
│   └── assets/                   # Images (intro, outro logos)
└── output/
    └── video.mp4                 # Rendered output
```

---

## 5. Pipeline Stages

### Stage 1: Ingest

Discovers inputs in the project directory. Detects audio format, lyrics format, stem ZIPs, MIDI ZIPs. Determines input tier (Basic/Standard/Enhanced/Full).

**CLI**: `mvp init -p <dir> -a <audio> -l <lyrics>`
**Output**: `ingest.json`

### Stage 2: Analyze

Extracts audio features using librosa:
- Beat detection (BPM, beat times, confidence)
- RMS energy (normalized 0-1, per-frame)
- Spectral centroids (brightness per frame)
- Onset detection
- Per-stem energy (if stems available)
- Waveform generation (100 peaks/second)

**CLI**: `mvp analyze -p <dir>`
**Output**: `analysis.json` (~560 KB for 86s track)

### Stage 3: Sync

Aligns lyrics to audio at word level. Three-tier approach:
1. **MIDI note alignment** (if MIDI available)
2. **Vocal stem onset + Whisper transcription** (if vocal stem available)
3. **Full mix onset heuristic** (fallback)

Produces word-level timestamps with `start`/`end` for every word. Applies reconciliation:
- Line boundaries: `min(curr_last_word_end, next_first_word_start)`
- Minimum word duration: 0.04s
- No inversions: `start < end` guaranteed

**CLI**: `mvp sync -p <dir>`
**Output**: `lyrics_synced.json`

### Stage 4: Structure

Detects sections from lyrics markers (`[Verse]`, `[Chorus]`, etc.) and audio energy profiles. Maps custom section names to canonical types via keyword matching (e.g., "spoken_prophetic_opening" → "intro").

Handled internally during script generation.

### Stage 5: Design (Script Generation)

Creates `script.json` — the complete visual design specification:
- Assigns background gradients, colors, textures per section
- Selects font families from 1781-font pool based on section type
- Assigns text styles (ice/neon/chrome/hologram/gold)
- Computes word positions (y-coordinates)
- Sets reveal modes, animation types, reactivity

**CLI**: `mvp render -p <dir> --script-only`
**Output**: `script.json`

### Stage 6: Render

Frame-by-frame rendering:
1. For each frame, find active word at timestamp
2. Resolve visual properties (defaults → section → line → word overrides)
3. Draw gradient background
4. Apply ambient motion effects
5. Layout and render text at computed positions
6. Apply enter/exit animations
7. Encode via FFmpeg streaming encoder
8. Mux audio

**CLI**: `mvp render -p <dir>`
**Output**: `output/video.mp4`

---

## 6. Script.json Schema

The script is the heart of the visual design. Every render decision is controlled by this file.

### Top Level

```json
{
  "name": "Song Title",
  "defaults": { ... },
  "caption_style": { ... },
  "sections": [ ... ],
  "intro": { ... },
  "outro": { ... }
}
```

### Defaults

Applied when no section/line/word override exists.

```json
{
  "background_type": "gradient",
  "background_color": "#162126",
  "gradient_colors": ["#162126", "#222b39"],
  "gradient_direction": "radial_center",
  "texture_type": "vignette_soft",
  "texture_opacity": 0.2,
  "texture_blend_mode": "multiply",
  "text_auto_contrast": true,
  "font_size": 146,
  "animation_type": "fade",
  "animation_speed": 1.0,
  "reveal_mode": "progressive",
  "reveal_words": 1,
  "reveal_slide": false,
  "reactivity": ["vocals"],
  "text_align": "center"
}
```

### Caption Style

Global text rendering options:

```json
{
  "font_family": 0,
  "highlight_color": "#FF8C00",
  "text_position": "center",
  "letter_spacing": 1,
  "text_shadow": false,
  "outline": false
}
```

### Section

Each section covers a range of lines and defines visual overrides:

```json
{
  "name": "cinematic prophetic build",
  "type": "cinematic_prophetic_build",
  "lines": [10, 11, 12, 13, 14, 15],
  "visual": {
    "background_type": "gradient",
    "gradient_direction": "cross",
    "background_color": "#1e2d40",
    "gradient_colors": ["#080c16", "#2c3152", "#3a2845", "#1e2d40", "#0a0e1a"],
    "texture_type": "noise_grain",
    "texture_opacity": 0.08,
    "texture_blend_mode": "multiply",
    "font_size": 94,
    "reveal_mode": "progressive",
    "reveal_words": 1,
    "reactivity": ["energy"],
    "text_position": "center",
    "animation_type": "scale_in",
    "animation_speed": 1.5,
    "bg_animation_preset": "cinematic",
    "text_style": "chrome",
    "font_family": 3
  },
  "lines_overrides": {
    "10": { "font_size": 96 },
    "11": { "font_size": 99 },
    "12": { "font_size": 101 },
    "13": { "font_size": 104 },
    "14": { "font_size": 107 },
    "15": { "font_size": 109 }
  },
  "words_overrides": {
    "10.0": { "y": 0.2, "font_size_delta": 0 },
    "10.1": { "y": 0.2 },
    "10.2": { "y": 0.2 },
    "10.3": { "font_size_delta": 6 },
    "10.4": { "font_size_delta": 8 },
    "10.5": { "font_size_delta": 10 }
  }
}
```

### Override Hierarchy

Visual properties are resolved in priority order:

```
defaults → section.visual → lines_overrides → words_overrides
```

Later values override earlier ones. The `get_visual(line_idx, word_idx)` method in `renderer.py:178` implements this cascade.

### Word Override Keys

Words are keyed as `"line_idx.word_idx"`:

```json
{
  "17.0": { "y": 0.2, "font_size_delta": 0 },
  "17.1": { "y": 0.2, "font_size_delta": 3 },
  "17.2": { "y": 0.2, "font_size_delta": 6 }
}
```

### Word Override Fields

| Field | Type | Description |
|-------|------|-------------|
| `y` | float (0.0-1.0) | Vertical position (proportional to height) |
| `x` | float (0.0-1.0) | Horizontal position (optional, pinned) |
| `font_size_delta` | int | Additive size change to base font size |
| `text_position` | string | Named position: "top", "center", "bottom" (fallback if no `y`) |
| `font_size` | int | Absolute font size override |
| `color` | hex | Word-specific color |

### Intro Config

```json
{
  "intro": {
    "image": "/absolute/path/to/intro_brand.png",
    "title": "",
    "subtitle": "",
    "duration": 4.789
  }
}
```

Duration is typically set to the start time of the first word.

### Outro Config

```json
{
  "outro": {
    "image": "/absolute/path/to/intro_brand.png",
    "logo": "/absolute/path/to/outro_logo.png",
    "text": "Presented by"
  }
}
```

Duration is auto-computed as `audio_duration - last_word_end`.

---

## 7. Rendering Architecture

### Frame Pipeline

```
For each frame at time t:
  1. Find active word: _find_active_word(t) → (line_idx, word_idx)
  2. If no active word:
     a. Check intro: _render_intro_frame(t)
     b. Check outro: _render_outro_frame(t)
     c. Render gap frame with nearest section's visuals + brightness boost
  3. If active word:
     a. Resolve visual: get_visual(line_idx, word_idx)
     b. Draw background: _draw_background(img, v)
     c. Apply ambient motion: _apply_bg_motion(img, t, v)
     d. Compute animation: _compute_animation_progress(t, line_idx)
     e. Create transparent text layer
     f. Layout + render text per reveal mode
     g. Apply animation transforms (scale, rotation, opacity)
     h. Alpha composite text onto background
  4. Encode frame via FFmpeg
```

Source: `renderer.py:1037-1117` (`render_frame`) and `renderer.py:1119-1195` (`_render_text_on_bg`)

### Frame Caching

The render loop (`renderer.py:1224-1293`) caches frames to avoid re-rendering identical frames:

- Backgrounds are cached per section name (`_get_bg_for_section`)
- Styled text images are cached by `(text, style, size, family)` tuple
- Frames with the same `(line_idx, word_idx)` key are reused byte-for-byte
- Animated frames use `(line_idx, word_idx, frame_idx)` as key — never cached
- Gap frames bucket at 1/4 second intervals for caching

### Rendering Stats (AI Psalm 9)

- Total frames: 2586 (86.2s × 30fps)
- Unique frames rendered: 2054 (79.5%)
- Reused frames: 532 (20.5%)
- Output size: 53.3 MB

### Encoder

FFmpeg streaming encoder (`encoder.py`):
- Codec: libx264
- Pixel format: yuv420p
- Audio: AAC from source
- movflag: +faststart
- Frame rate: 30fps

---

## 8. 2D Positioning System

The layout system places each word at an explicit (x, y) position. There is no fill-spreading or auto-layout engine — the script IS the layout.

### `_layout_line()` — `renderer.py:637-681`

1. **Resolve each word's y-position**: Falls back through `y` → `text_position` → section default → "center"
2. **Resolve each word's font size**: `base_font_size + font_size_delta * scale_factor`
3. **Measure word widths**: Uses tight font metrics (`font.getbbox()`) NOT styled image widths
4. **Pin explicitly-x-positioned words**: If word has `x` override, place at `x * width`
5. **Group unpinned words by y**: Words at the same y are centered together
6. **Center each group**: Calculate total width with spacing, center horizontally

### Spacing

- Base spacing: `letter_spacing * (height/1080) * max(8, font_size * 0.08)`
- For styled text (ice/neon/chrome/etc.): `max(base_spacing, font_size * 0.35)`
  - The 0.35 minimum prevents glow effects from overlapping between words

### Y-Position Resolution — `renderer.py:631-635`

```python
def _resolve_word_y(self, wv, section_pos):
    if "y" in wv:
        return wv["y"]           # Explicit y (0.0-1.0)
    tp = wv.get("text_position", section_pos)
    return self._POS_TO_Y.get(tp, 0.5)  # Named position → fixed y
```

| text_position | y value |
|---------------|---------|
| "top" | 0.2 |
| "center" | 0.5 |
| "bottom" | 0.8 |

### Reading Order

First phrase always appears above second phrase. For split-line layouts (e.g., Section 0):
- First phrase: y=0.5 (center)
- Second phrase: y=0.8 (lower)

Never y=0.8 then y=0.2 — that would reverse reading order.

---

## 9. Font System

### Font Pool

1781 Google Font families downloaded via `download_fonts.py`:
- Sans: 718 families
- Display: 466 families
- Serif: 323 families
- Handwriting: 226 families
- Mono: 48 families

Total: 3614 TTF files, 1.26 GB (gitignored)

### Font Registry — `font_registry.json`

Each entry maps a numeric ID to font file paths:

```json
{
  "Exo 2": {
    "id": 1,
    "bold": "Exo2-Bold.ttf",
    "regular": "Exo2-Regular.ttf",
    "category": "sans"
  },
  "Bangers": {
    "id": 2,
    "bold": "Bangers-Regular.ttf",
    "regular": "Bangers-Regular.ttf",
    "category": "display"
  }
}
```

IDs 1-6 are reserved for the original font families. IDs 7+ are assigned alphabetically by font name.

### Font Loading — `font_styles.py:41-55`

The `_load_registry()` function:
1. Starts with legacy font map (IDs 1-6)
2. Loads `font_registry.json` if it exists
3. Merges new entries, skipping existing IDs
4. Result cached in module-level `_font_registry` dict

### Font Selection — `rules.py`

`assign_font_family()` selects fonts based on section type:

| Section type | Category preference |
|--------------|-------------------|
| verse, intro | sans |
| chorus, lift | display |
| bridge, breakdown | serif |
| pre_chorus | sans or display (energy-dependent) |
| outro | serif or handwriting |

Uses song name hash for deterministic unique selection — same song always gets same fonts.

### Legacy Font IDs

| ID | Font | Category |
|----|------|----------|
| 1 | Exo 2 | sans |
| 2 | Bangers | display |
| 3 | Bebas Neue | sans/display |
| 4 | JetBrains Mono | mono |
| 5 | Lora | serif |
| 6 | Oswald | sans |

---

## 10. Text Styles

Nine styles available via `font_styles.py`. Each produces an RGBA image with glow, gradient, and color effects.

### Style Reference

| Style | Core Colors | Glow Color | Effect |
|-------|-------------|------------|--------|
| **ice** | Orange gradient `(255,160,20)→(255,200,80)` | `(255,140,0)` | Warm orange glow with soft outer haze |
| **neon** | Hot pink/magenta | Bright pink | Intense glow with bloom |
| **chrome** | Silver-blue metallic | Cool white | Metallic gradient, beveled look |
| **hologram** | Rainbow shimmer | Prismatic | Shifting rainbow colors |
| **gold** | Warm amber/gold | Golden | Metallic gold with warm glow |
| **fire** | Red-orange-yellow | Hot red | Flame-like gradient |
| **graffiti** | Bright green/lime | Green | Spray-paint effect |
| **matrix** | Green-on-black | Phosphor green | Terminal/digital look |
| **basic** | White/contrast | None | Plain text, no effects |

### Rendering Pipeline — `generate_styled_text()`

1. Create transparent RGBA canvas (oversized for glow)
2. Render base text at requested size
3. Apply style-specific glow layers (gaussian blur at multiple radii)
4. Draw core text with gradient fill
5. Add highlight/shimmer effects
6. Crop to tight bounds
7. Return RGBA image

### Styled Text Caching

Styled text images are cached in `VideoRenderer._styled_cache` keyed by `(text, style, size, family)`. This prevents regenerating the same styled word across frames.

### Styled Text Layout Consideration

Styled text images are wider than tight font metrics due to glow padding. The layout system uses **tight font metrics** (`font.getbbox()`) for positioning, with a minimum spacing of `font_size * 0.35` for styled text to prevent glow merging between words.

---

## 11. Background System

### Gradient Types (16 geometries)

| Type | Direction String | Description |
|------|-----------------|-------------|
| Vertical TB | `vertical_top_bottom` | Top to bottom |
| Vertical BT | `vertical_bottom_top` | Bottom to top |
| Horizontal LR | `horizontal_left_right` | Left to right |
| Horizontal RL | `horizontal_right_left` | Right to left |
| Diagonal TL-BR | `diagonal_tl_br` | Top-left to bottom-right |
| Diagonal TR-BL | `diagonal_tr_bl` | Top-right to bottom-left |
| Radial center | `radial_center` | Center outward |
| Radial top | `radial_top` | Top-center outward |
| Radial bottom | `radial_bottom` | Bottom-center outward |
| Radial TL | `radial_tl` | Top-left corner outward |
| Radial BR | `radial_br` | Bottom-right corner outward |
| Conic | `conic` or `conic_<offset>` | Angular sweep from center |
| Diamond | `diamond` | Manhattan distance from center |
| Dual spot | `dual_spot_<x1>_<y1>_<x2>_<y2>` | Two focal points |
| Bands | `bands` | Horizontal color bands |
| Cross | `cross` | Cruciform pattern from center |
| Spiral | `spiral` | Spiral pattern from center |

All gradients support 2-5 color stops with linear interpolation.

Source: `renderer.py:338-481`

### Texture Types

| Type | Effect |
|------|--------|
| `none` | No texture |
| `noise_fine` | Fine grain noise |
| `noise_coarse` | Binary noise (50% threshold) |
| `noise_grain` | Medium grain (used in AI Psalm 9) |
| `grain_film` | Film-like grain |
| `paper_subtle` | Very subtle paper texture |
| `vignette_soft` | Soft edge darkening |
| `vignette_heavy` | Strong edge darkening |

Blend modes: `normal` (additive) or `multiply` (darkening)

Source: `renderer.py:516-548`

### Background Images

Supports file paths with `cover` or `contain` fit and configurable opacity.

---

## 12. Ambient Motion & Effects

### Effect Presets — `effect_presets.py`

| Preset | Effects | Audio |
|--------|---------|-------|
| **cinematic** | ken_burns, color_drift, bokeh, radial_pulse, zoom_pulse, color_shift, vignette_pulse | energy |
| **energetic** | ken_burns, bokeh, radial_pulse, camera_shake, brightness_pulse | drums, energy |
| **dreamy** | ken_burns, color_drift, bokeh (18 particles), radial_pulse, wave_distortion, zoom_blur, vignette_pulse | energy |
| **glitch** | ken_burns, bokeh, radial_pulse, glitch, contrast_pulse | drums |
| **minimal** | (none) | (none) |
| **psychedelic** | ken_burns, color_drift, bokeh (20), radial_pulse, color_shift (30°), wave_distortion | energy, drums |
| **smooth** | ken_burns, color_drift, bokeh (8), radial_pulse, zoom_pulse, vignette_pulse | energy |
| **intense** | ken_burns, bokeh, radial_pulse, camera_shake, brightness_pulse, contrast_pulse, color_shift | energy, drums |

### Frame Effects — `frame_effects.py`

| Effect | Parameters | Visual Result |
|--------|-----------|---------------|
| `ken_burns` | speed, max_zoom, drift | Slow pan/zoom |
| `color_drift` | speed, hue_range, sat_pulse | Subtle hue shift |
| `bokeh_particles` | count, speed, color, max_radius, max_alpha | Floating light orbs |
| `radial_pulse` | speed, max_alpha | Pulsing center glow |
| `zoom_pulse` | intensity, speed | Rhythmic zoom |
| `color_shift` | hue_shift | Static hue rotation |
| `vignette_pulse` | intensity | Breathing vignette |
| `camera_shake` | intensity | Random displacement |
| `brightness_pulse` | speed | Beat-synced flash |
| `contrast_pulse` | speed | Dynamic contrast |
| `glitch` | intensity | RGB channel offset |
| `wave_distortion` | intensity, speed | Wavy distortion |
| `zoom_blur` | intensity | Radial blur |

### Processing Pipeline — `renderer.py:572-596`

1. Background image → downsample 2x (for perf)
2. Apply each preset effect in sequence via `apply_frame_effect()`
3. Apply audio-reactive effects via `apply_audio_effects()`
4. Upsample back to full resolution

### Gap Frame Handling

When no word is active (between lines, during intro/outro):
- Uses nearest section's visual settings
- Applies `gap` preset (minimal effects)
- 2.5x brightness boost on background to prevent dark voids
- Ambient motion continues

Source: `renderer.py:1041-1064`

---

## 13. Audio Reactivity

### Audio Data Sources

From `analysis.json`:
- `rms_energy[]` — Per-frame RMS energy (normalized 0-1)
- `spectral_centroids[]` — Per-frame spectral centroid (brightness)
- `beat_times[]` — Beat timestamps

Accessed via `_get_audio_at(t)` (`renderer.py:203-220`).

### Reactivity Modes

| Mode | Effect |
|------|--------|
| `energy` | Overall energy modulates glow intensity, color saturation |
| `drums` | Beat detection triggers flash effects, camera shake |
| `vocals` | Vocal energy drives text opacity, color shift |
| `bass` | Bass energy modulates background intensity |

Specified per-section via `reactivity` array (can combine multiple).

Source: `audio_reactive.py`

---

## 14. Animation System

### Animation Types — `animations.py`

| Type | Enter Effect | Exit Effect |
|------|-------------|-------------|
| `fade_in` | Opacity 0→1 | Opacity 1→0 |
| `slide_in` | Slide from bottom | Slide to top |
| `scale_in` | Scale 0.5→1.0 | Scale 1.0→0.5 |
| `bounce_in` | Bounce overshoot | — |
| `elastic_in` | Spring overshoot | — |
| `rotate_in` | Rotate from -15° | — |
| `typewriter` | Characters appear one by one | — |
| `glow_pulse` | Glow intensity pulse | — |
| `wave` | Wave distortion | — |
| `shake` | Random vibration | — |
| `none` | No animation | No animation |

### Easing Functions

7 easing functions: `LINEAR`, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT`, `BOUNCE`, `ELASTIC`, `SPRING`

### Animation Timing — `renderer.py:222-285`

```python
enter_duration = 0.25 / animation_speed
enter_end = min(0.3, enter_duration / line_duration)
exit_start = max(last_word_progress, 1.0 - 0.2 / animation_speed)
```

- Enter: First 25% of animation speed, capped at 30% of line duration
- Steady: Full opacity, no transform
- Exit: Last 20% of animation speed, starting after last word begins

For `fade_in` specifically, opacity is forced to 1.0 during the first 20% of enter phase (prevents flicker at line boundaries).

### Scale Clamping

Minimum scale: 0.5 — prevents text from becoming too small during scale animations.

---

## 15. Reveal Modes

### Progressive

Words appear one at a time as they're timed. The active word and its group are at full opacity; previously revealed words are at 80% opacity.

- `reveal_words` (default: 1): How many words to reveal per step
- `reveal_slide`: If true, uses a sliding window instead of cumulative reveal

Source: `renderer.py:777-848`

### Karaoke

All words visible simultaneously. The active word is highlighted (full opacity), inactive words are at 75% opacity. Uses `highlight_color` for active word.

Source: `renderer.py:727-775`

### Line-by-line

Entire line text rendered at once as a single string. No word-by-word reveal. Positioned at `text_position` (top/center/bottom).

Source: `renderer.py:683-725`

### Stacking

Like line-by-line, but lines accumulate on screen. For each active line, all lines up to and including it are drawn at their respective y-positions. Used for multi-line displays where lines should remain visible (e.g., title + subtitle).

Source: `renderer.py:1082-1093`

---

## 16. Intro & Outro

### Intro — `renderer.py:850-918`

Two-phase static display:

**Phase 1** (0 — 55% of intro duration): Full-screen branding image (cover fit)
**Transition** (55% — 60%): Default gradient background
**Phase 2** (60% — 100%): Default gradient + centered title card

Title card text (hardcoded for AI Psalm 9):
```
AI Psalm 9        (80pt, BebasNeue)
A Reality Signal   (44pt, Lora)
by                 (44pt, Lora)
Asabaal Horan      (44pt, Lora)
```

The intro is entirely static — no fade animations. Text uses shadow offset for depth.

### Outro — `renderer.py:929-1012`

Auto-computed duration: `audio_duration - last_word_end` (~3.9s for AI Psalm 9)

Two phases (mirrors intro structure):

**Phase 1** (0 — 45% of outro duration): Branding image
**Transition** (45% — 50%): Default gradient
**Phase 2** (50% — 100%): Default gradient + "Presented by" text (36pt, Lora) + transparent logo centered below

---

## 17. CLI Reference

### Run Command

```bash
cd music-video-pipeline
PYTHONPATH=src python3 -m cli.commands <command> -p <project_dir>
```

**Important**: Always pass `-p` with the project path. The pipeline's own `data/` directory has a different project.

### Commands

#### `init` — Create project

```bash
mvp init -p ../projects/myproject -a ../song.wav -l ../lyrics.txt
```

Options:
- `-a, --audio`: Audio file path (WAV/MP3/FLAC)
- `-l, --lyrics`: Lyrics file path (TXT/SRT/LRC)

#### `analyze` — Extract audio features

```bash
mvp analyze -p ../projects/myproject
```

Runs beat detection, RMS energy, spectral analysis, onset detection. Outputs `analysis.json`.

#### `sync` — Sync lyrics to audio

```bash
mvp sync -p ../projects/myproject
```

Three-tier sync: MIDI > vocal stem + Whisper > full mix onset heuristic. Outputs `lyrics_synced.json`.

#### `render` — Generate script and/or render video

```bash
# Generate script only
mvp render -p ../projects/myproject --script-only

# Full render
mvp render -p ../projects/myproject

# Render with options
mvp render -p ../projects/myproject \
  --intro-image ../brand.png \
  --intro-title "Song Title" \
  --intro-subtitle "by Artist" \
  --start 10.0 --end 60.0
```

Options:
- `--script-only`: Generate script.json without rendering
- `--intro-image`: Branding image for intro
- `--intro-title`: Title text
- `--intro-subtitle`: Subtitle text
- `--start` / `--end`: Render time range (seconds)
- `--bare`: Minimal rendering for timing preview

#### `info` — Show project info

```bash
mvp info -p ../projects/myproject
```

#### `audit` — Audit rendered video

```bash
mvp audit -p ../projects/myproject
```

Generates per-word frame samples in `output/audit/` for visual inspection.

#### `serve` — Start browser tools

```bash
mvp serve -p ../projects/myproject
```

Starts HTTP server with browser-based editor.

### AI Psalm 9 Render Command

```bash
cd music-video-pipeline
PYTHONPATH=src python3 -m cli.commands render \
  -p ../projects/prophetic-preprint/projects/ai-psalm-9
```

---

## 18. Configuration & Customization

### Auto-Generated Script → Manual Tuning

The pipeline generates a complete `script.json`, but for production quality it's usually hand-tuned:

1. Run `mvp render -p <dir> --script-only` to generate initial script
2. Edit `data/script.json` directly
3. Run `mvp render -p <dir>` to render

**Warning**: `projects/` is gitignored. Manual edits to `script.json` are lost if regeneration is triggered. Back up your scripts.

### Common Customizations

#### Change text style for a section

```json
{
  "visual": {
    "text_style": "neon"
  }
}
```

Options: `ice`, `neon`, `chrome`, `hologram`, `gold`, `fire`, `graffiti`, `matrix`, `basic`

#### Change font family

```json
{
  "visual": {
    "font_family": 42
  }
}
```

Look up IDs in `font_registry.json`. IDs 1-6 are legacy defaults.

#### Custom word positions (two-line layout)

```json
{
  "words_overrides": {
    "0.0": { "y": 0.3 },
    "0.1": { "y": 0.3 },
    "0.2": { "y": 0.7 },
    "0.3": { "y": 0.7 }
  }
}
```

#### Ascending font sizes per line

```json
{
  "lines_overrides": {
    "2": { "font_size": 94 },
    "3": { "font_size": 97 },
    "4": { "font_size": 100 },
    "5": { "font_size": 104 }
  }
}
```

#### Per-word size ramp

```json
{
  "words_overrides": {
    "10.0": { "font_size_delta": 0 },
    "10.1": { "font_size_delta": 5 },
    "10.2": { "font_size_delta": 10 },
    "10.3": { "font_size_delta": 15 }
  }
}
```

#### Stacking reveal for title/subtitle

```json
{
  "visual": {
    "reveal_mode": "stacking"
  },
  "words_overrides": {
    "0.0": { "y": 0.35 },
    "1.0": { "y": 0.65 }
  }
}
```

### Section Type Resolution

Custom section names in lyrics are mapped to canonical types via keyword matching:

```python
_CANONICAL_KEYWORDS = {
    "intro": ["intro", "opening", "prologue", "preface"],
    "verse": ["verse", "testimony", "melodic", "strophe", "stanza"],
    "chorus": ["chorus", "hook", "refrain", "lift", "declaration", "peak", "anthem", "praise"],
    "bridge": ["bridge", "breakdown", "interlude", "liturgical", "break", "spoken_word"],
    "pre_chorus": ["pre_chorus", "prechorus", "build", "ramp", "climb", "rising"],
    "outro": ["outro", "ending", "closing", "resolution", "final", "coda", "fade"],
}
```

Source: `rules.py:51-58`

### Troubleshooting

**Words overlapping / too far apart**: Check `font_size_delta` values and `letter_spacing`. For styled text, minimum spacing is `font_size * 0.35`.

**Dark gaps between sections**: The renderer applies a 2.5x brightness boost and uses the nearest section's visuals. If gaps are still dark, check gradient colors have sufficient brightness.

**Animation flicker**: For `fade_in`, the first 20% of enter phase is forced to full opacity (1.0) to prevent flicker at line boundaries. This is intentional.

**Font not found**: The font registry loads from `font_registry.json` in the render directory. Ensure fonts are downloaded via `download_fonts.py` if using IDs > 6.

**Timing issues**: Check `lyrics_synced.json` for word timestamps. The reconciliation step ensures `start < end` and minimum duration of 0.04s per word.

**Reading order reversed**: Ensure first phrase has lower y value than second phrase (e.g., y=0.5 for first, y=0.8 for second — never the reverse).
