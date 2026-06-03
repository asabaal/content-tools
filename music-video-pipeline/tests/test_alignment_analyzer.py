import numpy as np
import pytest

from audio.features import AudioFeatures, BeatInfo
from lyrics.alignment_analyzer import (
    AlignmentAnalysis,
    LineMatch,
    WordTiming,
    _align_lyrics_to_segments,
    _cluster_onsets,
    _compute_onset_word_timings,
    _compute_word_timings,
    _count_syllables,
    _group_onsets_by_gap,
    _normalize,
    _recover_unmatched_lines,
    _score_boundary_quality,
    _snap_word_starts_to_onsets,
    analyze_alignment,
)
from lyrics.parser import LyricLine, LyricWord


def _make_features(duration=30.0):
    return AudioFeatures(
        duration=duration,
        sample_rate=22050,
        beats=BeatInfo(times=np.array([0.0, 0.5, 1.0]), tempo=120.0, confidence=0.9),
        onset_times=np.array([0.5, 1.0, 1.5]),
        rms_energy=np.zeros(100),
        spectral_centroids=np.zeros(100),
        zero_crossing_rate=np.zeros(100),
    )


def _make_lines(texts):
    return [
        LyricLine(index=i, text=t, start=i * 3.0, end=i * 3.0 + 3.0, words=[LyricWord(text=w, start=0, end=1) for w in t.split()])
        for i, t in enumerate(texts)
    ]


class TestNormalize:
    def test_lowercase(self):
        assert _normalize("Hello World") == "hello world"

    def test_strip_punctuation(self):
        assert _normalize("hello, world!") == "hello world"

    def test_both(self):
        assert _normalize("Hello, World!") == "hello world"


class TestBoundaryQuality:
    def test_perfect_boundary(self):
        score = _score_boundary_quality(1.0, 3.0, 5, 3.5)
        assert score > 0.7

    def test_too_short(self):
        score = _score_boundary_quality(1.0, 1.2, 10, 1.5)
        assert score < 0.6

    def test_too_long(self):
        score = _score_boundary_quality(1.0, 20.0, 3, 21.0)
        assert score < 0.6

    def test_overlap(self):
        score = _score_boundary_quality(5.0, 7.0, 3, 6.0)
        assert score < 0.8

    def test_very_large_gap(self):
        score = _score_boundary_quality(1.0, 3.0, 3, 20.0)
        assert score < 1.0

    def test_no_next(self):
        score = _score_boundary_quality(1.0, 3.0, 5, None)
        assert score > 0.5

    def test_zero_duration(self):
        score = _score_boundary_quality(1.0, 1.0, 5, 2.0)
        assert score == 0.0

    def test_zero_words(self):
        score = _score_boundary_quality(1.0, 3.0, 0, 3.5)
        assert score == 0.0


class TestClusterOnsets:
    def test_basic(self):
        onsets = np.array([1.0, 1.1, 1.2, 5.0, 5.1, 10.0, 10.1])
        clusters = _cluster_onsets(onsets)
        assert len(clusters) == 3

    def test_single(self):
        clusters = _cluster_onsets(np.array([1.0]))
        assert len(clusters) == 1

    def test_empty(self):
        clusters = _cluster_onsets(np.array([]))
        assert clusters == []


