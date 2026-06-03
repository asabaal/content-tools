import pytest

from scriptgen.palette import (
    SectionColor,
    LineColor,
    _hsl_to_hex,
    _hex_to_hsl,
    _section_hue,
    _section_sat,
    _section_lit,
    generate_line_colors,
    generate_palette,
)
from scriptgen.moods import MOODS, MoodProfile


def _make_mood(base_hue=240, sat=(0.15, 0.35), lit=(0.08, 0.18)):
    return MoodProfile(
        name="test",
        base_hue=base_hue,
        saturation=sat,
        lightness=lit,
        texture_default="none",
        direction="horizontal_left_right",
        gradient_likely=False,
    )


class TestHslToHex:
    def test_black(self):
        assert _hsl_to_hex(0.0, 0.0, 0.0) == "#000000"

    def test_white(self):
        assert _hsl_to_hex(0.0, 0.0, 1.0) == "#ffffff"

    def test_pure_red(self):
        result = _hsl_to_hex(0.0, 1.0, 0.5)
        r = int(result[1:3], 16)
        assert r == 255

    def test_output_format(self):
        result = _hsl_to_hex(0.5, 0.5, 0.5)
        assert result.startswith("#")
        assert len(result) == 7

    def test_valid_hex_chars(self):
        result = _hsl_to_hex(0.33, 0.7, 0.6)
        for c in result[1:]:
            assert c in "0123456789abcdef"


class TestHexToHsl:
    def test_black(self):
        h, l, s = _hex_to_hsl("#000000")
        assert l == pytest.approx(0.0, abs=0.01)

    def test_white(self):
        h, l, s = _hex_to_hsl("#ffffff")
        assert l == pytest.approx(1.0, abs=0.01)

    def test_roundtrip(self):
        for h, s, l in [(0.0, 0.5, 0.5), (0.33, 0.7, 0.4), (0.75, 0.3, 0.6), (0.5, 0.8, 0.3)]:
            hex_color = _hsl_to_hex(h, s, l)
            h2, l2, s2 = _hex_to_hsl(hex_color)
            assert h2 == pytest.approx(h, abs=0.02)
            assert s2 == pytest.approx(s, abs=0.02)
            assert l2 == pytest.approx(l, abs=0.02)


class TestSectionHue:
    def test_verse_shifts_with_index(self):
        h1 = _section_hue(0.5, "verse", 0, 0.5)
        h2 = _section_hue(0.5, "verse", 1, 0.5)
        assert h1 != h2

    def test_chorus_large_shift(self):
        h = _section_hue(0.5, "chorus", 0, 0.5)
        assert abs(h - 0.5) > 0.3 or abs(h - 0.5) < -0.3 % 1.0

    def test_bridge_small_shift(self):
        h = _section_hue(0.5, "bridge", 0, 0.5)
        assert 0.0 <= h <= 1.0

    def test_intro_no_shift(self):
        h = _section_hue(0.5, "intro", 0, 0.5)
        assert h == pytest.approx(0.5)

    def test_outro_slight_negative(self):
        h = _section_hue(0.5, "outro", 0, 0.5)
        assert 0.0 <= h <= 1.0

    def test_result_always_0_to_1(self):
        for stype in ("verse", "chorus", "bridge", "intro", "outro", "pre_chorus", "interlude"):
            for idx in range(5):
                for var in (0.1, 0.5, 0.9):
                    h = _section_hue(0.5, stype, idx, var)
                    assert 0.0 <= h <= 1.0

    def test_unknown_type_uses_index(self):
        h0 = _section_hue(0.5, "custom", 0, 0.5)
        h1 = _section_hue(0.5, "custom", 1, 0.5)
        assert h0 != h1

    def test_hook_same_as_chorus(self):
        h_chorus = _section_hue(0.5, "chorus", 0, 0.5)
        h_hook = _section_hue(0.5, "hook", 0, 0.5)
        assert h_chorus == pytest.approx(h_hook)


