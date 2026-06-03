import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scriptgen.moods import MoodProfile
from scriptgen.palette import SectionColor
from scriptgen.rules import (
    SectionProfile,
    _clamp_opacity,
    _energy_level,
    _energy_preset_override,
    _load_font_pool,
    _pace_level,
    _split_into_phrases,
    assign_animation,
    assign_background,
    assign_font_family,
    assign_font_size,
    assign_reactivity,
    assign_reveal,
    assign_section_visual,
    assign_text_position,
    assign_text_style,
    assign_texture,
    assign_word_positions,
    compute_emphasis_overrides,
    resolve_section_type,
)
import scriptgen.rules as _rules_mod


def _mood(name="dark_moody", texture_default="vignette_heavy", gradient_likely=True, direction="diagonal_tl_br"):
    return MoodProfile(
        name=name,
        base_hue=240,
        saturation=(0.15, 0.35),
        lightness=(0.08, 0.18),
        texture_default=texture_default,
        direction=direction,
        gradient_likely=gradient_likely,
    )


def _profile(**kw):
    defaults = dict(
        section_type="verse",
        name="Verse 1",
        start_line=0,
        end_line=1,
        start_time=0.0,
        end_time=2.0,
        energy=0.5,
        spectral_centroid=0.5,
        pace=2.0,
        tags=[],
        word_count=6,
        resolved_type="",
    )
    defaults.update(kw)
    return SectionProfile(**defaults)


def _color():
    return SectionColor(primary="#aabbcc", companion="#ddeeff", hue=0.5, sat=0.3, lit=0.2)


class TestEnergyLevel:
    def test_low(self):
        assert _energy_level(0.1) == "low"

    def test_medium(self):
        assert _energy_level(0.4) == "medium"

    def test_high(self):
        assert _energy_level(0.8) == "high"

    def test_boundary_low(self):
        assert _energy_level(0.29) == "low"

    def test_boundary_medium(self):
        assert _energy_level(0.59) == "medium"


class TestPaceLevel:
    def test_slow(self):
        assert _pace_level(1.0) == "slow"

    def test_medium(self):
        assert _pace_level(3.0) == "medium"

    def test_fast(self):
        assert _pace_level(5.0) == "fast"

    def test_boundary_slow(self):
        assert _pace_level(1.99) == "slow"

    def test_boundary_medium(self):
        assert _pace_level(3.99) == "medium"


class TestResolveSectionType:
    def test_standard_types_pass_through(self):
        for st in ("intro", "verse", "chorus", "hook", "bridge", "pre_chorus", "outro", "interlude"):
            assert resolve_section_type(st, "", [], 0.5) == st

    def test_keyword_match_name_intro(self):
        assert resolve_section_type("unknown", "Opening", [], 0.5) == "intro"

    def test_keyword_match_name_chorus(self):
        assert resolve_section_type("unknown", "Refrain", [], 0.5) == "chorus"

    def test_keyword_match_tags(self):
        assert resolve_section_type("unknown", "", ["anthem"], 0.5) == "chorus"

    def test_keyword_match_bridge(self):
        assert resolve_section_type("unknown", "breakdown", [], 0.5) == "bridge"

    def test_keyword_match_pre_chorus(self):
        assert resolve_section_type("unknown", "build up", [], 0.5) == "pre_chorus"

    def test_keyword_match_outro(self):
        assert resolve_section_type("unknown", "coda", [], 0.5) == "outro"

    def test_energy_fallback_low(self):
        assert resolve_section_type("custom", "xyz", [], 0.2) == "intro"

    def test_energy_fallback_high(self):
        assert resolve_section_type("custom", "xyz", [], 0.7) == "chorus"

    def test_energy_fallback_mid(self):
        assert resolve_section_type("custom", "xyz", [], 0.5) == "verse"

    def test_no_keyword_no_match(self):
        assert resolve_section_type("custom", "zzzzz", [], 0.5) == "verse"


