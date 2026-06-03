import json

import pytest

from scriptgen.generator import ScriptGenerator, GenerateResult, generate_script
from scriptgen.moods import MOODS, DEFAULT_MOOD, MoodProfile


def _analysis(rms_energy=None, spectral_centroids=None, sample_rate=48000, duration=30.0, hop_length=512):
    if rms_energy is None:
        rms_energy = [0.5] * 100
    if spectral_centroids is None:
        spectral_centroids = [0.5] * 100
    return {
        "duration": duration,
        "sample_rate": sample_rate,
        "hop_length": hop_length,
        "rms_energy": rms_energy,
        "spectral_centroids": spectral_centroids,
    }


def _lyrics_raw():
    return {"lines": [
        {"index": 0, "text": "First line intro", "section": {"section_type": "intro", "raw_marker": "Intro"}},
        {"index": 1, "text": "Second line intro", "section": {"section_type": "intro", "raw_marker": "Intro"}},
        {"index": 2, "text": "Verse line one", "section": {"section_type": "verse", "raw_marker": "Verse 1"}},
        {"index": 3, "text": "Verse line two", "section": {"section_type": "verse", "raw_marker": "Verse 1"}},
        {"index": 4, "text": "Chorus big line", "section": {"section_type": "chorus", "raw_marker": "Chorus"}},
        {"index": 5, "text": "Chorus second line", "section": {"section_type": "chorus", "raw_marker": "Chorus"}},
    ]}


def _lyrics_synced():
    return {
        "lines": [
            {
                "index": 0, "text": "First line intro", "start": 0.0, "end": 2.0,
                "words": [{"text": "First", "start": 0.0, "end": 0.5}, {"text": "line", "start": 0.5, "end": 1.0}, {"text": "intro", "start": 1.0, "end": 2.0}],
            },
            {
                "index": 1, "text": "Second line intro", "start": 2.0, "end": 4.0,
                "words": [{"text": "Second", "start": 2.0, "end": 2.5}, {"text": "line", "start": 2.5, "end": 3.0}, {"text": "intro", "start": 3.0, "end": 4.0}],
            },
            {
                "index": 2, "text": "Verse line one", "start": 4.5, "end": 7.0,
                "words": [{"text": "Verse", "start": 4.5, "end": 5.0}, {"text": "line", "start": 5.0, "end": 5.5}, {"text": "one", "start": 5.5, "end": 7.0}],
            },
            {
                "index": 3, "text": "Verse line two", "start": 7.0, "end": 9.5,
                "words": [{"text": "Verse", "start": 7.0, "end": 7.5}, {"text": "line", "start": 7.5, "end": 8.0}, {"text": "two", "start": 8.0, "end": 9.5}],
            },
            {
                "index": 4, "text": "Chorus big line", "start": 10.0, "end": 13.0,
                "words": [{"text": "Chorus", "start": 10.0, "end": 10.5}, {"text": "big", "start": 10.5, "end": 11.0}, {"text": "line", "start": 11.0, "end": 13.0}],
            },
            {
                "index": 5, "text": "Chorus second line", "start": 13.0, "end": 16.0,
                "words": [{"text": "Chorus", "start": 13.0, "end": 13.5}, {"text": "second", "start": 13.5, "end": 14.0}, {"text": "line", "start": 14.0, "end": 16.0}],
            },
        ]
    }


def _setup_project(tmp_path, analysis=None, lyrics_raw=None, lyrics_synced=None, use_data_dir=False, song_name=""):
    if use_data_dir:
        base = tmp_path / "data"
        base.mkdir()
    else:
        base = tmp_path

    if analysis is not None:
        (base / "analysis.json").write_text(json.dumps(analysis), encoding="utf-8")
    if lyrics_raw is not None:
        (base / "lyrics_raw.json").write_text(json.dumps(lyrics_raw), encoding="utf-8")
    if lyrics_synced is not None:
        (base / "lyrics_synced.json").write_text(json.dumps(lyrics_synced), encoding="utf-8")
    if song_name:
        (base / "mvp_project.json").write_text(json.dumps({"name": song_name}), encoding="utf-8")

    return tmp_path


