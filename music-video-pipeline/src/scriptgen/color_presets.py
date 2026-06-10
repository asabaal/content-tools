from __future__ import annotations

import colorsys
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TextBoxConfig:
    enabled: bool
    color: str
    opacity: float
    padding: int
    radius: int


@dataclass(frozen=True)
class ColorPreset:
    name: str
    display_name: str
    description: str
    themes: tuple[str, ...]
    background_base: str
    background_mid: str
    foreground_colors: tuple[str, ...]
    accent_color: str
    glow_color: Optional[str]
    shadow_color: Optional[str]
    recommended_text_color: str
    recommended_text_style: str
    recommended_text_box: Optional[TextBoxConfig]
    max_foreground_opacity: float
    compatible_geometries: tuple[str, ...]


_PRESETS: dict[str, ColorPreset] = {}


def _r(name: str, **kwargs) -> None:
    _PRESETS[name] = ColorPreset(name=name, **kwargs)


_r("dark_teal_emerald",
   display_name="Dark Teal & Emerald",
   description="Deep dark teal background with emerald green accents and luminous highlights",
   themes=("mysterious", "forest", "calm", "ambient", "peace", "wilderness"),
   background_base="#060e12",
   background_mid="#0d3a2a",
   foreground_colors=("#0d4a3a", "#1db88a", "#0a3028"),
   accent_color="#2effa8",
   glow_color="#1db88a",
   shadow_color="#02100a",
   recommended_text_color="#ffffff",
   recommended_text_style="neon",
   recommended_text_box=TextBoxConfig(True, "#000000", 0.45, 12, 10),
   max_foreground_opacity=0.75,
   compatible_geometries=("grid", "spiral", "rings", "bands"),
)

_r("gold_deep_navy",
   display_name="Gold on Deep Navy",
   description="Rich navy blue base with warm gold accents and subtle metallic highlights",
   themes=("prophetic", "glory", "ancient", "celebration", "hopeful"),
   background_base="#080c1e",
   background_mid="#1a2858",
   foreground_colors=("#c9a227", "#0f1a38", "#3d3010"),
   accent_color="#ffd700",
   glow_color="#c9a227",
   shadow_color="#02030a",
   recommended_text_color="#ffffff",
   recommended_text_style="gold",
   recommended_text_box=TextBoxConfig(True, "#000000", 0.4, 14, 12),
   max_foreground_opacity=0.8,
   compatible_geometries=("grid", "diamond", "cross", "radial_center"),
)

_r("electric_blue_noir",
   display_name="Electric Blue on Noir",
   description="Near-black background with bright electric blue signal highlights",
   themes=("synthetic", "signal", "warning", "urban", "night"),
   background_base="#060610",
   background_mid="#0a1430",
   foreground_colors=("#1a4090", "#00b4ff", "#0a2060"),
   accent_color="#00d4ff",
   glow_color="#00b4ff",
   shadow_color="#000004",
   recommended_text_color="#ffffff",
   recommended_text_style="chrome",
   recommended_text_box=TextBoxConfig(True, "#000000", 0.55, 10, 8),
   max_foreground_opacity=0.7,
   compatible_geometries=("grid", "conic", "burst", "scatter_field"),
)

_r("sandstone_warm",
   display_name="Sandstone & Warm Brown",
   description="Warm earth-tone palette with sand, brown, and terracotta accents",
   themes=("desert", "ancient", "warm", "earth", "peace"),
   background_base="#1a140e",
   background_mid="#3d2e1e",
   foreground_colors=("#a08060", "#5c4030", "#c4a070"),
   accent_color="#d4a574",
   glow_color="#a08060",
   shadow_color="#0a0806",
   recommended_text_color="#1a140e",
   recommended_text_style="",
   recommended_text_box=None,
   max_foreground_opacity=0.85,
   compatible_geometries=("bands", "diamond", "linear"),
)

_r("deep_purple_violet",
   display_name="Deep Purple & Violet",
   description="Dark violet background with rich purple and magenta accents",
   themes=("night", "mysterious", "prophetic", "lament", "somber"),
   background_base="#0a0614",
   background_mid="#2a1050",
   foreground_colors=("#7b2fbe", "#1a0838", "#a040d0"),
   accent_color="#a855f7",
   glow_color="#7b2fbe",
   shadow_color="#040208",
   recommended_text_color="#ffffff",
   recommended_text_style="neon",
   recommended_text_box=TextBoxConfig(True, "#000000", 0.45, 12, 10),
   max_foreground_opacity=0.7,
   compatible_geometries=("conic", "spiral", "rings", "spot_field"),
)

