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
        self._whisper_models: dict = {}

    def _get_whisper_model(self, model_size: str):
        if model_size not in self._whisper_models:
            from faster_whisper import WhisperModel
            import ctranslate2
            if ctranslate2.get_cuda_device_count() > 0:
                self._whisper_models.clear()
                try:
                    logger.info("Loading Whisper model: %s (cuda/float16)", model_size)
                    self._whisper_models[model_size] = WhisperModel(
                        model_size, device="cuda", compute_type="float16"
                    )
                except Exception as e:
                    logger.warning("CUDA load failed (%s), falling back to CPU", e)
                    self._whisper_models[model_size] = WhisperModel(
                        model_size, device="cpu", compute_type="int8"
                    )
            else:
                logger.info("Loading Whisper model: %s (cpu/int8)", model_size)
                self._whisper_models[model_size] = WhisperModel(
                    model_size, device="cpu", compute_type="int8"
                )
        return self._whisper_models[model_size]

    def release_models(self) -> None:
        self._whisper_models.clear()

    def release_audio(self) -> None:
        self._audio = None
        self._sr = None

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

    def transcribe_vocal_stem(self, stem_path: Union[str, Path], model_size: str = "small", skip_gap_fill: bool = False) -> dict:
        model = self._get_whisper_model(model_size)
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

        result["segments"] = self._filter_hallucinations(result["segments"], info.language)
        if not skip_gap_fill:
            result["segments"] = self._fill_gaps(result["segments"], str(stem_path), model_size, info.language)
        result["words"] = [w for seg in result["segments"] for w in seg.get("words", [])]

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

        _, match_ratios, _, _ = _align_lyrics_to_segments(lyrics_lines, segments)
        return sum(1 for r in match_ratios.values() if r <= 0.0)

    MIN_GAP_SECONDS = 30
    GAP_PADDING_SECONDS = 2
    MAX_FILL_DURATION = 300

    def _fill_gaps(self, segments: list, stem_path: str, model_size: str, detected_language: str) -> list:
        if not segments:
            return segments

        import librosa
        import soundfile as sf
        import tempfile

        total_duration = librosa.get_duration(path=stem_path)

        gaps = []
        prev_end = segments[0]["end"]
        for i in range(1, len(segments)):
            gap_start = prev_end
            gap_end = segments[i]["start"]
            gap_dur = gap_end - gap_start
            if gap_dur >= self.MIN_GAP_SECONDS:
                gaps.append((gap_start, gap_end, gap_dur))
            prev_end = segments[i]["end"]

        final_gap_dur = total_duration - segments[-1]["end"]
        if final_gap_dur >= self.MIN_GAP_SECONDS:
            gaps.append((segments[-1]["end"], total_duration, final_gap_dur))

        if not gaps:
            return segments

        for gap_start, gap_end, gap_dur in gaps:
            if gap_dur > self.MAX_FILL_DURATION:
                logger.info("Skipping large gap %.1f-%.1f (%.0fs, exceeds max %ds)",
                            gap_start, gap_end, gap_dur, self.MAX_FILL_DURATION)
                continue

            clip_start = max(0, gap_start - self.GAP_PADDING_SECONDS)
            clip_end = min(total_duration, gap_end + self.GAP_PADDING_SECONDS)
            clip_dur = clip_end - clip_start
            clip_audio, sr = librosa.load(
                stem_path, sr=None, mono=True,
                offset=clip_start, duration=clip_dur,
            )

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, clip_audio, sr)
                tmp_path = tmp.name

            del clip_audio

            try:
                logger.info("Re-transcribing gap %.1f-%.1f (%.0fs) from %s",
                            gap_start, gap_end, gap_dur, stem_path)
                gap_result = self.transcribe_vocal_stem(tmp_path, model_size=model_size, skip_gap_fill=True)
                gap_segs = gap_result["segments"]

                gap_segs = self._filter_hallucinations(gap_segs, gap_result.get("language", detected_language))

                for seg in gap_segs:
                    seg["start"] = round(seg["start"] + clip_start, 3)
                    seg["end"] = round(seg["end"] + clip_start, 3)
                    for w in seg.get("words", []):
                        w["start"] = round(w["start"] + clip_start, 3)
                        w["end"] = round(w["end"] + clip_start, 3)

                if gap_segs:
                    logger.info("Gap %.1f-%.1f: found %d new segments", gap_start, gap_end, len(gap_segs))
                    segments.extend(gap_segs)
            except Exception as e:
                logger.warning("Gap re-transcription failed for %.1f-%.1f: %s", gap_start, gap_end, e)
            finally:
                Path(tmp_path).unlink(missing_ok=True)

        segments.sort(key=lambda s: s["start"])
        return segments

    @staticmethod
    def _filter_hallucinations(segments: list, detected_language: str) -> list:
        if not segments:
            return segments

        import re
        cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]')

        def _is_cjk(text: str) -> bool:
            return bool(cjk_pattern.search(text))

        def _has_common_hallucination(text: str) -> bool:
            lower = text.lower().strip()
            hallucinations = [
                "thank you for watching",
                "thank you for listening",
                "subscribe",
                "please subscribe",
                "like and subscribe",
            ]
            return lower in hallucinations

        cjk_count = sum(1 for seg in segments if _is_cjk(seg["text"]))
        latin_count = sum(1 for seg in segments if not _is_cjk(seg["text"]) and seg["text"].strip())
        majority_cjk = cjk_count > latin_count

        text_groups: dict[str, list[int]] = {}
        for i, seg in enumerate(segments):
            text = seg["text"].strip()
            if not text:
                continue
            text_groups.setdefault(text, []).append(i)

        repeated_texts = {text: indices for text, indices in text_groups.items() if len(indices) >= 4}

        kept = []
        for i, seg in enumerate(segments):
            text = seg["text"].strip()
            discard = False

            if _is_cjk(text) and (not majority_cjk or latin_count > 0):
                discard = True
                logger.info("Filtered CJK segment at %.1f: \"%s\"", seg["start"], text)

            if not discard and _has_common_hallucination(text):
                discard = True
                logger.info("Filtered common hallucination at %.1f: \"%s\"", seg["start"], text)

            if not discard and i in {idx for indices in repeated_texts.values() for idx in indices}:
                if text in repeated_texts:
                    indices = repeated_texts[text]
                    starts = [segments[j]["start"] for j in indices]
                    gaps = [starts[k+1] - starts[k] for k in range(len(starts)-1)]
                    if gaps:
                        mean_gap = sum(gaps) / len(gaps)
                        cv = (sum((g - mean_gap)**2 for g in gaps) / len(gaps))**0.5 / mean_gap if mean_gap > 0 else 0
                        if mean_gap > 5 and cv < 0.3 and len(text.split()) <= 3:
                            discard = True
                            logger.info("Filtered repeated hallucination (%dx, ~%.0fs apart, cv=%.2f) at %.1f: \"%s\"",
                                        len(indices), mean_gap, cv, seg["start"], text)

            if not discard:
                kept.append(seg)

        removed = len(segments) - len(kept)
        if removed > 0:
            logger.info("Hallucination filter removed %d/%d segments", removed, len(segments))

        return kept

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
