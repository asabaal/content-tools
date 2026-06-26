"""Branded intro/outro scene transformation.

Adds the top-level ``intro`` and ``outro`` blocks the renderer needs to produce
the branded opening (image -> title card "A Reality Signal / by / Asabaal
Horan") and closing ("Presented by" + logo) scenes, modelled on the AI Psalm 9
reference script.
"""

from __future__ import annotations

from .core import REGISTRY, ScriptContext, Transformation


def _title_case_slug(name: str) -> str:
    cleaned = (name or "").replace("-", " ").replace("_", " ").strip()
    if not cleaned:
        return ""
    return " ".join(w.capitalize() for w in cleaned.split())


class AddBrandedScenes(Transformation):
    """Write ``intro``/``outro`` blocks so the renderer emits branded scenes."""

    name = "add_branded_scenes"
    description = "Add top-level intro/outro blocks (image, title, logo) for branded scenes"

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        branding_image = params.get("branding_image", "")
        logo_path = params.get("logo_path", "")
        title = params.get("title") or _title_case_slug(ctx.script.get("name", ""))
        subtitle = params.get("subtitle", "A Reality Signal")
        text = params.get("text", "Presented by")

        duration = params.get("duration")
        if (duration is None or duration == "") and ctx.synced_lines:
            # The renderer scans ALL lines for an active word, so the intro can
            # only occupy the gap before the globally-earliest vocal word.
            starts = [
                float(w.get("start", 0.0))
                for ln in ctx.synced_lines
                for w in (ln.get("words", []) or [])
            ]
            start = min(starts) if starts else 0.0
            min_duration = float(params.get("min_duration", 1.5))
            duration = round(start, 3) if start >= min_duration else 0.0
        if duration is None:
            duration = 0.0

        ctx.script["intro"] = {
            "image": branding_image,
            "title": title,
            "subtitle": subtitle,
            "duration": float(duration),
        }
        ctx.script["outro"] = {
            "image": branding_image,
            "logo": logo_path,
            "text": text,
        }


REGISTRY.register(AddBrandedScenes())


__all__ = ["AddBrandedScenes"]
