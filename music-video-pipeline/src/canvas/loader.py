from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import CanvasScene


VALID_OBJECT_TYPES = {"shape", "light", "gradient", "path", "image", "texture", "mask", "group"}
VALID_BLEND_MODES = {"normal", "screen", "multiply", "overlay", "soft_light", "add", "lighten", "darken"}
VALID_MOTION_TYPES = {"static", "rotate", "drift", "pulse", "breathe", "zoom", "shimmer", "orbit"}
VALID_REPEAT_MODES = {"none", "grid", "radial", "random", "mirror"}
VALID_SHAPE_TYPES = {"rectangle", "rect", "circle", "ellipse", "polygon", "diamond", "line", "ring", "arc", "grid", "hexagon", "octagon", "pentagon", "triangle"}
VALID_LIGHT_TYPES = {"radial", "conic", "spot"}


class ValidationError(Exception):
    pass


def validate_scene(data: dict) -> List[str]:
    errors: List[str] = []

    if not isinstance(data, dict):
        return ["Scene must be a dictionary"]

    objects = data.get("objects", {})
    if not isinstance(objects, dict):
        errors.append("objects must be a dictionary")
        return errors

    ids = set()
    for oid, odata in objects.items():
        if not isinstance(odata, dict):
            errors.append(f"Object '{oid}' must be a dictionary")
            continue

        ids.add(oid)

        obj_type = odata.get("type", "")
        if obj_type and obj_type not in VALID_OBJECT_TYPES:
            errors.append(f"Object '{oid}': unknown type '{obj_type}'")

        style = odata.get("style", {})
        if isinstance(style, dict):
            blend = style.get("blend_mode", "")
            if blend and blend not in VALID_BLEND_MODES:
                errors.append(f"Object '{oid}': unknown blend_mode '{blend}'")

        motion = odata.get("motion", {})
        if isinstance(motion, dict):
            mtype = motion.get("type", "")
            if mtype and mtype not in VALID_MOTION_TYPES:
                errors.append(f"Object '{oid}': unknown motion type '{mtype}'")

        repeat = odata.get("repeat", {})
        if isinstance(repeat, dict):
            rmode = repeat.get("mode", "")
            if rmode and rmode not in VALID_REPEAT_MODES:
                errors.append(f"Object '{oid}': unknown repeat mode '{rmode}'")

        children = odata.get("children", [])
        for cid in children:
            if cid not in objects:
                errors.append(f"Object '{oid}': references missing child '{cid}'")

        mask = odata.get("mask")
        if mask and mask not in objects:
            errors.append(f"Object '{oid}': references missing mask '{mask}'")

    layers = data.get("layers", list(objects.keys()))
    for lid in layers:
        if lid not in objects:
            errors.append(f"Layer '{lid}' not found in objects")

    return errors


def load_scene(data: dict) -> CanvasScene:
    errors = validate_scene(data)
    if errors:
        raise ValidationError(f"Canvas scene validation failed: {'; '.join(errors)}")
    return CanvasScene.from_dict(data)
