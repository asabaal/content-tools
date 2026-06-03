from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Tuple

import numpy as np

from .models import CanvasObject, _parse_position, _parse_size


def expand_repeats(
    obj: CanvasObject,
    w: int,
    h: int,
) -> List[Dict]:
    repeat = obj.repeat
    mode = repeat.get("mode", "none")
    if not mode or mode == "none":
        pos = _parse_position(obj.position, w, h)
        return [_obj_to_instance(obj, pos, obj.rotation, obj.opacity)]

    instances = []

    if mode == "grid":
        rows = int(repeat.get("rows", 3))
        cols = int(repeat.get("cols", 3))
        spacing_x = float(repeat.get("spacing_x", repeat.get("spacing", 0.15)))
        spacing_y = float(repeat.get("spacing_y", repeat.get("spacing", 0.15)))
        base_pos = _parse_position(obj.position, w, h)
        base_x = base_pos[0] / w - (cols - 1) * spacing_x / 2
        base_y = base_pos[1] / h - (rows - 1) * spacing_y / 2
        for r in range(rows):
            for c in range(cols):
                px = base_x + c * spacing_x
                py = base_y + r * spacing_y
                jitter_x = float(repeat.get("jitter_x", 0))
                jitter_y = float(repeat.get("jitter_y", 0))
                if jitter_x or jitter_y:
                    seed = int(repeat.get("seed", 42)) + r * cols + c
                    rng = np.random.RandomState(seed)
                    px += rng.uniform(-jitter_x, jitter_x)
                    py += rng.uniform(-jitter_y, jitter_y)
                offset = (px * w, py * h)
                instances.append(_obj_to_instance(obj, offset, obj.rotation, obj.opacity))

    elif mode == "radial":
        count = int(repeat.get("count", 8))
        radius = float(repeat.get("radius", 0.3))
        center = _parse_position(repeat.get("center", obj.position), w, h)
        start_angle = float(repeat.get("start_angle", 0))
        for i in range(count):
            angle = start_angle + 2 * math.pi * i / count
            px = center[0] / w + radius * math.cos(angle)
            py = center[1] / h + radius * math.sin(angle)
            rot = obj.rotation + math.degrees(angle)
            offset = (px * w, py * h)
            instances.append(_obj_to_instance(obj, offset, rot, obj.opacity))

    elif mode == "random":
        count = int(repeat.get("count", 10))
        seed = int(repeat.get("seed", 42))
        rng = np.random.RandomState(seed)
        area = repeat.get("area", {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8})
        ax, ay = float(area.get("x", 0.1)), float(area.get("y", 0.1))
        aw, ah = float(area.get("w", 0.8)), float(area.get("h", 0.8))
        for i in range(count):
            px = ax + rng.random() * aw
            py = ay + rng.random() * ah
            rot = obj.rotation + rng.uniform(-30, 30)
            scale = float(repeat.get("scale_variance", 0.3))
            opacity_var = float(repeat.get("opacity_variance", 0.2))
            obj_opacity = obj.opacity * (1.0 - opacity_var * rng.random())
            offset = (px * w, py * h)
            instances.append(_obj_to_instance(obj, offset, rot, obj_opacity))

    elif mode == "mirror":
        axes = repeat.get("axes", "x")
        base_pos = _parse_position(obj.position, w, h)
        instances.append(_obj_to_instance(obj, (base_pos[0], base_pos[1]), obj.rotation, obj.opacity))
        if "x" in axes:
            mirror_x = w - base_pos[0]
            instances.append(_obj_to_instance(obj, (mirror_x, base_pos[1]), -obj.rotation, obj.opacity))
        if "y" in axes:
            mirror_y = h - base_pos[1]
            instances.append(_obj_to_instance(obj, (base_pos[0], mirror_y), -obj.rotation, obj.opacity))
        if "x" in axes and "y" in axes:
            instances.append(_obj_to_instance(obj, (w - base_pos[0], h - base_pos[1]), obj.rotation + 180, obj.opacity))

    return instances


def _obj_to_instance(obj: CanvasObject, position: tuple, rotation: float, opacity: float) -> Dict:
    return {
        "obj": obj,
        "position": position,
        "rotation": rotation,
        "opacity": min(1.0, max(0.0, opacity)),
    }
