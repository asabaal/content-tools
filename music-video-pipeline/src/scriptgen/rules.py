from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .moods import MoodProfile
from .palette import SectionColor
from render.effect_presets import get_preset_for_section


@dataclass
class SectionProfile:
    section_type: str
    name: str
    start_line: int
    end_line: int
    start_time: float
    end_time: float
    energy: float
    spectral_centroid: float
    pace: float
    tags: list[str]
    word_count: int
    resolved_type: str = ""


GRADIENT_ROTATION = [
    "diagonal_tl_br",
    "vertical_top_bottom",
    "diagonal_tr_bl",
    "horizontal_left_right",
]


def _energy_level(energy: float) -> str:
    if energy < 0.3:
        return "low"
    elif energy < 0.6:
        return "medium"
    return "high"


def _pace_level(pace: float) -> str:
    if pace < 2.0:
        return "slow"
    elif pace < 4.0:
        return "medium"
    return "fast"


_CANONICAL_KEYWORDS: dict[str, list[str]] = {
    "intro": ["intro", "opening", "prologue", "preface"],
    "verse": ["verse", "testimony", "melodic", "strophe", "stanza"],
    "chorus": ["chorus", "hook", "refrain", "lift", "declaration", "peak", "anthem", "praise"],
    "bridge": ["bridge", "breakdown", "interlude", "liturgical", "break", "spoken_word"],
    "pre_chorus": ["pre_chorus", "prechorus", "build", "ramp", "climb", "rising"],
    "outro": ["outro", "ending", "closing", "resolution", "final", "coda", "fade"],
}


def resolve_section_type(section_type: str, name: str, tags: list[str], energy: float) -> str:
    _STANDARD = {"intro", "verse", "chorus", "hook", "bridge", "pre_chorus", "outro", "interlude"}
    if section_type in _STANDARD:
        return section_type

    searchable = f"{section_type} {name}".lower()
    for tag in tags:
        searchable += f" {tag.lower()}"

    best_match = None
    best_score = 0
    for canonical, keywords in _CANONICAL_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in searchable:
                score += len(kw)
        if score > best_score:
            best_score = score
            best_match = canonical

    if best_match:
        return best_match

    if energy < 0.25:
        return "intro"
    if energy > 0.65:
        return "chorus"
    return "verse"


def assign_background(
    section_type: str,
    energy: float,
    mood: MoodProfile,
    variance: float,
    section_index: int,
) -> dict:
    bg_type = "solid"
    direction = mood.direction
    if mood.gradient_likely:
        bg_type = "gradient"
    if section_type in ("intro", "outro"):
        bg_type = "gradient" if mood.gradient_likely else "solid"
    elif section_type in ("chorus", "hook"):
        bg_type = "gradient"
    elif section_type == "bridge":
        bg_type = "gradient"
    direction = GRADIENT_ROTATION[section_index % len(GRADIENT_ROTATION)]
    if section_type == "bridge":
        direction = GRADIENT_ROTATION[(section_index + 2) % len(GRADIENT_ROTATION)]
    return {"background_type": bg_type, "gradient_direction": direction}


def assign_texture(
    section_type: str,
    energy: float,
    mood: MoodProfile,
    variance: float,
) -> dict:
    tex = mood.texture_default
    opacity = 0.2
    if section_type in ("intro", "outro"):
        if tex == "none":
            tex = "vignette_soft"
        opacity = 0.35
    elif section_type in ("chorus", "hook"):
        if energy > 0.6 and variance > 0.5:
            tex = "grain_film"
        opacity = 0.15
    elif section_type == "bridge":
        if tex not in ("none", "vignette_soft"):
            tex = "vignette_soft"
        opacity = 0.25
    if energy < 0.3:
        opacity = _clamp_opacity(opacity + 0.15)
    return {"texture_type": tex, "texture_opacity": opacity, "texture_blend_mode": "multiply"}


