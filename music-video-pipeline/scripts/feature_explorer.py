#!/usr/bin/env python3
"""MVP Feature Explorer - generates a visual gallery of all render features.

Renders real frames from the canonical song using VideoRenderer, then
assembles a static HTML gallery page with dark-themed card layout.

Usage:
    python scripts/feature_explorer.py              # generate all (skips existing)
    python scripts/feature_explorer.py --force      # regenerate everything
    python scripts/feature_explorer.py --force tmpl_ grad_   # specific prefixes
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image

PROJECT_DIR = ROOT / "data" / "i-never-asked-to-be-queer"
ASSETS_DIR = ROOT / "explorer_assets"
STATIC_DIR = ASSETS_DIR / "static"
VIDEO_DIR = ASSETS_DIR / "video"

RENDER_W, RENDER_H = 1280, 720
FPS = 30

SNAPSHOT_T = 3.5
VERSE_SNAPSHOT_T = 23.5
CLIP_START = 1.0
CLIP_END = 6.0

BASE_DEFAULTS = {
    "background_type": "solid",
    "background_color": "#1a1a2e",
    "gradient_direction": "vertical_top_bottom",
    "texture_type": "none",
    "texture_opacity": 0.15,
    "texture_blend_mode": "multiply",
    "text_auto_contrast": True,
    "font_size": 48,
    "animation_type": "fade",
    "animation_speed": 1.0,
    "reveal_mode": "progressive",
    "reveal_words": 1,
    "reveal_slide": False,
    "reactivity": ["vocals"],
}

BASE_CAPTION = {
    "font_family": 0,
    "highlight_color": "#4cc9f0",
    "text_position": "center",
    "letter_spacing": 1,
    "text_shadow": False,
    "text_shadow_color": "#000000",
    "outline": False,
    "outline_color": "#000000",
    "outline_width": 2,
}

TEMPLATES: Dict[str, dict] = {}
for _tf in sorted((ROOT / "templates").glob("*.json")):
    TEMPLATES[_tf.stem] = json.loads(_tf.read_text())

COLOR_PRESETS = {
    "Blue": "#4A90E2",
    "Warm": "#E67E22",
    "Teal": "#27AE60",
    "Purple": "#8E44AD",
    "Red": "#C0392B",
    "Navy": "#1A1A2E",
    "Charcoal": "#2D2D2D",
    "Cream": "#F5E6CC",
}

GRADIENT_DIRECTIONS = [
    "vertical_top_bottom",
    "vertical_bottom_top",
    "horizontal_left_right",
    "horizontal_right_left",
    "diagonal_tl_br",
    "diagonal_tr_bl",
    "radial_center",
    "radial_top",
    "radial_bottom",
    "radial_tl",
    "radial_br",
    "conic",
    "conic_0.8",
    "cross",
    "diamond",
    "spiral",
    "bands",
    "dual_spot_0.3_0.3_0.7_0.7",
    "dual_spot_0.3_0.4_0.7_0.6",
    "angle_0",
    "angle_30",
    "angle_45",
    "angle_90",
    "angle_135",
]

GRAD_DIR_SHORT = {
    "vertical_top_bottom": "vert_tb",
    "vertical_bottom_top": "vert_bt",
    "horizontal_left_right": "horiz_lr",
    "horizontal_right_left": "horiz_rl",
    "diagonal_tl_br": "diag_tlbr",
    "diagonal_tr_bl": "diag_trbl",
    "radial_center": "rad_ctr",
    "radial_top": "rad_top",
    "radial_bottom": "rad_bot",
    "radial_tl": "rad_tl",
    "radial_br": "rad_br",
    "conic": "conic",
    "conic_0.8": "conic_08",
    "cross": "cross",
    "diamond": "diamond",
    "spiral": "spiral",
    "bands": "bands",
    "dual_spot_0.3_0.3_0.7_0.7": "dual_sym",
    "dual_spot_0.3_0.4_0.7_0.6": "dual_asym",
    "angle_0": "ang_0",
    "angle_30": "ang_30",
    "angle_45": "ang_45",
    "angle_90": "ang_90",
    "angle_135": "ang_135",
}

TEXTURES = [
    "none", "noise_fine", "noise_coarse", "grain_film",
    "paper_subtle", "vignette_soft", "vignette_heavy",
]

OPACITY_SERIES = [0.1, 0.3, 0.5, 0.8]

RECIPES = {
    "Cinematic": {
        "background_type": "gradient",
        "background_color": "#0a0a2e",
        "gradient_colors": ["#0a0a2e", "#1a1a4e"],
        "gradient_direction": "diagonal_tl_br",
        "texture_type": "vignette_heavy",
        "texture_opacity": 0.5,
    },
    "Editorial": {
        "background_type": "solid",
        "background_color": "#F5E6CC",
        "texture_type": "paper_subtle",
        "texture_opacity": 0.2,
    },
    "Ambient Loop": {
        "background_type": "gradient",
        "background_color": "#1a1a2e",
        "gradient_colors": ["#1a1a2e", "#4A90E2", "#8E44AD"],
        "gradient_direction": "radial_center",
        "texture_type": "none",
    },
    "High Contrast": {
        "background_type": "solid",
        "background_color": "#C0392B",
        "texture_type": "grain_film",
        "texture_opacity": 0.2,
    },
}

GROUP_LABELS = {
    "types": "Texture Types",
    "opacity": "Opacity Series (grain_film)",
    "blend": "Blend Mode Comparison (noise_coarse)",
    "sizes": "Font Sizes",
    "positions": "Text Positions",
    "shadow": "Text Shadow",
    "outline": "Text Outline",
    "contrast": "Auto Contrast",
}


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _should_skip(path: Path, force_prefixes: List[str] | None = None) -> bool:
    if not path.exists():
        return False
    if force_prefixes is None:
        return True
    for pfx in force_prefixes:
        if path.name.startswith(pfx):
            return False
    return True


def _make_renderer(w: int = RENDER_W, h: int = RENDER_H) -> Any:
    from render.renderer import VideoRenderer
    r = VideoRenderer(PROJECT_DIR, width=w, height=h)
    r.load()
    return r


def _override(r: Any, defaults: dict, caption: dict | None = None):
    orig_d = dict(r.defaults)
    orig_sd = r.script.get("defaults", {})
    orig_secs = list(r.script.get("sections", []))
    orig_cs = dict(r.caption_style)

    r.defaults = defaults
    r.script["defaults"] = defaults
    r.script["sections"] = []
    if caption is not None:
        r.caption_style = {**orig_cs, **caption}
        r.script["caption_style"] = r.caption_style

    def restore():
        r.defaults = orig_d
        r.script["defaults"] = orig_sd
        r.script["sections"] = orig_secs
        r.caption_style = orig_cs
        r.script["caption_style"] = orig_cs

    return restore


def _render_frame(
    r: Any,
    defaults: dict,
    caption: dict | None = None,
    t: float = SNAPSHOT_T,
) -> Image.Image:
    restore = _override(r, defaults, caption)
    try:
        return r.render_frame(t)
    finally:
        restore()


def _render_clip(
    r: Any,
    defaults: dict,
    caption: dict | None,
    t_start: float,
    t_end: float,
    out_path: Path,
    fps: int = FPS,
) -> Path:
    from render.encoder import VideoEncoder
    out_path.parent.mkdir(parents=True, exist_ok=True)
    restore = _override(r, defaults, caption)
    total = int((t_end - t_start) * fps) + 1
    prev_bytes: bytes | None = None
    prev_key: tuple | None = None
    has_anim = (
        defaults.get("animation_type", "none") != "none"
        or bool(defaults.get("bg_animation_preset", ""))
        or defaults.get("animation_type", "") in ("wave", "shake", "glow_pulse")
    )
    try:
        with VideoEncoder(out_path, r.width, r.height, fps) as enc:
            for i in range(total):
                t = t_start + i / fps
                li, wi = r._find_active_word(t)
                key = (li, wi) if not has_anim else (li, wi, i)
                if key == prev_key and prev_bytes is not None:
                    enc.write_frame(prev_bytes)
                else:
                    fb = r.render_frame(t).tobytes()
                    enc.write_frame(fb)
                    prev_bytes = fb
                    prev_key = key
    finally:
        restore()
    return out_path


def _save(img: Image.Image, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def _gen_variant(
    r: Any,
    defaults: dict,
    stem: str,
    force: List[str],
    caption: dict | None = None,
    t_snap: float = SNAPSHOT_T,
    t_start: float = CLIP_START,
    t_end: float = CLIP_END,
) -> tuple[str, str | None]:
    """Generate a poster PNG + video clip for a single variant."""
    png_path = STATIC_DIR / f"{stem}.png"
    mp4_path = VIDEO_DIR / f"{stem}.mp4"

    if not _should_skip(png_path, force):
        _save(_render_frame(r, defaults, caption, t_snap), png_path)

    has_video = mp4_path.exists()
    try:
        if not _should_skip(mp4_path, force):
            _render_clip(r, defaults, caption, t_start, t_end, mp4_path)
            has_video = True
    except Exception:
        pass

    return png_path.name, mp4_path.name if has_video else None


def _json_snippet(d: dict) -> str:
    return json.dumps(d, indent=2)


# ---------------------------------------------------------------------------
# Section generators
# ---------------------------------------------------------------------------

def gen_01_default(r: Any, force: List[str]) -> dict:
    defaults = {**BASE_DEFAULTS, **TEMPLATES["default"]}
    img, vid = _gen_variant(r, defaults, "default", force)
    print(f"  [01] default")
    return {
        "id": "01", "number": "01", "title": "Default Render",
        "desc": "Out of the box with default template settings. No customization applied.",
        "cards": [{"img": img, "video": vid, "label": "Default", "config": TEMPLATES["default"]}],
    }


def gen_02_templates(r: Any, force: List[str]) -> dict:
    cards = []
    for tname, tvals in TEMPLATES.items():
        stem = f"tmpl_{tname}"
        defaults = {**BASE_DEFAULTS, **tvals}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [02] {tname}")
        cards.append({"img": img, "video": vid, "label": tname.capitalize(), "config": tvals})
    return {
        "id": "02", "number": "02", "title": "Style Templates",
        "desc": "The six built-in visual templates, each combining background, texture, and animation settings.",
        "cards": cards,
    }


def gen_03_colors(r: Any, force: List[str]) -> dict:
    cards = []
    for cname, chex in COLOR_PRESETS.items():
        stem = f"color_{cname.lower()}"
        defaults = {**BASE_DEFAULTS, "background_type": "solid", "background_color": chex, "texture_type": "none"}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [03] {cname}")
        cards.append({"img": img, "video": vid, "label": f"{cname} ({chex})", "config": {"background_color": chex}})
    return {
        "id": "03", "number": "03", "title": "Background Colors",
        "desc": "Solid background colors with auto-contrast text. Notice cream (#F5E6CC) gets dark text while navy (#1A1A2E) gets light text automatically.",
        "cards": cards,
    }


def gen_04_gradients(r: Any, force: List[str]) -> dict:
    cards = []
    two_color = ["#4A90E2", "#C0392B"]
    five_color = ["#0a0a2e", "#4A90E2", "#8E44AD", "#C0392B", "#1a1a4e"]
    geometric = {
        "conic", "conic_0.8", "cross", "diamond", "spiral", "bands",
        "dual_spot_0.3_0.3_0.7_0.7", "dual_spot_0.3_0.4_0.7_0.6",
    }
    for direction in GRADIENT_DIRECTIONS:
        short = GRAD_DIR_SHORT[direction]
        stem = f"grad_{short}"
        if direction in geometric:
            colors = five_color
        else:
            colors = two_color
        defaults = {**BASE_DEFAULTS, "background_type": "gradient", "gradient_colors": colors, "texture_type": "none", "gradient_direction": direction}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [04] {direction}")
        cards.append({"img": img, "video": vid, "label": direction.replace("_", " "), "config": {"gradient_direction": direction}})
    return {
        "id": "04", "number": "04", "title": "Gradient Geometries",
        "desc": "All gradient geometries: linear, radial, conic, and geometric patterns. Geometric types use 5-color palettes for clarity.",
        "cards": cards,
    }


def gen_05_multistop(r: Any, force: List[str]) -> dict:
    cards = []
    stops = [
        ("2-color", ["#4A90E2", "#C0392B"]),
        ("3-color", ["#4A90E2", "#8E44AD", "#C0392B"]),
        ("4-color", ["#4A90E2", "#27AE60", "#8E44AD", "#C0392B"]),
    ]
    for label, colors in stops:
        stem = f"gradstop_{len(colors)}"
        defaults = {**BASE_DEFAULTS, "background_type": "gradient", "gradient_colors": colors, "gradient_direction": "diagonal_tl_br", "texture_type": "none"}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [05] {label}")
        cards.append({"img": img, "video": vid, "label": label, "config": {"gradient_colors": colors}})
    return {
        "id": "05", "number": "05", "title": "Gradient Multi-Stop",
        "desc": "Gradients with 2, 3, and 4 color stops on a diagonal. Colors interpolate smoothly across the frame.",
        "cards": cards,
    }


def gen_06_textures(r: Any, force: List[str]) -> dict:
    cards = []

    for tex in TEXTURES:
        stem = f"tex_{tex}"
        defaults = {**BASE_DEFAULTS, "texture_type": tex, "texture_opacity": 0.3}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [06] texture: {tex}")
        cards.append({"img": img, "video": vid, "label": tex.replace("_", " ").title(), "config": {"texture_type": tex, "texture_opacity": 0.3}, "group": "types"})

    for op in OPACITY_SERIES:
        stem = f"texop_{op}"
        defaults = {**BASE_DEFAULTS, "texture_type": "grain_film", "texture_opacity": op}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [06] opacity: {op}")
        cards.append({"img": img, "video": vid, "label": f"grain_film @ {op}", "config": {"texture_type": "grain_film", "texture_opacity": op}, "group": "opacity"})

    for blend in ["normal", "multiply"]:
        stem = f"texbl_{blend}"
        defaults = {**BASE_DEFAULTS, "texture_type": "noise_coarse", "texture_opacity": 0.5, "texture_blend_mode": blend}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [06] blend: {blend}")
        cards.append({"img": img, "video": vid, "label": f"blend: {blend}", "config": {"texture_blend_mode": blend, "texture_opacity": 0.5}, "group": "blend"})

    return {
        "id": "06", "number": "06", "title": "Texture Overlays",
        "desc": "Seven texture types, an opacity series using grain_film, and blend mode comparison using noise_coarse.",
        "cards": cards, "subgroups": True,
    }


def gen_07_reveal_modes(r: Any, force: List[str]) -> dict:
    cards = []
    modes = [
        ("progressive", "progressive", "Words appear one-by-one, highlighted as active"),
        ("karaoke", "karaoke", "All words shown, active word highlighted"),
        ("linebyline", "line-by-line", "Full line appears at once"),
    ]
    for key, mode, desc in modes:
        stem = f"reveal_{key}"
        defaults = {**BASE_DEFAULTS, "reveal_mode": mode}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [07] {mode}")
        cards.append({
            "img": img, "video": vid,
            "label": mode,
            "desc": desc,
            "config": {"reveal_mode": mode},
        })

    return {
        "id": "07", "number": "07", "title": "Reveal Modes",
        "desc": "How lyrics appear during playback. Each card has a static snapshot and a 5-second video clip.",
        "cards": cards, "has_video": True,
    }


def gen_08_text_styling(r: Any, force: List[str]) -> dict:
    cards = []

    for size in [32, 48, 64, 80]:
        stem = f"txt_size_{size}"
        defaults = {**BASE_DEFAULTS, "font_size": size}
        img, vid = _gen_variant(r, defaults, stem, force, t_snap=VERSE_SNAPSHOT_T)
        print(f"  [08] size: {size}")
        cards.append({"img": img, "video": vid, "label": f"font_size: {size}", "config": {"font_size": size}, "group": "sizes"})

    for pos in ["top", "center", "bottom"]:
        stem = f"txt_pos_{pos}"
        caption = {**BASE_CAPTION, "text_position": pos}
        img, vid = _gen_variant(r, BASE_DEFAULTS, stem, force, caption=caption)
        print(f"  [08] pos: {pos}")
        cards.append({"img": img, "video": vid, "label": f"position: {pos}", "config": {"caption_style": {"text_position": pos}}, "group": "positions"})

    for on in [False, True]:
        tag = "on" if on else "off"
        stem = f"txt_shadow_{tag}"
        caption = {**BASE_CAPTION, "text_shadow": on}
        img, vid = _gen_variant(r, BASE_DEFAULTS, stem, force, caption=caption)
        print(f"  [08] shadow: {tag}")
        cards.append({"img": img, "video": vid, "label": f"shadow: {tag}", "config": {"text_shadow": on}, "group": "shadow"})

    for on in [False, True]:
        tag = "on" if on else "off"
        stem = f"txt_outline_{tag}"
        caption = {**BASE_CAPTION, "outline": on, "outline_width": 2}
        img, vid = _gen_variant(r, BASE_DEFAULTS, stem, force, caption=caption)
        print(f"  [08] outline: {tag}")
        cards.append({"img": img, "video": vid, "label": f"outline: {tag}", "config": {"outline": on, "outline_width": 2}, "group": "outline"})

    for on in [True, False]:
        tag = "on" if on else "off"
        stem = f"txt_autocontrast_{tag}"
        if on:
            defaults = BASE_DEFAULTS
            cfg = {"text_auto_contrast": True}
        else:
            defaults = {**BASE_DEFAULTS, "text_auto_contrast": False, "text_color": "#ff6b6b"}
            cfg = {"text_auto_contrast": False, "text_color": "#ff6b6b"}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [08] autocontrast: {tag}")
        cards.append({"img": img, "video": vid, "label": f"auto_contrast: {tag}", "config": cfg, "group": "contrast"})

    return {
        "id": "08", "number": "08", "title": "Text Styling",
        "desc": "Font sizes (shown on a longer verse line), text positions, shadow, outline, and auto-contrast toggle.",
        "cards": cards, "subgroups": True,
    }


def gen_09_recipes(r: Any, force: List[str]) -> dict:
    cards = []
    for rname, rconfig in RECIPES.items():
        safe = rname.lower().replace(" ", "_")
        stem = f"recipe_{safe}"
        defaults = {**BASE_DEFAULTS, **rconfig}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [09] {rname}")
        cards.append({"img": img, "video": vid, "label": rname, "config": rconfig})
    return {
        "id": "09", "number": "09", "title": "Style Recipes",
        "desc": "Named combinations of settings that produce distinct visual moods.",
        "cards": cards,
    }


ANIMATION_TYPES = [
    "fade_in", "fade_out", "slide_in", "slide_out",
    "scale_in", "scale_out", "rotate_in",
    "typewriter", "bounce_in", "elastic_in",
    "wave", "shake", "glow_pulse",
]

ANIMATION_LABELS = {
    "fade_in": "Fade In", "fade_out": "Fade Out",
    "slide_in": "Slide In", "slide_out": "Slide Out",
    "scale_in": "Scale In", "scale_out": "Scale Out",
    "rotate_in": "Rotate In",
    "typewriter": "Typewriter", "bounce_in": "Bounce In",
    "elastic_in": "Elastic In",
    "wave": "Wave", "shake": "Shake", "glow_pulse": "Glow Pulse",
}


def gen_10_animations(r: Any, force: List[str]) -> dict:
    cards = []
    for anim in ANIMATION_TYPES:
        stem = f"anim_{anim}"
        defaults = {**BASE_DEFAULTS, "animation_type": anim, "animation_speed": 1.0}
        img, vid = _gen_variant(r, defaults, stem, force)
        label = ANIMATION_LABELS.get(anim, anim)
        print(f"  [10] animation: {anim}")
        cards.append({
            "img": img, "video": vid, "label": label,
            "config": {"animation_type": anim, "animation_speed": 1.0},
        })
    return {
        "id": "10", "number": "10", "title": "Text Animations",
        "desc": "13 animation types controlling how lyrics enter and exit the frame. Each card shows a 5-second clip with the animation applied.",
        "cards": cards, "has_video": True,
    }


def gen_11_text_styles(r: Any, force: List[str]) -> dict:
    cards = []
    text_style_configs = [
        ("modern_bold", "Modern Bold", {}),
        ("neon_glow", "Neon Glow", {}),
        ("elegant_gold", "Elegant Gold", {}),
        ("hip_hop", "Hip Hop", {}),
        ("clean_white", "Clean White", {}),
        ("dramatic_red", "Dramatic Red", {}),
    ]
    for style_name, label, _ in text_style_configs:
        stem = f"tstyle_{style_name}"
        defaults = {**BASE_DEFAULTS, "text_style": style_name}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [11] text_style: {style_name}")
        cards.append({
            "img": img, "video": vid, "label": label,
            "config": {"text_style": style_name},
        })
    return {
        "id": "11", "number": "11", "title": "Professional Text Styles",
        "desc": "6 multi-pass text rendering styles with shadow, glow, outline, and fill layers powered by OpenCV.",
        "cards": cards, "has_video": True,
    }


FONT_STYLES = [
    ("neon", "Neon", "Multi-layer magenta/purple glow with bright white core"),
    ("graffiti", "Graffiti", "Red-to-yellow gradient with black outline and shadow"),
    ("chrome", "Chrome", "Metallic silver gradient with horizontal highlight bands"),
    ("fire", "Fire", "Red-orange-yellow flame layers with wave distortion"),
    ("ice", "Ice", "Blue-to-white gradient with sparkle highlights"),
    ("gold", "Gold", "Sinusoidal gold gradient with outer golden glow"),
    ("hologram", "Hologram", "Cyan fill with scan lines and transparency noise"),
    ("matrix", "Matrix", "Green vertical gradient with random bright artifacts"),
    ("basic", "Basic Rainbow", "Horizontal rainbow gradient with magenta glow"),
]


def gen_12_font_styles(r: Any, force: List[str]) -> dict:
    cards = []
    for style_name, label, desc in FONT_STYLES:
        stem = f"fstyle_{style_name}"
        defaults = {**BASE_DEFAULTS, "font_style": style_name}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [12] font_style: {style_name}")
        cards.append({
            "img": img, "video": vid, "label": label, "desc": desc,
            "config": {"font_style": style_name},
        })
    return {
        "id": "12", "number": "12", "title": "Procedural Font Styles",
        "desc": "9 algorithmically-generated text styles with gradients, glow layers, wave distortion, and special effects.",
        "cards": cards, "has_video": True,
    }


REACTIVITY_CONFIGS = [
    ("react_energy", "Energy", ["energy"], "Energy-driven glow and color shift"),
    ("react_drums", "Drums", ["drums"], "Beat flash and energy burst on hits"),
    ("react_vocals", "Vocals", ["vocals"], "Chromatic aberration on vocal energy"),
    ("react_all", "Full Mix", ["energy", "drums", "vocals"], "All audio-reactive effects combined"),
]


def gen_13_audio_reactive(r: Any, force: List[str]) -> dict:
    cards = []
    for stem, label, reactivity, desc in REACTIVITY_CONFIGS:
        defaults = {**BASE_DEFAULTS, "reactivity": reactivity, "animation_type": "fade_in"}
        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [13] reactivity: {label}")
        cards.append({
            "img": img, "video": vid, "label": label, "desc": desc,
            "config": {"reactivity": reactivity, "animation_type": "fade_in"},
        })
    return {
        "id": "13", "number": "13", "title": "Audio-Reactive Effects",
        "desc": "Real-time audio-driven visual effects using RMS energy, spectral centroid, and beat detection from analysis.json.",
        "cards": cards, "has_video": True,
    }


MOTION_PRESETS = [
    "cinematic", "energetic", "dreamy", "glitch",
    "minimal", "psychedelic", "smooth", "intense",
]

PRESET_DESCS = {
    "cinematic": "Slow zoom, subtle color shift, vignette pulse",
    "energetic": "Camera shake, brightness pulse, beat-synced",
    "dreamy": "Wave distortion, zoom blur, soft vignette",
    "glitch": "Digital glitch, contrast pulse, line displacement",
    "minimal": "No effects, clean output",
    "psychedelic": "Rainbow color shift, heavy wave distortion",
    "smooth": "Gentle zoom, soft vignette",
    "intense": "Heavy shake, rapid zoom, glitch, all stems",
}


def gen_14_motion_presets(r: Any, force: List[str]) -> dict:
    cards = []
    for preset_name in MOTION_PRESETS:
        stem = f"mpreset_{preset_name}"
        defaults = {**BASE_DEFAULTS, "bg_animation_preset": preset_name, "animation_type": "fade_in"}
        img, vid = _gen_variant(r, defaults, stem, force)
        desc = PRESET_DESCS.get(preset_name, "")
        print(f"  [14] preset: {preset_name}")
        cards.append({
            "img": img, "video": vid, "label": preset_name.capitalize(),
            "desc": desc,
            "config": {"bg_animation_preset": preset_name, "animation_type": "fade_in"},
        })
    return {
        "id": "14", "number": "14", "title": "Motion Effect Presets",
        "desc": "8 named presets combining frame-level motion effects with audio reactivity settings, assigned automatically by section type and mood.",
        "cards": cards, "has_video": True,
    }


MOOD_RENDERS = [
    ("dark_moody", "Dark Moody", "Neon font, cinematic/dreamy presets, fade animations"),
    ("bright_poppy", "Bright Poppy", "Graffiti/chrome font, energetic presets, scale animations"),
    ("warm_intimate", "Warm Intimate", "Gold font, smooth presets, gentle fade animations"),
    ("cool_ethereal", "Cool Ethereal", "Ice/hologram font, dreamy presets, wave distortion"),
    ("high_energy", "High Energy", "Fire font, intense presets, elastic/bounce animations"),
]


def gen_15_mood_renders(r: Any, force: List[str]) -> dict:
    cards = []
    for mood_id, label, desc in MOOD_RENDERS:
        stem = f"mood_{mood_id}"
        from scriptgen.generator import ScriptGenerator
        from scriptgen.moods import MOODS

        mood = MOODS.get(mood_id)
        if mood is None:
            continue

        defaults = {**BASE_DEFAULTS, "animation_type": "fade_in", "animation_speed": 1.0}
        if mood_id == "dark_moody":
            defaults.update({"background_type": "gradient", "background_color": "#1a1a2e", "gradient_colors": ["#1a1a2e", "#16213e"]})
        elif mood_id == "bright_poppy":
            defaults.update({"background_type": "gradient", "background_color": "#E67E22", "gradient_colors": ["#E67E22", "#C0392B"]})
        elif mood_id == "warm_intimate":
            defaults.update({"background_type": "gradient", "background_color": "#8B4513", "gradient_colors": ["#8B4513", "#D2691E"]})
        elif mood_id == "cool_ethereal":
            defaults.update({"background_type": "gradient", "background_color": "#1a1a4e", "gradient_colors": ["#1a1a4e", "#4A90E2"]})
        elif mood_id == "high_energy":
            defaults.update({"background_type": "gradient", "background_color": "#C0392B", "gradient_colors": ["#C0392B", "#8E44AD"]})

        defaults["reactivity"] = ["energy", "vocals"]
        defaults["bg_animation_preset"] = "cinematic" if mood_id in ("warm_intimate", "cool_ethereal") else "energetic"

        img, vid = _gen_variant(r, defaults, stem, force)
        print(f"  [15] mood: {mood_id}")
        cards.append({
            "img": img, "video": vid, "label": label, "desc": desc,
            "config": {"mood": mood_id, "bg_animation_preset": defaults["bg_animation_preset"]},
        })
    return {
        "id": "15", "number": "15", "title": "Mood Compositions",
        "desc": "Full mood-driven renders combining font styles, animation types, motion presets, and audio reactivity into cohesive visual themes.",
        "cards": cards, "has_video": True,
    }


def gen_16_coming_soon() -> dict:
    return {
        "id": "16", "number": "16", "title": "Coming Soon",
        "desc": "Features defined but not yet fully integrated into the explorer pipeline.",
        "cards": [
            {"info": True, "title": "Background Video", "desc": "Load MP4/image backgrounds with beat-synced clip switching. Supports video files and image directories with automatic format detection.", "fields": "background_video (path), beat-synced switching"},
            {"info": True, "title": "Custom Reveal Mode", "desc": "A fully customizable reveal mode (reveal_mode: 'custom') with user-defined behavior for how lyrics are shown.", "fields": "reveal_mode: 'custom'"},
            {"info": True, "title": "GPU Compositing", "desc": "CUDA-accelerated glow, blur, and remap operations for real-time preview and faster rendering on supported hardware.", "fields": "gpu compositing toggle"},
        ],
    }


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

def _card_html(card: dict) -> str:
    if card.get("info"):
        return (
            '<div class="info-card">'
            f'<h4>{card["title"]}</h4>'
            f'<p>{card["desc"]}</p>'
            f'<div class="field-names">Fields: <code>{card["fields"]}</code></div>'
            '</div>'
        )

    config_str = _json_snippet(card["config"])
    desc_html = f'<p class="card-desc">{card["desc"]}</p>' if card.get("desc") else ""

    if card.get("video"):
        snap_rel = f"explorer_assets/static/{card['img']}"
        vid_rel = f"explorer_assets/video/{card['video']}"
        return (
            '<div class="card video-card">'
            '<div class="card-preview">'
            f'<video autoplay loop muted playsinline poster="{snap_rel}">'
            f'<source src="{vid_rel}" type="video/mp4">'
            '</video>'
            '</div>'
            '<div class="card-body">'
            f'<div class="card-label">{card["label"]}</div>'
            f'{desc_html}'
            f'<details><summary>Config</summary><pre><code>{config_str}</code></pre></details>'
            '</div></div>'
        )

    img_rel = f"explorer_assets/static/{card['img']}"
    return (
        '<div class="card">'
        '<div class="card-preview">'
        f'<img src="{img_rel}" alt="{card["label"]}" loading="lazy">'
        '</div>'
        '<div class="card-body">'
        f'<div class="card-label">{card["label"]}</div>'
        f'<details><summary>Config</summary><pre><code>{config_str}</code></pre></details>'
        '</div></div>'
    )


def build_html(sections: list[dict]) -> str:
    sidebar_links = ""
    for sec in sections:
        sidebar_links += (
            f'<a href="#sec-{sec["id"]}" data-section="sec-{sec["id"]}">'
            f'{sec["number"]} {sec["title"]}</a>\n'
        )

    main_html = ""
    for sec in sections:
        cards_html = ""
        current_group = None
        for card in sec.get("cards", []):
            if "group" in card and card["group"] != current_group:
                current_group = card["group"]
                if current_group in GROUP_LABELS:
                    cards_html += f'<h3 class="subgroup-header">{GROUP_LABELS[current_group]}</h3>\n'
            cards_html += _card_html(card) + "\n"

        main_html += (
            f'<section id="sec-{sec["id"]}" class="gallery-section">\n'
            f'<h2>{sec["number"]} &middot; {sec["title"]}</h2>\n'
            f'<p class="section-desc">{sec["desc"]}</p>\n'
            f'<div class="card-grid">\n{cards_html}</div>\n'
            f'</section>\n\n'
        )

    generated = time.strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MVP Feature Explorer</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: #0d1117;
    color: #e6edf3;
    line-height: 1.5;
}}
.topbar {{
    position: fixed; top: 0; left: 0; right: 0;
    height: 56px;
    background: #010409;
    border-bottom: 1px solid #30363d;
    display: flex; align-items: center;
    padding: 0 24px;
    font-size: 18px; font-weight: 600;
    z-index: 100;
    color: #e6edf3;
}}
.sidebar {{
    position: fixed; top: 56px; left: 0; bottom: 0;
    width: 240px;
    background: #010409;
    border-right: 1px solid #30363d;
    padding: 16px 0;
    overflow-y: auto;
    z-index: 50;
}}
.sidebar a {{
    display: block;
    padding: 8px 20px;
    color: #8b949e;
    text-decoration: none;
    font-size: 13px;
    border-left: 3px solid transparent;
    transition: color 0.15s, border-color 0.15s, background 0.15s;
}}
.sidebar a:hover, .sidebar a.active {{
    color: #e6edf3;
    border-left-color: #4cc9f0;
    background: rgba(76, 201, 240, 0.05);
}}
.main-content {{
    margin-left: 240px;
    margin-top: 56px;
    padding: 40px;
    max-width: 1400px;
}}
.gallery-section {{
    margin-bottom: 64px;
}}
.gallery-section h2 {{
    font-size: 24px;
    margin-bottom: 8px;
    padding-bottom: 12px;
    border-bottom: 1px solid #30363d;
}}
.section-desc {{
    color: #8b949e;
    margin-bottom: 24px;
    font-size: 14px;
    max-width: 700px;
}}
.subgroup-header {{
    font-size: 16px;
    color: #8b949e;
    margin: 32px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px dashed #30363d;
    grid-column: 1 / -1;
}}
.card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 20px;
    align-items: start;
}}
.card {{
    background: #161b22;
    border-radius: 8px;
    border: 1px solid #30363d;
    overflow: hidden;
    transition: border-color 0.15s;
}}
.card:hover {{
    border-color: #4cc9f0;
}}
.card-preview {{
    position: relative;
    width: 100%;
    aspect-ratio: 16/9;
    overflow: hidden;
    background: #0d1117;
}}
.card-preview img, .card-preview video {{
    width: 100%; height: 100%;
    object-fit: cover;
    display: block;
}}
.card-body {{
    padding: 12px 16px;
}}
.card-label {{
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 4px;
}}
.card-desc {{
    font-size: 12px;
    color: #8b949e;
    margin-bottom: 8px;
}}
details {{
    margin-top: 8px;
}}
summary {{
    cursor: pointer;
    font-size: 12px;
    color: #4cc9f0;
    user-select: none;
}}
details pre {{
    margin-top: 8px;
    padding: 8px;
    background: #0d1117;
    border-radius: 4px;
    font-size: 11px;
    overflow-x: auto;
    color: #e6edf3;
}}
.info-card {{
    background: #161b22;
    border-left: 4px solid #4cc9f0;
    border-radius: 0 8px 8px 0;
    padding: 16px 20px;
    grid-column: 1 / -1;
}}
.info-card h4 {{
    margin-bottom: 4px;
    color: #4cc9f0;
}}
.info-card p {{
    color: #8b949e;
    font-size: 14px;
    margin-bottom: 8px;
}}
.info-card .field-names {{
    font-size: 12px;
    color: #8b949e;
}}
.info-card .field-names code {{
    color: #e6edf3;
    background: #0d1117;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
}}
.footer {{
    margin-top: 64px;
    padding-top: 16px;
    border-top: 1px solid #30363d;
    color: #484f58;
    font-size: 12px;
}}
@media (max-width: 900px) {{
    .sidebar {{ display: none; }}
    .main-content {{ margin-left: 0; padding: 24px; }}
    .card-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<div class="topbar">MVP Feature Explorer</div>
<nav class="sidebar">
{sidebar_links}
</nav>
<main class="main-content">
{main_html}
<div class="footer">Generated {generated} by <code>scripts/feature_explorer.py</code></div>
</main>
<script>
const links = document.querySelectorAll('.sidebar a');
const sections = document.querySelectorAll('.gallery-section');
const observer = new IntersectionObserver((entries) => {{
    entries.forEach(entry => {{
        if (entry.isIntersecting) {{
            const id = entry.target.id;
            links.forEach(link => {{
                link.classList.toggle('active', link.getAttribute('href') === '#' + id);
            }});
        }}
    }});
}}, {{ rootMargin: '-80px 0px -70% 0px' }});
sections.forEach(s => observer.observe(s));
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="MVP Feature Explorer")
    parser.add_argument("--force", nargs="*", default=None,
                        help="Filename prefixes to force-regenerate (default: skip existing)")
    parser.add_argument("--width", type=int, default=RENDER_W)
    parser.add_argument("--height", type=int, default=RENDER_H)
    args = parser.parse_args()

    force = args.force if args.force is not None else []

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print("MVP Feature Explorer")
    print(f"  Project: {PROJECT_DIR}")
    print(f"  Resolution: {args.width}x{args.height}")
    print(f"  Force prefixes: {force or '(none - skip existing)'}")
    print()

    r = _make_renderer(args.width, args.height)

    sections = [
        gen_01_default(r, force),
        gen_02_templates(r, force),
        gen_03_colors(r, force),
        gen_04_gradients(r, force),
        gen_05_multistop(r, force),
        gen_06_textures(r, force),
        gen_07_reveal_modes(r, force),
        gen_08_text_styling(r, force),
        gen_09_recipes(r, force),
        gen_10_animations(r, force),
        gen_11_text_styles(r, force),
        gen_12_font_styles(r, force),
        gen_13_audio_reactive(r, force),
        gen_14_motion_presets(r, force),
        gen_15_mood_renders(r, force),
        gen_16_coming_soon(),
    ]

    html = build_html(sections)
    out_path = ROOT / "explorer.html"
    out_path.write_text(html, encoding="utf-8")

    elapsed = time.time() - t0
    n_static = len(list(STATIC_DIR.glob("*.png")))
    n_video = len(list(VIDEO_DIR.glob("*.mp4")))
    print(f"\nDone in {elapsed:.1f}s")
    print(f"  {n_static} static frames, {n_video} video clips")
    print(f"  {out_path}")


if __name__ == "__main__":
    main()
