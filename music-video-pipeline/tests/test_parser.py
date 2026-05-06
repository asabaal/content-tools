import json
from pathlib import Path

import pytest

from lyrics.parser import LyricParser, LyricWord, LyricLine, LyricsResult, LyricSection, _parse_section_marker


class TestParseSectionMarker:
    def test_simple_section(self):
        s = _parse_section_marker("[Intro]")
        assert s is not None
        assert s.section_type == "intro"
        assert s.index is None
        assert s.tags == []

    def test_section_with_index(self):
        s = _parse_section_marker("[Verse 2]")
        assert s is not None
        assert s.section_type == "verse"
        assert s.index == 2

    def test_section_with_tags(self):
        s = _parse_section_marker("[Verse 3, double time, female]")
        assert s is not None
        assert s.section_type == "verse"
        assert s.index == 3
        assert "double_time" in s.tags
        assert "female" in s.tags

    def test_complex_marker(self):
        s = _parse_section_marker("[Intro, swooshy]")
        assert s is not None
        assert s.section_type == "intro"
        assert "swooshy" in s.tags

    def test_outro(self):
        s = _parse_section_marker("[Outro]")
        assert s is not None
        assert s.section_type == "outro"

    def test_overexaggerated_marker(self):
        s = _parse_section_marker("[Overexaggerated tyrannical laughter]")
        assert s is not None
        assert s.section_type == "overexaggerated_tyrannical_laughter"

    def test_not_a_marker(self):
        s = _parse_section_marker("Hello world")
        assert s is None

    def test_marker_with_spaces(self):
        s = _parse_section_marker("  [Verse]  ")
        assert s is not None
        assert s.section_type == "verse"


class TestLyricSection:
    def test_to_dict(self):
        s = LyricSection(raw_marker="Verse 2", section_type="verse", index=2, tags=["double_time"])
        d = s.to_dict()
        assert d["section_type"] == "verse"
        assert d["index"] == 2
        assert d["tags"] == ["double_time"]


class TestLyricWord:
    def test_duration(self):
        w = LyricWord(text="hello", start=1.0, end=1.5)
        assert w.duration == 0.5

    def test_is_active_true(self):
        w = LyricWord(text="hello", start=1.0, end=2.0)
        assert w.is_active(1.5)

    def test_is_active_at_start(self):
        w = LyricWord(text="hello", start=1.0, end=2.0)
        assert w.is_active(1.0)

    def test_is_active_at_end(self):
        w = LyricWord(text="hello", start=1.0, end=2.0)
        assert w.is_active(2.0)

    def test_is_active_false_before(self):
        w = LyricWord(text="hello", start=1.0, end=2.0)
        assert not w.is_active(0.5)

    def test_is_active_false_after(self):
        w = LyricWord(text="hello", start=1.0, end=2.0)
        assert not w.is_active(2.5)

    def test_to_dict(self):
        w = LyricWord(text="hello", start=1.0, end=2.0)
        d = w.to_dict()
        assert d["text"] == "hello"
        assert d["start"] == 1.0
        assert d["end"] == 2.0


