import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from audio.features import AudioFeatures, BeatInfo
from lyrics.alignment_analyzer import AlignmentAnalysis, LineMatch, WordTiming
from lyrics.parser import LyricLine, LyricParser, LyricSection, LyricWord
from lyrics.synchronizer import LyricSynchronizer, SyncResult, SyncedLine, SyncedWord


def _make_features(
    duration: float = 30.0,
    beat_times: list | None = None,
    onset_times: list | None = None,
    tempo: float = 120.0,
) -> AudioFeatures:
    bt = np.array(beat_times if beat_times is not None else [0.0, 0.5, 1.0, 1.5, 2.0], dtype=float)
    ot = np.array(onset_times if onset_times is not None else [0.0, 0.5, 1.0, 1.5, 2.0], dtype=float)
    n_frames = 100
    return AudioFeatures(
        duration=duration,
        sample_rate=22050,
        beats=BeatInfo(times=bt, tempo=tempo, confidence=0.9),
        onset_times=ot,
        rms_energy=np.zeros(n_frames),
        spectral_centroids=np.zeros(n_frames),
        zero_crossing_rate=np.zeros(n_frames),
    )


def _make_lines(texts: list[str], start: float = 0.0, dur: float = 3.0) -> list[LyricLine]:
    lines = []
    for i, text in enumerate(texts):
        s = start + i * dur
        e = s + dur
        words = [LyricWord(text=w, start=s, end=e) for w in text.split()]
        lines.append(LyricLine(index=i, text=text, start=s, end=e, words=words))
    return lines


class TestSyncedWord:
    def test_duration(self):
        w = SyncedWord(text="hello", start=1.0, end=1.5)
        assert w.duration == 0.5

    def test_to_dict(self):
        w = SyncedWord(text="hello", start=1.0, end=1.5, source="onset")
        d = w.to_dict()
        assert d == {"text": "hello", "start": 1.0, "end": 1.5, "source": "onset"}

    def test_default_source(self):
        w = SyncedWord(text="x", start=0.0, end=1.0)
        assert w.source == "interpolated"


class TestSyncedLine:
    def test_duration(self):
        line = SyncedLine(text="test", start=1.0, end=3.0)
        assert line.duration == 2.0

    def test_to_dict_no_section(self):
        line = SyncedLine(text="test", start=1.0, end=3.0, alignment_confidence=0.8)
        d = line.to_dict()
        assert "section" not in d
        assert d["alignment_confidence"] == 0.8

    def test_to_dict_with_section(self):
        sec = LyricSection(raw_marker="Verse", section_type="verse")
        line = SyncedLine(text="test", start=0.0, end=1.0, section=sec, alignment_confidence=1.0)
        d = line.to_dict()
        assert d["section"]["section_type"] == "verse"

    def test_empty_words(self):
        line = SyncedLine(text="", start=0.0, end=1.0)
        assert line.words == []


