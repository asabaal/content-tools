from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from lyrics.synchronizer import SyncedLine, SyncResult, SyncedWord

logger = logging.getLogger(__name__)

ONSET_MERGE_THRESHOLD = 0.05
SNAP_TOLERANCE_TRANSCRIPTION = 0.15
SNAP_TOLERANCE_INTERPOLATED = 0.25
MIN_SEGMENT_DURATION = 0.005
BREATH_DURATION_THRESHOLD = 0.12
MIN_WORD_DURATION = 0.04

TRIM_MAX_DURATION = 1.5
TRIM_FILL_CAP = 1.2
TRIM_FILL_MARGIN = 0.3
TRIM_RESCUE_TARGET = 0.3
TRIM_FLOOR_MULT = 3.0
TRIM_TAIL = 0.10
TRIM_GAP = 0.03
TRIM_GAP_THRESHOLD = 0.5


def _percentile(data: List[float], pct: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


def _trim_noise_floor(peaks: Optional[List[float]]) -> float:
    if not peaks:
        return 0.01
    return max(_percentile(peaks, 25), 0.005)


def _trim_energy_end(
    peaks: List[float], ws: float, we: float, floor: float,
    tail: float, pps: int,
) -> Optional[float]:
    si = max(0, int(ws * pps))
    ei = min(len(peaks), int(math.ceil(we * pps)))
    if si >= ei:
        return None
    for j in range(ei - si - 1, -1, -1):
        if peaks[si + j] > floor:
            return (si + j) / pps + tail
    return None


def _audio_aware_post_process(
    words: List[SyncedWord],
    line_start: float,
    line_end: float,
    onsets: List[float],
    peaks: Optional[List[float]],
    floor: float,
    pps: int,
) -> None:
    """Audio-aware trim + undersize rescue + gap fill (in-place on words).

    Replaces the blind last-word-to-line_end stretch with evidence-based
    duration management:
      Pass 1 — trim overflow words to their actual vocal extent
      Pass 2 — rescue undersize words into adjacent freed space
      Pass 3 — audio-capped gap fill (never extends past voice + margin)
    """
    if not words:
        return

    energy_ends: Dict[int, float] = {}

    # Pass 1: trim
    for i, w in enumerate(words):
        ws, we = w.start, w.end
        if we - ws <= TRIM_MAX_DURATION:
            continue
        next_event = (words[i + 1].start - TRIM_GAP) if i + 1 < len(words) else line_end
        candidates = [we, next_event, ws + TRIM_MAX_DURATION]
        if peaks:
            e_end = _trim_energy_end(peaks, ws, we, floor, TRIM_TAIL, pps)
            if e_end is not None:
                candidates.append(e_end)
                energy_ends[i] = e_end
        for ot in onsets:
            if ws + 0.08 < ot < we:
                candidates.append(ot - TRIM_GAP)
                break
        real_end = max(min(candidates), ws + MIN_WORD_DURATION)
        w.end = round(real_end, 3)

    # Pass 2: rescue undersize
    for i, w in enumerate(words):
        ws, we = w.start, w.end
        dur = we - ws
        if dur >= MIN_WORD_DURATION * 2:
            continue
        deficit = TRIM_RESCUE_TARGET - dur
        if deficit <= 0:
            continue
        next_start = words[i + 1].start if i + 1 < len(words) else line_end
        end_room = next_start - we
        if end_room > 0.001:
            give = min(deficit, end_room)
            we += give
            deficit -= give
            w.end = round(we, 3)
        if deficit > 0 and i > 0:
            prev_end = words[i - 1].end
            start_room = ws - prev_end
            if start_room > 0.001:
                give = min(deficit, start_room)
                w.start = round(ws - give, 3)

    # Pass 3: audio-capped gap fill
    for i, w in enumerate(words):
        ws, we = w.start, w.end
        next_event = words[i + 1].start if i + 1 < len(words) else line_end
        gap_to_next = next_event - we
        if gap_to_next <= TRIM_GAP_THRESHOLD:
            continue
        hard_cap = ws + TRIM_FILL_CAP
        if i in energy_ends:
            audio_cap = energy_ends[i] + TRIM_FILL_MARGIN
        else:
            audio_cap = hard_cap
        target = min(hard_cap, audio_cap, we + (gap_to_next - TRIM_GAP_THRESHOLD) + 0.01)
        new_end = min(target, next_event)
        w.end = round(max(new_end, we), 3)


def refine_synced_lines(
    sync_result: SyncResult,
    vocal_onset_times: np.ndarray,
    waveform_peaks: Optional[List[float]] = None,
    peaks_per_second: int = 100,
) -> SyncResult:
    for line in sync_result.lines:
        if not line.text.strip():
            continue
        line_onsets = [float(t) for t in vocal_onset_times if line.start <= t <= line.end]
        line_peaks = None
        if waveform_peaks and peaks_per_second > 0:
            si = max(0, int(line.start * peaks_per_second))
            ei = min(len(waveform_peaks), int(line.end * peaks_per_second))
            line_peaks = waveform_peaks[si:ei]
        words, onset_segs, word_assigns, warnings = refine_line(
            line.words, line_onsets, line.start, line.end, line_peaks, peaks_per_second,
        )
        line.words = words
        line.onset_segments = [s.to_dict() for s in onset_segs]
        line.word_segment_assignments = [a.to_dict() for a in word_assigns]
        line.warnings = warnings
    for line in sync_result.lines:
        for w in line.words:
            if w.end - w.start < MIN_WORD_DURATION:
                w.end = w.start + MIN_WORD_DURATION
        for i in range(len(line.words) - 1):
            if line.words[i].end > line.words[i + 1].start:
                mid = (line.words[i].end + line.words[i + 1].start) / 2
                boundary = max(mid, line.words[i].start + MIN_WORD_DURATION)
                if boundary < line.words[i + 1].end - MIN_WORD_DURATION:
                    line.words[i].end = boundary
                    line.words[i + 1].start = boundary
                else:
                    line.words[i].end = min(line.words[i].end, line.words[i + 1].start - 0.001)
                    if line.words[i].end <= line.words[i].start:
                        line.words[i].end = line.words[i].start + MIN_WORD_DURATION
        for w in line.words:
            if w.end - w.start < 0.001:
                w.end = w.start + MIN_WORD_DURATION

    noise_floor_val = _trim_noise_floor(waveform_peaks) * TRIM_FLOOR_MULT
    for line in sync_result.lines:
        if not line.words:
            continue
        line_onsets = [float(t) for t in vocal_onset_times if line.start <= t <= line.end]
        _audio_aware_post_process(
            line.words, line.start, line.end, line_onsets,
            waveform_peaks, noise_floor_val, peaks_per_second,
        )
    return sync_result


def refine_line(
    words: List[SyncedWord],
    onsets: List[float],
    line_start: float,
    line_end: float,
    line_peaks: Optional[List[float]] = None,
    pps: int = 100,
) -> Tuple[List[SyncedWord], list, list, List[str]]:
    warnings: List[str] = []

    if not words:
        return words, [], [], warnings

    merged = merge_close_onsets(onsets, ONSET_MERGE_THRESHOLD)

    has_whisper = any(w.source == "transcription" for w in words)
    has_onsets = len(merged) > 0

    if not has_onsets:
        warnings.append("no_onsets_in_line")
        segments = build_onset_segments([], line_start, line_end, line_peaks, pps)
        assignments = build_word_assignments(words, segments, line_start, line_end, "interpolated")
        return words, segments, assignments, warnings

    if has_whisper:
        words = snap_words_to_onsets(words, merged, line_start, line_end)
    else:
        words = assign_onsets_to_words(words, merged, line_start, line_end)

    segments = build_onset_segments(merged, line_start, line_end, line_peaks, pps)

    assign_onset_segments_to_words(segments, words)

    classify_segments(segments, words, line_peaks, pps)

    assignments = build_word_assignments(words, segments, line_start, line_end,
                                          "whisper_plus_vocal_onset" if has_whisper else "vocal_onset_only")

    for w in words:
        dur = w.end - w.start
        if dur < 0.05:
            warnings.append(f"word_duration_very_short: {w.text} ({dur:.3f}s)")
        elif dur > 2.0:
            warnings.append(f"word_duration_very_long: {w.text} ({dur:.3f}s)")

    if has_onsets and len(merged) > 0 and len(words) > 0:
        ratio = abs(len(merged) - len(words)) / len(words)
        if ratio > 0.5:
            warnings.append(f"onset_count_mismatch: {len(merged)} onsets vs {len(words)} words")

    return words, segments, assignments, warnings


def merge_close_onsets(onsets: List[float], threshold: float = ONSET_MERGE_THRESHOLD) -> List[float]:
    if not onsets:
        return []
    merged = [onsets[0]]
    for t in onsets[1:]:
        if t - merged[-1] < threshold:
            merged[-1] = (merged[-1] + t) / 2
        else:
            merged.append(t)
    return merged


def snap_words_to_onsets(
    words: List[SyncedWord],
    onsets: List[float],
    line_start: float,
    line_end: float,
) -> List[SyncedWord]:
    used_onsets = set()
    new_words = []
    for w in words:
        nw = SyncedWord(text=w.text, start=w.start, end=w.end, source=w.source)
        tol = SNAP_TOLERANCE_INTERPOLATED if w.source == "interpolated" else SNAP_TOLERANCE_TRANSCRIPTION
        best_dist = tol
        best_oi = None
        for oi, ot in enumerate(onsets):
            if oi in used_onsets:
                continue
            dist = abs(ot - w.start)
            if dist < best_dist:
                best_dist = dist
                best_oi = oi
        if best_oi is not None:
            used_onsets.add(best_oi)
            nw.start = onsets[best_oi]
            if nw.start >= nw.end:
                nw.end = nw.start + MIN_WORD_DURATION
            if nw.source in ("transcription", "vocal_onset"):
                nw.source = "whisper_plus_vocal_onset"
        new_words.append(nw)

    for i in range(len(new_words) - 1):
        if new_words[i].end > new_words[i + 1].start:
            mid = (new_words[i].end + new_words[i + 1].start) / 2
            boundary = max(mid, new_words[i].start + MIN_WORD_DURATION)
            if boundary < new_words[i + 1].end - MIN_WORD_DURATION:
                new_words[i].end = boundary
                new_words[i + 1].start = boundary
            else:
                new_words[i].end = min(new_words[i].end, new_words[i + 1].start - 0.001)
                if new_words[i].end <= new_words[i].start:
                    new_words[i].end = new_words[i].start + MIN_WORD_DURATION
    if new_words:
        if line_end > new_words[-1].start:
            new_words[-1].end = line_end
        else:
            new_words[-1].end = new_words[-1].start + MIN_WORD_DURATION

    return new_words


def assign_onsets_to_words(
    words: List[SyncedWord],
    onsets: List[float],
    line_start: float,
    line_end: float,
) -> List[SyncedWord]:
    n = len(words)
    m = len(onsets)
    if n == 0 or m == 0:
        for w in words:
            w.source = "interpolated"
        return words

    total_chars = sum(len(w.text) for w in words)
    if total_chars == 0:
        total_chars = n
    char_fracs = [len(w.text) / total_chars for w in words]
    line_dur = line_end - line_start

    INF = float('inf')
    dp = [[(-INF, None) for _ in range(m + 1)] for _ in range(n + 1)]
    dp[0][0] = (0.0, None)

    for wi in range(n):
        for oi in range(m + 1):
            cur_score, _ = dp[wi][oi]

            if oi < m:
                word_start = onsets[oi]
                if wi + 1 < n:
                    if oi + 1 < m:
                        word_end = onsets[oi + 1]
                    else:
                        word_end = line_end
                else:
                    word_end = line_end
                dur = word_end - word_start
                expected_dur = char_fracs[wi] * line_dur
                if expected_dur > 0:
                    dur_score = max(0.0, 1.0 - abs(dur - expected_dur) / expected_dur)
                else:
                    dur_score = 0.5
                new_score = cur_score + dur_score
                if new_score > dp[wi + 1][oi + 1][0]:
                    dp[wi + 1][oi + 1] = (new_score, ('assign', oi))

                skip_score = cur_score - 0.15
                if skip_score > dp[wi][oi + 1][0]:
                    dp[wi][oi + 1] = (skip_score, ('skip', oi))

            interp_score = cur_score - 0.25
            if interp_score > dp[wi + 1][oi][0]:
                dp[wi + 1][oi] = (interp_score, ('interp', oi))

    assigned_onsets = [None] * n
    wi, oi = n, m
    while wi > 0 or oi > 0:
        _, action = dp[wi][oi]
        kind, idx = action
        if kind == 'assign':
            wi -= 1
            oi -= 1
            assigned_onsets[wi] = onsets[oi]
        elif kind == 'skip':
            oi -= 1
        elif kind == 'interp':
            wi -= 1

    boundaries = []
    for wi_idx in range(n):
        if assigned_onsets[wi_idx] is not None:
            boundaries.append((wi_idx, assigned_onsets[wi_idx]))

    for wi_idx, onset_t in boundaries:
        words[wi_idx].start = onset_t
        words[wi_idx].source = "vocal_onset_only"

    for i in range(n):
        if words[i].source != "vocal_onset_only":
            prev_end = words[i - 1].end if i > 0 else line_start
            next_start = None
            for j in range(i + 1, n):
                if words[j].source == "vocal_onset_only":
                    next_start = words[j].start
                    break
            if next_start is None:
                next_start = line_end
            gap = next_start - prev_end
            remaining = sum(1 for j in range(i, n) if words[j].source != "vocal_onset_only" and (j < i or words[j].source != "vocal_onset_only"))
            remaining_with_next = 0
            for j in range(i, n):
                if words[j].source != "vocal_onset_only":
                    remaining_with_next += 1
                else:
                    break
            if remaining_with_next > 0:
                per_word = gap / remaining_with_next if gap > 0 else 0.3
                for j in range(i, min(i + remaining_with_next, n)):
                    words[j].start = prev_end
                    words[j].end = prev_end + per_word
                    if words[j].end <= words[j].start:
                        words[j].end = words[j].start + MIN_WORD_DURATION
                    words[j].source = "interpolated"
                    prev_end = words[j].end
            break

    for i in range(n):
        if words[i].source == "vocal_onset_only":
            next_boundary = line_end
            for j in range(i + 1, n):
                if words[j].start > words[i].start:
                    next_boundary = words[j].start
                    break
            if next_boundary <= words[i].start:
                next_boundary = words[i].start + MIN_WORD_DURATION
            words[i].end = next_boundary

    return words


def _interpolate_words(words: List[SyncedWord], line_start: float, line_end: float) -> List[SyncedWord]:
    n = len(words)
    if n == 0:
        return words
    total_chars = sum(len(w.text) for w in words) or n
    dur = line_end - line_start
    t = line_start
    for i, w in enumerate(words):
        frac = len(w.text) / total_chars
        w.start = t
        w.end = t + frac * dur
        w.source = "interpolated"
        t = w.end
    return words


@dataclass
class OnsetSegment:
    segment_idx: int
    start: float
    end: float
    duration: float
    classification: str = "unknown"
    assigned_word_indices: List[int] = field(default_factory=list)
    assigned_text: str = ""
    confidence: float = 0.0
    warnings: List[str] = field(default_factory=list)
    energy: float = 0.0

    def to_dict(self) -> dict:
        return {
            "segment_idx": self.segment_idx,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "duration": round(self.duration, 3),
            "classification": self.classification,
            "assigned_word_indices": self.assigned_word_indices,
            "assigned_text": self.assigned_text,
            "confidence": round(self.confidence, 3),
            "warnings": self.warnings,
            "energy": round(self.energy, 4),
        }


@dataclass
class WordAssignment:
    assignment_idx: int
    text: str
    word_index: int
    group_id: Optional[int] = None
    group_text: Optional[str] = None
    segment_indices: List[int] = field(default_factory=list)
    start: float = 0.0
    end: float = 0.0
    source: str = "interpolated"
    confidence: float = 0.0
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "assignment_idx": self.assignment_idx,
            "text": self.text,
            "word_index": self.word_index,
            "segment_indices": self.segment_indices,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "source": self.source,
            "confidence": round(self.confidence, 3),
        }
        if self.group_id is not None:
            d["group_id"] = self.group_id
        if self.group_text is not None:
            d["group_text"] = self.group_text
        if self.warnings:
            d["warnings"] = self.warnings
        return d


