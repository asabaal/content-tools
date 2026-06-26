"""Selectors: resolve declarative specs to concrete section/line addresses.

Supported selector shapes (any combination, ``section`` wins for resolution):

    {}                                 -> all sections
    {"section": "hook"}                -> every section whose type is "hook"
    {"section": "hook:2"}              -> the 2nd hook (1-based ordinal)
    {"sections": ["chorus", "hook"]}   -> all sections of any listed type
    {"index": 3}                       -> absolute section index (0-based)
    {"indices": [0, 2]}                -> several absolute indices
    {"style": "elegant_gold"}          -> sections whose visual.text_style matches
    {"style": "gold"}                  -> alias matching any gold style
    {"name_contains": "Verse"}         -> sections whose name contains substring

Gold style alias groups:

    "gold"   -> {"elegant_gold", "gold"}
    "white"  -> {"clean_white"}
    "neon"   -> {"neon", "neon_glow"}
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

_GOLD_STYLES = {"elegant_gold", "gold"}
_WHITE_STYLES = {"clean_white"}
_NEON_STYLES = {"neon", "neon_glow"}

_STYLE_ALIASES: Dict[str, set] = {
    "gold": _GOLD_STYLES,
    "white": _WHITE_STYLES,
    "neon": _NEON_STYLES,
}


def _section_style(section: dict) -> str:
    visual = section.get("visual", {}) or {}
    return str(visual.get("text_style", "") or "")


def _match_style(section: dict, style: str) -> bool:
    actual = _section_style(section)
    alias = _STYLE_ALIASES.get(style.lower())
    if alias is not None:
        return actual in alias
    return actual == style


def _parse_type_ordinal(token: str) -> tuple:
    if ":" in token:
        base, _, ord_str = token.partition(":")
        try:
            return base, int(ord_str)
        except ValueError:
            return token, 0
    return token, 0


def _norm_type(value: str) -> str:
    """Normalize a section type for matching (hyphens <-> underscores, lowercased)."""
    return str(value).strip().lower().replace("-", "_")


def resolve_section_indices(sections: List[dict], selector: Optional[Dict[str, Any]]) -> List[int]:
    """Return the 0-based indices of sections targeted by ``selector``."""
    if not selector:
        return list(range(len(sections)))

    # Direct absolute indexing short-circuits everything else.
    if "index" in selector:
        idx = int(selector["index"])
        return [idx] if 0 <= idx < len(sections) else []
    if "indices" in selector:
        out = []
        for idx in selector["indices"]:
            idx = int(idx)
            if 0 <= idx < len(sections):
                out.append(idx)
        return out

    matched: List[int] = []

    style = selector.get("style")
    types = selector.get("sections")
    if "section" in selector:
        types = [selector["section"]] if isinstance(selector["section"], str) else list(selector["section"])
    elif isinstance(types, str):
        types = [types]
    elif types is None:
        types = []

    name_contains = selector.get("name_contains")

    type_filters: List[tuple] = []
    for token in types or []:
        base, ordinal = _parse_type_ordinal(str(token))
        type_filters.append((_norm_type(base), ordinal))

    for i, sec in enumerate(sections):
        keep = True

        if style is not None and not _match_style(sec, str(style)):
            keep = False

        if keep and type_filters:
            stype = _norm_type(sec.get("type", ""))
            ordinal_seen = 0
            ordinal_match = False
            for base, ordinal in type_filters:
                if stype == base:
                    ordinal_seen += 1
                    if ordinal == 0 or ordinal_seen == ordinal:
                        ordinal_match = True
            if not ordinal_match:
                keep = False

        if keep and name_contains is not None:
            if str(name_contains).lower() not in str(sec.get("name", "")).lower():
                keep = False

        if keep:
            matched.append(i)

    return matched


def resolve_line_keys(section: dict) -> List[int]:
    """Return the integer line indices a section governs (in order)."""
    out: List[int] = []
    for value in section.get("lines", []) or []:
        try:
            out.append(int(value))
        except (TypeError, ValueError):
            continue
    return out


__all__ = ["resolve_section_indices", "resolve_line_keys"]
