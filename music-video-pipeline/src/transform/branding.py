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


class AddInterstitialBranding(Transformation):
    """Add interstitial branded scenes between lyric lines.

    Accepts a mapping of line-gap indices to content specifiers.
    Index convention: ``0`` is before the first line, ``1`` is between
    line 1 and line 2, ``2`` is between line 2 and line 3, etc.

    Each insertion can specify ``start`` and ``end`` times explicitly,
    or they are inferred from the gap between adjacent sync lines.

    Example params::

        {
            "insertions": {
                "1": {"type": "image", "path": "branding.png"},
                "2": {"type": "title", "title": "ASABAAL", "subtitle": "A Reality Signal"}
            }
        }
    """

    name = "add_interstitial_branding"
    description = "Add interstitial branded scenes at specified line-gap indices"

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        insertions = params.get("insertions", {})
        if not insertions:
            return

        interstitials = []
        lines = ctx.synced_lines

        for idx_str, ins in sorted(insertions.items()):
            idx = int(idx_str)

            start = ins.get("start")
            end = ins.get("end")

            if start is None or end is None:
                if idx == 0:
                    prev_end = 0.0
                    next_start = (
                        lines[0]["words"][0]["start"]
                        if lines and lines[0].get("words")
                        else 0.0
                    )
                elif idx >= len(lines):
                    prev_end = (
                        lines[-1]["words"][-1]["end"]
                        if lines and lines[-1].get("words")
                        else 0.0
                    )
                    next_start = prev_end + 3.0
                else:
                    prev = lines[idx - 1]
                    prev_end = (
                        prev["words"][-1]["end"]
                        if prev.get("words")
                        else prev.get("end", 0.0)
                    )
                    nxt = lines[idx]
                    next_start = (
                        nxt["words"][0]["start"]
                        if nxt.get("words")
                        else nxt.get("start", 0.0)
                    )
                if start is None:
                    start = prev_end
                if end is None:
                    end = next_start

            if start >= end:
                continue

            entry = {"start": start, "end": end}
            ins_type = ins.get("type", "image")
            entry["type"] = ins_type
            if ins_type == "image":
                entry["path"] = ins.get("path", "")
            elif ins_type == "title":
                entry["title"] = ins.get("title", "")
                entry["subtitle"] = ins.get("subtitle", "")

            interstitials.append(entry)

        if interstitials:
            ctx.script["interstitials"] = interstitials


REGISTRY.register(AddBrandedScenes())
REGISTRY.register(AddInterstitialBranding())


__all__ = ["AddBrandedScenes", "AddInterstitialBranding"]
