# MVP Feature Status

Catalog of all visual features in the music-video-pipeline. Organized by implementation status.

## Fully Implemented (Renderable)

### Background

| Feature | Field | Values | Notes |
|---------|-------|--------|-------|
| Solid color | `background_type: "solid"` | Any hex color | Default `#1a1a2e` |
| Gradient | `background_type: "gradient"` | 9 directions, 2-4 color stops | Multi-stop interpolation |
| Background image | `background_type: "image"` | File path or data-URI | Cover/contain fit + opacity |

**Gradient directions:** `vertical_top_bottom`, `vertical_bottom_top`, `horizontal_left_right`, `horizontal_right_left`, `diagonal_tl_br`, `diagonal_tr_bl`, `radial_center`, `radial_top`, `radial_bottom`

### Textures

| Feature | Field | Values | Notes |
|---------|-------|--------|-------|
| Texture types | `texture_type` | `none`, `noise_fine`, `noise_coarse`, `grain_film`, `paper_subtle`, `vignette_soft`, `vignette_heavy` | 7 types |
| Opacity | `texture_opacity` | 0.0 - 1.0 | Default 0.15 |
| Blend mode | `texture_blend_mode` | `normal` (additive), `multiply` | |

### Text & Captions

| Feature | Field | Values | Notes |
|---------|-------|--------|-------|
| Auto contrast | `text_auto_contrast` | bool | Picks black/white based on background luminance |
| Manual text color | `text_color` | hex | Only when auto_contrast is false |
| Font size | `font_size` | 24 - 96 | Scales with render height |
| Text position | `caption_style.text_position` | `top`, `center`, `bottom` | |
| Text shadow | `caption_style.text_shadow` | bool | Color configurable via `text_shadow_color` |
| Text outline | `caption_style.outline` | bool | Color + width configurable |
| Highlight color | `caption_style.highlight_color` | hex | Active word color in progressive/karaoke modes |
| Letter spacing | `caption_style.letter_spacing` | multiplier | Used in progressive and karaoke modes |

### Reveal Modes

| Mode | Field | Behavior |
|------|-------|----------|
| Progressive | `reveal_mode: "progressive"` | Words appear one-by-one. `reveal_words` (1-8) controls grouping, `reveal_slide` enables sliding window |
| Karaoke | `reveal_mode: "karaoke"` | All words visible, active word highlighted with highlight_color |
| Line-by-line | `reveal_mode: "line-by-line"` | Full line text appears at once, no word-by-word reveal |

### Per-Section Overrides

| Level | Field | Notes |
|-------|-------|-------|
| Section | `sections[].visual` | Override any visual property for a section |
| Line | `sections[].lines_overrides` | Keyed by line index as string |
| Word | `sections[].words_overrides` | Keyed by `"line_idx.word_idx"` |

### Rendering Engine

| Feature | Status |
|---------|--------|
| Frame caching (reuse identical frames) | Implemented |
| Section background caching | Implemented |
| FFmpeg streaming encoder (libx264 + AAC) | Implemented |
| Bitrate control (`-b:v`) | Implemented |
| `+faststart` movflag | Implemented |

---

## Partially Implemented

| Feature | What Works | What's Missing |
|---------|-----------|----------------|
| Font families | 5 families defined in editor UI (`system-ui`, `Georgia`, `Courier New`, `Impact`, `Trebuchet MS`) | Renderer uses single hardcoded font path search (`_find_font`) ignoring `caption_style.font_family` |
| Letter spacing | Applied in progressive and karaoke word layout | Not applied in line-by-line mode (`_draw_text_line`) |
| Background images | Cover/contain fit + opacity works for file paths | Data-URI images (`data:...`) return early without rendering in `_draw_bg_image` |
| Highlight color | Used in progressive and karaoke modes | Not visible in line-by-line mode (no active word distinction) |

---

## Defined but Not Rendered

