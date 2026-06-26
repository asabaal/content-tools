"""Geometric background transformation (learned from the AI Psalm 9 reference).

AI Psalm 9 keeps all of its visual geometry at the *section* level: each section
has a 5-stop palette with visible mid-tone accents (lum ~0.05-0.10) on a varied,
parameterized gradient direction (``cross``, ``conic_0.8``, ``spiral``,
``dual_spot_...``). Crucially, its per-line overrides carry only ``font_size`` —
never background — so the section geometry actually renders.

This transform reproduces that recipe and, just as importantly, **strips per-line
background/gradient keys** that would otherwise mask the geometry.
"""

from __future__ import annotations

from typing import List, Tuple

from .colors import hex_to_hls, hls_to_hex, clamp
from .core import REGISTRY, ScriptContext, Transformation
from render.readability import relative_luminance

GEO_DIRECTIONS = [
    "cross",
    "conic_0.8",
    "dual_spot_0.3_0.4_0.7_0.6",
    "spiral",
    "diamond",
    "rings_4",
    "dual_spot_0.3_0.3_0.7_0.7",
    "burst",
    "conic_0.6",
    "grid_8",
]

_PER_LINE_BG_KEYS = ("background_color", "gradient_colors", "gradient_direction")


def _enrich_to_5(colors: List[str], accent_l: float = 0.24, second_l: float = 0.20) -> List[str]:
    """Build a 5-stop dark/bright/dark/bright/dark palette from existing colors.

    Accent hues are taken from the most-saturated existing stops (the section's
    identity colors), then reshaped to visible mid-tones (HLS lightness
    ~0.20-0.24, ~relative luminance 0.05-0.10) so the geometric direction
    renders without sitting too bright behind the text. Mirrors the AI Psalm 9
    palette structure.
    """
    stops: List[Tuple[float, float, float, float]] = []
    for c in colors or []:
        try:
            h, l, s = hex_to_hls(c)
            stops.append((h, l, s, relative_luminance(c)))
        except (ValueError, TypeError):
            continue
    if not stops:
        stops = [(0.10, 0.5, 0.60, 0.2)]

    viable = [st for st in stops if st[3] > 0.02] or stops
    # Most colorful identity first; luminance breaks ties.
    viable.sort(key=lambda st: (st[2], st[3]), reverse=True)

    a1 = viable[0]
    a2 = viable[1] if len(viable) > 1 else ((a1[0] + 0.06) % 1.0, a1[1], a1[2], a1[3])

    a1 = (a1[0], accent_l, max(a1[2], 0.45))
    a2 = (a2[0], second_l, max(a2[2], 0.35))

    dark1 = (a1[0], 0.010, a1[2] * 0.5)
    dark_mid = (a2[0], 0.018, a2[2] * 0.5)
    dark2 = (a1[0], 0.012, a1[2] * 0.4)

    return [
        hls_to_hex(*dark1),
        hls_to_hex(*a1),
        hls_to_hex(*dark_mid),
        hls_to_hex(*a2),
        hls_to_hex(*dark2),
    ]


class GeometricBackgrounds(Transformation):
    """Give each section a 5-stop geometric palette and strip per-line backgrounds."""

    name = "geometric_backgrounds"
    description = "5-stop section palettes + varied geometric directions; clear per-line bg overrides"

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        directions = params.get("directions") or GEO_DIRECTIONS
        accent_l = float(params.get("accent_lightness", 0.24))

        indices = ctx.section_indices(selector or None)
        for gi, idx in enumerate(indices):
            section = ctx.sections[idx]
            visual = section.setdefault("visual", {})
            colors = visual.get("gradient_colors") or [visual.get("background_color", "#0B1020")]
            palette = _enrich_to_5(colors, accent_l)
            visual["gradient_colors"] = palette
            visual["background_color"] = palette[0]
            visual["gradient_direction"] = directions[gi % len(directions)]

            # Critical: per-line background overrides mask the section geometry.
            lines_overrides = section.get("lines_overrides") or {}
            for key in list(lines_overrides.keys()):
                entry = lines_overrides[key]
                for bg_key in _PER_LINE_BG_KEYS:
                    entry.pop(bg_key, None)
                if not entry:
                    del lines_overrides[key]


REGISTRY.register(GeometricBackgrounds())


__all__ = ["GeometricBackgrounds", "GEO_DIRECTIONS", "_enrich_to_5"]
