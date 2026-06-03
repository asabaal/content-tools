from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def render_text_safety_overlay(
    w: int,
    h: int,
    config: dict,
    t: float = 0.0,
) -> np.ndarray:
    if not config:
        return np.zeros((h, w, 4), dtype=np.uint8)

    overlay = np.zeros((h, w, 4), dtype=np.uint8)
    mode = config.get("mode", "none")

    if mode == "none":
        return overlay

    if mode in ("dim_center", "dim"):
        zone_w = float(config.get("width", 0.6))
        zone_h = float(config.get("height", 0.4))
        strength = float(config.get("strength", 0.3))
        cx, cy = w / 2.0, h / 2.0
        zw, zh = w * zone_w, h * zone_h

        ys, xs = np.mgrid[:h, :w].astype(np.float32)
        dx = np.abs(xs - cx) / max(1.0, zw / 2)
        dy = np.abs(ys - cy) / max(1.0, zh / 2)
        dist = np.sqrt(dx * dx + dy * dy)
        alpha = np.clip((1.0 - dist) * strength * 255, 0, 255).astype(np.uint8)
        overlay[:, :, 3] = alpha

    elif mode == "vignette_text":
        strength = float(config.get("strength", 0.4))
        margin = float(config.get("margin", 0.2))
        ys, xs = np.mgrid[:h, :w].astype(np.float32)
        top = ys / h
        bottom = 1.0 - ys / h
        left = xs / w
        right = 1.0 - xs / w
        min_dist = np.minimum(np.minimum(top, bottom), np.minimum(left, right))
        alpha = np.clip((1.0 - min_dist / margin) * strength * 255, 0, 255).astype(np.uint8)
        overlay[:, :, 3] = alpha

    return overlay
