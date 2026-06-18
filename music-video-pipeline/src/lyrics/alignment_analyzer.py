from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

import numpy as np

from audio.features import AudioFeatures
from lyrics.parser import LyricLine

logger = logging.getLogger(__name__)

WORD_PACE_MIN = 0.15
WORD_PACE_MAX = 0.8
MAX_GAP = 5.0


@dataclass
class WordTiming:
    word: str
    start: float
    end: float
    source: str

    def to_dict(self) -> dict:
        return {
            "word": self.word,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "source": self.source,
        }


@dataclass
class LineMatch:
    lyric_index: int
    lyric_text: str
    matched_segments: List[int] = field(default_factory=list)
    transcription_text: Optional[str] = None
    word_match_ratio: float = 0.0
    transcription_start: Optional[float] = None
    transcription_end: Optional[float] = None
    boundary_quality: Optional[float] = None
    is_split: bool = False
    recovery_method: Optional[str] = None
    word_timings: Optional[List[WordTiming]] = None

    def to_dict(self) -> dict:
        d = {
            "lyric_index": self.lyric_index,
            "lyric_text": self.lyric_text,
            "matched_segments": self.matched_segments,
            "transcription_text": self.transcription_text,
            "word_match_ratio": round(self.word_match_ratio, 3),
            "is_split": self.is_split,
        }
        if self.recovery_method is not None:
            d["recovery_method"] = self.recovery_method
        if self.transcription_start is not None:
            d["transcription_start"] = round(self.transcription_start, 3)
            d["transcription_end"] = round(self.transcription_end, 3)
        if self.boundary_quality is not None:
            d["boundary_quality"] = round(self.boundary_quality, 3)
        if self.word_timings is not None:
            d["word_timings"] = [wt.to_dict() for wt in self.word_timings]
        return d


@dataclass
class AlignmentAnalysis:
    line_matches: List[LineMatch]
    total_lines: int
    transcription_segment_count: int
    exact_matches: int
    partial_matches: int
    unmatched_lines: int
    lines_split: int
    lines_recovered: int
    boundary_avg_quality: float
    recommendation: str
    recommendation_reason: str
    onset_count: int = 0
    onset_cluster_count: int = 0
    onset_cluster_details: Optional[List[dict]] = None

    def to_dict(self) -> dict:
        return {
            "line_matches": [m.to_dict() for m in self.line_matches],
            "summary": {
                "total_lines": self.total_lines,
                "transcription_segment_count": self.transcription_segment_count,
                "onset_count": self.onset_count,
                "onset_cluster_count": self.onset_cluster_count,
                "exact_matches": self.exact_matches,
                "partial_matches": self.partial_matches,
                "unmatched_lines": self.unmatched_lines,
                "lines_split": self.lines_split,
                "lines_recovered": self.lines_recovered,
                "boundary_avg_quality": round(self.boundary_avg_quality, 3),
                "recommendation": self.recommendation,
                "recommendation_reason": self.recommendation_reason,
                "clustering_note": "Onset clustering is not functional for sung vocals. Transcription-based alignment is used instead.",
            },
            "onset_cluster_details": self.onset_cluster_details,
        }

    def save(self, path) -> None:
        import json
        from pathlib import Path

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def _normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def _score_boundary_quality(
    start: float, end: float, word_count: int, next_start: Optional[float]
) -> float:
    duration = end - start
    if duration <= 0 or word_count <= 0:
        return 0.0

    pace = duration / word_count
    pace_score = 1.0
    if pace < WORD_PACE_MIN:
        pace_score = pace / WORD_PACE_MIN
    elif pace > WORD_PACE_MAX:
        pace_score = max(0, 1.0 - (pace - WORD_PACE_MAX) / WORD_PACE_MAX)

    gap_score = 1.0
    if next_start is not None:
        gap = next_start - end
        if gap < 0:
            gap_score = 0.0
        elif gap > MAX_GAP:
            gap_score = max(0, 1.0 - (gap - MAX_GAP) / MAX_GAP)

    return (pace_score + gap_score) / 2.0


def _cluster_onsets(onset_times: np.ndarray) -> List[Tuple[float, float]]:
    if len(onset_times) < 2:
        if len(onset_times) == 1:
            return [(float(onset_times[0]), float(onset_times[0]) + 1.0)]
        return []

    gaps = np.diff(onset_times)
    median_gap = float(np.median(gaps))
    threshold = max(median_gap * 3.0, 0.8)

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