_r("stark_monochrome",
   display_name="Stark Monochrome",
   description="Pure black and white high contrast palette for maximum readability",
   themes=("high_contrast", "minimal", "documentary"),
   background_base="#000000",
   background_mid="#222222",
   foreground_colors=("#333333", "#555555", "#444444"),
   accent_color="#ffffff",
   glow_color=None,
   shadow_color=None,
   recommended_text_color="#ffffff",
   recommended_text_style="",
   recommended_text_box=None,
   max_foreground_opacity=0.9,
   compatible_geometries=(),
)

_r("burnt_orange_charcoal",
   display_name="Burnt Orange on Charcoal",
   description="Dark charcoal base with warm burnt orange and ember-like highlights",
   themes=("fire", "warning", "warm", "ember", "glory"),
   background_base="#0e0a08",
   background_mid="#2a1a10",
   foreground_colors=("#cc5500", "#1a1008", "#ff7722"),
   accent_color="#ff6b35",
   glow_color="#cc5500",
   shadow_color="#060402",
   recommended_text_color="#ffffff",
   recommended_text_style="fire",
   recommended_text_box=TextBoxConfig(True, "#000000", 0.4, 12, 10),
   max_foreground_opacity=0.75,
   compatible_geometries=("rings", "burst", "radial_center", "bands"),
)

_r("steel_gray_slate",
   display_name="Steel Gray & Slate",
   description="Cool industrial gray palette with muted blue-steel accents",
   themes=("documentary", "somber", "urban", "ambient"),
   background_base="#10121a",
   background_mid="#2a3040",
   foreground_colors=("#5a6a7a", "#3a4450", "#6a7a8a"),
   accent_color="#8aa0b8",
   glow_color="#5a6a7a",
   shadow_color="#06080c",
   recommended_text_color="#e0e0e0",
   recommended_text_style="",
   recommended_text_box=None,
   max_foreground_opacity=0.8,
   compatible_geometries=("linear", "bands", "grid"),
)


THEME_PRESETS: dict[str, list[str]] = {
    "wilderness": ["dark_teal_emerald", "sandstone_warm"],
    "prophetic": ["gold_deep_navy", "deep_purple_violet"],
    "lament": ["deep_purple_violet", "steel_gray_slate"],
    "glory": ["gold_deep_navy", "burnt_orange_charcoal"],
    "warning": ["electric_blue_noir", "burnt_orange_charcoal"],
    "peace": ["dark_teal_emerald", "steel_gray_slate"],
    "synthetic": ["electric_blue_noir", "stark_monochrome"],
    "ancient": ["sandstone_warm", "gold_deep_navy"],
    "ambient": ["steel_gray_slate", "dark_teal_emerald"],
    "mysterious": ["dark_teal_emerald", "deep_purple_violet"],
    "desert": ["sandstone_warm"],
    "fire": ["burnt_orange_charcoal"],
    "night": ["deep_purple_violet", "electric_blue_noir"],
    "urban": ["steel_gray_slate", "electric_blue_noir"],
    "celebration": ["gold_deep_navy", "burnt_orange_charcoal"],
    "somber": ["steel_gray_slate", "deep_purple_violet"],
    "hopeful": ["gold_deep_navy", "dark_teal_emerald"],
    "minimal": ["stark_monochrome"],
    "documentary": ["steel_gray_slate", "stark_monochrome"],
    "high_contrast": ["stark_monochrome"],
    "earth": ["sandstone_warm", "burnt_orange_charcoal"],
    "calm": ["dark_teal_emerald", "steel_gray_slate"],
    "signal": ["electric_blue_noir"],
    "forest": ["dark_teal_emerald"],
    "warm": ["sandstone_warm", "burnt_orange_charcoal"],
}


@dataclass
class PresetRecommendation:
    preset: ColorPreset
    reason: str
    expected_mood: str
    recommended_text_color: str
    text_box_needed: bool
    warnings: list[str]


def get_preset(name: str) -> ColorPreset:
    if name in _PRESETS:
        return _PRESETS[name]
    available = ", ".join(sorted(_PRESETS.keys()))
    raise KeyError(f"Unknown color preset '{name}'. Available: {available}")


