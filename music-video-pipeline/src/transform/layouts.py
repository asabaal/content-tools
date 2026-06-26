"""Layout transformations: vertical centering and symmetric multi-phrase rows."""

from __future__ import annotations

from typing import List

from .core import REGISTRY, ScriptContext, Transformation

# Reuse the generator's phrase-splitting so multi-row layouts match its notion
# of where a line naturally breaks.
try:  # pragma: no cover - import guard
    from scriptgen.rules import _split_into_phrases
except Exception:  # pragma: no cover
    _split_into_phrases = None  # type: ignore[assignment]


_TWO_ROWS = (0.42, 0.58)
_THREE_ROWS = (0.34, 0.5, 0.66)
_ROW_STEP = 0.16  # spacing for 4+ phrase lines, symmetric about 0.5


def _rows_for(n: int) -> List[float]:
    if n == 2:
        return list(_TWO_ROWS)
    if n == 3:
        return list(_THREE_ROWS)
    return [round(0.5 + (i - (n - 1) / 2.0) * _ROW_STEP, 3) for i in range(n)]


class CenterText(Transformation):
    """Center every selected section's text vertically; drop per-line positions."""

    name = "center_text"
    description = "Set text_position=center on each section and clear per-line position overrides"

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        for idx in ctx.section_indices(selector or None):
            section = ctx.sections[idx]
            visual = section.setdefault("visual", {})
            visual["text_position"] = "center"
            for override in (section.get("lines_overrides", {}) or {}).values():
                override.pop("text_position", None)


class SymmetrizePhraseRows(Transformation):
    """Make multi-phrase lines read as centered pairs/triples.

    Single-phrase lines resolve to the section position (center); 2-phrase lines
    sit symmetric about center (0.42 / 0.58), 3-phrase as 0.34 / 0.5 / 0.66.
    """

    name = "symmetrize_phrase_rows"
    description = "Vertically center multi-phrase lines as symmetric row pairs about 0.5"

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        if _split_into_phrases is None:
            return
        synced_lines = ctx.synced_lines
        for idx in ctx.section_indices(selector or None):
            section = ctx.sections[idx]
            words_overrides = section.setdefault("words_overrides", {})
            for li in section.get("lines", []) or []:
                if li >= len(synced_lines):
                    continue
                words = synced_lines[li].get("words", []) or []
                if not words:
                    continue
                phrases = _split_into_phrases(words)
                if len(phrases) <= 1:
                    # single row -> defer to section position; drop explicit y
                    for wi in range(len(words)):
                        key = f"{li}.{wi}"
                        entry = words_overrides.get(key)
                        if entry and "y" in entry:
                            entry.pop("y", None)
                            if not entry:
                                words_overrides.pop(key, None)
                    continue
                rows = _rows_for(len(phrases))
                for phrase, y in zip(phrases, rows):
                    rounded = round(float(y), 3)
                    for wi in phrase:
                        words_overrides.setdefault(f"{li}.{wi}", {})["y"] = rounded


REGISTRY.register(CenterText())
REGISTRY.register(SymmetrizePhraseRows())


__all__ = ["CenterText", "SymmetrizePhraseRows", "_rows_for"]