class TestAlignLyricsToSegments:
    def test_perfect_1to1(self):
        lines = _make_lines(["hello world", "foo bar"])
        segments = [
            {"text": "hello world", "start": 0.0, "end": 2.0},
            {"text": "foo bar", "start": 2.5, "end": 4.0},
        ]
        line_segs, ratios, texts = _align_lyrics_to_segments(lines, segments)
        assert line_segs[0] == [0]
        assert line_segs[1] == [1]
        assert ratios[0] == 1.0
        assert ratios[1] == 1.0

    def test_split_line_across_segments(self):
        lines = _make_lines(["they caused my anxiety now its chronic", "if jesus was platonic"])
        segments = [
            {"text": "they caused my anxiety", "start": 1.0, "end": 3.0},
            {"text": "now its chronic if jesus", "start": 3.0, "end": 5.0},
            {"text": "was platonic", "start": 5.0, "end": 7.0},
        ]
        line_segs, ratios, texts = _align_lyrics_to_segments(lines, segments)
        assert 0 in line_segs[0]
        assert 1 in line_segs[0]
        assert line_segs[1] == [1, 2]

    def test_more_segments_than_lines(self):
        lines = _make_lines(["hello world", "foo bar"])
        segments = [
            {"text": "hello world", "start": 0.0, "end": 2.0},
            {"text": "extra segment", "start": 2.0, "end": 3.0},
            {"text": "foo bar", "start": 3.0, "end": 5.0},
        ]
        line_segs, ratios, texts = _align_lyrics_to_segments(lines, segments)
        assert line_segs[0] == [0]
        assert line_segs[1] == [2]

    def test_fewer_segments_than_lines(self):
        lines = _make_lines(["a", "b", "c", "d"])
        segments = [
            {"text": "a", "start": 1.0, "end": 2.0},
            {"text": "b", "start": 3.0, "end": 4.0},
        ]
        line_segs, ratios, texts = _align_lyrics_to_segments(lines, segments)
        assert line_segs[0] == [0]
        assert line_segs[1] == [1]

    def test_no_text_overlap(self):
        lines = _make_lines(["xyz completely unique text"])
        segments = [{"text": "abc totally different stuff", "start": 1.0, "end": 3.0}]
        line_segs, ratios, texts = _align_lyrics_to_segments(lines, segments)
        assert ratios[0] == 0.0


class TestLineMatch:
    def test_to_dict_minimal(self):
        m = LineMatch(lyric_index=0, lyric_text="hello")
        d = m.to_dict()
        assert d["lyric_index"] == 0
        assert "transcription_start" not in d
        assert d["is_split"] is False
        assert d["matched_segments"] == []

    def test_to_dict_full(self):
        m = LineMatch(
            lyric_index=0, lyric_text="hello",
            matched_segments=[0, 1],
            transcription_text="hello world",
            word_match_ratio=0.9,
            transcription_start=1.0, transcription_end=3.0,
            boundary_quality=0.8,
            is_split=True,
            recovery_method="onset_syllable",
        )
        d = m.to_dict()
        assert d["transcription_start"] == 1.0
        assert d["is_split"] is True
        assert d["matched_segments"] == [0, 1]
        assert d["word_match_ratio"] == 0.9
        assert d["boundary_quality"] == 0.8
        assert d["recovery_method"] == "onset_syllable"


class TestAlignmentAnalysis:
    def test_to_dict(self):
        a = AlignmentAnalysis(
            line_matches=[],
            total_lines=0,
            transcription_segment_count=0,
            exact_matches=0,
            partial_matches=0,
            unmatched_lines=0,
            lines_split=0,
            lines_recovered=0,
            boundary_avg_quality=0.0,
            recommendation="none",
            recommendation_reason="No data",
        )
        d = a.to_dict()
        assert "summary" in d
        assert d["summary"]["recommendation"] == "none"
        assert d["summary"]["lines_split"] == 0
        assert "clustering_note" in d["summary"]

    def test_save(self, tmp_path):
        a = AlignmentAnalysis(
            line_matches=[],
            total_lines=0,
            transcription_segment_count=0,
            exact_matches=0,
            partial_matches=0,
            unmatched_lines=0,
            lines_split=0,
            lines_recovered=0,
            boundary_avg_quality=0.0,
            recommendation="none",
            recommendation_reason="No data",
        )
        path = tmp_path / "alignment_analysis.json"
        a.save(path)
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "summary" in data