def build_onset_segments(
    onsets: List[float],
    line_start: float,
    line_end: float,
    line_peaks: Optional[List[float]] = None,
    pps: int = 100,
) -> List[OnsetSegment]:
    if not onsets:
        if line_end - line_start > MIN_SEGMENT_DURATION:
            return [OnsetSegment(
                segment_idx=0, start=line_start, end=line_end,
                duration=line_end - line_start, energy=compute_energy(line_start, line_end, line_peaks, pps),
            )]
        return []

    boundaries = [line_start] + onsets + [line_end]
    segments = []
    for i in range(len(boundaries) - 1):
        s = boundaries[i]
        e = boundaries[i + 1]
        dur = e - s
        if dur < MIN_SEGMENT_DURATION:
            continue
        segments.append(OnsetSegment(
            segment_idx=i,
            start=s, end=e, duration=dur,
            energy=compute_energy(s, e, line_peaks, pps),
        ))
    return segments


def compute_energy(seg_start: float, seg_end: float, line_peaks: Optional[List[float]], pps: int) -> float:
    if not line_peaks or pps <= 0:
        return 0.0
    si = max(0, int((seg_start) * pps))
    ei = min(len(line_peaks), int((seg_end) * pps))
    if si >= ei:
        return 0.0
    return float(np.mean(line_peaks[si:ei]))