These features have fields in the data model (`src/pipeline/models.py`), template files, and editor UI, but the renderer (`src/render/renderer.py`) does not implement them.

### Animation Types

Text entrance/exit animations for how lyrics appear and disappear.

| Type | Field Value | Intended Behavior |
|------|------------|-------------------|
| Fade | `animation_type: "fade"` | Text fades in/out smoothly |
| Slide | `animation_type: "slide"` | Text slides in from one side |
| Scale | `animation_type: "scale"` | Text scales up from small to full size |
| Typewriter | `animation_type: "typewriter"` | Characters appear one at a time |
| Pulse | `animation_type: "pulse"` | Text pulses/breathes rhythmically |
| None | `animation_type: "none"` | No animation |

**Controlling fields:** `animation_type`, `animation_speed` (0.1 - 2.0)

### Background Animations

Movement and effects applied to the background layer.

| Type | Field Value | Intended Behavior |
|------|------------|-------------------|
| Drift | `bg_animation_type: "drift"` | Slow background panning |
| Flow | `bg_animation_type: "flow"` | Flowing color movement |
| Pulse | `bg_animation_type: "pulse"` | Background pulses synced to beat |
| Distortion | `bg_animation_type: "distortion"` | Wave-like distortion effect |
| Parallax | `bg_animation_type: "parallax"` | Parallax depth scrolling |

**Controlling fields:** `bg_animation_type`, `bg_animation_intensity` (0.05 - 0.5), `bg_animation_speed` (0.1 - 2.0)

### Audio Reactivity

Real-time visual changes driven by audio stem energy.

| Stem | Field Value | Intended Effect |
|------|------------|----------------|
| Vocals | `"vocals"` | Vocal energy modulates text/background |
| Drums | `"drums"` | Drum hits trigger visual effects |
| Bass | `"bass"` | Bass energy drives background changes |
| Synth | `"synth"` | Synth levels affect color/intensity |
| Energy | `"energy"` | Overall mix energy drives effects |

**Controlling field:** `reactivity` (list of stem names, e.g. `["vocals", "drums"]`)

**Prerequisite:** Requires per-frame audio energy data from `analysis.json` to be fed into the render loop.

### Custom Reveal Mode

`reveal_mode: "custom"` is an accepted value but has no implementation. Intended for user-defined word reveal behavior.

---

## Fully Implemented (Non-Renderer)

### Audio Pipeline

- Beat detection (tempo/BPM, beat times, confidence)
- Onset detection
- RMS energy (normalized 0-1)
- Spectral centroids (brightness)
- Zero crossing rate (percussive indicator)
- Per-stem energy profiles and onset counts
- Vocal onset extraction from vocal stem
- Vocal transcription via faster_whisper (word-level timestamps)
- MIDI tempo and per-instrument note extraction
- Waveform generation (100 peaks/second)

### Lyrics Pipeline

- SRT, LRC, TXT parsing with section markers
- Section type + index + tag extraction from markers (e.g. `[Verse 2, double time, female]`)
- Beat-snapped onset alignment (3-tier: MIDI > vocal stem > full mix)
- Transcription-based word alignment via SequenceMatcher
- Alignment quality scoring per line
- Syllable counting and word pace analysis
- Minimum duration enforcement (0.15s per word, 0.5s per line)

### CLI & Server

- 6 CLI commands: `init`, `analyze`, `sync`, `info`, `serve`, `render`
- 14 HTTP API endpoints (project, analysis, lyrics, structure, script, templates, etc.)
- Browser-based unified editor (`/editor`)
- Browser-based alignment review tool (`/tools/analysis/`)

### Infrastructure

- Input tier detection: Basic (audio) / Standard (+lyrics) / Enhanced (+stems) / Full (+MIDI)
- Graceful degradation for missing optional dependencies (pretty_midi, faster_whisper, ffmpeg)
- 6 visual template presets
- 4 style recipe presets
- Color presets (8 named colors)