class TestAnalyzeAlignment:
    def test_no_data(self):
        features = _make_features()
        lines = _make_lines(["hello world", "foo bar"])
        result = analyze_alignment(lines, None, None, features)
        assert result.total_lines == 2
        assert result.recommendation == "none"

    def test_with_transcription(self):
        features = _make_features()
        lines = _make_lines(["hello world", "foo bar baz"])
        segments = [
            {"text": "hello world", "start": 1.0, "end": 3.0},
            {"text": "foo bar baz", "start": 4.0, "end": 6.0},
        ]
        result = analyze_alignment(lines, segments, None, features)
        assert result.transcription_segment_count == 2
        assert result.exact_matches == 2
        assert result.recommendation == "transcription"

    def test_with_onsets_logged(self):
        features = _make_features()
        lines = _make_lines(["hello world", "foo bar"])
        onsets = np.array([1.0, 1.2, 5.0, 5.3])
        result = analyze_alignment(lines, None, onsets, features)
        assert result.onset_cluster_count > 0
        assert result.onset_cluster_details is not None
        assert result.recommendation == "none"

    def test_split_line_detected(self):
        features = _make_features()
        lines = _make_lines(["they caused my anxiety now its chronic", "if jesus was platonic"])
        segments = [
            {"text": "they caused my anxiety", "start": 1.0, "end": 3.0},
            {"text": "now its chronic if jesus", "start": 3.0, "end": 5.0},
            {"text": "was platonic", "start": 5.0, "end": 7.0},
        ]
        result = analyze_alignment(lines, segments, None, features)
        assert result.lines_split > 0
        m0 = result.line_matches[0]
        assert m0.is_split is True
        assert len(m0.matched_segments) > 1

    def test_no_splits_when_1to1(self):
        features = _make_features()
        lines = _make_lines(["hello world", "foo bar"])
        segments = [
            {"text": "hello world", "start": 1.0, "end": 3.0},
            {"text": "foo bar", "start": 4.0, "end": 6.0},
        ]
        result = analyze_alignment(lines, segments, None, features)
        assert result.lines_split == 0
        for m in result.line_matches:
            assert m.is_split is False

    def test_word_match_ratio_perfect(self):
        features = _make_features()
        lines = _make_lines(["hello world", "foo bar"])
        segments = [
            {"text": "hello world", "start": 1.0, "end": 3.0},
            {"text": "foo bar", "start": 4.0, "end": 6.0},
        ]
        result = analyze_alignment(lines, segments, None, features)
        for m in result.line_matches:
            assert m.word_match_ratio == 1.0

    def test_unequal_segments_more(self):
        features = _make_features()
        lines = _make_lines(["hello world", "foo bar"])
        segments = [
            {"text": "hello world", "start": 1.0, "end": 2.0},
            {"text": "extra segment", "start": 2.0, "end": 3.0},
            {"text": "foo bar", "start": 3.0, "end": 5.0},
        ]
        result = analyze_alignment(lines, segments, None, features)
        assert result.transcription_segment_count == 3

    def test_unequal_segments_fewer(self):
        features = _make_features()
        lines = _make_lines(["hello world", "foo bar", "baz qux"])
        segments = [
            {"text": "hello world", "start": 1.0, "end": 3.0},
            {"text": "foo bar", "start": 4.0, "end": 6.0},
        ]
        result = analyze_alignment(lines, segments, None, features)
        assert result.total_lines == 3

    def test_cluster_details_logged_with_transcription(self):
        features = _make_features()
        lines = _make_lines(["hello world", "foo bar"])
        segments = [
            {"text": "hello world", "start": 1.0, "end": 3.0},
            {"text": "foo bar", "start": 4.0, "end": 6.0},
        ]
        onsets = np.array([1.0, 1.1, 5.0, 5.1])
        result = analyze_alignment(lines, segments, onsets, features)
        assert result.onset_cluster_details is not None
        assert result.onset_cluster_count > 0
        assert result.recommendation == "transcription"

    def test_unmatched_lines_in_analysis(self):
        features = _make_features()
        lines = _make_lines(["unique text xyz", "hello world", "completely different abc"])
        segments = [
            {"text": "unique text xyz", "start": 1.0, "end": 3.0},
            {"text": "hello world", "start": 4.0, "end": 6.0},
            {"text": "wrong mismatch text", "start": 7.0, "end": 9.0},
        ]
        result = analyze_alignment(lines, segments, None, features)
        assert result.unmatched_lines >= 0

    def test_boundary_quality_scored(self):
        features = _make_features()
        lines = _make_lines(["hello world", "foo bar"])
        segments = [
            {"text": "hello world", "start": 1.0, "end": 3.0},
            {"text": "foo bar", "start": 4.0, "end": 6.0},
        ]
        result = analyze_alignment(lines, segments, None, features)
        for m in result.line_matches:
            assert m.boundary_quality is not None
            assert m.boundary_quality > 0.0

    def test_transcription_boundary_spans_segments(self):
        features = _make_features()
        lines = _make_lines(["they caused my anxiety now its chronic"])
        segments = [
            {"text": "they caused my anxiety", "start": 1.0, "end": 3.0},
            {"text": "now its chronic", "start": 3.0, "end": 5.0},
        ]
        result = analyze_alignment(lines, segments, None, features)
        m = result.line_matches[0]
        assert m.is_split is True
        assert m.transcription_start == 1.0
        assert m.transcription_end == 5.0


