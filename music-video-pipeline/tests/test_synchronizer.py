import json
from pathlib import Path

import numpy as np
import pytest

from audio.features import AudioFeatures, BeatInfo
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
        features = _make_features(onset_times=[10.0, 20.0])
        lines = _make_lines(["hello world"], start=0.0, dur=3.0)
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
