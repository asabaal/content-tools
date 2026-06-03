from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image


def apply_energy_glow(
    frame: np.ndarray,
    energy: float,
    color: Tuple[int, int, int] = (255, 200, 100),
    max_radius: int = 15,
) -> np.ndarray:
    if energy < 0.01:
        return frame.copy()

    h, w = frame.shape[:2]
    result = frame.astype(np.float32)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, bright = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    bright_f = bright.astype(np.float32) / 255.0

    radius = max(3, int(max_radius * energy))
    if radius % 2 == 0:
        radius += 1
    blurred = cv2.GaussianBlur(frame, (radius, radius), 0)
    glow = blurred.astype(np.float32)

    color_arr = np.array(color, dtype=np.float32)
    for c in range(3):
        result[:, :, c] += glow[:, :, c] * bright_f * energy * 0.5 * (color_arr[c] / 255.0)

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_color_shift(
    frame: np.ndarray,
    centroid: float,
    energy: float,
) -> np.ndarray:
    if energy < 0.01:
        return frame.copy()

    result = frame.copy()
    hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)

    hue_shift = energy * 30 * math.sin(energy * math.pi * 4)
    if centroid > 0.7:
        hue_shift += 15
    elif centroid < 0.3:
        hue_shift -= 15

    hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift) % 180
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1.0 + energy * 0.4), 0, 255)

    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def apply_beat_flash(
    frame: np.ndarray,
    is_beat: bool,
    energy: float,
) -> np.ndarray:
    if not is_beat:
        return frame.copy()

    flash_intensity = 1.3 + energy * 0.5
    result = cv2.convertScaleAbs(frame, alpha=flash_intensity, beta=15)
    return result


def apply_wave_distortion(
    layer: np.ndarray,
    energy: float,
    t: float,
    frequency: float = 0.05,
) -> np.ndarray:
    if energy < 0.05:
        return layer.copy()

    h, w = layer.shape[:2]
    amplitude = energy * 8.0
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)

    x_map = xs + amplitude * np.sin(2 * np.pi * ys * frequency / h + t * 5)
    y_map = ys + amplitude * np.sin(2 * np.pi * xs * frequency / w + t * 3) * 0.5

    border = cv2.BORDER_REFLECT if layer.shape[2] == 3 else cv2.BORDER_CONSTANT
    border_val = (0, 0, 0) if layer.shape[2] == 3 else (0, 0, 0, 0)
    return cv2.remap(layer, x_map, y_map, cv2.INTER_LINEAR, borderMode=border, borderValue=border_val)


def apply_chromatic_aberration(
    layer: np.ndarray,
    energy: float,
) -> np.ndarray:
    offset = int(energy * 8)
    if offset < 1:
        return layer.copy()

    result = layer.copy()
    h, w = layer.shape[:2]

    if result.ndim == 3 and result.shape[2] >= 3:
        if offset < w:
            result[offset:, :-offset, 2] = layer[:-offset, offset:, 2]
        if offset < w:
            result[:-offset, offset:, 0] = layer[offset:, :-offset, 0]

    return result


def apply_energy_burst(
    frame: np.ndarray,
    energy: float,
    center: Optional[Tuple[int, int]] = None,
) -> np.ndarray:
    if energy < 0.6:
        return frame.copy()

    h, w = frame.shape[:2]
    if center is None:
        center = (w // 2, h // 2)

    result = frame.astype(np.float32)
    ys, xs = np.ogrid[0:h, 0:w]
    dist = np.sqrt((xs - center[0]) ** 2 + (ys - center[1]) ** 2).astype(np.float32)
    max_dist = np.sqrt(center[0] ** 2 + center[1] ** 2)
    if max_dist == 0:
        max_dist = 1.0
    norm_dist = dist / max_dist

    ring = np.sin(norm_dist * np.pi * 8 * energy)
    energy_layer = np.zeros_like(result)
    energy_layer[:, :, 0] = ring * 0.8
    energy_layer[:, :, 1] = ring * 0.4
    energy_layer[:, :, 2] = ring * 1.0

    blur_size = 15
    for c in range(3):
        energy_layer[:, :, c] = cv2.GaussianBlur(energy_layer[:, :, c], (blur_size, blur_size), 0)

    energy_layer *= energy * 0.6
    result += energy_layer

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_audio_effects(
    frame: np.ndarray,
    audio: Dict[str, float],
    t: float,
    reactivity: Optional[List[str]] = None,
) -> np.ndarray:
    if reactivity is None:
        reactivity = []

    energy = audio.get("energy", 0.0)
    centroid = audio.get("centroid", 0.5)
    is_beat = audio.get("is_beat", False)

    result = frame.copy()

    if "energy" in reactivity:
        result = apply_energy_glow(result, energy)
        if energy > 0.4:
            result = apply_color_shift(result, centroid, energy)

    if "drums" in reactivity:
        result = apply_beat_flash(result, is_beat, energy)
        if energy > 0.7:
            result = apply_energy_burst(result, energy)

    if "vocals" in reactivity and energy > 0.3:
        result = apply_chromatic_aberration(result, energy * 0.5)

    if energy > 0.5:
        result = apply_wave_distortion(result, energy * 0.3, t)

    return result