def _align_lyrics_to_segments(
    lines: List[LyricLine], segments: List[dict]
) -> Tuple[Dict[int, List[int]], Dict[int, float], Dict[int, str], float]:
    flat_lyric = []
    for li, line in enumerate(lines):
        for w in _normalize(line.text).split():
            flat_lyric.append((w, li))

    flat_trans = []
    for si, seg in enumerate(segments):
        for w in _normalize(seg.get("text", "")).split():
            flat_trans.append((w, si))

    lw = [w for w, _ in flat_lyric]
    tw = [w for w, _ in flat_trans]

    matcher = SequenceMatcher(None, lw, tw, autojunk=False)

    line_to_segs: Dict[int, set] = defaultdict(set)
    line_matched_words: Dict[int, int] = defaultdict(int)
    line_total_words: Dict[int, int] = defaultdict(int)
    total_matched_words = 0

    for li, line in enumerate(lines):
        line_total_words[li] = len(_normalize(line.text).split())

    for i, j, n in matcher.get_matching_blocks():
        total_matched_words += n
        for k in range(n):
            li = flat_lyric[i + k][1]
            si = flat_trans[j + k][1]
            line_to_segs[li].add(si)
            line_matched_words[li] += 1

    unmatched_lines = [li for li in range(len(lines)) if line_matched_words[li] == 0]
    if unmatched_lines and segments:
        matched_line_times: Dict[int, tuple] = {}
        for li in range(len(lines)):
            segs = line_to_segs.get(li, set())
            if segs:
                starts = [segments[si]["start"] for si in segs if si < len(segments)]
                ends = [segments[si]["end"] for si in segs if si < len(segments)]
                if starts and ends:
                    matched_line_times[li] = (min(starts), max(ends))

        seg_time_list = [(si, seg["start"], seg["end"]) for si, seg in enumerate(segments)]

        for li in unmatched_lines:
            prev_li = None
            next_li = None
            for other in range(li - 1, -1, -1):
                if other in matched_line_times:
                    prev_li = other
                    break
            for other in range(li + 1, len(lines)):
                if other in matched_line_times:
                    next_li = other
                    break

            t_start = 0.0
            t_end = segments[-1]["end"] if segments else 0.0

            if prev_li is not None and next_li is not None:
                t_start = matched_line_times[prev_li][1]
                t_end = matched_line_times[next_li][0]
            elif prev_li is not None:
                t_start = matched_line_times[prev_li][1]
            elif next_li is not None:
                t_end = matched_line_times[next_li][0]

            if t_end <= t_start:
                gap = t_end - t_start if t_end > t_start else 5.0
                t_start = t_start - gap
                t_end = t_end + gap

            candidate_segs = [si for si, s, e in seg_time_list if s <= t_end + 1.0 and e >= t_start - 1.0]

            lyric_words = _normalize(lines[li].text).split()
            if not lyric_words:
                continue
            lyric_word_set = set(lyric_words)

            best_si = None
            best_overlap = 0
            used_segs = set()
            for other_li, other_segs in line_to_segs.items():
                if other_li != li:
                    used_segs.update(other_segs)

            for si in candidate_segs:
                if si in used_segs:
                    continue
                seg_words = _normalize(segments[si].get("text", "")).split()
                if not seg_words:
                    continue
                overlap = len(lyric_word_set & set(seg_words))
                ratio = overlap / len(lyric_words)
                if ratio > best_overlap:
                    best_overlap = overlap
                    best_si = si

            if best_si is not None and best_overlap / max(len(lyric_words), 1) >= 0.3:
                line_to_segs[li].add(best_si)
                line_matched_words[li] = best_overlap

    ordered_line_to_segs: Dict[int, List[int]] = {}
    for li in range(len(lines)):
        segs = sorted(line_to_segs.get(li, set()))
        ordered_line_to_segs[li] = segs

    match_ratios: Dict[int, float] = {}
    for li in range(len(lines)):
        total = line_total_words.get(li, 1)
        matched = line_matched_words.get(li, 0)
        match_ratios[li] = matched / total if total > 0 else 0.0

    seg_texts: Dict[int, str] = {}
    for li in range(len(lines)):
        seg_indices = ordered_line_to_segs.get(li, [])
        if seg_indices:
            parts = [segments[si].get("text", "") for si in seg_indices]
            seg_texts[li] = " | ".join(parts)
        else:
            seg_texts[li] = ""

    reverse_coverage = total_matched_words / max(len(tw), 1) if tw else 0.0

    return ordered_line_to_segs, match_ratios, seg_texts, reverse_coverage


