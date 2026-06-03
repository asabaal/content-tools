from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


def _resolve_color(raw: str, palette: Dict[str, str]) -> str:
    if raw.startswith("$"):
        return palette.get(raw[1:], raw)
    return raw


def _parse_position(pos, canvas_w: int, canvas_h: int) -> Tuple[float, float]:
    if pos is None:
        return (canvas_w / 2.0, canvas_h / 2.0)
    if isinstance(pos, (list, tuple)):
        x, y = pos
    elif isinstance(pos, dict):
        x = pos.get("x", 0.5)
        y = pos.get("y", 0.5)
    else:
        x = y = float(pos)
    if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
        return (x * canvas_w, y * canvas_h)
    return (float(x), float(y))


def _parse_size(size, canvas_w: int, canvas_h: int) -> Tuple[float, float]:
    if size is None:
        return (float(canvas_w), float(canvas_h))
    if isinstance(size, (list, tuple)):
        w, h = size
    elif isinstance(size, dict):
        w = size.get("w", 1.0)
        h = size.get("h", 1.0)
    else:
        w = h = float(size)
    if 0.0 <= w <= 1.0 and 0.0 <= h <= 1.0:
        return (w * canvas_w, h * canvas_h)
    return (float(w), float(h))


@dataclass
class CanvasObject:
    id: str
    type: str
    geometry: Dict[str, Any] = field(default_factory=dict)
    position: Any = None
    size: Any = None
    rotation: float = 0.0
    opacity: float = 1.0
    style: Dict[str, Any] = field(default_factory=dict)
    motion: Dict[str, Any] = field(default_factory=dict)
    repeat: Dict[str, Any] = field(default_factory=dict)
    mask: Optional[str] = None
    timing: Dict[str, Any] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> CanvasObject:
        return cls(
            id=data.get("id", ""),
            type=data.get("type", "shape"),
            geometry=data.get("geometry", {}),
            position=data.get("position"),
            size=data.get("size"),
            rotation=data.get("rotation", 0.0),
            opacity=data.get("opacity", 1.0),
            style=data.get("style", {}),
            motion=data.get("motion", {}),
            repeat=data.get("repeat", {}),
            mask=data.get("mask"),
            timing=data.get("timing", {}),
            children=data.get("children", []),
        )


@dataclass
class CanvasScene:
    canvas: Dict[str, Any] = field(default_factory=lambda: {
        "width": 1920, "height": 1080, "base_color": "#0d1117",
    })
    palette: Dict[str, str] = field(default_factory=dict)
    layers: List[str] = field(default_factory=list)
    objects: Dict[str, CanvasObject] = field(default_factory=dict)
    text_safety: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> CanvasScene:
        objects = {}
        for oid, odata in data.get("objects", {}).items():
            if isinstance(odata, dict):
                odata.setdefault("id", oid)
                objects[oid] = CanvasObject.from_dict(odata)
        layers = data.get("layers", list(objects.keys()))
        return cls(
            canvas=data.get("canvas", {}),
            palette=data.get("palette", {}),
            layers=layers,
            objects=objects,
            text_safety=data.get("text_safety", {}),
        )

    def get_object(self, obj_id: str) -> Optional[CanvasObject]:
        return self.objects.get(obj_id)

    @property
    def width(self) -> int:
        return int(self.canvas.get("width", 1920))

    @property
    def height(self) -> int:
        return int(self.canvas.get("height", 1080))

    @property
    def base_color(self) -> str:
        return self.canvas.get("base_color", "#0d1117")
