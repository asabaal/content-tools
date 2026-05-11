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

    def to_dict(self) -> dict:
        d = {
            "lyric_index": self.lyric_index,
            "lyric_text": self.lyric_text,
            "matched_segments": self.matched_segments,
            "transcription_text": self.transcription_text,
            "word_match_ratio": round(self.word_match_ratio, 3),
            "is_split": self.is_split,
        }
        if self.transcription_start is not None:
            d["transcription_start"] = round(self.transcription_start, 3)
            d["transcription_end"] = round(self.transcription_end, 3)
        if self.boundary_quality is not None:
            d["boundary_quality"] = round(self.boundary_quality, 3)
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
) -> Tuple[Dict[int, List[int]], Dict[int, float], Dict[int, str]]:
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

    matcher = SequenceMatcher(None, lw, tw)

    line_to_segs: Dict[int, set] = defaultdict(set)
    line_matched_words: Dict[int, int] = defaultdict(int)
    line_total_words: Dict[int, int] = defaultdict(int)

    for li, line in enumerate(lines):
        line_total_words[li] = len(_normalize(line.text).split())

    for i, j, n in matcher.get_matching_blocks():
        for k in range(n):
            li = flat_lyric[i + k][1]
            si = flat_trans[j + k][1]
            line_to_segs[li].add(si)
            line_matched_words[li] += 1

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

    return ordered_line_to_segs, match_ratios, seg_texts


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
        line_segs, match_ratios, seg_texts = _align_lyrics_to_segments(non_empty, transcription_segments)

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

            matches.append(LineMatch(
                lyric_index=line.index,
                lyric_text=line.text,
                matched_segments=seg_indices,
                transcription_text=trans_text if trans_text else None,
                word_match_ratio=ratio,
                transcription_start=t_start,
                transcription_end=t_end,
                is_split=is_split,
            ))
    else:
        for line in non_empty:
            matches.append(LineMatch(
                lyric_index=line.index,
                lyric_text=line.text,
            ))

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
    unmatched = sum(1 for m in matches if m.word_match_ratio <= 0.3)
    lines_split = sum(1 for m in matches if m.is_split)

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
        boundary_avg_quality=avg_quality,
        recommendation=rec,
        recommendation_reason=reason,
        onset_cluster_details=cluster_details,
    )