def _count_syllables(text: str) -> int:
    normalized = _normalize(text)
    if not normalized:
        return 0
    words = normalized.split()
    count = 0
    for word in words:
        vowels = re.findall(r"[aeiouy]+", word)
        count += max(1, len(vowels)) if vowels else 1
    return count


def _group_onsets_by_gap(onset_times: np.ndarray, gap_threshold: float = 1.0) -> List[np.ndarray]:
    if len(onset_times) == 0:
        return []
    groups = [[float(onset_times[0])]]
    for i in range(1, len(onset_times)):
        if float(onset_times[i]) - groups[-1][-1] > gap_threshold:
            groups.append([])
        groups[-1].append(float(onset_times[i]))
    return [np.array(g) for g in groups]


def _snap_word_starts_to_onsets(
    timings: List[WordTiming],
    onset_times: Optional[np.ndarray],
    first_segment_words: Optional[set] = None,
    prev_line_end: float = 0.0,
) -> None:
    if onset_times is None or len(onset_times) == 0 or not timings:
        return

    if first_segment_words is None:
        first_segment_words = set()

    for i, wt in enumerate(timings):
        if wt.source != "transcription":
            continue

        is_first_in_seg = (_normalize(wt.word), round(wt.start, 3)) in first_segment_words

        window_start = wt.start - 0.3
        window_end = wt.end
        mask = (onset_times >= window_start) & (onset_times <= window_end)
        candidates = onset_times[mask]

        if len(candidates) == 0:
            continue

        nearest = candidates[np.argmin(np.abs(candidates - wt.start))]
        gap = float(nearest) - wt.start

        if abs(gap) <= 0.1:
            continue

        if gap > 0:
            if not is_first_in_seg:
                continue
            new_start = float(nearest)
        else:
            boundary = prev_line_end if i == 0 else timings[i - 1].end
            if float(nearest) < boundary:
                continue
            new_start = float(nearest)

        if wt.end - new_start < 0.05:
            continue

        wt.start = new_start


def _compute_word_timings(
    lyric_text: str,
    matched_segments: List[int],
    transcription_segments: List[dict],
    line_start: Optional[float],
    line_end: Optional[float],
    onset_times: Optional[np.ndarray] = None,
    prev_line_end: float = 0.0,
) -> Optional[List[WordTiming]]:
    if not matched_segments:
        return None

    lyric_words_raw = lyric_text.split()
    if not lyric_words_raw:
        return None

    lyric_words_norm = [_normalize(w) for w in lyric_words_raw]

    trans_words_raw: List[dict] = []
    for si in matched_segments:
        seg = transcription_segments[si]
        for w in seg.get("words", []):
            trans_words_raw.append(w)

    if not trans_words_raw:
        return None

    first_segment_words: set = set()
    for si in matched_segments:
        seg = transcription_segments[si]
        seg_words = seg.get("words", [])
        if seg_words:
            fw = seg_words[0]
            first_segment_words.add((_normalize(fw.get("word", "")), round(float(fw.get("start", 0)), 3)))

    trans_words_norm = [_normalize(w.get("word", "")) for w in trans_words_raw]

    matcher = SequenceMatcher(None, lyric_words_norm, trans_words_norm)

    lyric_to_trans: Dict[int, int] = {}
    for i, j, n in matcher.get_matching_blocks():
        for k in range(n):
            lyric_to_trans[i + k] = j + k

    used_trans = set(lyric_to_trans.values())
    unmatched = [li for li in range(len(lyric_words_raw)) if li not in lyric_to_trans]
    changed = True
    while changed and unmatched:
        changed = False
        still_unmatched = []
        for li in unmatched:
            prev_trans = lyric_to_trans.get(li - 1)
            next_trans = lyric_to_trans.get(li + 1)
            if prev_trans is not None and next_trans is not None:
                expected = prev_trans + 1
                if expected == next_trans - 1 and expected not in used_trans and expected < len(trans_words_raw):
                    lyric_to_trans[li] = expected
                    used_trans.add(expected)
                    changed = True
                else:
                    still_unmatched.append(li)
            elif prev_trans is not None and li == len(lyric_words_raw) - 1:
                expected = prev_trans + 1
                if expected not in used_trans and expected < len(trans_words_raw):
                    lyric_to_trans[li] = expected
                    used_trans.add(expected)
                    changed = True
                else:
                    still_unmatched.append(li)
            elif next_trans is not None and li == 0:
                expected = next_trans - 1
                if expected >= 0 and expected not in used_trans:
                    lyric_to_trans[li] = expected
                    used_trans.add(expected)
                    changed = True
                else:
                    still_unmatched.append(li)
            else:
                still_unmatched.append(li)
        unmatched = still_unmatched

    timings: List[WordTiming] = []
    for li, raw_word in enumerate(lyric_words_raw):
        if li in lyric_to_trans:
            tw = trans_words_raw[lyric_to_trans[li]]
            ws = float(tw["start"])
            we = float(tw["end"])
            if we <= ws:
                we = ws + 0.04
            timings.append(WordTiming(
                word=raw_word,
                start=ws,
                end=we,
                source="transcription",
            ))
        else:
            prev_end = line_start if line_start is not None else 0.0
            for pli in range(li - 1, -1, -1):
                if pli in lyric_to_trans:
                    prev_end = float(trans_words_raw[lyric_to_trans[pli]]["end"])
                    break

            next_start = line_end if line_end is not None else prev_end + 0.3
            for nli in range(li + 1, len(lyric_words_raw)):
                if nli in lyric_to_trans:
                    next_start = float(trans_words_raw[lyric_to_trans[nli]]["start"])
                    break

            if next_start <= prev_end:
                next_start = prev_end + 0.1

            timings.append(WordTiming(
                word=raw_word,
                start=prev_end,
                end=next_start,
                source="interpolated",
            ))

    _snap_word_starts_to_onsets(timings, onset_times, first_segment_words, prev_line_end)

    return timings


