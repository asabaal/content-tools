from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

import numpy as np

from .features import AudioFeatures, BeatInfo, StemFeatures

logger = logging.getLogger(__name__)

PEAKS_PER_SECOND = 100


class AudioAnalyzer:
    def __init__(self, hop_length: int = 512, n_fft: int = 2048):
        self.hop_length = hop_length
        self.n_fft = n_fft
        self._audio: Optional[np.ndarray] = None
        self._sr: Optional[int] = None

    def load_audio(self, audio_path: Union[str, Path], start_time: Optional[float] = None, end_time: Optional[float] = None) -> None:
        import librosa

        audio_path = Path(audio_path)
        logger.info("Loading audio: %s", audio_path)

        offset = start_time if start_time is not None else 0.0
        duration = (end_time - offset) if end_time is not None else None

        if offset > 0 or duration is not None:
            self._audio, self._sr = librosa.load(str(audio_path), sr=None, mono=True, offset=offset, duration=duration)
        else:
            self._audio, self._sr = librosa.load(str(audio_path), sr=None, mono=True)

        dur = len(self._audio) / self._sr
        logger.info("Loaded %.2fs at %dHz", dur, self._sr)

    def analyze(self, audio_path: Optional[Union[str, Path]] = None, start_time: Optional[float] = None, end_time: Optional[float] = None) -> AudioFeatures:
        import librosa

        if audio_path:
            self.load_audio(audio_path, start_time, end_time)
        if self._audio is None:
            raise ValueError("No audio loaded")

        logger.info("Analyzing audio...")

        tempo, beat_frames = librosa.beat.beat_track(y=self._audio, sr=self._sr, hop_length=self.hop_length)
        tempo = float(np.atleast_1d(tempo)[0])
        beat_frames = np.atleast_1d(beat_frames)
        beat_times = librosa.frames_to_time(beat_frames, sr=self._sr, hop_length=self.hop_length)
        beat_times = np.atleast_1d(beat_times).astype(float)

        confidence = 0.0
        if len(beat_times) > 1:
            intervals = np.diff(beat_times)
            valid = intervals[intervals > 0]
            if len(valid) > 0:
                tempo_std = np.std(60.0 / valid)
                confidence = 1.0 - min(tempo_std / 10.0, 1.0)
        beats = BeatInfo(times=beat_times, tempo=tempo, confidence=confidence)

        onset_env = librosa.onset.onset_strength(y=self._audio, sr=self._sr, hop_length=self.hop_length)
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=self._sr, hop_length=self.hop_length, backtrack=True)
        onset_times = librosa.frames_to_time(onset_frames, sr=self._sr, hop_length=self.hop_length)

        rms = librosa.feature.rms(y=self._audio, frame_length=self.n_fft, hop_length=self.hop_length)[0]
        if rms.max() > 0:
            rms = rms / rms.max()

        centroids = librosa.feature.spectral_centroid(y=self._audio, sr=self._sr, hop_length=self.hop_length)[0]
        if centroids.max() > 0:
            centroids = centroids / centroids.max()

        zcr = librosa.feature.zero_crossing_rate(self._audio, frame_length=self.n_fft, hop_length=self.hop_length)[0]

        features = AudioFeatures(
            duration=len(self._audio) / self._sr,
            sample_rate=self._sr,
            beats=beats,
            onset_times=np.asarray(onset_times, dtype=float),
            rms_energy=rms,
            spectral_centroids=centroids,
            zero_crossing_rate=zcr,
            hop_length=self.hop_length,
            n_fft=self.n_fft,
        )

        logger.info("Analysis complete: %d beats, %d onsets, %.1f BPM", len(beat_times), len(onset_times), float(tempo))
        return features

    def extract_vocal_onsets(self, stem_path: Union[str, Path]) -> np.ndarray:
        import librosa

        audio, sr = librosa.load(str(stem_path), sr=None, mono=True)
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=self.hop_length)
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=self.hop_length, backtrack=True)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=self.hop_length)
        return np.asarray(onset_times, dtype=float)

    def transcribe_vocal_stem(self, stem_path: Union[str, Path], model_size: str = "small") -> dict:
        from faster_whisper import WhisperModel

        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(stem_path), word_timestamps=True)

        result = {
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 3),
            "segments": [],
            "words": [],
            "whisper_model": model_size,
        }

        for seg in segments:  # pragma: no cover
            seg_data = {
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text.strip(),
                "words": [],
            }
            for w in seg.words:
                word_data = {
                    "word": w.word.strip(),
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "probability": round(w.probability, 3),
                }
                seg_data["words"].append(word_data)
                result["words"].append(word_data)
            result["segments"].append(seg_data)

        return result

    WHISPER_FALLBACK_ORDER = ["small", "medium", "large-v3"]

    def transcribe_with_fallback(
        self,
        stem_path: Union[str, Path],
        lyrics_lines: Optional[list] = None,
        start_model: str = "small",
    ) -> dict:
        start_idx = self.WHISPER_FALLBACK_ORDER.index(start_model) if start_model in self.WHISPER_FALLBACK_ORDER else 0
        models_to_try = self.WHISPER_FALLBACK_ORDER[start_idx:]

        best_result = None
        best_unmatched = float("inf")
        best_model = None
        all_attempts = []

        for model_size in models_to_try:
            logger.info("Transcribing %s with whisper model: %s", stem_path, model_size)
            result = self.transcribe_vocal_stem(stem_path, model_size=model_size)
            result["whisper_model"] = model_size

            if lyrics_lines is None or not lyrics_lines:
                return result

            unmatched = self._count_unmatched_lines(lyrics_lines, result["segments"])
            all_attempts.append({"model": model_size, "unmatched": unmatched, "segments": len(result["segments"])})

            if unmatched < best_unmatched:
                best_result = result
                best_unmatched = unmatched
                best_model = model_size

            if unmatched == 0:
                break

        if best_result is not None:
            best_result["whisper_model"] = best_model
            if len(all_attempts) > 1:
                best_result["whisper_fallback_attempts"] = all_attempts
            if best_model != models_to_try[0]:
                logger.info("Whisper fallback: %s -> %s (unmatched: %d -> %d)",
                            models_to_try[0], best_model,
                            all_attempts[0]["unmatched"] if all_attempts else -1, best_unmatched)
            return best_result

        return self.transcribe_vocal_stem(stem_path, model_size=models_to_try[0])

    def _count_unmatched_lines(self, lyrics_lines: list, segments: list) -> int:
        if not segments or not lyrics_lines:
            return len(lyrics_lines) if lyrics_lines else 0

        from lyrics.alignment_analyzer import _align_lyrics_to_segments
        from lyrics.parser import LyricLine

        if not isinstance(lyrics_lines[0], LyricLine):
            lyrics_lines = [LyricLine(index=i, text=t, start=0.0, end=0.0, words=[])
                            for i, t in enumerate(lyrics_lines) if t and t.strip()]

        _, match_ratios, _ = _align_lyrics_to_segments(lyrics_lines, segments)
        return sum(1 for r in match_ratios.values() if r <= 0.0)

    def analyze_stem(self, stem_path: Union[str, Path], stem_type: str, name: str) -> StemFeatures:
        import librosa

        audio, sr = librosa.load(str(stem_path), sr=None, mono=True)

        rms = librosa.feature.rms(y=audio, frame_length=self.n_fft, hop_length=self.hop_length)[0]
        energy = float(rms.mean())
        if energy > 0:
            max_rms = float(rms.max())
            if max_rms > 0:
                energy = energy / max_rms

        onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=self.hop_length)
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=self.hop_length, backtrack=True)
        onset_count = len(onset_frames)

        return StemFeatures(stem_type=stem_type, name=name, energy=energy, onset_count=onset_count)

    def _compute_peaks(self, audio: np.ndarray, sr: int) -> tuple[list[float], float]:
        duration = len(audio) / sr
        num_peaks = int(duration * PEAKS_PER_SECOND)
        if num_peaks == 0:
            return [], duration
        samples_per_peak = max(1, len(audio) // num_peaks)

        peaks = []
        for i in range(num_peaks):
            start = i * samples_per_peak
            end = min(start + samples_per_peak, len(audio))
            chunk = audio[start:end]
            peaks.append(round(float(np.max(np.abs(chunk))), 4))

        return peaks, duration

    def generate_waveforms(self) -> tuple[list[float], float]:
        if self._audio is None:
            raise ValueError("No audio loaded")
        return self._compute_peaks(self._audio, self._sr)

    def generate_waveforms_for_file(self, audio_path: Union[str, Path]) -> tuple[list[float], float]:
        import librosa
        audio, sr = librosa.load(str(audio_path), sr=None, mono=True)
        return self._compute_peaks(audio, sr)
