from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from scriptgen.color_presets import (
    ColorPreset,
    TextBoxConfig,
    PresetRecommendation,
    THEME_PRESETS,
    get_preset,
    list_presets,
    recommend_presets,
    preset_to_script_colors,
    style_colors_from_accent,
    _hex_to_rgb,
    _rgb_to_hsl,
    _hsl_to_rgb,
    _shift_color,
)


class TestGetPreset:
    def test_valid_name(self):
        p = get_preset("dark_teal_emerald")
        assert p.name == "dark_teal_emerald"

    def test_gold_deep_navy(self):
        p = get_preset("gold_deep_navy")
        assert p.accent_color == "#ffd700"

    def test_electric_blue_noir(self):
        p = get_preset("electric_blue_noir")
        assert p.accent_color == "#00d4ff"

    def test_unknown_raises(self):
        with pytest.raises(KeyError, match="Unknown color preset"):
            get_preset("nonexistent_preset")

    def test_all_presets_loadable(self):
        names = [
            "dark_teal_emerald", "gold_deep_navy", "electric_blue_noir",
            "sandstone_warm", "deep_purple_violet", "stark_monochrome",
            "burnt_orange_charcoal", "steel_gray_slate",
        ]
        for name in names:
            p = get_preset(name)
            assert p.name == name


class TestListPresets:
    def test_returns_list(self):
        presets = list_presets()
        assert isinstance(presets, list)
        assert len(presets) == 8

    def test_all_are_colorpreset(self):
        for p in list_presets():
            assert isinstance(p, ColorPreset)

    def test_unique_names(self):
        names = [p.name for p in list_presets()]
        assert len(names) == len(set(names))


class TestColorPresetFields:
    def test_dark_teal_has_text_box(self):
        p = get_preset("dark_teal_emerald")
        assert p.recommended_text_box is not None
        assert p.recommended_text_box.enabled is True

    def test_stark_mono_no_text_box(self):
        p = get_preset("stark_monochrome")
        assert p.recommended_text_box is None

    def test_sandstone_dark_text(self):
        p = get_preset("sandstone_warm")
        assert p.recommended_text_color != "#ffffff"

    def test_all_have_accent(self):
        for p in list_presets():
            assert p.accent_color.startswith("#")
            assert len(p.accent_color) == 7

    def test_all_have_background_base(self):
        for p in list_presets():
            assert p.background_base.startswith("#")

    def test_all_have_themes(self):
        for p in list_presets():
            assert isinstance(p.themes, tuple)
            assert len(p.themes) > 0


class TestRecommendPresets:
    def test_prophetic_theme(self):
        recs = recommend_presets("prophetic")
        assert len(recs) > 0
        assert isinstance(recs[0], PresetRecommendation)

    def test_wilderness_theme(self):
        recs = recommend_presets("wilderness")
        assert len(recs) > 0

    def test_unknown_theme(self):
        recs = recommend_presets("completely_unknown_theme")
        assert isinstance(recs, list)

    def test_partial_match(self):
        recs = recommend_presets("fire")
        assert len(recs) > 0
        assert recs[0].preset.name == "burnt_orange_charcoal"

    def test_n_limit(self):
        recs = recommend_presets("prophetic", n=1)
        assert len(recs) <= 1

    def test_warnings_populated(self):
        p = get_preset("stark_monochrome")
        assert p.recommended_text_box is None
        recs = recommend_presets("minimal")
        for r in recs:
            assert isinstance(r.warnings, list)

    def test_preset_recommendation_fields(self):
        recs = recommend_presets("prophetic")
        r = recs[0]
        assert isinstance(r.preset, ColorPreset)
        assert isinstance(r.reason, str)
        assert isinstance(r.expected_mood, str)
        assert isinstance(r.recommended_text_color, str)
        assert isinstance(r.text_box_needed, bool)


class TestPresetToScriptColors:
    def test_dark_teal_output(self):
        p = get_preset("dark_teal_emerald")
        d = preset_to_script_colors(p)
        assert "background_color" in d
        assert "gradient_colors" in d
        assert d["text_auto_contrast"] is False
        assert d["text_style"] == "neon"
        assert "text_backdrop" in d

    def test_stark_mono_output(self):
        p = get_preset("stark_monochrome")
        d = preset_to_script_colors(p)
        assert d["background_color"] == "#000000"
        assert "text_backdrop" not in d

    def test_gold_output(self):
        p = get_preset("gold_deep_navy")
        d = preset_to_script_colors(p)
        assert d["highlight_color"] == "#ffd700"
        assert d["text_style"] == "gold"

    def test_sandstone_no_text_style(self):
        p = get_preset("sandstone_warm")
        d = preset_to_script_colors(p)
        assert "text_style" not in d or d["text_style"] == ""

    def test_all_presets_produce_valid_dict(self):
        for p in list_presets():
            d = preset_to_script_colors(p)
            assert "background_color" in d
            assert "gradient_colors" in d
            assert "text_auto_contrast" in d


