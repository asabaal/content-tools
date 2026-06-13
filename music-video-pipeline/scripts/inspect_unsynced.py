#!/usr/bin/env python3
"""Inspect unsynced words across a song collection.

Reads lyrics.txt (ground truth), lyrics_synced.json (sync results),
alignment_analysis.json (match details), and vocal_transcription.json
(Whisper output) to report which lyrical words were not synced and why.

Usage:
    python scripts/inspect_unsynced.py -d projects/prophetic-preprint
    python scripts/inspect_unsynced.py -d projects/prophetic-preprint --songs blessed-the-name,freedom
    python scripts/inspect_unsynced.py -d projects/prophetic-preprint --json
    python scripts/inspect_unsynced.py -d projects/prophetic-preprint --summary-only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _norm(text: str) -> List[str]:
    t = text.lower().strip()
    t = re.sub(r"[^\w\s]", "", t)
    return t.split()


def _discover_projects(projects_dir: Path) -> List[dict]:
    projects = []
    for p in sorted(projects_dir.iterdir()):
        if not p.is_dir():
            continue
        proj_file = p / "data" / "mvp_project.json"
        if proj_file.exists():
            with open(proj_file) as f:
                pd = json.load(f)
            projects.append({"slug": p.name, "dir": p, "data": pd})
    return projects


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _get_whisper_text_in_window(
    segments: List[dict], start: float, end: float
) -> str:
    actual_start = min(start, end)
    actual_end = max(start, end)
    parts = []
    for s in segments:
        if s["start"] < actual_end + 1.0 and s["end"] > actual_start - 1.0:
            parts.append(s.get("text", ""))
    return " | ".join(parts) if parts else "(no Whisper coverage)"


def _classify_line(
    li: int,
    line_synced: dict,
    line_match: Optional[dict],
    trans_words_counter: Counter,
    lyric_words_counter: Counter,
    trans_word_set: set,
    whisper_segments: List[dict],
) -> dict:
    text = line_synced.get("text", "")
    words = line_synced.get("word_segment_assignments", [])
    start = line_synced.get("start", 0)
    end = line_synced.get("end", 0)
    alignment_conf = line_synced.get("alignment_confidence", 0)

    unsynced_words = []
    synced_words = []
    for w in words:
        if w.get("source") == "interpolated":
            unsynced_words.append(w)
        else:
            synced_words.append(w)

    if not unsynced_words:
        return None

    ratio = line_match.get("word_match_ratio", 0) if line_match else 0
    recovery = line_match.get("recovery_method") if line_match else None
    inverted = start > end

    lyric_words = _norm(text)
    absent = [w for w in lyric_words if w not in trans_word_set]
    has_segs = bool(
        whisper_segments
        and any(
            s["start"] < max(start, end) + 1.0 and s["end"] > min(start, end) - 1.0
            for s in whisper_segments
        )
    )

    if inverted:
        reason = "sync_bug_inverted_times"
        detail = f"start ({start:.1f}s) > end ({end:.1f}s)"
    elif not lyric_words:
        reason = "empty_line"
        detail = ""
    elif absent and not has_segs:
        reason = "whisper_gap_no_coverage"
        detail = f"no Whisper segments in region, absent words: {absent[:5]}"
    elif absent:
        reason = "whisper_misheard"
        detail = f"absent from all transcription: {absent[:5]}"
    elif not has_segs:
        reason = "whisper_gap_no_coverage"
        detail = "no Whisper segments in region"
    elif ratio == 0:
        deficits = []
        for w in set(lyric_words):
            lc = lyric_words_counter.get(w, 0)
            tc = trans_words_counter.get(w, 0)
            if lc > tc:
                deficits.append(f'"{w}" {lc}x/{tc}x')
        if deficits:
            reason = "whisper_compression"
            detail = f"word shortage: {', '.join(deficits[:4])}"
        else:
            reason = "alignment_mismatch"
            detail = "words exist in transcription but SequenceMatcher assigned none to this line"
    else:
        reason = "partial_sync"
        detail = f"ratio={ratio:.2f}, {len(unsynced_words)}/{len(words)} words unsynced"

    whisper_in_region = _get_whisper_text_in_window(
        whisper_segments or [], start, end
    )

    return {
        "line_idx": li,
        "text": text,
        "start": start,
        "end": end,
        "alignment_confidence": alignment_conf,
        "word_match_ratio": ratio,
        "recovery_method": recovery,
        "reason": reason,
        "detail": detail,
        "total_words": len(words),
        "synced_words": len(synced_words),
        "unsynced_words": len(unsynced_words),
        "unsynced_word_texts": [w.get("text", "") for w in unsynced_words],
        "whisper_in_region": whisper_in_region[:200],
    }


def inspect_song(
    song_dir: Path, verbose: bool = False
) -> Optional[dict]:
    data_dir = song_dir / "data"
    synced_data = _load_json(data_dir / "lyrics_synced.json")
    if not synced_data:
        return None

    align_data = _load_json(data_dir / "alignment_analysis.json")
    trans_data = _load_json(data_dir / "vocal_transcription.json")

    lyrics_file = data_dir / "lyrics.txt"
    lyrics_lines = []
    if lyrics_file.exists():
        with open(lyrics_file) as f:
            lyrics_lines = [l.rstrip() for l in f]

    lines_synced = synced_data.get("lines", [])
    line_matches = {}
    if align_data:
        for m in align_data.get("line_matches", []):
            idx = m.get("lyric_index", 0)
            line_matches[idx] = m

    whisper_segments = []
    trans_words_counter = Counter()
    trans_word_set = set()
    if trans_data:
        whisper_segments = trans_data.get("segments", [])
        for seg in whisper_segments:
            for w in _norm(seg.get("text", "")):
                trans_words_counter[w] += 1
                trans_word_set.add(w)

    lyric_words_counter = Counter()
    for line in lines_synced:
        for w in _norm(line.get("text", "")):
            lyric_words_counter[w] += 1

    unsynced_lines = []
    total_words = 0
    total_synced = 0
    total_unsynced = 0

    for li, line in enumerate(lines_synced):
        words = line.get("word_segment_assignments", [])
        n_unsynced = sum(1 for w in words if w.get("source") == "interpolated")
        n_synced = len(words) - n_unsynced
        total_words += len(words)
        total_synced += n_synced
        total_unsynced += n_unsynced

        if n_unsynced > 0:
            match = line_matches.get(li)
            result = _classify_line(
                li,
                line,
                match,
                trans_words_counter,
                lyric_words_counter,
                trans_word_set,
                whisper_segments,
            )
            if result:
                unsynced_lines.append(result)

    return {
        "slug": song_dir.name,
        "lyrics_lines": len(lyrics_lines),
        "synced_lines": len(lines_synced),
        "total_words": total_words,
        "synced_words": total_synced,
        "unsynced_words": total_unsynced,
        "lines_with_unsynced": len(unsynced_lines),
        "unsynced_lines": unsynced_lines,
    }


def print_song_report(report: dict, verbose: bool = False):
    slug = report["slug"]
    print(f"\n{'=' * 70}")
    print(
        f"  {slug}: {report['lines_with_unsynced']} lines with unsynced words "
        f"({report['unsynced_words']}/{report['total_words']} words unsynced)"
    )
    print(f"{'=' * 70}")

    for line in report["unsynced_lines"]:
        reason_labels = {
            "sync_bug_inverted_times": "SYNC BUG",
            "whisper_gap_no_coverage": "WHISPER GAP",
            "whisper_misheard": "MISHEARD",
            "whisper_compression": "COMPRESSION",
            "alignment_mismatch": "ALIGNMENT MISMATCH",
            "partial_sync": "PARTIAL SYNC",
            "empty_line": "EMPTY",
        }
        label = reason_labels.get(line["reason"], line["reason"].upper())

        conf = line["alignment_confidence"]
        ratio = line["word_match_ratio"]
        n_us = line["unsynced_words"]
        n_tot = line["total_words"]

        if n_us == n_tot:
            word_status = f"ALL UNSYNCED ({n_us}/{n_tot})"
        else:
            word_status = f"PARTIAL ({n_us}/{n_tot} unsynced)"

        print(f"\n  L{line['line_idx']:>3d}  [{label}]  conf={conf:.2f}  ratio={ratio:.2f}")
        print(f"       \"{line['text'][:65]}\"")
        print(f"       {word_status}")

        if line["unsynced_word_texts"]:
            texts = line["unsynced_word_texts"]
            if len(texts) <= 8:
                print(f"       unsynced: {texts}")
            else:
                print(f"       unsynced: {texts[:6]} ... ({len(texts)} total)")

        print(f"       → {line['detail']}")

        if verbose:
            print(f"       Whisper in region: \"{line['whisper_in_region'][:100]}\"")


def print_summary(reports: List[dict]):
    print(f"\n{'=' * 70}")
    print("  COLLECTION SUMMARY")
    print(f"{'=' * 70}")

    total_songs = len(reports)
    songs_with_unsynced = [r for r in reports if r["unsynced_words"] > 0]
    total_words = sum(r["total_words"] for r in reports)
    total_synced = sum(r["synced_words"] for r in reports)
    total_unsynced = sum(r["unsynced_words"] for r in reports)

    print(f"\n  Songs: {total_songs} total, {len(songs_with_unsynced)} with unsynced words")
    print(
        f"  Words: {total_words} total, {total_synced} synced ({total_synced/total_words*100:.1f}%), "
        f"{total_unsynced} unsynced ({total_unsynced/total_words*100:.1f}%)"
    )

    reason_counts = Counter()
    reason_lines = Counter()
    for r in reports:
        for line in r["unsynced_lines"]:
            reason_counts[line["reason"]] += line["unsynced_words"]
            reason_lines[line["reason"]] += 1

    print(f"\n  By reason:")
    reason_order = [
        "whisper_compression",
        "whisper_gap_no_coverage",
        "whisper_misheard",
        "sync_bug_inverted_times",
        "alignment_mismatch",
        "partial_sync",
    ]
    for reason in reason_order:
        wc = reason_counts.get(reason, 0)
        lc = reason_lines.get(reason, 0)
        if wc > 0:
            print(f"    {reason:<35s} {lc:>4d} lines, {wc:>5d} words")
    other_reasons = set(reason_counts.keys()) - set(reason_order)
    for reason in sorted(other_reasons):
        wc = reason_counts.get(reason, 0)
        lc = reason_lines.get(reason, 0)
        if wc > 0:
            print(f"    {reason:<35s} {lc:>4d} lines, {wc:>5d} words")

    print(f"\n  Top songs by unsynced words:")
    by_unsynced = sorted(songs_with_unsynced, key=lambda r: -r["unsynced_words"])
    for r in by_unsynced[:15]:
        pct = r["unsynced_words"] / r["total_words"] * 100 if r["total_words"] else 0
        reasons = Counter()
        for line in r["unsynced_lines"]:
            reasons[line["reason"]] += line["unsynced_words"]
        top_reason = reasons.most_common(1)[0][0] if reasons else ""
        print(
            f"    {r['slug']:<30s} {r['unsynced_words']:>4d} unsynced ({pct:>5.1f}%)  "
            f"[{top_reason}]"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Inspect unsynced words across a song collection"
    )
    parser.add_argument(
        "--project-dir",
        "-d",
        required=True,
        help="Path to collection root",
    )
    parser.add_argument(
        "--songs",
        default=None,
        help="Include only these song slugs (comma-separated)",
    )
    parser.add_argument(
        "--songs-from",
        default=None,
        help="Include only songs listed in file (one per line)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show Whisper region text for each line",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output machine-readable JSON",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only show the collection summary",
    )
    args = parser.parse_args()

    collection_dir = Path(args.project_dir).resolve()
    if not collection_dir.is_dir():
        print(f"Error: {collection_dir} is not a directory")
        sys.exit(1)

    projects_dir = collection_dir
    projects = _discover_projects(projects_dir)
    if not projects:
        sub = collection_dir / "projects"
        if sub.is_dir():
            projects = _discover_projects(sub)
            projects_dir = sub
    if not projects:
        print(f"No projects found under {collection_dir}")
        sys.exit(1)

    if args.songs:
        include = set(args.songs.split(","))
        projects = [p for p in projects if p["slug"] in include]
    elif args.songs_from:
        slugs = set()
        with open(args.songs_from) as f:
            for line in f:
                s = line.strip()
                if s and not s.startswith("#"):
                    slugs.add(s)
        projects = [p for p in projects if p["slug"] in slugs]

    print(f"\n  Collection: {collection_dir.name}")
    print(f"  Songs: {len(projects)}")

    reports = []
    for p in projects:
        report = inspect_song(p["dir"], verbose=args.verbose)
        if report:
            reports.append(report)

    if args.json_output:
        print(json.dumps(reports, indent=2))
        return

    if not args.summary_only:
        for report in reports:
            if report["lines_with_unsynced"] > 0:
                print_song_report(report, verbose=args.verbose)

    print_summary(reports)


if __name__ == "__main__":
    main()
