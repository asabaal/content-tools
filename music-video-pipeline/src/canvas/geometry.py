from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .models import _parse_position, _parse_size, _resolve_color


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


_SMALL_THRESHOLD = 0.4


def render_shape(
    obj: Any,
    w: int,
    h: int,
    palette: Dict[str, str],
) -> np.ndarray:
    geo = obj.geometry
    shape_type = geo.get("shape", "rectangle")
    pos = _parse_position(obj.position, w, h)
    size = _parse_size(obj.size, w, h)
    sw, sh = size

    style = obj.style
    stroke_width = int(style.get("stroke_width", 2))
    corner_radius = float(style.get("corner_radius", 0))

    fill_raw = style.get("fill")
    stroke_raw = style.get("stroke")
    fill = _hex_to_rgb(_resolve_color(fill_raw, palette)) if fill_raw and fill_raw != "none" else None
    stroke = _hex_to_rgb(_resolve_color(stroke_raw, palette)) if stroke_raw and stroke_raw != "none" else None

    use_sub = (sw / w < _SMALL_THRESHOLD) and (sh / h < _SMALL_THRESHOLD)

    if use_sub:
        pad = stroke_width + 4
        sub_w = int(sw) + pad * 2
        sub_h = int(sh) + pad * 2
        scx, scy = sub_w / 2, sub_h / 2
        half_w, half_h = sw / 2, sh / 2

        sub_layer = np.zeros((sub_h, sub_w, 4), dtype=np.uint8)
        sub_img = Image.fromarray(sub_layer)
        draw = ImageDraw.Draw(sub_img)

        _draw_shape_on(draw, shape_type, geo, scx, scy, half_w, half_h, fill, stroke, stroke_width, corner_radius, w, h)

        drawn = np.array(sub_img)
        full_layer = np.zeros((h, w, 4), dtype=np.uint8)
        px, py = int(pos[0] - sub_w / 2), int(pos[1] - sub_h / 2)

        sx0 = max(0, -px)
        sy0 = max(0, -py)
        dx0 = max(0, px)
        dy0 = max(0, py)
        copy_w = min(sub_w - sx0, w - dx0)
        copy_h = min(sub_h - sy0, h - dy0)
        if copy_w > 0 and copy_h > 0:
            full_layer[dy0:dy0 + copy_h, dx0:dx0 + copy_w] = drawn[sy0:sy0 + copy_h, sx0:sx0 + copy_w]
        return full_layer

    cx, cy = pos
    half_w, half_h = sw / 2, sh / 2
    layer = np.zeros((h, w, 4), dtype=np.uint8)
    img = Image.fromarray(layer)
    draw = ImageDraw.Draw(img)

    _draw_shape_on(draw, shape_type, geo, cx, cy, half_w, half_h, fill, stroke, stroke_width, corner_radius, w, h)

    return np.array(img)


