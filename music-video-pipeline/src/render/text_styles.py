from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class TextStyle(Enum):
    MODERN_BOLD = "modern_bold"
    NEON_GLOW = "neon_glow"
    ELEGANT_GOLD = "elegant_gold"
    HIP_HOP = "hip_hop"
    CLEAN_WHITE = "clean_white"
    DRAMATIC_RED = "dramatic_red"


@dataclass
class StyleConfig:
    fill_color: Tuple[int, int, int, int]
    outline_color: Tuple[int, int, int, int]
    outline_width: int
    shadow_color: Tuple[int, int, int, int] | None
    shadow_offset: Tuple[int, int]
    shadow_blur: int
    glow_color: Tuple[int, int, int, int] | None
    glow_radius: int


_STYLE_CONFIGS: dict[TextStyle, StyleConfig] = {
    TextStyle.MODERN_BOLD: StyleConfig(
        fill_color=(255, 255, 255, 255),
        outline_color=(0, 0, 0, 255),
        outline_width=2,
        shadow_color=(0, 0, 0, 180),
        shadow_offset=(4, 4),
        shadow_blur=7,
        glow_color=None,
        glow_radius=0,
    ),
    TextStyle.NEON_GLOW: StyleConfig(
        fill_color=(255, 255, 255, 255),
        outline_color=(255, 0, 255, 255),
        outline_width=1,
        shadow_color=None,
        shadow_offset=(0, 0),
        shadow_blur=0,
        glow_color=(255, 0, 255, 120),
        glow_radius=15,
    ),
    TextStyle.ELEGANT_GOLD: StyleConfig(
        fill_color=(0, 215, 255, 255),
        outline_color=(0, 100, 150, 255),
        outline_width=2,
        shadow_color=(0, 0, 0, 200),
        shadow_offset=(3, 3),
        shadow_blur=7,
        glow_color=(0, 255, 255, 60),
        glow_radius=8,
    ),
    TextStyle.HIP_HOP: StyleConfig(
        fill_color=(0, 255, 255, 255),
        outline_color=(0, 0, 0, 255),
        outline_width=3,
        shadow_color=(128, 0, 128, 150),
        shadow_offset=(6, 6),
        shadow_blur=7,
        glow_color=None,
        glow_radius=0,
    ),
    TextStyle.CLEAN_WHITE: StyleConfig(
        fill_color=(255, 255, 255, 255),
        outline_color=(64, 64, 64, 255),
        outline_width=1,
        shadow_color=(0, 0, 0, 120),
        shadow_offset=(2, 2),
        shadow_blur=5,
        glow_color=None,
        glow_radius=0,
    ),
    TextStyle.DRAMATIC_RED: StyleConfig(
        fill_color=(0, 0, 255, 255),
        outline_color=(0, 0, 139, 255),
        outline_width=2,
        shadow_color=(0, 0, 0, 200),
        shadow_offset=(4, 4),
        shadow_blur=7,
        glow_color=(0, 0, 255, 100),
        glow_radius=10,
    ),
}


def _find_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _pil_to_cv2_alpha(pil_img: Image.Image) -> np.ndarray:
    arr = np.array(pil_img.convert("RGBA"))
    return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)


def _cv2_to_pil(bgra: np.ndarray) -> Image.Image:
    rgba = cv2.cvtColor(bgra, cv2.COLOR_BGRA2RGBA)
    return Image.fromarray(rgba)


def _render_text_base(
    text: str,
    font_size: int,
    width: int,
    height: int,
    color: Tuple[int, int, int, int],
) -> np.ndarray:
    font = _find_font(font_size)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (width - tw) // 2
    y = (height - th) // 2
    draw.text((x, y), text, fill=color, font=font)
    return _pil_to_cv2_alpha(img)


