from __future__ import annotations

import colorsys
import math
import random
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class FontStyle(Enum):
    NEON = "neon"
    GRAFFITI = "graffiti"
    CHROME = "chrome"
    FIRE = "fire"
    ICE = "ice"
    GOLD = "gold"
    HOLOGRAM = "hologram"
    MATRIX = "matrix"
    BASIC = "basic"


_FONTS_DIR = Path(__file__).resolve().parent.parent.parent / "fonts"

_FONT_FILES = {
    1: ("Exo2-Bold.ttf", "Exo2-Regular.ttf"),
    2: ("Bangers-Regular.ttf", "Bangers-Regular.ttf"),
    3: ("BebasNeue-Regular.ttf", "BebasNeue-Regular.ttf"),
    4: ("JetBrainsMono-Regular.ttf", "JetBrainsMono-Regular.ttf"),
    5: ("Lora-Bold.ttf", "Lora-Regular.ttf"),
    6: ("Oswald-Bold.ttf", "Oswald-Regular.ttf"),
}


def _find_font(size: int, bold: bool = True, family: int = 0) -> ImageFont.FreeTypeFont:
    if family > 0 and family in _FONT_FILES:
        bold_name, regular_name = _FONT_FILES[family]
        name = bold_name if bold else regular_name
        path = _FONTS_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ]
    if not bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _create_base_text(text: str, size: int, bold: bool = True, family: int = 0) -> np.ndarray:
    font = _find_font(size, bold, family)
    tmp = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tmp)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0] + 4
    th = bbox[3] - bbox[1] + 4
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((-bbox[0] + 2, -bbox[1] + 2), text, fill=(255, 255, 255, 255), font=font)
    return np.array(img)


def _create_outline(image: np.ndarray, thickness: int = 2) -> np.ndarray:
    alpha = image[:, :, 3]
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (thickness * 2 + 1, thickness * 2 + 1)
    )
    dilated = cv2.dilate(alpha, kernel, iterations=1)
    outline = np.zeros_like(image)
    outline[:, :, 3] = dilated
    return outline


def _apply_glow(image: np.ndarray, color: Tuple[int, int, int], radius: int, alpha: int = 100) -> np.ndarray:
    h, w = image.shape[:2]
    glow = np.zeros((h, w, 4), dtype=np.uint8)
    alpha_mask = image[:, :, 3].astype(np.float32) / 255.0
    k = radius * 2 + 1
    for c in range(3):
        glow[:, :, c] = color[c]
    glow[:, :, 3] = (alpha_mask * alpha).astype(np.uint8)
    glow[:, :, 3] = cv2.GaussianBlur(glow[:, :, 3], (k, k), radius / 3.0)
    return glow


def _composite(base: np.ndarray, overlay: np.ndarray, x: int = 0, y: int = 0) -> np.ndarray:
    oh, ow = overlay.shape[:2]
    bh, bw = base.shape[:2]
    y1 = max(0, y)
    y2 = min(bh, y + oh)
    x1 = max(0, x)
    x2 = min(bw, x + ow)
    if y1 >= y2 or x1 >= x2:
        return base
    oy1 = y1 - y
    oy2 = oy1 + (y2 - y1)
    ox1 = x1 - x
    ox2 = ox1 + (x2 - x1)
    src = overlay[oy1:oy2, ox1:ox2].astype(np.float32)
    dst = base[y1:y2, x1:x2].astype(np.float32)
    sa = src[:, :, 3:4] / 255.0
    da = dst[:, :, 3:4] / 255.0
    out_a = sa + da * (1 - sa)
    out_a = np.where(out_a > 0, out_a, 1.0)
    for c in range(3):
        dst[:, :, c] = (src[:, :, c] * sa[:, :, 0] + dst[:, :, c] * da[:, :, 0] * (1 - sa[:, :, 0])) / out_a[:, :, 0]
    dst[:, :, 3] = ((sa[:, :, 0] + da[:, :, 0] * (1 - sa[:, :, 0])) * 255).clip(0, 255)
    base[y1:y2, x1:x2] = dst.astype(np.uint8)
    return base