class TestLyricLine:
    def _make_line(self):
        words = [
            LyricWord(text="Hello", start=1.0, end=1.5),
            LyricWord(text="world", start=1.5, end=2.0),
        ]
        return LyricLine(index=0, text="Hello world", start=1.0, end=2.0, words=words)

    def test_duration(self):
        line = self._make_line()
        assert line.duration == 1.0

    def test_is_active_true(self):
        line = self._make_line()
        assert line.is_active(1.5)

    def test_is_active_false(self):
        line = self._make_line()
        assert not line.is_active(0.5)

    def test_get_active_words(self):
        line = self._make_line()
        active = line.get_active_words(1.2)
        assert len(active) == 1
        assert active[0].text == "Hello"

    def test_get_active_words_multiple(self):
        line = self._make_line()
        active = line.get_active_words(1.5)
        assert len(active) == 2

    def test_get_active_words_none(self):
        line = self._make_line()
        active = line.get_active_words(3.0)
        assert len(active) == 0

    def test_get_progress_before(self):
        line = self._make_line()
        assert line.get_progress(0.0) == 0.0

    def test_get_progress_after(self):
        line = self._make_line()
        assert line.get_progress(5.0) == 1.0

    def test_get_progress_middle(self):
        line = self._make_line()
        assert line.get_progress(1.5) == 0.5

    def test_get_progress_zero_duration(self):
        line = LyricLine(index=0, text="x", start=1.0, end=1.0)
        assert line.get_progress(1.0) == 0.0

    def test_to_dict(self):
        line = self._make_line()
        d = line.to_dict()
        assert d["index"] == 0
        assert d["text"] == "Hello world"
        assert d["start"] == 1.0
        assert d["end"] == 2.0
        assert len(d["words"]) == 2

    def test_to_dict_with_section(self):
        words = [LyricWord(text="Hello", start=0.0, end=3.0)]
        section = LyricSection(raw_marker="Intro", section_type="intro")
        line = LyricLine(index=0, text="Hello", start=0.0, end=3.0, words=words, section=section)
        d = line.to_dict()
        assert d["section"]["section_type"] == "intro"

    def test_to_dict_no_section(self):
        words = [LyricWord(text="Hello", start=0.0, end=3.0)]
        line = LyricLine(index=0, text="Hello", start=0.0, end=3.0, words=words)
        d = line.to_dict()
        assert "section" not in d


class TestLyricsResult:
    def _make_result(self):
        words = [LyricWord(text="Hello", start=1.0, end=2.0)]
        lines = [
            LyricLine(index=0, text="Hello", start=1.0, end=2.0, words=words),
            LyricLine(index=1, text="World", start=3.0, end=4.0, words=[LyricWord(text="World", start=3.0, end=4.0)]),
        ]
        return LyricsResult(format="srt", source_file="test.srt", lines=lines)

    def test_total_lines(self):
        r = self._make_result()
        assert r.total_lines == 2

    def test_total_words(self):
        r = self._make_result()
        assert r.total_words == 2

    def test_first_line_time(self):
        r = self._make_result()
        assert r.first_line_time == 1.0

    def test_last_line_time(self):
        r = self._make_result()
        assert r.last_line_time == 4.0

    def test_first_line_time_empty(self):
        r = LyricsResult(format="srt", source_file="x", lines=[])
        assert r.first_line_time is None

    def test_last_line_time_empty(self):
        r = LyricsResult(format="srt", source_file="x", lines=[])
        assert r.last_line_time is None

    def test_to_dict(self):
        r = self._make_result()
        d = r.to_dict()
        assert d["format"] == "srt"
        assert d["total_lines"] == 2
        assert d["total_words"] == 2
        assert len(d["lines"]) == 2
        assert d["has_sections"] is False
        assert d["section_count"] == 0

    def test_to_dict_with_sections(self):
        section = LyricSection(raw_marker="Verse", section_type="verse")
        r = LyricsResult(format="txt", source_file="test.txt", lines=[], sections=[section])
        d = r.to_dict()
        assert d["has_sections"] is True
        assert d["section_count"] == 1

    def test_save(self, tmp_path):
        r = self._make_result()
        out = tmp_path / "lyrics.json"
        r.save(out)
        data = json.loads(out.read_text())
        assert data["total_lines"] == 2

    def test_save_creates_parent_dirs(self, tmp_path):
        r = self._make_result()
        out = tmp_path / "deep" / "nested" / "lyrics.json"
        r.save(out)
        assert out.exists()


