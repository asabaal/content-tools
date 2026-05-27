# Visual Features Implementation Plan

## Overview

Port visual features from the original pipeline (`asabaal-utils/.../lyric_video/`) into the new pipeline. The new renderer currently produces static-frame caption overlays with solid/gradient backgrounds. The goal is to add animations, text styles, audio-reactive effects, motion effects, and procedural font styles.

## Dependency

Add `opencv-python-headless` to project dependencies. Required for GaussianBlur, remap (distortions), warpAffine (transforms), dilate, and image processing.

## Baseline Benchmark

Before any changes, capture render performance:
- Command: `mvp render` with dark_moody mood on canonical song
- Metrics: wall time, frames/second, unique frames, output file size
- Record in `RENDER_BENCHMARKS.md`

## Phase 1: Animation Foundation + Text Styles (Critical)

Everything else depends on this phase. Introduces the RGBA layer pipeline that all subsequent features use.

### 1.1 `src/render/animations.py` (~200 lines)

Port from `asabaal-utils/.../text/animations.py` (249 lines). Pure math, no cv2.

**AnimationType enum** (13 types):
- FADE_IN, FADE_OUT, SLIDE_IN, SLIDE_OUT, SCALE_IN, SCALE_OUT
- ROTATE_IN, TYPEWRITER, BOUNCE_IN, ELASTIC_IN, WAVE, SHAKE, GLOW_PULSE

**AnimationEasing enum** (7 types):
- LINEAR, EASE_IN, EASE_OUT, EASE_IN_OUT, BOUNCE, ELASTIC, BACK

**AnimationState dataclass**:
- position, scale, rotation, opacity, char_progress

**Functions**:
- 7 easing functions (pure math)
- `calculate_animation_state(animation_type, progress, easing, start_pos, target_pos, amplitude) -> AnimationState`
- `interpolate_states(state1, state2, blend) -> AnimationState`

**Tests** (`tests/test_animations.py`):
- Every easing function: verify output at t=0, t=0.5, t=1.0
- Every animation type: verify state at progress=0 and progress=1
- Edge cases: progress < 0, progress > 1, interpolation at blend=0 and blend=1

### 1.2 `src/render/text_styles.py` (~400 lines)

Adapt from `asabaal-utils/.../text/professional_renderer.py` (421 lines). Uses cv2 + PIL.

**TextStyle enum** (6 styles):
- modern_bold, neon_glow, elegant_gold, hip_hop, clean_white, dramatic_red

**Multi-pass rendering pipeline** (back to front):
1. Shadow layer: render text in shadow color, cv2.GaussianBlur, alpha blend
2. Glow layer: iterative blur at increasing radii with diminishing opacity
3. Outline layer: cv2.dilate alpha channel, render in outline color
4. Fill layer: render text in fill color

**Functions**:
- `render_styled_text(text, font, style, size, ...) -> Image` — returns RGBA PIL Image
- `_render_shadow(layer, color, offset, blur_radius) -> layer`
- `_render_glow(layer, color, radius, intensity) -> layer`
- `_render_outline(layer, color, width) -> layer`
- Style config dataclass per style

**Tests** (`tests/test_text_styles.py`):
- Each style produces a valid RGBA image
- Output dimensions are reasonable (non-zero width/height)
- Glow/shadow/outline functions produce different output than input
- Edge case: empty string, single character

### 1.3 Renderer Integration (~250 lines of changes to `renderer.py`)

**Architecture change**: from direct PIL draw to RGBA layer pipeline.

```
BEFORE:  draw_bg(img) -> draw_text_at_y(img, y) -> done
AFTER:   draw_bg(img) -> render_text_to_layer() -> apply_animation(layer)
         -> apply_text_style(layer) -> composite(img, layer) -> done
```

