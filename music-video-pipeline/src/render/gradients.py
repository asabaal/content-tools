from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


PRIMITIVES = (
    "linear",
    "spot_field",
    "conic",
    "spiral",
    "cross",
    "diamond",
    "bands",
    "rings",
    "grid",
    "scatter_field",
    "burst",
)

MAX_SCATTER_COUNT = 200
SCATTER_CHUNK_SIZE = 8


def apply_color_map(t: np.ndarray, rgb_arr: np.ndarray) -> np.ndarray:
    n = len(rgb_arr)
    if n < 2:
        return np.full((t.shape[0], t.shape[1], 3), rgb_arr[0], dtype=np.uint8)
    ci = np.clip(t, 0.0, 1.0) * (n - 1)
    lo = np.floor(ci).astype(np.int32)
    hi = np.minimum(lo + 1, n - 1)
    f = (ci - lo)[:, :, np.newaxis]
    return np.clip(rgb_arr[lo] * (1 - f) + rgb_arr[hi] * f, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

def _prim_linear(w: int, h: int, **p) -> np.ndarray:
    axis = p.get("axis", "angle")
    angle_deg = float(p.get("angle", 0.0))
    reverse = bool(p.get("reverse", False))

    ys, xs = np.mgrid[:h, :w].astype(np.float32)

    if axis == "y":
        t = ys / max(1, h - 1)
    elif axis == "x":
        t = xs / max(1, w - 1)
    elif axis == "diagonal":
        t = (xs + ys) / max(1, w + h - 2)
    else:
        rad = math.radians(angle_deg)
        dx, dy = math.cos(rad), math.sin(rad)
        proj = xs * dx + ys * dy
        p_min, p_max = proj.min(), proj.max()
        rng = max(1.0, p_max - p_min)
        t = (proj - p_min) / rng

    if reverse:
        t = 1.0 - t
    return np.clip(t, 0.0, 1.0)


def _prim_spot_field(w: int, h: int, **p) -> np.ndarray:
    positions = p.get("positions", [[0.5, 0.5]])
    softness = float(p.get("softness", 1.0))
    radius_scale = float(p.get("radius_scale", 2.0))
    blend = p.get("blend", "nearest")

    if not positions:
        positions = [[0.5, 0.5]]

    if len(positions) == 1:
        px, py = positions[0]
        ys, xs = np.mgrid[:h, :w].astype(np.float32)
        dist = np.sqrt((xs / w - px) ** 2 + (ys / h - py) ** 2)
        if softness != 1.0:
            dist = dist ** softness
        t = np.clip(dist * radius_scale, 0.0, 1.0)
        return t

    ys, xs = np.mgrid[:h, :w].astype(np.float32)
    xn = xs / w
    yn = ys / h

    dists = np.empty((len(positions), h, w), dtype=np.float32)
    for i, (px, py) in enumerate(positions):
        d = np.sqrt((xn - px) ** 2 + (yn - py) ** 2)
        dists[i] = d ** softness if softness != 1.0 else d

    if blend == "additive":
        lights = np.clip(1.0 - dists * radius_scale, 0.0, 1.0)
        combined = lights.sum(axis=0)
        t = np.clip(1.0 - combined, 0.0, 1.0)
    elif blend == "max":
        lights = np.clip(1.0 - dists * radius_scale, 0.0, 1.0)
        combined = lights.max(axis=0)
        t = np.clip(1.0 - combined, 0.0, 1.0)
    else:
        t = np.clip(np.minimum.reduce(dists) * radius_scale, 0.0, 1.0)

    return t


def _prim_conic(w: int, h: int, **p) -> np.ndarray:
    phase = float(p.get("phase", 0.0))
    frequency = float(p.get("frequency", 1.0))
    center = p.get("center", [0.5, 0.5])
    reverse = bool(p.get("reverse", False))

    cx, cy = center[0] * w, center[1] * h
    ys, xs = np.mgrid[:h, :w].astype(np.float32)
    angles = np.arctan2(ys - cy, xs - cx) + np.pi + phase
    t = ((angles % (2 * np.pi)) / (2 * np.pi)) * frequency
    if reverse:
        t = 1.0 - t
    return np.clip(t % 1.0, 0.0, 1.0)


def _prim_spiral(w: int, h: int, **p) -> np.ndarray:
    tightness = float(p.get("tightness", 0.5))
    phase = float(p.get("phase", 0.0))
    center = p.get("center", [0.5, 0.5])
    radial_weight = float(p.get("radial_weight", 1.0))

    cx, cy = center[0] * w, center[1] * h
    max_r = math.sqrt(cx * cx + cy * cy)
    if max_r < 1.0:
        max_r = 1.0

    ys, xs = np.mgrid[:h, :w].astype(np.float32)
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / max_r
    angles = np.arctan2(ys - cy, xs - cx)

    t = (dist * radial_weight + angles / (2 * np.pi) * tightness + phase) % 1.0
    return np.clip(t, 0.0, 1.0)


def _prim_cross(w: int, h: int, **p) -> np.ndarray:
    thickness = float(p.get("thickness", 1.5))
    center = p.get("center", [0.5, 0.5])
    softness = float(p.get("softness", 0.0))

    cx, cy = center[0] * w, center[1] * h
    ys, xs = np.mgrid[:h, :w].astype(np.float32)
    dx = np.abs(xs - cx) / max(1.0, cx)
    dy = np.abs(ys - cy) / max(1.0, cy)
    t = np.minimum(dx, dy) * thickness

    if softness > 0.0:
        t = t / (1.0 + softness)

    return np.clip(t, 0.0, 1.0)


def _prim_diamond(w: int, h: int, **p) -> np.ndarray:
    scale = float(p.get("scale", 1.0))
    center = p.get("center", [0.5, 0.5])

    cx, cy = center[0] * w, center[1] * h
    max_d = max(1.0, (cx + cy) * scale)

    ys, xs = np.mgrid[:h, :w].astype(np.float32)
    dist = np.abs(xs - cx) + np.abs(ys - cy)
    return np.clip(dist / max_d, 0.0, 1.0)


def _prim_bands(w: int, h: int, **p) -> np.ndarray:
    axis = p.get("axis", "y")
    frequency = p.get("frequency")
    phase = float(p.get("phase", 0.0))
    wave = bool(p.get("wave", False))
    wave_amplitude = float(p.get("wave_amplitude", 0.1))
    wave_frequency = float(p.get("wave_frequency", 3.0))

    if axis == "x":
        coords = np.arange(w, dtype=np.float32)
        length = w
        other_size = h
    else:
        coords = np.arange(h, dtype=np.float32)
        length = h
        other_size = w

    if frequency is not None and frequency > 0:
        band_h = length / max(1, frequency)
    else:
        band_h = length / max(1.0, length / max(1, length * 0.1))

    t_1d = (coords + phase * band_h) / max(1.0, band_h)

    if wave:
        wave_t = np.arange(other_size, dtype=np.float32) / max(1, other_size - 1)
        displacement = np.sin(wave_t * wave_frequency * 2 * np.pi) * wave_amplitude
        t_2d = t_1d[:, np.newaxis] + displacement[np.newaxis, :]
        if axis == "x":
            t_2d = t_2d.T
        t = t_2d
    else:
        if axis == "x":
            t = np.broadcast_to(t_1d[np.newaxis, :], (h, w)).copy()
        else:
            t = np.broadcast_to(t_1d[:, np.newaxis], (h, w)).copy()

    return np.clip(t, 0.0, 1.0)


def _prim_rings(w: int, h: int, **p) -> np.ndarray:
    center = p.get("center", [0.5, 0.5])
    frequency = float(p.get("frequency", 5.0))
    phase = float(p.get("phase", 0.0))
    contrast = float(p.get("contrast", 1.0))
    radial_scale = float(p.get("radial_scale", 1.0))

    cx, cy = center[0] * w, center[1] * h
    max_r = math.sqrt((w / 2) ** 2 + (h / 2) ** 2)
    if max_r < 1.0:
        max_r = 1.0

    ys, xs = np.mgrid[:h, :w].astype(np.float32)
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / max_r

    raw = np.sin(dist * frequency * 2 * np.pi * radial_scale + phase)
    t = raw * contrast * 0.5 + 0.5
    return np.clip(t, 0.0, 1.0)


def _prim_grid(w: int, h: int, **p) -> np.ndarray:
    freq_x = float(p.get("freq_x", 5.0))
    freq_y = float(p.get("freq_y", 5.0))
    phase_x = float(p.get("phase_x", 0.0))
    phase_y = float(p.get("phase_y", 0.0))
    shape = p.get("shape", "diamond")
    contrast = float(p.get("contrast", 1.0))

    ys, xs = np.mgrid[:h, :w].astype(np.float32)
    xn = xs / max(1, w)
    yn = ys / max(1, h)

    sx = np.sin(xn * freq_x * 2 * np.pi + phase_x)
    sy = np.sin(yn * freq_y * 2 * np.pi + phase_y)

    if shape == "checker":
        t = ((sx > 0).astype(np.float32) * 2 - 1) * ((sy > 0).astype(np.float32) * 2 - 1)
        t = t * 0.5 + 0.5
    elif shape == "dots":
        t = sx * sy * 0.5 + 0.5
    else:
        t = (sx + sy) * 0.25 + 0.5

    if contrast != 1.0:
        t = (t - 0.5) * contrast + 0.5

    return np.clip(t, 0.0, 1.0)


def _prim_scatter_field(w: int, h: int, **p) -> np.ndarray:
    count = min(int(p.get("count", 20)), MAX_SCATTER_COUNT)
    seed = int(p.get("seed", 42))
    shape = p.get("shape", "dot")
    size = float(p.get("size", 0.05))
    size_jitter = float(p.get("size_jitter", 0.3))
    blend = p.get("blend", "max")

    rng = np.random.RandomState(seed)
    px = rng.uniform(0.1, 0.9, count)
    py = rng.uniform(0.1, 0.9, count)
    sizes = np.full(count, size, dtype=np.float32)
    if size_jitter > 0:
        jitter = rng.uniform(-size_jitter, size_jitter, count).astype(np.float32)
        sizes = np.clip(sizes * (1 + jitter), 0.01, 0.5)

    ys, xs = np.mgrid[:h, :w].astype(np.float32)
    xn = (xs / max(1, w)).astype(np.float32)
    yn = (ys / max(1, h)).astype(np.float32)

    field = np.zeros((h, w), dtype=np.float32)

    for i in range(0, count, SCATTER_CHUNK_SIZE):
        chunk_end = min(i + SCATTER_CHUNK_SIZE, count)
        chunk_px = px[i:chunk_end].astype(np.float32)
        chunk_py = py[i:chunk_end].astype(np.float32)
        chunk_sizes = sizes[i:chunk_end]
        chunk_count = chunk_end - i

        dx = xn[np.newaxis, :, :] - chunk_px[:, np.newaxis, np.newaxis]
        dy = yn[np.newaxis, :, :] - chunk_py[:, np.newaxis, np.newaxis]

        if shape == "diamond":
            d = np.abs(dx) + np.abs(dy)
        elif shape == "ring":
            d = np.abs(np.sqrt(dx ** 2 + dy ** 2) - chunk_sizes[:, np.newaxis, np.newaxis] * 0.5)
        else:
            d = np.sqrt(dx ** 2 + dy ** 2)

        elem_r = np.float32(chunk_sizes[:, np.newaxis, np.newaxis] * 0.5)
        if shape == "ring":
            elem_r = elem_r * np.float32(0.3)

        elem_field = np.clip(np.float32(1.0) - d / np.maximum(elem_r, np.float32(0.001)), np.float32(0.0), np.float32(1.0))

        if blend == "additive":
            field = field + elem_field.max(axis=0).astype(np.float32)
        else:
            field = np.maximum(field, elem_field.max(axis=0).astype(np.float32))

    return np.clip(field, 0.0, 1.0)


def _prim_burst(w: int, h: int, **p) -> np.ndarray:
    center = p.get("center", [0.5, 0.5])
    ray_count = max(2, int(p.get("ray_count", 8)))
    phase = float(p.get("phase", 0.0))
    sharpness = float(p.get("sharpness", 0.5))
    radial_falloff = float(p.get("radial_falloff", 1.0))

    cx, cy = center[0] * w, center[1] * h
    max_r = math.sqrt((w / 2) ** 2 + (h / 2) ** 2)
    if max_r < 1.0:
        max_r = 1.0

    ys, xs = np.mgrid[:h, :w].astype(np.float32)
    dx = xs - cx
    dy = ys - cy
    dist = np.sqrt(dx ** 2 + dy ** 2) / max_r

    angles = np.arctan2(dy, dx) + np.pi + phase
    sector_width = 2 * np.pi / ray_count
    sector_pos = (angles % sector_width) / sector_width

    ray_t = 0.5 + 0.5 * np.cos(sector_pos * 2 * np.pi)
    if sharpness != 0.5:
        ray_t = ray_t ** max(0.01, sharpness * 2)

    dist_t = np.clip(1.0 - dist ** radial_falloff, 0.0, 1.0)
    t = ray_t * dist_t
    return np.clip(t, 0.0, 1.0)


_PRIMITIVE_FUNCS = {
    "linear": _prim_linear,
    "spot_field": _prim_spot_field,
    "conic": _prim_conic,
    "spiral": _prim_spiral,
    "cross": _prim_cross,
    "diamond": _prim_diamond,
    "bands": _prim_bands,
    "rings": _prim_rings,
    "grid": _prim_grid,
    "scatter_field": _prim_scatter_field,
    "burst": _prim_burst,
}


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

RECIPES: Dict[str, Dict[str, Any]] = {
    "diamond_field": {
        "primitive": "grid",
        "params": {"shape": "diamond", "freq_x": 8, "freq_y": 8},
    },
    "expanding_ring": {
        "primitive": "rings",
        "params": {"frequency": 5, "contrast": 0.8},
    },
    "conic_burst": {
        "primitive": "burst",
        "params": {"ray_count": 12, "sharpness": 0.7},
    },
    "playful_scatter": {
        "primitive": "scatter_field",
        "params": {"count": 30, "shape": "diamond", "size": 0.04, "blend": "max"},
    },
}


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _try_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def parse_direction(direction: str) -> Tuple[str, Dict[str, Any]]:
    if not direction:
        return "spot_field", {"positions": [[0.5, 0.5]]}

    if direction in RECIPES:
        recipe = RECIPES[direction]
        return recipe["primitive"], dict(recipe["params"])

    _LINEAR_ALIASES = {
        "vertical_top_bottom": ("y", False),
        "vertical_bottom_top": ("y", True),
        "horizontal_left_right": ("x", False),
        "horizontal_right_left": ("x", True),
        "diagonal_tl_br": ("diagonal", False),
        "diagonal_tr_bl": ("diagonal", True),
    }
    if direction in _LINEAR_ALIASES:
        axis, rev = _LINEAR_ALIASES[direction]
        return "linear", {"axis": axis, "reverse": rev}

    if direction.startswith("angle_"):
        parts = direction.split("_")
        val = _try_float(parts[1]) if len(parts) > 1 else None
        if val is None:
            raise ValueError(f"Invalid angle direction: {direction!r}")
        return "linear", {"axis": "angle", "angle": val}

    _RADIAL_ALIASES = {
        "radial_center": [0.5, 0.5],
        "radial_top": [0.5, 0.0],
        "radial_bottom": [0.5, 1.0],
        "radial_tl": [0.0, 0.0],
        "radial_br": [1.0, 1.0],
    }
    if direction in _RADIAL_ALIASES:
        return "spot_field", {"positions": [_RADIAL_ALIASES[direction]]}

    if direction.startswith("conic"):
        parts = direction.split("_")
        phase = 0.0
        if len(parts) >= 2:
            candidate = _try_float(parts[1])
            if candidate is not None:
                phase = candidate
            elif len(parts) >= 3:
                candidate2 = _try_float(parts[2])
                if candidate2 is not None:
                    phase = candidate2
        return "conic", {"phase": phase}

    if direction.startswith("dual_spot"):
        parts = direction.split("_")
        if len(parts) >= 6:
            vals = [_try_float(parts[i]) for i in range(2, 6)]
            if all(v is not None for v in vals):
                positions = [[vals[0], vals[1]], [vals[2], vals[3]]]
                return "spot_field", {"positions": positions}
        return "spot_field", {"positions": [[0.25, 0.25], [0.75, 0.75]]}

    if direction == "spiral":
        return "spiral", {}

    if direction == "cross":
        return "cross", {}

    if direction == "diamond":
        return "diamond", {}

    if direction == "bands":
        return "bands", {}

    if direction.startswith("rings"):
        parts = direction.split("_")
        freq = 5.0
        if len(parts) >= 2:
            v = _try_float(parts[1])
            if v is not None:
                freq = v
        return "rings", {"frequency": freq}

    if direction.startswith("grid"):
        parts = direction.split("_")
        freq = 5.0
        if len(parts) >= 2:
            v = _try_float(parts[1])
            if v is not None:
                freq = v
        return "grid", {"freq_x": freq, "freq_y": freq}

    if direction == "scatter_field":
        return "scatter_field", {}

    if direction.startswith("burst"):
        parts = direction.split("_")
        ray_count = 8
        if len(parts) >= 2:
            v = _try_float(parts[1])
            if v is not None:
                ray_count = max(2, int(v))
        return "burst", {"ray_count": ray_count}

    if direction in PRIMITIVES:
        return direction, {}

    return "spot_field", {"positions": [[0.5, 0.5]]}


def resolve_gradient(direction: str, params_dict: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    primitive, string_params = parse_direction(direction)
    if params_dict:
        merged = {**string_params, **params_dict}
    else:
        merged = string_params
    return primitive, merged


def compute_field(w: int, h: int, primitive: str, params: Dict[str, Any]) -> np.ndarray:
    func = _PRIMITIVE_FUNCS.get(primitive)
    if func is None:
        raise ValueError(f"Unknown gradient primitive: {primitive!r}")
    return func(w, h, **params)


def resolve_and_compute(direction: str, w: int, h: int,
                        params_dict: Optional[Dict[str, Any]] = None) -> np.ndarray:
    primitive, params = resolve_gradient(direction, params_dict)
    return compute_field(w, h, primitive, params)