class TestScriptGeneratorInit:
    def test_loads_from_project_dir(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        assert gen.analysis["duration"] == 30.0
        assert len(gen.lyrics_raw) > 0
        assert len(gen.lyrics_synced) > 0

    def test_loads_from_data_subdir(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced(), use_data_dir=True)
        gen = ScriptGenerator(tmp_path)
        assert gen.analysis["duration"] == 30.0
        assert gen.data_dir == tmp_path / "data"

    def test_missing_files_silent(self, tmp_path):
        gen = ScriptGenerator(tmp_path)
        assert gen.analysis == {}
        assert gen.lyrics_raw == {}
        assert gen.lyrics_synced == {}
        assert gen.song_name == ""

    def test_song_name_from_project_file(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced(), song_name="My Song")
        gen = ScriptGenerator(tmp_path)
        assert gen.song_name == "My Song"

    def test_partial_files_ok(self, tmp_path):
        _setup_project(tmp_path, lyrics_raw=_lyrics_raw())
        gen = ScriptGenerator(tmp_path)
        assert gen.analysis == {}
        assert len(gen.lyrics_raw) > 0


class TestLoadData:
    def test_load_analysis(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(rms_energy=[0.3, 0.7], spectral_centroids=[0.4, 0.6]))
        gen = ScriptGenerator(tmp_path)
        assert gen.analysis["rms_energy"] == [0.3, 0.7]

    def test_load_lyrics_raw(self, tmp_path):
        raw = [{"index": 0, "text": "Hello"}]
        _setup_project(tmp_path, lyrics_raw=raw)
        gen = ScriptGenerator(tmp_path)
        assert gen.lyrics_raw == raw

    def test_load_lyrics_synced(self, tmp_path):
        synced = _lyrics_synced()
        _setup_project(tmp_path, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        assert gen.lyrics_synced["lines"][0]["text"] == "First line intro"


class TestBuildSections:
    def test_builds_multiple_sections(self, tmp_path):
        _setup_project(tmp_path, lyrics_raw=_lyrics_raw())
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        assert len(sections) == 3
        assert sections[0]["type"] == "intro"
        assert sections[1]["type"] == "verse"
        assert sections[2]["type"] == "chorus"

    def test_section_line_ranges(self, tmp_path):
        _setup_project(tmp_path, lyrics_raw=_lyrics_raw())
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        assert sections[0]["start_line"] == 0
        assert sections[0]["end_line"] == 1
        assert sections[1]["start_line"] == 2
        assert sections[1]["end_line"] == 3
        assert sections[2]["start_line"] == 4
        assert sections[2]["end_line"] == 5

    def test_section_names(self, tmp_path):
        _setup_project(tmp_path, lyrics_raw=_lyrics_raw())
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        assert sections[0]["name"] == "Intro"
        assert sections[1]["name"] == "Verse 1"
        assert sections[2]["name"] == "Chorus"

    def test_empty_raw_returns_empty(self, tmp_path):
        _setup_project(tmp_path, lyrics_raw={"lines": []})
        gen = ScriptGenerator(tmp_path)
        assert gen._build_sections() == []

    def test_no_raw_returns_empty(self, tmp_path):
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        assert gen._build_sections() == []

    def test_single_section(self, tmp_path):
        raw = {"lines": [
            {"index": 0, "text": "Line one", "section": {"section_type": "verse", "raw_marker": "Verse"}},
            {"index": 1, "text": "Line two", "section": {"section_type": "verse", "raw_marker": "Verse"}},
        ]}
        _setup_project(tmp_path, lyrics_raw=raw)
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        assert len(sections) == 1
        assert sections[0]["type"] == "verse"
        assert sections[0]["start_line"] == 0
        assert sections[0]["end_line"] == 1

    def test_section_without_section_key(self, tmp_path):
        raw = {"lines": [
            {"index": 0, "text": "A line"},
            {"index": 1, "text": "Another line"},
        ]}
        _setup_project(tmp_path, lyrics_raw=raw)
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        assert len(sections) == 1
        assert sections[0]["type"] == "verse"

    def test_tags_carried_through(self, tmp_path):
        raw = {"lines": [
            {"index": 0, "text": "Line", "section": {"section_type": "chorus", "raw_marker": "Chorus", "tags": ["BIG"]}},
        ]}
        _setup_project(tmp_path, lyrics_raw=raw)
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        assert sections[0]["tags"] == ["BIG"]


class TestBuildProfiles:
    def test_builds_profiles_from_sections(self, tmp_path):
        _setup_project(tmp_path, lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced(), analysis=_analysis())
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        profiles = gen._build_profiles(sections)
        assert len(profiles) == 3
        assert profiles[0].section_type == "intro"
        assert profiles[1].section_type == "verse"
        assert profiles[2].section_type == "chorus"

    def test_profile_timing(self, tmp_path):
        _setup_project(tmp_path, lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced(), analysis=_analysis())
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        profiles = gen._build_profiles(sections)
        assert profiles[0].start_time >= 0.0
        assert profiles[0].end_time > profiles[0].start_time
        assert profiles[1].start_time > profiles[0].end_time

    def test_profile_pace(self, tmp_path):
        _setup_project(tmp_path, lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced(), analysis=_analysis())
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        profiles = gen._build_profiles(sections)
        for p in profiles:
            assert p.pace > 0

    def test_profile_word_count(self, tmp_path):
        _setup_project(tmp_path, lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced(), analysis=_analysis())
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        profiles = gen._build_profiles(sections)
        assert profiles[0].word_count == 6
        assert profiles[1].word_count == 6

    def test_profiles_with_no_synced(self, tmp_path):
        _setup_project(tmp_path, lyrics_raw=_lyrics_raw(), analysis=_analysis())
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        profiles = gen._build_profiles(sections)
        assert len(profiles) == 3
        for p in profiles:
            assert p.start_time == 0.0
            assert p.end_time == 0.0
            assert p.word_count == 0

    def test_resolved_type_set(self, tmp_path):
        _setup_project(tmp_path, lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced(), analysis=_analysis())
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        profiles = gen._build_profiles(sections)
        for p in profiles:
            assert p.resolved_type != ""


class TestSectionEnergy:
    def test_with_rms_data(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(rms_energy=[0.2] * 300))
        gen = ScriptGenerator(tmp_path)
        energy = gen._section_energy(0.0, 1.0)
        assert 0.0 <= energy <= 1.0

    def test_without_rms_returns_default(self, tmp_path):
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        assert gen._section_energy(0.0, 1.0) == 0.5

    def test_empty_segment_returns_default(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(rms_energy=[0.3], sample_rate=48000))
        gen = ScriptGenerator(tmp_path)
        energy = gen._section_energy(1000.0, 2000.0)
        assert energy == 0.5

    def test_high_energy_segment(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(rms_energy=[0.9] * 300))
        gen = ScriptGenerator(tmp_path)
        energy = gen._section_energy(0.0, 1.0)
        assert energy > 0.7

    def test_low_energy_segment(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(rms_energy=[0.1] * 300))
        gen = ScriptGenerator(tmp_path)
        energy = gen._section_energy(0.0, 1.0)
        assert energy < 0.3


class TestSectionCentroid:
    def test_with_centroid_data(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(spectral_centroids=[0.4] * 300))
        gen = ScriptGenerator(tmp_path)
        centroid = gen._section_centroid(0.0, 1.0)
        assert 0.0 <= centroid <= 1.0

    def test_without_centroids_returns_default(self, tmp_path):
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        assert gen._section_centroid(0.0, 1.0) == 0.5

    def test_empty_segment_returns_default(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(spectral_centroids=[0.5]))
        gen = ScriptGenerator(tmp_path)
        assert gen._section_centroid(1000.0, 2000.0) == 0.5


class TestResolveVariance:
    @pytest.fixture
    def gen(self, tmp_path):
        _setup_project(tmp_path)
        return ScriptGenerator(tmp_path)

    def test_low_mode(self, gen):
        assert gen._resolve_variance("low", [0.5, 0.6]) == pytest.approx(0.25)

    def test_medium_mode(self, gen):
        assert gen._resolve_variance("medium", [0.5, 0.6]) == pytest.approx(0.55)

    def test_high_mode(self, gen):
        assert gen._resolve_variance("high", [0.5, 0.6]) == pytest.approx(0.85)

    def test_auto_with_uniform_energies(self, gen):
        result = gen._resolve_variance("auto", [0.5, 0.5, 0.5])
        assert 0.15 <= result <= 0.9

    def test_auto_with_diverse_energies(self, gen):
        result = gen._resolve_variance("auto", [0.1, 0.5, 0.9])
        assert result > 0.25

    def test_auto_with_empty_energies(self, gen):
        assert gen._resolve_variance("auto", []) == 0.5

    def test_auto_with_zero_energies(self, gen):
        assert gen._resolve_variance("auto", [0.0, 0.0]) == 0.5

    def test_auto_clamps_result(self, gen):
        result = gen._resolve_variance("auto", [0.001, 0.999])
        assert 0.15 <= result <= 0.9


class TestBuildDefaults:
    def test_uses_first_color(self, tmp_path):
        from scriptgen.palette import SectionColor
        from scriptgen.moods import MoodProfile
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        mood = MOODS["dark_moody"]
        colors = [SectionColor(primary="#aabbcc", companion="#ddeeff", hue=0.5, sat=0.3, lit=0.2)]
        defaults = gen._build_defaults(mood, [], colors)
        assert defaults["background_color"] == "#aabbcc"
        assert defaults["gradient_colors"] == ["#aabbcc", "#ddeeff"]

    def test_no_colors_uses_fallback(self, tmp_path):
        from scriptgen.moods import MoodProfile
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        mood = MOODS["dark_moody"]
        defaults = gen._build_defaults(mood, [], [])
        assert defaults["background_color"] == "#1a1a2e"
        assert defaults["gradient_colors"] == ["#1a1a2e", "#16213e"]

    def test_gradient_setting_from_mood(self, tmp_path):
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        defaults_dm = gen._build_defaults(MOODS["dark_moody"], [], [])
        defaults_bp = gen._build_defaults(MOODS["bright_poppy"], [], [])
        assert defaults_dm["background_type"] == "gradient"
        assert defaults_bp["background_type"] == "solid"

    def test_has_required_keys(self, tmp_path):
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        defaults = gen._build_defaults(MOODS["dark_moody"], [], [])
        expected_keys = {
            "background_type", "background_color", "gradient_colors", "gradient_direction",
            "texture_type", "texture_opacity", "texture_blend_mode",
            "text_auto_contrast", "font_size", "animation_type", "animation_speed",
            "reveal_mode", "reveal_words", "reveal_slide", "reactivity", "text_align",
        }
        assert expected_keys.issubset(set(defaults.keys()))

    def test_direction_from_mood(self, tmp_path):
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        defaults = gen._build_defaults(MOODS["dark_moody"], [], [])
        assert defaults["gradient_direction"] == MOODS["dark_moody"].direction


class TestBuildCaptionStyle:
    def test_returns_required_keys(self, tmp_path):
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        cap = gen._build_caption_style(MOODS["dark_moody"], 0.5)
        assert "font_family" in cap
        assert "highlight_color" in cap
        assert "text_position" in cap
        assert "letter_spacing" in cap

    def test_warm_hue_uses_red_highlight(self, tmp_path):
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        cap = gen._build_caption_style(MOODS["warm_intimate"], 0.5)
        assert cap["highlight_color"] == "#ff6b6b"

    def test_bright_poppy_uses_red_highlight(self, tmp_path):
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        cap = gen._build_caption_style(MOODS["bright_poppy"], 0.5)
        assert cap["highlight_color"] == "#ff6b6b"

    def test_cool_hue_uses_cyan_highlight(self, tmp_path):
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        cap = gen._build_caption_style(MOODS["cool_ethereal"], 0.5)
        assert cap["highlight_color"] == "#4cc9f0"

    def test_red_hue_uses_red_highlight(self, tmp_path):
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        cap = gen._build_caption_style(MOODS["high_energy"], 0.5)
        assert cap["highlight_color"] == "#ff6b6b"

    def test_dark_moody_uses_cyan_highlight(self, tmp_path):
        _setup_project(tmp_path)
        gen = ScriptGenerator(tmp_path)
        cap = gen._build_caption_style(MOODS["dark_moody"], 0.5)
        assert cap["highlight_color"] == "#4cc9f0"


class TestIsTitleLine:
    def test_title_line_detected(self, tmp_path):
        _setup_project(tmp_path, lyrics_synced=_lyrics_synced(), song_name="Chorus big line")
        gen = ScriptGenerator(tmp_path)
        assert gen._is_title_line(4) is True

    def test_non_title_line(self, tmp_path):
        _setup_project(tmp_path, lyrics_synced=_lyrics_synced(), song_name="My Song Title")
        gen = ScriptGenerator(tmp_path)
        assert gen._is_title_line(0) is False

    def test_no_song_name(self, tmp_path):
        _setup_project(tmp_path, lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        assert gen._is_title_line(0) is False

    def test_line_index_out_of_range(self, tmp_path):
        _setup_project(tmp_path, lyrics_synced=_lyrics_synced(), song_name="Test")
        gen = ScriptGenerator(tmp_path)
        assert gen._is_title_line(100) is False

    def test_case_insensitive(self, tmp_path):
        synced = {"lines": [{"index": 0, "text": "MY AWESOME SONG", "start": 0, "end": 1, "words": []}]}
        _setup_project(tmp_path, lyrics_synced=synced, song_name="my awesome song")
        gen = ScriptGenerator(tmp_path)
        assert gen._is_title_line(0) is True


class TestApplyGapRevealOverrides:
    def test_no_override_when_lines_continuous(self, tmp_path):
        synced = _lyrics_synced()
        _setup_project(tmp_path, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        script = {
            "sections": [{
                "lines": [0, 1],
                "visual": {"reveal_mode": "karaoke"},
                "lines_overrides": {},
            }]
        }
        gen._apply_gap_reveal_overrides(script)
        lo = script["sections"][0]["lines_overrides"]
        assert all(lo[k].get("reveal_mode") != "progressive" for k in lo)

    def test_override_when_large_gap(self, tmp_path):
        synced = {
            "lines": [
                {"index": 0, "text": "Line 1", "start": 0.0, "end": 1.0, "words": [{"text": "Line", "start": 0.0, "end": 0.5}, {"text": "1", "start": 0.5, "end": 1.0}]},
                {"index": 1, "text": "Line 2", "start": 3.0, "end": 4.0, "words": [{"text": "Line", "start": 3.0, "end": 3.5}, {"text": "2", "start": 3.5, "end": 4.0}]},
            ]
        }
        _setup_project(tmp_path, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        script = {
            "sections": [{
                "lines": [0, 1],
                "visual": {"reveal_mode": "karaoke"},
                "lines_overrides": {},
            }]
        }
        gen._apply_gap_reveal_overrides(script)
        assert script["sections"][0]["lines_overrides"]["1"]["reveal_mode"] == "progressive"
        assert script["sections"][0]["lines_overrides"]["1"]["reveal_words"] == 1

    def test_override_when_first_word_delayed(self, tmp_path):
        synced = {
            "lines": [
                {"index": 0, "text": "Line 1", "start": 0.0, "end": 1.0, "words": [{"text": "Line", "start": 0.0, "end": 0.5}]},
                {"index": 1, "text": "Line 2", "start": 1.5, "end": 3.0, "words": [{"text": "Line", "start": 2.5, "end": 3.0}]},
            ]
        }
        _setup_project(tmp_path, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        script = {
            "sections": [{
                "lines": [0, 1],
                "visual": {"reveal_mode": "karaoke"},
                "lines_overrides": {},
            }]
        }
        gen._apply_gap_reveal_overrides(script)
        assert script["sections"][0]["lines_overrides"]["1"]["reveal_mode"] == "progressive"

    def test_no_change_if_already_progressive(self, tmp_path):
        synced = {
            "lines": [
                {"index": 0, "text": "Line 1", "start": 0.0, "end": 1.0, "words": [{"text": "L", "start": 0.0, "end": 0.5}]},
                {"index": 1, "text": "Line 2", "start": 3.0, "end": 4.0, "words": [{"text": "L", "start": 3.0, "end": 3.5}]},
            ]
        }
        _setup_project(tmp_path, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        script = {
            "sections": [{
                "lines": [0, 1],
                "visual": {"reveal_mode": "progressive"},
                "lines_overrides": {},
            }]
        }
        gen._apply_gap_reveal_overrides(script)
        assert "1" not in script["sections"][0]["lines_overrides"]

    def test_fewer_than_two_synced_lines_noop(self, tmp_path):
        synced = {"lines": [{"index": 0, "text": "Only one", "start": 0, "end": 1, "words": []}]}
        _setup_project(tmp_path, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        script = {"sections": [{"lines": [0], "visual": {"reveal_mode": "karaoke"}, "lines_overrides": {}}]}
        gen._apply_gap_reveal_overrides(script)
        assert script["sections"][0]["lines_overrides"] == {}

    def test_line_idx_out_of_range_noop(self, tmp_path):
        synced = _lyrics_synced()
        _setup_project(tmp_path, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        script = {
            "sections": [{
                "lines": [0, 99],
                "visual": {"reveal_mode": "karaoke"},
                "lines_overrides": {},
            }]
        }
        gen._apply_gap_reveal_overrides(script)
        assert "99" not in script["sections"][0]["lines_overrides"]


class TestGenerate:
    def test_full_pipeline(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced(), song_name="Test Song")
        gen = ScriptGenerator(tmp_path)
        result = gen.generate()
        assert isinstance(result, GenerateResult)
        assert result.sections_profiled == 3
        assert result.mood_used == DEFAULT_MOOD
        assert result.variance_detected in ("low", "medium", "high")
        assert "sections" in result.script
        assert "defaults" in result.script
        assert "caption_style" in result.script
        assert len(result.script["sections"]) == 3

    def test_custom_mood(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(mood="bright_poppy")
        assert result.mood_used == "bright_poppy"

    def test_custom_base_color(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(base_color="#ff0000")
        for sec in result.script["sections"]:
            bg = sec["visual"].get("background_color", "")
            assert bg.startswith("#")

    def test_variance_low(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(variance="low")
        assert result.variance_detected == "low"

    def test_variance_high(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(variance="high")
        assert result.variance_detected == "high"

    def test_variance_medium(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(variance="medium")
        assert result.variance_detected == "medium"

    def test_section_has_visual(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        result = gen.generate()
        for sec in result.script["sections"]:
            assert "visual" in sec
            assert "background_color" in sec["visual"]

    def test_section_has_lines_overrides(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        result = gen.generate()
        for sec in result.script["sections"]:
            assert "lines_overrides" in sec
            assert len(sec["lines_overrides"]) > 0

    def test_intro_added_when_provided(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(intro={"image": "cover.jpg", "title": "My Song"})
        assert "intro" in result.script
        assert result.script["intro"]["image"] == "cover.jpg"
        assert result.script["intro"]["duration"] >= 0

    def test_intro_not_added_without_image(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(intro={"title": "My Song"})
        assert "intro" not in result.script

    def test_no_intro_by_default(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        result = gen.generate()
        assert "intro" not in result.script

    def test_empty_sections_produces_empty_script(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw={"lines": []})
        gen = ScriptGenerator(tmp_path)
        result = gen.generate()
        assert result.sections_profiled == 0
        assert result.script["sections"] == []

    def test_script_name_set(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced(), song_name="My Great Song")
        gen = ScriptGenerator(tmp_path)
        result = gen.generate()
        assert result.script["name"] == "My Great Song"

    def test_unknown_mood_falls_back(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(mood="nonexistent_mood")
        assert result.mood_used == "nonexistent_mood"
        assert len(result.script["sections"]) > 0


class TestGenerateScript:
    def test_convenience_function(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        result = generate_script(tmp_path)
        assert isinstance(result, GenerateResult)
        assert result.sections_profiled == 3

    def test_convenience_with_kwargs(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=_lyrics_synced())
        result = generate_script(tmp_path, mood="bright_poppy", variance="high")
        assert result.mood_used == "bright_poppy"
        assert result.variance_detected == "high"


class TestEdgeCases:
    def test_single_line_section(self, tmp_path):
        raw = {"lines": [{"index": 0, "text": "Only line", "section": {"section_type": "verse", "raw_marker": "Verse"}}]}
        synced = {"lines": [{"index": 0, "text": "Only line", "start": 0.0, "end": 2.0, "words": [{"text": "Only", "start": 0.0, "end": 1.0}, {"text": "line", "start": 1.0, "end": 2.0}]}]}
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=raw, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        result = gen.generate()
        assert result.sections_profiled == 1
        assert len(result.script["sections"]) == 1

    def test_many_sections(self, tmp_path):
        raw = {"lines": []}
        synced_lines = []
        section_types = ["intro", "verse", "chorus", "verse", "bridge", "chorus", "outro"]
        idx = 0
        for i, stype in enumerate(section_types):
            raw["lines"].append({"index": idx, "text": f"{stype} line", "section": {"section_type": stype, "raw_marker": f"{stype}_{i}"}})
            synced_lines.append({"index": idx, "text": f"{stype} line", "start": float(idx * 3), "end": float(idx * 3 + 2), "words": [{"text": f"{stype}", "start": float(idx * 3), "end": float(idx * 3 + 1)}, {"text": "line", "start": float(idx * 3 + 1), "end": float(idx * 3 + 2)}]})
            idx += 1
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=raw, lyrics_synced={"lines": synced_lines})
        gen = ScriptGenerator(tmp_path)
        result = gen.generate()
        assert result.sections_profiled == len(section_types)

    def test_no_synced_data_builds_profiles(self, tmp_path):
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw())
        gen = ScriptGenerator(tmp_path)
        sections = gen._build_sections()
        profiles = gen._build_profiles(sections)
        assert len(profiles) == 3
        for p in profiles:
            assert p.word_count == 0

    def test_variance_auto_with_single_section(self, tmp_path):
        raw = {"lines": [{"index": 0, "text": "One line", "section": {"section_type": "verse", "raw_marker": "V"}}]}
        synced = {"lines": [{"index": 0, "text": "One line", "start": 0.0, "end": 2.0, "words": [{"text": "One", "start": 0.0, "end": 1.0}, {"text": "line", "start": 1.0, "end": 2.0}]}]}
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=raw, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(variance="auto")
        assert result.variance_detected in ("low", "medium", "high")

    def test_intro_duration_uses_first_word_start(self, tmp_path):
        synced = _lyrics_synced()
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=_lyrics_raw(), lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(intro={"image": "bg.png"})
        assert result.script["intro"]["duration"] == pytest.approx(0.0, abs=0.01)


class TestWordsOverridesPresent:
    def test_word_overrides_in_script(self, tmp_path):
        raw = {"lines": [
            {"index": 0, "text": "First line", "section": {"section_type": "chorus", "raw_marker": "Chorus"}},
            {"index": 1, "text": "Second line, with more words here today", "section": {"section_type": "chorus", "raw_marker": "Chorus"}},
            {"index": 2, "text": "Third line! And then some more text now", "section": {"section_type": "chorus", "raw_marker": "Chorus"}},
        ]}
        synced = {"lines": [
            {"index": 0, "text": "First line", "start": 0.0, "end": 2.0, "words": [{"text": "First", "start": 0.0, "end": 0.5}, {"text": "line", "start": 0.5, "end": 2.0}]},
            {"index": 1, "text": "Second line, with more words here today", "start": 2.0, "end": 5.0, "words": [{"text": "Second", "start": 2.0, "end": 2.5}, {"text": "line,", "start": 2.5, "end": 3.0}, {"text": "with", "start": 3.0, "end": 3.3}, {"text": "more", "start": 3.3, "end": 3.6}, {"text": "words", "start": 3.6, "end": 4.0}, {"text": "here", "start": 4.0, "end": 4.3}, {"text": "today", "start": 4.3, "end": 5.0}]},
            {"index": 2, "text": "Third line! And then some more text now", "start": 5.0, "end": 8.0, "words": [{"text": "Third", "start": 5.0, "end": 5.5}, {"text": "line!", "start": 5.5, "end": 6.0}, {"text": "And", "start": 6.0, "end": 6.3}, {"text": "then", "start": 6.3, "end": 6.6}, {"text": "some", "start": 6.6, "end": 7.0}, {"text": "more", "start": 7.0, "end": 7.3}, {"text": "text", "start": 7.3, "end": 7.6}, {"text": "now", "start": 7.6, "end": 8.0}]},
        ]}
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=raw, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(mood="bright_poppy", variance="high")
        assert "sections" in result.script


class TestCaptionStyleBranches:
    def test_warm_hue_branch(self, tmp_path):
        raw = _lyrics_raw()
        synced = _lyrics_synced()
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=raw, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(mood="warm_intimate")
        assert "caption_style" in result.script

    def test_green_hue_branch(self, tmp_path):
        raw = _lyrics_raw()
        synced = _lyrics_synced()
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=raw, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        result = gen.generate(mood="cool_ethereal")
        assert "caption_style" in result.script

    def test_medium_hue_branch(self, tmp_path):
        green_mood = MoodProfile(
            name="Green", base_hue=120, saturation=(0.3, 0.5),
            lightness=(0.2, 0.4), texture_default="none",
            direction="horizontal_left_right", gradient_likely=False,
        )
        raw = _lyrics_raw()
        synced = _lyrics_synced()
        _setup_project(tmp_path, analysis=_analysis(), lyrics_raw=raw, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        style = gen._build_caption_style(green_mood, 0.5)
        assert style["highlight_color"] == "#f0a04c"


class TestGapRevealEmptyWords:
    def test_line_with_no_words_continues(self, tmp_path):
        synced = {
            "lines": [
                {"index": 0, "text": "Line 1", "start": 0.0, "end": 1.0, "words": [{"text": "Line", "start": 0.0, "end": 0.5}]},
                {"index": 1, "text": "Line 2", "start": 2.0, "end": 3.0, "words": []},
            ]
        }
        _setup_project(tmp_path, lyrics_synced=synced)
        gen = ScriptGenerator(tmp_path)
        script = {
            "sections": [{
                "lines": [0, 1],
                "visual": {"reveal_mode": "karaoke"},
                "lines_overrides": {},
            }]
        }
        gen._apply_gap_reveal_overrides(script)
        assert isinstance(script["sections"][0]["lines_overrides"], dict)
