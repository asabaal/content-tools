from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from audio.features import AudioFeatures, StemFeatures
from lyrics.parser import LyricLine, LyricSection, LyricWord

logger = logging.getLogger(__name__)

BEAT_SNAP_TOLERANCE = 0.2
ONSET_GAP_MULTIPLIER = 3.0
MIN_CLUSTER_GAP = 0.8
MIN_LINE_DURATION = 0.5


@dataclass
class SyncedWord:
    text: str
    start: float
    end: float
    source: str = "interpolated"

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> dict:
        return {"text": self.text, "start": round(self.start, 3), "end": round(self.end, 3), "source": self.source}


@dataclass
class SyncedLine:
    text: str
    start: float
    end: float
    words: List[SyncedWord] = field(default_factory=list)
    section: Optional[LyricSection] = None
    alignment_confidence: float = 0.0

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> dict:
        d = {
            "text": self.text,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "words": [w.to_dict() for w in self.words],
            "alignment_confidence": round(self.alignment_confidence, 3),
        }
        if self.section:
            d["section"] = self.section.to_dict()
        return d


@dataclass
class SyncResult:
    lines: List[SyncedLine]
    source: str = "full_mix"
    avg_confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "lines": [l.to_dict() for l in self.lines],
            "source": self.source,
            "avg_confidence": round(self.avg_confidence, 3),
        }

    def save(self, path) -> None:
        import json
        from pathlib import Path

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


