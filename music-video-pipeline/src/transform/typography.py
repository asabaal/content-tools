"""Typography / signature transformations."""

from __future__ import annotations

from typing import Any

from .colors import shift_hue
from .core import REGISTRY, ScriptContext, Transformation


class SetSectionFont(Transformation):
    """Set font size on selected sections.

    With ``size``: writes the absolute size to the section visual and (by
    default) to every line override so the size reads uniformly. With ``delta``:
    applies a relative bump to the existing sizes.
    """

    name = "set_section_font"
    description = "Set or bump section font sizes (optionally uniform across lines)"

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        size = params.get("size")
        delta = params.get("delta")
        uniform_lines = params.get("uniform_lines", True)
        if size is None and delta is None:
            return

        for idx in ctx.section_indices(selector or None):
            section = ctx.sections[idx]
            visual = section.setdefault("visual", {})
            current = visual.get("font_size")
            if size is not None:
                target = int(size)
            else:
                base = current if isinstance(current, int) else 80
                target = int(base) + int(delta or 0)
            visual["font_size"] = target

            lines_overrides = section.get("lines_overrides", {}) or {}
            if uniform_lines:
                for li in (section.get("lines", []) or []):
                    entry = lines_overrides.get(str(li))
                    if entry is None:
                        entry = {}
                        lines_overrides[str(li)] = entry
                    entry["font_size"] = target


class SetSectionVisual(Transformation):
    """Merge arbitrary keys into the ``visual`` block of selected sections.

    Used declaratively in recipes to assign per-type signatures (gradient
    direction, bg animation preset, text style, etc.).
    """

    name = "set_section_visual"
    description = "Merge arbitrary keys into section.visual for selected sections"

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        keys = params.get("keys") or {}
        # also allow top-level scalar params (e.g. direction, bg_animation_preset)
        for k, v in params.items():
            if k == "keys":
                continue
            keys.setdefault(k, v)
        if not keys:
            return
        for idx in ctx.section_indices(selector or None):
            visual = ctx.sections[idx].setdefault("visual", {})
            visual.update(keys)


class ShiftSectionHue(Transformation):
    """Rotate the hue of a section's background palette by ``delta`` (turns)."""

    name = "shift_section_hue"
    description = "Rotate section background hue, preserving lightness/saturation"

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        delta = float(params.get("delta", 0.0))
        if not delta:
            return
        for idx in ctx.section_indices(selector or None):
            section = ctx.sections[idx]
            visual = section.setdefault("visual", {})
            if visual.get("background_color"):
                visual["background_color"] = shift_hue(visual["background_color"], delta)
            gc = visual.get("gradient_colors")
            if isinstance(gc, list):
                visual["gradient_colors"] = [shift_hue(c, delta) for c in gc]
            for override in (section.get("lines_overrides", {}) or {}).values():
                if override.get("background_color"):
                    override["background_color"] = shift_hue(override["background_color"], delta)
                ogc = override.get("gradient_colors")
                if isinstance(ogc, list):
                    override["gradient_colors"] = [shift_hue(c, delta) for c in ogc]


REGISTRY.register(SetSectionFont())
REGISTRY.register(SetSectionVisual())
REGISTRY.register(ShiftSectionHue())


__all__ = ["SetSectionFont", "SetSectionVisual", "ShiftSectionHue"]
