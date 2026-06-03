from __future__ import annotations

from typing import Optional

import cv2
import numpy as np


def composite_layer(
    base: np.ndarray,
    layer: np.ndarray,
    blend_mode: str = "normal",
    mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    if layer.shape[2] == 3:
        alpha = np.full((layer.shape[0], layer.shape[1]), 255, dtype=np.float32)
    else:
        alpha = layer[:, :, 3].astype(np.float32)

    if mask is not None:
        if mask.ndim == 2:
            alpha = alpha * (mask.astype(np.float32) / 255.0)
        elif mask.shape[2] >= 1:
            alpha = alpha * (mask[:, :, 0].astype(np.float32) / 255.0)

    a = alpha / 255.0
    a3 = a[:, :, np.newaxis]

    base_f = base[:, :, :3].astype(np.float32)
    layer_f = layer[:, :, :3].astype(np.float32)

    if blend_mode == "normal":
        blended = layer_f
    elif blend_mode == "screen":
        blended = base_f + layer_f - (base_f * layer_f / 255.0)
    elif blend_mode == "multiply":
        blended = base_f * layer_f / 255.0
    elif blend_mode == "overlay":
        low = 2.0 * base_f * layer_f / 255.0
        high = 255.0 - 2.0 * (255.0 - base_f) * (255.0 - layer_f) / 255.0
        blended = np.where(base_f < 128, low, high)
    elif blend_mode == "soft_light":
        blended = base_f + (layer_f - 128.0) * (base_f / 255.0) * (1.0 - base_f / 255.0) * 2.0
    elif blend_mode == "add":
        blended = base_f + layer_f
    elif blend_mode == "lighten":
        blended = np.maximum(base_f, layer_f)
    elif blend_mode == "darken":
        blended = np.minimum(base_f, layer_f)
    else:
        blended = layer_f

    result = base_f * (1.0 - a3) + blended * a3
    result = np.clip(result, 0, 255).astype(np.uint8)

    if base.shape[2] == 4:
        result_alpha = np.clip(base[:, :, 3].astype(np.float32) * (1.0 - a) + alpha, 0, 255).astype(np.uint8)
        out = np.zeros((base.shape[0], base.shape[1], 4), dtype=np.uint8)
        out[:, :, :3] = result
        out[:, :, 3] = result_alpha
        return out

    return result


def apply_glow(
    layer: np.ndarray,
    color: tuple,
    radius: int,
    intensity: float = 1.0,
) -> np.ndarray:
    if radius < 1 or intensity < 0.01:
        return layer

    if layer.shape[2] == 4:
        alpha = layer[:, :, 3].astype(np.float32) / 255.0
    else:
        alpha = np.ones((layer.shape[0], layer.shape[1]), dtype=np.float32)

    glow = cv2.GaussianBlur(alpha, (0, 0), radius) * 255.0 * intensity
    glow = np.clip(glow, 0, 255).astype(np.uint8)

    result = np.zeros_like(layer)
    result[:, :, 0] = (glow * color[0] / 255).astype(np.uint8)
    result[:, :, 1] = (glow * color[1] / 255).astype(np.uint8)
    result[:, :, 2] = (glow * color[2] / 255).astype(np.uint8)
    if result.shape[2] == 4:
        result[:, :, 3] = glow

    return result


def apply_blur(
    layer: np.ndarray,
    radius: float,
) -> np.ndarray:
    if radius < 0.5:
        return layer
    ksize = int(radius * 2)
    if ksize % 2 == 0:
        ksize += 1
    return cv2.GaussianBlur(layer, (ksize, ksize), radius)


def fill_canvas(width: int, height: int, color: str) -> np.ndarray:
    h = color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    rgb = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[:, :] = rgb
    return canvas
