from __future__ import annotations

import colorsys
import random
from dataclasses import dataclass

from .moods import MoodProfile


@dataclass
class SectionColor:
    primary: str
    companion: str
    hue: float
    sat: float
    lit: float


def _hsl_to_hex(h: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def _hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    return colorsys.rgb_to_hls(r, g, b)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _section_hue(
    base_hue: float,
    section_type: str,
    index: int,
    variance: float,
) -> float:
    shift = 0.0
    if section_type in ("chorus", "hook"):
        shift = 0.45 + variance * 0.1
    elif section_type == "bridge":
        shift = 0.08 + variance * 0.05
    elif section_type == "pre_chorus":
        shift = 0.04
    elif section_type == "interlude":
        shift = 0.15
    elif section_type in ("verse",):
        shift = index * 0.03 * (0.5 + variance * 0.5)
    elif section_type == "intro":
        shift = 0.0
    elif section_type == "outro":
        shift = -0.02
    else:
        shift = index * 0.02
    return (base_hue + shift) % 1.0


def _section_sat(
    mood: MoodProfile,
    section_type: str,
    energy: float,
    variance: float,
) -> float:
    lo, hi = mood.saturation
    base = _lerp(lo, hi, 0.5)
    if section_type in ("chorus", "hook"):
        base = _lerp(lo, hi, 0.7 + variance * 0.2)
    elif section_type in ("intro", "outro"):
        base = _lerp(lo, hi, 0.2)
    elif section_type == "bridge":
        base = _lerp(lo, hi, 0.4)
    energy_boost = (energy - 0.5) * 0.15 * variance
    return _clamp(base + energy_boost, lo, hi)


def _section_lit(
    mood: MoodProfile,
    section_type: str,
    energy: float,
    variance: float,
) -> float:
    lo, hi = mood.lightness
    base = _lerp(lo, hi, 0.5)
    if section_type in ("chorus", "hook"):
        base = _lerp(lo, hi, 0.7 + variance * 0.15)
    elif section_type in ("intro", "outro"):
        base = _lerp(lo, hi, 0.15)
    elif section_type == "bridge":
        base = _lerp(lo, hi, 0.35)
    energy_boost = (energy - 0.5) * 0.1 * variance
    return _clamp(base + energy_boost, lo, hi)


@dataclass
class LineColor:
    primary: str
    companion: str


_HUE_DRIFT = {
    "dark_moody": (0.005, 0.01),
    "bright_poppy": (0.02, 0.04),
    "warm_intimate": (0.01, 0.02),
    "cool_ethereal": (0.015, 0.03),
    "high_energy": (0.03, 0.06),
}

_LIT_OSCILLATION = {
    "dark_moody": 0.02,
    "bright_poppy": 0.03,
    "warm_intimate": 0.02,
    "cool_ethereal": 0.02,
    "high_energy": 0.04,
}


def generate_line_colors(
    section_color: SectionColor,
    num_lines: int,
    mood_name: str,
    variance: float,
) -> list[LineColor]:
    if num_lines <= 1:
        return [LineColor(primary=section_color.primary, companion=section_color.companion)]

    hue_lo, hue_hi = _HUE_DRIFT.get(mood_name, (0.01, 0.02))
    lit_osc = _LIT_OSCILLATION.get(mood_name, 0.02)

    hue_step = _lerp(hue_lo, hue_hi, variance) / max(1, num_lines - 1)
    lit_step = lit_osc * variance

    colors = []
    for i in range(num_lines):
        h = (section_color.hue + hue_step * i) % 1.0
        l = section_color.lit + lit_step * (1 if i % 2 == 0 else -1) * (0.5 + 0.5 * (i / max(1, num_lines - 1)))
        s = section_color.sat

        l = _clamp(l, 0.05, 0.95)

        primary = _hsl_to_hex(h, s, l)
        comp_h = (h + 0.03 + variance * 0.02) % 1.0
        comp_s = _clamp(s * 0.85, 0.05, 0.95)
        comp_l = _clamp(l + 0.06, 0.05, 0.95)
        companion = _hsl_to_hex(comp_h, comp_s, comp_l)

        colors.append(LineColor(primary=primary, companion=companion))

    return colors


def generate_palette(
    section_types: list[str],
    energies: list[float],
    mood: MoodProfile,
    variance: float,
    base_color: str | None = None,
) -> list[SectionColor]:
    base_hue = mood.base_hue / 360.0
    if base_color:
        h, l, s = _hex_to_hsl(base_color)
        base_hue = h

    colors = []
    verse_count = 0
    for i, stype in enumerate(section_types):
        if stype == "verse":
            verse_count += 1
        energy = energies[i] if i < len(energies) else 0.5
        h = _section_hue(base_hue, stype, verse_count, variance)
        s = _section_sat(mood, stype, energy, variance)
        l = _section_lit(mood, stype, energy, variance)

        primary = _hsl_to_hex(h, s, l)

        comp_h = (h + 0.03 + variance * 0.02) % 1.0
        comp_s = _clamp(s * 0.85, mood.saturation[0], mood.saturation[1])
        comp_l = _clamp(l + 0.06, mood.lightness[0], mood.lightness[1])
        companion = _hsl_to_hex(comp_h, comp_s, comp_l)

        colors.append(SectionColor(primary=primary, companion=companion, hue=h, sat=s, lit=l))

    return colors
