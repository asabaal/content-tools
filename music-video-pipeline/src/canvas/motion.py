from __future__ import annotations

import math
from typing import Any, Dict, Tuple

import cv2
import numpy as np


def apply_motion(
    obj: Any,
    position: Tuple[float, float],
    rotation: float,
    opacity: float,
    t: float,
    w: int,
    h: int,
) -> Dict:
    motion = obj.motion if hasattr(obj, "motion") else {}
    if isinstance(motion, dict):
        motion = motion
    else:
        return {"position": position, "rotation": rotation, "opacity": opacity}

    mode = motion.get("type", "static")
    if not mode or mode == "static":
        return {"position": position, "rotation": rotation, "opacity": opacity}

    speed = float(motion.get("speed", 1.0))
    amplitude = float(motion.get("amplitude", 0.05))
    phase = float(motion.get("phase", 0.0))
    cx, cy = position
    new_rot = rotation
    new_opacity = opacity

    if mode == "rotate":
        new_rot = rotation + t * speed * 60

    elif mode == "drift":
        dx = amplitude * w * math.sin(t * speed * 2 * math.pi + phase)
        dy = amplitude * h * math.cos(t * speed * 1.5 * math.pi + phase * 0.7)
        cx += dx
        cy += dy

    elif mode == "pulse":
        scale = 1.0 + amplitude * math.sin(t * speed * 2 * math.pi + phase)
        new_opacity = opacity * (0.7 + 0.3 * (1.0 + math.sin(t * speed * 2 * math.pi + phase)) / 2)

    elif mode == "breathe":
        breath = 0.5 + 0.5 * math.sin(t * speed * math.pi + phase)
        new_opacity = opacity * (0.5 + 0.5 * breath)

    elif mode == "zoom":
        factor = 1.0 + amplitude * t * speed
        new_rot = rotation

    elif mode == "shimmer":
        shimmer = 0.5 + 0.5 * math.sin(t * speed * 4 * math.pi + phase)
        new_opacity = opacity * (0.3 + 0.7 * shimmer)

    elif mode == "orbit":
        orbit_radius = amplitude * min(w, h) * 0.5
        angle = t * speed * 2 * math.pi + phase
        dx = orbit_radius * math.cos(angle)
        dy = orbit_radius * math.sin(angle)
        cx += dx
        cy += dy

    return {"position": (cx, cy), "rotation": new_rot, "opacity": min(1.0, max(0.0, new_opacity))}


def transform_layer(
    layer: np.ndarray,
    position: Tuple[float, float],
    rotation: float,
    canvas_w: int,
    canvas_h: int,
) -> np.ndarray:
    if rotation == 0.0:
        return layer

    if layer.shape[2] == 4:
        h, w = layer.shape[:2]
        cx, cy = w / 2.0, h / 2.0
        M = cv2.getRotationMatrix2D((cx, cy), rotation, 1.0)
        rotated = cv2.warpAffine(layer, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        return rotated

    h, w = layer.shape[:2]
    cx, cy = w / 2.0, h / 2.0
    M = cv2.getRotationMatrix2D((cx, cy), rotation, 1.0)
    return cv2.warpAffine(layer, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))


def place_layer(
    layer: np.ndarray,
    position: Tuple[float, float],
    canvas_w: int,
    canvas_h: int,
    opacity: float = 1.0,
) -> np.ndarray:
    canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)

    lh, lw = layer.shape[:2]
    cx, cy = int(position[0]), int(position[1])
    x0 = cx - lw // 2
    y0 = cy - lh // 2

    sx0 = max(0, -x0)
    sy0 = max(0, -y0)
    dx0 = max(0, x0)
    dy0 = max(0, y0)
    copy_w = min(lw - sx0, canvas_w - dx0)
    copy_h = min(lh - sy0, canvas_h - dy0)

    if copy_w <= 0 or copy_h <= 0:
        return canvas

    src = layer[sy0:sy0 + copy_h, sx0:sx0 + copy_w]
    if layer.shape[2] == 4:
        canvas[dy0:dy0 + copy_h, dx0:dx0 + copy_w] = src
    else:
        canvas[dy0:dy0 + copy_h, dx0:dx0 + copy_w, :3] = src
        canvas[dy0:dy0 + copy_h, dx0:dx0 + copy_w, 3] = 255

    if opacity < 1.0:
        canvas[:, :, 3] = (canvas[:, :, 3].astype(np.float32) * opacity).astype(np.uint8)

    return canvas
