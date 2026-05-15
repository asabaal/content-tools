from __future__ import annotations

import colorsys
import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from tqdm import tqdm


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


def _find_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
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
        self._font_cache: Dict[int, ImageFont.FreeTypeFont] = {}
        self.font = self._get_font(48)

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        if size not in self._font_cache:
            self._font_cache[size] = _find_font(size)
        return self._font_cache[size]
    def load(self) -> None:
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

    def _draw_text_line(self, img: Image.Image, text: str, v: Dict, y: int, font_size: int) -> None:
        draw = ImageDraw.Draw(img)
        font = self._get_font(font_size)
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

    def _draw_karaoke(self, img: Image.Image, line: Dict, word_idx: int, v: Dict, y: int, font_size: int) -> None:
        draw = ImageDraw.Draw(img)
        font = self._get_font(font_size)
        words = line["words"]
        cs = self.caption_style
        auto_contrast = v.get("text_auto_contrast", True)
        base_hex = _contrast_color(v.get("background_color", "#1a1a2e")) if auto_contrast is not False else v.get("text_color", cs.get("text_color", "#ffffff"))
        hl_hex = cs.get("highlight_color", "#4cc9f0")
        dim_hex = base_hex + "44" if len(base_hex) == 7 else base_hex
        base_rgb = _hex_to_rgb(base_hex)
        hl_rgb = _hex_to_rgb(hl_hex)

        spacing = cs.get("letter_spacing", 1) * (self.height / 1080) * 4
        widths = [draw.textbbox((0, 0), w["text"], font=font)[2] for w in words]
        total_w = sum(widths) + spacing * max(0, len(words) - 1)
        x = (self.width - total_w) / 2

        for j, w in enumerate(words):
            wW = widths[j]
            cx = x + wW / 2
            is_active = j == word_idx
            rgb = hl_rgb if is_active else base_rgb
            if cs.get("outline"):
                ow = cs.get("outline_width", 2)
                oc = _hex_to_rgb(cs.get("outline_color", "#000000"))
                for dx in range(-ow, ow + 1):
                    for dy in range(-ow, ow + 1):
                        if dx == 0 and dy == 0:
                            continue
                        draw.text((cx - wW / 2 + dx, y + dy), w["text"], fill=oc, font=font, anchor="lm")
            if cs.get("text_shadow"):
                sc = _hex_to_rgb(cs.get("text_shadow_color", "#000000"))
                sf = self.height / 1080
                draw.text((cx - wW / 2 + 2 * sf, y + 2 * sf), w["text"], fill=sc, font=font, anchor="lm")
            draw.text((cx - wW / 2, y), w["text"], fill=rgb, font=font, anchor="lm")
            x += wW + spacing

    def _draw_progressive(self, img: Image.Image, line: Dict, word_idx: int, v: Dict, y: int, font_size: int) -> None:
        draw = ImageDraw.Draw(img)
        font = self._get_font(font_size)
        words = line["words"]
        cs = self.caption_style
        auto_contrast = v.get("text_auto_contrast", True)
        base_hex = _contrast_color(v.get("background_color", "#1a1a2e")) if auto_contrast is not False else v.get("text_color", cs.get("text_color", "#ffffff"))
        hl_hex = cs.get("highlight_color", "#4cc9f0")
        base_rgb = _hex_to_rgb(base_hex)
        hl_rgb = _hex_to_rgb(hl_hex)

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

        spacing = cs.get("letter_spacing", 1) * (self.height / 1080) * 4
        widths = [draw.textbbox((0, 0), w["text"], font=font)[2] for w in vis]
        total_w = sum(widths) + spacing * max(0, len(vis) - 1)
        x = (self.width - total_w) / 2

        for j, w in enumerate(vis):
            wW = widths[j]
            orig_idx = start + j if slide else j
            is_active = orig_idx >= group_start and orig_idx <= word_idx
            rgb = hl_rgb if is_active else base_rgb
            cx = x + wW / 2
            if cs.get("outline"):
                ow = cs.get("outline_width", 2)
                oc = _hex_to_rgb(cs.get("outline_color", "#000000"))
                for dx in range(-ow, ow + 1):
                    for dy in range(-ow, ow + 1):
                        if dx == 0 and dy == 0:
                            continue
                        draw.text((cx - wW / 2 + dx, y + dy), w["text"], fill=oc, font=font, anchor="lm")
            if cs.get("text_shadow"):
                sc = _hex_to_rgb(cs.get("text_shadow_color", "#000000"))
                sf = self.height / 1080
                draw.text((cx - wW / 2 + 2 * sf, y + 2 * sf), w["text"], fill=sc, font=font, anchor="lm")
            draw.text((cx - wW / 2, y), w["text"], fill=rgb, font=font, anchor="lm")
            x += wW + spacing

    def render_frame(self, t: float) -> Image.Image:
        img = Image.new("RGB", (self.width, self.height), (10, 10, 30))
        line_idx, word_idx = self._find_active_word(t)

        if line_idx < 0:
            v = dict(self.defaults)
            self._draw_background(img, v)
            return img

        v = self.get_visual(line_idx, word_idx)
        self._draw_background(img, v)

        line = self.synced["lines"][line_idx]
        font_size = int((v.get("font_size", self.caption_style.get("font_size", 48))) * (self.height / 1080))

        pos = self.caption_style.get("text_position", "center")
        if pos == "top":
            y = int(self.height * 0.2)
        elif pos == "bottom":
            y = int(self.height * 0.8)
        else:
            y = self.height // 2

        mode = self._get_reveal_mode(v)

        if mode == "line-by-line":
            self._draw_text_line(img, line["text"], v, y, font_size)
        elif mode == "progressive":
            self._draw_progressive(img, line, word_idx, v, y, font_size)
        else:
            self._draw_karaoke(img, line, word_idx, v, y, font_size)

        return img

    def _render_text_on_bg(self, bg: Image.Image, line_idx: int, word_idx: int) -> Image.Image:
        img = bg.copy()
        if line_idx < 0:
            return img

        line = self.synced["lines"][line_idx]
        v = self.get_visual(line_idx, word_idx)
        font_size = int((v.get("font_size", self.caption_style.get("font_size", 48))) * (self.height / 1080))

        pos = self.caption_style.get("text_position", "center")
        if pos == "top":
            y = int(self.height * 0.2)
        elif pos == "bottom":
            y = int(self.height * 0.8)
        else:
            y = self.height // 2

        mode = self._get_reveal_mode(v)

        if mode == "line-by-line":
            self._draw_text_line(img, line["text"], v, y, font_size)
        elif mode == "progressive":
            self._draw_progressive(img, line, word_idx, v, y, font_size)
        else:
            self._draw_karaoke(img, line, word_idx, v, y, font_size)

        return img

    def _get_bg_for_section(self, line_idx: int, bg_cache: dict) -> Image.Image:
        sec = self._find_section(line_idx) if line_idx >= 0 else None
        sec_key = sec.get("name", "__none__") if sec else "__default__"

        if sec_key not in bg_cache:
            bg = Image.new("RGB", (self.width, self.height), (10, 10, 30))
            if line_idx >= 0:
                v = self.get_visual(line_idx, 0)
            else:
                v = dict(self.defaults)
            self._draw_background(bg, v)
            bg_cache[sec_key] = bg

        return bg_cache[sec_key]

    def render(self, output_path: str | Path, audio_path: Optional[str | Path] = None) -> Path:
        from render.encoder import VideoEncoder

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        audio = audio_path or self.audio_path

        total_frames = int(self.duration * self.fps) + 1

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
            for frame_idx in pbar:
                t = frame_idx / self.fps
                line_idx, word_idx = self._find_active_word(t)
                key = (line_idx, word_idx)

                if key == prev_key and prev_bytes is not None:
                    enc.write_frame(prev_bytes)
                    reused += 1
                else:
                    bg = self._get_bg_for_section(line_idx, bg_cache)
                    img = self._render_text_on_bg(bg, line_idx, word_idx)
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