class TestAssignTexture:
    def test_chorus_grain_film(self):
        m = _mood(texture_default="none")
        result = assign_texture("chorus", 0.8, m, 0.6)
        assert result["texture_type"] == "grain_film"
        assert result["texture_opacity"] == 0.15

    def test_chorus_no_grain(self):
        m = _mood(texture_default="none")
        result = assign_texture("chorus", 0.5, m, 0.3)
        assert result["texture_type"] == "none"

    def test_low_energy_opacity_boost(self):
        m = _mood(texture_default="none")
        result = assign_texture("verse", 0.2, m, 0.5)
        assert result["texture_opacity"] > 0.2

    def test_intro_none_becomes_vignette(self):
        m = _mood(texture_default="none")
        result = assign_texture("intro", 0.3, m, 0.5)
        assert result["texture_type"] == "vignette_soft"

    def test_intro_opacity(self):
        m = _mood(texture_default="none")
        result = assign_texture("intro", 0.5, m, 0.5)
        assert result["texture_opacity"] == 0.35

    def test_bridge_texture_override(self):
        m = _mood(texture_default="paper_subtle")
        result = assign_texture("bridge", 0.5, m, 0.5)
        assert result["texture_type"] == "vignette_soft"

    def test_bridge_keep_vignette(self):
        m = _mood(texture_default="vignette_soft")
        result = assign_texture("bridge", 0.5, m, 0.5)
        assert result["texture_type"] == "vignette_soft"

    def test_bridge_opacity(self):
        m = _mood(texture_default="vignette_soft")
        result = assign_texture("bridge", 0.5, m, 0.5)
        assert result["texture_opacity"] == 0.25


class TestAssignFontSize:
    def test_big_tag(self):
        result = assign_font_size("verse", 0.5, 2.0, ["BIG"], 0.5)
        assert result >= 32

    def test_fast_pace(self):
        result = assign_font_size("verse", 0.5, 5.0, [], 0.5)
        assert result >= 32

    def test_chorus_base(self):
        result = assign_font_size("chorus", 0.5, 2.0, [], 0.5)
        assert result >= 32

    def test_bridge_base(self):
        result = assign_font_size("bridge", 0.5, 2.0, [], 0.5)
        assert result >= 32


class TestAssignReveal:
    def test_bridge(self):
        result = assign_reveal("bridge", 2.0)
        assert result["reveal_mode"] == "line-by-line"

    def test_chorus_fast(self):
        result = assign_reveal("chorus", 4.0)
        assert result["reveal_mode"] == "progressive"
        assert result["reveal_words"] == 2

    def test_chorus_slow(self):
        result = assign_reveal("chorus", 2.0)
        assert result["reveal_mode"] == "karaoke"

    def test_fast_pace_non_chorus(self):
        result = assign_reveal("verse", 5.0)
        assert result["reveal_mode"] == "progressive"
        assert result["reveal_words"] == 3

    def test_default(self):
        result = assign_reveal("verse", 2.0)
        assert result["reveal_mode"] == "progressive"
        assert result["reveal_words"] == 1


class TestAssignTextPosition:
    def test_bright_poppy_verse_odd(self):
        assert assign_text_position("verse", 1, "bright_poppy") == "top"

    def test_bright_poppy_bridge(self):
        assert assign_text_position("bridge", 0, "bright_poppy") == "bottom"

    def test_warm_intimate_top_to_center(self):
        assert assign_text_position("intro", 0, "warm_intimate") == "center"

    def test_warm_intimate_verse_even(self):
        assert assign_text_position("verse", 0, "warm_intimate") == "bottom"

    def test_warm_intimate_verse_odd(self):
        assert assign_text_position("verse", 1, "warm_intimate") == "center"

    def test_high_energy_verse_even(self):
        assert assign_text_position("verse", 0, "high_energy") == "top"

    def test_high_energy_verse_odd(self):
        assert assign_text_position("verse", 1, "high_energy") == "bottom"

    def test_high_energy_intro(self):
        assert assign_text_position("intro", 0, "high_energy") == "top"

    def test_high_energy_bridge(self):
        assert assign_text_position("bridge", 0, "high_energy") == "bottom"

    def test_cool_ethereal_verse_mod3(self):
        assert assign_text_position("verse", 2, "cool_ethereal") == "bottom"

    def test_cool_ethereal_verse_other(self):
        assert assign_text_position("verse", 0, "cool_ethereal") == "center"

    def test_bright_poppy_verse_even(self):
        assert assign_text_position("verse", 0, "bright_poppy") == "center"

    def test_default_position(self):
        assert assign_text_position("verse", 0, "dark_moody") == "center"

    def test_chorus_default(self):
        assert assign_text_position("chorus", 0, "dark_moody") == "bottom"


