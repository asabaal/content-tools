from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EffectPreset:
    name: str
    effects: List[Dict] = field(default_factory=list)
    audio_reactivity: List[str] = field(default_factory=list)

    def describe(self) -> str:
        lines = [f"Preset: {self.name}"]
        for eff in self.effects:
            lines.append(f"  - {eff['effect']}: {eff.get('params', {})}")
        if self.audio_reactivity:
            lines.append(f"  - audio: {self.audio_reactivity}")
        return "\n".join(lines)


PRESETS: Dict[str, EffectPreset] = {
    "cinematic": EffectPreset(
        name="cinematic",
        effects=[
            {"effect": "ken_burns", "params": {"speed": 0.1, "max_zoom": 1.03, "drift": 10.0}},
            {"effect": "color_drift", "params": {"speed": 0.1, "hue_range": 5.0, "sat_pulse": 0.05}},
            {"effect": "bokeh_particles", "params": {"count": 6, "speed": 0.2, "color": [200, 220, 255], "max_radius": 25, "max_alpha": 0.1}},
            {"effect": "radial_pulse", "params": {"speed": 0.4, "max_alpha": 0.08}},
            {"effect": "zoom_pulse", "params": {"intensity": 0.03, "speed": 0.5}},
            {"effect": "color_shift", "params": {"hue_shift": 5.0}},
            {"effect": "vignette_pulse", "params": {"intensity": 0.15}},
        ],
        audio_reactivity=["energy"],
    ),
    "energetic": EffectPreset(
        name="energetic",
        effects=[
            {"effect": "ken_burns", "params": {"speed": 0.15, "max_zoom": 1.05, "drift": 20.0}},
            {"effect": "bokeh_particles", "params": {"count": 15, "speed": 0.5, "color": [255, 200, 100], "max_radius": 35, "max_alpha": 0.18}},
            {"effect": "radial_pulse", "params": {"speed": 0.6, "max_alpha": 0.1}},
            {"effect": "camera_shake", "params": {"intensity": 3.0}},
            {"effect": "brightness_pulse", "params": {"speed": 2.0}},
        ],
        audio_reactivity=["drums", "energy"],
    ),
    "dreamy": EffectPreset(
        name="dreamy",
        effects=[
            {"effect": "ken_burns", "params": {"speed": 0.08, "max_zoom": 1.05, "drift": 20.0}},
            {"effect": "color_drift", "params": {"speed": 0.12, "hue_range": 10.0, "sat_pulse": 0.1}},
            {"effect": "bokeh_particles", "params": {"count": 18, "speed": 0.2, "color": [180, 200, 255], "max_radius": 40, "max_alpha": 0.12}},
            {"effect": "radial_pulse", "params": {"speed": 0.3, "max_alpha": 0.1}},
            {"effect": "wave_distortion", "params": {"intensity": 2.0, "speed": 0.5}},
            {"effect": "zoom_blur", "params": {"intensity": 0.01}},
            {"effect": "vignette_pulse", "params": {"intensity": 0.2}},
        ],
        audio_reactivity=["energy"],
    ),
    "glitch": EffectPreset(
        name="glitch",
        effects=[
            {"effect": "ken_burns", "params": {"speed": 0.15, "max_zoom": 1.04, "drift": 12.0}},
            {"effect": "bokeh_particles", "params": {"count": 8, "speed": 0.4, "color": [255, 100, 255], "max_radius": 20, "max_alpha": 0.12}},
            {"effect": "radial_pulse", "params": {"speed": 0.5, "max_alpha": 0.08}},
            {"effect": "glitch", "params": {"intensity": 0.4}},
            {"effect": "contrast_pulse", "params": {"speed": 3.0}},
        ],
        audio_reactivity=["drums"],
    ),
    "minimal": EffectPreset(
        name="minimal",
        effects=[],
        audio_reactivity=[],
    ),
    "psychedelic": EffectPreset(
        name="psychedelic",
        effects=[
            {"effect": "ken_burns", "params": {"speed": 0.2, "max_zoom": 1.06, "drift": 25.0}},
            {"effect": "color_drift", "params": {"speed": 0.25, "hue_range": 15.0, "sat_pulse": 0.12}},
            {"effect": "bokeh_particles", "params": {"count": 20, "speed": 0.6, "color": [255, 150, 50], "max_radius": 35, "max_alpha": 0.15}},
            {"effect": "radial_pulse", "params": {"speed": 0.7, "max_alpha": 0.12}},
            {"effect": "color_shift", "params": {"hue_shift": 30.0}},
            {"effect": "wave_distortion", "params": {"intensity": 4.0, "speed": 2.0}},
        ],
        audio_reactivity=["energy", "drums"],
    ),
    "smooth": EffectPreset(
        name="smooth",
        effects=[
            {"effect": "ken_burns", "params": {"speed": 0.08, "max_zoom": 1.03, "drift": 12.0}},
            {"effect": "color_drift", "params": {"speed": 0.08, "hue_range": 4.0, "sat_pulse": 0.04}},
            {"effect": "bokeh_particles", "params": {"count": 8, "speed": 0.15, "color": [220, 230, 255], "max_radius": 25, "max_alpha": 0.08}},
            {"effect": "radial_pulse", "params": {"speed": 0.3, "max_alpha": 0.06}},
            {"effect": "zoom_pulse", "params": {"intensity": 0.02, "speed": 0.3}},
            {"effect": "vignette_pulse", "params": {"intensity": 0.1}},
        ],
        audio_reactivity=["energy"],
    ),
    "intense": EffectPreset(
        name="intense",
        effects=[
            {"effect": "camera_shake", "params": {"intensity": 5.0}},
            {"effect": "zoom_pulse", "params": {"intensity": 0.06, "speed": 3.0}},
            {"effect": "glitch", "params": {"intensity": 0.3}},
        ],
        audio_reactivity=["drums", "energy", "vocals"],
    ),
    "ambient": EffectPreset(
        name="ambient",
        effects=[
            {"effect": "ken_burns", "params": {"speed": 0.12, "max_zoom": 1.04, "drift": 15.0}},
            {"effect": "color_drift", "params": {"speed": 0.15, "hue_range": 8.0, "sat_pulse": 0.08}},
            {"effect": "bokeh_particles", "params": {"count": 12, "speed": 0.3, "color": [255, 255, 255], "max_radius": 30, "max_alpha": 0.15}},
            {"effect": "radial_pulse", "params": {"speed": 0.5, "max_alpha": 0.12}},
        ],
        audio_reactivity=["energy"],
    ),
    "gap": EffectPreset(
        name="gap",
        effects=[
            {"effect": "ken_burns", "params": {"speed": 0.18, "max_zoom": 1.06, "drift": 25.0}},
            {"effect": "color_drift", "params": {"speed": 0.2, "hue_range": 15.0, "sat_pulse": 0.15}},
            {"effect": "bokeh_particles", "params": {"count": 12, "speed": 0.5, "color": [255, 255, 255], "max_radius": 40, "max_alpha": 0.25}},
            {"effect": "brightness_pulse", "params": {"speed": 1.5}},
            {"effect": "radial_pulse", "params": {"speed": 0.6, "max_alpha": 0.15}},
        ],
        audio_reactivity=["energy"],
    ),
}

PRESET_BY_SECTION = {
    "intro": "smooth",
    "verse": "cinematic",
    "chorus": "energetic",
    "hook": "energetic",
    "bridge": "dreamy",
    "pre_chorus": "cinematic",
    "outro": "smooth",
}


PRESET_BY_MOOD = {
    "dark_moody": {"verse": "cinematic", "chorus": "energetic"},
    "bright_poppy": {"verse": "smooth", "chorus": "energetic"},
    "warm_intimate": {"verse": "smooth", "chorus": "cinematic"},
    "cool_ethereal": {"verse": "dreamy", "chorus": "dreamy"},
    "high_energy": {"verse": "energetic", "chorus": "intense"},
}


def get_preset(name: str) -> EffectPreset:
    return PRESETS.get(name, PRESETS["minimal"])


def get_preset_for_section(section_type: str, mood_name: str = "") -> EffectPreset:
    mood_overrides = PRESET_BY_MOOD.get(mood_name, {})
    preset_name = mood_overrides.get(section_type)
    if preset_name is None:
        preset_name = PRESET_BY_SECTION.get(section_type, "minimal")
    return get_preset(preset_name)
