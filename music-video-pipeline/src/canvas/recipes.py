from __future__ import annotations

from typing import Any, Dict, List


def cross_recipe(colors: List[str] = None, opacity: float = 0.3, width: float = 0.12) -> dict:
    colors = colors or ["#1a6078", "#501878", "#080e18"]
    return {
        "canvas": {"base_color": colors[2] if len(colors) > 2 else "#080e18"},
        "palette": {"primary": colors[0], "secondary": colors[1] if len(colors) > 1 else colors[0]},
        "layers": ["h_bar", "v_bar"],
        "objects": {
            "h_bar": {
                "type": "shape",
                "geometry": {"shape": "rectangle"},
                "position": [0.5, 0.5],
                "size": [1.0, width],
                "opacity": opacity,
                "style": {"fill": "$primary", "blend_mode": "screen"},
            },
            "v_bar": {
                "type": "shape",
                "geometry": {"shape": "rectangle"},
                "position": [0.5, 0.5],
                "size": [width, 1.0],
                "opacity": opacity,
                "style": {"fill": "$primary", "blend_mode": "screen"},
            },
        },
    }


def conic_recipe(colors: List[str] = None, offset: float = 0.0, opacity: float = 0.7) -> dict:
    colors = colors or ["#080e18", "#2E86C1", "#0e1628", "#8E44AD", "#1a2548"]
    return {
        "canvas": {"base_color": colors[0]},
        "palette": {},
        "layers": ["conic"],
        "objects": {
            "conic": {
                "type": "light",
                "geometry": {"shape": "conic", "offset": offset},
                "position": [0.5, 0.5],
                "size": [1.0, 1.0],
                "opacity": opacity,
                "style": {"color": "#2E86C1", "intensity": 1.0, "softness": 0.8, "blend_mode": "add"},
            },
        },
    }


def diamond_recipe(colors: List[str] = None, count: int = 1, opacity: float = 0.15, size: float = 0.15) -> dict:
    colors = colors or ["#4A90E2", "#0a0a2e"]
    repeat = {"mode": "none"}
    if count > 1:
        import math
        cols = int(math.ceil(math.sqrt(count)))
        rows = int(math.ceil(count / cols))
        repeat = {"mode": "grid", "rows": rows, "cols": cols, "spacing": size * 1.8}

    return {
        "canvas": {"base_color": colors[1] if len(colors) > 1 else "#0a0a2e"},
        "palette": {"primary": colors[0]},
        "layers": ["diamonds"],
        "objects": {
            "diamonds": {
                "type": "shape",
                "geometry": {"shape": "diamond"},
                "position": [0.5, 0.5],
                "size": [size, size],
                "opacity": opacity,
                "style": {"stroke": "$primary", "stroke_width": 2, "fill": "none", "blend_mode": "screen"},
                "repeat": repeat,
            },
        },
    }


def dual_spot_recipe(
    colors: List[str] = None,
    pos1: List[float] = None,
    pos2: List[float] = None,
    opacity: float = 0.7,
) -> dict:
    colors = colors or ["#2E86C1", "#8E44AD", "#060a14"]
    pos1 = pos1 or [0.3, 0.4]
    pos2 = pos2 or [0.7, 0.6]
    return {
        "canvas": {"base_color": colors[2] if len(colors) > 2 else "#060a14"},
        "palette": {"primary": colors[0], "secondary": colors[1] if len(colors) > 1 else colors[0]},
        "layers": ["spot1", "spot2"],
        "objects": {
            "spot1": {
                "type": "light",
                "geometry": {"shape": "radial"},
                "position": pos1,
                "size": [0.7, 0.7],
                "opacity": opacity,
                "style": {"color": "$primary", "intensity": 1.2, "softness": 1.0, "blend_mode": "add"},
            },
            "spot2": {
                "type": "light",
                "geometry": {"shape": "radial"},
                "position": pos2,
                "size": [0.7, 0.7],
                "opacity": opacity,
                "style": {"color": "$secondary", "intensity": 1.2, "softness": 1.0, "blend_mode": "add"},
            },
        },
    }


def spiral_recipe(colors: List[str] = None, opacity: float = 0.3) -> dict:
    import math
    colors = colors or ["#0a0814", "#1c1a38", "#0a2a3a", "#3a1858", "#1a0a28"]
    points = []
    turns = 3
    steps = 120
    for i in range(steps):
        t = i / steps
        angle = t * turns * 2 * math.pi
        r = t * 0.4
        px = 0.5 + r * math.cos(angle)
        py = 0.5 + r * math.sin(angle)
        points.append([px, py])
    return {
        "canvas": {"base_color": colors[0]},
        "palette": {"primary": colors[2] if len(colors) > 2 else "#0a2a3a"},
        "layers": ["spiral"],
        "objects": {
            "spiral": {
                "type": "path",
                "geometry": {"points": points, "closed": False},
                "position": [0.5, 0.5],
                "size": [1.0, 1.0],
                "opacity": opacity,
                "style": {"stroke": "$primary", "stroke_width": 3, "blend_mode": "screen"},
                "motion": {"type": "rotate", "speed": 0.02},
            },
        },
    }


def bands_recipe(colors: List[str] = None, count: int = 5, opacity: float = 0.25) -> dict:
    colors = colors or ["#4A90E2", "#C0392B", "#1a1a2e"]
    return {
        "canvas": {"base_color": colors[-1] if len(colors) > 2 else "#1a1a2e"},
        "palette": {},
        "layers": ["bands"],
        "objects": {
            "bands": {
                "type": "shape",
                "geometry": {"shape": "rectangle"},
                "position": [0.5, 0.5],
                "size": [1.0, 1.0 / count * 0.6],
                "opacity": opacity,
                "style": {"fill": colors[0], "blend_mode": "screen"},
                "repeat": {"mode": "grid", "rows": count, "cols": 1, "spacing": 1.0 / count},
            },
        },
    }


def radial_recipe(cx: float = 0.25, cy: float = 0.25, colors: List[str] = None, opacity: float = 0.7) -> dict:
    colors = colors or ["#2E86C1", "#0a0a2e"]
    return {
        "canvas": {"base_color": colors[1] if len(colors) > 1 else "#1a1a2e"},
        "palette": {"primary": colors[0]},
        "layers": ["light"],
        "objects": {
            "light": {
                "type": "light",
                "geometry": {"shape": "radial"},
                "position": [cx, cy],
                "size": [0.8, 0.8],
                "opacity": opacity,
                "style": {"color": "$primary", "intensity": 1.2, "softness": 0.8, "blend_mode": "add"},
            },
        },
    }


RECIPES = {
    "cross": cross_recipe,
    "conic": conic_recipe,
    "diamond": diamond_recipe,
    "dual_spot": dual_spot_recipe,
    "spiral": spiral_recipe,
    "bands": bands_recipe,
    "radial_tl": lambda **kw: radial_recipe(0.25, 0.25, **kw),
    "radial_br": lambda **kw: radial_recipe(0.75, 0.75, **kw),
    "radial_center": lambda **kw: radial_recipe(0.5, 0.5, **kw),
}


def get_recipe(name: str, **kwargs) -> dict:
    fn = RECIPES.get(name)
    if fn is None:
        raise ValueError(f"Unknown recipe: {name}. Available: {list(RECIPES.keys())}")
    return fn(**kwargs)