class TestLyricParserSRT:
    def test_parse_three_blocks(self, sample_srt):
        result = LyricParser().parse_file(sample_srt)
        assert result.total_lines == 3
        assert result.format == "srt"
        assert result.source_file == "lyrics.srt"

    def test_srt_timing(self, sample_srt):
        result = LyricParser().parse_file(sample_srt)
        assert result.lines[0].start == 1.0
        assert result.lines[0].end == 3.0
        assert result.lines[1].start == 3.5
        assert result.lines[1].end == 6.0

    def test_srt_words(self, sample_srt):
        result = LyricParser().parse_file(sample_srt)
        words = result.lines[0].words
        assert len(words) == 6
        assert words[0].text == "Hello"
        assert words[-1].text == "test"

    def test_srt_word_timing_interpolated(self, sample_srt):
        result = LyricParser().parse_file(sample_srt)
        w = result.lines[0].words[0]
        assert w.start == 1.0
        assert w.end > w.start

    def test_srt_text_content(self, sample_srt):
        result = LyricParser().parse_file(sample_srt)
        assert result.lines[0].text == "Hello world this is a test"
        assert result.lines[2].text == "Third and final verse here"

    def test_srt_empty_blocks_skipped(self, tmp_path):
        content = "1\n00:00:01,000 --> 00:00:02,000\n\n2\n00:00:03,000 --> 00:00:04,000\nHello"
        p = tmp_path / "test.srt"
        p.write_text(content)
        result = LyricParser().parse_file(p)
        assert result.total_lines == 1

    def test_srt_multiline_text_joined(self, tmp_path):
        content = "1\n00:00:01,000 --> 00:00:03,000\nLine one\nLine two"
        p = tmp_path / "test.srt"
        p.write_text(content)
        result = LyricParser().parse_file(p)
        assert result.lines[0].text == "Line one Line two"

    def test_srt_malformed_timing_skipped(self, tmp_path):
        content = "1\nbad timing\nHello\n\n2\n00:00:01,000 --> 00:00:02,000\nWorld"
        p = tmp_path / "test.srt"
        p.write_text(content)
        result = LyricParser().parse_file(p)
        assert result.total_lines == 1
        assert result.lines[0].text == "World"

    def test_srt_no_sections(self, sample_srt):
        result = LyricParser().parse_file(sample_srt)
        assert result.sections == []


class TestLyricParserLRC:
    def test_parse_three_lines(self, sample_lrc):
        result = LyricParser().parse_file(sample_lrc)
        assert result.total_lines == 3
        assert result.format == "lrc"

    def test_lrc_timing(self, sample_lrc):
        result = LyricParser().parse_file(sample_lrc)
        assert result.lines[0].start == 1.0
        assert result.lines[1].start == 3.5
        assert result.lines[2].start == 6.5

    def test_lrc_end_time_from_next_line(self, sample_lrc):
        result = LyricParser().parse_file(sample_lrc)
        assert result.lines[0].end == 3.5
        assert result.lines[1].end == 6.5

    def test_lrc_last_line_default_duration(self, sample_lrc):
        result = LyricParser().parse_file(sample_lrc)
        assert result.lines[2].end == 6.5 + 3.0

    def test_lrc_milliseconds(self, tmp_path):
        content = "[00:01.50]Hello\n[00:03.00]World"
        p = tmp_path / "test.lrc"
        p.write_text(content)
        result = LyricParser().parse_file(p)
        assert result.lines[0].start == 1.5

    def test_lrc_3digit_ms(self, tmp_path):
        content = "[00:01.500]Hello"
        p = tmp_path / "test.lrc"
        p.write_text(content)
        result = LyricParser().parse_file(p)
        assert result.lines[0].start == pytest.approx(1.5, abs=0.01)

    def test_lrc_metadata_lines_skipped(self, tmp_path):
        content = "[ti:Song Title]\n[ar:Artist]\n[00:01.00]Hello"
        p = tmp_path / "test.lrc"
        p.write_text(content)
        result = LyricParser().parse_file(p)
        assert result.total_lines == 1


