import numpy as np
import pytest

from audio.features import BeatInfo, FrequencyBands, AudioFeatures, StemFeatures


class TestBeatInfo:
    def test_get_nearest_beat(self):
        beats = BeatInfo(times=np.array([1.0, 2.0, 3.0]), tempo=120.0, confidence=0.9)
        t, idx = beats.get_nearest_beat(1.7)
        assert t == 2.0
        assert idx == 1

    def test_get_nearest_beat_empty(self):
        beats = BeatInfo(times=np.array([]), tempo=0.0, confidence=0.0)
        t, idx = beats.get_nearest_beat(5.0)
        assert t == 0.0
        assert idx == 0

    def test_get_nearest_beat_exact(self):
        beats = BeatInfo(times=np.array([1.0, 2.0, 3.0]), tempo=120.0, confidence=0.9)
        t, idx = beats.get_nearest_beat(2.0)
        assert t == 2.0
        assert idx == 1

    def test_is_on_beat_true(self):
        beats = BeatInfo(times=np.array([1.0, 2.0, 3.0]), tempo=120.0, confidence=0.9)
        assert beats.is_on_beat(1.03, tolerance=0.05)

    def test_is_on_beat_false(self):
        beats = BeatInfo(times=np.array([1.0, 2.0, 3.0]), tempo=120.0, confidence=0.9)
        assert not beats.is_on_beat(1.5, tolerance=0.05)

    def test_is_on_beat_empty(self):
        beats = BeatInfo(times=np.array([]), tempo=0.0, confidence=0.0)
        assert not beats.is_on_beat(1.0)

    def test_to_dict(self):
        beats = BeatInfo(times=np.array([1.0, 2.0]), tempo=120.0, confidence=0.9)
        d = beats.to_dict()
        assert d["times"] == [1.0, 2.0]
        assert d["tempo"] == 120.0
        assert d["confidence"] == 0.9


class TestFrequencyBands:
    def test_get_dominant_band_bass(self):
        fb = FrequencyBands(bass=0.8, low_mid=0.2, mid=0.1, high_mid=0.05, high=0.02)
        assert fb.get_dominant_band() == "bass"

    def test_get_dominant_band_high(self):
        fb = FrequencyBands(bass=0.1, low_mid=0.2, mid=0.1, high_mid=0.05, high=0.9)
        assert fb.get_dominant_band() == "high"

    def test_get_energy_level(self):
        fb = FrequencyBands(bass=0.5, low_mid=0.5, mid=0.5, high_mid=0.5, high=0.5)
        assert fb.get_energy_level() == 0.5

    def test_get_energy_level_capped_at_1(self):
        fb = FrequencyBands(bass=1.0, low_mid=1.0, mid=1.0, high_mid=1.0, high=1.0)
        assert fb.get_energy_level() == 1.0


class TestStemFeatures:
    def test_to_dict(self):
        sf = StemFeatures(stem_type="drums", name="Drums", energy=0.7, onset_count=50)
        d = sf.to_dict()
        assert d["stem_type"] == "drums"
        assert d["name"] == "Drums"
        assert d["energy"] == 0.7
        assert d["onset_count"] == 50


def _make_features(duration=10.0, sr=22050, beat_times=None, onset_times=None, rms=None, centroids=None, zcr=None):
    if beat_times is None:
        beat_times = np.array([0.5, 1.0, 1.5])
    if onset_times is None:
        onset_times = np.array([0.5, 1.0])
    n_frames = 10
    return AudioFeatures(
        duration=duration,
        sample_rate=sr,
        beats=BeatInfo(times=beat_times, tempo=120.0, confidence=0.9),
        onset_times=onset_times,
        rms_energy=rms if rms is not None else np.linspace(0.1, 0.9, n_frames),
        spectral_centroids=centroids if centroids is not None else np.linspace(0.2, 0.8, n_frames),
        zero_crossing_rate=zcr if zcr is not None else np.linspace(0.05, 0.15, n_frames),
        hop_length=512,
        n_fft=2048,
    )


class TestAudioFeatures:
    def test_frame_rate(self):
        f = _make_features()
        assert f.frame_rate > 0

    def test_frame_rate_zero_duration(self):
        f = _make_features(duration=0.0)
        assert f.frame_rate == 0.0

    def test_get_features_at_time(self):
        f = _make_features()
        result = f.get_features_at_time(0.5)
        assert "rms_energy" in result
        assert "spectral_centroid" in result
        assert "zero_crossing_rate" in result
        assert "is_onset" in result
        assert "on_beat" in result

    def test_get_features_at_time_clamps(self):
        f = _make_features()
        result = f.get_features_at_time(999.0)
        assert "rms_energy" in result

    def test_get_features_zero_duration(self):
        f = _make_features(duration=0.0)
        result = f.get_features_at_time(1.0)
        assert result["rms_energy"] == 0.0
        assert result["is_onset"] is False
        assert result["on_beat"] is False

    def test_is_onset_true(self):
        f = _make_features(onset_times=np.array([1.0]))
        result = f.get_features_at_time(1.0)
        assert result["is_onset"] is True

    def test_is_onset_false(self):
        f = _make_features(onset_times=np.array([5.0]))
        result = f.get_features_at_time(1.0)
        assert result["is_onset"] is False

    def test_is_onset_empty(self):
        f = _make_features(onset_times=np.array([]))
        result = f.get_features_at_time(1.0)
        assert result["is_onset"] is False

    def test_to_dict(self):
        f = _make_features()
        d = f.to_dict()
        assert d["duration"] == 10.0
        assert d["sample_rate"] == 22050
        assert d["bpm"] == 120.0
        assert d["beat_confidence"] == 0.9
        assert isinstance(d["beat_times"], list)
        assert isinstance(d["rms_energy"], list)
        assert d["hop_length"] == 512
        assert d["n_fft"] == 2048
        assert d["frame_rate"] == f.frame_rate

    def test_to_dict_with_midi_tempo(self):
        f = _make_features()
        f.midi_tempo = 103.8
        d = f.to_dict()
        assert d["midi_tempo"] == 103.8

    def test_to_dict_without_midi_tempo(self):
        f = _make_features()
        d = f.to_dict()
        assert "midi_tempo" not in d

    def test_to_dict_with_stem_features(self):
        f = _make_features()
        f.stem_features = [StemFeatures(stem_type="drums", name="Drums", energy=0.5)]
        d = f.to_dict()
        assert "stem_features" in d
        assert len(d["stem_features"]) == 1
        assert d["stem_features"][0]["stem_type"] == "drums"

    def test_to_dict_without_stem_features(self):
        f = _make_features()
        d = f.to_dict()
        assert "stem_features" not in d

    def test_default_stem_features_none(self):
        f = _make_features()
        assert f.stem_features is None

    def test_default_midi_tempo_none(self):
        f = _make_features()
        assert f.midi_tempo is None
