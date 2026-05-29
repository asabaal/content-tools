from __future__ import annotations

from dataclasses import dataclass

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
    st = profile.resolved_type or profile.section_type

    for line_idx in range(profile.start_line, min(profile.end_line + 1, len(synced_lines))):
        line = synced_lines[line_idx]
        words = line.get("words", [])
        if not words:
            continue

        for w_idx, word_data in enumerate(words):
            word_ov = {}
            pos = _word_position(
                w_idx, len(words), line_idx, profile, mood_name, variance, section_position,
            )
            if pos != section_position:
                word_ov["text_position"] = pos

            word_text = word_data.get("text", "") if isinstance(word_data, dict) else str(word_data)

            if variance > 0.4 and w_idx == 0 and st in ("chorus", "pre_chorus"):
                word_ov["font_size_delta"] = 2
            if variance > 0.5 and w_idx == len(words) - 1 and len(word_text) <= 4 and len(words) <= 3:
                word_ov["font_size_delta"] = -2

            if word_ov:
                overrides[f"{line_idx}.{w_idx}"] = word_ov

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
    _MOOD_STYLE = {
        "dark_moody": "neon",
        "bright_poppy": "graffiti",
        "warm_intimate": "gold",
        "cool_ethereal": "ice",
        "high_energy": "fire",
    }
    _SECTION_OVERRIDE = {
        "chorus": {"dark_moody": "neon", "high_energy": "fire", "bright_poppy": "chrome"},
        "bridge": {"dark_moody": "hologram", "cool_ethereal": "hologram"},
    }
    override = _SECTION_OVERRIDE.get(section_type, {}).get(mood_name)
    if override:
        return override
    return _MOOD_STYLE.get(mood_name, "basic")


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
    base_font = visual.get("font_size", 48)
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

    return overrides if overrides else {}


def _clamp_opacity(v: float) -> float:
    return max(0.05, min(0.8, v))
