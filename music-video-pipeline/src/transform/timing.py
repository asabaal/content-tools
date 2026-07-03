"""Timing / alignment transformations.

Transformations that re-derive lyric timing for a selected region from a named
vocal stem. Unlike the visual transforms, these write a journaled
``timing_overrides`` block into ``script.json``; the renderer merges that block
over ``lyrics_synced.json`` so the override wins at render time. Because the
overrides live inside ``ctx.script``, the existing groupoid machinery (Journal
inverse, idempotent recipe re-application) covers them with no core changes.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .core import REGISTRY, ScriptContext, Transformation
from .selectors import resolve_line_indices
from lyrics.synchronizer import snap_to_nearest_beat

logger = logging.getLogger(__name__)

# How far around the region's current span we look for candidate stem segments.
_WINDOW_PAD = 4.0
# Per-line word/line padding so captions lead/trail the audio slightly.
_LINE_LEAD = 0.05
_LINE_TRAIL = 0.05
# Below this lyric-vs-stem word match ratio we refuse to override a line.
_MIN_MATCH_RATIO = 0.5
# When distributing a timing group across its words, snap a word's even-split
# start to the nearest vocal onset within this tolerance (seconds).
_ONSET_SNAP_TOLERANCE = 0.08


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _stem_transcription_path(project_dir: Path, stem: str) -> Path:
    data_dir = project_dir / "data"
    return data_dir / f"vocal_transcription_{stem}.json"


class RealignFromStem(Transformation):
    """Re-align a region's lyric timing from a chosen vocal stem.

    Selector resolves to line indices (any section selector, plus the explicit
    ``{"lines": [...]}`` form). ``params``:

    - ``stem`` (required): vocal stem to align from, e.g. ``"backing_vocals"``,
      ``"lead_vocals"``, or ``"combined_vocals"``. The corresponding
      ``vocal_transcription_<stem>.json`` must exist in ``data/``.
    - ``snap`` (default ``true``): snap line boundaries to the nearest beat
      (from ``analysis.json``) and word starts to vocal onsets (from
      ``vocal_onsets.json``) when within tolerance.
    - ``min_match_ratio`` (default ``0.5``): skip overriding a line whose
      lyric-vs-stem word match falls below this.

    For each successfully realigned line the transform writes
    ``script["timing_overrides"]["<line_idx>"] = {"start","end","words":[...]}``
    plus a ``_provenance`` record (stem, match ratio, skip reason if any).
    """

    name = "realign_from_stem"
    description = "Re-derive lyric timing for a region from a named vocal stem"

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        stem = params.get("stem")
        if not stem:
            raise ValueError("realign_from_stem requires a 'stem' param")
        snap = bool(params.get("snap", True))
        min_match_ratio = float(params.get("min_match_ratio", _MIN_MATCH_RATIO))

        synced_lines: List[dict] = list((ctx.lyrics_synced or {}).get("lines", []) or [])
        if not synced_lines:
            raise ValueError("realign_from_stem requires lyrics_synced lines in the context")

        target_indices = ctx.line_indices(selector or None)
        target_indices = [i for i in target_indices if 0 <= i < len(synced_lines)]
        if not target_indices:
            raise ValueError(f"realign_from_stem selector matched no lines: {selector!r}")

        if ctx.project_dir is None:
            raise ValueError("realign_from_stem requires project_dir in the context")
        trans_path = _stem_transcription_path(Path(ctx.project_dir), stem)
        transcription = _load_json(trans_path)
        if not transcription:
            raise FileNotFoundError(
                f"realign_from_stem: stem transcription not found: {trans_path}"
            )
        segments: List[dict] = transcription.get("segments", []) or []
        if not segments:
            raise ValueError(f"realign_from_stem: no segments in {trans_path.name}")

        # Import lazily so the transform module stays free of heavy deps at import.
        from lyrics.alignment_analyzer import _align_lyrics_to_segments, align_words_from_segments
        from lyrics.parser import LyricLine
        from lyrics.synchronizer import (
            snap_to_nearest_beat,
            reconcile_region_boundaries,
        )

        beat_times = self._load_beat_times(Path(ctx.project_dir))
        onset_times = self._load_onset_times(Path(ctx.project_dir))

        # Build region inputs and the segment search window from current timing.
        region_lines_in: List[LyricLine] = []
        for li in target_indices:
            base = synced_lines[li]
            region_lines_in.append(
                LyricLine(
                    index=li,
                    text=base.get("text", ""),
                    start=float(base.get("start", 0.0)),
                    end=float(base.get("end", 0.0)),
                )
            )

        region_start = min(l.start for l in region_lines_in) - _WINDOW_PAD
        region_end = max(l.end for l in region_lines_in) + _WINDOW_PAD
        windowed = [s for s in segments if self._seg_overlap(s, region_start, region_end)]
        if not windowed:
            # Fall back to the full transcription if the window caught nothing.
            windowed = list(segments)

        line_to_segs, match_ratios, _, _ = _align_lyrics_to_segments(region_lines_in, windowed)
        # _align_lyrics_to_segments indices are positional into region_lines_in.
        pos_to_global = {pos: target_indices[pos] for pos in range(len(target_indices))}

        overrides = dict(ctx.script.get("timing_overrides", {}) or {})
        overrides.pop("_provenance", None)
        provenance: Dict[str, Any] = {"stem": stem, "snap": snap, "lines": {}}

        # First pass: derive raw line/word timing from the stem.
        realigned: List[Optional[dict]] = []
        for pos, line in enumerate(region_lines_in):
            seg_idxs = line_to_segs.get(pos, [])
            ratio = match_ratios.get(pos, 0.0)
            global_idx = pos_to_global[pos]

            if not seg_idxs or ratio < min_match_ratio:
                provenance["lines"][str(global_idx)] = {
                    "stem": stem,
                    "match_ratio": round(ratio, 3),
                    "skipped": True,
                    "reason": "no_segment" if not seg_idxs else "low_match",
                }
                realigned.append(None)
                continue

            # Map positional seg indices back to the windowed/segment list.
            resolved = self._resolve_segment_indices(seg_idxs, segments, windowed)
            prev_end = self._previous_end(synced_lines, target_indices, pos)

            words = align_words_from_segments(
                lyric_text=line.text,
                matched_segments=resolved,
                segments=segments,
                line_start=line.start,
                line_end=line.end,
                onset_times=onset_times if snap else None,
                prev_line_end=prev_end,
            )
            if not words:
                provenance["lines"][str(global_idx)] = {
                    "stem": stem,
                    "match_ratio": round(ratio, 3),
                    "skipped": True,
                    "reason": "no_word_timing",
                }
                realigned.append(None)
                continue

            self._finalize_words(words, beat_times if snap else None)
            start = round(words[0]["start"] - _LINE_LEAD, 3)
            end = round(words[-1]["end"] + _LINE_TRAIL, 3)
            if end <= start:
                end = round(start + 0.2, 3)

            entry = {
                "start": start,
                "end": end,
                "words": [
                    {"word": w["word"], "start": w["start"], "end": w["end"]}
                    for w in words
                ],
            }
            realigned.append(entry)
            provenance["lines"][str(global_idx)] = {
                "stem": stem,
                "match_ratio": round(ratio, 3),
                "segments": resolved,
            }

        # Neighbour clamps: the unchanged lines immediately outside the region.
        prev_end = self._outer_prev_end(synced_lines, target_indices)
        next_start = self._outer_next_start(synced_lines, target_indices)

        # Second pass: reconcile sequential boundaries, then commit.
        present = [r for r in realigned if r is not None]
        reconcile_region_boundaries(present, prev_end=prev_end, next_start=next_start)

        for pos, entry in enumerate(realigned):
            if entry is None:
                continue
            global_idx = pos_to_global[pos]
            overrides[str(global_idx)] = {
                "start": round(entry["start"], 3),
                "end": round(entry["end"], 3),
                "words": entry["words"],
            }

        overrides["_provenance"] = provenance
        ctx.script["timing_overrides"] = overrides

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _seg_overlap(seg: dict, lo: float, hi: float) -> bool:
        s = float(seg.get("start", 0.0))
        e = float(seg.get("end", s))
        return s <= hi and e >= lo

    @staticmethod
    def _resolve_segment_indices(
        pos_idxs: List[int], full_segments: List[dict], windowed: List[dict]
    ) -> List[int]:
        """Map positional indices into ``windowed`` back to indices in ``full_segments``.

        ``_align_lyrics_to_segments`` returns indices into whatever segment list
        it was given. We pass the windowed list, so resolve against the full
        transcription by matching on (start, end, text) identity.
        """
        out: List[int] = []
        for pi in pos_idxs:
            if pi < 0 or pi >= len(windowed):
                continue
            seg = windowed[pi]
            for fi, full in enumerate(full_segments):
                if (
                    full.get("start") == seg.get("start")
                    and full.get("end") == seg.get("end")
                    and full.get("text") == seg.get("text")
                ):
                    out.append(fi)
                    break
        return sorted(set(out))

    @staticmethod
    def _finalize_words(words: List[dict], beat_times: Optional[np.ndarray]) -> None:
        """Round and (optionally) snap word starts; guarantee positive durations."""
        snap = None
        if beat_times is not None and len(beat_times):
            from lyrics.synchronizer import snap_to_nearest_beat

            def snap(t: float) -> float:
                return snap_to_nearest_beat(t, beat_times)

        for w in words:
            start = float(w["start"])
            if snap is not None:
                start = snap(start)
            end = float(w["end"])
            if end <= start:
                end = start + 0.04
            w["start"] = round(start, 3)
            w["end"] = round(end, 3)

    @staticmethod
    def _previous_end(
        synced_lines: List[dict], target_indices: List[int], pos: int
    ) -> float:
        """End time of the realigned line just before ``pos`` (region-internal)."""
        for back in range(pos - 1, -1, -1):
            li = synced_lines[target_indices[back]]
            return float(li.get("end", 0.0))
        return 0.0

    @staticmethod
    def _outer_prev_end(synced_lines: List[dict], target_indices: List[int]) -> Optional[float]:
        first = target_indices[0]
        if first <= 0:
            return None
        return float(synced_lines[first - 1].get("end", 0.0))

    @staticmethod
    def _outer_next_start(synced_lines: List[dict], target_indices: List[int]) -> Optional[float]:
        last = target_indices[-1]
        if last >= len(synced_lines) - 1:
            return None
        return float(synced_lines[last + 1].get("start", 0.0))

    @staticmethod
    def _load_beat_times(project_dir: Path) -> np.ndarray:
        analysis = _load_json(project_dir / "data" / "analysis.json")
        if not analysis:
            return np.asarray([], dtype=float)
        return np.asarray(analysis.get("beat_times", []) or [], dtype=float)

    @staticmethod
    def _load_onset_times(project_dir: Path) -> Optional[np.ndarray]:
        onsets = _load_json(project_dir / "data" / "vocal_onsets.json")
        if not onsets:
            return None
        times = onsets.get("onset_times") or []
        if not times:
            return None
        return np.asarray(times, dtype=float)


REGISTRY.register(RealignFromStem())


class DistributeTimingGroups(Transformation):
    """Distribute human-assigned timing groups into per-word ``timing_overrides``.

    Consumes ``data/timing_groups.json`` produced by the lyrics timing editor:
    a list of groups, each binding a contiguous run of canonical lyric words to
    ONE time range. The editor intentionally does NOT split a group across its
    words -- that is this transform's job. For each group we carve its
    ``[start, end]`` into per-word slices, snapping word starts to the nearest
    vocal onset (within tolerance) and optionally to beats, so the result reveals
    word-by-word in the renderer instead of lighting up the whole group at once.

    ``params``:
    - ``groups_file`` (default ``timing_groups.json``): filename in ``data/``.
    - ``snap_onsets`` (default ``True``): snap word starts to vocal onsets from
      ``vocal_onsets.json`` when within ``_ONSET_SNAP_TOLERANCE``.
    - ``snap_beats`` (default ``False``): additionally snap to beats from
      ``analysis.json`` when within ``BEAT_SNAP_TOLERANCE``.

    Writes ``script["timing_overrides"]["<line_idx>"] = {"start","end","words":[...]}``
    plus a ``_provenance`` block recording the source group for each line.
    """

    name = "distribute_timing_groups"
    description = "Distribute human-assigned timing groups into per-word timing_overrides"

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        groups_file = params.get("groups_file", "timing_groups.json")
        snap_onsets = bool(params.get("snap_onsets", True))
        snap_beats = bool(params.get("snap_beats", False))

        if ctx.project_dir is None:
            raise ValueError("distribute_timing_groups requires project_dir in the context")
        groups_path = Path(ctx.project_dir) / "data" / groups_file
        data = _load_json(groups_path)
        if not data:
            raise FileNotFoundError(
                f"distribute_timing_groups: groups file not found: {groups_path}"
            )
        groups: List[dict] = data.get("groups", []) or []
        if not groups:
            raise ValueError(f"distribute_timing_groups: no groups in {groups_path.name}")

        synced_lines: List[dict] = list((ctx.lyrics_synced or {}).get("lines", []) or [])
        if not synced_lines:
            raise ValueError("distribute_timing_groups requires lyrics_synced lines in the context")

        beat_times = RealignFromStem._load_beat_times(Path(ctx.project_dir)) if snap_beats else np.asarray([], dtype=float)
        onset_times = RealignFromStem._load_onset_times(Path(ctx.project_dir)) if snap_onsets else None

        # group entries by line, preserving order
        by_line: Dict[int, List[dict]] = {}
        for g in groups:
            li = int(g.get("synced_line_idx", -1))
            by_line.setdefault(li, []).append(g)

        overrides = dict(ctx.script.get("timing_overrides", {}) or {})
        overrides.pop("_provenance", None)
        provenance: Dict[str, Any] = {"source": "timing_groups", "lines": {}}

        for li in sorted(by_line.keys()):
            if li < 0 or li >= len(synced_lines):
                continue
            line_groups = sorted(by_line[li], key=lambda g: g.get("start", 0.0))
            words_out: List[dict] = []
            for g in line_groups:
                start = float(g.get("start"))
                end = float(g.get("end"))
                if end <= start:
                    end = round(start + 0.2, 3)
                word_idxs = list(g.get("word_indices", []) or [])
                word_texts = self._word_texts(synced_lines[li], word_idxs)
                if not word_texts:
                    continue
                distributed = self._distribute_group(
                    word_texts, start, end,
                    onset_times=onset_times, beat_times=beat_times if snap_beats else None,
                )
                words_out.extend(distributed)
            if not words_out:
                continue
            # ensure chronological within the line (touch up any onset-snap inversions)
            words_out = self._enforce_chronological(words_out)
            line_start = round(words_out[0]["start"] - _LINE_LEAD, 3)
            line_end = round(words_out[-1]["end"] + _LINE_TRAIL, 3)
            if line_end <= line_start:
                line_end = round(line_start + 0.2, 3)
            overrides[str(li)] = {
                "start": line_start,
                "end": line_end,
                "words": [
                    {"word": w["word"], "start": w["start"], "end": w["end"]}
                    for w in words_out
                ],
            }
            provenance["lines"][str(li)] = {
                "distributed_from": "timing_groups",
                "groups": [
                    {
                        "text": g.get("text", ""),
                        "word_indices": list(g.get("word_indices", []) or []),
                        "start": float(g.get("start")),
                        "end": float(g.get("end")),
                        "source": g.get("source"),
                    }
                    for g in line_groups
                ],
            }

        overrides["_provenance"] = provenance
        ctx.script["timing_overrides"] = overrides

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _word_texts(synced_line: dict, word_idxs: List[int]) -> List[str]:
        """Canonical word texts for the indices, from the synced line's words."""
        synced_words = synced_line.get("words", []) or []
        out = []
        for wi in word_idxs:
            if 0 <= wi < len(synced_words):
                w = synced_words[wi]
                out.append(w.get("text", w.get("word", "")))
            else:
                out.append("")
        return [t for t in out if t]

    @staticmethod
    def _distribute_group(
        word_texts: List[str],
        start: float,
        end: float,
        onset_times: Optional[np.ndarray] = None,
        beat_times: Optional[np.ndarray] = None,
    ) -> List[dict]:
        """Carve ``[start, end]`` into per-word slices for the given words.

        Even split as the baseline; each word start is then snapped to the
        nearest onset (and optionally beat) within tolerance. The final word's
        end is always the group's ``end`` so the group fully covers its span.
        """
        n = len(word_texts)
        if n == 0:
            return []
        if n == 1:
            return [{"word": word_texts[0], "start": round(start, 3), "end": round(end, 3)}]
        span = end - start
        per = span / n
        raw = [(start + i * per, start + (i + 1) * per) for i in range(n)]

        snapped_starts = []
        for i, (s, _e) in enumerate(raw):
            snapped = s
            if onset_times is not None and onset_times.size:
                snapped = DistributeTimingGroups._snap_to_nearest(snapped, onset_times, _ONSET_SNAP_TOLERANCE)
            if beat_times is not None and beat_times.size:
                snapped = snap_to_nearest_beat(snapped, beat_times)
            snapped_starts.append(snapped)

        words: List[dict] = []
        for i, text in enumerate(word_texts):
            ws = snapped_starts[i]
            # end = next word's snapped start, or the group end for the last word
            we = snapped_starts[i + 1] if i + 1 < n else end
            if we <= ws:
                we = round(ws + min(per, 0.1), 3)
            words.append({"word": text, "start": round(ws, 3), "end": round(we, 3)})
        return words

    @staticmethod
    def _snap_to_nearest(time: float, onset_times: np.ndarray, tolerance: float) -> float:
        idx = int(np.argmin(np.abs(onset_times - time)))
        nearest = float(onset_times[idx])
        if abs(nearest - time) <= tolerance:
            return nearest
        return time

    @staticmethod
    def _enforce_chronological(words: List[dict]) -> List[dict]:
        """Fix any inversion introduced by snapping so starts stay non-decreasing
        and every word has positive duration. Mutates in place and returns."""
        for i in range(1, len(words)):
            prev_end = words[i - 1]["end"]
            if words[i]["start"] < prev_end:
                words[i]["start"] = prev_end
            if words[i]["end"] <= words[i]["start"]:
                words[i]["end"] = round(words[i]["start"] + 0.04, 3)
        return words


REGISTRY.register(DistributeTimingGroups())


__all__ = ["RealignFromStem", "DistributeTimingGroups"]
