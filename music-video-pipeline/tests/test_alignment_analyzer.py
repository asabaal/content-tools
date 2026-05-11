import numpy as np
import pytest

from audio.features import AudioFeatures, BeatInfo
from lyrics.alignment_analyzer import (
    AlignmentAnalysis,
    LineMatch,
    _align_lyrics_to_segments,
    _cluster_onsets,
    _normalize,
    _score_boundary_quality,
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
        )
        d = m.to_dict()
        assert d["transcription_start"] == 1.0
        assert d["is_split"] is True
        assert d["matched_segments"] == [0, 1]
        assert d["word_match_ratio"] == 0.9
        assert d["boundary_quality"] == 0.8


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