def _compute_onset_word_timings(
    lyric_text: str,
    onset_times: np.ndarray,
) -> Optional[List[WordTiming]]:
    if len(onset_times) == 0:
        return None

    words = lyric_text.split()
    if not words:
        return None

    syllable_counts = [_count_syllables(w) for w in words]
    total_syllables = sum(syllable_counts)

    range_start = float(onset_times[0])
    range_end = float(onset_times[-1]) + 0.1

    timings: List[WordTiming] = []
    onset_idx = 0
    for wi, word in enumerate(words):
        frac = syllable_counts[wi] / total_syllables
        word_onset_count = max(1, round(frac * len(onset_times)))

        word_start = float(onset_times[min(onset_idx, len(onset_times) - 1)])
        end_idx = min(onset_idx + word_onset_count, len(onset_times))
        if end_idx < len(onset_times):
            word_end = float(onset_times[end_idx])
        else:
            word_end = range_end

        timings.append(WordTiming(
            word=word,
            start=word_start,
            end=word_end,
            source="onset_syllable",
        ))
        onset_idx = end_idx

    return timings


def _recover_unmatched_lines(
    matches: List[LineMatch],
    vocal_onset_times: Optional[np.ndarray],
    duration: float,
) -> None:
    if vocal_onset_times is None or len(vocal_onset_times) == 0:
        return

    unmatched_indices = [i for i, m in enumerate(matches) if not m.matched_segments]
    if not unmatched_indices:
        return

    for idx in unmatched_indices:
        m = matches[idx]

        range_start = 0.0
        for prev_i in range(idx - 1, -1, -1):
            if matches[prev_i].transcription_end is not None:
                range_start = matches[prev_i].transcription_end
                break

        range_end = duration
        for next_i in range(idx + 1, len(matches)):
            if matches[next_i].transcription_start is not None:
                range_end = matches[next_i].transcription_start
                break

        mask = (vocal_onset_times >= range_start) & (vocal_onset_times <= range_end)
        range_onsets = vocal_onset_times[mask]

        if len(range_onsets) == 0:
            continue

        target_syllables = _count_syllables(m.lyric_text)
        groups = _group_onsets_by_gap(range_onsets)

        best_group = None
        best_score = float("inf")
        for g in groups:
            diff = abs(len(g) - target_syllables)
            score = diff / max(target_syllables, 1)
            if score < best_score:
                best_score = score
                best_group = g

        if best_group is not None and best_score <= 0.5:
            m.transcription_start = round(float(best_group[0]), 3)
            m.transcription_end = round(float(best_group[-1]) + 0.1, 3)
            m.recovery_method = "onset_syllable"
            m.word_timings = _compute_onset_word_timings(m.lyric_text, best_group)


