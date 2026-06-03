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
    alpha = np.clip(alpha, 0, 0.7)

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

    return cv2.filter2D(frame, -1, kernel)


def apply_ken_burns(
    frame: np.ndarray,
    t: float,
    speed: float = 0.12,
    max_zoom: float = 1.04,
    drift: float = 15.0,
) -> np.ndarray:
    h, w = frame.shape[:2]
    cycle = math.sin(t * speed * 2 * math.pi)
    scale = 1.0 + (max_zoom - 1.0) * (0.5 + 0.5 * cycle)
    dx = drift * math.sin(t * speed * math.pi * 0.7)
    dy = drift * math.cos(t * speed * math.pi * 0.5)
    cx, cy = w / 2, h / 2
    M = np.float32([[scale, 0, -cx * (scale - 1) + dx],
                    [0, scale, -cy * (scale - 1) + dy]])
    return cv2.warpAffine(frame, M, (w, h), borderMode=cv2.BORDER_REFLECT)


def apply_color_drift(
    frame: np.ndarray,
    t: float,
    speed: float = 0.15,
    hue_range: float = 8.0,
    sat_pulse: float = 0.08,
) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
    shift = hue_range * math.sin(t * speed * 2 * math.pi)
    hsv[:, :, 0] = (hsv[:, :, 0] + shift) % 180
    sat_factor = 1.0 + sat_pulse * math.sin(t * speed * 2 * math.pi * 1.3)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_factor, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def apply_bokeh_particles(
    frame: np.ndarray,
    t: float,
    count: int = 12,
    speed: float = 0.3,
    color: Tuple[int, int, int] = (255, 255, 255),
    max_radius: int = 30,
    max_alpha: float = 0.15,
) -> np.ndarray:
    h, w = frame.shape[:2]
    overlay = np.zeros((h, w, 3), dtype=np.float32)
    rng = np.random.RandomState(42)

    seeds = []
    for i in range(count):
        seeds.append((
            rng.uniform(0.1, 0.9),
            rng.uniform(0.1, 0.9),
            rng.uniform(0, 2 * math.pi),
            rng.uniform(0.4, 1.0),
            rng.uniform(0.5, 1.0),
        ))

    radii = [1, 3, 5, 8, 12, 16, 20, 25, 30, 40]
    stamp_cache: Dict[int, np.ndarray] = {}

    for seed_x, seed_y, seed_phase, seed_size, seed_bright in seeds:
        drift_x = math.sin(t * speed + seed_phase) * 0.05
        drift_y = (-t * speed * 0.02 - seed_phase * 0.1) % 1.0

        cx = int(((seed_x + drift_x) % 1.0) * w)
        cy = int(((seed_y + drift_y) % 1.0) * h)
        radius = int(max_radius * seed_size * (0.7 + 0.3 * math.sin(t * speed * 2 + seed_phase)))
        alpha = max_alpha * seed_bright * (0.5 + 0.5 * math.sin(t * speed * 1.5 + seed_phase))

        if radius < 2:
            continue

        quantized = min(radii, key=lambda r: abs(r - radius))
        if quantized not in stamp_cache:
            sz = quantized * 2
            yy, xx = np.mgrid[-quantized:quantized, -quantized:quantized].astype(np.float32)
            d = np.sqrt(xx * xx + yy * yy)
            s = np.clip(1.0 - d / quantized, 0, 1) ** 2
            stamp_cache[quantized] = s

        stamp = stamp_cache[quantized]

        y1 = cy - quantized
        y2 = cy + quantized
        x1 = cx - quantized
        x2 = cx + quantized

        sy1 = max(0, -y1)
        sx1 = max(0, -x1)
        ty1 = max(0, y1)
        ty2 = min(h, y2)
        tx1 = max(0, x1)
        tx2 = min(w, x2)

        crop = stamp[sy1:sy1 + (ty2 - ty1), sx1:sx1 + (tx2 - tx1)]
        for c in range(3):
            overlay[ty1:ty2, tx1:tx2, c] += crop * alpha * color[c]

    result = frame.astype(np.float32) + overlay
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_radial_pulse(
    frame: np.ndarray,
    t: float,
    speed: float = 0.5,
    max_alpha: float = 0.12,
) -> np.ndarray:
    h, w = frame.shape[:2]
    cx, cy = w / 2.0, h / 2.0
    max_r = math.sqrt(cx * cx + cy * cy)

    phase = (t * speed) % 1.0
    ring_r = phase * max_r
    ring_w = max_r * 0.15

    ys, xs = np.ogrid[:h, :w]
    ys = ys.astype(np.float32)
    xs = xs.astype(np.float32)
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    ring = np.exp(-0.5 * ((dist - ring_r) / max(ring_w, 1.0)) ** 2)
    alpha = ring * max_alpha * (1.0 - phase * 0.5)

    result = frame.astype(np.float32)
    for c in range(3):
        result[:, :, c] = np.clip(result[:, :, c] + alpha * 80, 0, 255)

    return result.astype(np.uint8)


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
    "ken_burns": apply_ken_burns,
    "color_drift": apply_color_drift,
    "bokeh_particles": apply_bokeh_particles,
    "radial_pulse": apply_radial_pulse,
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