def assign_onset_segments_to_words(segments: List[OnsetSegment], words: List[SyncedWord]) -> None:
    for seg in segments:
        seg.assigned_word_indices = []
        seg.assigned_text = ""
        for wi, w in enumerate(words):
            overlap_start = max(seg.start, w.start)
            overlap_end = min(seg.end, w.end)
            if overlap_end > overlap_start:
                seg.assigned_word_indices.append(wi)
        if seg.assigned_word_indices:
            seg.assigned_text = " ".join(words[i].text for i in seg.assigned_word_indices)


def classify_segments(
    segments: List[OnsetSegment],
    words: List[SyncedWord],
    line_peaks: Optional[List[float]] = None,
    pps: int = 100,
) -> None:
    energies = [s.energy for s in segments] if segments else [0.0]
    median_energy = float(np.median(energies)) if energies else 0.0
    low_energy_threshold = median_energy / 3.0 if median_energy > 0 else 0.01

    for seg in segments:
        has_assignment = len(seg.assigned_word_indices) > 0
        if has_assignment:
            overlap_score = compute_segment_word_confidence(seg, words)
            seg.confidence = overlap_score
            if overlap_score >= 0.5:
                seg.classification = "lyric"
            else:
                seg.classification = "unknown"
                seg.warnings.append("low_confidence_assignment")
        else:
            if seg.duration < BREATH_DURATION_THRESHOLD:
                seg.classification = "breath"
                seg.confidence = 0.3
            elif seg.energy < low_energy_threshold:
                seg.classification = "noise"
                seg.confidence = 0.2
            elif seg.duration > 0.3:
                seg.classification = "unassigned"
                seg.confidence = 0.4
            else:
                seg.classification = "unknown"
                seg.confidence = 0.3


