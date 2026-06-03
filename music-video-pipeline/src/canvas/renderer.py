from __future__ import annotations

import math
from typing import Any, Dict, Optional

import numpy as np
from PIL import Image

from .models import CanvasObject, CanvasScene, _parse_position, _parse_size, _resolve_color
from .geometry import render_shape, render_path
from .lights import render_light, render_gradient
from .compositing import composite_layer, apply_glow, apply_blur, fill_canvas
from .repetition import expand_repeats
from .motion import apply_motion, transform_layer, place_layer


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


class CanvasRenderer:
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height

    def render_scene(self, scene: CanvasScene, t: float = 0.0) -> Image.Image:
        canvas_cfg = scene.canvas if isinstance(scene.canvas, dict) else {}
        w = int(canvas_cfg.get("width", 0)) or self.width
        h = int(canvas_cfg.get("height", 0)) or self.height
        palette = scene.palette

        canvas = fill_canvas(w, h, scene.base_color)

        for layer_id in scene.layers:
            obj = scene.get_object(layer_id)
            if obj is None:
                continue

            if obj.type == "group":
                canvas = self._render_group(canvas, obj, scene, w, h, t, palette)
            else:
                canvas = self._render_object(canvas, obj, scene, w, h, t, palette)

        return Image.fromarray(canvas)

    def _render_group(
        self,
        canvas: np.ndarray,
        group: CanvasObject,
        scene: CanvasScene,
        w: int,
        h: int,
        t: float,
        palette: Dict[str, str],
    ) -> np.ndarray:
        group_motion = apply_motion(group, _parse_position(group.position, w, h), group.rotation, group.opacity, t, w, h)
        for child_id in group.children:
            child = scene.get_object(child_id)
            if child is None:
                continue
            merged = _merge_group_transform(child, group_motion, w, h)
            canvas = self._render_object(canvas, merged, scene, w, h, t, palette)
        return canvas

    def _render_object(
        self,
        canvas: np.ndarray,
        obj: CanvasObject,
        scene: CanvasScene,
        w: int,
        h: int,
        t: float,
        palette: Dict[str, str],
    ) -> np.ndarray:
        instances = expand_repeats(obj, w, h)

        for inst in instances:
            base_obj = inst["obj"]
            pos = inst["position"]
            rot = inst["rotation"]
            opac = inst["opacity"]

            mot = apply_motion(base_obj, pos, rot, opac, t, w, h)
            pos = mot["position"]
            rot = mot["rotation"]
            opac = mot["opacity"]

            layer = self._draw_object(base_obj, w, h, palette)
            if layer is None:
                continue

            style = base_obj.style
            glow_color_raw = style.get("glow")
            if glow_color_raw and glow_color_raw != "none":
                glow_color = _hex_to_rgb(_resolve_color(glow_color_raw, palette))
                glow_radius = int(style.get("glow_radius", 10))
                glow_intensity = float(style.get("glow_intensity", 0.5))
                glow_layer = apply_glow(layer, glow_color, glow_radius, glow_intensity)
                glow_placed = place_layer(glow_layer, pos, w, h, opac * glow_intensity)
                canvas = composite_layer(canvas, glow_placed, style.get("blend_mode", "screen"))

            blur_radius = float(style.get("blur", 0))
            if blur_radius > 0.5:
                layer = apply_blur(layer, blur_radius)

            if rot != 0:
                layer = transform_layer(layer, pos, rot, w, h)

            placed = place_layer(layer, pos, w, h, opac)
            blend = style.get("blend_mode", "normal")
            canvas = composite_layer(canvas, placed, blend)

            mask_id = base_obj.mask
            if mask_id:
                mask_obj = scene.get_object(mask_id)
                if mask_obj:
                    mask_layer = self._draw_object(mask_obj, w, h, palette)
                    if mask_layer is not None and mask_layer.shape[2] == 4:
                        canvas = composite_layer(canvas, mask_layer, "multiply", mask_layer[:, :, 3])

        return canvas

    def _draw_object(
        self,
        obj: CanvasObject,
        w: int,
        h: int,
        palette: Dict[str, str],
    ) -> Optional[np.ndarray]:
        obj_type = obj.type

        if obj_type == "shape":
            return render_shape(obj, w, h, palette)
        elif obj_type == "light":
            return render_light(obj, w, h, palette)
        elif obj_type == "gradient":
            return render_gradient(obj, w, h, palette)
        elif obj_type == "path":
            return render_path(obj, w, h, palette)
        elif obj_type == "image":
            return self._render_image(obj, w, h, palette)
        elif obj_type == "texture":
            return self._render_texture(obj, w, h, palette)
        elif obj_type == "mask":
            return self._render_mask(obj, w, h, palette)

        return None

    def _render_image(self, obj: CanvasObject, w: int, h: int, palette: Dict[str, str]) -> Optional[np.ndarray]:
        path = obj.geometry.get("src", obj.geometry.get("path", ""))
        if not path:
            return None
        try:
            from pathlib import Path
            p = Path(path)
            if not p.exists():
                return None
            img = Image.open(p).convert("RGBA")
            img = img.resize((w, h), Image.LANCZOS)
            return np.array(img)
        except Exception:
            return None

    def _render_texture(self, obj: CanvasObject, w: int, h: int, palette: Dict[str, str]) -> Optional[np.ndarray]:
        geo = obj.geometry
        noise_type = geo.get("noise_type", "grain")
        seed = int(geo.get("seed", 42))
        rng = np.random.RandomState(seed)

        layer = np.zeros((h, w, 4), dtype=np.uint8)

        if noise_type in ("noise", "grain", "noise_grain"):
            noise = rng.random((h, w)).astype(np.float32)
            val = (noise * 50 * obj.opacity).astype(np.uint8)
            layer[:, :, 0] = val
            layer[:, :, 1] = val
            layer[:, :, 2] = val
            layer[:, :, 3] = int(obj.opacity * 80) if isinstance(obj.opacity, float) else 80
        elif noise_type == "paper":
            noise = rng.random((h, w)).astype(np.float32)
            val = (noise * 20 * obj.opacity).astype(np.uint8)
            layer[:, :, 0] = val
            layer[:, :, 1] = val
            layer[:, :, 2] = val
            layer[:, :, 3] = 60
        elif noise_type == "film":
            noise = rng.random((h, w)).astype(np.float32)
            val = (noise * 40 * obj.opacity).astype(np.uint8)
            layer[:, :, 0] = val
            layer[:, :, 1] = val
            layer[:, :, 2] = val
            layer[:, :, 3] = 70

        return layer

    def _render_mask(self, obj: CanvasObject, w: int, h: int, palette: Dict[str, str]) -> Optional[np.ndarray]:
        geo = obj.geometry
        mask_type = geo.get("shape", "rectangle")
        pos = _parse_position(obj.position, w, h)
        size = _parse_size(obj.size, w, h)
        cx, cy = pos
        sw, sh = size

        layer = np.zeros((h, w, 4), dtype=np.uint8)

        if mask_type in ("rectangle", "rect"):
            half_w, half_h = sw / 2, sh / 2
            x0 = max(0, int(cx - half_w))
            y0 = max(0, int(cy - half_h))
            x1 = min(w, int(cx + half_w))
            y1 = min(h, int(cy + half_h))
            layer[y0:y1, x0:x1] = 255
        elif mask_type in ("circle", "ellipse"):
            ys, xs = np.mgrid[:h, :w].astype(np.float32)
            half_w = max(1.0, sw / 2)
            half_h = max(1.0, sh / 2)
            dx = (xs - cx) / half_w
            dy = (ys - cy) / half_h
            dist = np.sqrt(dx * dx + dy * dy)
            alpha = np.clip((1.0 - dist) * 255, 0, 255).astype(np.uint8)
            layer[:, :, 0] = alpha
            layer[:, :, 1] = alpha
            layer[:, :, 2] = alpha
            layer[:, :, 3] = alpha
        elif mask_type == "gradient":
            ys = np.arange(h, dtype=np.float32) / max(1, h - 1)
            direction = geo.get("direction", "vertical")
            if direction == "horizontal":
                vals = np.arange(w, dtype=np.float32) / max(1, w - 1)
                alpha = np.broadcast_to((vals * 255).astype(np.uint8)[np.newaxis, :], (h, w)).copy()
            else:
                alpha = np.broadcast_to((ys * 255).astype(np.uint8)[:, np.newaxis], (h, w)).copy()
            layer[:, :, 0] = alpha
            layer[:, :, 1] = alpha
            layer[:, :, 2] = alpha
            layer[:, :, 3] = alpha

        if obj.opacity < 1.0:
            layer[:, :, 3] = (layer[:, :, 3].astype(np.float32) * obj.opacity).astype(np.uint8)

        return layer


def _merge_group_transform(child: CanvasObject, group_motion: dict, w: int, h: int) -> CanvasObject:
    merged = CanvasObject(
        id=child.id,
        type=child.type,
        geometry=child.geometry,
        position=child.position,
        size=child.size,
        rotation=child.rotation,
        opacity=child.opacity,
        style=child.style,
        motion=child.motion,
        repeat=child.repeat,
        mask=child.mask,
        timing=child.timing,
        children=child.children,
    )
    merged.rotation += group_motion.get("rotation", 0)
    merged.opacity *= group_motion.get("opacity", 1.0)
    return merged


def render_canvas(config: dict, width: int = 1920, height: int = 1080, t: float = 0.0) -> Image.Image:
    scene = CanvasScene.from_dict(config)
    renderer = CanvasRenderer(width, height)
    return renderer.render_scene(scene, t)
