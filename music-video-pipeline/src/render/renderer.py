from __future__ import annotations

import colorsys
import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from tqdm import tqdm

from .animations import (
    AnimationEasing,
    AnimationState,
    AnimationType,
    calculate_animation_state,
)
from .audio_reactive import apply_audio_effects
from .frame_effects import apply_frame_effect
from .effect_presets import get_preset, get_preset_for_section
from .background_video import create_background_source
from .font_styles import generate_styled_text
from .gradients import resolve_and_compute, apply_color_map
from canvas.renderer import render_canvas


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _contrast_color(bg_hex: str) -> str:
    r, g, b = _hex_to_rgb(bg_hex)
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#000000" if lum > 0.5 else "#ffffff"


def _companion_color(hex_color: str, shift: float = 40) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    h2, s, l = colorsys.rgb_to_hls(r, g, b)
    h2 = (h2 + shift / 360) % 1.0
    s = min(1.0, s * 1.1)
    l = max(0.2, min(0.8, l * 0.9))
    r2, g2, b2 = colorsys.hls_to_rgb(h2, l, s)
    return "#%02x%02x%02x" % (int(r2 * 255), int(g2 * 255), int(b2 * 255))


_FONTS_DIR = Path(__file__).resolve().parent.parent.parent / "fonts"

_FONT_FILES = {
    0: None,
    1: ("Exo2-Bold.ttf", "Exo2-Regular.ttf"),
    2: ("Bangers-Regular.ttf", "Bangers-Regular.ttf"),
    3: ("BebasNeue-Regular.ttf", "BebasNeue-Regular.ttf"),
    4: ("JetBrainsMono-Regular.ttf", "JetBrainsMono-Regular.ttf"),
    5: ("Lora-Bold.ttf", "Lora-Regular.ttf"),
    6: ("Oswald-Bold.ttf", "Oswald-Regular.ttf"),
}

_SYSTEM_FALLBACKS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]

_SYSTEM_FALLBACKS_REGULAR = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]


def _find_font(size: int, bold: bool = True, family: int = 0) -> ImageFont.FreeTypeFont:
    if family > 0 and family in _FONT_FILES:
        bold_name, regular_name = _FONT_FILES[family]
        name = bold_name if bold else regular_name
        path = _FONTS_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    fallbacks = _SYSTEM_FALLBACKS if bold else _SYSTEM_FALLBACKS_REGULAR
    for path in fallbacks:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


