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
            if elapsed < enter_duration:
                p = min(1.0, elapsed / enter_duration)
            else:
                p = 1.0
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
            self._draw_gradient(img, colors, direction)
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

    def _draw_gradient(self, img: Image.Image, colors: List[str], direction: str) -> None:
        arr = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        rgbs = [_hex_to_rgb(c) for c in colors]
        n = len(rgbs)

        if direction in ("vertical_top_bottom", "vertical_bottom_top"):
            for y in range(self.height):
                t = y / max(1, self.height - 1)
                if direction == "vertical_bottom_top":
                    t = 1 - t
                ci = t * (n - 1)
                lo = int(ci)
                hi = min(lo + 1, n - 1)
                f = ci - lo
                r = int(rgbs[lo][0] * (1 - f) + rgbs[hi][0] * f)
                g = int(rgbs[lo][1] * (1 - f) + rgbs[hi][1] * f)
                b = int(rgbs[lo][2] * (1 - f) + rgbs[hi][2] * f)
                arr[y, :] = [r, g, b]
        elif direction in ("horizontal_left_right", "horizontal_right_left"):
            for x in range(self.width):
                t = x / max(1, self.width - 1)
                if direction == "horizontal_right_left":
                    t = 1 - t
                ci = t * (n - 1)
                lo = int(ci)
                hi = min(lo + 1, n - 1)
                f = ci - lo
                r = int(rgbs[lo][0] * (1 - f) + rgbs[hi][0] * f)
                g = int(rgbs[lo][1] * (1 - f) + rgbs[hi][1] * f)
                b = int(rgbs[lo][2] * (1 - f) + rgbs[hi][2] * f)
                arr[:, x] = [r, g, b]
        elif direction in ("diagonal_tl_br", "diagonal_tr_bl"):
            for y in range(self.height):
                for x in range(self.width):
                    t = (x + y) / max(1, self.width + self.height - 2)
                    if direction == "diagonal_tr_bl":
                        t = 1 - t
                    ci = t * (n - 1)
                    lo = int(ci)
                    hi = min(lo + 1, n - 1)
                    f = ci - lo
                    r = int(rgbs[lo][0] * (1 - f) + rgbs[hi][0] * f)
                    g = int(rgbs[lo][1] * (1 - f) + rgbs[hi][1] * f)
                    b = int(rgbs[lo][2] * (1 - f) + rgbs[hi][2] * f)
                    arr[y, x] = [r, g, b]
        else:
            cx, cy = self.width / 2, self.height / 2
            max_r = math.sqrt(cx * cx + cy * cy)
            ys, xs = np.ogrid[:self.height, :self.width]
            if direction == "radial_top":
                dist = np.sqrt((xs - cx) ** 2 + ys ** 2)
            elif direction == "radial_bottom":
                dist = np.sqrt((xs - cx) ** 2 + (ys - self.height) ** 2)
            else:
                dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
            t = np.clip(dist / max_r, 0, 1)
            ci = t * (n - 1)
            lo = np.floor(ci).astype(int)
            hi = np.minimum(lo + 1, n - 1)
            f = (ci - lo)[:, :, np.newaxis] if ci.ndim == 2 else (ci - lo)
            if f.ndim == 2:
                f = f[:, :, np.newaxis]
            elif f.ndim == 0:
                f = np.array([[[float(f)]]])
            rgb_arr = np.array(rgbs, dtype=np.float32)
            blended = rgb_arr[lo] * (1 - f) + rgb_arr[hi] * f
            arr = np.clip(blended, 0, 255).astype(np.uint8)

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

    def _get_styled_text(self, text: str, style: str, size: int, family: int = 0) -> Image.Image:
        key = (text, style, size, family)
        if key not in self._styled_cache:
            self._styled_cache[key] = generate_styled_text(text, style, size, family=family)
        return self._styled_cache[key]

    def _compute_line_layout(self, words: list, font: ImageFont.FreeTypeFont, spacing: float, text_align: str = "center") -> list:
        widths = [font.getbbox(w["text"])[2] for w in words]
        total_w = sum(widths) + spacing * max(0, len(words) - 1)
        if text_align == "left":
            x = self.width * 0.1
        elif text_align == "right":
            x = self.width * 0.9 - total_w
        else:
            x = (self.width - total_w) / 2
        positions = []
        for j in range(len(words)):
            cx = x + widths[j] / 2
            positions.append((cx, widths[j]))
            x += widths[j] + spacing
        return positions

    def _scale_font_to_fill(
        self,
        words: list,
        base_font_size: int,
        font_family: int,
        target_fill: float = 0.75,
        max_scale: float = 1.8,
    ) -> tuple:
        min_size = base_font_size
        spacing = self.caption_style.get("letter_spacing", 1) * (self.height / 1080) * 4
        target_w = self.width * target_fill
        for _ in range(8):
            font = self._get_font(min_size, font_family)
            widths = [font.getbbox(w["text"])[2] for w in words]
            total_w = sum(widths) + spacing * max(0, len(words) - 1)
            if total_w >= target_w:
                break
            scale = target_w / max(1, total_w)
            min_size = min(int(min_size * scale), int(base_font_size * max_scale))
            if min_size <= base_font_size:
                break
        font = self._get_font(min_size, font_family)
        return font, min_size

    def _compute_multirow_layout(
        self,
        words: list,
        line_idx: int,
        font: ImageFont.FreeTypeFont,
        spacing: float,
        text_align: str = "center",
        target_fill: float = 0.70,
    ) -> list:
        cs = self.caption_style
        default_pos = cs.get("text_position", "center")
        word_positions = []
        for wi in range(len(words)):
            v = self.get_visual(line_idx, wi)
            pos = v.get("text_position", default_pos)
            word_positions.append(pos)

        unique_rows = []
        seen = set()
        for p in word_positions:
            if p not in seen:
                unique_rows.append(p)
                seen.add(p)

        if len(unique_rows) <= 1:
            return self._compute_line_layout(words, font, spacing, text_align)

        groups: list[list[int]] = []
        current_group = [0]
        for i in range(1, len(words)):
            if word_positions[i] == word_positions[i - 1]:
                current_group.append(i)
            else:
                groups.append(current_group)
                current_group = [i]
        groups.append(current_group)

        widths = [font.getbbox(w["text"])[2] for w in words]
        target_w = self.width * target_fill
        result = [(0.0, 0)] * len(words)

        for group in groups:
            group_widths = [widths[i] for i in group]
            text_w = sum(group_widths)
            n_gaps = max(1, len(group) - 1)
            gap_count = n_gaps if n_gaps > 0 else 1
            group_spacing = max(spacing, (target_w - text_w) / gap_count)
            total_w = text_w + group_spacing * n_gaps
            x = (self.width - total_w) / 2
            for j, wi in enumerate(group):
                cx = x + group_widths[j] / 2
                result[wi] = (cx, group_widths[j])
                x += group_widths[j] + group_spacing

        return result

    def _draw_text_line(self, img: Image.Image, text: str, v: Dict, y: int, font_size: int) -> None:
        if self._has_styled_text(v):
            family = v.get("font_family", 0)
            styled = self._get_styled_text(text, v["text_style"], font_size, family)
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
        font = self._get_font(font_size, font_family)
        spacing = cs.get("letter_spacing", 1) * (self.height / 1080) * 4
        all_positions = self._compute_multirow_layout(words, line_idx, font, spacing)

        if self._has_styled_text(v):
            for j, w in enumerate(words):
                cx, wW = all_positions[j]
                word_v = self.get_visual(line_idx, j)
                word_y = self._y_for_pos(word_v.get("text_position", cs.get("text_position", "center")))
                is_active = j == word_idx
                word_size = font_size
                delta = word_v.get("font_size_delta", 0)
                if delta:
                    word_size = max(24, word_size + int(delta * (self.height / 1080)))
                opacity = 1.0 if is_active else 0.75
                styled = self._get_styled_text(w["text"], text_style, word_size, font_family).copy()
                sw, sh = styled.size
                px = int(cx - sw / 2)
                py = int(word_y - sh / 2)
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
            cx, wW = all_positions[j]
            is_active = j == word_idx
            rgb = hl_rgb if is_active else base_rgb
            word_v = self.get_visual(line_idx, j)
            word_y = self._y_for_pos(word_v.get("text_position", cs.get("text_position", "center")))
            if cs.get("outline"):
                ow = cs.get("outline_width", 2)
                oc = _hex_to_rgb(cs.get("outline_color", "#000000"))
                for dx in range(-ow, ow + 1):
                    for dy in range(-ow, ow + 1):
                        if dx == 0 and dy == 0:
                            continue
                        draw.text((cx - wW / 2 + dx, word_y + dy), w["text"], fill=oc, font=font, anchor="lm")
            if cs.get("text_shadow"):
                sc = _hex_to_rgb(cs.get("text_shadow_color", "#000000"))
                sf = self.height / 1080
                draw.text((cx - wW / 2 + 2 * sf, word_y + 2 * sf), w["text"], fill=sc, font=font, anchor="lm")
            draw.text((cx - wW / 2, word_y), w["text"], fill=rgb, font=font, anchor="lm")

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

        font = self._get_font(font_size, font_family)
        spacing = cs.get("letter_spacing", 1) * (self.height / 1080) * 4
        text_align = v.get("text_align", "center")
        all_positions = self._compute_multirow_layout(words, line_idx, font, spacing, text_align)

        if not slide:
            visible_range = range(0, min(word_idx + 1, len(words)))
        else:
            visible_range = range(start, min(start + step * 2, len(words)))

        if self._has_styled_text(v):
            for idx in visible_range:
                cx, wW = all_positions[idx]
                is_active = idx >= group_start and idx <= word_idx
                word_v = self.get_visual(line_idx, idx)
                word_y = self._y_for_pos(word_v.get("text_position", cs.get("text_position", "center")))
                word_size = font_size
                delta = word_v.get("font_size_delta", 0)
                if delta:
                    word_size = max(24, word_size + int(delta * (self.height / 1080)))
                opacity = 1.0 if is_active else 0.8
                styled = self._get_styled_text(words[idx]["text"], text_style, word_size, font_family).copy()
                sw, sh = styled.size
                px = int(cx - sw / 2)
                py = int(word_y - sh / 2)
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
            cx, wW = all_positions[idx]
            is_active = idx >= group_start and idx <= word_idx
            rgb = hl_rgb if is_active else base_rgb
            word_v = self.get_visual(line_idx, idx)
            word_y = self._y_for_pos(word_v.get("text_position", cs.get("text_position", "center")))
            if cs.get("outline"):
                ow = cs.get("outline_width", 2)
                oc = _hex_to_rgb(cs.get("outline_color", "#000000"))
                for dx in range(-ow, ow + 1):
                    for dy in range(-ow, ow + 1):
                        if dx == 0 and dy == 0:
                            continue
                        draw.text((cx - wW / 2 + dx, word_y + dy), words[idx]["text"], fill=oc, font=font, anchor="lm")
            if cs.get("text_shadow"):
                sc = _hex_to_rgb(cs.get("text_shadow_color", "#000000"))
                sf = self.height / 1080
                draw.text((cx - wW / 2 + 2 * sf, word_y + 2 * sf), words[idx]["text"], fill=sc, font=font, anchor="lm")
            draw.text((cx - wW / 2, word_y), words[idx]["text"], fill=rgb, font=font, anchor="lm")

    def _render_intro_frame(self, t: float) -> Optional[Image.Image]:
        intro = self.script.get("intro")
        if not intro:
            return None
        duration = intro.get("duration", 0.0)
        if duration <= 0 or t >= duration:
            return None

        img = Image.new("RGB", (self.width, self.height), (10, 10, 30))

        phase1_end = duration * 0.60
        phase1_fade_in = duration * 0.12
        phase1_fade_out_start = duration * 0.52
        phase2_start = duration * 0.65
        phase2_fade_in = phase2_start + duration * 0.04
        phase2_fade_out_start = duration * 0.88

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

            opacity = 1.0
            if t < phase1_fade_in:
                opacity = t / max(0.01, phase1_fade_in)
            elif t > phase1_fade_out_start:
                opacity = 1.0 - (t - phase1_fade_out_start) / max(0.01, phase1_end - phase1_fade_out_start)
            opacity = max(0.0, min(1.0, opacity))

            title = intro.get("title", "")
            if title and opacity > 0.01:
                font_size = int(80 * (self.height / 1080))
                font = self._get_font(font_size, family=3)
                txt_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(txt_layer)
                bbox = draw.textbbox((0, 0), title, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                cx = (self.width - tw) / 2
                cy = self.height * 0.78
                shadow_offset = max(2, int(3 * (self.height / 1080)))
                draw.text((cx + shadow_offset, cy + shadow_offset), title, fill=(0, 0, 0, int(200 * opacity)), font=font)
                draw.text((cx, cy), title, fill=(255, 255, 255, int(255 * opacity)), font=font)
                img_rgba = img.convert("RGBA")
                img_rgba = Image.alpha_composite(img_rgba, txt_layer)
                img = img_rgba.convert("RGB")

            if opacity < 1.0:
                black = Image.new("RGB", (self.width, self.height), (10, 10, 30))
                img = Image.blend(black, img, opacity)

        elif t >= phase2_start:
            v_bg = dict(self.defaults)
            self._draw_background(img, v_bg)

            opacity = 1.0
            if t < phase2_fade_in:
                opacity = (t - phase2_start) / max(0.01, phase2_fade_in - phase2_start)
            elif t > phase2_fade_out_start:
                opacity = 1.0 - (t - phase2_fade_out_start) / max(0.01, duration - phase2_fade_out_start)
            opacity = max(0.0, min(1.0, opacity))

            subtitle = intro.get("subtitle", "")
            if subtitle and opacity > 0.01:
                font_size = int(44 * (self.height / 1080))
                font = self._get_font(font_size, family=5)
                txt_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(txt_layer)
                bbox = draw.textbbox((0, 0), subtitle, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                cx = (self.width - tw) / 2
                cy = (self.height - th) / 2
                shadow_offset = max(2, int(2 * (self.height / 1080)))
                draw.text((cx + shadow_offset, cy + shadow_offset), subtitle, fill=(0, 0, 0, int(180 * opacity)), font=font)
                draw.text((cx, cy), subtitle, fill=(220, 220, 230, int(255 * opacity)), font=font)
                img_rgba = img.convert("RGBA")
                img_rgba = Image.alpha_composite(img_rgba, txt_layer)
                img = img_rgba.convert("RGB")

            if opacity < 1.0:
                black = Image.new("RGB", (self.width, self.height), (10, 10, 30))
                img = Image.blend(black, img, opacity)
        else:
            v_bg = dict(self.defaults)
            self._draw_background(img, v_bg)

        return img

    def render_frame(self, t: float) -> Image.Image:
        img = Image.new("RGB", (self.width, self.height), (10, 10, 30))
        line_idx, word_idx = self._find_active_word(t)

        if line_idx < 0:
            intro_frame = self._render_intro_frame(t)
            if intro_frame is not None:
                intro_frame = self._apply_bg_motion(intro_frame, t, dict(self.defaults))
                return intro_frame
            v = dict(self.defaults)
            if not v.get("bg_animation_preset"):
                sections = self.script.get("sections", [])
                if sections:
                    sv = sections[0].get("visual", {})
                    v["bg_animation_preset"] = sv.get("bg_animation_preset", "ambient")
                    v["reactivity"] = sv.get("reactivity", ["energy"])
                else:
                    v["bg_animation_preset"] = "ambient"
                    v["reactivity"] = ["energy"]
            self._draw_background(img, v)
            img = self._apply_bg_motion(img, t, v)
            return img

        v = self.get_visual(line_idx, word_idx)
        self._draw_background(img, v)
        img = self._apply_bg_motion(img, t, v)

        line = self.synced["lines"][line_idx]
        font_size = int((v.get("font_size", self.caption_style.get("font_size", 112))) * (self.height / 1080))
        font_family = v.get("font_family", 0)
        scaled_font, font_size = self._scale_font_to_fill(
            line["words"], font_size, font_family, target_fill=0.75, max_scale=1.8,
        )

        anim = self._compute_animation_progress(t, line_idx)

        text_img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        mode = self._get_reveal_mode(v)

        if mode == "line-by-line":
            pos = v.get("text_position", self.caption_style.get("text_position", "center"))
            y = self._y_for_pos(pos)
            self._draw_text_line(text_img, line["text"], v, y, font_size)
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
            intro_frame = self._render_intro_frame(t)
            v_gap = dict(self.defaults)
            if not v_gap.get("bg_animation_preset"):
                sections = self.script.get("sections", [])
                if sections:
                    sv = sections[0].get("visual", {})
                    v_gap["bg_animation_preset"] = sv.get("bg_animation_preset", "ambient")
                    v_gap["reactivity"] = sv.get("reactivity", ["energy"])
                else:
                    v_gap["bg_animation_preset"] = "ambient"
                    v_gap["reactivity"] = ["energy"]
            if intro_frame is not None:
                return self._apply_bg_motion(intro_frame, t, v_gap)
            img = bg.copy()
            img = self._apply_bg_motion(img, t, v_gap)
            return img

        img = bg.copy()
        v = self.get_visual(line_idx, word_idx)
        img = self._apply_bg_motion(img, t, v)

        line = self.synced["lines"][line_idx]
        font_size = int((v.get("font_size", self.caption_style.get("font_size", 112))) * (self.height / 1080))
        font_family = v.get("font_family", 0)
        _, font_size = self._scale_font_to_fill(
            line["words"], font_size, font_family, target_fill=0.75, max_scale=1.8,
        )

        anim = self._compute_animation_progress(t, line_idx)

        text_img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        mode = self._get_reveal_mode(v)

        if mode == "line-by-line":
            pos = v.get("text_position", self.caption_style.get("text_position", "center"))
            y = self._y_for_pos(pos)
            self._draw_text_line(text_img, line["text"], v, y, font_size)
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
        sec_key = sec.get("name", "__none__") if sec else "__default__"

        if sec_key not in bg_cache:
            bg = Image.new("RGB", (self.width, self.height), (10, 10, 30))

            if line_idx >= 0:
                v = self.get_visual(line_idx, 0)
            else:
                v = dict(self.defaults)

            broll_image = v.get("broll_image", "")
            broll_blend = v.get("broll_blend", 0.35)

            if broll_image:
                base_v = {
                    "background_type": "image",
                    "background_image": broll_image,
                    "background_image_opacity": 1.0,
                    "background_image_fit": "cover",
                    "background_color": v.get("background_color", "#000000"),
                }
                self._draw_background(bg, base_v)

                section_bg = Image.new("RGB", (self.width, self.height), (10, 10, 30))
                self._draw_background(section_bg, v)
                bg = Image.blend(bg, section_bg, broll_blend)
            else:
                self._draw_background(bg, v)

            self._draw_texture(bg, v)
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
                else:
                    key = (line_idx, word_idx)

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