class TestStyleColorsFromAccent:
    def test_red_accent(self):
        colors = style_colors_from_accent("#ff0000")
        assert "neon" in colors
        assert "chrome" in colors
        assert "gold" in colors
        assert "fire" in colors
        assert "ice" in colors
        assert "hologram" in colors
        assert "graffiti" in colors
        assert "matrix" in colors
        assert "basic" in colors

    def test_blue_accent(self):
        colors = style_colors_from_accent("#0088ff")
        assert "neon" in colors
        neon = colors["neon"]
        assert "core_color" in neon
        assert "glow_color" in neon

    def test_neon_colors_are_tuples(self):
        colors = style_colors_from_accent("#ff6b35")
        for style_name, style_dict in colors.items():
            if style_name == "basic":
                continue
            for key, val in style_dict.items():
                assert isinstance(val, tuple), f"{style_name}.{key} is {type(val)}"
                assert len(val) == 3

    def test_basic_is_empty(self):
        colors = style_colors_from_accent("#ff0000")
        assert colors["basic"] == {}

    def test_chrome_has_gradient_keys(self):
        colors = style_colors_from_accent("#ff0000")
        assert "gradient_top" in colors["chrome"]
        assert "gradient_mid" in colors["chrome"]
        assert "gradient_bottom" in colors["chrome"]


class TestHexToRgb:
    def test_black(self):
        assert _hex_to_rgb("#000000") == (0, 0, 0)

    def test_white(self):
        assert _hex_to_rgb("#ffffff") == (255, 255, 255)

    def test_red(self):
        assert _hex_to_rgb("#ff0000") == (255, 0, 0)

    def test_no_hash(self):
        assert _hex_to_rgb("ff0000") == (255, 0, 0)

    def test_mixed(self):
        assert _hex_to_rgb("#1a2b3c") == (26, 43, 60)


class TestRgbToHsl:
    def test_black(self):
        h, l, s = _rgb_to_hsl(0, 0, 0)
        assert l == pytest.approx(0.0, abs=0.01)

    def test_white(self):
        h, l, s = _rgb_to_hsl(255, 255, 255)
        assert l == pytest.approx(1.0, abs=0.01)

    def test_red(self):
        h, l, s = _rgb_to_hsl(255, 0, 0)
        assert h == pytest.approx(0.0, abs=0.01)
        assert s == pytest.approx(1.0, abs=0.01)

    def test_green(self):
        h, l, s = _rgb_to_hsl(0, 255, 0)
        assert h == pytest.approx(0.333, abs=0.01)


class TestHslToRgb:
    def test_black(self):
        assert _hsl_to_rgb(0, 0, 0) == (0, 0, 0)

    def test_white(self):
        assert _hsl_to_rgb(0, 0, 1.0) == (255, 255, 255)

    def test_red(self):
        assert _hsl_to_rgb(0, 1.0, 0.5) == (255, 0, 0)

    def test_roundtrip(self):
        orig = (128, 64, 200)
        h, l, s = _rgb_to_hsl(*orig)
        result = _hsl_to_rgb(h, s, l)
        assert result[0] == pytest.approx(orig[0], abs=2)
        assert result[1] == pytest.approx(orig[1], abs=2)
        assert result[2] == pytest.approx(orig[2], abs=2)


class TestShiftColor:
    def test_no_shift(self):
        result = _shift_color("#ff0000", hue_shift=0, sat_mult=1.0, lit_shift=0)
        assert result == pytest.approx((255, 0, 0), abs=2)

    def test_hue_shift(self):
        result = _shift_color("#ff0000", hue_shift=0.333)
        assert result[1] > 100

    def test_saturation_mult(self):
        result = _shift_color("#ff0000", sat_mult=0.0)
        assert result[0] == result[1] == result[2]

    def test_lightness_shift(self):
        result = _shift_color("#800000", lit_shift=0.3)
        assert result[0] > 128


class TestThemePresets:
    def test_all_theme_values_are_valid_presets(self):
        for theme, preset_names in THEME_PRESETS.items():
            for pn in preset_names:
                p = get_preset(pn)
                assert p.name == pn

    def test_at_least_one_theme(self):
        assert len(THEME_PRESETS) > 0

    def test_theme_keys_are_lowercase(self):
        for key in THEME_PRESETS:
            assert key == key.lower()
