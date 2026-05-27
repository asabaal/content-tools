from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

import cv2
import numpy as np


def apply_zoom_pulse(
    frame: np.ndarray,
    t: float,
    intensity: float = 0.05,
    speed: float = 2.0,
) -> np.ndarray:
    if intensity < 0.001:
        return frame.copy()

    h, w = frame.shape[:2]
    scale = 1.0 + intensity * math.sin(t * speed * 2 * math.pi)
    cx, cy = w / 2, h / 2
    M = cv2.getRotationMatrix2D((cx, cy), 0, scale)
    return cv2.warpAffine(frame, M, (w, h), borderMode=cv2.BORDER_REFLECT)


def apply_camera_shake(
    frame: np.ndarray,
    t: float,
    intensity: float = 5.0,
    seed: int = 42,
) -> np.ndarray:
    if intensity < 0.1:
        return frame.copy()

    h, w = frame.shape[:2]
    rng = np.random.RandomState(seed + round(t * 30))
    dx = int(rng.uniform(-intensity, intensity))
    dy = int(rng.uniform(-intensity, intensity))
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(frame, M, (w, h), borderMode=cv2.BORDER_REFLECT)


def apply_wave_distortion_frame(
    frame: np.ndarray,
    t: float,
    intensity: float = 3.0,
    speed: float = 1.0,
) -> np.ndarray:
    if intensity < 0.1:
        return frame.copy()

    h, w = frame.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    amplitude = intensity
    freq = speed * 0.05

    x_map = xs + amplitude * np.sin(2 * np.pi * ys * freq / h + t * speed * 3)
    y_map = ys + amplitude * np.cos(2 * np.pi * xs * freq / w + t * speed * 2) * 0.5

    return cv2.remap(frame, x_map, y_map, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def apply_zoom_blur(
    frame: np.ndarray,
    t: float,
    intensity: float = 0.02,
) -> np.ndarray:
    if intensity < 0.001:
        return frame.copy()

    h, w = frame.shape[:2]
    cx, cy = w / 2, h / 2
    result = frame.astype(np.float32)
    n_scales = 5

    for i in range(1, n_scales + 1):
        scale = 1.0 + intensity * i * math.sin(t * 2 * math.pi)
        M = cv2.getRotationMatrix2D((cx, cy), 0, scale)
        scaled = cv2.warpAffine(frame, M, (w, h), borderMode=cv2.BORDER_REFLECT)
        result += scaled.astype(np.float32)

    result /= (n_scales + 1)
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_color_shift_frame(
    frame: np.ndarray,
    t: float,
    hue_shift: float = 10.0,
) -> np.ndarray:
    if abs(hue_shift) < 0.1:
        return frame.copy()

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
    shift = hue_shift * math.sin(t * math.pi * 2)
    hsv[:, :, 0] = (hsv[:, :, 0] + shift) % 180
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def apply_brightness_pulse(
    frame: np.ndarray,
    t: float,
    speed: float = 1.0,
) -> np.ndarray:
    factor = 1.0 + 0.15 * math.sin(t * speed * 2 * math.pi)
    return cv2.convertScaleAbs(frame, alpha=factor, beta=0)


def apply_contrast_pulse(
    frame: np.ndarray,
    t: float,
    speed: float = 1.0,
) -> np.ndarray:
    alpha = 1.0 + 0.2 * math.sin(t * speed * 2 * math.pi)
    beta = 10 * math.sin(t * speed * 2 * math.pi)
    return cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)


def apply_glitch(
    frame: np.ndarray,
    t: float,
    intensity: float = 0.3,
) -> np.ndarray:
    if intensity < 0.05:
        return frame.copy()

    h, w = frame.shape[:2]
    result = frame.copy()
    rng = np.random.RandomState(round(t * 10))

    num_bands = max(1, int(intensity * 8))
    for _ in range(num_bands):
        y = rng.randint(0, h)
        band_h = rng.randint(1, max(2, int(h * 0.05 * intensity)))
        shift = rng.randint(-int(w * 0.1 * intensity), int(w * 0.1 * intensity))
        y_end = min(y + band_h, h)
        result[y:y_end] = np.roll(result[y:y_end], shift, axis=1)

    if intensity > 0.5:
        offset = max(1, int(intensity * 5))
        if offset < w:
            result[:, :-offset, 2] = frame[:, offset:, 2]
            result[:, offset:, 0] = frame[:, :-offset, 0]

    return result


def apply_vignette_pulse(
    frame: np.ndarray,
    t: float,
    intensity: float = 0.5,
) -> np.ndarray:
    if intensity < 0.01:
        return frame.copy()

    h, w = frame.shape[:2]
    cx, cy = w / 2, h / 2
    max_r = math.sqrt(cx * cx + cy * cy)

    pulse = 0.5 + 0.3 * math.sin(t * 2 * math.pi)
    inner = pulse - 0.2
    outer = pulse + 0.3

    ys, xs = np.ogrid[:h, :w]
    ys = ys.astype(np.float32)
    xs = xs.astype(np.float32)
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / max_r
    alpha = np.clip((dist - inner) / max(0.01, outer - inner), 0, 1) * intensity

    result = frame.astype(np.float32)
    for c in range(3):
        result[:, :, c] *= (1 - alpha)

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_motion_blur(
    frame: np.ndarray,
    angle: float = 0.0,
    intensity: float = 5.0,
) -> np.ndarray:
    if intensity < 0.5:
        return frame.copy()

    size = int(intensity * 2)
    if size < 3:
        size = 3
    if size % 2 == 0:
        size += 1

    kernel = np.zeros((size, size), dtype=np.float32)
    rad = math.radians(angle)
    cx, cy = size // 2, size // 2
    for i in range(size):
        dx = int(cx + (i - cx) * math.cos(rad))
        dy = int(cy + (i - cx) * math.sin(rad))
        if 0 <= dx < size and 0 <= dy < size:
            kernel[dy, dx] = 1.0

    total = kernel.sum()
    if total > 0:
        kernel /= total
    else:
        kernel[size // 2, size // 2] = 1.0

    return cv2.filter2D(frame, -1, kernel)


_FRAME_EFFECTS = {
    "zoom_pulse": apply_zoom_pulse,
    "camera_shake": apply_camera_shake,
    "wave_distortion": apply_wave_distortion_frame,
    "zoom_blur": apply_zoom_blur,
    "color_shift": apply_color_shift_frame,
    "brightness_pulse": apply_brightness_pulse,
    "contrast_pulse": apply_contrast_pulse,
    "glitch": apply_glitch,
    "vignette_pulse": apply_vignette_pulse,
    "motion_blur": apply_motion_blur,
}


def apply_frame_effect(
    frame: np.ndarray,
    name: str,
    t: float,
    params: Optional[Dict] = None,
) -> np.ndarray:
    fn = _FRAME_EFFECTS.get(name)
    if fn is None:
        return frame.copy()
    params = params or {}
    return fn(frame, t, **params)