def _apply_wave_distortion(image: np.ndarray, amplitude: float, frequency: float = 0.1) -> np.ndarray:
    h, w = image.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    x_map = xs + amplitude * np.sin(2 * math.pi * ys * frequency / h)
    y_map = ys.copy()
    return cv2.remap(image, x_map, y_map, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def _generate_neon(text: str, size: int, family: int = 0) -> np.ndarray:
    base = _create_base_text(text, int(size * 1.2), family=family)
    pad = 100
    h, w = base.shape[:2]
    canvas = np.zeros((h + pad * 2, w + pad * 2, 4), dtype=np.uint8)

    layers = [
        ((100, 0, 100), 18, 100),
        ((200, 0, 200), 10, 140),
        ((255, 80, 220), 5, 180),
        ((255, 40, 200), 2, 220),
    ]
    for color, blur_r, alpha_val in reversed(layers):
        glow = _apply_glow(base, color, blur_r, alpha_val)
        _composite(canvas, glow, pad, pad)

    core = base.copy()
    core[:, :, 0] = 255
    core[:, :, 1] = 120
    core[:, :, 2] = 230
    core[:, :, 3] = np.where(core[:, :, 3] > 0, 255, 0)
    _composite(canvas, core, pad, pad)
    return canvas


def _generate_graffiti(text: str, size: int, family: int = 0) -> np.ndarray:
    base = _create_base_text(text, size, family=family)
    pad = 60
    h, w = base.shape[:2]
    canvas = np.zeros((h + pad * 2, w + pad * 2, 4), dtype=np.uint8)

    outline = _create_outline(base, max(1, size // 20))
    outline[:, :, :3] = 0
    outline[:, :, 3] = np.where(outline[:, :, 3] > 0, 255, 0)
    _composite(canvas, outline, pad, pad)

    shadow = base.copy()
    shadow[:, :, :3] = 0
    shadow[:, :, 3] = np.where(shadow[:, :, 3] > 0, 150, 0)
    _composite(canvas, shadow, pad + 5, pad + 5)

    colored = base.copy()
    alpha_mask = colored[:, :, 3] > 0
    for row in range(colored.shape[0]):
        progress = row / max(1, colored.shape[0] - 1)
        r = int(255 * (1 - progress * 0.3))
        g = int(255 * progress)
        colored[row, alpha_mask[row], 0] = r
        colored[row, alpha_mask[row], 1] = g
        colored[row, alpha_mask[row], 2] = 0
    _composite(canvas, colored, pad, pad)
    return canvas


def _generate_chrome(text: str, size: int, family: int = 0) -> np.ndarray:
    base = _create_base_text(text, size, family=family)
    pad = 40
    h, w = base.shape[:2]
    canvas = np.zeros((h + pad * 2, w + pad * 2, 4), dtype=np.uint8)

    glow = _apply_glow(base, (160, 60, 255), 14, 160)
    _composite(canvas, glow, pad, pad)

    colored = base.copy()
    alpha_mask = colored[:, :, 3] > 0
    for row in range(colored.shape[0]):
        progress = row / max(1, colored.shape[0] - 1)
        sin_val = math.sin(progress * math.pi)
        colored[row, alpha_mask[row], 0] = int(180 + 75 * sin_val)
        colored[row, alpha_mask[row], 1] = int(60 + 40 * sin_val)
        colored[row, alpha_mask[row], 2] = int(220 + 35 * sin_val)

    if h > 4:
        q1 = h // 4
        q3 = 3 * h // 4
        colored[q1, alpha_mask[q1], 0] = 255
        colored[q1, alpha_mask[q1], 1] = 200
        colored[q1, alpha_mask[q1], 2] = 255
        colored[q3, alpha_mask[q3], 0] = 255
        colored[q3, alpha_mask[q3], 1] = 200
        colored[q3, alpha_mask[q3], 2] = 255

    _composite(canvas, colored, pad, pad)
    return canvas


def _generate_fire(text: str, size: int, family: int = 0) -> np.ndarray:
    base = _create_base_text(text, size, family=family)
    pad = 80
    h, w = base.shape[:2]
    canvas = np.zeros((h + pad * 2, w + pad * 2, 4), dtype=np.uint8)

    flame_colors = [
        (255, 0, 0),
        (255, 100, 0),
        (255, 200, 0),
        (255, 255, 100),
    ]
    for i, color in enumerate(flame_colors):
        layer = base.copy()
        alpha_mask = layer[:, :, 3] > 0
        layer[:, :, :3] = 0
        layer[alpha_mask, 0] = color[0]
        layer[alpha_mask, 1] = color[1]
        layer[alpha_mask, 2] = color[2]
        if i > 0:
            layer = _apply_wave_distortion(layer, amplitude=i * 2, frequency=0.1)
            k = i * 3 + 1
            if k % 2 == 0:
                k += 1
            layer[:, :, 3] = cv2.GaussianBlur(layer[:, :, 3], (k, k), 0)
        _composite(canvas, layer, pad, pad)
    return canvas


def _generate_ice(text: str, size: int, family: int = 0) -> np.ndarray:
    base = _create_base_text(text, size, family=family)
    pad = 60
    h, w = base.shape[:2]
    canvas = np.zeros((h + pad * 2, w + pad * 2, 4), dtype=np.uint8)

    glow = _apply_glow(base, (255, 140, 0), 18, 180)
    _composite(canvas, glow, pad, pad)

    colored = base.copy()
    alpha_mask = colored[:, :, 3] > 0
    for row in range(colored.shape[0]):
        progress = row / max(1, colored.shape[0] - 1)
        colored[row, alpha_mask[row], 0] = 255
        colored[row, alpha_mask[row], 1] = int(160 + 40 * progress)
        colored[row, alpha_mask[row], 2] = int(20 + 60 * progress)

    _composite(canvas, colored, pad, pad)
    return canvas


def _generate_gold(text: str, size: int, family: int = 0) -> np.ndarray:
    base = _create_base_text(text, size, family=family)
    pad = 40
    h, w = base.shape[:2]
    canvas = np.zeros((h + pad * 2, w + pad * 2, 4), dtype=np.uint8)

    glow = _apply_glow(base, (255, 220, 80), 18, 200)
    _composite(canvas, glow, pad, pad)

    colored = base.copy()
    alpha_mask = colored[:, :, 3] > 0
    for row in range(colored.shape[0]):
        progress = row / max(1, colored.shape[0] - 1)
        sin_val = math.sin(progress * math.pi)
        colored[row, alpha_mask[row], 0] = int(230 + 25 * sin_val)
        colored[row, alpha_mask[row], 1] = int(200 + 40 * sin_val)
        colored[row, alpha_mask[row], 2] = int(80 + 40 * sin_val)

    _composite(canvas, colored, pad, pad)
    return canvas


def _generate_hologram(text: str, size: int, family: int = 0) -> np.ndarray:
    base = _create_base_text(text, size, family=family)
    pad = 50
    h, w = base.shape[:2]
    canvas = np.zeros((h + pad * 2, w + pad * 2, 4), dtype=np.uint8)

    glow = _apply_glow(base, (0, 255, 180), 14, 180)
    _composite(canvas, glow, pad, pad)

    colored = base.copy()
    alpha_mask = colored[:, :, 3] > 0
    colored[alpha_mask, 0] = 50
    colored[alpha_mask, 1] = 255
    colored[alpha_mask, 2] = 180
    colored[alpha_mask, 3] = 255

    for row in range(0, h, 4):
        colored[row, alpha_mask[row], 3] = 240

    rng = random.Random(42)
    noise = np.array([rng.random() * 0.05 + 0.95 for _ in range(colored.size // 4)], dtype=np.float32).reshape(colored.shape[:2])
    colored[:, :, 3] = (colored[:, :, 3].astype(np.float32) * noise).clip(0, 255).astype(np.uint8)

    _composite(canvas, colored, pad, pad)
    return canvas


def _generate_matrix(text: str, size: int, family: int = 0) -> np.ndarray:
    base = _create_base_text(text, size, family=family)
    pad = 60
    h, w = base.shape[:2]
    canvas = np.zeros((h + pad * 2, w + pad * 2, 4), dtype=np.uint8)

    glow = _apply_glow(base, (0, 255, 0), 15, 80)
    _composite(canvas, glow, pad, pad)

    colored = base.copy()
    alpha_mask = colored[:, :, 3] > 0
    for row in range(colored.shape[0]):
        progress = row / max(1, colored.shape[0] - 1)
        g = int(255 * (1 - progress * 0.5))
        colored[row, alpha_mask[row], 0] = 0
        colored[row, alpha_mask[row], 1] = g
        colored[row, alpha_mask[row], 2] = 0

    rng = random.Random(42)
    for _ in range(w // 20):
        rx = rng.randint(0, w - 1)
        ry = rng.randint(0, h - 1)
        if alpha_mask[ry, rx]:
            colored[ry, rx, 1] = 255
            colored[ry, rx, 3] = 255

    _composite(canvas, colored, pad, pad)
    return canvas


def _generate_basic(text: str, size: int, family: int = 0) -> np.ndarray:
    base = _create_base_text(text, size, family=family)
    pad = 60
    h, w = base.shape[:2]
    canvas = np.zeros((h + pad * 2, w + pad * 2, 4), dtype=np.uint8)

    glow = _apply_glow(base, (255, 100, 255), 20, 100)
    _composite(canvas, glow, pad, pad)

    colored = base.copy()
    alpha_mask = colored[:, :, 3] > 0
    for col in range(colored.shape[1]):
        hue = (col / max(1, colored.shape[1] - 1)) * 360 / 360
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        colored[alpha_mask[:, col], col, 0] = int(r * 255)
        colored[alpha_mask[:, col], col, 1] = int(g * 255)
        colored[alpha_mask[:, col], col, 2] = int(b * 255)

    _composite(canvas, colored, pad, pad)
    return canvas


_STYLE_GENERATORS = {
    FontStyle.NEON: _generate_neon,
    FontStyle.GRAFFITI: _generate_graffiti,
    FontStyle.CHROME: _generate_chrome,
    FontStyle.FIRE: _generate_fire,
    FontStyle.ICE: _generate_ice,
    FontStyle.GOLD: _generate_gold,
    FontStyle.HOLOGRAM: _generate_hologram,
    FontStyle.MATRIX: _generate_matrix,
    FontStyle.BASIC: _generate_basic,
}


def generate_styled_text(
    text: str,
    style: str | FontStyle,
    size: int = 72,
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
    family: int = 0,
) -> Image.Image:
    if isinstance(style, str):
        try:
            style = FontStyle(style)
        except ValueError:
            style = FontStyle.BASIC

    generator = _STYLE_GENERATORS.get(style, _generate_basic)
    arr = generator(text, size, family)

    if target_width and target_height:
        h, w = arr.shape[:2]
        canvas = np.zeros((target_height, target_width, 4), dtype=np.uint8)
        x = (target_width - w) // 2
        y = (target_height - h) // 2
        _composite(canvas, arr, x, y)
        arr = canvas

    return Image.fromarray(arr)