def analyze_alignment(
    lyrics: List[LyricLine],
    transcription_segments: Optional[List[dict]],
    vocal_onset_times: Optional[np.ndarray],
    audio_features: AudioFeatures,
) -> AlignmentAnalysis:
    non_empty = [l for l in lyrics if l.text.strip()]
    n_lines = len(non_empty)

    clusters: List[Tuple[float, float]] = []
    if vocal_onset_times is not None and len(vocal_onset_times) > 0:
        clusters = _cluster_onsets(vocal_onset_times)

    matches: List[LineMatch] = []

    if transcription_segments and len(transcription_segments) > 0:
        line_segs, match_ratios, seg_texts, _ = _align_lyrics_to_segments(non_empty, transcription_segments)

        for i, line in enumerate(non_empty):
            seg_indices = line_segs.get(i, [])
            ratio = match_ratios.get(i, 0.0)
            trans_text = seg_texts.get(i, "")
            is_split = len(seg_indices) > 1

            t_start = None
            t_end = None
            if seg_indices:
                t_start = transcription_segments[seg_indices[0]].get("start")
                t_end = transcription_segments[seg_indices[-1]].get("end")

            prev_end = 0.0
            for pi in range(i - 1, -1, -1):
                prev_match = matches[pi]
                if prev_match.transcription_end is not None:
                    prev_end = prev_match.transcription_end
                    break

            matches.append(LineMatch(
                lyric_index=line.index,
                lyric_text=line.text,
                matched_segments=seg_indices,
                transcription_text=trans_text if trans_text else None,
                word_match_ratio=ratio,
                transcription_start=t_start,
                transcription_end=t_end,
                is_split=is_split,
                word_timings=_compute_word_timings(
                    line.text, seg_indices, transcription_segments, t_start, t_end,
                    onset_times=vocal_onset_times,
                    prev_line_end=prev_end,
                ),
            ))
    else:
        for line in non_empty:
            matches.append(LineMatch(
                lyric_index=line.index,
                lyric_text=line.text,
            ))

    _recover_unmatched_lines(matches, vocal_onset_times, audio_features.duration)

    for i, m in enumerate(matches):
        if m.transcription_start is not None and m.transcription_end is not None:
            word_count = len(m.lyric_text.split())
            next_start = None
            if i + 1 < len(matches) and matches[i + 1].transcription_start is not None:
                next_start = matches[i + 1].transcription_start
            m.boundary_quality = _score_boundary_quality(
                m.transcription_start, m.transcription_end, word_count, next_start
            )

    exact = sum(1 for m in matches if m.word_match_ratio > 0.9)
    partial = sum(1 for m in matches if 0.3 < m.word_match_ratio <= 0.9)
    unmatched = sum(1 for m in matches if m.word_match_ratio <= 0.3 and m.recovery_method is None)
    lines_split = sum(1 for m in matches if m.is_split)
    lines_recovered = sum(1 for m in matches if m.recovery_method is not None)

    quality_scores = [m.boundary_quality for m in matches if m.boundary_quality is not None]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

    has_transcription = transcription_segments is not None and len(transcription_segments) > 0
    if has_transcription:
        rec = "transcription"
        reason = "Transcription-based alignment"
    else:
        rec = "none"
        reason = "No transcription data available"

    cluster_details = None
    if clusters:
        cluster_details = [
            {"start": round(c[0], 3), "end": round(c[1], 3), "duration": round(c[1] - c[0], 3)}
            for c in clusters
        ]

    return AlignmentAnalysis(
        line_matches=matches,
        total_lines=n_lines,
        transcription_segment_count=len(transcription_segments) if transcription_segments else 0,
        onset_cluster_count=len(clusters),
        onset_count=len(vocal_onset_times) if vocal_onset_times is not None else 0,
        exact_matches=exact,
        partial_matches=partial,
        unmatched_lines=unmatched,
        lines_split=lines_split,
        lines_recovered=lines_recovered,
        boundary_avg_quality=avg_quality,
        recommendation=rec,
        recommendation_reason=reason,
        onset_cluster_details=cluster_details,
    )


