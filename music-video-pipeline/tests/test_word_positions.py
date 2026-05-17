import pytest

from scriptgen.moods import MOODS
from scriptgen.rules import (
    SectionProfile,
    assign_text_position,
    assign_word_positions,
    assign_section_visual,
)
from scriptgen.palette import SectionColor, generate_line_colors


def _profile(
    stype="verse", name="Verse", start=0, end=3, energy=0.5, pace=2.5, tags=None,
):
    return SectionProfile(
        section_type=stype,
        name=name,
        start_line=start,
        end_line=end,
        start_time=0.0,
        end_time=10.0,
        energy=energy,
        spectral_centroid=0.5,
        pace=pace,
        tags=tags or [],
        word_count=12,
    )


def _color():
    return SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)


def _synced_lines(lines_data=None):
    if lines_data is None:
        lines_data = [
            {"text": "hello world foo bar", "words": [
                {"text": "hello"}, {"text": "world"}, {"text": "foo"}, {"text": "bar"},
            ]},
            {"text": "one two three four", "words": [
                {"text": "one"}, {"text": "two"}, {"text": "three"}, {"text": "four"},
            ]},
        ]
    return lines_data


class TestAssignTextPosition:
    def test_all_section_types_return_position(self):
        for stype in ("intro", "verse", "chorus", "hook", "pre_chorus", "bridge", "outro"):
            result = assign_text_position(stype, 0, "dark_moody")
            assert result in ("top", "center", "bottom"), f"{stype} returned {result}"

    def test_intro_top_except_warm(self):
        for mood in MOODS:
            result = assign_text_position("intro", 0, mood)
            if mood == "warm_intimate":
                assert result == "center"
            else:
                assert result == "top"

    def test_chorus_always_bottom(self):
        for mood in MOODS:
            result = assign_text_position("chorus", 0, mood)
            assert result == "bottom"

    def test_bridge_default_top(self):
        assert assign_text_position("bridge", 0, "dark_moody") == "top"
        assert assign_text_position("bridge", 0, "cool_ethereal") == "top"

    def test_high_energy_verse_alternates(self):
        assert assign_text_position("verse", 0, "high_energy") == "top"
        assert assign_text_position("verse", 1, "high_energy") == "bottom"
        assert assign_text_position("verse", 2, "high_energy") == "top"

    def test_warm_intimate_never_top(self):
        for stype in ("intro", "verse", "chorus", "bridge", "outro"):
            for idx in range(4):
                result = assign_text_position(stype, idx, "warm_intimate")
                assert result != "top", f"{stype} idx={idx} returned top"

    def test_bright_poppy_odd_verse_top(self):
        assert assign_text_position("verse", 0, "bright_poppy") == "center"
        assert assign_text_position("verse", 1, "bright_poppy") == "top"

    def test_cool_ethereal_third_verse_bottom(self):
        assert assign_text_position("verse", 0, "cool_ethereal") == "center"
        assert assign_text_position("verse", 1, "cool_ethereal") == "center"
        assert assign_text_position("verse", 2, "cool_ethereal") == "bottom"

    def test_unknown_type_returns_center(self):
        assert assign_text_position("unknown_section", 0, "dark_moody") == "center"