class TestCountSyllables:
    def test_single_syllable_words(self):
        assert _count_syllables("ha ha ha") == 3

    def test_multi_syllable_words(self):
        n = _count_syllables("laughing crying")
        assert n >= 3

    def test_empty(self):
        assert _count_syllables("") == 0

    def test_ha_line(self):
        text = " ".join(["HA"] * 21)
        assert _count_syllables(text) == 21


class TestGroupOnsetsByGap:
    def test_empty(self):
        groups = _group_onsets_by_gap(np.array([]))
        assert groups == []

    def test_single(self):
        groups = _group_onsets_by_gap(np.array([1.0]))
        assert len(groups) == 1
        assert len(groups[0]) == 1

    def test_two_groups(self):
        groups = _group_onsets_by_gap(np.array([1.0, 1.2, 5.0, 5.3]))
        assert len(groups) == 2

    def test_one_group(self):
        groups = _group_onsets_by_gap(np.array([1.0, 1.1, 1.2, 1.3]))
        assert len(groups) == 1


class TestRecoverUnmatchedLines:
    def test_recovers_last_line(self):
        matches = [
            LineMatch(lyric_index=0, lyric_text="hello world", matched_segments=[0],
                      transcription_start=1.0, transcription_end=3.0),
            LineMatch(lyric_index=1, lyric_text="ha ha ha ha ha", matched_segments=[]),
        ]
        onsets = np.array([1.5, 1.8, 4.0, 4.2, 4.4, 4.6, 4.8, 5.0])
        _recover_unmatched_lines(matches, onsets, 10.0)
        assert matches[1].recovery_method == "onset_syllable"
        assert matches[1].transcription_start is not None
        assert matches[1].transcription_end is not None

    def test_no_onsets_leaves_unmatched(self):
        matches = [
            LineMatch(lyric_index=0, lyric_text="hello", matched_segments=[0],
                      transcription_start=1.0, transcription_end=3.0),
            LineMatch(lyric_index=1, lyric_text="xyz", matched_segments=[]),
        ]
        _recover_unmatched_lines(matches, None, 10.0)
        assert matches[1].recovery_method is None

    def test_no_onsets_in_range_leaves_unmatched(self):
        matches = [
            LineMatch(lyric_index=0, lyric_text="hello", matched_segments=[0],
                      transcription_start=1.0, transcription_end=3.0),
            LineMatch(lyric_index=1, lyric_text="xyz unique", matched_segments=[]),
            LineMatch(lyric_index=2, lyric_text="done", matched_segments=[1],
                      transcription_start=5.0, transcription_end=7.0),
        ]
        onsets = np.array([1.5, 8.0, 8.5])
        _recover_unmatched_lines(matches, onsets, 15.0)
        assert matches[1].recovery_method is None

    def test_no_unmatched_does_nothing(self):
        matches = [
            LineMatch(lyric_index=0, lyric_text="hello", matched_segments=[0],
                      transcription_start=1.0, transcription_end=3.0),
        ]
        _recover_unmatched_lines(matches, np.array([1.5]), 10.0)
        assert matches[0].recovery_method is None

    def test_recovers_middle_line(self):
        matches = [
            LineMatch(lyric_index=0, lyric_text="hello", matched_segments=[0],
                      transcription_start=1.0, transcription_end=3.0),
            LineMatch(lyric_index=1, lyric_text="ha ha ha", matched_segments=[]),
            LineMatch(lyric_index=2, lyric_text="goodbye", matched_segments=[1],
                      transcription_start=8.0, transcription_end=10.0),
        ]
        onsets = np.array([1.5, 4.0, 4.3, 4.6, 7.0, 8.5])
        _recover_unmatched_lines(matches, onsets, 15.0)
        assert matches[1].recovery_method == "onset_syllable"
        assert matches[1].transcription_start >= 3.0
        assert matches[1].transcription_end <= 8.0


