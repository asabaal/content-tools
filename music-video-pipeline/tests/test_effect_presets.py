import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from render.effect_presets import (
    PRESETS,
    PRESET_BY_MOOD,
    PRESET_BY_SECTION,
    EffectPreset,
    get_preset,
    get_preset_for_section,
)


class TestEffectPreset:
    def test_describe(self):
        p = EffectPreset(name="test", effects=[{"effect": "zoom_pulse", "params": {"intensity": 0.05}}], audio_reactivity=["energy"])
        desc = p.describe()
        assert "test" in desc
        assert "zoom_pulse" in desc
        assert "energy" in desc

    def test_describe_empty(self):
        p = EffectPreset(name="empty")
        desc = p.describe()
        assert "empty" in desc


class TestPresets:
    def test_all_presets_exist(self):
        assert len(PRESETS) == 8

    def test_preset_names(self):
        expected = {"cinematic", "energetic", "dreamy", "glitch", "minimal", "psychedelic", "smooth", "intense"}
        assert set(PRESETS.keys()) == expected

    def test_minimal_has_no_effects(self):
        assert PRESETS["minimal"].effects == []
        assert PRESETS["minimal"].audio_reactivity == []

    def test_cinematic_has_effects(self):
        p = PRESETS["cinematic"]
        assert len(p.effects) > 0
        assert "energy" in p.audio_reactivity

    def test_energetic_has_drums(self):
        p = PRESETS["energetic"]
        assert "drums" in p.audio_reactivity

    def test_all_effects_have_valid_names(self):
        from render.frame_effects import _FRAME_EFFECTS
        for name, preset in PRESETS.items():
            for eff in preset.effects:
                assert eff["effect"] in _FRAME_EFFECTS, f"{name}: unknown effect {eff['effect']}"


class TestGetPreset:
    def test_known_preset(self):
        p = get_preset("cinematic")
        assert p.name == "cinematic"

    def test_unknown_returns_minimal(self):
        p = get_preset("nonexistent")
        assert p.name == "minimal"


class TestGetPresetForSection:
    def test_verse_default(self):
        p = get_preset_for_section("verse")
        assert p.name == "cinematic"

    def test_chorus_default(self):
        p = get_preset_for_section("chorus")
        assert p.name == "energetic"

    def test_intro_default(self):
        p = get_preset_for_section("intro")
        assert p.name == "smooth"

    def test_unknown_section(self):
        p = get_preset_for_section("breakdown")
        assert isinstance(p, EffectPreset)

    def test_high_energy_chorus_is_intense(self):
        p = get_preset_for_section("chorus", "high_energy")
        assert p.name == "intense"

    def test_cool_ethereal_verse_is_dreamy(self):
        p = get_preset_for_section("verse", "cool_ethereal")
        assert p.name == "dreamy"

    def test_dark_moody_verse(self):
        p = get_preset_for_section("verse", "dark_moody")
        assert p.name == "cinematic"

    def test_bright_poppy_chorus(self):
        p = get_preset_for_section("chorus", "bright_poppy")
        assert p.name == "energetic"


class TestPresetBySection:
    def test_all_sections_mapped(self):
        for sec in ("intro", "verse", "chorus", "hook", "bridge", "pre_chorus", "outro"):
            assert sec in PRESET_BY_SECTION

    def test_all_mood_keys_valid(self):
        for mood, overrides in PRESET_BY_MOOD.items():
            assert isinstance(overrides, dict)
            for sec, preset_name in overrides.items():
                assert preset_name in PRESETS