class TestSplitIntoPhrases:
    def test_short_words(self):
        words = [{"text": "a"}, {"text": "b"}]
        result = _split_into_phrases(words)
        assert result == [[0, 1]]

    def test_punctuation_break(self):
        words = [{"text": "hello,"}, {"text": "world"}, {"text": "test"}, {"text": "end"}]
        result = _split_into_phrases(words)
        assert len(result) == 2
        assert result[0] == [0]
        assert result[1] == [1, 2, 3]

    def test_break_word(self):
        words = [{"text": "run"}, {"text": "that"}, {"text": "test"}, {"text": "end"}]
        result = _split_into_phrases(words)
        assert len(result) == 2
        assert result[0] == [0, 1]

    def test_long_single_group_split(self):
        words = [{"text": f"word{i}"} for i in range(7)]
        result = _split_into_phrases(words)
        assert len(result) == 2
        assert len(result[0]) == 3
        assert len(result[1]) == 4

    def test_no_break_at_last_word(self):
        words = [{"text": "a"}, {"text": "b"}, {"text": "c"}, {"text": "d,"}]
        result = _split_into_phrases(words)
        assert len(result) == 1


class TestAssignWordPositions:
    def test_low_variance(self):
        p = _profile()
        assert assign_word_positions(p, "center", "dark_moody", 0.2, []) == {}

    def test_none_synced_lines(self):
        p = _profile()
        assert assign_word_positions(p, "center", "dark_moody", 0.5, None) == {}

    def test_empty_words(self):
        p = _profile(start_line=0, end_line=0)
        synced = [{"words": []}]
        result = assign_word_positions(p, "center", "dark_moody", 0.5, synced)
        assert result == {}

    def test_multi_phrase_creates_overrides(self):
        words = [
            {"text": "hello,"},
            {"text": "world"},
            {"text": "test"},
            {"text": "end"},
        ]
        p = _profile(start_line=0, end_line=0, resolved_type="verse")
        synced = [{"words": words}]
        result = assign_word_positions(p, "center", "bright_poppy", 0.5, synced)
        assert len(result) > 0

    def test_chorus_first_word_delta(self):
        words = [
            {"text": "hello,"},
            {"text": "world"},
            {"text": "test"},
            {"text": "end"},
        ]
        p = _profile(start_line=0, end_line=0, resolved_type="chorus")
        synced = [{"words": words}]
        result = assign_word_positions(p, "center", "bright_poppy", 0.5, synced)
        if "0.0" in result and "font_size_delta" in result["0.0"]:
            assert result["0.0"]["font_size_delta"] == 2

    def test_last_word_shrink(self):
        words = [
            {"text": "a"},
            {"text": "b"},
            {"text": "ok"},
        ]
        p = _profile(start_line=0, end_line=0, resolved_type="verse")
        synced = [{"words": words}]
        result = assign_word_positions(p, "center", "dark_moody", 0.6, synced)
        assert isinstance(result, dict)


class TestAssignReactivity:
    def test_low(self):
        assert assign_reactivity(0.2, "verse") == []

    def test_medium(self):
        assert assign_reactivity(0.4, "verse") == ["vocals"]

    def test_high_chorus(self):
        assert assign_reactivity(0.8, "chorus") == ["vocals", "drums", "energy"]

    def test_high_verse(self):
        assert assign_reactivity(0.8, "verse") == ["vocals", "drums"]

    def test_high_hook(self):
        assert assign_reactivity(0.8, "hook") == ["vocals", "drums", "energy"]


class TestAssignAnimation:
    def test_high_energy_chorus(self):
        result = assign_animation("chorus", "high_energy")
        assert result["animation_type"] == "elastic_in"
        assert result["animation_speed"] == 1.3

    def test_high_energy_intro(self):
        result = assign_animation("intro", "high_energy")
        assert result["animation_type"] == "bounce_in"

    def test_cool_ethereal(self):
        result = assign_animation("verse", "cool_ethereal")
        assert result["animation_type"] == "fade_in"
        assert result["animation_speed"] == 0.7

    def test_bright_poppy_chorus(self):
        result = assign_animation("chorus", "bright_poppy")
        assert result["animation_type"] == "scale_in"

    def test_default_verse(self):
        result = assign_animation("verse", "dark_moody")
        assert result["animation_type"] == "fade_in"
        assert result["animation_speed"] == 1.0


class TestLoadFontPool:
    def setup_method(self):
        _rules_mod._font_pool_cache = None

    def test_exception_handled(self, tmp_path):
        reg = tmp_path / "font_registry.json"
        reg.write_text("NOT VALID JSON{{{", encoding="utf-8")
        with patch.object(Path, "resolve", return_value=reg):
            with patch.object(Path, "exists", return_value=True):
                pool = _load_font_pool()
        for v in pool.values():
            assert v == []

    def teardown_method(self):
        _rules_mod._font_pool_cache = None