**Changes to `renderer.py`**:
- `load()`: also load `rms_energy`, `spectral_centroids`, `beat_times` into `self.audio_features`
- New `_get_audio_at(t) -> dict`: returns `{energy, centroid, is_beat}` for timestamp
- New `_get_line_timing(line_idx) -> dict`: returns `{start, end, duration}` from synced lyrics
- New `_compute_animation_progress(t, line_idx) -> AnimationState`: uses line timing + animation_type from visual dict
- New `_render_text_layer(line, word_idx, v, y, font_size) -> Image`: renders text to RGBA layer
- New `_composite_layer(img, layer, anim_state) -> Image`: applies animation transforms (opacity, position offset, scale) and composites
- Modified `render_frame()` and `_render_text_on_bg()`: use new pipeline
- Frame caching: disable for animated sections (every frame is unique), keep for non-animated

### 1.4 Scriptgen Wiring

**`generator.py`**:
- `_build_defaults()`: add `animation_type: "fade"`, `animation_speed: 1.0`, `text_style: "modern_bold"`
- Section loop: add `text_style` to visual dict

**`rules.py`**:
- New `assign_animation(section_type, mood_name, energy, pace) -> dict`: returns `{animation_type, animation_speed}`
- Per-section animation assignment:
  - Intro: scale_in
  - Verse: fade_in
  - Chorus: bounce_in
  - Bridge: slide_in
  - Outro: fade_out
- New `assign_text_style(section_type, mood_name) -> str`: returns style name
- Per-section style assignment by mood

### Phase 1 Benchmark

After all Phase 1 changes, re-run render benchmark. Compare against baseline.

---

## Phase 2: Audio-Reactive Effects (High Priority)

Depends on Phase 1 (needs RGBA layer pipeline + _get_audio_at).

### 2.1 `src/render/audio_reactive.py` (~350 lines)

Adapt from `asabaal-utils/.../compositor.py` (853 lines, audio-reactive section).

**Effects** (6 functions):
- `apply_energy_glow(layer, energy, color, max_radius=15)` — multi-layer cv2.GaussianBlur glow, intensity ∝ energy
- `apply_color_shift(frame, centroid, energy)` — HSV hue rotation by centroid, saturation boost by energy
- `apply_beat_flash(frame, is_beat, energy)` — brightness pulse on beats: `frame * (1.3 + energy * 0.5)`
- `apply_wave_distortion(layer, energy, t)` — cv2.remap with sinusoidal displacement, amplitude ∝ energy
- `apply_chromatic_aberration(layer, energy)` — RGB channel horizontal offset: `offset = int(energy * 8)`
- `apply_energy_burst(frame, energy, center)` — radial ray pattern (cv2.line segments), triggered at energy > 0.6

**Audio feature lookup**:
- `_lookup_rms(rms_array, t, fps)` — index into rms_energy array
- `_is_near_beat(beat_times, t, window=0.05)` — check proximity to any beat

**Tests** (`tests/test_audio_reactive.py`):
- Each effect produces valid output (correct shape, no NaN/negative values)
- Energy=0 produces no change (identity)
- Energy=1.0 produces visible change
- Beat flash only activates near beat times
- Chromatic aberration offset scales with energy

### 2.2 Renderer Wiring

- In `render_frame()`, after text compositing, check `v.get("reactivity", [])`
- Map stems to effects:
  - `"energy"` → glow + brightness modulation
  - `"vocals"` → text opacity pulsing
  - `"drums"` → beat flash + camera shake
- Effects applied proportionally to energy level

### Phase 2 Benchmark

Re-run render. Compare Phase 1 vs Phase 2 timing.

---

## Phase 3: Frame-Level Motion Effects (Medium Priority)

Depends on Phase 1.

### 3.1 `src/render/frame_effects.py` (~400 lines)

Adapt from `asabaal-utils/.../effects/motion_effects.py` (650 lines) + `video_effects.py` (243 lines).