class LyricSynchronizer:
    def __init__(
        self,
        lyrics: List[LyricLine],
        audio_features: AudioFeatures,
        *,
        vocal_onset_times: Optional[np.ndarray] = None,
        midi_note_starts: Optional[np.ndarray] = None,
        transcription_segments: Optional[List[dict]] = None,
    ):
        self.lyrics = lyrics
        self.audio_features = audio_features
        self.vocal_onset_times = vocal_onset_times
        self.midi_note_starts = midi_note_starts
        self.transcription_segments = transcription_segments

    def synchronize(self, snap_to_beats: bool = True, snap_to_onsets: bool = True) -> SyncResult:
        source = self._determine_source()
        onset_times = self._get_onset_times(source)

        lines = self.lyrics
        used_transcription = False
        if self._has_naive_timing(lines):
            if self.transcription_segments and len(self.transcription_segments) > 0:
                lines = self._rough_align_from_transcription(lines)
                used_transcription = True
            elif len(onset_times) > 0:
                lines = self._rough_align_lines(lines, onset_times)

        effective_snap_beats = snap_to_beats and not used_transcription

        synced_lines: List[SyncedLine] = []
        total_confidence = 0.0

        for line in lines:
            if not line.text.strip():
                continue

            start = line.start
            end = line.end

            if effective_snap_beats and len(self.audio_features.beats.times) > 0:
                start = self._snap_to_nearest_beat(start)
                end = self._snap_to_nearest_beat(end)

            if end <= start:
                end = start + line.duration if line.duration > 0 else start + 3.0

            words = self._align_words(line.words, start, end, onset_times, snap_to_onsets)
            confidence = self._compute_confidence(words)

            synced_lines.append(
                SyncedLine(
                    text=line.text,
                    start=start,
                    end=end,
                    words=words,
                    section=line.section,
                    alignment_confidence=confidence,
                )
            )
            total_confidence += confidence

        avg_confidence = total_confidence / len(synced_lines) if synced_lines else 0.0

        return SyncResult(lines=synced_lines, source=source, avg_confidence=avg_confidence)

    def _has_naive_timing(self, lines: List[LyricLine]) -> bool:
        if not lines:
            return False
        if lines[0].start > 0.5:
            return False
        durations = [l.duration for l in lines if l.duration > 0]
        if not durations:
            return True
        if len(set(round(d, 1) for d in durations)) == 1:
            return True
        return False

    def _rough_align_lines(self, lines: List[LyricLine], onset_times: np.ndarray) -> List[LyricLine]:
        clusters = self._cluster_onsets(onset_times)
        non_empty = [l for l in lines if l.text.strip()]
        if not clusters or not non_empty:
            return lines

        mapped = self._map_lines_to_clusters(non_empty, clusters)

        result = []
        line_idx = 0
        for orig in lines:
            if not orig.text.strip():
                result.append(orig)
                continue
            cl = mapped[line_idx]
            new_line = LyricLine(
                index=orig.index,
                text=orig.text,
                start=cl[0],
                end=cl[1],
                words=orig.words,
                section=orig.section,
            )
            result.append(new_line)
            line_idx += 1

        return result

    def _rough_align_from_transcription(self, lines: List[LyricLine]) -> List[LyricLine]:
        if not self.transcription_segments:
            return lines

        non_empty = [l for l in lines if l.text.strip()]
        segments = self.transcription_segments

        if len(segments) == len(non_empty):
            boundaries = [(s["start"], s["end"]) for s in segments]
        elif len(segments) > len(non_empty):
            boundaries = self._merge_transcription_segments(segments, len(non_empty))
        else:
            return self._rough_align_lines(
                lines,
                self.vocal_onset_times if self.vocal_onset_times is not None else np.array([]),
            )

        result = []
        line_idx = 0
        for orig in lines:
            if not orig.text.strip():
                result.append(orig)
                continue
            bd = boundaries[line_idx]
            new_line = LyricLine(
                index=orig.index,
                text=orig.text,
                start=bd[0],
                end=bd[1],
                words=orig.words,
                section=orig.section,
            )
            result.append(new_line)
            line_idx += 1

        return result

    def _merge_transcription_segments(
        self, segments: List[dict], n_lines: int
    ) -> List[tuple]:
        n_seg = len(segments)
        per_line = n_seg / n_lines
        result = []
        for line_i in range(n_lines):
            start_idx = int(line_i * per_line)
            end_idx = min(int((line_i + 1) * per_line), n_seg - 1)
            if line_i == n_lines - 1:
                end_idx = n_seg - 1
            start = segments[start_idx]["start"]
            end = segments[end_idx]["end"]
            if end - start < MIN_LINE_DURATION:
                end = start + MIN_LINE_DURATION
            result.append((start, min(end, self.audio_features.duration)))
        return result

    def _cluster_onsets(self, onset_times: np.ndarray) -> List[tuple]:
        if len(onset_times) < 2:
            if len(onset_times) == 1:
                return [(float(onset_times[0]), float(onset_times[0]) + 1.0)]
            return []

        gaps = np.diff(onset_times)
        median_gap = float(np.median(gaps))
        threshold = max(median_gap * ONSET_GAP_MULTIPLIER, MIN_CLUSTER_GAP)

        clusters = []
        cluster_start = float(onset_times[0])
        cluster_end = float(onset_times[0])

        for i in range(1, len(onset_times)):
            gap = float(onset_times[i]) - cluster_end
            if gap > threshold:
                clusters.append((cluster_start, cluster_end + median_gap * 0.5))
                cluster_start = float(onset_times[i])
                cluster_end = float(onset_times[i])
            else:
                cluster_end = float(onset_times[i])

        clusters.append((cluster_start, cluster_end + median_gap * 0.5))
        return clusters

    def _map_lines_to_clusters(
        self, lines: List[LyricLine], clusters: List[tuple]
    ) -> List[tuple]:
        n_lines = len(lines)
        n_clusters = len(clusters)

        if n_clusters == n_lines:
            return list(clusters)

        if n_clusters > n_lines:
            return self._merge_clusters_to_lines(clusters, n_lines)

        return self._split_clusters_to_lines(clusters, n_lines)

    def _merge_clusters_to_lines(
        self, clusters: List[tuple], n_lines: int
    ) -> List[tuple]:
        duration = self.audio_features.duration
        n_clusters = len(clusters)
        result = []
        per_line = n_clusters / n_lines

        for line_i in range(n_lines):
            start_cluster = int(line_i * per_line)
            end_cluster = min(int((line_i + 1) * per_line), n_clusters - 1)
            if line_i == n_lines - 1:
                end_cluster = n_clusters - 1

            start = clusters[start_cluster][0]
            end = clusters[end_cluster][1]
            if line_i == n_lines - 1:
                end = min(end, duration)

            if end - start < MIN_LINE_DURATION:
                end = start + MIN_LINE_DURATION

            result.append((start, min(end, duration)))

        return result

    def _split_clusters_to_lines(
        self, clusters: List[tuple], n_lines: int
    ) -> List[tuple]:
        duration = self.audio_features.duration
        n_clusters = len(clusters)
        cluster_sizes = [max(1, round(n_lines / n_clusters)) for _ in range(n_clusters)]

        total = sum(cluster_sizes)
        diff = n_lines - total
        idx = 0
        while diff > 0:
            cluster_sizes[idx % n_clusters] += 1
            diff -= 1
            idx += 1
        while diff < 0:
            cluster_sizes[idx % n_clusters] -= 1
            diff += 1
            idx += 1

        result = []
        for ci, cluster in enumerate(clusters):
            n = cluster_sizes[ci]
            cl_start, cl_end = cluster
            cl_duration = cl_end - cl_start

            if ci == n_clusters - 1:
                cl_end = min(cl_end, duration)
                cl_duration = cl_end - cl_start

            per_line = cl_duration / n if n > 0 else MIN_LINE_DURATION

            for li in range(n):
                ls = cl_start + li * per_line
                le = ls + per_line
                if le - ls < MIN_LINE_DURATION:
                    le = ls + MIN_LINE_DURATION
                result.append((ls, min(le, duration)))

        if len(result) > n_lines:  # pragma: no cover
            result = result[:n_lines]
        while len(result) < n_lines:  # pragma: no cover
            last_end = result[-1][1] if result else 0.0
            result.append((last_end, min(last_end + MIN_LINE_DURATION, duration)))

        return result

    def _determine_source(self) -> str:
        if self.midi_note_starts is not None and len(self.midi_note_starts) > 0:
            return "midi"
        if self.vocal_onset_times is not None and len(self.vocal_onset_times) > 0:
            return "vocal_stem"
        return "full_mix"

    def _get_onset_times(self, source: str) -> np.ndarray:
        if source == "midi" and self.midi_note_starts is not None:
            return self.midi_note_starts
        if source == "vocal_stem" and self.vocal_onset_times is not None:
            return self.vocal_onset_times
        return self.audio_features.onset_times

    def _snap_to_nearest_beat(self, time: float) -> float:
        beat_times = self.audio_features.beats.times
        if len(beat_times) == 0:
            return time
        idx = int(np.argmin(np.abs(beat_times - time)))
        nearest = float(beat_times[idx])
        if abs(nearest - time) <= BEAT_SNAP_TOLERANCE:
            return nearest
        return time

    def _align_words(
        self,
        words: List[LyricWord],
        start: float,
        end: float,
        onset_times: np.ndarray,
        snap_to_onsets: bool,
    ) -> List[SyncedWord]:
        if not words:
            return []

        texts = [w.text for w in words]

        if not snap_to_onsets or len(onset_times) == 0:
            return self._interpolate_words(texts, start, end, "interpolated")

        line_onsets = onset_times[(onset_times >= start) & (onset_times <= end)]

        if len(line_onsets) == 0:
            return self._interpolate_words(texts, start, end, "interpolated")

        source = self._determine_source()
        onset_label = "midi" if source == "midi" else ("vocal_onset" if source == "vocal_stem" else "onset")

        if len(line_onsets) >= len(texts):
            return self._align_words_to_onsets(texts, start, end, line_onsets, onset_label)
        else:
            return self._align_words_mixed(texts, start, end, line_onsets, onset_label)

    def _align_words_to_onsets(
        self,
        texts: List[str],
        start: float,
        end: float,
        onsets: np.ndarray,
        onset_label: str,
    ) -> List[SyncedWord]:
        result: List[SyncedWord] = []
        for i, text in enumerate(texts):
            word_start = float(onsets[i])
            word_end = float(onsets[i + 1]) if i + 1 < len(onsets) else end
            if word_end <= word_start:  # pragma: no cover
                word_end = word_start + 0.3
            result.append(SyncedWord(text=text, start=word_start, end=min(word_end, end), source=onset_label))
        return result

    def _align_words_mixed(
        self,
        texts: List[str],
        start: float,
        end: float,
        onsets: np.ndarray,
        onset_label: str,
    ) -> List[SyncedWord]:
        result: List[SyncedWord] = []
        words_per_onset = len(texts) / len(onsets)

        for i, text in enumerate(texts):
            onset_idx = min(int(i / words_per_onset), len(onsets) - 1)

            if onset_idx < len(onsets) - 1:
                segment_start = float(onsets[onset_idx])
                segment_end = float(onsets[onset_idx + 1])
                local_count = max(1, round(words_per_onset))
                local_idx = i - int(onset_idx * words_per_onset)
                local_idx = min(local_idx, local_count - 1)
                per_word = (segment_end - segment_start) / local_count
                word_start = segment_start + local_idx * per_word
                word_end = word_start + per_word
            else:
                remaining = len(texts) - i
                per_word = (end - float(onsets[-1])) / remaining if remaining > 0 else 0.3
                word_start = float(onsets[-1]) + (i - round(onset_idx * words_per_onset)) * per_word
                word_end = word_start + per_word

            is_onset_word = i < len(onsets)
            result.append(
                SyncedWord(
                    text=text,
                    start=word_start,
                    end=min(word_end, end),
                    source=onset_label if is_onset_word else "interpolated",
                )
            )

        return result

    def _interpolate_words(self, texts: List[str], start: float, end: float, source: str) -> List[SyncedWord]:
        if not texts:
            return []
        per_word = (end - start) / len(texts)
        return [SyncedWord(text=t, start=start + i * per_word, end=start + (i + 1) * per_word, source=source) for i, t in enumerate(texts)]

    def _compute_confidence(self, words: List[SyncedWord]) -> float:
        if not words:
            return 0.0
        onset_count = sum(1 for w in words if w.source != "interpolated")
        return onset_count / len(words)