def compute_segment_word_confidence(seg: OnsetSegment, words: List[SyncedWord]) -> float:
    if not seg.assigned_word_indices:
        return 0.0
    total_overlap = 0.0
    seg_dur = seg.duration
    if seg_dur <= 0:
        return 0.0
    for wi in seg.assigned_word_indices:
        w = words[wi]
        overlap_start = max(seg.start, w.start)
        overlap_end = min(seg.end, w.end)
        if overlap_end > overlap_start:
            total_overlap += overlap_end - overlap_start
    coverage = min(1.0, total_overlap / seg_dur)
    word_coverage = len(seg.assigned_word_indices) / len(words) if words else 0
    return (coverage * 0.6 + min(1.0, word_coverage * 2) * 0.4)


def build_word_assignments(
    words: List[SyncedWord],
    segments: List[OnsetSegment],
    line_start: float,
    line_end: float,
    default_source: str = "interpolated",
) -> List[WordAssignment]:
    assignments = []
    group_counter = 0
    prev_seg_set = None

    for wi, w in enumerate(words):
        seg_indices = []
        for seg in segments:
            overlap_start = max(seg.start, w.start)
            overlap_end = min(seg.end, w.end)
            if overlap_end > overlap_start:
                seg_indices.append(seg.segment_idx)

        current_seg_set = set(seg_indices) if seg_indices else None
        if current_seg_set and current_seg_set == prev_seg_set:
            gid = group_counter - 1
        else:
            gid = group_counter
            group_counter += 1
        prev_seg_set = current_seg_set

        src = w.source if w.source in ("transcription", "whisper_plus_vocal_onset", "vocal_onset_only", "interpolated", "vocal_onset") else default_source

        conf = 0.5
        if src == "whisper_plus_vocal_onset":
            conf = 0.8
        elif src == "transcription":
            conf = 0.7
        elif src == "vocal_onset_only":
            conf = 0.6
        elif src == "interpolated":
            conf = 0.3

        assigns_in_group = [a for a in assignments if a.group_id == gid]
        group_text = " ".join([a.text for a in assigns_in_group] + [w.text]) if assigns_in_group else None

        assignments.append(WordAssignment(
            assignment_idx=wi,
            text=w.text,
            word_index=wi,
            group_id=gid if current_seg_set else None,
            group_text=group_text if current_seg_set else None,
            segment_indices=seg_indices,
            start=w.start,
            end=w.end,
            source=src,
            confidence=conf,
        ))

    if assignments:
        for a in assignments:
            if a.group_id is not None:
                group_members = [x for x in assignments if x.group_id == a.group_id]
                group_text = " ".join(x.text for x in group_members)
                for m in group_members:
                    m.group_text = group_text

    return assignments