**Effects** (10 functions):
- `apply_zoom_pulse(frame, t, intensity, speed)` — cv2.warpAffine scale oscillation
- `apply_camera_shake(frame, t, intensity, seed)` — random (x,y) offset, seeded for reproducibility
- `apply_wave_distortion_frame(frame, t, intensity, speed)` — cv2.remap sinusoidal full-frame distortion
- `apply_zoom_blur(frame, t, intensity)` — multi-scale averaging at 5 scales
- `apply_color_shift_frame(frame, t, hue_shift)` — HSV hue rotation
- `apply_brightness_pulse(frame, t, speed)` — sin-based brightness oscillation
- `apply_contrast_pulse(frame, t, speed)` — alpha/beta scaling oscillation
- `apply_glitch(frame, t, intensity)` — horizontal line displacement + RGB split
- `apply_vignette_pulse(frame, t, intensity)` — dynamic vignette with pulsing radius
- `apply_motion_blur(frame, angle, intensity)` — directional kernel convolution

**Tests** (`tests/test_frame_effects.py`):
- Each effect produces same-shape output
- Intensity=0 is identity
- Reproducibility: same seed produces same shake output
- No negative or >255 values in output

### 3.2 `src/render/effect_presets.py` (~100 lines)

8 named presets combining frame effects + audio reactivity settings:
- `cinematic`: slow zoom + color shift
- `energetic`: shake + brightness pulse + beat flash
- `dreamy`: wave distortion + zoom blur
- `glitch`: digital glitch + chromatic aberration
- `minimal`: none
- `psychedelic`: color shift + wave distortion + energy burst
- `smooth`: gentle zoom pulse + vignette pulse
- `intense`: shake + zoom pulse + glitch + energy burst

### 3.3 Scriptgen + Renderer Wiring

- Read `bg_animation_type` from visual dict
- Map bg_animation_type to effect function calls
- Intensity/speed from `bg_animation_intensity` / `bg_animation_speed`

### Phase 3 Benchmark

Re-run render. Compare Phase 2 vs Phase 3 timing.

---

## Phase 4: Procedural Font Styles + Background Video (Lower Priority)

Depends on Phase 1.

### 4.1 `src/render/font_styles.py` (~500 lines)

Port from `asabaal-utils/.../text/font_generator.py` (581 lines).

**9 procedural styles**: neon, graffiti, chrome, fire, ice, gold, hologram, matrix, basic

Each renders text to RGBA layer then applies style-specific effects:
- Multi-layer glow (neon, matrix, hologram)
- Gradient fills (graffiti, chrome, fire, ice, gold)
- Wave distortion (fire, hologram)
- Random effects (matrix artifacts, hologram scan lines)

**Tests** (`tests/test_font_styles.py`):
- Each style produces valid RGBA image
- All 9 styles produce visually different output
- Edge cases: empty string, very long string

### 4.2 `src/render/background_video.py` (~300 lines)

- Load background video via cv2.VideoCapture
- Extract frame at timestamp with seeking
- Directory mode: load multiple clips, beat-synced switching
- Resize to output resolution

**Tests** (`tests/test_background_video.py`):
- Mock VideoCapture for unit tests
- Frame extraction at various timestamps
- Beat switching logic

### Phase 4 Benchmark

Re-run render. Compare Phase 3 vs Phase 4 timing.

---

## Test Coverage Targets

| File | Target | Test File |
|---|---|---|
| `src/render/animations.py` | 100% | `tests/test_animations.py` |
| `src/render/text_styles.py` | 100% | `tests/test_text_styles.py` |
| `src/render/audio_reactive.py` | 100% | `tests/test_audio_reactive.py` |
| `src/render/frame_effects.py` | 100% | `tests/test_frame_effects.py` |
| `src/render/font_styles.py` | 100% | `tests/test_font_styles.py` |
| `src/render/background_video.py` | 100% | `tests/test_background_video.py` |
| `src/render/effect_presets.py` | 100% | `tests/test_frame_effects.py` |
| New code in `renderer.py` | 100% | existing `tests/test_render.py` + new cases |
| New code in `rules.py` | 100% | `tests/test_word_positions.py` + new cases |
| New code in `generator.py` | 100% | existing tests + new cases |

All 570+ existing tests must continue passing throughout.

## Benchmark Tracking

Stored in `RENDER_BENCHMARKS.md` with columns:
- Phase, wall time, fps, unique frames, output size, vs baseline %