class TestAnalyzeAlignmentRecovery:
    def test_recovers_unmatched_line_with_onsets(self):
        features = _make_features(duration=30.0)
        lines = _make_lines(["hello world", "ha ha ha ha ha", "goodbye world"])
        segments = [
            {"text": "hello world", "start": 1.0, "end": 3.0},
            {"text": "goodbye world", "start": 10.0, "end": 12.0},
        ]
        onsets = np.array([1.5, 5.0, 5.3, 5.6, 5.9, 6.2, 10.5])
        result = analyze_alignment(lines, segments, onsets, features)
        assert result.lines_recovered == 1
        m = result.line_matches[1]
        assert m.recovery_method == "onset_syllable"
        assert m.transcription_start is not None

    def test_no_recovery_without_onsets(self):
        features = _make_features()
        lines = _make_lines(["hello world", "ha ha ha", "goodbye"])
        segments = [
            {"text": "hello world", "start": 1.0, "end": 3.0},
            {"text": "goodbye", "start": 8.0, "end": 10.0},
        ]
        result = analyze_alignment(lines, segments, None, features)
        assert result.lines_recovered == 0
        assert result.unmatched_lines >= 1


class TestSnapWordStartsToOnsets:
    def test_default_first_segment_words(self):
        timings = [WordTiming(word="hello", start=1.0, end=2.0, source="transcription")]
        onsets = np.array([1.5])
        _snap_word_starts_to_onsets(timings, onsets)
        assert timings[0].start == 1.0

    def test_skips_non_transcription_source(self):
        timings = [
            WordTiming(word="hello", start=1.0, end=2.0, source="interpolated"),
            WordTiming(word="world", start=2.0, end=3.0, source="transcription"),
        ]
        onsets = np.array([1.5])
        _snap_word_starts_to_onsets(timings, onsets)
        assert timings[0].start == 1.0

    def test_nearby_onset_no_change(self):
        timings = [WordTiming(word="hello", start=1.0, end=2.0, source="transcription")]
        onsets = np.array([1.05])
        _snap_word_starts_to_onsets(timings, onsets, set())
        assert timings[0].start == 1.0

    def test_positive_gap_not_first_in_seg(self):
        timings = [WordTiming(word="hello", start=1.0, end=2.0, source="transcription")]
        onsets = np.array([1.2])
        _snap_word_starts_to_onsets(timings, onsets, {("other", 1.0)})
        assert timings[0].start == 1.0

    def test_negative_gap_snaps_backward(self):
        timings = [WordTiming(word="hello", start=1.0, end=3.0, source="transcription")]
        onsets = np.array([0.8])
        _snap_word_starts_to_onsets(timings, onsets, {("hello", 1.0)}, prev_line_end=0.0)
        assert timings[0].start == 0.8

    def test_snap_makes_duration_too_short(self):
        timings = [WordTiming(word="hi", start=1.0, end=1.15, source="transcription")]
        onsets = np.array([1.12])
        _snap_word_starts_to_onsets(timings, onsets, {("hi", 1.0)})
        assert timings[0].start == 1.0

    def test_negative_gap_onset_before_boundary(self):
        timings = [WordTiming(word="hello", start=1.5, end=3.0, source="transcription")]
        onsets = np.array([1.25])
        _snap_word_starts_to_onsets(timings, onsets, {("hello", 1.5)}, prev_line_end=1.3)
        assert timings[0].start == 1.5


class TestWordTiming:
    def test_to_dict(self):
        wt = WordTiming(word="hello", start=1.0, end=2.0, source="transcription")
        d = wt.to_dict()
        assert d["word"] == "hello"
        assert d["start"] == 1.0
        assert d["end"] == 2.0
        assert d["source"] == "transcription"


