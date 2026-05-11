import numpy as np
import pytest

from audio.analyzer import AudioAnalyzer, PEAKS_PER_SECOND
from audio.features import AudioFeatures, StemFeatures


class TestAudioAnalyzerLoad:
    def test_load_wav(self, sample_wav):
        a = AudioAnalyzer()
        a.load_audio(sample_wav)
        assert a._audio is not None
        assert a._sr > 0

    def test_load_with_offset(self, sample_wav):
        a = AudioAnalyzer()
        a.load_audio(sample_wav, start_time=0.2, end_time=0.8)
        assert a._audio is not None
        loaded_dur = len(a._audio) / a._sr
        assert loaded_dur < 1.0

    def test_load_with_start_only(self, sample_wav):
        a = AudioAnalyzer()
        a.load_audio(sample_wav, start_time=0.5)
        assert a._audio is not None


class TestAudioAnalyzerAnalyze:
    def test_analyze_returns_features(self, sample_wav):
        a = AudioAnalyzer()
        features = a.analyze(sample_wav)
        assert isinstance(features, AudioFeatures)
        assert features.duration > 0
        assert features.sample_rate > 0
        assert features.beats.tempo >= 0
        assert len(features.rms_energy) > 0
        assert len(features.spectral_centroids) > 0
        assert len(features.zero_crossing_rate) > 0

    def test_analyze_rms_normalized(self, sample_wav):
        a = AudioAnalyzer()
        features = a.analyze(sample_wav)
        assert features.rms_energy.max() <= 1.0
        assert features.rms_energy.min() >= 0.0

    def test_analyze_spectral_normalized(self, sample_wav):
        a = AudioAnalyzer()
        features = a.analyze(sample_wav)
        assert features.spectral_centroids.max() <= 1.0

    def test_analyze_no_audio_raises(self):
        a = AudioAnalyzer()
        with pytest.raises(ValueError, match="No audio loaded"):
            a.analyze()

    def test_analyze_with_path_loads_first(self, sample_wav):
        a = AudioAnalyzer()
        features = a.analyze(sample_wav)
        assert a._audio is not None
        assert features.duration > 0

    def test_analyze_beat_confidence_single_beat(self, tmp_path):
        import soundfile as sf
        sr = 22050
        sig = np.zeros(int(sr * 0.5), dtype=np.float32)
        sig[0:100] = 0.5 * np.sin(2 * np.pi * 440 * np.arange(100) / sr).astype(np.float32)
        p = tmp_path / "short.wav"
        sf.write(str(p), sig, sr)
        a = AudioAnalyzer()
        features = a.analyze(p)
        assert features.duration > 0

    def test_analyze_stores_hop_and_fft(self, sample_wav):
        a = AudioAnalyzer(hop_length=256, n_fft=1024)
        features = a.analyze(sample_wav)
        assert features.hop_length == 256
        assert features.n_fft == 1024

    def test_analyze_with_midi_tempo(self, sample_wav):
        a = AudioAnalyzer()
        features = a.analyze(sample_wav)
        features.midi_tempo = 103.8
        assert features.midi_tempo == 103.8


class TestAudioAnalyzerStems:
    def test_analyze_stem(self, sample_stem_wav):
        a = AudioAnalyzer()
        result = a.analyze_stem(sample_stem_wav, "lead_vocals", "Lead Vocals")
        assert isinstance(result, StemFeatures)
        assert result.stem_type == "lead_vocals"
        assert result.name == "Lead Vocals"
        assert result.energy >= 0.0
        assert result.onset_count >= 0


class TestAudioAnalyzerWaveforms:
    def test_generate_waveforms(self, sample_wav):
        a = AudioAnalyzer()
        a.load_audio(sample_wav)
        peaks, duration = a.generate_waveforms()
        expected = int(duration * PEAKS_PER_SECOND)
        assert len(peaks) == expected
        assert duration > 0

    def test_waveform_peaks_range(self, sample_wav):
        a = AudioAnalyzer()
        a.load_audio(sample_wav)
        peaks, _ = a.generate_waveforms()
        for p in peaks:
            assert 0.0 <= p <= 1.0

    def test_generate_waveforms_no_audio_raises(self):
        a = AudioAnalyzer()
        with pytest.raises(ValueError, match="No audio loaded"):
            a.generate_waveforms()

    def test_waveform_peak_count(self, sample_wav_with_beats):
        a = AudioAnalyzer()
        a.load_audio(sample_wav_with_beats)
        peaks, duration = a.generate_waveforms()
        assert len(peaks) == int(duration * PEAKS_PER_SECOND)


class TestAudioAnalyzerVocalOnsets:
    def test_extract_vocal_onsets(self, sample_stem_wav):
        a = AudioAnalyzer()
        onsets = a.extract_vocal_onsets(sample_stem_wav)
        assert isinstance(onsets, np.ndarray)
        assert len(onsets) >= 0
        if len(onsets) > 0:
            assert onsets[0] >= 0.0

    def test_extract_vocal_onsets_returns_float(self, sample_stem_wav):
        a = AudioAnalyzer()
        onsets = a.extract_vocal_onsets(sample_stem_wav)
        assert onsets.dtype == float


class TestAudioAnalyzerTranscription:
    def test_transcribe_vocal_stem(self, sample_stem_wav):
        a = AudioAnalyzer()
        result = a.transcribe_vocal_stem(sample_stem_wav, model_size="tiny")
        assert "segments" in result
        assert "words" in result
        assert "language" in result
        assert "duration" in result
        assert isinstance(result["segments"], list)
        assert isinstance(result["words"], list)

    def test_transcription_word_format(self, sample_stem_wav):
        a = AudioAnalyzer()
        result = a.transcribe_vocal_stem(sample_stem_wav, model_size="tiny")
        for w in result["words"]:
            assert "word" in w
            assert "start" in w
            assert "end" in w
            assert "probability" in w

    def test_transcription_segment_format(self, sample_stem_wav):
        a = AudioAnalyzer()
        result = a.transcribe_vocal_stem(sample_stem_wav, model_size="tiny")
        for seg in result["segments"]:
            assert "start" in seg
            assert "end" in seg
            assert "text" in seg
            assert "words" in seg
    def test_confidence_with_multiple_beats(self, tmp_path):
        import soundfile as sf
        sr = 22050
        dur = 4.0
        t = np.linspace(0, dur, int(sr * dur), endpoint=False, dtype=np.float32)
        sig = np.zeros_like(t)
        for beat in np.arange(0, dur, 0.5):
            idx = int(beat * sr)
            if idx + 300 < len(sig):
                env = np.exp(-np.arange(300) / (sr * 0.015)).astype(np.float32)
                sig[idx:idx + 300] += env * 0.8 * np.sin(2 * np.pi * 880 * np.arange(300) / sr).astype(np.float32)
        p = tmp_path / "beats.wav"
        sf.write(str(p), sig, sr)
        a = AudioAnalyzer()
        features = a.analyze(p)
        assert features.beats.confidence > 0
        assert len(features.beats.times) > 1

    def test_waveform_empty_chunk(self, tmp_path):
        import soundfile as sf
        sr = 22050
        sig = np.array([0.1], dtype=np.float32)
        p = tmp_path / "tiny.wav"
        sf.write(str(p), sig, sr)
        a = AudioAnalyzer()
        a.load_audio(p)
        peaks, dur = a.generate_waveforms()
        assert dur > 0
        assert isinstance(peaks, list)