class TestSyncResult:
    def test_to_dict(self):
        words = [SyncedWord(text="hi", start=0.0, end=0.5, source="onset")]
        lines = [SyncedLine(text="hi", start=0.0, end=0.5, words=words, alignment_confidence=1.0)]
        result = SyncResult(lines=lines, source="midi", avg_confidence=1.0)
        d = result.to_dict()
        assert d["source"] == "midi"
        assert len(d["lines"]) == 1
        assert d["avg_confidence"] == 1.0

    def test_save(self, tmp_path):
        result = SyncResult(lines=[], source="full_mix", avg_confidence=0.0)
        path = tmp_path / "sub" / "lyrics_synced.json"
        result.save(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["source"] == "full_mix"

    def test_save_creates_dirs(self, tmp_path):
        result = SyncResult(lines=[], source="full_mix")
        path = tmp_path / "a" / "b" / "c" / "out.json"
        result.save(path)
        assert path.exists()


class TestLyricSynchronizer:
    def test_basic_synchronize(self):
        features = _make_features(onset_times=[0.5, 1.0, 1.5, 2.0, 2.5])
        lines = _make_lines(["hello world", "foo bar baz"])
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        assert result.source == "full_mix"
        assert len(result.lines) == 2

    def test_synchronize_snap_to_beats(self):
        beat_times = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5]
        features = _make_features(beat_times=beat_times, onset_times=[])
        lines = _make_lines(["hello world"], start=0.1, dur=3.0)
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize(snap_to_beats=True, snap_to_onsets=False)
        assert result.lines[0].start == 0.0
        assert result.lines[0].end == 3.0

    def test_no_beat_snap_when_disabled(self):
        beat_times = [0.0, 0.5, 1.0]
        features = _make_features(beat_times=beat_times, onset_times=[])
        lines = _make_lines(["hello world"], start=0.1, dur=3.0)
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize(snap_to_beats=False, snap_to_onsets=False)
        assert result.lines[0].start == 0.1

    def test_beat_snap_tolerance(self):
        beat_times = [0.0, 1.0]
        features = _make_features(beat_times=beat_times, onset_times=[])
        lines = _make_lines(["hello"], start=0.3, dur=3.0)
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize(snap_to_beats=True, snap_to_onsets=False)
        assert result.lines[0].start == 0.3

    def test_midi_source(self):
        features = _make_features(onset_times=[0.5])
        lines = _make_lines(["hello world"])
        midi_starts = np.array([0.0, 0.5, 1.0, 1.5])
        syncer = LyricSynchronizer(lines, features, midi_note_starts=midi_starts)
        result = syncer.synchronize()
        assert result.source == "midi"

    def test_vocal_stem_source(self):
        features = _make_features(onset_times=[0.5])
        lines = _make_lines(["hello world"])
        vocal_onsets = np.array([0.0, 0.5, 1.0])
        syncer = LyricSynchronizer(lines, features, vocal_onset_times=vocal_onsets)
        result = syncer.synchronize()
        assert result.source == "vocal_stem"

    def test_empty_lyrics(self):
        features = _make_features()
        syncer = LyricSynchronizer([], features)
        result = syncer.synchronize()
        assert result.lines == []
        assert result.avg_confidence == 0.0

    def test_empty_text_line_skipped(self):
        features = _make_features()
        lines = [LyricLine(index=0, text="", start=0.0, end=3.0, words=[])]
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        assert result.lines == []

    def test_whitespace_only_line_skipped(self):
        features = _make_features()
        lines = [LyricLine(index=0, text="   ", start=0.0, end=3.0, words=[])]
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        assert result.lines == []

    def test_more_onsets_than_words(self):
        onsets = [0.5, 0.8, 1.1, 1.4, 1.7]
        features = _make_features(onset_times=onsets)
        lines = _make_lines(["hi there"], start=0.4, dur=2.0)
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        words = result.lines[0].words
        assert len(words) == 2
        assert words[0].source == "onset"
        assert words[1].source == "onset"

    def test_fewer_onsets_than_words(self):
        onsets = [0.5, 1.0]
        features = _make_features(onset_times=onsets)
        lines = _make_lines(["one two three four"], start=0.3, dur=2.0)
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        words = result.lines[0].words
        assert len(words) == 4

    def test_no_onsets_in_line_range(self):
        features = _make_features(duration=30.0, onset_times=[10.0, 20.0])
        lines = [LyricLine(index=0, text="hello world", start=5.0, end=8.0, words=[LyricWord(text="hello", start=5.0, end=6.5), LyricWord(text="world", start=6.5, end=8.0)])]
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        words = result.lines[0].words
        assert all(w.source == "interpolated" for w in words)

    def test_confidence_all_onset(self):
        onsets = [0.0, 0.5, 1.0, 1.5]
        features = _make_features(onset_times=onsets)
        lines = _make_lines(["a b c"], start=0.0, dur=2.0)
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        assert result.lines[0].alignment_confidence == 1.0

    def test_confidence_all_interpolated(self):
        features = _make_features(onset_times=[])
        lines = _make_lines(["a b c"])
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        assert result.lines[0].alignment_confidence == 0.0

    def test_confidence_mixed(self):
        onsets = [0.5, 1.5]
        features = _make_features(onset_times=onsets)
        lines = _make_lines(["a b c d"], start=0.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        conf = result.lines[0].alignment_confidence
        assert 0.0 < conf < 1.0

    def test_section_preserved(self):
        features = _make_features(onset_times=[])
        sec = LyricSection(raw_marker="Verse", section_type="verse")
        lines = [LyricLine(index=0, text="hello", start=0.0, end=3.0, words=[LyricWord(text="hello", start=0.0, end=3.0)], section=sec)]
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        assert result.lines[0].section.section_type == "verse"

    def test_end_before_start_fixed(self):
        features = _make_features(onset_times=[])
        lines = [LyricLine(index=0, text="hello", start=5.0, end=3.0, words=[LyricWord(text="hello", start=5.0, end=3.0)])]
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize(snap_to_beats=False)
        assert result.lines[0].end > result.lines[0].start

    def test_empty_words_list(self):
        features = _make_features(onset_times=[0.5])
        lines = [LyricLine(index=0, text="hello", start=0.0, end=3.0, words=[])]
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        assert result.lines[0].words == []

    def test_avg_confidence_multiple_lines(self):
        onsets = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
        features = _make_features(onset_times=onsets)
        lines = _make_lines(["a b", "c d"], start=0.0, dur=2.0)
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        assert 0.0 < result.avg_confidence <= 1.0

    def test_vocal_onset_label(self):
        vocal_onsets = np.array([0.5, 1.0, 1.5])
        features = _make_features(onset_times=[0.5])
        lines = _make_lines(["a b c"], start=0.0, dur=2.0)
        syncer = LyricSynchronizer(lines, features, vocal_onset_times=vocal_onsets)
        result = syncer.synchronize()
        assert any(w.source == "vocal_onset" for w in result.lines[0].words)

    def test_midi_onset_label(self):
        midi_starts = np.array([0.5, 1.0, 1.5])
        features = _make_features(onset_times=[0.5])
        lines = _make_lines(["a b c"], start=0.0, dur=2.0)
        syncer = LyricSynchronizer(lines, features, midi_note_starts=midi_starts)
        result = syncer.synchronize()
        assert any(w.source == "midi" for w in result.lines[0].words)

    def test_interpolate_words_empty(self):
        features = _make_features()
        syncer = LyricSynchronizer([], features)
        result = syncer._interpolate_words([], 0.0, 1.0, "interp")
        assert result == []

    def test_no_snap_empty_beats(self):
        features = _make_features(beat_times=[], onset_times=[])
        lines = _make_lines(["hello"])
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize(snap_to_beats=True, snap_to_onsets=False)
        assert result.lines[0].start == 0.0
        assert result.lines[0].end == 3.0

    def test_word_end_capped_at_line_end(self):
        onsets = [0.5, 1.0, 1.5]
        features = _make_features(onset_times=onsets)
        lines = _make_lines(["a b"], start=0.3, dur=1.0)
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        for w in result.lines[0].words:
            assert w.end <= result.lines[0].end + 0.01

    def test_onset_word_end_before_start(self):
        onsets = [1.0, 0.5, 2.0]
        features = _make_features(onset_times=onsets)
        lines = _make_lines(["a b c"], start=0.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize()
        for w in result.lines[0].words:
            assert w.end > w.start

    def test_snap_empty_beats_internal(self):
        features = _make_features(beat_times=[], onset_times=[])
        lines = _make_lines(["hello"])
        syncer = LyricSynchronizer(lines, features)
        assert syncer._snap_to_nearest_beat(5.0) == 5.0

    def test_full_integration_with_parser(self, tmp_path):
        srt_content = "1\n00:00:01,000 --> 00:00:03,000\nHello world test\n\n2\n00:00:03,500 --> 00:00:06,000\nSecond line here\n"
        lyrics_file = tmp_path / "test.srt"
        lyrics_file.write_text(srt_content, encoding="utf-8")

        parser = LyricParser()
        parsed = parser.parse_file(lyrics_file)

        features = _make_features(
            duration=10.0,
            beat_times=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0],
            onset_times=[1.0, 1.5, 2.0, 2.5, 3.5, 4.0, 4.5, 5.0, 5.5],
        )

        syncer = LyricSynchronizer(parsed.lines, features)
        result = syncer.synchronize()

        assert len(result.lines) == 2
        assert result.lines[0].text == "Hello world test"
        assert result.lines[1].text == "Second line here"
        assert result.avg_confidence > 0.0

        out_path = tmp_path / "lyrics_synced.json"
        result.save(out_path)
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert data["source"] == "full_mix"
        assert len(data["lines"]) == 2


class TestNaiveTimingDetection:
    def test_detects_naive_uniform_duration(self):
        features = _make_features(onset_times=[1.0, 2.0])
        lines = _make_lines(["a b", "c d"], start=0.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features)
        assert syncer._has_naive_timing(lines) is True

    def test_detects_naive_start_at_zero(self):
        features = _make_features(onset_times=[1.0, 2.0])
        lines = _make_lines(["a b", "c d"], start=0.0, dur=2.5)
        syncer = LyricSynchronizer(lines, features)
        assert syncer._has_naive_timing(lines) is True

    def test_not_naive_when_first_line_has_offset(self):
        features = _make_features(onset_times=[1.0, 2.0])
        lines = _make_lines(["a b", "c d"], start=5.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features)
        assert syncer._has_naive_timing(lines) is False

    def test_empty_lines(self):
        features = _make_features()
        syncer = LyricSynchronizer([], features)
        assert syncer._has_naive_timing([]) is False

    def test_detects_exact_3s_duration(self):
        features = _make_features(onset_times=[1.0])
        lines = _make_lines(["a", "b", "c"], start=0.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features)
        assert syncer._has_naive_timing(lines) is True

    def test_detects_zero_durations(self):
        features = _make_features(onset_times=[1.0])
        lines = [
            LyricLine(index=0, text="a", start=0.0, end=0.0, words=[]),
            LyricLine(index=1, text="b", start=0.0, end=0.0, words=[]),
        ]
        syncer = LyricSynchronizer(lines, features)
        assert syncer._has_naive_timing(lines) is True

    def test_not_naive_with_varied_durations(self):
        features = _make_features(onset_times=[1.0])
        lines = [
            LyricLine(index=0, text="short", start=0.0, end=1.0, words=[LyricWord(text="short", start=0.0, end=1.0)]),
            LyricLine(index=1, text="longer line here", start=1.0, end=4.0, words=[LyricWord(text="longer", start=1.0, end=4.0)]),
        ]
        syncer = LyricSynchronizer(lines, features)
        assert syncer._has_naive_timing(lines) is False


class TestClusterOnsets:
    def test_basic_clustering(self):
        features = _make_features(onset_times=[])
        syncer = LyricSynchronizer([], features)
        onsets = np.array([0.5, 0.6, 0.7, 2.0, 2.1, 2.2, 5.0, 5.1])
        clusters = syncer._cluster_onsets(onsets)
        assert len(clusters) == 3

    def test_single_onset(self):
        features = _make_features(onset_times=[])
        syncer = LyricSynchronizer([], features)
        onsets = np.array([1.0])
        clusters = syncer._cluster_onsets(onsets)
        assert len(clusters) == 1
        assert clusters[0][0] == 1.0

    def test_empty_onsets(self):
        features = _make_features(onset_times=[])
        syncer = LyricSynchronizer([], features)
        clusters = syncer._cluster_onsets(np.array([]))
        assert clusters == []

    def test_all_same_cluster(self):
        features = _make_features(onset_times=[])
        syncer = LyricSynchronizer([], features)
        onsets = np.array([1.0, 1.1, 1.2, 1.3, 1.4])
        clusters = syncer._cluster_onsets(onsets)
        assert len(clusters) == 1

    def test_each_onset_own_cluster(self):
        features = _make_features(onset_times=[])
        syncer = LyricSynchronizer([], features)
        onsets = np.array([1.0, 1.1, 5.0, 5.1, 10.0, 10.1])
        clusters = syncer._cluster_onsets(onsets)
        assert len(clusters) == 3


class TestMapLinesToClusters:
    def test_exact_match(self):
        features = _make_features(onset_times=[0.0, 1.0, 3.0, 4.0, 6.0, 7.0])
        lines = _make_lines(["a b", "c d", "e f"])
        syncer = LyricSynchronizer(lines, features, vocal_onset_times=features.onset_times)
        clusters = [(0.0, 2.0), (3.0, 5.0), (6.0, 8.0)]
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        assert len(result) == 3
        for start, end in result:
            assert end > start

    def test_more_clusters_than_lines(self):
        features = _make_features(duration=20.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        clusters = [(0.0, 2.0), (2.5, 4.0), (4.5, 6.0), (6.5, 8.0), (8.5, 10.0)]
        lines = _make_lines(["a b c", "d e f"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        assert len(result) == 2

    def test_fewer_clusters_than_lines(self):
        features = _make_features(duration=20.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        clusters = [(0.0, 4.0), (5.0, 9.0)]
        lines = _make_lines(["a", "b", "c", "d"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        assert len(result) == 4

    def test_split_produces_valid_ranges(self):
        features = _make_features(duration=20.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        clusters = [(0.0, 3.0)]
        lines = _make_lines(["a", "b", "c"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        assert len(result) == 3
        for start, end in result:
            assert end > start

    def test_result_capped_at_duration(self):
        features = _make_features(duration=10.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        clusters = [(0.0, 3.0), (4.0, 8.0), (9.0, 15.0)]
        lines = _make_lines(["a b c", "d e f"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        assert result[-1][1] <= 10.0

    def test_all_results_have_min_duration(self):
        features = _make_features(duration=20.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        clusters = [(0.0, 1.0), (10.0, 11.0), (15.0, 16.0)]
        lines = _make_lines(["a", "b", "c"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        for start, end in result:
            assert end - start >= 0.5

    def test_empty_clusters_returns_min_duration(self):
        features = _make_features(duration=20.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        lines = _make_lines(["a", "b"])
        result = syncer._assign_clusters_to_lines([], lines, features.onset_times)
        assert len(result) == 2
        for start, end in result:
            assert end > start


class TestRoughAlign:
    def test_rough_align_with_vocal_onsets(self):
        onsets = np.array([2.0, 2.3, 2.6, 5.0, 5.3, 5.6, 8.0, 8.3])
        features = _make_features(duration=15.0, onset_times=[])
        lines = _make_lines(["line one", "line two", "line three"], start=0.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features, vocal_onset_times=onsets)
        result = syncer._rough_align_lines(lines, onsets)

        assert result[0].start == pytest.approx(2.0, abs=0.5)
        assert result[1].start > result[0].end - 2.0
        assert result[2].start > result[1].end - 2.0
        assert all(l.end > l.start for l in result)

    def test_no_change_with_good_timing(self):
        features = _make_features(duration=15.0, onset_times=[])
        lines = [
            LyricLine(index=0, text="hello", start=5.0, end=8.0, words=[LyricWord(text="hello", start=5.0, end=8.0)]),
            LyricLine(index=1, text="world", start=8.5, end=11.0, words=[LyricWord(text="world", start=8.5, end=11.0)]),
        ]
        onsets = np.array([5.0, 8.5])
        syncer = LyricSynchronizer(lines, features)
        assert syncer._has_naive_timing(lines) is False

    def test_empty_onsets_returns_original(self):
        features = _make_features(duration=15.0, onset_times=[])
        lines = _make_lines(["a", "b"])
        syncer = LyricSynchronizer(lines, features)
        result = syncer._rough_align_lines(lines, np.array([]))
        assert result == lines

    def test_skips_empty_lines(self):
        features = _make_features(duration=15.0, onset_times=[])
        onsets = np.array([2.0, 2.5, 6.0, 6.5])
        lines = [
            LyricLine(index=0, text="", start=0.0, end=3.0, words=[]),
            LyricLine(index=1, text="hello world", start=3.0, end=6.0, words=[LyricWord(text="hello", start=3.0, end=6.0)]),
        ]
        syncer = LyricSynchronizer(lines, features, vocal_onset_times=onsets)
        result = syncer._rough_align_lines(lines, onsets)
        assert result[0].text == ""
        assert result[1].start >= 0.0

    def test_assign_clusters_fills_all_lines(self):
        features = _make_features(duration=20.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        clusters = [(0.0, 3.0)]
        lines = _make_lines(["a", "b", "c", "d", "e"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        assert len(result) == 5


class TestTranscriptionAlignment:
    def test_exact_match_segments_to_lines(self):
        features = _make_features(duration=30.0, onset_times=[])
        segments = [
            {"start": 1.0, "end": 4.0, "text": "line one"},
            {"start": 5.0, "end": 8.0, "text": "line two"},
            {"start": 9.0, "end": 12.0, "text": "line three"},
        ]
        lines = _make_lines(["a b", "c d", "e f"], start=0.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features, transcription_segments=segments)
        result = syncer._rough_align_from_transcription(lines)

        assert result[0].start == 1.0
        assert result[0].end == 4.0
        assert result[1].start == 5.0
        assert result[2].start == 9.0

    def test_more_segments_than_lines(self):
        features = _make_features(duration=30.0, onset_times=[])
        segments = [
            {"start": 1.0, "end": 3.0, "text": "a"},
            {"start": 3.5, "end": 5.0, "text": "b"},
            {"start": 5.5, "end": 7.0, "text": "c"},
            {"start": 7.5, "end": 9.0, "text": "d"},
            {"start": 9.5, "end": 12.0, "text": "e"},
        ]
        lines = _make_lines(["line one", "line two"])
        syncer = LyricSynchronizer(lines, features, transcription_segments=segments)
        result = syncer._rough_align_from_transcription(lines)

        assert len(result) == 2
        assert result[0].start == 1.0
        assert result[1].end >= 9.0

    def test_fewer_segments_falls_back_to_onsets(self):
        features = _make_features(duration=30.0, onset_times=[2.0, 2.5, 6.0, 6.5])
        segments = [{"start": 1.0, "end": 3.0, "text": "a"}]
        lines = _make_lines(["a", "b"])
        vocal_onsets = np.array([2.0, 2.5, 6.0, 6.5])
        syncer = LyricSynchronizer(
            lines, features,
            vocal_onset_times=vocal_onsets,
            transcription_segments=segments,
        )
        result = syncer._rough_align_from_transcription(lines)
        assert len(result) == 2

    def test_no_segments_returns_original(self):
        features = _make_features(duration=30.0, onset_times=[])
        lines = _make_lines(["a", "b"])
        syncer = LyricSynchronizer(lines, features, transcription_segments=None)
        result = syncer._rough_align_from_transcription(lines)
        assert result == lines

    def test_empty_segments_returns_original(self):
        features = _make_features(duration=30.0, onset_times=[])
        lines = _make_lines(["a", "b"])
        syncer = LyricSynchronizer(lines, features, transcription_segments=[])
        result = syncer._rough_align_from_transcription(lines)
        assert result == lines

    def test_skips_empty_lines(self):
        features = _make_features(duration=30.0, onset_times=[])
        segments = [
            {"start": 1.0, "end": 4.0, "text": "line one"},
            {"start": 5.0, "end": 8.0, "text": "line two"},
        ]
        lines = [
            LyricLine(index=0, text="", start=0.0, end=3.0, words=[]),
            LyricLine(index=1, text="hello", start=3.0, end=6.0, words=[LyricWord(text="hello", start=3.0, end=6.0)]),
            LyricLine(index=2, text="world", start=6.0, end=9.0, words=[LyricWord(text="world", start=6.0, end=9.0)]),
        ]
        syncer = LyricSynchronizer(lines, features, transcription_segments=segments)
        result = syncer._rough_align_from_transcription(lines)
        assert result[0].text == ""
        assert result[1].start == 1.0
        assert result[2].start == 5.0

    def test_synchronize_uses_transcription_when_available(self):
        features = _make_features(duration=30.0, onset_times=[1.0, 2.0])
        segments = [
            {"start": 1.0, "end": 4.0, "text": "line one"},
            {"start": 5.0, "end": 8.0, "text": "line two"},
        ]
        lines = _make_lines(["a b", "c d"], start=0.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features, transcription_segments=segments)
        result = syncer.synchronize()
        assert result.lines[0].start == pytest.approx(1.0, abs=0.3)
        assert result.lines[1].start == pytest.approx(5.0, abs=0.6)

    def test_merge_transcription_enforces_min_duration(self):
        features = _make_features(duration=30.0, onset_times=[])
        segments = [
            {"start": 1.0, "end": 1.1, "text": "a"},
            {"start": 1.2, "end": 1.3, "text": "b"},
            {"start": 1.4, "end": 1.5, "text": "c"},
        ]
        lines = _make_lines(["x", "y"])
        syncer = LyricSynchronizer(lines, features, transcription_segments=segments)
        result = syncer._merge_transcription_segments(segments, 2)
        for start, end in result:
            assert end - start >= 0.5


class TestSyncedLineToDictExtras:
    def test_to_dict_with_warnings(self):
        line = SyncedLine(text="test", start=0.0, end=1.0, warnings=["gap too large"])
        d = line.to_dict()
        assert d["warnings"] == ["gap too large"]

    def test_to_dict_with_onset_segments(self):
        line = SyncedLine(text="test", start=0.0, end=1.0, onset_segments=[{"start": 0.1}])
        d = line.to_dict()
        assert d["onset_segments"] == [{"start": 0.1}]

    def test_to_dict_with_word_segment_assignments(self):
        line = SyncedLine(text="test", start=0.0, end=1.0, word_segment_assignments=[{"word": "test"}])
        d = line.to_dict()
        assert d["word_segment_assignments"] == [{"word": "test"}]


class TestTranscriptionWordAdjustments:
    def test_transcription_words_adjust_start(self):
        features = _make_features(duration=30.0, onset_times=[])
        segments = [
            {"start": 1.0, "end": 4.0, "text": "hello world"},
            {"start": 5.0, "end": 8.0, "text": "second line"},
        ]
        lines = _make_lines(["hello world", "second line"], start=0.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features, transcription_segments=segments)
        syncer._alignment_result = AlignmentAnalysis(
            line_matches=[
                LineMatch(
                    lyric_index=0, lyric_text="hello world",
                    word_match_ratio=0.9,
                    transcription_start=1.0, transcription_end=4.0,
                    word_timings=[
                        WordTiming(word="hello", start=1.05, end=2.0, source="whisper"),
                        WordTiming(word="world", start=2.05, end=3.5, source="whisper"),
                    ],
                ),
                LineMatch(
                    lyric_index=1, lyric_text="second line",
                    word_match_ratio=0.9,
                    transcription_start=5.0, transcription_end=8.0,
                    word_timings=[
                        WordTiming(word="second", start=5.1, end=6.5, source="whisper"),
                        WordTiming(word="line", start=6.6, end=7.5, source="whisper"),
                    ],
                ),
            ],
            total_lines=2, transcription_segment_count=2,
            exact_matches=2, partial_matches=0, unmatched_lines=0,
            lines_split=0, lines_recovered=0, boundary_avg_quality=0.9,
            recommendation="good", recommendation_reason="",
        )
        result = syncer.synchronize(snap_to_beats=False)
        assert len(result.lines) == 2
        assert any(w.source == "transcription" for w in result.lines[0].words)

    def test_word_start_adjusts_line_start(self):
        features = _make_features(duration=30.0, onset_times=[])
        segments = [{"start": 1.0, "end": 4.0, "text": "hello world"}]
        lines = _make_lines(["hello world"], start=0.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features, transcription_segments=segments)
        syncer._alignment_result = AlignmentAnalysis(
            line_matches=[
                LineMatch(
                    lyric_index=0, lyric_text="hello world",
                    word_match_ratio=0.9,
                    transcription_start=1.0, transcription_end=4.0,
                    word_timings=[
                        WordTiming(word="hello", start=2.0, end=3.0, source="whisper"),
                        WordTiming(word="world", start=3.1, end=3.8, source="whisper"),
                    ],
                ),
            ],
            total_lines=1, transcription_segment_count=1,
            exact_matches=1, partial_matches=0, unmatched_lines=0,
            lines_split=0, lines_recovered=0, boundary_avg_quality=0.9,
            recommendation="good", recommendation_reason="",
        )
        result = syncer.synchronize(snap_to_beats=False)
        assert result.lines[0].start < 2.0

    def test_word_end_adjusts_line_end(self):
        features = _make_features(duration=30.0, onset_times=[])
        segments = [{"start": 1.0, "end": 4.0, "text": "hello world"}]
        lines = _make_lines(["hello world"], start=0.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features, transcription_segments=segments)
        syncer._alignment_result = AlignmentAnalysis(
            line_matches=[
                LineMatch(
                    lyric_index=0, lyric_text="hello world",
                    word_match_ratio=0.9,
                    transcription_start=1.0, transcription_end=4.0,
                    word_timings=[
                        WordTiming(word="hello", start=1.1, end=2.0, source="whisper"),
                        WordTiming(word="world", start=2.1, end=2.5, source="whisper"),
                    ],
                ),
            ],
            total_lines=1, transcription_segment_count=1,
            exact_matches=1, partial_matches=0, unmatched_lines=0,
            lines_split=0, lines_recovered=0, boundary_avg_quality=0.9,
            recommendation="good", recommendation_reason="",
        )
        result = syncer.synchronize(snap_to_beats=False)
        assert result.lines[0].end < 3.0


class TestReconcileBoundaries:
    def test_overlapping_words_reconciled(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        w1 = [SyncedWord(text="a", start=0.0, end=2.5)]
        w2 = [SyncedWord(text="b", start=2.0, end=4.0)]
        lines = [
            SyncedLine(text="a", start=0.0, end=2.5, words=w1),
            SyncedLine(text="b", start=2.0, end=4.0, words=w2),
        ]
        syncer._reconcile_boundaries(lines)
        assert lines[0].end == lines[1].start
        assert lines[0].words[-1].end <= lines[1].words[0].start


class TestFindLowestEnergyPoint:
    def test_with_vocal_waveform_peaks(self):
        features = _make_features(duration=30.0, onset_times=[])
        peaks = [0.5, 0.3, 0.1, 0.2, 0.6, 0.4, 0.8, 0.7, 0.9, 0.5]
        syncer = LyricSynchronizer([], features, vocal_waveform_peaks=peaks, vocal_waveform_pps=10)
        result = syncer._find_lowest_energy_point(0.2, 0.7)
        assert result == pytest.approx(0.2, abs=0.05)

    def test_with_empty_peaks(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features, vocal_waveform_peaks=None)
        result = syncer._find_lowest_energy_point(1.0, 3.0)
        assert result == 2.0

    def test_si_ge_ei_returns_midpoint(self):
        features = _make_features(duration=30.0, onset_times=[])
        peaks = [0.1] * 5
        syncer = LyricSynchronizer([], features, vocal_waveform_peaks=peaks, vocal_waveform_pps=1)
        result = syncer._find_lowest_energy_point(10.0, 20.0)
        assert result == 15.0


class TestCheckVocalStemQuality:
    def test_zero_duration_returns_early(self):
        features = _make_features(duration=0.0, onset_times=[])
        lines = _make_lines(["hello"])
        syncer = LyricSynchronizer(lines, features, vocal_onset_times=np.array([1.0, 2.0]))
        syncer._check_vocal_stem_quality()
        assert syncer._vocal_stem_quality == "ok"

    def test_narrow_coverage_with_good_full_mix(self):
        features = _make_features(duration=30.0, onset_times=np.linspace(0, 29, 60))
        lines = _make_lines(["hello world"] * 5)
        vocal_onsets = np.array([5.0, 5.1, 5.2])
        syncer = LyricSynchronizer(lines, features, vocal_onset_times=vocal_onsets)
        syncer._check_vocal_stem_quality()
        assert syncer._vocal_stem_quality == "degraded"
        assert syncer._effective_onset_source == "full_mix"
        assert syncer.vocal_onset_times is None

    def test_sparse_and_few_onsets(self):
        features = _make_features(duration=30.0, onset_times=np.linspace(0, 29, 60))
        lines = _make_lines(["hello world"] * 20)
        vocal_onsets = np.linspace(5.0, 7.0, 5)
        syncer = LyricSynchronizer(lines, features, vocal_onset_times=vocal_onsets)
        syncer._check_vocal_stem_quality()
        assert syncer._vocal_stem_quality == "degraded"

    def test_sparse_and_few_independent(self):
        features = _make_features(duration=30.0, onset_times=[1.0, 5.0, 10.0, 15.0, 20.0, 25.0, 28.0])
        lines = _make_lines(["hello world"] * 50)
        vocal_onsets = np.linspace(1.0, 28.0, 4)
        syncer = LyricSynchronizer(lines, features, vocal_onset_times=vocal_onsets)
        syncer._check_vocal_stem_quality()
        assert syncer._vocal_stem_quality == "degraded"

    def test_good_vocal_stem_quality(self):
        features = _make_features(duration=30.0, onset_times=[0.5])
        lines = _make_lines(["hello world"])
        vocal_onsets = np.linspace(1.0, 28.0, 40)
        syncer = LyricSynchronizer(lines, features, vocal_onset_times=vocal_onsets)
        syncer._check_vocal_stem_quality()
        assert syncer._vocal_stem_quality == "ok"
        assert syncer._effective_onset_source == "vocal_stem"


class TestRoughAlignFromTranscriptionFallback:
    def test_fewer_segments_analyzer_returns_none_falls_back(self):
        features = _make_features(duration=30.0, onset_times=[2.0, 2.5, 6.0, 6.5])
        segments = [{"start": 1.0, "end": 3.0, "text": "hello"}]
        lines = _make_lines(["hello", "world"])
        vocal_onsets = np.array([2.0, 2.5, 6.0, 6.5])
        syncer = LyricSynchronizer(
            lines, features,
            vocal_onset_times=vocal_onsets,
            transcription_segments=segments,
        )
        with patch("lyrics.alignment_analyzer.analyze_alignment") as mock_aa:
            mock_aa.return_value = AlignmentAnalysis(
                line_matches=[
                    LineMatch(lyric_index=0, lyric_text="hello", word_match_ratio=0.5),
                    LineMatch(lyric_index=1, lyric_text="world", word_match_ratio=0.5),
                ],
                total_lines=2, transcription_segment_count=1,
                exact_matches=0, partial_matches=2, unmatched_lines=0,
                lines_split=0, lines_recovered=0, boundary_avg_quality=0.5,
                recommendation="fair", recommendation_reason="",
            )
            result = syncer._rough_align_from_transcription(lines)
        assert len(result) == 2


class TestAlignViaAnalyzer:
    def test_import_error_returns_none(self):
        features = _make_features(duration=30.0, onset_times=[])
        lines = _make_lines(["hello"])
        syncer = LyricSynchronizer(lines, features, transcription_segments=[{"start": 0, "end": 1}])
        with patch.dict("sys.modules", {"lyrics.alignment_analyzer": None}):
            result = syncer._align_via_analyzer(lines, lines)
        assert result is None

    def test_inverted_timing_fixed(self):
        features = _make_features(duration=30.0, onset_times=[])
        lines = _make_lines(["hello"])
        syncer = LyricSynchronizer(lines, features, transcription_segments=[{"start": 0, "end": 1}])
        with patch("lyrics.alignment_analyzer.analyze_alignment") as mock_aa:
            mock_aa.return_value = AlignmentAnalysis(
                line_matches=[
                    LineMatch(
                        lyric_index=0, lyric_text="hello",
                        transcription_start=5.0, transcription_end=3.0,
                        word_match_ratio=0.9,
                    ),
                ],
                total_lines=1, transcription_segment_count=1,
                exact_matches=1, partial_matches=0, unmatched_lines=0,
                lines_split=0, lines_recovered=0, boundary_avg_quality=0.9,
                recommendation="good", recommendation_reason="",
            )
            result = syncer._align_via_analyzer(lines, lines)
        assert result is not None
        assert result[0][1] > result[0][0]

    def test_no_prior_boundaries_appends_zero_start(self):
        features = _make_features(duration=30.0, onset_times=[])
        lines = _make_lines(["hello"])
        syncer = LyricSynchronizer(lines, features, transcription_segments=[{"start": 0, "end": 1}])
        with patch("lyrics.alignment_analyzer.analyze_alignment") as mock_aa:
            mock_aa.return_value = AlignmentAnalysis(
                line_matches=[
                    LineMatch(
                        lyric_index=0, lyric_text="hello",
                        word_match_ratio=0.1,
                    ),
                ],
                total_lines=1, transcription_segment_count=1,
                exact_matches=0, partial_matches=0, unmatched_lines=1,
                lines_split=0, lines_recovered=0, boundary_avg_quality=0.0,
                recommendation="poor", recommendation_reason="",
            )
            result = syncer._align_via_analyzer(lines, lines)
        assert result is not None
        assert result[0][0] == 0.0

    def test_count_mismatch_returns_none(self):
        features = _make_features(duration=30.0, onset_times=[])
        lines = _make_lines(["hello", "world"])
        syncer = LyricSynchronizer(lines, features, transcription_segments=[{"start": 0, "end": 1}])
        with patch("lyrics.alignment_analyzer.analyze_alignment") as mock_aa:
            mock_aa.return_value = AlignmentAnalysis(
                line_matches=[
                    LineMatch(
                        lyric_index=0, lyric_text="hello",
                        transcription_start=1.0, transcription_end=4.0,
                        word_match_ratio=0.9,
                    ),
                ],
                total_lines=1, transcription_segment_count=1,
                exact_matches=1, partial_matches=0, unmatched_lines=0,
                lines_split=0, lines_recovered=0, boundary_avg_quality=0.9,
                recommendation="good", recommendation_reason="",
            )
            result = syncer._align_via_analyzer(lines, [lines[0], lines[1]])
        assert result is None


class TestEnsureAlignmentResult:
    def test_already_set_returns_early(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features, transcription_segments=[{"start": 0, "end": 1}])
        syncer._alignment_result = MagicMock()
        syncer._ensure_alignment_result()
        assert syncer._alignment_result is not None

    def test_import_error_returns(self):
        features = _make_features(duration=30.0, onset_times=[])
        lines = _make_lines(["hello"])
        syncer = LyricSynchronizer(lines, features, transcription_segments=[{"start": 0, "end": 1}])
        with patch.dict("sys.modules", {"lyrics.alignment_analyzer": None}):
            syncer._ensure_alignment_result()
        assert syncer._alignment_result is None

    def test_empty_lines_returns(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer(
            [LyricLine(index=0, text="", start=0.0, end=3.0, words=[])],
            features,
            transcription_segments=[{"start": 0, "end": 1}],
        )
        syncer._ensure_alignment_result()
        assert syncer._alignment_result is None


class TestSubdivideSharedBoundaries:
    def test_shared_boundaries_subdivided(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        boundaries = [(1.0, 4.0), (1.0, 4.0), (1.0, 4.0)]
        lines = _make_lines(["short", "a bit longer text", "medium length"])
        result = syncer._subdivide_shared_boundaries(boundaries, lines)
        assert len(result) == 3
        assert result[0][0] == 1.0
        for s, e in result:
            assert e > s


class TestAssignClustersEdgeCases:
    def test_single_cluster_short_duration_enforced(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        clusters = [(5.0, 5.1)]
        lines = _make_lines(["a"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        assert result[0][1] - result[0][0] >= 0.5

    def test_multi_cluster_short_duration_enforced(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        clusters = [(0.0, 1.0), (5.0, 5.05)]
        lines = _make_lines(["short", "tiny"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        for s, e in result:
            assert e - s >= 0.5

    def test_result_trimmed_to_n_lines(self):
        features = _make_features(duration=30.0, onset_times=[0.0, 1.0, 2.0, 3.0, 4.0])
        syncer = LyricSynchronizer([], features, vocal_onset_times=features.onset_times)
        clusters = [(0.0, 1.0), (2.0, 3.0), (4.0, 5.0)]
        lines = _make_lines(["a"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        assert len(result) == 1

    def test_result_padded_when_short(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        clusters = [(0.0, 5.0)]
        lines = _make_lines(["a", "b", "c", "d", "e"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        assert len(result) == 5
        for s, e in result:
            assert e > s


class TestGetWhisperMatch:
    def test_idx_beyond_matches(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        syncer._alignment_result = AlignmentAnalysis(
            line_matches=[LineMatch(lyric_index=0, lyric_text="hello", word_match_ratio=0.9)],
            total_lines=1, transcription_segment_count=1,
            exact_matches=1, partial_matches=0, unmatched_lines=0,
            lines_split=0, lines_recovered=0, boundary_avg_quality=0.9,
            recommendation="good", recommendation_reason="",
        )
        assert syncer._get_whisper_match(5) is None

    def test_low_match_ratio(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        syncer._alignment_result = AlignmentAnalysis(
            line_matches=[
                LineMatch(
                    lyric_index=0, lyric_text="hello",
                    word_match_ratio=0.1,
                    word_timings=[WordTiming(word="hello", start=0.0, end=1.0, source="whisper")],
                ),
            ],
            total_lines=1, transcription_segment_count=1,
            exact_matches=0, partial_matches=0, unmatched_lines=1,
            lines_split=0, lines_recovered=0, boundary_avg_quality=0.0,
            recommendation="poor", recommendation_reason="",
        )
        assert syncer._get_whisper_match(0) is None


class TestBuildWordsFromWhisper:
    def test_perfect_match(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        match = MagicMock()
        match.word_timings = [
            WordTiming(word="hello", start=1.0, end=2.0, source="whisper"),
            WordTiming(word="world", start=2.1, end=3.0, source="whisper"),
        ]
        result = syncer._build_words_from_whisper(["hello", "world"], 1.0, 3.0, match)
        assert result is not None
        assert len(result) == 2
        assert result[0].source == "transcription"
        assert result[0].text == "hello"
        assert result[1].text == "world"

    def test_partial_match_with_interpolation(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        match = MagicMock()
        match.word_timings = [
            WordTiming(word="hello", start=1.0, end=2.0, source="whisper"),
        ]
        result = syncer._build_words_from_whisper(["hello", "world"], 1.0, 4.0, match)
        assert result is not None
        assert len(result) == 2
        assert result[0].source == "transcription"
        assert result[1].source == "interpolated"

    def test_empty_word_timings(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        match = MagicMock()
        match.word_timings = []
        result = syncer._build_words_from_whisper(["hello"], 0.0, 1.0, match)
        assert result is None

    def test_unmatched_word_at_start_interpolated(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        match = MagicMock()
        match.word_timings = [
            WordTiming(word="world", start=2.0, end=3.0, source="whisper"),
        ]
        result = syncer._build_words_from_whisper(["hello", "world"], 1.0, 4.0, match)
        assert result is not None
        assert len(result) == 2
        assert result[0].source == "interpolated"
        assert result[1].source == "transcription"

    def test_overlapping_timing_fixed(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        match = MagicMock()
        match.word_timings = [
            WordTiming(word="hello", start=1.0, end=2.5, source="whisper"),
            WordTiming(word="world", start=2.0, end=3.0, source="whisper"),
        ]
        result = syncer._build_words_from_whisper(["hello", "world"], 1.0, 3.0, match)
        assert result is not None
        assert result[1].start >= result[0].end

    def test_end_before_start_fixed(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        match = MagicMock()
        match.word_timings = [
            WordTiming(word="hello", start=1.0, end=0.5, source="whisper"),
        ]
        result = syncer._build_words_from_whisper(["hello"], 0.0, 2.0, match)
        assert result is not None
        assert result[0].end > result[0].start


class TestAlignWordsWhisperPath:
    def test_whisper_match_used_in_align_words(self):
        features = _make_features(duration=30.0, onset_times=[])
        lines = _make_lines(["hello world"], start=0.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features, transcription_segments=[{"start": 0, "end": 1}])
        syncer._alignment_result = AlignmentAnalysis(
            line_matches=[
                LineMatch(
                    lyric_index=0, lyric_text="hello world",
                    word_match_ratio=0.9,
                    transcription_start=0.5, transcription_end=2.5,
                    word_timings=[
                        WordTiming(word="hello", start=0.5, end=1.2, source="whisper"),
                        WordTiming(word="world", start=1.3, end=2.5, source="whisper"),
                    ],
                ),
            ],
            total_lines=1, transcription_segment_count=1,
            exact_matches=1, partial_matches=0, unmatched_lines=0,
            lines_split=0, lines_recovered=0, boundary_avg_quality=0.9,
            recommendation="good", recommendation_reason="",
        )
        result = syncer.synchronize(snap_to_beats=False)
        assert len(result.lines) == 1
        assert any(w.source == "transcription" for w in result.lines[0].words)


class TestTranscriptionOverlapAdjustment:
    def test_previous_line_end_adjusted_on_overlap(self):
        features = _make_features(duration=30.0, onset_times=[])
        segments = [
            {"start": 1.0, "end": 3.0, "text": "first line"},
            {"start": 2.5, "end": 5.0, "text": "second line"},
        ]
        lines = _make_lines(["first line", "second line"], start=0.0, dur=3.0)
        syncer = LyricSynchronizer(lines, features, transcription_segments=segments)
        syncer._alignment_result = AlignmentAnalysis(
            line_matches=[
                LineMatch(
                    lyric_index=0, lyric_text="first line",
                    word_match_ratio=0.9,
                    transcription_start=1.0, transcription_end=3.0,
                    word_timings=[
                        WordTiming(word="first", start=1.0, end=2.0, source="whisper"),
                        WordTiming(word="line", start=2.1, end=2.9, source="whisper"),
                    ],
                ),
                LineMatch(
                    lyric_index=1, lyric_text="second line",
                    word_match_ratio=0.9,
                    transcription_start=2.5, transcription_end=5.0,
                    word_timings=[
                        WordTiming(word="second", start=2.5, end=3.5, source="whisper"),
                        WordTiming(word="line", start=3.6, end=4.5, source="whisper"),
                    ],
                ),
            ],
            total_lines=2, transcription_segment_count=2,
            exact_matches=2, partial_matches=0, unmatched_lines=0,
            lines_split=0, lines_recovered=0, boundary_avg_quality=0.9,
            recommendation="good", recommendation_reason="",
        )
        result = syncer.synchronize(snap_to_beats=False)
        assert len(result.lines) == 2
        assert result.lines[0].end <= result.lines[1].start + 0.01

    def test_word_start_far_from_line_start_adjusted(self):
        features = _make_features(duration=30.0, onset_times=[0.8, 1.5, 3.0, 4.0, 5.0])
        lines = [
            LyricLine(
                index=0, text="hello", start=0.0, end=2.0,
                words=[LyricWord(text="hello", start=0.0, end=2.0)],
            ),
            LyricLine(
                index=1, text="world foo", start=2.0, end=6.0,
                words=[LyricWord(text="world", start=2.0, end=4.0), LyricWord(text="foo", start=4.0, end=6.0)],
            ),
        ]
        syncer = LyricSynchronizer(lines, features)
        result = syncer.synchronize(snap_to_beats=False, snap_to_onsets=True)
        assert len(result.lines) == 2


class TestFindLowestEnergyPointLoop:
    def test_finds_min_in_range(self):
        features = _make_features(duration=30.0, onset_times=[])
        peaks = [0.9, 0.8, 0.3, 0.7, 0.6, 0.5, 0.4, 0.2, 0.1, 0.8]
        syncer = LyricSynchronizer([], features, vocal_waveform_peaks=peaks, vocal_waveform_pps=10)
        result = syncer._find_lowest_energy_point(0.0, 0.8)
        assert result == pytest.approx(0.8, abs=0.01)


class TestFallbackFromTranscription:
    def test_fewer_segments_analyzer_returns_none_falls_to_onsets(self):
        features = _make_features(duration=30.0, onset_times=[2.0, 2.5, 6.0, 6.5])
        segments = [{"start": 1.0, "end": 3.0, "text": "hello"}]
        lines = _make_lines(["hello", "world"])
        vocal_onsets = np.array([2.0, 2.5, 6.0, 6.5])
        syncer = LyricSynchronizer(
            lines, features,
            vocal_onset_times=vocal_onsets,
            transcription_segments=segments,
        )
        with patch("lyrics.alignment_analyzer.analyze_alignment") as mock_aa:
            mock_aa.return_value = AlignmentAnalysis(
                line_matches=[
                    LineMatch(lyric_index=0, lyric_text="hello", word_match_ratio=0.5),
                    LineMatch(lyric_index=1, lyric_text="world", word_match_ratio=0.5),
                ],
                total_lines=2, transcription_segment_count=1,
                exact_matches=0, partial_matches=2, unmatched_lines=0,
                lines_split=0, lines_recovered=0, boundary_avg_quality=0.5,
                recommendation="fair", recommendation_reason="",
            )
            result = syncer._rough_align_from_transcription(lines)
        assert len(result) == 2

    def test_fewer_segments_analyzer_none_falls_to_rough_align(self):
        features = _make_features(duration=30.0, onset_times=[2.0, 2.5, 6.0, 6.5])
        segments = [{"start": 1.0, "end": 3.0, "text": "hello"}]
        lines = _make_lines(["hello", "world"])
        vocal_onsets = np.array([2.0, 2.5, 6.0, 6.5])
        syncer = LyricSynchronizer(
            lines, features,
            vocal_onset_times=vocal_onsets,
            transcription_segments=segments,
        )
        with patch("lyrics.alignment_analyzer.analyze_alignment") as mock_aa:
            mock_aa.return_value = AlignmentAnalysis(
                line_matches=[
                    LineMatch(lyric_index=0, lyric_text="hello", word_match_ratio=0.5),
                ],
                total_lines=1, transcription_segment_count=1,
                exact_matches=0, partial_matches=1, unmatched_lines=0,
                lines_split=0, lines_recovered=0, boundary_avg_quality=0.5,
                recommendation="fair", recommendation_reason="",
            )
            result = syncer._rough_align_from_transcription(lines)
        assert len(result) == 2


class TestAssignClustersEdgeCasesIntegration:
    def test_single_cluster_short_duration(self):
        features = _make_features(duration=30.0, onset_times=[5.0])
        syncer = LyricSynchronizer([], features, vocal_onset_times=np.array([5.0]))
        clusters = [(5.0, 5.05)]
        lines = _make_lines(["a"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        assert result[0][1] - result[0][0] >= 0.5

    def test_multi_cluster_short_duration(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        clusters = [(0.0, 1.0), (10.0, 10.01)]
        lines = _make_lines(["a", "b"])
        onset_times = np.array([0.0, 10.0])
        result = syncer._assign_clusters_to_lines(clusters, lines, onset_times)
        for s, e in result:
            assert e - s >= 0.5

    def test_trim_result_to_n_lines(self):
        features = _make_features(duration=30.0, onset_times=[0.0, 1.0, 2.0, 3.0, 4.0])
        syncer = LyricSynchronizer([], features, vocal_onset_times=features.onset_times)
        clusters = [(0.0, 2.0), (3.0, 5.0)]
        lines = _make_lines(["a"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        assert len(result) == 1

    def test_pad_result_when_short(self):
        features = _make_features(duration=30.0, onset_times=[])
        syncer = LyricSynchronizer([], features)
        clusters = [(0.0, 5.0)]
        lines = _make_lines(["a", "b", "c", "d", "e"])
        result = syncer._assign_clusters_to_lines(clusters, lines, features.onset_times)
        assert len(result) == 5
        for s, e in result:
            assert e > s

    def test_shared_cluster_short_share_enforced(self):
        features = _make_features(duration=10.0, onset_times=[0.0, 0.1, 0.2])
        syncer = LyricSynchronizer([], features, vocal_onset_times=np.array([0.0, 0.1, 0.2]))
        clusters = [(0.0, 0.15)]
        lines = _make_lines(["a", "b", "c"])
        result = syncer._assign_clusters_to_lines(clusters, lines, np.array([0.0, 0.1, 0.2]))
        assert len(result) == 3