class TestAssignFontFamily:
    def setup_method(self):
        _rules_mod._font_pool_cache = None

    def test_empty_pool_returns_legacy(self):
        _rules_mod._font_pool_cache = {"sans": [], "serif": [], "display": [], "handwriting": [], "mono": []}
        result = assign_font_family("neon", "verse")
        assert isinstance(result, int)

    def test_missing_category_returns_legacy(self):
        _rules_mod._font_pool_cache = {"sans": [10], "serif": [], "display": [], "handwriting": [], "mono": []}
        result = assign_font_family("neon", "breakdown")
        assert isinstance(result, int)

    def teardown_method(self):
        _rules_mod._font_pool_cache = None


class TestEnergyPresetOverride:
    def test_low_intro(self):
        assert _energy_preset_override("intro", 0.2, "dark_moody") == "smooth"

    def test_low_non_intro(self):
        assert _energy_preset_override("verse", 0.2, "dark_moody") is None

    def test_high_chorus_high_energy(self):
        assert _energy_preset_override("chorus", 0.7, "high_energy") == "intense"

    def test_high_chorus_other_mood(self):
        assert _energy_preset_override("chorus", 0.7, "dark_moody") == "energetic"

    def test_high_verse(self):
        assert _energy_preset_override("verse", 0.7, "dark_moody") == "cinematic"

    def test_high_other_section(self):
        assert _energy_preset_override("bridge", 0.7, "dark_moody") is None

    def test_mid_cool_verse(self):
        assert _energy_preset_override("verse", 0.5, "cool_ethereal") == "dreamy"

    def test_mid_dark_verse(self):
        assert _energy_preset_override("verse", 0.5, "dark_moody") == "dreamy"

    def test_mid_verse_other_mood(self):
        assert _energy_preset_override("verse", 0.5, "bright_poppy") == "cinematic"

    def test_mid_pre_chorus(self):
        assert _energy_preset_override("pre_chorus", 0.5, "bright_poppy") == "cinematic"

    def test_mid_bridge(self):
        assert _energy_preset_override("bridge", 0.5, "dark_moody") == "dreamy"

    def test_no_match(self):
        assert _energy_preset_override("intro", 0.5, "dark_moody") is None


class TestAssignSectionVisual:
    def test_preset_audio_reactivity_fallback(self):
        p = _profile(section_type="verse", energy=0.2, pace=2.0, tags=[], resolved_type="verse")
        result = assign_section_visual(p, _color(), _mood(), "dark_moody", 0.5, 0)
        assert "bg_animation_preset" in result


class TestComputeEmphasisOverrides:
    def _visual(self, **kw):
        defaults = dict(
            font_size=50,
            reveal_mode="progressive",
            animation_speed=1.0,
        )
        defaults.update(kw)
        return defaults

    def test_title_line(self):
        p = _profile()
        result = compute_emphasis_overrides(p, self._visual(), "song", True, False)
        assert result["font_size"] == 60

    def test_big_tag(self):
        p = _profile(tags=["BIG"])
        result = compute_emphasis_overrides(p, self._visual(), "song", False, False)
        assert result["font_size"] == 62

    def test_high_energy_section_start(self):
        p = _profile(energy=0.8)
        result = compute_emphasis_overrides(p, self._visual(), "song", False, True)
        assert result["font_size"] == 54

    def test_pre_chorus_curve(self):
        p = _profile(resolved_type="pre_chorus")
        result = compute_emphasis_overrides(
            p, self._visual(), "song", False, False,
            line_index_in_section=3, num_lines_in_section=5,
        )
        assert result["font_size"] > 50

    def test_outro_descending(self):
        p = _profile(resolved_type="outro")
        result = compute_emphasis_overrides(
            p, self._visual(), "song", False, False,
            line_index_in_section=0, num_lines_in_section=4,
        )
        assert result["font_size"] < 50

    def test_chorus_midpoint(self):
        p = _profile(resolved_type="chorus")
        result = compute_emphasis_overrides(
            p, self._visual(), "song", False, False,
            line_index_in_section=1, num_lines_in_section=3,
        )
        assert result["font_size"] == 53

    def test_verse_alternating(self):
        p = _profile(resolved_type="verse")
        result = compute_emphasis_overrides(
            p, self._visual(), "song", False, False,
            line_index_in_section=1, num_lines_in_section=3,
        )
        assert result["font_size"] == 49

    def test_pre_chorus_animation(self):
        p = _profile(resolved_type="pre_chorus")
        result = compute_emphasis_overrides(
            p, self._visual(), "song", False, False,
            line_index_in_section=3, num_lines_in_section=4,
        )
        assert result.get("animation_type") == "scale_in"

    def test_verse_last_line_bottom(self):
        p = _profile(resolved_type="verse")
        result = compute_emphasis_overrides(
            p, self._visual(), "song", False, False,
            line_index_in_section=3, num_lines_in_section=4,
        )
        assert result.get("text_position") == "bottom"

    def test_zero_word_count(self):
        p = _profile(word_count=0)
        result = compute_emphasis_overrides(
            p, self._visual(reveal_mode="progressive"), "song", False, False,
            line_index_in_section=0, num_lines_in_section=1,
        )
        assert isinstance(result, dict)

    def test_progressive_many_words_left_align(self):
        p = _profile(word_count=20)
        result = compute_emphasis_overrides(
            p, self._visual(reveal_mode="progressive"), "song", False, False,
            line_index_in_section=0, num_lines_in_section=1,
        )
        assert result.get("text_align") == "left"

    def test_line_by_line_center_align(self):
        p = _profile(word_count=20)
        result = compute_emphasis_overrides(
            p, self._visual(reveal_mode="line-by-line"), "song", False, False,
            line_index_in_section=0, num_lines_in_section=1,
        )
        assert result.get("text_align") == "center"