def _alpha_blend(dest: np.ndarray, src: np.ndarray) -> None:
    if src.shape[2] == 4:
        alpha = src[:, :, 3:4].astype(np.float32) / 255.0
        dest[:, :, :3] = (dest[:, :, :3].astype(np.float32) * (1 - alpha) + src[:, :, :3].astype(np.float32) * alpha).astype(np.uint8)
        dest[:, :, 3:4] = np.maximum(dest[:, :, 3:4], src[:, :, 3:4])


def _render_shadow(
    frame: np.ndarray,
    text: str,
    font_size: int,
    width: int,
    height: int,
    config: StyleConfig,
) -> None:
    if not config.shadow_color:
        return
    shadow = _render_text_base(text, font_size, width, height, config.shadow_color)
    ox, oy = config.shadow_offset
    k = config.shadow_blur
    if k > 0:
        for c in range(4):
            shadow[:, :, c] = cv2.GaussianBlur(shadow[:, :, c], (k * 2 + 1, k * 2 + 1), 0)
    shifted = np.zeros_like(frame)
    sx = min(ox, width)
    sy = min(oy, height)
    ex = min(width, width + sx)
    ey = min(height, height + sy)
    shifted[sy:ey, sx:ex] = shadow[sy - oy : ey - oy, sx - ox : ex - ox]
    _alpha_blend(frame, shifted)


def _render_glow(
    frame: np.ndarray,
    text: str,
    font_size: int,
    width: int,
    height: int,
    config: StyleConfig,
) -> None:
    if not config.glow_color or config.glow_radius <= 0:
        return
    for radius in range(config.glow_radius, 0, -2):
        alpha = int(config.glow_color[3] * (1.0 - radius / config.glow_radius))
        glow_col = (config.glow_color[0], config.glow_color[1], config.glow_color[2], alpha)
        glow = _render_text_base(text, font_size + radius, width, height, glow_col)
        k = max(1, radius * 2 + 1)
        glow = cv2.GaussianBlur(glow, (k, k), radius / 3.0)
        _alpha_blend(frame, glow)


def _render_outline(
    frame: np.ndarray,
    text: str,
    font_size: int,
    width: int,
    height: int,
    config: StyleConfig,
) -> None:
    if config.outline_width <= 0:
        return
    outline = _render_text_base(text, font_size, width, height, config.outline_color)
    gray = cv2.cvtColor(outline, cv2.COLOR_BGRA2GRAY)
    _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    kernel_size = config.outline_width * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    dilated = cv2.dilate(mask, kernel, iterations=1)
    dilated_rgba = cv2.cvtColor(dilated, cv2.COLOR_GRAY2BGRA)
    dilated_rgba[:, :, 0] = config.outline_color[0]
    dilated_rgba[:, :, 1] = config.outline_color[1]
    dilated_rgba[:, :, 2] = config.outline_color[2]
    dilated_rgba[:, :, 3] = np.where(dilated > 0, config.outline_color[3], 0)
    _alpha_blend(frame, dilated_rgba)
    _alpha_blend(frame, outline)


def _render_fill(
    frame: np.ndarray,
    text: str,
    font_size: int,
    width: int,
    height: int,
    config: StyleConfig,
) -> None:
    fill = _render_text_base(text, font_size, width, height, config.fill_color)
    _alpha_blend(frame, fill)


def get_style_config(style: TextStyle) -> StyleConfig:
    return _STYLE_CONFIGS.get(style, _STYLE_CONFIGS[TextStyle.CLEAN_WHITE])


def render_styled_text(
    text: str,
    font_size: int,
    style: TextStyle,
    width: int = 1920,
    height: int = 1080,
) -> Image.Image:
    config = get_style_config(style)
    frame = np.zeros((height, width, 4), dtype=np.uint8)
    _render_shadow(frame, text, font_size, width, height, config)
    _render_glow(frame, text, font_size, width, height, config)
    _render_outline(frame, text, font_size, width, height, config)
    _render_fill(frame, text, font_size, width, height, config)
    return _cv2_to_pil(frame)