class TestComputeWordTimings:
    def _make_segments_with_words(self, *specs):
        segments = []
        for text, start, end, words in specs:
            segments.append({"text": text, "start": start, "end": end, "words": words})
        return segments

    def test_perfect_match(self):
        segs = self._make_segments_with_words(
            ("hello world", 1.0, 3.0, [
                {"word": "hello", "start": 1.0, "end": 2.0, "probability": 0.9},
                {"word": "world", "start": 2.0, "end": 3.0, "probability": 0.9},
            ]),
        )
        timings = _compute_word_timings("hello world", [0], segs, 1.0, 3.0)
        assert timings is not None
        assert len(timings) == 2
        assert timings[0].word == "hello"
        assert timings[0].source == "transcription"
        assert timings[0].start == 1.0
        assert timings[1].word == "world"
        assert timings[1].source == "transcription"

    def test_no_matched_segments(self):
        timings = _compute_word_timings("hello", [], [], 0.0, 1.0)
        assert timings is None

    def test_empty_lyric_text(self):
        segs = self._make_segments_with_words(
            ("hello", 1.0, 2.0, [{"word": "hello", "start": 1.0, "end": 2.0, "probability": 0.9}]),
        )
        timings = _compute_word_timings("", [0], segs, 1.0, 2.0)
        assert timings is None

    def test_no_transcription_words(self):
        segs = [{"text": "hello", "start": 1.0, "end": 2.0, "words": []}]
        timings = _compute_word_timings("hello", [0], segs, 1.0, 2.0)
        assert timings is None

    def test_interpolated_word(self):
        segs = self._make_segments_with_words(
            ("cause my extreme", 1.0, 3.0, [
                {"word": "cause", "start": 1.0, "end": 1.5, "probability": 0.9},
                {"word": "my", "start": 1.5, "end": 2.0, "probability": 0.9},
                {"word": "extreme", "start": 2.0, "end": 3.0, "probability": 0.9},
            ]),
        )
        timings = _compute_word_timings("they caused my extreme anxiety", [0], segs, 1.0, 3.0)
        assert timings is not None
        assert len(timings) == 5
        assert timings[0].word == "they"
        assert timings[0].source == "interpolated"
        assert timings[1].word == "caused"
        assert timings[1].source == "interpolated"
        assert timings[2].word == "my"
        assert timings[2].source == "transcription"
        assert timings[3].word == "extreme"
        assert timings[3].source == "transcription"
        assert timings[4].word == "anxiety"
        assert timings[4].source == "interpolated"

    def test_split_line_across_segments(self):
        segs = self._make_segments_with_words(
            ("they caused my", 1.0, 3.0, [
                {"word": "they", "start": 1.0, "end": 1.5, "probability": 0.9},
                {"word": "caused", "start": 1.5, "end": 2.0, "probability": 0.9},
                {"word": "my", "start": 2.0, "end": 3.0, "probability": 0.9},
            ]),
            ("extreme anxiety", 3.0, 5.0, [
                {"word": "extreme", "start": 3.0, "end": 4.0, "probability": 0.9},
                {"word": "anxiety", "start": 4.0, "end": 5.0, "probability": 0.9},
            ]),
        )
        timings = _compute_word_timings("they caused my extreme anxiety", [0, 1], segs, 1.0, 5.0)
        assert timings is not None
        assert len(timings) == 5
        for t in timings:
            assert t.source == "transcription"
        assert timings[0].start == 1.0
        assert timings[4].end == 5.0

    def test_interpolation_first_word(self):
        segs = self._make_segments_with_words(
            ("hello world", 1.0, 3.0, [
                {"word": "hello", "start": 1.0, "end": 2.0, "probability": 0.9},
                {"word": "world", "start": 2.0, "end": 3.0, "probability": 0.9},
            ]),
        )
        timings = _compute_word_timings("xyz hello world", [0], segs, 1.0, 3.0)
        assert timings is not None
        assert timings[0].word == "xyz"
        assert timings[0].source == "interpolated"
        assert timings[0].start == 1.0
        assert timings[0].end == 1.1

    def test_unmatched_between_matched_fills(self):
        segs = self._make_segments_with_words(
            ("hello my world", 0.0, 3.0, [
                {"word": "hello", "start": 0.0, "end": 1.0, "probability": 0.9},
                {"word": "my", "start": 1.0, "end": 2.0, "probability": 0.9},
                {"word": "world", "start": 2.0, "end": 3.0, "probability": 0.9},
            ]),
        )
        timings = _compute_word_timings("hello there world", [0], segs, 0.0, 3.0)
        assert timings is not None
        assert len(timings) == 3
        assert timings[1].word == "there"
        assert timings[1].source == "transcription"

    def test_unmatched_between_matched_else_branch(self):
        segs = self._make_segments_with_words(
            ("a c e", 0.0, 5.0, [
                {"word": "a", "start": 0.0, "end": 1.0, "probability": 0.9},
                {"word": "c", "start": 2.0, "end": 3.0, "probability": 0.9},
                {"word": "e", "start": 4.0, "end": 5.0, "probability": 0.9},
            ]),
        )
        timings = _compute_word_timings("a b c d e", [0], segs, 0.0, 5.0)
        assert timings is not None
        assert timings[1].source == "interpolated"
        assert timings[3].source == "interpolated"

    def test_unmatched_last_word_fills_from_prev(self):
        segs = self._make_segments_with_words(
            ("a b c d", 0.0, 4.0, [
                {"word": "a", "start": 0.0, "end": 1.0, "probability": 0.9},
                {"word": "b", "start": 1.0, "end": 2.0, "probability": 0.9},
                {"word": "c", "start": 2.0, "end": 3.0, "probability": 0.9},
                {"word": "d", "start": 3.0, "end": 4.0, "probability": 0.9},
            ]),
        )
        timings = _compute_word_timings("a b c extra", [0], segs, 0.0, 4.0)
        assert timings is not None
        assert timings[3].word == "extra"
        assert timings[3].source == "transcription"

    def test_unmatched_first_word_fills_from_next(self):
        segs = self._make_segments_with_words(
            ("x a b c", 0.0, 4.0, [
                {"word": "x", "start": 0.0, "end": 1.0, "probability": 0.9},
                {"word": "a", "start": 1.0, "end": 2.0, "probability": 0.9},
                {"word": "b", "start": 2.0, "end": 3.0, "probability": 0.9},
                {"word": "c", "start": 3.0, "end": 4.0, "probability": 0.9},
            ]),
        )
        timings = _compute_word_timings("extra a b c", [0], segs, 0.0, 4.0)
        assert timings is not None
        assert timings[0].word == "extra"
        assert timings[0].source == "transcription"