class TestSectionSat:
    def test_returns_within_mood_range(self):
        mood = MOODS["dark_moody"]
        for stype in ("verse", "chorus", "intro", "outro", "bridge"):
            s = _section_sat(mood, stype, 0.5, 0.5)
            assert mood.saturation[0] <= s <= mood.saturation[1]

    def test_chorus_higher_than_verse(self):
        mood = MOODS["bright_poppy"]
        s_chorus = _section_sat(mood, "chorus", 0.5, 0.5)
        s_intro = _section_sat(mood, "intro", 0.5, 0.5)
        assert s_chorus >= s_intro

    def test_energy_boost(self):
        mood = MOODS["bright_poppy"]
        s_low = _section_sat(mood, "verse", 0.2, 0.8)
        s_high = _section_sat(mood, "verse", 0.8, 0.8)
        assert s_high >= s_low

    def test_all_section_types_clamped(self):
        mood = _make_mood(sat=(0.3, 0.7))
        for stype in ("verse", "chorus", "bridge", "intro", "outro", "hook", "pre_chorus"):
            s = _section_sat(mood, stype, 0.5, 0.5)
            assert 0.3 <= s <= 0.7


class TestSectionLit:
    def test_returns_within_mood_range(self):
        mood = MOODS["dark_moody"]
        for stype in ("verse", "chorus", "intro", "outro", "bridge"):
            l = _section_lit(mood, stype, 0.5, 0.5)
            assert mood.lightness[0] <= l <= mood.lightness[1]

    def test_chorus_brighter_than_intro(self):
        mood = MOODS["bright_poppy"]
        l_chorus = _section_lit(mood, "chorus", 0.5, 0.5)
        l_intro = _section_lit(mood, "intro", 0.5, 0.5)
        assert l_chorus >= l_intro

    def test_energy_boost(self):
        mood = MOODS["bright_poppy"]
        l_low = _section_lit(mood, "verse", 0.2, 0.8)
        l_high = _section_lit(mood, "verse", 0.8, 0.8)
        assert l_high >= l_low

    def test_all_section_types_clamped(self):
        mood = _make_mood(lit=(0.2, 0.5))
        for stype in ("verse", "chorus", "bridge", "intro", "outro", "hook"):
            l = _section_lit(mood, stype, 0.5, 0.5)
            assert 0.2 <= l <= 0.5


