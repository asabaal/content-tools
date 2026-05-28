from __future__ import annotations

import logging
import re
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
    vocal_stem_quality: str = "ok"
    onset_source: str = "vocal_stem"
    cluster_count: int = 0
    onset_count: int = 0

    def to_dict(self) -> dict:
        d = {
            "lines": [l.to_dict() for l in self.lines],
            "source": self.source,
            "avg_confidence": round(self.avg_confidence, 3),
        }
        if self.vocal_stem_quality != "ok":
            d["vocal_stem_quality"] = self.vocal_stem_quality
        if self.onset_source != "vocal_stem":
            d["onset_source"] = self.onset_source
        if self.cluster_count > 0:
            d["cluster_count"] = self.cluster_count
        if self.onset_count > 0:
            d["onset_count"] = self.onset_count
        return d

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
        self._alignment_result = None
        self._vocal_stem_quality = "ok"
        self._effective_onset_source = "vocal_stem"

    def synchronize(self, snap_to_beats: bool = True, snap_to_onsets: bool = True) -> SyncResult:
        self._check_vocal_stem_quality()
        source = self._determine_source()
        onset_times = self._get_onset_times(source)
        effective_onset_count = len(onset_times)

        clusters = self._cluster_onsets(onset_times) if len(onset_times) > 0 else []

        lines = self.lyrics
        used_transcription = False
        if self._has_naive_timing(lines):
            if self.transcription_segments and len(self.transcription_segments) > 0:
                lines = self._rough_align_from_transcription(lines)
                used_transcription = True
            elif len(onset_times) > 0:
                lines = self._rough_align_lines(lines, onset_times)

        if self._alignment_result is None and self.transcription_segments:
            self._ensure_alignment_result()

        effective_snap_beats = snap_to_beats and not used_transcription

        synced_lines: List[SyncedLine] = []
        total_confidence = 0.0
        non_empty_idx = 0

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

            whisper_match = self._get_whisper_match(non_empty_idx)
            words = self._align_words(line.words, start, end, onset_times, snap_to_onsets, whisper_match)

            if words:
                has_transcription = any(w.source == "transcription" for w in words)
                if has_transcription:
                    word_start = words[0].start - 0.05
                    word_end = words[-1].end + 0.05
                    if synced_lines and synced_lines[-1].end > word_start:
                        prev_last_end = synced_lines[-1].words[-1].end if synced_lines[-1].words else 0.0
                        synced_lines[-1].end = max(prev_last_end + 0.01, word_start)
                    start = word_start
                    end = word_end
                elif words[0].start > start + 0.1:
                    min_start = synced_lines[-1].end if synced_lines else 0.0
                    start = max(words[0].start - 0.05, min_start)
                if words[-1].end < end - 0.1:
                    end = words[-1].end + 0.05

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
            non_empty_idx += 1

        avg_confidence = total_confidence / len(synced_lines) if synced_lines else 0.0

        return SyncResult(
            lines=synced_lines,
            source=source,
            avg_confidence=avg_confidence,
            vocal_stem_quality=self._vocal_stem_quality,
            onset_source=self._effective_onset_source,
            cluster_count=len(clusters),
            onset_count=effective_onset_count,
        )

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

    def _check_vocal_stem_quality(self) -> None:
        if self.vocal_onset_times is None or len(self.vocal_onset_times) == 0:
            self._vocal_stem_quality = "none"
            self._effective_onset_source = "full_mix"
            return

        duration = self.audio_features.duration
        if duration <= 0:
            return

        n_onsets = len(self.vocal_onset_times)
        onset_range = float(self.vocal_onset_times[-1]) - float(self.vocal_onset_times[0])
        total_lyric_words = sum(max(1, len(l.text.split())) for l in self.lyrics if l.text.strip())

        vocal_coverage = onset_range / duration if duration > 0 else 0
        sparse = n_onsets < total_lyric_words * 0.05
        narrow = vocal_coverage < 0.1
        few = n_onsets < 30

        full_mix_onsets = self.audio_features.onset_times
        full_mix_coverage = 0.0
        if len(full_mix_onsets) > 1:
            fm_range = float(full_mix_onsets[-1]) - float(full_mix_onsets[0])
            full_mix_coverage = fm_range / duration if duration > 0 else 0

        degraded = False
        reasons = []

        if narrow and full_mix_coverage > 0.5:
            degraded = True
            reasons.append(
                f"Vocal onset coverage {vocal_coverage*100:.1f}% vs full-mix coverage {full_mix_coverage*100:.1f}%"
            )

        if sparse and few:
            degraded = True
            reasons.append(
                f"Only {n_onsets} onsets for {total_lyric_words} lyric words"
            )

        if degraded:
            full_mix_count = len(full_mix_onsets)
            reason_str = "; ".join(reasons)
            logger.warning(
                f"Vocal stem quality degraded: {n_onsets} onsets in {onset_range:.1f}s range "
                f"({vocal_coverage*100:.1f}% of {duration:.0f}s). {reason_str}. "
                f"Falling back to full-mix onsets ({full_mix_count}, {full_mix_coverage*100:.1f}% coverage)"
            )
            self._vocal_stem_quality = "degraded"
            self._effective_onset_source = "full_mix"
            self.vocal_onset_times = None
        else:
            self._vocal_stem_quality = "ok"
            self._effective_onset_source = "vocal_stem"

    def _rough_align_lines(self, lines: List[LyricLine], onset_times: np.ndarray) -> List[LyricLine]:
        clusters = self._cluster_onsets(onset_times)
        non_empty = [l for l in lines if l.text.strip()]
        if not clusters or not non_empty:
            return lines

        mapped = self._assign_clusters_to_lines(clusters, non_empty, onset_times)

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
            boundaries = self._align_via_analyzer(lines, non_empty)
            if boundaries is None:
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

    def _align_via_analyzer(
        self, lines: List[LyricLine], non_empty: List[LyricLine]
    ) -> Optional[List[tuple]]:
        try:
            from lyrics.alignment_analyzer import analyze_alignment
        except ImportError:
            logger.warning("alignment_analyzer not available, falling back to onset clustering")
            return None

        alignment = analyze_alignment(
            lyrics=non_empty,
            transcription_segments=self.transcription_segments,
            vocal_onset_times=self.vocal_onset_times,
            audio_features=self.audio_features,
        )

        self._alignment_result = alignment

        raw_boundaries: List[tuple] = []
        for match in alignment.line_matches:
            if match.transcription_start is not None and match.transcription_end is not None:
                start = match.transcription_start
                end = match.transcription_end
                if end <= start:
                    end = start + MIN_LINE_DURATION
                raw_boundaries.append((start, min(end, self.audio_features.duration)))
            else:
                if raw_boundaries:
                    prev_end = raw_boundaries[-1][1]
                    raw_boundaries.append((prev_end, min(prev_end + MIN_LINE_DURATION, self.audio_features.duration)))
                else:
                    raw_boundaries.append((0.0, MIN_LINE_DURATION))

        if len(raw_boundaries) != len(non_empty):
            logger.warning(
                f"Analyzer returned {len(raw_boundaries)} boundaries for {len(non_empty)} lines, falling back"
            )
            return None

        return self._subdivide_shared_boundaries(raw_boundaries, non_empty)

    def _ensure_alignment_result(self) -> None:
        if self._alignment_result is not None:
            return
        try:
            from lyrics.alignment_analyzer import analyze_alignment
        except ImportError:
            return
        non_empty = [l for l in self.lyrics if l.text.strip()]
        if not non_empty:
            return
        self._alignment_result = analyze_alignment(
            lyrics=non_empty,
            transcription_segments=self.transcription_segments,
            vocal_onset_times=self.vocal_onset_times,
            audio_features=self.audio_features,
        )

    def _subdivide_shared_boundaries(
        self, boundaries: List[tuple], lines: List[LyricLine]
    ) -> List[tuple]:
        groups: List[List[int]] = []
        current_group: List[int] = [0]

        for i in range(1, len(boundaries)):
            if abs(boundaries[i][0] - boundaries[i - 1][0]) < 0.01 and abs(
                boundaries[i][1] - boundaries[i - 1][1]
            ) < 0.01:
                current_group.append(i)
            else:
                groups.append(current_group)
                current_group = [i]
        groups.append(current_group)

        result = list(boundaries)
        for group in groups:
            if len(group) <= 1:
                continue
            seg_start = boundaries[group[0]][0]
            seg_end = boundaries[group[0]][1]
            seg_duration = seg_end - seg_start
            word_counts = [max(1, len(lines[i].text.split())) for i in group]
            total_words = sum(word_counts)
            cursor = seg_start
            for j, idx in enumerate(group):
                share = seg_duration * (word_counts[j] / total_words)
                line_end = min(cursor + share, self.audio_features.duration)
                if line_end - cursor < MIN_LINE_DURATION:
                    line_end = min(cursor + MIN_LINE_DURATION, self.audio_features.duration)
                result[idx] = (cursor, line_end)
                cursor = line_end

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

    def _assign_clusters_to_lines(
        self, clusters: List[tuple], lines: List[LyricLine], onset_times: np.ndarray
    ) -> List[tuple]:
        duration = self.audio_features.duration
        n_lines = len(lines)
        n_clusters = len(clusters)

        if n_clusters == 0:
            return [(0.0, MIN_LINE_DURATION)] * n_lines

        word_counts = [max(1, len(l.text.split())) for l in lines]
        total_words = sum(word_counts)

        onset_counts = []
        for cl_start, cl_end in clusters:
            count = int(np.sum((onset_times >= cl_start) & (onset_times <= cl_end)))
            onset_counts.append(max(1, count))
        total_onset_capacity = sum(onset_counts)

        cum_words = [0.0]
        for wc in word_counts:
            cum_words.append(cum_words[-1] + wc)

        cum_capacity = [0.0]
        for oc in onset_counts:
            cum_capacity.append(cum_capacity[-1] + oc)

        line_clusters: List[tuple] = []
        for li in range(n_lines):
            target_start_frac = cum_words[li] / total_words
            target_end_frac = cum_words[li + 1] / total_words

            target_cap_start = target_start_frac * total_onset_capacity
            target_cap_end = target_end_frac * total_onset_capacity

            start_ci = 0
            for ci in range(n_clusters):
                if cum_capacity[ci + 1] >= target_cap_start:
                    start_ci = ci
                    break

            end_ci = start_ci
            for ci in range(start_ci, n_clusters):
                if cum_capacity[ci + 1] >= target_cap_end:
                    end_ci = ci
                    break
            if li == n_lines - 1:
                end_ci = n_clusters - 1

            line_clusters.append((start_ci, end_ci))

        result: List[tuple] = []
        for li in range(n_lines):
            start_ci, end_ci = line_clusters[li]

            if start_ci == end_ci:
                cl_start = clusters[start_ci][0]
                cl_end = clusters[start_ci][1]
                lines_sharing = []
                for lj in range(n_lines):
                    if line_clusters[lj] == (start_ci, end_ci):
                        lines_sharing.append(lj)
                if len(lines_sharing) > 1:
                    my_idx = lines_sharing.index(li)
                    my_words = word_counts[li]
                    total_sharing_words = sum(word_counts[lj] for lj in lines_sharing)
                    share = (cl_end - cl_start) * (my_words / total_sharing_words)
                    ls = cl_start + sum(
                        (cl_end - cl_start) * (word_counts[lines_sharing[k]] / total_sharing_words)
                        for k in range(my_idx)
                    )
                    le = ls + share
                    if le - ls < MIN_LINE_DURATION:
                        le = ls + MIN_LINE_DURATION
                    result.append((ls, min(le, duration)))
                else:
                    s = clusters[start_ci][0]
                    e = clusters[start_ci][1]
                    if e - s < MIN_LINE_DURATION:
                        e = s + MIN_LINE_DURATION
                    result.append((s, min(e, duration)))
            else:
                s = clusters[start_ci][0]
                e = clusters[end_ci][1]
                if li == n_lines - 1:
                    e = min(e, duration)
                if e - s < MIN_LINE_DURATION:
                    e = s + MIN_LINE_DURATION
                result.append((s, min(e, duration)))

        for i in range(1, len(result)):
            if result[i][0] < result[i - 1][1]:
                mid = (result[i][0] + result[i - 1][1]) / 2
                prev = list(result[i - 1])
                prev[1] = mid
                result[i - 1] = tuple(prev)
                curr = list(result[i])
                curr[0] = mid
                result[i] = tuple(curr)

        if len(result) > n_lines:
            result = result[:n_lines]
        while len(result) < n_lines:
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
        whisper_match: Optional[object] = None,
    ) -> List[SyncedWord]:
        if not words:
            return []

        texts = [w.text for w in words]

        if whisper_match is not None:
            whisper_words = self._build_words_from_whisper(texts, start, end, whisper_match)
            if whisper_words is not None:
                return whisper_words

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

    def _get_whisper_match(self, non_empty_idx: int) -> Optional[object]:
        if self._alignment_result is None:
            return None
        matches = self._alignment_result.line_matches
        if non_empty_idx >= len(matches):
            return None
        match = matches[non_empty_idx]
        if not match.word_timings or len(match.word_timings) == 0:
            return None
        if match.word_match_ratio < 0.2:
            return None
        return match

    def _build_words_from_whisper(
        self, texts: List[str], start: float, end: float, match: object
    ) -> Optional[List[SyncedWord]]:
        wt_list = match.word_timings
        if not wt_list:
            return None

        from difflib import SequenceMatcher

        def _norm(s: str) -> str:
            return re.sub(r"[^a-z0-9]", "", s.lower())

        lyric_norm = [_norm(t) for t in texts]
        whisper_norm = [_norm(w.word) for w in wt_list]

        matcher = SequenceMatcher(None, lyric_norm, whisper_norm)
        matched_pairs: List[Optional[int]] = [None] * len(texts)
        for i, j, n in matcher.get_matching_blocks():
            for k in range(n):
                matched_pairs[i + k] = j + k

        result: List[SyncedWord] = []
        last_end = 0.0

        for li, text in enumerate(texts):
            wi = matched_pairs[li]
            if wi is not None and wi < len(wt_list):
                wt = wt_list[wi]
                ws = float(wt.start)
                we = float(wt.end)
                if ws < last_end:
                    ws = last_end
                if we <= ws:
                    we = ws + 0.1
                result.append(SyncedWord(text=text, start=ws, end=we, source="transcription"))
                last_end = we
            else:
                if result:
                    gap_start = result[-1].end
                else:
                    gap_start = start
                remaining = len(texts) - li
                per_word = (end - gap_start) / remaining if remaining > 0 else 0.3
                ws = gap_start
                we = min(ws + per_word, end)
                result.append(SyncedWord(text=text, start=ws, end=we, source="interpolated"))
                last_end = we

        return result