def detect_transcription_discrepancies(
    lines: List[LyricLine],
    segments: List[dict],
    line_segs: Dict[int, List[int]],
    match_ratios: Dict[int, float],
) -> List[dict]:
    """Detect mismatches between lyrics and transcription for human review.

    Returns a list of discrepancy flags, each describing a potential data
    quality issue where the lyrics and transcription disagree.
    """
    flags: List[dict] = []
    if not lines or not segments:
        return flags

    for li, line in enumerate(lines):
        if not line.text.strip():
            continue

        ratio = match_ratios.get(li, 0.0)
        lyric_text = _normalize(line.text)
        lyric_words = lyric_text.split()

        seg_indices = line_segs.get(li, [])

        if not seg_indices:
            nearest_dist = float('inf')
            nearest_si = None
            for si, seg in enumerate(segments):
                seg_mid = (seg.get("start", 0) + seg.get("end", 0)) / 2
                line_mid = (line.start + line.end) / 2 if line.end > line.start else line.start
                dist = abs(seg_mid - line_mid)
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_si = si

            if nearest_si is not None and nearest_dist <= 10:
                seg = segments[nearest_si]
                seg_text = _normalize(seg.get("text", ""))
                sim = SequenceMatcher(None, lyric_text, seg_text).ratio()
                if sim < 0.5 and lyric_words and seg_text:
                    flags.append({
                        "type": "misheard_text",
                        "line": li,
                        "lyric_text": line.text,
                        "transcribed_text": seg.get("text", ""),
                        "segment_index": nearest_si,
                        "timestamp": f"{seg.get('start', 0):.1f}-{seg.get('end', 0):.1f}",
                        "similarity": round(sim, 2),
                        "description": f"Transcription differs significantly from lyrics (similarity {sim:.0%})",
                        "suggestion": "Check if Whisper misheard the phrase or if lyrics need correction",
                    })
            elif nearest_dist > 10 or nearest_si is None:
                flags.append({
                    "type": "missing_section",
                    "line": li,
                    "lyric_text": line.text,
                    "timestamp": f"{line.start:.1f}-{line.end:.1f}" if line.end > line.start else f"{line.start:.1f}",
                    "description": "No transcription segment found near this lyric line",
                    "suggestion": "Verify vocal content exists at this timestamp, or check if lyrics are correct",
                })
            continue

        if ratio < 0.5:
            seg_texts = [_normalize(segments[si].get("text", "")) for si in seg_indices if si < len(segments)]
            combined_seg = " ".join(seg_texts)
            seg_word_count = len(combined_seg.split())

            lyric_word_set = set(lyric_words)
            seg_word_set = set(combined_seg.split())

            is_repetition = (
                seg_word_count > 0
                and len(lyric_words) > seg_word_count * 2
                and (seg_word_set <= lyric_word_set or lyric_word_set <= seg_word_set)
            )

            if is_repetition:
                flags.append({
                    "type": "repetition_mismatch",
                    "line": li,
                    "lyric_text": line.text,
                    "transcribed_text": " | ".join(segments[si].get("text", "") for si in seg_indices if si < len(segments)),
                    "lyric_word_count": len(lyric_words),
                    "transcribed_word_count": seg_word_count,
                    "timestamp": f"{line.start:.1f}-{line.end:.1f}" if line.end > line.start else f"{line.start:.1f}",
                    "description": f"Transcription has {seg_word_count} words where lyrics expect {len(lyric_words)}",
                    "suggestion": "Verify actual repetition count in the audio — lyrics may need correction",
                })
            else:
                sim = SequenceMatcher(None, lyric_text, combined_seg).ratio()
                if sim < 0.3 and combined_seg:
                    flags.append({
                        "type": "misheard_text",
                        "line": li,
                        "lyric_text": line.text,
                        "transcribed_text": " | ".join(segments[si].get("text", "") for si in seg_indices if si < len(segments)),
                        "timestamp": f"{line.start:.1f}-{line.end:.1f}" if line.end > line.start else f"{line.start:.1f}",
                        "similarity": round(sim, 2),
                        "description": f"Transcription differs significantly from lyrics (similarity {sim:.0%})",
                        "suggestion": "Check if Whisper misheard the phrase or if lyrics need correction",
                    })

    return flags