def assign_font_size(
    section_type: str,
    energy: float,
    pace: float,
    tags: list[str],
    variance: float,
) -> int:
    base = 112
    if section_type in ("chorus", "hook"):
        base = 124 + int(variance * 6)
    elif section_type == "bridge":
        base = 100
    energy_mod = int((energy - 0.5) * 8 * variance)
    if "BIG" in tags or "big" in tags:
        energy_mod += 8
    if pace > 4.0:
        base = max(36, base - 4)
    return max(32, min(72, base + energy_mod))


def assign_reveal(section_type: str, pace: float) -> dict:
    if section_type == "bridge":
        return {"reveal_mode": "line-by-line"}
    if section_type in ("chorus", "hook"):
        if pace > 3.5:
            return {"reveal_mode": "progressive", "reveal_words": 2}
        return {"reveal_mode": "karaoke"}
    if pace > 4.0:
        return {"reveal_mode": "progressive", "reveal_words": 3}
    return {"reveal_mode": "progressive", "reveal_words": 1}


def assign_text_position(
    section_type: str,
    section_index: int,
    mood_name: str,
) -> str:
    _POSITIONS = {
        "intro": "top",
        "verse": "center",
        "chorus": "bottom",
        "hook": "bottom",
        "pre_chorus": "center",
        "bridge": "top",
        "outro": "bottom",
    }
    base = _POSITIONS.get(section_type, "center")

    if mood_name == "bright_poppy":
        if section_type == "verse" and section_index % 2 == 1:
            base = "top"
        elif section_type == "bridge":
            base = "bottom"
    elif mood_name == "warm_intimate":
        if base == "top":
            base = "center"
        if section_type == "verse" and section_index % 2 == 0:
            base = "bottom"
    elif mood_name == "high_energy":
        if section_type == "verse":
            base = "top" if section_index % 2 == 0 else "bottom"
        elif section_type == "intro":
            base = "top"
        elif section_type == "bridge":
            base = "bottom"
    elif mood_name == "cool_ethereal":
        if section_type == "verse" and section_index % 3 == 2:
            base = "bottom"

    return base


_PHRASE_BREAK_PUNCT = {",", ";", ":", "—", "–"}
_PHRASE_BREAK_WORDS = {"that", "when", "while", "where", "which", "because", "although"}


def _split_into_phrases(words: list[dict]) -> list[list[int]]:
    if len(words) <= 3:
        return [list(range(len(words)))]

    groups: list[list[int]] = []
    current: list[int] = []

    for i, w in enumerate(words):
        text = w.get("text", "") if isinstance(w, dict) else str(w)
        clean = text.rstrip(".,;:!?—–")
        current.append(i)

        breaks_after = False
        if any(c in text for c in _PHRASE_BREAK_PUNCT):
            breaks_after = True
        elif i < len(words) - 1 and clean.lower() in _PHRASE_BREAK_WORDS:
            breaks_after = True

        if breaks_after and i < len(words) - 1:
            groups.append(current)
            current = []

    if current:
        groups.append(current)

    if len(groups) == 1 and len(words) > 5:
        mid = len(words) // 2
        groups = [list(range(mid)), list(range(mid, len(words)))]

    return groups


_POSITION_ROWS: dict[str, list[str]] = {
    "top": ["top", "center"],
    "center": ["top", "center", "bottom"],
    "bottom": ["center", "bottom"],
}

_POS_TO_Y = {"top": 0.2, "center": 0.5, "bottom": 0.8}

_MOOD_ROW_STRATEGIES: dict[str, list[str]] = {
    "dark_moody": ["center", "bottom"],
    "bright_poppy": ["top", "center", "bottom"],
    "warm_intimate": ["center", "bottom"],
    "cool_ethereal": ["center", "bottom"],
    "high_energy": ["top", "center", "bottom"],
}