class VideoRenderer:
    def __init__(
        self,
        project_dir: Path,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
    ):
        self.project_dir = project_dir
        self.data_dir = project_dir / "data" if (project_dir / "data").exists() else project_dir
        self.width = width
        self.height = height
        self.fps = fps
        self.script: Dict[str, Any] = {}
        self.synced: Dict[str, Any] = {}
        self.defaults: Dict[str, Any] = {}
        self.caption_style: Dict[str, Any] = {}
        self.audio_path: Optional[Path] = None
        self.duration: float = 0.0
        self._bg_cache: Dict[str, Image.Image] = {}
        self._font_cache: Dict[tuple, ImageFont.FreeTypeFont] = {}
        self._bg_source = None
        self._styled_cache: Dict[tuple, Image.Image] = {}
        self._canvas_scene_cache: Dict[int, Any] = {}
        self.font = self._get_font(48)

    def _get_font(self, size: int, family: int = 0) -> ImageFont.FreeTypeFont:
        key = (family, size)
        if key not in self._font_cache:
            self._font_cache[key] = _find_font(size, family=family)
        return self._font_cache[key]
    def load(self, script_path: Optional[Path] = None) -> None:
        if script_path is None:
            script_path = self.data_dir / "script.json"
        if script_path.exists():
            self.script = json.loads(script_path.read_text(encoding="utf-8"))
        else:
            self.script = {}

        synced_path = self.data_dir / "lyrics_synced.json"
        if synced_path.exists():
            self.synced = json.loads(synced_path.read_text(encoding="utf-8"))
        else:
            raise FileNotFoundError("lyrics_synced.json not found")

        analysis_path = self.data_dir / "analysis.json"
        if analysis_path.exists():
            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
            self.duration = analysis.get("duration", 0.0)
            self._rms_energy = analysis.get("rms_energy", [])
            self._spectral_centroids = analysis.get("spectral_centroids", [])
            self._beat_times = analysis.get("beat_times", [])
            sr = analysis.get("sample_rate", 48000)
            hop = analysis.get("hop_length", 512)
            self._audio_fps = sr / hop
        elif self.synced.get("lines"):
            last = self.synced["lines"][-1]
            self.duration = last.get("end", 0.0) + 2.0
        else:
            self.duration = 0.0

        self.defaults = self.script.get("defaults", {})
        self.caption_style = self.script.get("caption_style", {})

        self._apply_timing_overrides()

        proj_path = self.data_dir / "mvp_project.json"
        if proj_path.exists():
            proj = json.loads(proj_path.read_text(encoding="utf-8"))
            audio_rel = proj.get("paths", {}).get("audio", "")
            if audio_rel:
                candidate = Path(audio_rel)
                if not candidate.is_absolute():
                    candidate = self.project_dir / audio_rel
                if candidate.exists():
                    self.audio_path = candidate
                else:
                    candidate2 = self.data_dir / audio_rel
                    if candidate2.exists():
                        self.audio_path = candidate2

    def _find_section(self, line_idx: int) -> Optional[Dict]:
        for sec in self.script.get("sections", []):
            lines = sec.get("lines", [])
            if isinstance(lines, list) and len(lines) > 0:
                if isinstance(lines[0], int) and isinstance(lines[-1], int):
                    if lines[0] <= line_idx <= lines[-1]:
                        return sec
        return None

    def get_visual(self, line_idx: int, word_idx: int) -> Dict[str, Any]:
        v = dict(self.defaults)
        sec = self._find_section(line_idx)
        if sec:
            if sec.get("visual"):
                v.update(sec["visual"])
            lo = sec.get("lines_overrides", {})
            if lo and str(line_idx) in lo:
                v.update(lo[str(line_idx)])
            wo = sec.get("words_overrides", {})
            key = f"{line_idx}.{word_idx}"
            if wo and key in wo:
                v.update(wo[key])
        return v

    def _get_reveal_mode(self, v: Dict) -> str:
        return v.get("reveal_mode", "progressive")

    def _apply_timing_overrides(self) -> None:
        """Merge script-level ``timing_overrides`` over the loaded synced lines.

        ``realign_from_stem`` and other timing transforms write per-line overrides
        into ``script.json`` (a journaled, invertible layer). The renderer honours
        them by deep-overwriting ``start``/``end``/``words`` on the affected
        synced lines, so every downstream consumer (``_find_active_word``,
        ``_compute_animation_progress``, the draw routines) sees corrected timing
        without each one needing to know about overrides.
        """
        overrides = self.script.get("timing_overrides") or {}
        if not isinstance(overrides, dict) or not overrides:
            return
        lines = self.synced.get("lines") or []
        for key, entry in overrides.items():
            if key == "_provenance" or not isinstance(entry, dict):
                continue
            try:
                idx = int(key)
            except (TypeError, ValueError):
                continue
            if idx < 0 or idx >= len(lines):
                continue
            line = lines[idx]
            if "start" in entry:
                line["start"] = entry["start"]
            if "end" in entry:
                line["end"] = entry["end"]
            if isinstance(entry.get("words"), list):
                line["words"] = [
                    {
                        "text": w.get("text", w.get("word", "")),
                        "start": w["start"],
                        "end": w["end"],
                    }
                    for w in entry["words"]
                    if isinstance(w, dict) and "start" in w and "end" in w
                ]

    def _find_active_word(self, t: float) -> Tuple[int, int]:
        for i, line in enumerate(self.synced.get("lines", [])):
            for j, word in enumerate(line.get("words", [])):
                if word["start"] <= t <= word["end"]:
                    return i, j
        return -1, -1

    def _get_audio_at(self, t: float) -> Dict[str, Any]:
        energy = 0.0
        centroid = 0.5
        if self._rms_energy:
            idx = int(t * self._audio_fps)
            idx = max(0, min(idx, len(self._rms_energy) - 1))
            energy = self._rms_energy[idx]
        if self._spectral_centroids:
            idx = int(t * self._audio_fps)
            idx = max(0, min(idx, len(self._spectral_centroids) - 1))
            centroid = self._spectral_centroids[idx]
        is_beat = False
        if self._beat_times:
            for bt in self._beat_times:
                if abs(t - bt) < 0.05:
                    is_beat = True
                    break
        return {"energy": energy, "centroid": centroid, "is_beat": is_beat}

    def _compute_animation_progress(self, t: float, line_idx: int) -> AnimationState:
        if line_idx < 0 or line_idx >= len(self.synced.get("lines", [])):
            return AnimationState()
        line = self.synced["lines"][line_idx]
        line_start = line.get("start", 0.0)
        line_end = line.get("end", 0.0)
        duration = max(0.001, line_end - line_start)
        progress = (t - line_start) / duration
        progress = max(0.0, min(1.0, progress))

        v = self.get_visual(line_idx, 0)
        anim_type_str = v.get("animation_type", "fade")
        anim_speed = v.get("animation_speed", 1.0)

        try:
            anim_type = AnimationType(anim_type_str)
        except ValueError:
            anim_type = AnimationType.FADE_IN

        enter_duration = 0.25 / anim_speed
        enter_end = min(0.3, enter_duration / duration)

        words = line.get("words", [])
        last_word_start = words[-1].get("start", line_start) if words else line_start
        last_word_progress = (last_word_start - line_start) / duration
        exit_start = max(last_word_progress, 1.0 - 0.2 / anim_speed)

        if progress < enter_end:
            elapsed = t - line_start
            p = min(1.0, elapsed / enter_duration)
            anim_state = calculate_animation_state(
                anim_type, p, AnimationEasing.EASE_OUT,
                width=self.width, height=self.height,
            )
            if anim_type == AnimationType.FADE_IN and p < 0.2:
                anim_state.opacity = 1.0
            else:
                anim_state.opacity = max(anim_state.opacity, 0.85)
            sx, sy = anim_state.scale
            min_s = 0.5
            if sx < min_s:
                anim_state.scale = (min_s, min_s)
            return anim_state
        elif progress > exit_start:
            exit_range = max(0.001, 1.0 - exit_start)
            p = (progress - exit_start) / exit_range
            p = min(1.0, p)
            if anim_type == AnimationType.FADE_IN:
                exit_type = AnimationType.FADE_OUT
            elif anim_type == AnimationType.SLIDE_IN:
                exit_type = AnimationType.SLIDE_OUT
            elif anim_type == AnimationType.SCALE_IN:
                exit_type = AnimationType.SCALE_OUT
            else:
                exit_type = AnimationType.FADE_OUT
            return calculate_animation_state(
                exit_type, p, AnimationEasing.EASE_IN,
                width=self.width, height=self.height,
            )
        else:
            return AnimationState()

    def _apply_animation_transforms(
        self, text_img: Image.Image, anim: AnimationState
    ) -> Image.Image:
        sx, sy = anim.scale
        if abs(sx - 1.0) > 0.001 or abs(sy - 1.0) > 0.001:
            new_w = max(1, int(self.width * sx))
            new_h = max(1, int(self.height * sy))
            text_img = text_img.resize((new_w, new_h), Image.LANCZOS)
            canvas = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            paste_x = (self.width - new_w) // 2
            paste_y = (self.height - new_h) // 2
            canvas.paste(text_img, (paste_x, paste_y), text_img)
            text_img = canvas

        if abs(anim.rotation) > 0.1:
            text_img = text_img.rotate(
                -anim.rotation, resample=Image.BICUBIC, expand=False, fillcolor=None
            )

        return text_img

    def _draw_background(self, img: Image.Image, v: Dict) -> None:
        draw = ImageDraw.Draw(img)
        bg_type = v.get("background_type", "solid")

        if bg_type == "gradient":
            colors = v.get("gradient_colors", [v.get("background_color", "#1a1a2e"), "#8E44AD"])
            direction = v.get("gradient_direction", "vertical_top_bottom")
            params = v.get("gradient_params")
            self._draw_gradient(img, colors, direction, params)
        elif bg_type == "image" and v.get("background_image"):
            self._draw_bg_image(img, v)
        else:
            color = _hex_to_rgb(v.get("background_color", "#1a1a2e"))
            draw.rectangle([0, 0, self.width, self.height], fill=color)

        self._draw_texture(img, v)

    def _init_bg_source(self) -> None:
        if self._bg_source is not None:
            return
        bg_video = self.defaults.get("background_video", "")
        if not bg_video:
            return
        path = Path(bg_video)
        if not path.is_absolute():
            path = self.project_dir / bg_video
        if path.exists():
            self._bg_source = create_background_source(
                str(path), self.width, self.height, self._beat_times
            )

    def _draw_gradient(self, img: Image.Image, colors: List[str], direction: str,
                       params: Optional[Dict] = None) -> None:
        rgbs = [_hex_to_rgb(c) for c in colors]
        rgb_arr = np.array(rgbs, dtype=np.float32)
        t = resolve_and_compute(direction, self.width, self.height, params)
        arr = apply_color_map(t, rgb_arr)
        img.paste(Image.fromarray(arr))

    def _draw_bg_image(self, img: Image.Image, v: Dict) -> None:
        draw = ImageDraw.Draw(img)
        color = _hex_to_rgb(v.get("background_color", "#000000"))
        draw.rectangle([0, 0, self.width, self.height], fill=color)
        bg_img_path = v.get("background_image", "")
        if bg_img_path.startswith("data:"):
            return
        bg = self._bg_cache.get(bg_img_path)
        if bg is None:
            try:
                bg = Image.open(bg_img_path).convert("RGB")
                self._bg_cache[bg_img_path] = bg
            except Exception:
                return
        opacity = v.get("background_image_opacity", 1.0)
        fit = v.get("background_image_fit", "cover")
        iw, ih = bg.size
        if fit == "cover":
            scale = max(self.width / iw, self.height / ih)
        else:
            scale = min(self.width / iw, self.height / ih)
        sw, sh = int(iw * scale), int(ih * scale)
        resized = bg.resize((sw, sh), Image.LANCZOS)
        x_off = (self.width - sw) // 2
        y_off = (self.height - sh) // 2
        if opacity >= 1.0:
            img.paste(resized, (x_off, y_off))
        else:
            overlay = Image.new("RGB", (self.width, self.height), color)
            overlay.paste(resized, (x_off, y_off))
            img_blend = Image.blend(img, overlay, opacity)
            img.paste(img_blend)

    def _draw_texture(self, img: Image.Image, v: Dict) -> None:
        tex = v.get("texture_type", "none")
        if not tex or tex == "none":
            return
        opacity = v.get("texture_opacity", 0.15)

        if tex == "vignette_soft":
            self._draw_vignette(img, 0.2, 0.7, 0.7, opacity)
        elif tex == "vignette_heavy":
            self._draw_vignette(img, 0.1, 0.6, 0.9, opacity)
        else:
            arr = np.array(img, dtype=np.float32)
            rng = np.random.RandomState(42)
            noise = rng.random((self.height, self.width))
            if tex == "noise_fine":
                val = noise * 60
            elif tex == "noise_coarse":
                val = (noise > 0.5).astype(np.float32) * 40
            elif tex == "grain_film":
                val = noise * 50
            elif tex == "paper_subtle":
                val = noise * 20
            else:
                val = noise * 30
            blend = v.get("texture_blend_mode", "multiply")
            if blend == "multiply":
                factor = 1 - val / 255
                for c in range(3):
                    arr[:, :, c] *= factor
            else:
                for c in range(3):
                    arr[:, :, c] = np.minimum(255, arr[:, :, c] + val)
            img.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)))

    def _draw_vignette(self, img: Image.Image, inner_pct: float, outer_pct: float, strength: float, opacity: float) -> None:
        cx, cy = self.width / 2, self.height / 2
        max_r = math.sqrt(cx * cx + cy * cy)
        overlay = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        arr = np.array(overlay, dtype=np.float32)
        ys, xs = np.ogrid[:self.height, :self.width]
        dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        t = np.clip((dist / max_r - inner_pct) / max(0.01, outer_pct - inner_pct), 0, 1)
        alpha = (t * 255 * strength).astype(np.uint8)
        for c in range(3):
            arr[:, :, c] = alpha
        overlay = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        result = Image.blend(img, overlay, opacity)
        img.paste(result)

    def _y_for_pos(self, pos: str) -> int:
        if pos == "top":
            return int(self.height * 0.2)
        elif pos == "bottom":
            return int(self.height * 0.8)
        return self.height // 2

    def _apply_bg_motion(self, img: Image.Image, t: float, v: Dict) -> Image.Image:
        preset_name = v.get("bg_animation_preset", "")
        if not preset_name:
            sec = self._find_nearest_section(t)
            if sec:
                preset = get_preset_for_section(sec.get("type", ""))
                if preset:
                    preset_name = preset.name
        if not preset_name:
            return img
        preset = get_preset(preset_name)
        reactivity = v.get("reactivity", [])
        audio = self._get_audio_at(t)

        full_h, full_w = self.height, self.width
        scale = 2
        small_h, small_w = full_h // scale, full_w // scale

        arr = np.array(img)
        arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        arr = cv2.resize(arr, (small_w, small_h), interpolation=cv2.INTER_AREA)

        for eff in preset.effects:
            arr = apply_frame_effect(arr, eff["effect"], t, eff.get("params"))

        if reactivity:
            arr = apply_audio_effects(arr, audio, t, reactivity)

        arr = cv2.resize(arr, (full_w, full_h), interpolation=cv2.INTER_LINEAR)
        arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        return Image.fromarray(arr)

    def _frame_is_unique(self, line_idx: int) -> bool:
        if line_idx < 0:
            return True
        v = self.get_visual(line_idx, 0)
        if v.get("animation_type", "none") != "none":
            return True
        if v.get("bg_animation_preset", ""):
            return True
        return True

    def _has_styled_text(self, v: Dict) -> bool:
        ts = v.get("text_style", "")
        return bool(ts) and ts != "basic"

    def _get_styled_text(self, text: str, style: str, size: int, family: int = 0, style_colors: Optional[dict] = None) -> Image.Image:
        if style_colors:
            style_colors = {k: tuple(v) if isinstance(v, list) else v for k, v in style_colors.items()}
        key = (text, style, size, family, tuple(sorted((style_colors or {}).items())) if style_colors else None)
        if key not in self._styled_cache:
            self._styled_cache[key] = generate_styled_text(text, style, size, family=family, style_colors=style_colors)
        return self._styled_cache[key]

    def _styled_word_widths(self, words: list, style: str, size: int, family: int, style_colors: Optional[dict] = None) -> list:
        return [self._get_styled_text(w["text"], style, size, family, style_colors=style_colors).size[0] for w in words]

    def _word_widths(self, words: list, font: ImageFont.FreeTypeFont, v: Dict, font_size: int) -> list:
        if self._has_styled_text(v):
            return self._styled_word_widths(words, v["text_style"], font_size, v.get("font_family", 0), style_colors=v.get("text_style_colors"))
        return [font.getbbox(w["text"])[2] for w in words]

    def _base_spacing(self, font_size: int) -> float:
        return self.caption_style.get("letter_spacing", 1) * (self.height / 1080) * max(8, font_size * 0.08)

    def _draw_backdrop_group(self, img: Image.Image, layout: list, indices: list, v: Dict) -> None:
        enabled = v.get("text_backdrop", self.caption_style.get("text_backdrop", False))
        if not enabled or not indices:
            return
        sf = self.height / 1080
        color_hex = v.get("text_backdrop_color", self.caption_style.get("text_backdrop_color", "#000000"))
        opacity = float(v.get("text_backdrop_opacity", self.caption_style.get("text_backdrop_opacity", 0.5)))
        pad = int(float(v.get("text_backdrop_padding", self.caption_style.get("text_backdrop_padding", 15))) * sf)
        radius = int(float(v.get("text_backdrop_radius", self.caption_style.get("text_backdrop_radius", 12))) * sf)
        r, g, b = _hex_to_rgb(color_hex)
        a = int(opacity * 255)
        groups = {}
        for i in indices:
            y_key = round(layout[i]["px_y"])
            groups.setdefault(y_key, []).append(i)
        draw = ImageDraw.Draw(img)
        for y_key, gi in groups.items():
            boxes = []
            for i in gi:
                lr = layout[i]
                hw = lr["wW"] / 2
                hh = lr["word_size"] * 0.55
                boxes.append((lr["px_x"] - hw, lr["px_y"] - hh, lr["px_x"] + hw, lr["px_y"] + hh))
            x0 = min(b[0] for b in boxes)
            y0 = min(b[1] for b in boxes)
            x1 = max(b[2] for b in boxes)
            y1 = max(b[3] for b in boxes)
            draw.rounded_rectangle(
                [x0 - pad, y0 - pad, x1 + pad, y1 + pad],
                radius=radius,
                fill=(r, g, b, a),
            )

    _POS_TO_Y = {"top": 0.2, "center": 0.5, "bottom": 0.8}

    def _resolve_word_y(self, wv: Dict, section_pos: str) -> float:
        if "y" in wv:
            return wv["y"]
        tp = wv.get("text_position", section_pos)
        return self._POS_TO_Y.get(tp, 0.5)

    def _layout_line(self, words: list, line_idx: int, v: Dict, base_font_size: int, font_family: int) -> list:
        section_pos = v.get("text_position", self.caption_style.get("text_position", "center"))
        use_styled = self._has_styled_text(v)
        style = v.get("text_style", "")
        sf = self.height / 1080

        resolved = []
        for wi in range(len(words)):
            wv = self.get_visual(line_idx, wi)
            word_y = self._resolve_word_y(wv, section_pos)
            word_x = wv.get("x", None)
            delta = wv.get("font_size_delta", 0)
            word_size = max(24, base_font_size + int(delta * sf))
            f = self._get_font(word_size, font_family)
            wW = f.getbbox(words[wi]["text"])[2]
            resolved.append({"px_x": None, "px_y": int(word_y * self.height), "wW": wW, "word_size": word_size, "x": word_x})

        pinned = [(i, r) for i, r in enumerate(resolved) if r["x"] is not None]
        for i, r in pinned:
            r["px_x"] = int(r["x"] * self.width)

        grouped_indices = [i for i in range(len(words)) if resolved[i]["x"] is None]
        if grouped_indices:
            groups = []
            cur = [grouped_indices[0]]
            for k in range(1, len(grouped_indices)):
                if resolved[grouped_indices[k]]["px_y"] == resolved[grouped_indices[k - 1]]["px_y"]:
                    cur.append(grouped_indices[k])
                else:
                    groups.append(cur)
                    cur = [grouped_indices[k]]
            groups.append(cur)

            for group in groups:
                spacing = self._base_spacing(base_font_size)
                if use_styled:
                    spacing = max(spacing, base_font_size * 0.35)
                gw = [resolved[i]["wW"] for i in group]
                total_w = sum(gw) + spacing * max(0, len(group) - 1)

                max_w = self.width * 0.92
                if total_w > max_w:
                    scale = max_w / total_w
                    min_size = max(24, int(base_font_size * 0.40))
                    for wi in group:
                        resolved[wi]["word_size"] = max(min_size, int(resolved[wi]["word_size"] * scale))
                        f = self._get_font(resolved[wi]["word_size"], font_family)
                        resolved[wi]["wW"] = f.getbbox(words[wi]["text"])[2]
                    spacing = self._base_spacing(int(base_font_size * scale))
                    if use_styled:
                        spacing = max(spacing, int(base_font_size * scale) * 0.35)
                    gw = [resolved[i]["wW"] for i in group]
                    total_w = sum(gw) + spacing * max(0, len(group) - 1)

                x = (self.width - total_w) / 2
                for j, wi in enumerate(group):
                    resolved[wi]["px_x"] = x + gw[j] / 2
                    x += gw[j] + spacing

        return resolved

    def _draw_text_line(self, img: Image.Image, text: str, v: Dict, y: int, font_size: int) -> None:
        if self._has_styled_text(v):
            family = v.get("font_family", 0)
            styled = self._get_styled_text(text, v["text_style"], font_size, family, style_colors=v.get("text_style_colors"))
            sw, sh = styled.size
            px = (self.width - sw) // 2
            py = int(y - sh / 2)
            img.paste(styled, (px, py), styled)
            return

        draw = ImageDraw.Draw(img)
        font = self._get_font(font_size, v.get("font_family", 0))
        auto_contrast = v.get("text_auto_contrast", True)
        if auto_contrast is not False:
            color = _contrast_color(v.get("background_color", "#1a1a2e"))
        else:
            color = v.get("text_color", self.caption_style.get("text_color", "#ffffff"))
        rgb = _hex_to_rgb(color)

        cs = self.caption_style
        if cs.get("outline"):
            ow = cs.get("outline_width", 2)
            oc = _hex_to_rgb(cs.get("outline_color", "#000000"))
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            tx = (self.width - tw) // 2
            for dx in range(-ow, ow + 1):
                for dy in range(-ow, ow + 1):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((tx + dx, y + dy), text, fill=oc, font=font)

        if cs.get("text_shadow"):
            sc = _hex_to_rgb(cs.get("text_shadow_color", "#000000"))
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            tx = (self.width - tw) // 2
            draw.text((tx + 2, y + 2), text, fill=sc, font=font)

        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        tx = (self.width - tw) // 2
        draw.text((tx, y), text, fill=rgb, font=font)

    def _draw_karaoke(self, img: Image.Image, line: Dict, line_idx: int, word_idx: int, v: Dict, font_size: int) -> None:
        words = line["words"]
        cs = self.caption_style
        text_style = v.get("text_style", "")
        font_family = v.get("font_family", 0)
        layout = self._layout_line(words, line_idx, v, font_size, font_family)
        self._draw_backdrop_group(img, layout, list(range(len(words))), v)

        text_style_colors = v.get("text_style_colors")

        if self._has_styled_text(v):
            for j, w in enumerate(words):
                r = layout[j]
                is_active = j == word_idx
                opacity = 1.0 if is_active else 0.75
                styled = self._get_styled_text(w["text"], text_style, r["word_size"], font_family, style_colors=text_style_colors).copy()
                sw, sh = styled.size
                px = int(r["px_x"] - sw / 2)
                py = int(r["px_y"] - sh / 2)
                if opacity < 1.0:
                    alpha = styled.split()[3]
                    alpha = alpha.point(lambda a: int(a * opacity))
                    styled.putalpha(alpha)
                img.paste(styled, (px, py), styled)
            return

        draw = ImageDraw.Draw(img)
        auto_contrast = v.get("text_auto_contrast", True)
        base_hex = _contrast_color(v.get("background_color", "#1a1a2e")) if auto_contrast is not False else v.get("text_color", cs.get("text_color", "#ffffff"))
        hl_hex = cs.get("highlight_color", "#4cc9f0")
        base_rgb = _hex_to_rgb(base_hex)
        hl_rgb = _hex_to_rgb(hl_hex)

        for j, w in enumerate(words):
            r = layout[j]
            is_active = j == word_idx
            rgb = hl_rgb if is_active else base_rgb
            font = self._get_font(r["word_size"], font_family)
            wW = r["wW"]
            if cs.get("outline"):
                ow = cs.get("outline_width", 2)
                oc = _hex_to_rgb(cs.get("outline_color", "#000000"))
                for dx in range(-ow, ow + 1):
                    for dy in range(-ow, ow + 1):
                        if dx == 0 and dy == 0:
                            continue
                        draw.text((r["px_x"] - wW / 2 + dx, r["px_y"] + dy), w["text"], fill=oc, font=font, anchor="lm")
            if cs.get("text_shadow"):
                sc = _hex_to_rgb(cs.get("text_shadow_color", "#000000"))
                sf2 = self.height / 1080
                draw.text((r["px_x"] - wW / 2 + 2 * sf2, r["px_y"] + 2 * sf2), w["text"], fill=sc, font=font, anchor="lm")
            draw.text((r["px_x"] - wW / 2, r["px_y"]), w["text"], fill=rgb, font=font, anchor="lm")

    def _draw_progressive(self, img: Image.Image, line: Dict, line_idx: int, word_idx: int, v: Dict, font_size: int) -> None:
        words = line["words"]
        cs = self.caption_style
        text_style = v.get("text_style", "")
        font_family = v.get("font_family", 0)

        step = v.get("reveal_words", 1)
        slide = v.get("reveal_slide", False)

        if slide:
            window_size = step * 2
            start = max(0, word_idx - step + 1)
            if start + window_size > len(words):
                start = max(0, len(words) - window_size)
            end = min(len(words), start + window_size)
            vis = words[start:end]
        else:
            visible_count = word_idx + 1
            vis = words[:visible_count]
            start = 0

        group_start = (word_idx // step) * step if not slide else start

        layout = self._layout_line(words, line_idx, v, font_size, font_family)

        if not slide:
            visible_range = range(0, min(word_idx + 1, len(words)))
        else:
            visible_range = range(start, min(start + step * 2, len(words)))

        self._draw_backdrop_group(img, layout, list(visible_range), v)

        text_style_colors = v.get("text_style_colors")

        if self._has_styled_text(v):
            for idx in visible_range:
                r = layout[idx]
                is_active = idx >= group_start and idx <= word_idx
                opacity = 1.0 if is_active else 0.8
                styled = self._get_styled_text(words[idx]["text"], text_style, r["word_size"], font_family, style_colors=text_style_colors).copy()
                sw, sh = styled.size
                px = int(r["px_x"] - sw / 2)
                py = int(r["px_y"] - sh / 2)
                if opacity < 1.0:
                    alpha = styled.split()[3]
                    alpha = alpha.point(lambda a: int(a * opacity))
                    styled.putalpha(alpha)
                img.paste(styled, (px, py), styled)
            return

        draw = ImageDraw.Draw(img)
        auto_contrast = v.get("text_auto_contrast", True)
        base_hex = _contrast_color(v.get("background_color", "#1a1a2e")) if auto_contrast is not False else v.get("text_color", cs.get("text_color", "#ffffff"))
        hl_hex = cs.get("highlight_color", "#4cc9f0")
        base_rgb = _hex_to_rgb(base_hex)
        hl_rgb = _hex_to_rgb(hl_hex)

        for idx in visible_range:
            r = layout[idx]
            is_active = idx >= group_start and idx <= word_idx
            rgb = hl_rgb if is_active else base_rgb
            font = self._get_font(r["word_size"], font_family)
            wW = r["wW"]
            if cs.get("outline"):
                ow = cs.get("outline_width", 2)
                oc = _hex_to_rgb(cs.get("outline_color", "#000000"))
                for dx in range(-ow, ow + 1):
                    for dy in range(-ow, ow + 1):
                        if dx == 0 and dy == 0:
                            continue
                        draw.text((r["px_x"] - wW / 2 + dx, r["px_y"] + dy), words[idx]["text"], fill=oc, font=font, anchor="lm")
            if cs.get("text_shadow"):
                sc = _hex_to_rgb(cs.get("text_shadow_color", "#000000"))
                sf2 = self.height / 1080
                draw.text((r["px_x"] - wW / 2 + 2 * sf2, r["px_y"] + 2 * sf2), words[idx]["text"], fill=sc, font=font, anchor="lm")
            draw.text((r["px_x"] - wW / 2, r["px_y"]), words[idx]["text"], fill=rgb, font=font, anchor="lm")

    def _render_intro_frame(self, t: float) -> Optional[Image.Image]:
        intro = self.script.get("intro")
        if not intro:
            return None
        duration = intro.get("duration", 0.0)
        if duration <= 0 or t >= duration:
            return None

        img = Image.new("RGB", (self.width, self.height), (10, 10, 30))

        phase1_end = duration * 0.55
        phase2_start = duration * 0.60

        if t < phase1_end:
            image_path = intro.get("image", "")
            if image_path:
                v_img = {
                    "background_type": "image",
                    "background_image": image_path,
                    "background_image_opacity": 1.0,
                    "background_image_fit": "cover",
                    "background_color": "#000000",
                }
                self._draw_background(img, v_img)

        elif t >= phase2_start:
            v_bg = dict(self.defaults)
            self._draw_background(img, v_bg)

            lines = [
                (intro.get("title") or self.script.get("name", ""), int(80 * (self.height / 1080)), 3),
                (intro.get("subtitle") or "A Reality Signal", int(44 * (self.height / 1080)), 5),
                ("by", int(44 * (self.height / 1080)), 5),
                ("Asabaal Horan", int(44 * (self.height / 1080)), 5),
            ]

            txt_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(txt_layer)

            line_heights = []
            for text, size, family in lines:
                font = self._get_font(size, family=family)
                bbox = draw.textbbox((0, 0), text, font=font)
                line_heights.append(bbox[3] - bbox[1])

            line_spacing = int(12 * (self.height / 1080))
            total_h = sum(line_heights) + line_spacing * (len(lines) - 1)
            y = (self.height - total_h) / 2

            for i, (text, size, family) in enumerate(lines):
                font = self._get_font(size, family=family)
                bbox = draw.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                cx = (self.width - tw) / 2
                shadow_offset = max(2, int(2 * (self.height / 1080)))
                draw.text((cx + shadow_offset, y + shadow_offset), text, fill=(0, 0, 0, 180), font=font)
                draw.text((cx, y), text, fill=(220, 220, 230, 255), font=font)
                y += th + line_spacing

            img_rgba = img.convert("RGBA")
            img_rgba = Image.alpha_composite(img_rgba, txt_layer)
            img = img_rgba.convert("RGB")

        else:
            v_bg = dict(self.defaults)
            self._draw_background(img, v_bg)

        return img

    def _get_last_word_end(self) -> float:
        if not self.synced.get("lines"):
            return 0.0
        last_line = self.synced["lines"][-1]
        words = last_line.get("words", [])
        if not words:
            return 0.0
        return words[-1].get("end", 0.0)

    def _render_outro_frame(self, t: float) -> Optional[Image.Image]:
        outro = self.script.get("outro")
        if not outro:
            return None
        last_end = self._get_last_word_end()
        if last_end <= 0 or t < last_end:
            return None
        outro_start = last_end
        outro_duration = self.duration - outro_start
        if outro_duration <= 0:
            return None
        elapsed = t - outro_start
        if elapsed >= outro_duration:
            elapsed = outro_duration - 0.001

        img = Image.new("RGB", (self.width, self.height), (10, 10, 30))

        phase1_end = outro_duration * 0.45
        phase2_start = outro_duration * 0.50

        if elapsed < phase1_end:
            image_path = outro.get("image", "")
            if image_path:
                v_img = {
                    "background_type": "image",
                    "background_image": image_path,
                    "background_image_opacity": 1.0,
                    "background_image_fit": "cover",
                    "background_color": "#000000",
                }
                self._draw_background(img, v_img)

        elif elapsed >= phase2_start:
            v_bg = dict(self.defaults)
            self._draw_background(img, v_bg)

            txt_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(txt_layer)

            label = outro.get("text", "Presented by")
            label_size = int(36 * (self.height / 1080))
            label_font = self._get_font(label_size, family=5)
            lbbox = draw.textbbox((0, 0), label, font=label_font)
            lw = lbbox[2] - lbbox[0]
            lh = lbbox[3] - lbbox[1]
            lcx = (self.width - lw) / 2

            logo_path = outro.get("logo", "")
            logo_img = None
            logo_h = 0
            logo_w = 0
            if logo_path:
                try:
                    logo_img = Image.open(logo_path).convert("RGBA")
                    max_logo_w = int(self.width * 0.5)
                    if logo_img.size[0] > max_logo_w:
                        scale = max_logo_w / logo_img.size[0]
                        logo_img = logo_img.resize((int(logo_img.size[0] * scale), int(logo_img.size[1] * scale)), Image.LANCZOS)
                    logo_w, logo_h = logo_img.size
                except Exception:
                    logo_img = None

            gap = int(30 * (self.height / 1080))
            total_h = lh + gap + logo_h
            y = (self.height - total_h) / 2

            shadow_offset = max(2, int(2 * (self.height / 1080)))
            draw.text((lcx + shadow_offset, y + shadow_offset), label, fill=(0, 0, 0, 180), font=label_font)
            draw.text((lcx, y), label, fill=(180, 180, 190, 255), font=label_font)

            if logo_img:
                logo_x = (self.width - logo_w) // 2
                logo_y = int(y + lh + gap)
                txt_layer.paste(logo_img, (logo_x, logo_y), logo_img)

            img_rgba = img.convert("RGBA")
            img_rgba = Image.alpha_composite(img_rgba, txt_layer)
            img = img_rgba.convert("RGB")

        else:
            v_bg = dict(self.defaults)
            self._draw_background(img, v_bg)

        return img

    def _render_interstitial(self, t: float) -> Optional[Image.Image]:
        interstitials = self.script.get("interstitials", [])
        for ins in interstitials:
            start = float(ins.get("start", 0))
            end = float(ins.get("end", 0))
            if start <= t <= end:
                img = Image.new("RGB", (self.width, self.height), (10, 10, 30))
                ins_type = ins.get("type", "")
                if ins_type == "image":
                    image_path = ins.get("path", "")
                    if image_path:
                        v_img = {
                            "background_type": "image",
                            "background_image": image_path,
                            "background_image_opacity": 1.0,
                            "background_image_fit": "cover",
                            "background_color": "#000000",
                        }
                        self._draw_background(img, v_img)
                elif ins_type == "title":
                    v_bg = dict(self.defaults)
                    self._draw_background(img, v_bg)
                    txt_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(txt_layer)
                    title = ins.get("title", "")
                    subtitle = ins.get("subtitle", "")
                    lines = []
                    if title:
                        lines.append((title, int(80 * (self.height / 1080)), 3))
                    if subtitle:
                        lines.append((subtitle, int(44 * (self.height / 1080)), 5))
                    lines.append(("by", int(44 * (self.height / 1080)), 5))
                    lines.append(("Asabaal Horan", int(44 * (self.height / 1080)), 5))
                    if lines:
                        line_heights = []
                        for text, size, family in lines:
                            font = self._get_font(size, family=family)
                            bbox = draw.textbbox((0, 0), text, font=font)
                            line_heights.append(bbox[3] - bbox[1])
                        line_spacing = int(12 * (self.height / 1080))
                        total_h = sum(line_heights) + line_spacing * (len(lines) - 1)
                        y = (self.height - total_h) / 2
                        for text, size, family in lines:
                            font = self._get_font(size, family=family)
                            bbox = draw.textbbox((0, 0), text, font=font)
                            tw = bbox[2] - bbox[0]
                            th = bbox[3] - bbox[1]
                            cx = (self.width - tw) / 2
                            shadow_offset = max(2, int(2 * (self.height / 1080)))
                            draw.text((cx + shadow_offset, y + shadow_offset), text, fill=(0, 0, 0, 180), font=font)
                            draw.text((cx, y), text, fill=(220, 220, 230, 255), font=font)
                            y += th + line_spacing
                    img_rgba = img.convert("RGBA")
                    img_rgba = Image.alpha_composite(img_rgba, txt_layer)
                    img = img_rgba.convert("RGB")
                return img
        return None

    def _find_nearest_section(self, t: float) -> Optional[Dict]:
        best_sec = None
        best_dist = float("inf")
        for sec in self.script.get("sections", []):
            lines = sec.get("lines", [])
            if not lines:
                continue
            first_line = self.synced["lines"][lines[0]]
            last_line = self.synced["lines"][lines[-1]]
            sec_start = first_line.get("words", [{}])[0].get("start", 0)
            last_words = last_line.get("words", [{}])
            sec_end = last_words[-1].get("end", 0) if last_words else 0
            if t < sec_start:
                dist = sec_start - t
            elif t > sec_end:
                dist = t - sec_end
            else:
                return sec
            if dist < best_dist:
                best_dist = dist
                best_sec = sec
        return best_sec

    def render_frame(self, t: float) -> Image.Image:
        img = Image.new("RGB", (self.width, self.height), (10, 10, 30))
        line_idx, word_idx = self._find_active_word(t)

        if line_idx < 0:
            interstitial = self._render_interstitial(t)
            if interstitial is not None:
                return interstitial
            intro_frame = self._render_intro_frame(t)
            if intro_frame is not None:
                return intro_frame
            outro_frame = self._render_outro_frame(t)
            if outro_frame is not None:
                return outro_frame
            nearest = self._find_nearest_section(t)
            v_gap = dict(self.defaults)
            if nearest:
                nv = nearest.get("visual", {})
                v_gap.update(nv)
            v_gap["bg_animation_preset"] = "gap"
            v_gap["reactivity"] = ["energy"]
            if nearest:
                bg = self._get_bg_for_section(nearest["lines"][0], {})
            else:
                bg = img
                self._draw_background(bg, v_gap)
            arr = np.array(bg, dtype=np.float32)
            arr = np.clip(arr * 2.5, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr)
            img = self._apply_bg_motion(img, t, v_gap)
            return img

        v = self.get_visual(line_idx, word_idx)
        canvas_config = v.get("canvas")
        if canvas_config:
            img = render_canvas(canvas_config, self.width, self.height, t, self._canvas_scene_cache)
        else:
            self._draw_background(img, v)
        img = self._apply_bg_motion(img, t, v)

        line = self.synced["lines"][line_idx]
        font_size = int((v.get("font_size", self.caption_style.get("font_size", 112))) * (self.height / 1080))

        anim = self._compute_animation_progress(t, line_idx)

        text_img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        mode = self._get_reveal_mode(v)

        if mode == "line-by-line":
            pos = v.get("text_position", self.caption_style.get("text_position", "center"))
            y = self._y_for_pos(pos)
            self._draw_text_line(text_img, line["text"], v, y, font_size)
        elif mode == "stacking":
            sec = self._find_section(line_idx)
            if sec:
                section_pos = v.get("text_position", self.caption_style.get("text_position", "center"))
                for li in sec["lines"]:
                    if li > line_idx:
                        break
                    ld = self.synced["lines"][li]
                    lv = self.get_visual(li, 0)
                    line_y = int(self._resolve_word_y(lv, section_pos) * self.height)
                    line_fs = int((lv.get("font_size", self.caption_style.get("font_size", 112))) * (self.height / 1080))
                    self._draw_text_line(text_img, ld["text"], lv, line_y, line_fs)
        elif mode == "progressive":
            self._draw_progressive(text_img, line, line_idx, word_idx, v, font_size)
        else:
            self._draw_karaoke(text_img, line, line_idx, word_idx, v, font_size)

        text_img = self._apply_animation_transforms(text_img, anim)

        if anim.opacity < 1.0:
            alpha = text_img.split()[3]
            alpha = alpha.point(lambda a: int(a * anim.opacity))
            text_img.putalpha(alpha)

        ox = int(anim.position[0])
        oy = int(anim.position[1])
        if ox != 0 or oy != 0:
            canvas = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            canvas.paste(text_img, (ox, oy))
            text_img = canvas

        img_rgba = img.convert("RGBA")
        img_rgba = Image.alpha_composite(img_rgba, text_img)
        img = img_rgba.convert("RGB")

        return img

    def _render_text_on_bg(self, bg: Image.Image, line_idx: int, word_idx: int, t: float = 0.0) -> Image.Image:
        if line_idx < 0:
            interstitial = self._render_interstitial(t)
            if interstitial is not None:
                return interstitial
            intro_frame = self._render_intro_frame(t)
            if intro_frame is not None:
                return intro_frame
            outro_frame = self._render_outro_frame(t)
            if outro_frame is not None:
                return outro_frame
            nearest = self._find_nearest_section(t)
            v_gap = dict(self.defaults)
            if nearest:
                nv = nearest.get("visual", {})
                v_gap.update(nv)
            v_gap["bg_animation_preset"] = "gap"
            v_gap["reactivity"] = ["energy"]
            if nearest:
                bg = self._get_bg_for_section(nearest["lines"][0], {})
            else:
                bg = bg.copy()
            arr = np.array(bg, dtype=np.float32)
            arr = np.clip(arr * 2.5, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr)
            img = self._apply_bg_motion(img, t, v_gap)
            return img

        img = bg.copy()
        v = self.get_visual(line_idx, word_idx)
        canvas_config = v.get("canvas")
        if canvas_config:
            img = render_canvas(canvas_config, self.width, self.height, t, self._canvas_scene_cache)
        img = self._apply_bg_motion(img, t, v)

        line = self.synced["lines"][line_idx]
        font_size = int((v.get("font_size", self.caption_style.get("font_size", 112))) * (self.height / 1080))

        anim = self._compute_animation_progress(t, line_idx)

        text_img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        mode = self._get_reveal_mode(v)

        if mode == "line-by-line":
            pos = v.get("text_position", self.caption_style.get("text_position", "center"))
            y = self._y_for_pos(pos)
            self._draw_text_line(text_img, line["text"], v, y, font_size)
        elif mode == "stacking":
            sec = self._find_section(line_idx)
            if sec:
                section_pos = v.get("text_position", self.caption_style.get("text_position", "center"))
                for li in sec["lines"]:
                    if li > line_idx:
                        break
                    ld = self.synced["lines"][li]
                    lv = self.get_visual(li, 0)
                    line_y = int(self._resolve_word_y(lv, section_pos) * self.height)
                    line_fs = int((lv.get("font_size", self.caption_style.get("font_size", 112))) * (self.height / 1080))
                    self._draw_text_line(text_img, ld["text"], lv, line_y, line_fs)
        elif mode == "progressive":
            self._draw_progressive(text_img, line, line_idx, word_idx, v, font_size)
        else:
            self._draw_karaoke(text_img, line, line_idx, word_idx, v, font_size)

        text_img = self._apply_animation_transforms(text_img, anim)

        if anim.opacity < 1.0:
            alpha = text_img.split()[3]
            alpha = alpha.point(lambda a: int(a * anim.opacity))
            text_img.putalpha(alpha)

        ox = int(anim.position[0])
        oy = int(anim.position[1])
        if ox != 0 or oy != 0:
            canvas = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            canvas.paste(text_img, (ox, oy))
            text_img = canvas

        img_rgba = img.convert("RGBA")
        img_rgba = Image.alpha_composite(img_rgba, text_img)
        img = img_rgba.convert("RGB")

        return img

    def _get_bg_for_section(self, line_idx: int, bg_cache: dict, t: float = 0.0) -> Image.Image:
        self._init_bg_source()

        if self._bg_source is not None:
            bg_frame = self._bg_source.get_frame_pil(t)
            if bg_frame is not None:
                if bg_frame.size != (self.width, self.height):
                    bg_frame = bg_frame.resize((self.width, self.height), Image.LANCZOS)
                return bg_frame

        sec = self._find_section(line_idx) if line_idx >= 0 else None
        if sec:
            sec_key = (sec.get("name", "__none__"), line_idx)
        else:
            sec_key = "__default__"

        if sec_key not in bg_cache:
            bg = Image.new("RGB", (self.width, self.height), (10, 10, 30))

            if line_idx >= 0:
                v = self.get_visual(line_idx, 0)
            else:
                v = dict(self.defaults)

            self._draw_background(bg, v)

            bg_cache[sec_key] = bg

        return bg_cache[sec_key]

    def render(self, output_path: str | Path, audio_path: Optional[str | Path] = None,
               time_start: Optional[float] = None, time_end: Optional[float] = None) -> Path:
        from render.encoder import VideoEncoder

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        audio = audio_path or self.audio_path

        t_start = time_start if time_start is not None else 0.0
        t_end = time_end if time_end is not None else self.duration

        start_frame = int(t_start * self.fps)
        end_frame = int(t_end * self.fps)
        total_frames = end_frame - start_frame + 1

        bg_cache: dict = {}
        prev_bytes: Optional[bytes] = None
        prev_key: Optional[tuple] = None
        rendered = 0
        reused = 0

        with VideoEncoder(output_path, self.width, self.height, self.fps, audio) as enc:
            pbar = tqdm(
                range(total_frames),
                unit="frame",
                desc="Rendering",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}",
            )
            for offset_idx in pbar:
                frame_idx = start_frame + offset_idx
                t = frame_idx / self.fps
                line_idx, word_idx = self._find_active_word(t)

                intro_duration = self.script.get("intro", {}).get("duration", 0.0)
                in_intro = line_idx < 0 and t < intro_duration

                has_animation = self._frame_is_unique(line_idx) or in_intro
                if line_idx < 0 and has_animation:
                    gap_bucket = frame_idx // max(1, self.fps // 4)
                    key = (line_idx, word_idx, gap_bucket)
                elif has_animation:
                    key = (line_idx, word_idx, frame_idx)

                if key == prev_key and prev_bytes is not None:
                    enc.write_frame(prev_bytes)
                    reused += 1
                else:
                    bg = self._get_bg_for_section(line_idx, bg_cache, t)
                    img = self._render_text_on_bg(bg, line_idx, word_idx, t)
                    frame_bytes = img.tobytes()
                    enc.write_frame(frame_bytes)
                    prev_bytes = frame_bytes
                    rendered += 1

                prev_key = key

                if frame_idx % self.fps == 0:
                    sec = self._find_section(line_idx) if line_idx >= 0 else None
                    sec_name = sec["name"] if sec else "—"
                    lyric = ""
                    if line_idx >= 0 and line_idx < len(self.synced.get("lines", [])):
                        lyric = self.synced["lines"][line_idx]["text"][:40]
                    pbar.set_postfix_str(f"{sec_name} | {lyric}")

        unique_pct = rendered / max(1, total_frames) * 100
        tqdm.write(f"  Rendered {rendered} unique frames, reused {reused} ({unique_pct:.0f}% unique)")
        return output_path