class TestLyricParserTXT:
    def test_parse_three_lines(self, sample_txt):
        result = LyricParser().parse_file(sample_txt)
        assert result.total_lines == 3
        assert result.format == "txt"

    def test_txt_default_timing(self, sample_txt):
        result = LyricParser().parse_file(sample_txt)
        assert result.lines[0].start == 0.0
        assert result.lines[0].end == 3.0
        assert result.lines[1].start == 3.0
        assert result.lines[1].end == 6.0
        assert result.lines[2].start == 6.0
        assert result.lines[2].end == 9.0

    def test_txt_custom_duration(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("Line one\nLine two")
        parser = LyricParser()
        lines, sections = parser._parse_plain_text(p.read_text(), default_duration=5.0)
        assert lines[0].end == 5.0
        assert lines[1].start == 5.0

    def test_txt_words(self, sample_txt):
        result = LyricParser().parse_file(sample_txt)
        assert result.lines[0].words[0].text == "Hello"
        assert len(result.lines[0].words) == 6

    def test_txt_blank_lines_skipped(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("Line one\n\n\nLine two")
        result = LyricParser().parse_file(p)
        assert result.total_lines == 2


class TestLyricParserTXTSections:
    def test_sections_parsed(self, sample_txt_sections):
        result = LyricParser().parse_file(sample_txt_sections)
        assert len(result.sections) == 5
        assert result.sections[0].section_type == "intro"
        assert result.sections[1].section_type == "intro"
        assert result.sections[2].section_type == "verse"
        assert result.sections[3].section_type == "verse"
        assert result.sections[3].index == 2
        assert "double_time" in result.sections[3].tags
        assert "female" in result.sections[3].tags

    def test_section_markers_not_in_lines(self, sample_txt_sections):
        result = LyricParser().parse_file(sample_txt_sections)
        for line in result.lines:
            assert not line.text.startswith("[")

    def test_lines_have_section_references(self, sample_txt_sections):
        result = LyricParser().parse_file(sample_txt_sections)
        assert result.lines[0].section is not None
        assert result.lines[0].section.section_type == "intro"
        assert result.lines[1].section is not None
        assert result.lines[1].section.section_type == "verse"
        assert result.lines[3].section is not None
        assert result.lines[3].section.section_type == "verse"

    def test_word_count_excludes_markers(self, sample_txt_sections):
        result = LyricParser().parse_file(sample_txt_sections)
        assert result.total_lines == 6
        assert result.total_words > 0
        assert "Intro" not in " ".join(l.text for l in result.lines)

    def test_timing_continuous(self, sample_txt_sections):
        result = LyricParser().parse_file(sample_txt_sections)
        for i in range(1, len(result.lines)):
            assert result.lines[i].start == result.lines[i - 1].end

    def test_sections_only_file(self, sample_txt_sections_only):
        result = LyricParser().parse_file(sample_txt_sections_only)
        assert result.total_lines == 0
        assert len(result.sections) == 3

    def test_to_dict_includes_sections(self, sample_txt_sections):
        result = LyricParser().parse_file(sample_txt_sections)
        d = result.to_dict()
        assert d["has_sections"] is True
        assert d["section_count"] == 5
        assert len(d["sections"]) == 5

    def test_save_with_sections(self, sample_txt_sections, tmp_path):
        result = LyricParser().parse_file(sample_txt_sections)
        out = tmp_path / "lyrics.json"
        result.save(out)
        data = json.loads(out.read_text())
        assert data["has_sections"] is True
        assert data["section_count"] == 5


class TestLyricParserFileHandling:
    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Lyrics file not found"):
            LyricParser().parse_file(tmp_path / "missing.srt")

    def test_unsupported_format_raises(self, tmp_path):
        p = tmp_path / "lyrics.xml"
        p.write_text("<lyrics>test</lyrics>")
        with pytest.raises(ValueError, match="Unsupported lyrics format"):
            LyricParser().parse_file(p)

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.srt"
        p.write_text("")
        result = LyricParser().parse_file(p)
        assert result.total_lines == 0

    def test_make_words_empty_text(self):
        words = LyricParser._make_words("", 0.0, 1.0)
        assert words == []