def assign_word_positions(
    profile: SectionProfile,
    section_position: str,
    mood_name: str,
    variance: float,
    synced_lines: list[dict] | None = None,
) -> dict[str, dict]:
    if variance < 0.3:
        return {}

    if synced_lines is None:
        return {}

    overrides: dict[str, dict] = {}
    st = profile.resolved_type or profile.section_type

    rows = _MOOD_ROW_STRATEGIES.get(mood_name, [section_position])

    for line_idx in range(profile.start_line, min(profile.end_line + 1, len(synced_lines))):
        line = synced_lines[line_idx]
        words = line.get("words", [])
        if not words:
            continue

        phrases = _split_into_phrases(words)

        if len(phrases) <= 1:
            continue

        _ROW_ORDER = {"top": 0, "center": 1, "bottom": 2}
        available_rows = sorted(rows, key=lambda r: _ROW_ORDER.get(r, 1))
        while len(available_rows) < len(phrases):
            available_rows.append(available_rows[-1])

        for p_idx, phrase_word_indices in enumerate(phrases):
            row = available_rows[p_idx]
            if row == section_position:
                continue
            for w_idx in phrase_word_indices:
                overrides[f"{line_idx}.{w_idx}"] = {"y": _POS_TO_Y[row]}

        for w_idx, word_data in enumerate(words):
            word_text = word_data.get("text", "") if isinstance(word_data, dict) else str(word_data)
            key = f"{line_idx}.{w_idx}"
            if key not in overrides:
                overrides[key] = {}
            if variance > 0.4 and w_idx == 0 and st in ("chorus", "pre_chorus"):
                overrides[key]["font_size_delta"] = 2
            if variance > 0.5 and w_idx == len(words) - 1 and len(word_text) <= 4 and len(words) <= 3:
                overrides[key]["font_size_delta"] = -2
            if not overrides[key]:
                del overrides[key]

    return overrides


def assign_reactivity(energy: float, section_type: str) -> list[str]:
    if energy < 0.35:
        return []
    if energy < 0.6:
        return ["vocals"]
    if section_type in ("chorus", "hook"):
        return ["vocals", "drums", "energy"]
    return ["vocals", "drums"]


def assign_animation(section_type: str, mood_name: str) -> dict:
    _ANIM_MAP = {
        "intro": "scale_in",
        "verse": "fade_in",
        "chorus": "bounce_in",
        "hook": "bounce_in",
        "bridge": "slide_in",
        "pre_chorus": "fade_in",
        "outro": "fade_out",
    }
    anim = _ANIM_MAP.get(section_type, "fade_in")
    if mood_name == "high_energy":
        if section_type == "chorus":
            anim = "elastic_in"
        elif section_type == "intro":
            anim = "bounce_in"
    elif mood_name == "cool_ethereal":
        anim = "fade_in"
    elif mood_name == "bright_poppy":
        if section_type in ("chorus", "hook"):
            anim = "scale_in"
    speed = 1.0
    if mood_name == "high_energy":
        speed = 1.3
    elif mood_name == "cool_ethereal":
        speed = 0.7
    return {"animation_type": anim, "animation_speed": speed}


def assign_text_style(section_type: str, mood_name: str) -> str:
    _SECTION_STYLE = {
        "intro": {"dark_moody": "neon", "bright_poppy": "graffiti", "warm_intimate": "gold", "cool_ethereal": "ice", "high_energy": "fire"},
        "verse": {"dark_moody": "neon", "bright_poppy": "chrome", "warm_intimate": "gold", "cool_ethereal": "ice", "high_energy": "fire"},
        "chorus": {"dark_moody": "neon", "bright_poppy": "chrome", "warm_intimate": "gold", "cool_ethereal": "neon", "high_energy": "fire"},
        "hook": {"dark_moody": "neon", "bright_poppy": "chrome", "warm_intimate": "gold", "cool_ethereal": "neon", "high_energy": "fire"},
        "bridge": {"dark_moody": "hologram", "bright_poppy": "hologram", "warm_intimate": "hologram", "cool_ethereal": "hologram", "high_energy": "hologram"},
        "pre_chorus": {"dark_moody": "neon", "bright_poppy": "chrome", "warm_intimate": "gold", "cool_ethereal": "chrome", "high_energy": "chrome"},
        "outro": {"dark_moody": "neon", "bright_poppy": "graffiti", "warm_intimate": "gold", "cool_ethereal": "gold", "high_energy": "fire"},
    }
    override = _SECTION_STYLE.get(section_type, {}).get(mood_name)
    if override:
        return override
    _MOOD_STYLE = {
        "dark_moody": "neon",
        "bright_poppy": "graffiti",
        "warm_intimate": "gold",
        "cool_ethereal": "ice",
        "high_energy": "fire",
    }
    return _MOOD_STYLE.get(mood_name, "basic")


