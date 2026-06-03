from __future__ import annotations

import math
from typing import Any, Dict, Tuple

import numpy as np

from .models import _parse_position, _parse_size, _resolve_color


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def render_light(
    obj: Any,
    w: int,
    h: int,
    palette: Dict[str, str],
) -> np.ndarray:
    geo = obj.geometry
    light_type = geo.get("shape", "radial")
    style = obj.style
    color_raw = style.get("color", style.get("fill", "#ffffff"))
    color = _hex_to_rgb(_resolve_color(color_raw, palette))
    pos = _parse_position(obj.position, w, h)
    size = _parse_size(obj.size, w, h)
    intensity = float(style.get("intensity", 1.0))
    softness = float(style.get("softness", 1.0))

    layer = np.zeros((h, w, 4), dtype=np.float32)
    ys, xs = np.mgrid[:h, :w].astype(np.float32)

    cx, cy = w / 2, h / 2
    sw, sh = size

    if light_type == "radial":
        dx = (xs - cx) / max(1.0, sw / 2)
        dy = (ys - cy) / max(1.0, sh / 2)
        dist = np.sqrt(dx * dx + dy * dy)
        alpha = np.clip((1.0 - dist) * softness, 0, 1) ** 1.5
        alpha *= intensity * obj.opacity

    elif light_type == "conic":
        angle_offset = float(geo.get("offset", 0))
        angles = np.arctan2(ys - cy, xs - cx) + np.pi + angle_offset
        t = (angles % (2 * np.pi)) / (2 * np.pi)
        n_colors = max(2, int(geo.get("stops", 2)))
        ci = t * (n_colors - 1)
        lo = np.floor(ci).astype(int)
        hi = np.minimum(lo + 1, n_colors - 1)
        f = (ci - lo)
        alpha = np.clip((1.0 - f * 0.6) * intensity * obj.opacity, 0, 1)
        dx = (xs - cx) / max(1.0, sw)
        dy = (ys - cy) / max(1.0, sh)
        dist = np.sqrt(dx * dx + dy * dy)
        alpha *= np.clip(1.0 - dist * 0.3, 0, 1)

    elif light_type == "spot":
        angle = float(geo.get("angle", 0))
        spread = float(geo.get("spread", 0.5))
        rad = math.radians(angle)
        dx = (xs - cx) / max(1.0, sw)
        dy = (ys - cy) / max(1.0, sh)
        dist = np.sqrt(dx * dx + dy * dy)
        dot = dx * math.cos(rad) + dy * math.sin(rad)
        cone = np.clip((dot + 0.2) / max(0.01, spread), 0, 1)
        alpha = np.clip((1.0 - dist) * cone * softness, 0, 1)
        alpha *= intensity * obj.opacity

    else:
        alpha = np.zeros((h, w), dtype=np.float32)

    layer[:, :, 0] = color[0] * alpha
    layer[:, :, 1] = color[1] * alpha
    layer[:, :, 2] = color[2] * alpha
    layer[:, :, 3] = alpha * 255

    return np.clip(layer, 0, 255).astype(np.uint8)


def render_gradient(
    obj: Any,
    w: int,
    h: int,
    palette: Dict[str, str],
) -> np.ndarray:
    geo = obj.geometry
    style = obj.style
    colors_raw = style.get("colors", [])
    direction = geo.get("direction", "vertical_top_bottom")

    colors = [_hex_to_rgb(_resolve_color(c, palette)) for c in colors_raw]
    if not colors:
        colors = [(255, 255, 255), (0, 0, 0)]
    n = len(colors)

    arr = np.zeros((h, w, 3), dtype=np.float32)
    rgb_arr = np.array(colors, dtype=np.float32)

    pos = _parse_position(obj.position, w, h)
    cx, cy = pos
    size = _parse_size(obj.size, w, h)
    sw, sh = size

    ys, xs = np.mgrid[:h, :w].astype(np.float32)

    if direction.startswith("angle_"):
        parts = direction.split("_")
        angle_deg = float(parts[1]) if len(parts) > 1 else 0.0
        rad = math.radians(angle_deg)
        dx = math.cos(rad)
        dy = math.sin(rad)
        proj = xs * dx + ys * dy
        p_min = proj.min()
        p_max = proj.max()
        rng = max(1.0, p_max - p_min)
        t = np.clip((proj - p_min) / rng, 0, 1)
    elif direction == "radial":
        max_r = math.sqrt(sw * sw + sh * sh) / 2
        dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        t = np.clip(dist / max(1.0, max_r), 0, 1)
    elif direction == "conic":
        offset = float(geo.get("offset", 0))
        angles = np.arctan2(ys - cy, xs - cx) + np.pi + offset
        t = (angles % (2 * np.pi)) / (2 * np.pi)
    elif direction == "horizontal":
        t = xs / max(1, w - 1)
    elif direction == "vertical":
        t = ys / max(1, h - 1)
    else:
        t = ys / max(1, h - 1)

    ci = t * (n - 1)
    lo = np.floor(ci).astype(int)
    hi = np.minimum(lo + 1, n - 1)
    f = (ci - lo)[:, :, np.newaxis]
    arr = np.clip(rgb_arr[lo] * (1 - f) + rgb_arr[hi] * f, 0, 255)

    alpha_layer = np.full((h, w, 4), 0, dtype=np.uint8)
    alpha_layer[:, :, :3] = arr.astype(np.uint8)
    alpha_layer[:, :, 3] = int(obj.opacity * 255)

    return alpha_layer