class TestComputeOnsetWordTimings:
    def test_basic(self):
        onsets = np.array([1.0, 1.2, 1.4, 1.6, 1.8])
        timings = _compute_onset_word_timings("ha ha ha ha ha", onsets)
        assert timings is not None
        assert len(timings) == 5
        for t in timings:
            assert t.source == "onset_syllable"
            assert t.word == "ha"

    def test_empty_onsets(self):
        timings = _compute_onset_word_timings("hello", np.array([]))
        assert timings is None

    def test_empty_text(self):
        timings = _compute_onset_word_timings("", np.array([1.0, 2.0]))
        assert timings is None

    def test_multi_syllable_words(self):
        onsets = np.array([1.0, 1.3, 1.6, 2.0, 2.5, 3.0])
        timings = _compute_onset_word_timings("laughing crying", onsets)
        assert timings is not None
        assert len(timings) == 2
        assert timings[0].word == "laughing"
        assert timings[1].word == "crying"

    def test_single_word(self):
        onsets = np.array([1.0, 1.5, 2.0, 2.5])
        timings = _compute_onset_word_timings("supercalifragilistic", onsets)
        assert timings is not None
        assert len(timings) == 1
        assert timings[0].start == 1.0


class TestWordTimingsInAnalysis:
    def test_word_timings_present_for_matched_lines(self):
        features = _make_features()
        lines = _make_lines(["hello world", "foo bar"])
        segments = [
            {"text": "hello world", "start": 1.0, "end": 3.0, "words": [
                {"word": "hello", "start": 1.0, "end": 2.0, "probability": 0.9},
                {"word": "world", "start": 2.0, "end": 3.0, "probability": 0.9},
            ]},
            {"text": "foo bar", "start": 4.0, "end": 6.0, "words": [
                {"word": "foo", "start": 4.0, "end": 5.0, "probability": 0.9},
                {"word": "bar", "start": 5.0, "end": 6.0, "probability": 0.9},
            ]},
        ]
        result = analyze_alignment(lines, segments, None, features)
        m0 = result.line_matches[0]
        assert m0.word_timings is not None
        assert len(m0.word_timings) == 2
        assert m0.word_timings[0].source == "transcription"

    def test_word_timings_in_to_dict(self):
        features = _make_features()
        lines = _make_lines(["hello world"])
        segments = [
            {"text": "hello world", "start": 1.0, "end": 3.0, "words": [
                {"word": "hello", "start": 1.0, "end": 2.0, "probability": 0.9},
                {"word": "world", "start": 2.0, "end": 3.0, "probability": 0.9},
            ]},
        ]
        result = analyze_alignment(lines, segments, None, features)
        d = result.line_matches[0].to_dict()
        assert "word_timings" in d
        assert len(d["word_timings"]) == 2
        assert d["word_timings"][0]["word"] == "hello"
        assert d["word_timings"][0]["source"] == "transcription"

    def test_word_timings_none_for_unmatched(self):
        features = _make_features()
        lines = _make_lines(["unique text xyz"])
        segments = [{"text": "totally different", "start": 1.0, "end": 3.0, "words": [
            {"word": "totally", "start": 1.0, "end": 2.0, "probability": 0.9},
            {"word": "different", "start": 2.0, "end": 3.0, "probability": 0.9},
        ]}]
        result = analyze_alignment(lines, segments, None, features)
        d = result.line_matches[0].to_dict()
        assert "word_timings" not in d

    def test_word_timings_absent_when_no_transcription(self):
        features = _make_features()
        lines = _make_lines(["hello world"])
        result = analyze_alignment(lines, None, None, features)
        d = result.line_matches[0].to_dict()
        assert "word_timings" not in d

    def test_recovered_line_has_onset_word_timings(self):
        features = _make_features(duration=30.0)
        lines = _make_lines(["hello world", "ha ha ha ha ha", "goodbye world"])
        segments = [
            {"text": "hello world", "start": 1.0, "end": 3.0, "words": [
                {"word": "hello", "start": 1.0, "end": 2.0, "probability": 0.9},
                {"word": "world", "start": 2.0, "end": 3.0, "probability": 0.9},
            ]},
            {"text": "goodbye world", "start": 10.0, "end": 12.0, "words": [
                {"word": "goodbye", "start": 10.0, "end": 11.0, "probability": 0.9},
                {"word": "world", "start": 11.0, "end": 12.0, "probability": 0.9},
            ]},
        ]
        onsets = np.array([1.5, 5.0, 5.3, 5.6, 5.9, 6.2, 10.5])
        result = analyze_alignment(lines, segments, onsets, features)
        m = result.line_matches[1]
        assert m.word_timings is not None
        assert len(m.word_timings) == 5
        assert all(t.source == "onset_syllable" for t in m.word_timings)

    def test_split_line_word_timings(self):
        features = _make_features()
        lines = _make_lines(["they caused my extreme anxiety now its chronic"])
        segments = [
            {"text": "they caused my extreme anxiety", "start": 1.0, "end": 3.0, "words": [
                {"word": "they", "start": 1.0, "end": 1.3, "probability": 0.9},
                {"word": "caused", "start": 1.3, "end": 1.6, "probability": 0.9},
                {"word": "my", "start": 1.6, "end": 1.8, "probability": 0.9},
                {"word": "extreme", "start": 1.8, "end": 2.2, "probability": 0.9},
                {"word": "anxiety", "start": 2.2, "end": 3.0, "probability": 0.9},
            ]},
            {"text": "now its chronic", "start": 3.0, "end": 5.0, "words": [
                {"word": "now", "start": 3.0, "end": 3.3, "probability": 0.9},
                {"word": "its", "start": 3.3, "end": 3.5, "probability": 0.9},
                {"word": "chronic", "start": 3.5, "end": 5.0, "probability": 0.9},
            ]},
        ]
        result = analyze_alignment(lines, segments, None, features)
        m = result.line_matches[0]
        assert m.word_timings is not None
        assert len(m.word_timings) == 8
        assert m.word_timings[0].word == "they"
        assert m.word_timings[0].source == "transcription"
        assert m.word_timings[7].word == "chronic"
        assert m.word_timings[7].source == "transcription"
