#!/usr/bin/env python3
"""Audio-aware word-duration trim simulator (Phase 0/1).

Reads lyrics_synced.json + on-disk audio artifacts (vocal_onsets.json,
vocal_waveforms.json, vocal_transcription.json) to:

  Phase 0: reproduce the dashboard's timing-issue baseline directly from
           word timings (no renderer needed), and reconcile against
           stats.json.
  Phase 1: apply an audio-aware trim + redistribute transform in memory
           and measure the before/after delta across the collection.

The transform is a PURE function over the loaded data; no pipeline files
are written. This lets us validate the approach before touching the codebase.

Usage:
    python scripts/simulate_audio_aware_trim.py -d projects/prophetic-preprint
    python scripts/simulate_audio_aware_trim.py -d projects/prophetic-preprint --baseline-only
    python scripts/simulate_audio_aware_trim.py -d projects/prophetic-preprint --songs a-word,ai-psalm-1
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

OVERFLOW_THRESH = 1.5
UNDERSIZE_THRESH = 0.04
GAP_THRESH = 0.5
MIN_WORD_DURATION = 0.04

PPS = 100  # peaks per second in waveform artifacts


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def _load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class SongData:
    slug: str
    lines: List[dict]                       # lyrics_synced lines
    onsets: List[float]                     # vocal onset_times
    peaks: Optional[List[float]]            # vocal waveform peaks (100 Hz)
    duration: float                         # audio duration
    whisper_words: List[dict]               # flat whisper word list


def load_song(song_dir: Path) -> Optional[SongData]:
    data_dir = song_dir / "data"
    synced = _load_json(data_dir / "lyrics_synced.json")
    if not synced:
        return None
    onsets_json = _load_json(data_dir / "vocal_onsets.json") or {}
    wave_json = _load_json(data_dir / "vocal_waveforms.json") or {}
    trans_json = _load_json(data_dir / "vocal_transcription.json") or {}

    onsets = list(onsets_json.get("onset_times", []))
    peaks = wave_json.get("peaks")
    duration = float(wave_json.get("duration") or trans_json.get("duration") or 0.0)
    whisper_words = []
    for seg in trans_json.get("segments", []):
        whisper_words.extend(seg.get("words", []))
    # fall back to flat words list if segments had none
    if not whisper_words:
        whisper_words = trans_json.get("words", [])

    return SongData(
        slug=song_dir.name,
        lines=synced.get("lines", []),
        onsets=onsets,
        peaks=peaks,
        duration=duration,
        whisper_words=whisper_words,
    )


def discover_songs(collection_dir: Path) -> List[Path]:
    projects = collection_dir / "projects"
    root = projects if projects.is_dir() else collection_dir
    return sorted(d for d in root.iterdir() if d.is_dir())


# --------------------------------------------------------------------------- #
# Issue classification (mirrors cli/commands.py audit logic exactly)
# --------------------------------------------------------------------------- #
def classify_word(start: float, end: float) -> Optional[str]:
    if start >= end:
        return "start_gte_end"
    dur = end - start
    if dur < UNDERSIZE_THRESH:
        return "duration_undersize"
    if dur > OVERFLOW_THRESH:
        return "duration_overflow"
    return None


def compute_issues(lines: List[dict]) -> Counter:
    """Return a Counter of issue_type -> count, mirroring the audit."""
    counts: Counter = Counter()
    for line in lines:
        words = line.get("words", [])
        for wi, w in enumerate(words):
            start = float(w.get("start", 0.0))
            end = float(w.get("end", 0.0))
            itype = classify_word(start, end)
            if itype:
                counts[itype] += 1
            if wi > 0:
                prev = words[wi - 1]
                gap = start - float(prev.get("end", 0.0))
                if gap > GAP_THRESH:
                    counts["gap_from_prev"] += 1
    return counts


# --------------------------------------------------------------------------- #
# Baseline (Phase 0)
# --------------------------------------------------------------------------- #
def baseline_report(songs: List[SongData], stats: Optional[dict]) -> None:
    total = Counter()
    per_song = {}
    for sd in songs:
        c = compute_issues(sd.lines)
        per_song[sd.slug] = c
        total += c

    timing_types = ["duration_overflow", "duration_undersize", "gap_from_prev", "start_gte_end"]
    print("\n" + "=" * 64)
    print("  PHASE 0 — BASELINE (computed from lyrics_synced.json)")
    print("=" * 64)
    print(f"  Songs loaded: {len(songs)}")
    timing_total = sum(total[t] for t in timing_types)
    print(f"  Timing issues (excl. text_overflow): {timing_total}")
    for t in timing_types:
        if total[t]:
            print(f"    {t:<22s} {total[t]}")

    if stats:
        bt = stats.get("by_type", {})
        stats_by_song = {s["song"]: s for s in stats.get("by_song", [])}

        # Identify songs in stats but absent from harness (e.g. mid-rework, no synced file)
        harness_slugs = {sd.slug for sd in songs}
        missing = {s: d for s, d in stats_by_song.items() if s not in harness_slugs}
        missing_overflow = sum(d.get("type_duration_overflow", 0) for d in missing.values())
        missing_undersize = sum(d.get("type_duration_undersize", 0) for d in missing.values())
        missing_gap = sum(d.get("type_gap_from_prev", 0) for d in missing.values())

        print("\n  Reconciliation vs stats.json:")
        for t, moff in [("duration_overflow", missing_overflow),
                        ("duration_undersize", missing_undersize),
                        ("gap_from_prev", missing_gap)]:
            sval = bt.get(t, 0)
            hval = total.get(t, 0)
            # harness + missing-song contributions should equal stats
            recon = hval + moff
            flag = "OK" if recon == sval else f"RESIDUAL ({'+' if recon-sval>0 else ''}{recon-sval})"
            print(f"    {t:<22s} harness={hval:<5d} +missing={moff:<3d} stats={sval:<5d} {flag}")
        print(f"    {'text_overflow':<22s} (not computed by harness; stats={bt.get('text_overflow',0)})")
        print(f"    {'total':<22s} harness_timing={timing_total}  stats_total={stats.get('total_issues')}")
        if missing:
            print(f"\n  Songs in stats but not loadable (no lyrics_synced.json):")
            for slug, d in missing.items():
                print(f"    {slug:<28s} {d.get('issue_count',0)} issues in stats "
                      f"(ovf={d.get('type_duration_overflow',0)} und={d.get('type_duration_undersize',0)} "
                      f"gap={d.get('type_gap_from_prev',0)})")

    # top songs by timing issue count
    ranked = sorted(per_song.items(), key=lambda kv: -sum(kv[1].values()))[:12]
    print("\n  Top 12 songs by timing issues:")
    for slug, c in ranked:
        t = sum(c.values())
        print(f"    {slug:<28s} {t:>4d}  "
              f"ovf={c.get('duration_overflow',0):<3d} und={c.get('duration_undersize',0):<3d} "
              f"gap={c.get('gap_from_prev',0)}")


# --------------------------------------------------------------------------- #
# Audio-aware trim + redistribute (Phase 1)
# --------------------------------------------------------------------------- #
@dataclass
class TrimParams:
    floor_mult: float = 3.0       # speech floor = floor_mult * noise_floor (25th pct)
    tail: float = 0.10            # decay tail added after last energetic sample (s)
    gap: float = 0.03             # min gap to leave before next word start (s)
    max_duration: float = 1.5     # only trim words exceeding this (s)
    mode: str = "fill"            # pure | fill | hybrid
    fill_cap: float = 1.2         # in fill/hybrid, max display duration after gap-fill (s)
    hybrid_threshold: float = 1.0 # in hybrid, only fill gaps larger than this (s)
    rescue_undersize: bool = True # extend/pull undersize words into freed space
    shift_starts: bool = True     # allow pulling undersize starts earlier into freed gap
    rescue_target: float = 0.3    # target duration for rescued undersize words (s)
    fill_margin: float = 0.3      # how far past energy-end to fill (display padding) (s)


def _energy_end(peaks: List[float], ws: float, we: float, floor: float,
                tail: float, pps: int = PPS) -> Optional[float]:
    """Last time in [ws, we] where energy is above `floor`, + tail."""
    si = max(0, int(ws * pps))
    ei = min(len(peaks), int(math.ceil(we * pps)))
    if si >= ei:
        return None
    window = peaks[si:ei]
    for j in range(len(window) - 1, -1, -1):
        if window[j] > floor:
            return (si + j) / pps + tail
    return None  # no energy above floor at all


def _noise_floor(peaks: List[float]) -> float:
    """Robust silence estimate: 25th percentile of the energy envelope."""
    if not peaks:
        return 0.01
    quartile = _percentile(peaks, 25)
    return max(quartile, 0.005)


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


def _next_event_bound(new_words: List[dict], i: int, line_end: float, gap: float) -> float:
    if i + 1 < len(new_words):
        return float(new_words[i + 1]["start"]) - gap
    return line_end


def _rescue_undersize(words: List[dict], line_start: float, line_end: float,
                      params: TrimParams) -> List[dict]:
    """Extend undersize words into adjacent freed gap space.

    Two strategies:
      1. End-extension: if gap exists AFTER the word, extend its end forward.
      2. Start-pull (if shift_starts): if gap exists BEFORE the word (opened by
         a trimmed predecessor), pull its start backward so the word displays
         earlier. This trades a small amount of audio-sync precision for
         visibility — a word at 0.04s is invisible regardless.
    Targets params.rescue_target duration, never overlaps a neighbor.
    """
    for i, w in enumerate(words):
        ws = float(w["start"])
        we = float(w["end"])
        dur = we - ws
        if dur >= UNDERSIZE_THRESH * 2:
            continue

        deficit = params.rescue_target - dur
        if deficit <= 0:
            continue

        # try end-extension first
        next_start = float(words[i + 1]["start"]) if i + 1 < len(words) else line_end
        end_room = next_start - we
        if end_room > 0.001:
            give = min(deficit, end_room)
            we += give
            deficit -= give
            words[i]["end"] = round(we, 3)

        # then start-pull if still undersize and allowed
        if deficit > 0 and params.shift_starts and i > 0:
            prev_end = float(words[i - 1]["end"])
            start_room = ws - prev_end
            if start_room > 0.001:
                give = min(deficit, start_room)
                ws -= give
                words[i]["start"] = round(ws, 3)

    return words


def audio_aware_trim_line(
    words: List[dict],
    line_start: float,
    line_end: float,
    onsets: List[float],
    peaks: Optional[List[float]],
    params: TrimParams,
) -> List[dict]:
    """Return words with overflow durations trimmed to audio evidence.

    Pass 1 (trim): for each word exceeding max_duration, pull end in to the
      minimum of: energy-derived end, next onset, next-word boundary, and the
      hard max_duration cap.

    Pass 2 (gap-fill): depending on mode, extend trimmed words forward into
      the dead air they opened up so we don't trade overflow for gaps.
        pure   — no fill (dead air stays; most audio-faithful)
        fill   — extend every word forward up to fill_cap to close gaps
        hybrid — only fill gaps larger than hybrid_threshold, partially
    """
    new_words = [dict(w) for w in words]
    floor = _noise_floor(peaks) * params.floor_mult if peaks else None

    # energy_ends[i] = audio-derived end for word i (None if not computed/not overflow)
    energy_ends: Dict[int, float] = {}

    # --- Pass 1: audio-aware trim ---
    for i, w in enumerate(new_words):
        ws = float(w["start"])
        we = float(w["end"])
        if we - ws <= params.max_duration:
            continue

        next_event = _next_event_bound(new_words, i, line_end, params.gap)
        candidates = [we, next_event, ws + params.max_duration]

        if peaks and floor is not None:
            e_end = _energy_end(peaks, ws, we, floor, params.tail)
            if e_end is not None:
                candidates.append(e_end)
                energy_ends[i] = e_end

        for ot in onsets:
            if ws + 0.08 < ot < we:
                candidates.append(ot - params.gap)
                break

        real_end = max(min(candidates), ws + MIN_WORD_DURATION)
        new_words[i]["end"] = round(real_end, 3)

    # --- Pass 1.5: rescue undersize words into freed space ---
    if params.rescue_undersize:
        new_words = _rescue_undersize(new_words, line_start, line_end, params)

    # --- Pass 2: audio-capped gap-fill ---
    # Extend words forward into dead air, but NEVER beyond energy_end + margin.
    # This prevents re-inflating a briefly-spoken word back to fill_cap.
    if params.mode != "pure":
        for i, w in enumerate(new_words):
            ws = float(w["start"])
            we = float(w["end"])
            next_event = _next_event_bound(new_words, i, line_end, 0.0)
            gap_to_next = next_event - we
            if gap_to_next <= GAP_THRESH:
                continue
            if params.mode == "hybrid" and gap_to_next <= params.hybrid_threshold:
                continue

            hard_cap = ws + params.fill_cap
            # audio cap: don't fill past where voice actually stops
            audio_cap = energy_ends.get(i)
            if audio_cap is not None:
                audio_cap = audio_cap + params.fill_margin
            else:
                audio_cap = hard_cap

            if params.mode == "hybrid":
                target = we + gap_to_next * 0.5
            else:
                target = min(hard_cap, audio_cap, we + (gap_to_next - GAP_THRESH) + 0.01)

            new_end = min(target, next_event)
            new_words[i]["end"] = round(max(new_end, we), 3)

    return new_words


def simulate_trim(songs: List[SongData], params: TrimParams) -> None:
    before_total = Counter()
    after_total = Counter()
    new_inversions = 0
    per_song_delta = []

    for sd in songs:
        before = compute_issues(sd.lines)
        trimmed_lines = []
        for line in sd.lines:
            words = line.get("words", [])
            ls = float(line.get("start", 0.0))
            le = float(line.get("end", 0.0))
            tw = audio_aware_trim_line(words, ls, le, sd.onsets, sd.peaks, params)
            nl = dict(line)
            nl["words"] = tw
            trimmed_lines.append(nl)
        after = compute_issues(trimmed_lines)
        before_total += before
        after_total += after
        delta = sum(after.values()) - sum(before.values())
        per_song_delta.append((sd.slug, before, after, delta))

        # count NEW overlaps only (end[i] > start[i+1] that wasn't in original)
        for li_idx, line in enumerate(sd.lines):
            ow = line.get("words", [])
            tw = trimmed_lines[li_idx].get("words", [])
            for k in range(min(len(ow), len(tw)) - 1):
                was_overlap = float(ow[k]["end"]) > float(ow[k + 1]["start"])
                now_overlap = float(tw[k]["end"]) > float(tw[k + 1]["start"])
                if now_overlap and not was_overlap:
                    new_inversions += 1

    print("\n" + "=" * 64)
    print("  PHASE 1 — AUDIO-AWARE TRIM SIMULATION")
    print("=" * 64)
    print(f"  params: mode={params.mode} floor_mult={params.floor_mult} tail={params.tail}s "
          f"gap={params.gap}s fill_cap={params.fill_cap}s max_dur={params.max_duration}s")

    types = ["duration_overflow", "duration_undersize", "gap_from_prev", "start_gte_end"]
    print(f"\n  {'type':<22s} {'before':>7s} {'after':>7s} {'delta':>7s}")
    print(f"  {'-'*22} {'-'*7} {'-'*7} {'-'*7}")
    for t in types:
        b = before_total.get(t, 0)
        a = after_total.get(t, 0)
        if b or a:
            d = a - b
            sign = "+" if d > 0 else ""
            print(f"  {t:<22s} {b:>7d} {a:>7d} {sign}{d:>6d}")
    btot = sum(before_total.values())
    atot = sum(after_total.values())
    print(f"  {'-'*22} {'-'*7} {'-'*7} {'-'*7}")
    d = atot - btot
    sign = "+" if d > 0 else ""
    print(f"  {'TOTAL':<22s} {btot:>7d} {atot:>7d} {sign}{d:>6d}")
    print(f"\n  new inversions/overlaps introduced: {new_inversions}")

    # biggest improvements
    improved = sorted(per_song_delta, key=lambda x: x[3])[:10]
    if improved:
        print(f"\n  Top 10 improved songs:")
        for slug, b, a, delta in improved:
            ovf_d = a.get("duration_overflow", 0) - b.get("duration_overflow", 0)
            und_d = a.get("duration_undersize", 0) - b.get("duration_undersize", 0)
            print(f"    {slug:<28s} {sum(b.values()):>3d} -> {sum(a.values()):>3d}  "
                  f"(ovf {ovf_d:+d}, und {und_d:+d})")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-d", "--project-dir", required=True, help="Collection root")
    ap.add_argument("--songs", default=None, help="Comma-separated song slugs")
    ap.add_argument("--baseline-only", action="store_true", help="Skip trim simulation")
    ap.add_argument("--floor-mult", type=float, default=3.0, help="Speech floor multiplier over noise floor")
    ap.add_argument("--tail", type=float, default=0.10, help="Decay tail after last energetic sample (s)")
    ap.add_argument("--no-redistribute", action="store_true", help="(deprecated)")
    ap.add_argument("--mode", choices=["pure", "fill", "hybrid"], default="fill",
                    help="pure=dead air stays, fill=extend words to close gaps, hybrid=partial fill on big gaps")
    ap.add_argument("--fill-cap", type=float, default=1.2, help="Max display duration after gap-fill (s)")
    ap.add_argument("--max-duration", type=float, default=1.5, help="Only trim words exceeding this (s)")
    ap.add_argument("--rescue-target", type=float, default=0.3, help="Target duration for rescued undersize words (s)")
    ap.add_argument("--fill-margin", type=float, default=0.3, help="How far past energy-end to fill (display padding) (s)")
    ap.add_argument("--no-shift-starts", action="store_true", help="Don't pull undersize starts earlier")
    ap.add_argument("--no-rescue", action="store_true", help="Disable undersize rescue pass")
    args = ap.parse_args()

    collection = Path(args.project_dir).resolve()
    stats = _load_json(collection / "output" / "dashboard" / "stats.json")

    song_dirs = discover_songs(collection)
    if args.songs:
        incl = set(args.songs.split(","))
        song_dirs = [d for d in song_dirs if d.name in incl]

    songs: List[SongData] = []
    missing_audio = []
    for d in song_dirs:
        sd = load_song(d)
        if sd:
            songs.append(sd)
            if not sd.peaks or not sd.onsets:
                missing_audio.append((sd.slug, bool(sd.peaks), bool(sd.onsets)))

    if missing_audio:
        print("  Songs missing some audio artifacts (trim will degrade gracefully):")
        for slug, has_peaks, has_onsets in missing_audio:
            print(f"    {slug}: peaks={has_peaks} onsets={has_onsets}")

    baseline_report(songs, stats)

    if args.baseline_only:
        return

    params = TrimParams(
        floor_mult=args.floor_mult,
        tail=args.tail,
        max_duration=args.max_duration,
        mode=args.mode,
        fill_cap=args.fill_cap,
        rescue_target=args.rescue_target,
        fill_margin=args.fill_margin,
        rescue_undersize=not args.no_rescue,
        shift_starts=not args.no_shift_starts,
    )
    simulate_trim(songs, params)


if __name__ == "__main__":
    main()