_STYLE_FONT_MAP = {
    "ice": 1,
    "neon": 2,
    "chrome": 3,
    "hologram": 4,
    "gold": 5,
    "fire": 6,
    "graffiti": 2,
    "matrix": 4,
    "basic": 0,
}

_SECTION_CATEGORY_PREF = {
    "intro": "display",
    "verse": "sans",
    "pre_chorus": "sans",
    "chorus": "display",
    "hook": "display",
    "bridge": "serif",
    "outro": "serif",
    "breakdown": "handwriting",
    "interlude": "handwriting",
}

_NONVIABLE_FONTS = {
    1748,  # Yarndings 12 — renders text as knitted/cross-stitch chart pictographs
    1749,  # Yarndings 12 Charted — renders text as knitted/cross-stitch chart pictographs
    1750,  # Yarndings 20 — renders text as knitted/cross-stitch chart pictographs
    1751,  # Yarndings 20 Charted — renders text as knitted/cross-stitch chart pictographs
}

_font_pool_cache = None


def _load_font_pool() -> dict:
    global _font_pool_cache
    if _font_pool_cache is not None:
        return _font_pool_cache
    _font_pool_cache = {"sans": [], "serif": [], "display": [], "handwriting": [], "mono": []}
    reg_path = Path(__file__).resolve().parent.parent / "render" / "font_registry.json"
    if reg_path.exists():
        try:
            import json as _json
            data = _json.loads(reg_path.read_text(encoding="utf-8"))
            for name, info in data.items():
                cat = info.get("category", "sans")
                fid = info["id"]
                if cat in _font_pool_cache and fid not in _NONVIABLE_FONTS:
                    _font_pool_cache[cat].append(fid)
        except Exception:
            pass
    for cat in _font_pool_cache:
        _font_pool_cache[cat].sort()
    return _font_pool_cache


def assign_font_family(text_style: str, section_type: str = "", song_name: str = "", section_index: int = 0) -> int:
    legacy = _STYLE_FONT_MAP.get(text_style, 0)
    pool = _load_font_pool()
    if not any(pool.values()):
        return legacy

    pref_cat = _SECTION_CATEGORY_PREF.get(section_type, "sans")
    candidates = pool.get(pref_cat, pool.get("sans", []))
    if not candidates:
        return legacy

    song_hash = hash(song_name) if song_name else 0
    seed = abs(song_hash + section_index * 7919) % len(candidates)
    return candidates[seed]


def _energy_preset_override(section_type: str, energy: float, mood_name: str) -> str | None:
    if energy < 0.25:
        if section_type == "intro":
            return "smooth"
        return None
    if energy > 0.65:
        if section_type in ("chorus", "hook"):
            return "intense" if mood_name == "high_energy" else "energetic"
        if section_type == "verse":
            return "cinematic"
        return None
    if 0.4 < energy < 0.65:
        if section_type in ("verse", "pre_chorus"):
            if mood_name in ("cool_ethereal", "dark_moody"):
                return "dreamy"
            return "cinematic"
        if section_type == "bridge":
            return "dreamy"
    return None


