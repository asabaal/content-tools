"""Background transformations: contrast-safe darkening and per-line variety."""

from __future__ import annotations

from typing import List, Optional

from .colors import (
    GOLD_TEXT_PROXY,
    contrast,
    darken_to_contrast,
    hex_to_hls,
    hls_to_hex,
    clamp,
)
from .core import REGISTRY, ScriptContext, Transformation

_DIRECTION_SET = [
    "diagonal_tl_br",
    "vertical_top_bottom",
    "diagonal_tr_bl",
    "horizontal_left_right",
    "diamond",
    "rings_4",
    "radial_center",
    "conic",
]

_GOLD_STYLES = {"elegant_gold", "gold"}


def _is_gold(section: dict) -> bool:
    style = str((section.get("visual", {}) or {}).get("text_style", "") or "")
    return style in _GOLD_STYLES


def _section_base_color(section: dict) -> str:
    visual = section.get("visual", {}) or {}
    colors = visual.get("gradient_colors") or []
    if colors:
        return colors[0]
    return visual.get("background_color", "#0B1020")


def _darken_one(hex_color: str, text_hex: str, min_contrast: float, floor: float) -> str:
    try:
        return darken_to_contrast(hex_color, text_hex=text_hex, min_contrast=min_contrast,
                                  lightness_floor=floor)
    except ValueError:
        return hex_color


def _darken_section_colors(
    section: dict, text_hex: str, min_contrast: float, floor: float
) -> None:
    visual = section.setdefault("visual", {})
    if visual.get("background_color"):
        visual["background_color"] = _darken_one(
            visual["background_color"], text_hex, min_contrast, floor
        )
    gcolors = visual.get("gradient_colors")
    if isinstance(gcolors, list):
        visual["gradient_colors"] = [
            _darken_one(c, text_hex, min_contrast, floor) for c in gcolors
        ]
    for override in (section.get("lines_overrides", {}) or {}).values():
        if override.get("background_color"):
            override["background_color"] = _darken_one(
                override["background_color"], text_hex, min_contrast, floor
            )
        gc = override.get("gradient_colors")
        if isinstance(gc, list):
            override["gradient_colors"] = [
                _darken_one(c, text_hex, min_contrast, floor) for c in gc
            ]


class DarkenForContrast(Transformation):
    """Darken section/line backgrounds so text meets a minimum contrast ratio.

    Defaults target gold-text sections (the chorus/hook/outro/interlude family)
    but accepts any selector. Hue and saturation are preserved.
    """

    name = "darken_for_contrast"
    description = "Lower background lightness until text clears a contrast floor"

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        text_hex = params.get("text_color", GOLD_TEXT_PROXY)
        min_contrast = float(params.get("min_contrast", 4.5))
        floor = float(params.get("lightness_floor", 0.04))
        if not selector:
            selector = {"style": "gold"}
        for idx in ctx.section_indices(selector):
            _darken_section_colors(ctx.sections[idx], text_hex, min_contrast, floor)


class VaryLineBackgrounds(Transformation):
    """Give each lyrical line a distinct background.

    ``mode``: ``oscillate`` (default) bounces lightness/saturation across the
    section and rotates gradient direction per line; ``escalate`` (intro)
    monotonically increases saturation/lightness/complexity for rising intrigue.

    Gold sections are kept inside the contrast envelope (per-line colors are
    darkened to the text contrast floor) so variety never sacrifices
    readability.
    """

    name = "vary_line_backgrounds"
    description = "Generate distinct per-line background colors and gradient directions"

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        mode = params.get("mode", "oscillate")
        hue_span = float(params.get("hue_span", 0.10))
        lit_osc = float(params.get("lit_osc", 0.05))
        sat_osc = float(params.get("sat_osc", 0.12))
        directions = params.get("directions") or _DIRECTION_SET
        gold_text = params.get("text_color", GOLD_TEXT_PROXY)
        gold_min_contrast = float(params.get("min_contrast", 4.5))
        gold_floor = float(params.get("lightness_floor", 0.04))

        sel = selector or None
        for idx in ctx.section_indices(sel):
            section = ctx.sections[idx]
            is_gold = _is_gold(section)
            base = _section_base_color(section)
            try:
                b_h, b_l, b_s = hex_to_hls(base)
            except ValueError:
                continue

            line_indices = [int(x) for x in (section.get("lines", []) or [])]
            n = max(1, len(line_indices))
            lines_overrides = section.setdefault("lines_overrides", {})

            for pos, li in enumerate(line_indices):
                t = pos / max(1, n - 1)  # 0..1 across the section

                if mode == "escalate":
                    hue = (b_h + hue_span * t) % 1.0
                    lit = clamp(b_l + lit_osc * t, 0.05, 0.22)
                    sat = clamp(b_s + sat_osc * (0.4 + 0.6 * t), 0.05, 0.95)
                    direction = directions[min(len(directions) - 1, pos + 2)]
                else:
                    sign = 1.0 if pos % 2 == 0 else -1.0
                    hue = (b_h + hue_span * (t - 0.5) + 0.0) % 1.0
                    lit = clamp(b_l + lit_osc * sign, 0.04, 0.22)
                    sat = clamp(b_s + sat_osc * sign, 0.05, 0.95)
                    direction = directions[pos % len(directions)]

                primary = hls_to_hex(hue, lit, sat)
                companion = hls_to_hex((hue + 0.03) % 1.0, clamp(lit + 0.05, 0.0, 0.95),
                                       clamp(sat * 0.85, 0.05, 0.95))

                if is_gold:
                    primary = _darken_one(primary, gold_text, gold_min_contrast, gold_floor)
                    companion = _darken_one(companion, gold_text, gold_min_contrast, gold_floor)

                entry = lines_overrides.get(str(li))
                if entry is None:
                    entry = {}
                    lines_overrides[str(li)] = entry
                entry["background_color"] = primary
                entry["gradient_colors"] = [primary, companion]
                entry["gradient_direction"] = direction


REGISTRY.register(DarkenForContrast())
REGISTRY.register(VaryLineBackgrounds())


__all__ = [
    "DarkenForContrast",
    "VaryLineBackgrounds",
    "_darken_section_colors",
    "_DIRECTION_SET",
]