class TestClampOpacity:
    def test_normal(self):
        assert _clamp_opacity(0.5) == 0.5

    def test_too_low(self):
        assert _clamp_opacity(0.01) == 0.05

    def test_too_high(self):
        assert _clamp_opacity(0.9) == 0.8

    def test_boundary_low(self):
        assert _clamp_opacity(0.05) == 0.05

    def test_boundary_high(self):
        assert _clamp_opacity(0.8) == 0.8


class TestAssignBackground:
    def test_intro_gradient(self):
        m = _mood(gradient_likely=True)
        result = assign_background("intro", 0.3, m, 0.5, 0)
        assert result["background_type"] == "gradient"

    def test_intro_solid(self):
        m = _mood(gradient_likely=False)
        result = assign_background("intro", 0.3, m, 0.5, 0)
        assert result["background_type"] == "solid"

    def test_outro_gradient(self):
        m = _mood(gradient_likely=True)
        result = assign_background("outro", 0.3, m, 0.5, 0)
        assert result["background_type"] == "gradient"

    def test_chorus_gradient(self):
        m = _mood(gradient_likely=False)
        result = assign_background("chorus", 0.5, m, 0.5, 0)
        assert result["background_type"] == "gradient"

    def test_hook_gradient(self):
        m = _mood(gradient_likely=False)
        result = assign_background("hook", 0.5, m, 0.5, 0)
        assert result["background_type"] == "gradient"

    def test_bridge_gradient(self):
        m = _mood(gradient_likely=False)
        result = assign_background("bridge", 0.5, m, 0.5, 1)
        assert result["background_type"] == "gradient"

    def test_bridge_direction(self):
        m = _mood(gradient_likely=True)
        result = assign_background("bridge", 0.5, m, 0.5, 0)
        from scriptgen.rules import GRADIENT_ROTATION
        expected = GRADIENT_ROTATION[(0 + 2) % len(GRADIENT_ROTATION)]
        assert result["gradient_direction"] == expected


class TestAssignWordPositionsMore:
    def test_more_phrases_than_rows(self):
        words = [
            {"text": "a,"},
            {"text": "b"},
            {"text": "c,"},
            {"text": "d"},
        ]
        p = _profile(start_line=0, end_line=0, resolved_type="verse")
        synced = [{"words": words}]
        result = assign_word_positions(p, "center", "dark_moody", 0.6, synced)
        assert len(result) > 0

    def test_last_word_shrink_with_mock(self):
        words = [
            {"text": "hello"},
            {"text": "world"},
            {"text": "ok"},
        ]
        p = _profile(start_line=0, end_line=0, resolved_type="verse")
        synced = [{"words": words}]
        with patch("scriptgen.rules._split_into_phrases", return_value=[[0], [1, 2]]):
            result = assign_word_positions(p, "center", "dark_moody", 0.6, synced)
            assert "0.2" in result


class TestAssignTextStyle:
    def test_unknown_section_returns_mood_style(self):
        result = assign_text_style("unknown_section", "dark_moody")
        assert result == "neon"

    def test_unknown_section_unknown_mood(self):
        result = assign_text_style("unknown_section", "totally_unknown_mood")
        assert result == "basic"

    def test_known_combo(self):
        result = assign_text_style("intro", "bright_poppy")
        assert result == "graffiti"