def assign_section_visual(
    profile: SectionProfile,
    color: SectionColor,
    mood: MoodProfile,
    mood_name: str,
    variance: float,
    section_index: int,
) -> dict:
    st = profile.resolved_type or profile.section_type
    v = {}
    v.update(assign_background(st, profile.energy, mood, variance, section_index))
    v["background_color"] = color.primary
    if v.get("background_type") == "gradient":
        v["gradient_colors"] = [color.primary, color.companion]
    v.update(assign_texture(st, profile.energy, mood, variance))
    v["font_size"] = assign_font_size(
        st, profile.energy, profile.pace, profile.tags, variance,
    )
    v.update(assign_reveal(st, profile.pace))
    v["reactivity"] = assign_reactivity(profile.energy, st)
    v["text_position"] = assign_text_position(st, section_index, mood_name)
    v.update(assign_animation(st, mood_name))

    energy_preset = _energy_preset_override(st, profile.energy, mood_name)
    preset_name = energy_preset or get_preset_for_section(st, mood_name).name
    from render.effect_presets import get_preset as _get_preset
    preset = _get_preset(preset_name)
    v["bg_animation_preset"] = preset.name
    if preset.audio_reactivity and not v.get("reactivity"):
        v["reactivity"] = preset.audio_reactivity
    v["text_style"] = assign_text_style(st, mood_name)
    v["font_family"] = assign_font_family(v["text_style"], st, "", section_index)
    return v


def compute_emphasis_overrides(
    profile: SectionProfile,
    visual: dict,
    song_name: str,
    is_title_line: bool,
    is_section_start: bool,
    line_index_in_section: int = 0,
    num_lines_in_section: int = 1,
) -> dict:
    overrides = {}
    base_font = visual.get("font_size", 112)
    st = profile.resolved_type or profile.section_type
    variance = 0.5

    if is_title_line:
        overrides["font_size"] = base_font + 10
    if "BIG" in profile.tags or "big" in profile.tags:
        overrides["font_size"] = base_font + 12
    if profile.energy > 0.75 and is_section_start:
        overrides["font_size"] = base_font + 4

    if num_lines_in_section > 1:
        t = line_index_in_section / max(1, num_lines_in_section - 1)
        if st == "pre_chorus":
            size_curve = int(t * 4)
            overrides["font_size"] = overrides.get("font_size", base_font) + size_curve
        elif st == "outro":
            size_curve = int((1 - t) * 3)
            overrides["font_size"] = overrides.get("font_size", base_font) - size_curve
        elif st == "chorus":
            if line_index_in_section == num_lines_in_section // 2:
                overrides["font_size"] = overrides.get("font_size", base_font) + 3
        elif st == "verse":
            if line_index_in_section % 2 == 1:
                overrides["font_size"] = overrides.get("font_size", base_font) - 1

    synced_text = ""
    if hasattr(profile, 'name'):
        synced_text = profile.name.lower()
    if num_lines_in_section > 1 and line_index_in_section < num_lines_in_section:
        pass

    if st == "pre_chorus" and num_lines_in_section > 1:
        t = line_index_in_section / max(1, num_lines_in_section - 1)
        if t > 0.6:
            overrides["animation_type"] = "scale_in"
            overrides["animation_speed"] = visual.get("animation_speed", 1.0) * 1.2

    if st == "verse" and num_lines_in_section >= 4 and line_index_in_section == num_lines_in_section - 1:
        overrides["text_position"] = "bottom"

    reveal = visual.get("reveal_mode", "progressive")
    word_count = profile.word_count
    if word_count > 0:
        words_per_line = word_count / max(1, num_lines_in_section)
    else:
        words_per_line = 4
    if reveal == "progressive" and words_per_line > 5:
        overrides["text_align"] = "left"
    elif reveal == "line-by-line":
        overrides["text_align"] = "center"

    return overrides if overrides else {}


def _clamp_opacity(v: float) -> float:
    return max(0.05, min(0.8, v))