def _draw_shape_on(
    draw: ImageDraw.ImageDraw,
    shape_type: str,
    geo: dict,
    cx: float,
    cy: float,
    half_w: float,
    half_h: float,
    fill,
    stroke,
    stroke_width: int,
    corner_radius: float,
    canvas_w: int,
    canvas_h: int,
):
    if shape_type in ("rectangle", "rect"):
        bbox = [cx - half_w, cy - half_h, cx + half_w, cy + half_h]
        if corner_radius > 0:
            draw.rounded_rectangle(bbox, radius=int(corner_radius), fill=fill, outline=stroke, width=stroke_width)
        else:
            draw.rectangle(bbox, fill=fill, outline=stroke, width=stroke_width)

    elif shape_type in ("circle", "ellipse"):
        bbox = [cx - half_w, cy - half_h, cx + half_w, cy + half_h]
        draw.ellipse(bbox, fill=fill, outline=stroke, width=stroke_width)

    elif shape_type == "diamond":
        pts = [(cx, cy - half_h), (cx + half_w, cy), (cx, cy + half_h), (cx - half_w, cy)]
        draw.polygon(pts, fill=fill, outline=stroke, width=stroke_width)

    elif shape_type in ("polygon", "hexagon", "octagon", "pentagon", "triangle"):
        sides = geo.get("sides", 6)
        pts = []
        for i in range(sides):
            angle = 2 * math.pi * i / sides - math.pi / 2
            px = cx + half_w * math.cos(angle)
            py = cy + half_h * math.sin(angle)
            pts.append((px, py))
        draw.polygon(pts, fill=fill, outline=stroke, width=stroke_width)

    elif shape_type == "line":
        end_pos = _parse_position(geo.get("end", [cx + half_w * 2, cy]), canvas_w, canvas_h)
        draw.line([(cx, cy), end_pos], fill=stroke or fill or (255, 255, 255), width=max(1, stroke_width))

    elif shape_type == "ring":
        outer_bbox = [cx - half_w, cy - half_h, cx + half_w, cy + half_h]
        inner_frac = geo.get("inner_ratio", 0.6)
        iw, ih = half_w * inner_frac, half_h * inner_frac
        inner_bbox = [cx - iw, cy - ih, cx + iw, cy + ih]
        ring_fill = fill or stroke or (255, 255, 255)
        draw.ellipse(outer_bbox, fill=ring_fill)
        draw.ellipse(inner_bbox, fill=(0, 0, 0, 0))

    elif shape_type == "arc":
        start_angle = geo.get("start_angle", 0)
        end_angle = geo.get("end_angle", 180)
        bbox = [cx - half_w, cy - half_h, cx + half_w, cy + half_h]
        draw.arc(bbox, start=start_angle, end=end_angle, fill=stroke or fill or (255, 255, 255), width=max(1, stroke_width))

    elif shape_type == "grid":
        rows = geo.get("rows", 4)
        cols = geo.get("cols", 4)
        gap = float(geo.get("gap", 0))
        cell_w = half_w * 2 / cols - gap
        cell_h = half_h * 2 / rows - gap
        start_x = cx - half_w + gap / 2
        start_y = cy - half_h + gap / 2
        grid_fill = fill or (255, 255, 255, 30)
        grid_stroke = stroke
        for r in range(rows):
            for c in range(cols):
                x0 = start_x + c * (cell_w + gap)
                y0 = start_y + r * (cell_h + gap)
                draw.rectangle([x0, y0, x0 + cell_w, y0 + cell_h], fill=grid_fill, outline=grid_stroke, width=stroke_width)


def render_path(
    obj: Any,
    w: int,
    h: int,
    palette: Dict[str, str],
) -> np.ndarray:
    geo = obj.geometry
    style = obj.style
    stroke_raw = style.get("stroke")
    stroke_color = _hex_to_rgb(_resolve_color(stroke_raw, palette)) if stroke_raw and stroke_raw != "none" else (255, 255, 255)
    stroke_width = int(style.get("stroke_width", 2))
    fill_raw = style.get("fill")
    fill_color = _hex_to_rgb(_resolve_color(fill_raw, palette)) if fill_raw and fill_raw != "none" else None

    layer = np.zeros((h, w, 4), dtype=np.uint8)
    img = Image.fromarray(layer)
    draw = ImageDraw.Draw(img)

    points = geo.get("points", [])
    if points:
        parsed = []
        for p in points:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                px, py = p[0], p[1]
                if 0 < px <= 1.0 and 0 < py <= 1.0:
                    px, py = px * w, py * h
                parsed.append((px, py))
        if len(parsed) >= 2:
            closed = geo.get("closed", False)
            if closed and fill_color:
                draw.polygon(parsed, fill=fill_color, outline=stroke_color, width=stroke_width)
            else:
                draw.line(parsed, fill=stroke_color, width=stroke_width)

    return np.array(img)