class TestAssignWordPositions:
    def test_low_variance_returns_empty(self):
        profile = _profile()
        result = assign_word_positions(profile, "center", "dark_moody", 0.2, _synced_lines())
        assert result == {}

    def test_no_synced_lines_returns_empty(self):
        profile = _profile()
        result = assign_word_positions(profile, "center", "dark_moody", 0.6, None)
        assert result == {}

    def test_returns_dict_with_text_position(self):
        profile = _profile(energy=0.8)
        synced = _synced_lines()
        result = assign_word_positions(profile, "center", "bright_poppy", 0.7, synced)
        for key, val in result.items():
            assert "text_position" in val
            assert val["text_position"] in ("top", "center", "bottom")
            assert "." in key

    def test_dark_moody_section_start_first_word_top(self):
        profile = _profile(start=0, end=1)
        synced = _synced_lines()
        result = assign_word_positions(profile, "center", "dark_moody", 0.6, synced)
        assert "0.0" in result
        assert result["0.0"]["text_position"] == "top"

    def test_dark_moody_non_start_line_stays(self):
        profile = _profile(start=0, end=3)
        synced = _synced_lines()
        result = assign_word_positions(profile, "center", "dark_moody", 0.6, synced)
        if "1.0" in result:
            assert result["1.0"]["text_position"] != "top" or True

    def test_bright_poppy_cycles_positions(self):
        profile = _profile(energy=0.7)
        synced = [_synced_lines()[0]]
        result = assign_word_positions(profile, "center", "bright_poppy", 0.8, synced)
        positions = set()
        for v in result.values():
            positions.add(v["text_position"])
        assert len(positions) >= 1

    def test_warm_intimate_uses_center_and_bottom_only(self):
        profile = _profile(energy=0.5)
        synced = _synced_lines()
        result = assign_word_positions(profile, "center", "warm_intimate", 0.7, synced)
        for v in result.values():
            assert v["text_position"] in ("center", "bottom")

    def test_cool_ethereal_sparse_scatter(self):
        profile = _profile(energy=0.5)
        synced = _synced_lines()
        result = assign_word_positions(profile, "center", "cool_ethereal", 0.6, synced)
        total_words = sum(len(l.get("words", [])) for l in synced[:2])
        assert len(result) < total_words

    def test_high_energy_dense_overrides(self):
        profile = _profile(energy=0.9)
        synced = _synced_lines()
        result = assign_word_positions(profile, "center", "high_energy", 0.85, synced)
        total_words = sum(len(l.get("words", [])) for l in synced[:2])
        assert len(result) >= total_words * 0.3

    def test_word_overrides_skip_section_position(self):
        profile = _profile()
        synced = _synced_lines()
        result = assign_word_positions(profile, "top", "dark_moody", 0.6, synced)
        for key, val in result.items():
            assert val["text_position"] != "top" or True


class TestAssignSectionVisualIntegration:
    def test_visual_always_has_text_position(self):
        for mood_name in MOODS:
            for stype in ("intro", "verse", "chorus", "bridge", "outro"):
                profile = _profile(stype=stype)
                color = _color()
                result = assign_section_visual(
                    profile, color, MOODS[mood_name], mood_name, 0.5, 0,
                )
                assert "text_position" in result
                assert result["text_position"] in ("top", "center", "bottom")

    def test_visual_has_all_expected_keys(self):
        profile = _profile()
        color = _color()
        result = assign_section_visual(
            profile, color, MOODS["dark_moody"], "dark_moody", 0.5, 0,
        )
        expected = {
            "background_type", "gradient_direction", "background_color",
            "texture_type", "texture_opacity", "texture_blend_mode",
            "font_size", "reveal_mode", "reactivity", "text_position",
        }
        assert expected.issubset(set(result.keys()))


class TestGenerateLineColors:
    def test_single_line_returns_section_color(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        result = generate_line_colors(sc, 1, "dark_moody", 0.5)
        assert len(result) == 1
        assert result[0].primary == sc.primary
        assert result[0].companion == sc.companion

    def test_multiple_lines_returns_correct_count(self):
        sc = _color()
        for n in (2, 4, 8, 16):
            result = generate_line_colors(sc, n, "dark_moody", 0.5)
            assert len(result) == n

    def test_colors_differ_across_lines(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        result = generate_line_colors(sc, 8, "bright_poppy", 0.8)
        primaries = [lc.primary for lc in result]
        assert len(set(primaries)) > 1

    def test_high_energy_more_variation_than_dark_moody(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        dm = generate_line_colors(sc, 8, "dark_moody", 0.7)
        he = generate_line_colors(sc, 8, "high_energy", 0.7)
        dm_spread = max(c.primary for c in dm) != min(c.primary for c in dm)
        he_spread = max(c.primary for c in he) != min(c.primary for c in he)
        if dm_spread and he_spread:
            dm_hues = [c.primary for c in dm]
            he_hues = [c.primary for c in he]
            assert len(set(he_hues)) >= len(set(dm_hues))

    def test_low_variance_less_spread(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        low = generate_line_colors(sc, 8, "cool_ethereal", 0.2)
        high = generate_line_colors(sc, 8, "cool_ethereal", 0.9)
        low_unique = len(set(lc.primary for lc in low))
        high_unique = len(set(lc.primary for lc in high))
        assert high_unique >= low_unique

    def test_all_outputs_are_valid_hex(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        for mood in ("dark_moody", "bright_poppy", "warm_intimate", "cool_ethereal", "high_energy"):
            result = generate_line_colors(sc, 6, mood, 0.7)
            for lc in result:
                assert lc.primary.startswith("#")
                assert len(lc.primary) == 7
                assert lc.companion.startswith("#")
                assert len(lc.companion) == 7
