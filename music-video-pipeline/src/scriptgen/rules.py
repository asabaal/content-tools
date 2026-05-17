from __future__ import annotations

from dataclasses import dataclass

from .moods import MoodProfile
from .palette import SectionColor


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
    base = 48
    if section_type in ("chorus", "hook"):
        base = 52 + int(variance * 6)
    elif section_type == "bridge":
        base = 44
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
    positions = ("top", "center", "bottom")

    for line_idx in range(profile.start_line, min(profile.end_line + 1, len(synced_lines))):
        line = synced_lines[line_idx]
        words = line.get("words", [])
        if not words:
            continue

        for w_idx, _word in enumerate(words):
            pos = _word_position(
                w_idx, len(words), line_idx, profile, mood_name, variance, section_position,
            )
            if pos != section_position:
                overrides[f"{line_idx}.{w_idx}"] = {"text_position": pos}

    return overrides


def _word_position(
    word_idx: int,
    word_count: int,
    line_idx: int,
    profile: SectionProfile,
    mood_name: str,
    variance: float,
    section_position: str,
) -> str:
    if mood_name == "dark_moody":
        return _dark_moody_word_pos(word_idx, word_count, line_idx, profile, variance, section_position)
    elif mood_name == "bright_poppy":
        return _bright_poppy_word_pos(word_idx, word_count, variance, section_position)
    elif mood_name == "warm_intimate":
        return _warm_intimate_word_pos(word_idx, word_count, variance, section_position)
    elif mood_name == "cool_ethereal":
        return _cool_ethereal_word_pos(word_idx, word_count, line_idx, variance, section_position)
    elif mood_name == "high_energy":
        return _high_energy_word_pos(word_idx, word_count, variance, section_position)
    return section_position


def _dark_moody_word_pos(
    word_idx: int,
    word_count: int,
    line_idx: int,
    profile: SectionProfile,
    variance: float,
    section_position: str,
) -> str:
    if word_idx == 0 and line_idx == profile.start_line and section_position != "top":
        return "top"
    if word_idx == word_count - 1 and variance > 0.6 and section_position != "bottom":
        return "bottom"
    return section_position


def _bright_poppy_word_pos(
    word_idx: int,
    word_count: int,
    variance: float,
    section_position: str,
) -> str:
    density = 2 if variance < 0.6 else 1
    if word_idx % density != 0:
        return section_position
    cycle = ("top", "center", "bottom", "center")
    return cycle[word_idx % len(cycle)]


def _warm_intimate_word_pos(
    word_idx: int,
    word_count: int,
    variance: float,
    section_position: str,
) -> str:
    density = 3 if variance < 0.6 else 2
    if word_idx % density != 0:
        return section_position
    return "bottom" if section_position != "bottom" else "center"


def _cool_ethereal_word_pos(
    word_idx: int,
    word_count: int,
    line_idx: int,
    variance: float,
    section_position: str,
) -> str:
    skip = 2 if variance < 0.5 else 1
    seed = (line_idx * 7 + word_idx * 13) % 5
    if seed >= skip + 1:
        return section_position
    if section_position == "center":
        return ("top", "bottom")[seed % 2]
    return "center"


def _high_energy_word_pos(
    word_idx: int,
    word_count: int,
    variance: float,
    section_position: str,
) -> str:
    density = 1 if variance > 0.7 else 2
    if word_idx % density != 0:
        return section_position
    pair = word_idx // 2
    cycle = ("top", "bottom", "center")
    return cycle[pair % len(cycle)]


def assign_reactivity(energy: float, section_type: str) -> list[str]:
    if energy < 0.35:
        return []
    if energy < 0.6:
        return ["vocals"]
    if section_type in ("chorus", "hook"):
        return ["vocals", "drums", "energy"]
    return ["vocals", "drums"]


def assign_section_visual(
    profile: SectionProfile,
    color: SectionColor,
    mood: MoodProfile,
    mood_name: str,
    variance: float,
    section_index: int,
) -> dict:
    v = {}
    v.update(assign_background(profile.section_type, profile.energy, mood, variance, section_index))
    v["background_color"] = color.primary
    if v.get("background_type") == "gradient":
        v["gradient_colors"] = [color.primary, color.companion]
    v.update(assign_texture(profile.section_type, profile.energy, mood, variance))
    v["font_size"] = assign_font_size(
        profile.section_type, profile.energy, profile.pace, profile.tags, variance,
    )
    v.update(assign_reveal(profile.section_type, profile.pace))
    v["reactivity"] = assign_reactivity(profile.energy, profile.section_type)
    v["text_position"] = assign_text_position(profile.section_type, section_index, mood_name)
    return v


def compute_emphasis_overrides(
    profile: SectionProfile,
    visual: dict,
    song_name: str,
    is_title_line: bool,
    is_section_start: bool,
) -> dict:
    overrides = {}
    if is_title_line:
        overrides["font_size"] = visual.get("font_size", 48) + 10
    if "BIG" in profile.tags or "big" in profile.tags:
        overrides["font_size"] = visual.get("font_size", 48) + 12
    if profile.energy > 0.75 and is_section_start:
        overrides["font_size"] = visual.get("font_size", 48) + 4
    return overrides if overrides else {}


def _clamp_opacity(v: float) -> float:
    return max(0.05, min(0.8, v))