def list_presets() -> list[ColorPreset]:
    return list(_PRESETS.values())


def recommend_presets(theme: str, n: int = 3) -> list[PresetRecommendation]:
    theme_lower = theme.lower().strip()
    preset_names = THEME_PRESETS.get(theme_lower, [])
    if not preset_names:
        for t_key, p_names in THEME_PRESETS.items():
            if theme_lower in t_key or t_key in theme_lower:
                preset_names = p_names
                break
    results: list[PresetRecommendation] = []
    for pname in preset_names[:n]:
        p = _PRESETS[pname]
        warnings: list[str] = []
        if p.max_foreground_opacity < 0.6:
            warnings.append("Low foreground opacity may produce muddy shapes")
        if not p.recommended_text_box or not p.recommended_text_box.enabled:
            warnings.append("No text box recommended — ensure background has low busyness")
        results.append(PresetRecommendation(
            preset=p,
            reason=f"Theme '{theme_lower}' maps to {p.display_name}",
            expected_mood=p.themes[0] if p.themes else "neutral",
            recommended_text_color=p.recommended_text_color,
            text_box_needed=p.recommended_text_box is not None and p.recommended_text_box.enabled,
            warnings=warnings,
        ))
    return results


def preset_to_script_colors(preset: ColorPreset) -> dict:
    result: dict = {
        "background_color": preset.background_base,
        "gradient_colors": [preset.background_mid, preset.accent_color],
        "text_auto_contrast": False,
        "text_color": preset.recommended_text_color,
    }
    if preset.recommended_text_style:
        result["text_style"] = preset.recommended_text_style
    if len(preset.foreground_colors) > 2:
        result["gradient_colors"] = list(preset.foreground_colors[:3]) + [preset.accent_color]
    if preset.recommended_text_box and preset.recommended_text_box.enabled:
        result["text_backdrop"] = True
        result["text_backdrop_color"] = preset.recommended_text_box.color
        result["text_backdrop_opacity"] = preset.recommended_text_box.opacity
        result["text_backdrop_padding"] = preset.recommended_text_box.padding
        result["text_backdrop_radius"] = preset.recommended_text_box.radius
    if preset.accent_color:
        result["highlight_color"] = preset.accent_color
    return result


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    return colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))


def _shift_color(hex_color: str, hue_shift: float = 0, sat_mult: float = 1.0, lit_shift: float = 0) -> tuple[int, int, int]:
    r, g, b = _hex_to_rgb(hex_color)
    h, l, s = _rgb_to_hsl(r, g, b)
    h = (h + hue_shift) % 1.0
    s = max(0.0, min(1.0, s * sat_mult))
    l = max(0.0, min(1.0, l + lit_shift))
    return _hsl_to_rgb(h, s, l)


def style_colors_from_accent(accent_hex: str) -> dict[str, dict]:
    base = _hex_to_rgb(accent_hex)
    h, l, s = _rgb_to_hsl(*base)
    dark = _hsl_to_rgb(h, s, max(0.0, l - 0.3))
    mid = _hsl_to_rgb(h, s, max(0.0, l - 0.15))
    bright = _hsl_to_rgb(h, min(1.0, s + 0.1), min(1.0, l + 0.1))
    desat_dark = _hsl_to_rgb(h, max(0.0, s * 0.4), max(0.0, l * 0.4))
    desat_mid = _hsl_to_rgb(h, max(0.0, s * 0.6), max(0.0, l * 0.5))
    warm = _hsl_to_rgb((h - 0.05) % 1.0, min(1.0, s * 1.2), l)
    cool = _hsl_to_rgb((h + 0.1) % 1.0, s, min(1.0, l + 0.05))
    return {
        "neon": {"core_color": bright, "glow_color": mid},
        "chrome": {"glow_color": mid, "gradient_top": bright, "gradient_mid": base, "gradient_bottom": dark},
        "gold": {"glow_color": mid, "gradient_top": bright, "gradient_bottom": dark},
        "fire": {"flame_core": bright, "flame_mid": base, "flame_outer": dark, "glow_color": warm},
        "ice": {"glow_color": cool, "core_color": bright},
        "hologram": {"glow_color": mid, "core_color": bright},
        "graffiti": {"outline_color": dark, "gradient_top": bright, "gradient_bottom": base},
        "matrix": {"core_color": bright, "glow_color": desat_mid},
        "basic": {},
    }
