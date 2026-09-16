#!/usr/bin/env python3
"""Corpus-wide word-timing audit across Prophetic Preprint projects.

Classifies stored word/line timing into layer-specific failure signals and
cross-checks boundaries against independent audio evidence (vocal onsets,
combined-stem transcription words). Deterministic; no network; no rendering.

Usage (from music-video-pipeline/):
  python3 scripts/timing_corpus_audit.py --projects-dir ../projects/prophetic-preprint/projects

Outputs:
  <project>/output/timing-audit/timing-audit.json   machine-readable
  <project>/output/timing-audit/timing-audit.md     human-readable rollup
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

import numpy as np


def norm_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def load_onsets(path: Path) -> list[float]:
    if not path.exists():
        return []
    return [float(x) for x in json.loads(path.read_text()).get("onset_times", [])]


def load_stem_words(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for seg in json.loads(path.read_text()).get("segments", []):
        for w in seg.get("words", []):
            if w.get("start") is not None:
                out.append({"start": w["start"], "end": w.get("end", w["start"])})
    return out


def nearest_distance(t: float, arr: np.ndarray) -> float:
    if arr.size == 0:
        return float("inf")
    i = np.searchsorted(arr, t)
    cands = arr[max(0, i - 1): i + 1]
    return float(np.min(np.abs(cands - t)))


def audit_song(project: Path, context: float = 0.15) -> dict:
    data = project / "data"
    synced = json.loads((data / "lyrics_synced.json").read_text())
    lines = synced.get("lines", [])
    onsets = np.asarray(sorted(load_onsets(data / "vocal_onsets.json")), dtype=float)
    stem_words = sorted(load_stem_words(data / "vocal_transcription_combined_vocals.json"),
                        key=lambda w: w["start"])
    stem_starts = np.asarray([w["start"] for w in stem_words], dtype=float)

    overrides = {}
    sc = data / "script.json"
    if sc.exists():
        overrides = json.loads(sc.read_text()).get("timing_overrides", {})
    for key, entry in overrides.items():
        if key == "_provenance" or not isinstance(entry, dict):
            continue
        try:
            idx = int(key)
        except (TypeError, ValueError):
            continue
        if 0 <= idx < len(lines):
            line = lines[idx]
            if "start" in entry: line["start"] = entry["start"]
            if "end" in entry: line["end"] = entry["end"]
            if isinstance(entry.get("words"), list):
                line["words"] = [
                    {"text": w.get("text", w.get("word", "")),
                     "start": w["start"], "end": w["end"], "source": "override"}
                    for w in entry["words"]
                    if isinstance(w, dict) and "start" in w and "end" in w]

    words_flat = []
    for li, line in enumerate(lines):
        for wi, w in enumerate(line.get("words", [])):
            if w.get("start") is None or w.get("end") is None:
                continue
            words_flat.append({"li": li, "wi": wi, "text": w.get("text", ""),
                               "start": w["start"], "end": w["end"],
                               "source": w.get("source", "")})

    sig = {
        "n_words": len(words_flat),
        "zero_or_negative": [],
        "undersize_lt_40ms": [],
        "oversize_gt_1500ms": [],
        "intra_line_gap_gt_500ms": [],
        "onset_distance": [],
        "onset_distance_by_source": {},
        "stem_distance": [],
        "line_lead_gt_1500ms": [],
        "line_tail_gt_1500ms": [],
        "line_util_lt_50pct": [],
        "line_start_equals_prev_end": 0,
        "line_span_contiguous": 0,
    }

    prev_line_end = None
    for li, line in enumerate(lines):
        ws = [w for w in line.get("words", []) if w.get("start") is not None]
        l_start, l_end = line.get("start"), line.get("end")
        if prev_line_end is not None and l_start is not None:
            if abs(l_start - prev_line_end) < 0.001:
                sig["line_start_equals_prev_end"] += 1
                sig["line_span_contiguous"] += 1
        prev_line_end = l_end
        if not ws:
            continue
        w_first, w_last = ws[0]["start"], ws[-1]["end"]
        span = max(0.001, (l_end or w_last) - (l_start or w_first))
        utilization = (w_last - w_first) / span
        lead = w_first - (l_start if l_start is not None else w_first)
        tail = (l_end if l_end is not None else w_last) - w_last
        if lead > 1.5:
            sig["line_lead_gt_1500ms"].append(
                {"line": li, "lead": round(lead, 3), "text": line.get("text", "")[:50]})
        if tail > 1.5:
            sig["line_tail_gt_1500ms"].append(
                {"line": li, "tail": round(tail, 3), "text": line.get("text", "")[:50]})
        if utilization < 0.5 and span > 1.0:
            sig["line_util_lt_50pct"].append(
                {"line": li, "utilization": round(utilization, 3),
                 "text": line.get("text", "")[:50]})

    prev_end, prev_li = None, None
    onset_by_source = {}
    onset_all, stem_all = [], []
    for w in words_flat:
        dur = w["end"] - w["start"]
        entry = {"line": w["li"], "word": w["wi"], "text": w["text"][:24],
                 "start": round(w["start"], 3), "end": round(w["end"], 3),
                 "duration": round(dur, 3), "source": w["source"]}
        if dur <= 0:
            sig["zero_or_negative"].append(entry)
        elif dur < 0.04:
            sig["undersize_lt_40ms"].append(entry)
        elif dur > 1.5:
            sig["oversize_gt_1500ms"].append(entry)

        if prev_end is not None and w["li"] == prev_li:
            gap = round(w["start"] - prev_end, 3)
            if gap > 0.5:
                sig["intra_line_gap_gt_500ms"].append({**entry, "gap": gap})
        onset_dist = nearest_distance(w["start"], onsets)
        onset_all.append(onset_dist)
        onset_by_source.setdefault(w["source"], []).append(onset_dist)
        stem_all.append(nearest_distance(w["start"], stem_starts))
        prev_end, prev_li = w["end"], w["li"]

    def pct_summary(values):
        if not values:
            return None
        a = np.asarray(values)
        return {"n": len(a),
                "mean_ms": round(float(a.mean()) * 1000, 1),
                "p50_ms": round(float(np.percentile(a, 50)) * 1000, 1),
                "p90_ms": round(float(np.percentile(a, 90)) * 1000, 1),
                "p99_ms": round(float(np.percentile(a, 99)) * 1000, 1),
                "max_ms": round(float(a.max()) * 1000, 1),
                "gt_150ms": int((a > 0.15).sum()),
                "gt_300ms": int((a > 0.3).sum())}

    sig["onset_distance_summary"] = pct_summary(onset_all)
    sig["stem_distance_summary"] = pct_summary(stem_all)
    sig["onset_distance_by_source"] = {k: pct_summary(v) for k, v in onset_by_source.items()}
    return {"project": project.name, "lines": len(lines), "signals": sig}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--projects-dir", default="../projects/prophetic-preprint/projects")
    ap.add_argument("--out", default="output/timing-audit")
    ap.add_argument("--songs", help="comma-separated project names (default: all)")
    args = ap.parse_args()

    projects_dir = Path(args.projects_dir)
    songs = set(args.songs.split(",")) if args.songs else None

    results = {}
    for proj in sorted(projects_dir.iterdir()):
        if not proj.is_dir() or proj.name == "output":
            continue
        if not (proj / "data" / "lyrics_synced.json").exists():
            continue
        if songs and proj.name not in songs:
            continue
        results[proj.name] = audit_song(proj)

    signal_keys = ["zero_or_negative", "undersize_lt_40ms", "oversize_gt_1500ms",
                   "intra_line_gap_gt_500ms", "line_lead_gt_1500ms",
                   "line_tail_gt_1500ms", "line_util_lt_50pct"]
    rollup = {"n_songs": len(results), "signal_totals": {}}
    for key in signal_keys:
        total = sum(len(r["signals"].get(key, [])) for r in results.values())
        per_song = {name: len(r["signals"][key]) for name, r in results.items()
                    if r["signals"].get(key)}
        rollup["signal_totals"][key] = {"total": total, "songs_affected": per_song}

    md = ["# Corpus Timing Audit", "", f"Songs: {len(results)}", "", "## Signal totals", "",
          "| signal | total | songs affected |", "|---|---|---|"]
    for key in signal_keys:
        st = rollup["signal_totals"][key]
        md.append(f"| {key} | {st['total']} | {len(st['songs_affected'])} |")

    md += ["", "## Onset distance by song and source class", ""]
    for name, r in results.items():
        s = r["signals"].get("onset_distance_summary")
        if not s: continue
        md.append(f"**{name}** (n={s['n']}): p50={s['p50_ms']}ms p90={s['p90_ms']}ms "
                  f"max={s['max_ms']}ms >150ms={s['gt_150ms']} >300ms={s['gt_300ms']}")
        for src_cls, v in r["signals"].get("onset_distance_by_source", {}).items():
            if v:
                md.append(f"  · {src_cls}: n={v['n']} p50={v['p50_ms']}ms p90={v['p90_ms']}ms "
                          f">150ms={v['gt_150ms']} >300ms={v['gt_300ms']}")

    md += ["", "## Line span issues (lead/tail/utilization)", ""]
    for name, r in results.items():
        s = r["signals"]
        issues = (len(s["line_lead_gt_1500ms"]) + len(s["line_tail_gt_1500ms"])
                  + len(s["line_util_lt_50pct"]))
        if issues:
            md.append(f"**{name}**: {issues} line-span issue(s)")
            for e in s["line_lead_gt_1500ms"][:3]:
                md.append(f"  · L{e['line']} lead {e['lead']}s: {e['text']}")
            for e in s["line_util_lt_50pct"][:3]:
                md.append(f"  · L{e['line']} util {e['utilization']}: {e['text']}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "timing-audit.json").write_text(
        json.dumps({"results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "timing-audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {out_dir / 'timing-audit.md'} ({len(results)} songs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