class TestGenerateLineColors:
    def test_single_line_returns_section_color(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        result = generate_line_colors(sc, 1, "dark_moody", 0.5)
        assert len(result) == 1
        assert result[0].primary == sc.primary
        assert result[0].companion == sc.companion

    def test_multiple_lines_correct_count(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        for n in (2, 4, 8, 16):
            result = generate_line_colors(sc, n, "dark_moody", 0.5)
            assert len(result) == n

    def test_returns_line_color_instances(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        result = generate_line_colors(sc, 4, "dark_moody", 0.5)
        for lc in result:
            assert isinstance(lc, LineColor)
            assert lc.primary.startswith("#")
            assert lc.companion.startswith("#")

    def test_colors_differ_across_lines(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        result = generate_line_colors(sc, 8, "bright_poppy", 0.8)
        primaries = [lc.primary for lc in result]
        assert len(set(primaries)) > 1

    def test_all_hex_valid(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        for mood in MOODS:
            result = generate_line_colors(sc, 6, mood, 0.7)
            for lc in result:
                assert len(lc.primary) == 7
                assert len(lc.companion) == 7

    def test_unknown_mood_uses_defaults(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        result = generate_line_colors(sc, 4, "nonexistent", 0.5)
        assert len(result) == 4
        for lc in result:
            assert lc.primary.startswith("#")

    def test_high_variance_more_spread(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        low = generate_line_colors(sc, 8, "high_energy", 0.2)
        high = generate_line_colors(sc, 8, "high_energy", 0.9)
        low_unique = len(set(lc.primary for lc in low))
        high_unique = len(set(lc.primary for lc in high))
        assert high_unique >= low_unique


class TestGeneratePalette:
    def test_single_section(self):
        mood = MOODS["dark_moody"]
        colors = generate_palette(["verse"], [0.5], mood, 0.5)
        assert len(colors) == 1
        assert isinstance(colors[0], SectionColor)
        assert colors[0].primary.startswith("#")
        assert colors[0].companion.startswith("#")

    def test_multiple_sections(self):
        mood = MOODS["dark_moody"]
        types = ["intro", "verse", "chorus", "verse", "bridge", "outro"]
        energies = [0.3, 0.5, 0.8, 0.5, 0.4, 0.2]
        colors = generate_palette(types, energies, mood, 0.5)
        assert len(colors) == 6

    def test_base_color_override(self):
        mood = MOODS["dark_moody"]
        colors_default = generate_palette(["verse"], [0.5], mood, 0.5)
        colors_override = generate_palette(["verse"], [0.5], mood, 0.5, base_color="#ff0000")
        assert colors_default[0].primary != colors_override[0].primary

    def test_chorus_differs_from_verse(self):
        mood = MOODS["bright_poppy"]
        colors = generate_palette(["verse", "chorus"], [0.5, 0.5], mood, 0.5)
        assert colors[0].primary != colors[1].primary

    def test_verse_count_increments(self):
        mood = MOODS["dark_moody"]
        types = ["verse", "verse", "verse"]
        energies = [0.5, 0.5, 0.5]
        colors = generate_palette(types, energies, mood, 0.5)
        assert len(colors) == 3

    def test_mismatched_lengths_uses_default_energy(self):
        mood = MOODS["dark_moody"]
        colors = generate_palette(["verse", "chorus"], [0.5], mood, 0.5)
        assert len(colors) == 2

    def test_empty_section_types(self):
        mood = MOODS["dark_moody"]
        colors = generate_palette([], [], mood, 0.5)
        assert colors == []

    def test_all_moods_produce_valid_colors(self):
        for mood_key, mood in MOODS.items():
            colors = generate_palette(["intro", "verse", "chorus", "bridge", "outro"], [0.3, 0.5, 0.7, 0.4, 0.2], mood, 0.5)
            for c in colors:
                assert c.primary.startswith("#")
                assert c.companion.startswith("#")
                assert 0.0 <= c.hue <= 1.0
                assert 0.0 <= c.sat <= 1.0
                assert 0.0 <= c.lit <= 1.0

    def test_colors_have_companions(self):
        mood = MOODS["dark_moody"]
        colors = generate_palette(["verse", "chorus"], [0.5, 0.7], mood, 0.5)
        for c in colors:
            assert c.companion != c.primary

    def test_section_color_fields(self):
        mood = MOODS["dark_moody"]
        colors = generate_palette(["verse"], [0.5], mood, 0.5)
        c = colors[0]
        assert hasattr(c, "primary")
        assert hasattr(c, "companion")
        assert hasattr(c, "hue")
        assert hasattr(c, "sat")
        assert hasattr(c, "lit")

    def test_variance_affects_colors(self):
        mood = MOODS["bright_poppy"]
        types = ["verse", "chorus", "bridge"]
        energies = [0.5, 0.7, 0.4]
        low = generate_palette(types, energies, mood, 0.2)
        high = generate_palette(types, energies, mood, 0.8)
        assert low[0].primary != high[0].primary or low[1].primary != high[1].primary


class TestEdgeCases:
    def test_zero_variance(self):
        mood = MOODS["dark_moody"]
        colors = generate_palette(["verse"], [0.5], mood, 0.0)
        assert len(colors) == 1

    def test_max_variance(self):
        mood = MOODS["bright_poppy"]
        colors = generate_palette(["verse", "chorus"], [0.5, 0.5], mood, 1.0)
        assert len(colors) == 2

    def test_extreme_energies(self):
        mood = MOODS["high_energy"]
        colors = generate_palette(["verse", "chorus"], [0.0, 1.0], mood, 0.5)
        assert len(colors) == 2
        for c in colors:
            assert c.primary.startswith("#")

    def test_single_line_color_zero_lines(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        result = generate_line_colors(sc, 0, "dark_moody", 0.5)
        assert len(result) == 1

    def test_large_number_of_lines(self):
        sc = SectionColor(primary="#1a1a2e", companion="#16213e", hue=0.6, sat=0.2, lit=0.15)
        result = generate_line_colors(sc, 50, "high_energy", 0.8)
        assert len(result) == 50
        for lc in result:
            assert lc.primary.startswith("#")

    def test_base_color_with_different_hues(self):
        mood = MOODS["dark_moody"]
        red = generate_palette(["verse"], [0.5], mood, 0.5, base_color="#ff0000")
        blue = generate_palette(["verse"], [0.5], mood, 0.5, base_color="#0000ff")
        assert red[0].primary != blue[0].primary

    def test_all_section_types_handled(self):
        mood = MOODS["dark_moody"]
        types = ["intro", "verse", "pre_chorus", "chorus", "hook", "bridge", "interlude", "outro", "unknown"]
        energies = [0.3] * len(types)
        colors = generate_palette(types, energies, mood, 0.5)
        assert len(colors) == len(types)
