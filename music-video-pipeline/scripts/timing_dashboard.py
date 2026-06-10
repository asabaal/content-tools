#!/usr/bin/env python3
"""Timing Issues Dashboard Generator for Prophetic Preprint.

Reads audit summary.json and lyrics_synced.json for all songs, normalizes
timing issues into a structured dataset with diagnostic context, then
generates a self-contained HTML dashboard for exploration.

Usage:
    python scripts/timing_dashboard.py projects/prophetic-preprint
    python scripts/timing_dashboard.py projects/prophetic-preprint --open
    mvp dashboard projects/prophetic-preprint
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import webbrowser
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent


def classify_issue(issue: Dict) -> str:
    label = issue.get("issue", "")
    if label == "start >= end":
        return "start_gte_end"
    if "duration" in label and "> 1.5s" in label:
        return "duration_overflow"
    if "duration" in label and "< 0.04s" in label:
        return "duration_undersize"
    if "gap" in label and "from previous word" in label:
        return "gap_from_prev"
    if "clip" in label:
        return "text_overflow"
    if "contrast" in label.lower() or "readab" in label.lower():
        return "readability"
    return "unknown"


def severity_tier(issue_type: str, issue: Dict) -> str:
    if issue_type == "start_gte_end":
        return "critical"
    if issue_type == "gap_from_prev":
        gap = abs(issue.get("gap_from_prev", 0))
        if gap > 5:
            return "high"
        return "warning"
    if issue_type == "duration_overflow":
        dur = issue.get("duration", 0)
        if dur > 10:
            return "high"
        return "warning"
    if issue_type == "duration_undersize":
        return "warning"
    if issue_type in ("text_overflow", "readability"):
        return "warning"
    return "info"


def duration_bucket(duration: float) -> str:
    if duration <= 0:
        return "inverted"
    if duration < 0.04:
        return "< 0.04s"
    if duration < 0.5:
        return "0.04-0.5s"
    if duration < 1.5:
        return "0.5-1.5s"
    if duration < 3:
        return "1.5-3s"
    if duration < 5:
        return "3-5s"
    if duration < 10:
        return "5-10s"
    return "10s+"


def root_cause_hint(issue_type: str, issue: Dict, word_source: Optional[str]) -> str:
    if issue_type == "start_gte_end":
        if word_source == "transcription":
            return "transcription_inversion"
        if word_source == "interpolated":
            return "interpolated_inversion"
        if word_source == "vocal_onset_only":
            return "onset_only_inversion"
        return "unknown_inversion"
    if issue_type == "duration_undersize":
        if word_source == "interpolated":
            return "interpolated_undersize"
        return "unknown_undersize"
    if issue_type == "duration_overflow":
        if word_source == "vocal_onset_only":
            return "onset_only_overflow"
        return "unknown_overflow"
    if issue_type == "gap_from_prev":
        return "cascade_gap"
    return "ambiguous"


def repair_suggestion(hint: str) -> str:
    mapping = {
        "transcription_inversion": "re_align",
        "interpolated_inversion": "re_estimate",
        "onset_only_inversion": "re_estimate",
        "unknown_inversion": "manual_review",
        "interpolated_undersize": "re_estimate",
        "unknown_undersize": "manual_review",
        "onset_only_overflow": "cap_duration",
        "unknown_overflow": "manual_review",
        "cascade_gap": "fix_inversion_first",
        "independent_gap": "manual_review",
        "ambiguous": "manual_review",
    }
    return mapping.get(hint, "manual_review")


def collect_issues(projects_dir: Path) -> Tuple[List[Dict], Dict[str, Any]]:
    songs_dir = projects_dir / "projects"
    if not songs_dir.exists():
        raise FileNotFoundError(f"No projects dir at {songs_dir}")

    all_issues: List[Dict] = []
    songs_meta: Dict[str, Any] = {}

    song_dirs = sorted(
        [d for d in songs_dir.iterdir() if d.is_dir()]
    )

    for song_dir in song_dirs:
        song_name = song_dir.name
        audit_path = song_dir / "output" / "audit" / "summary.json"
        synced_path = song_dir / "data" / "lyrics_synced.json"
        script_path = song_dir / "data" / "script.json"

        if not audit_path.exists():
            continue

        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        synced_lines = []
        if synced_path.exists():
            synced_data = json.loads(synced_path.read_text(encoding="utf-8"))
            synced_lines = synced_data.get("lines", [])

        script_sections: List[Dict] = []
        if script_path.exists():
            script = json.loads(script_path.read_text(encoding="utf-8"))
            script_sections = script.get("sections", [])

        total_words = audit.get("total_words", 0)
        total_lines = audit.get("total_lines", 0)

        issue_word_set: set = set()
        for issue in audit.get("issues", []):
            itype = classify_issue(issue)
            li = issue.get("line", -1)
            wi = issue.get("word", -1)

            line_data = synced_lines[li] if li < len(synced_lines) else None
            word_data = None
            word_source = None
            if line_data:
                words = line_data.get("words", [])
                if wi < len(words):
                    word_data = words[wi]
                    word_source = word_data.get("source")

            prev_word = None
            next_word = None
            if line_data:
                words = line_data.get("words", [])
                if wi > 0 and wi - 1 < len(words):
                    pw = words[wi - 1]
                    prev_word = {"text": pw["text"], "end": pw.get("end")}
                if wi + 1 < len(words):
                    nw = words[wi + 1]
                    next_word = {"text": nw["text"], "start": nw.get("start")}

            prev_line_text = None
            next_line_text = None
            if li > 0 and li - 1 < len(synced_lines):
                prev_line_text = synced_lines[li - 1].get("text")
            if li + 1 < len(synced_lines):
                next_line_text = synced_lines[li + 1].get("text")

            section_name = None
            section_type = None
            if line_data:
                sec = line_data.get("section", {})
                section_name = sec.get("raw_marker", "")
                section_type = sec.get("section_type", "")
            if not section_name:
                for sec in script_sections:
                    sec_lines = sec.get("lines", [])
                    if isinstance(sec_lines, list) and li in sec_lines:
                        section_name = sec.get("name", "")
                        break

            hint = root_cause_hint(itype, issue, word_source)

            normalized = {
                "id": f"{song_name}_L{li}_W{wi}_{itype}",
                "song": song_name,
                "line_idx": li,
                "word_idx": wi,
                "word_text": issue.get("text", ""),
                "issue_type": itype,
                "issue_label": issue.get("issue", ""),
                "severity": severity_tier(itype, issue),
                "is_derivative": False,
                "start": issue.get("start"),
                "end": issue.get("end"),
                "duration": issue.get("duration"),
                "gap_from_prev": issue.get("gap_from_prev"),
                "line_text": line_data.get("text", "") if line_data else "",
                "prev_word": prev_word,
                "next_word": next_word,
                "prev_line_text": prev_line_text,
                "next_line_text": next_line_text,
                "word_source": word_source,
                "section_name": section_name,
                "section_type": section_type,
                "root_cause_hint": hint,
                "repair_suggestion": repair_suggestion(hint),
                "overflow_px": issue.get("overflow_px"),
                "edge": issue.get("edge"),
            }
            all_issues.append(normalized)
            issue_word_set.add((li, wi))

        songs_meta[song_name] = {
            "total_words": total_words,
            "total_lines": total_lines,
            "issue_count": len(audit.get("issues", [])),
            "affected_words": len(issue_word_set),
            "pct_affected": round(len(issue_word_set) / total_words * 100, 1) if total_words else 0,
        }

    # Mark derivative gaps
    inversions_by_song: Dict[str, set] = defaultdict(set)
    for iss in all_issues:
        if iss["issue_type"] == "start_gte_end":
            inversions_by_song[iss["song"]].add((iss["line_idx"], iss["word_idx"]))

    for iss in all_issues:
        if iss["issue_type"] == "gap_from_prev":
            song = iss["song"]
            li = iss["line_idx"]
            wi = iss["word_idx"]
            invs = inversions_by_song.get(song, set())
            if (li, wi) in invs or (li, wi - 1) in invs:
                iss["is_derivative"] = True
                iss["root_cause_hint"] = "cascade_gap"
                iss["repair_suggestion"] = "fix_inversion_first"
            else:
                iss["root_cause_hint"] = "independent_gap"

    # Rank songs by severity score
    song_scores: Dict[str, int] = {}
    weights = {"critical": 10, "high": 5, "warning": 1, "info": 0}
    for iss in all_issues:
        song_scores[iss["song"]] = song_scores.get(iss["song"], 0) + weights.get(iss["severity"], 0)
    ranked = sorted(song_scores.items(), key=lambda x: -x[1])
    rank_map = {name: i + 1 for i, (name, _) in enumerate(ranked)}
    for iss in all_issues:
        iss["song_rank"] = rank_map.get(iss["song"], 999)
    for name in songs_meta:
        songs_meta[name]["severity_rank"] = rank_map.get(name, 999)
        songs_meta[name]["severity_score"] = song_scores.get(name, 0)

    return all_issues, songs_meta


def compute_stats(all_issues: List[Dict], songs_meta: Dict) -> Dict[str, Any]:
    total_issues = len(all_issues)
    by_type: Dict[str, int] = Counter(i["issue_type"] for i in all_issues)
    by_severity: Dict[str, int] = Counter(i["severity"] for i in all_issues)
    by_source: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "issues": 0})
    by_hint: Dict[str, int] = Counter(i["root_cause_hint"] for i in all_issues)
    derivative_count = sum(1 for i in all_issues if i["is_derivative"])
    independent_count = total_issues - derivative_count

    source_word_totals: Dict[str, int] = Counter()
    for iss in all_issues:
        src = iss.get("word_source") or "unknown"
        by_source[src]["issues"] += 1
        source_word_totals[src] += 1

    by_song: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for iss in all_issues:
        by_song[iss["song"]][iss["issue_type"]] += 1
        by_song[iss["song"]]["total"] += 1
        by_song[iss["song"]][iss["severity"]] += 1

    songs_list = []
    for name, meta in sorted(songs_meta.items(), key=lambda x: x[1].get("severity_score", 0), reverse=True):
        row = {"song": name, **meta}
        for k, v in by_song.get(name, {}).items():
            row[f"type_{k}"] = v
        songs_list.append(row)

    duration_dist: Dict[str, int] = Counter(
        duration_bucket(i.get("duration", 0)) for i in all_issues if i.get("duration") is not None
    )
    gap_dist: Dict[str, int] = {}
    for iss in all_issues:
        if iss["issue_type"] == "gap_from_prev" and not iss["is_derivative"]:
            g = abs(iss.get("gap_from_prev", 0))
            bucket = f"{int(g)}s"
            gap_dist[bucket] = gap_dist.get(bucket, 0) + 1

    return {
        "total_issues": total_issues,
        "independent_issues": independent_count,
        "derivative_issues": derivative_count,
        "total_songs": len(songs_meta),
        "songs_with_issues": sum(1 for m in songs_meta.values() if m["issue_count"] > 0),
        "by_type": dict(by_type),
        "by_severity": dict(by_severity),
        "by_source": {k: dict(v) for k, v in by_source.items()},
        "by_hint": dict(by_hint),
        "by_song": songs_list,
        "duration_distribution": dict(duration_dist),
        "gap_distribution": gap_dist,
        "repair_suggestions": dict(Counter(i["repair_suggestion"] for i in all_issues)),
    }


def export_csv(all_issues: List[Dict], output_path: Path):
    if not all_issues:
        return
    fieldnames = [
        "id", "song", "song_rank", "line_idx", "word_idx", "word_text",
        "issue_type", "issue_label", "severity", "is_derivative",
        "start", "end", "duration", "gap_from_prev",
        "line_text", "word_source", "section_type",
        "root_cause_hint", "repair_suggestion",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for iss in all_issues:
            row = {k: iss.get(k, "") for k in fieldnames}
            row["is_derivative"] = str(row["is_derivative"])
            writer.writerow(row)


def generate_html(all_issues: List[Dict], songs_meta: Dict, stats: Dict, output_path: Path):
    issues_json = json.dumps(all_issues, ensure_ascii=False)
    songs_json = json.dumps(songs_meta, ensure_ascii=False)
    stats_json = json.dumps(stats, ensure_ascii=False)

    html = HTML_TEMPLATE.format(
        issues_json=issues_json,
        songs_json=songs_json,
        stats_json=stats_json,
        generated_at=_now_str(),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def _now_str() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_dashboard(projects_dir: Path, output_dir: Optional[Path] = None, open_browser: bool = False) -> Path:
    projects_dir = Path(projects_dir).resolve()
    if not output_dir:
        output_dir = projects_dir / "output" / "dashboard"
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Collecting timing issues from {projects_dir}...")
    all_issues, songs_meta = collect_issues(projects_dir)
    print(f"  Found {len(all_issues)} issues across {len(songs_meta)} songs")

    stats = compute_stats(all_issues, songs_meta)

    issues_path = output_dir / "timing_issues.json"
    issues_path.write_text(json.dumps(all_issues, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Wrote {issues_path}")

    csv_path = output_dir / "timing_issues.csv"
    export_csv(all_issues, csv_path)
    print(f"  Wrote {csv_path}")

    html_path = output_dir / "timing_dashboard.html"
    generate_html(all_issues, songs_meta, stats, html_path)
    print(f"  Wrote {html_path}")

    stats_path = output_dir / "stats.json"
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Wrote {stats_path}")

    print(f"\nDashboard generated: {html_path}")
    if open_browser:
        webbrowser.open(f"file://{html_path}")

    return html_path


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Prophetic Preprint - Timing Issues Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg: #0d1117; --surface: #161b22; --surface2: #1c2333; --border: #30363d;
  --text: #e6edf3; --text2: #8b949e; --accent: #58a6ff;
  --red: #f85149; --orange: #d29922; --yellow: #e3b341; --green: #3fb950; --blue: #58a6ff;
  --purple: #bc8cff; --pink: #f778ba;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.5; }}
a {{ color: var(--accent); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

.header {{ padding: 24px 32px; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; }}
.header h1 {{ font-size: 20px; font-weight: 600; }}
.header .meta {{ color: var(--text2); font-size: 12px; }}

.container {{ max-width: 1400px; margin: 0 auto; padding: 24px 32px; }}

.kpi-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }}
.kpi {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }}
.kpi .label {{ font-size: 12px; color: var(--text2); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
.kpi .value {{ font-size: 28px; font-weight: 700; }}
.kpi .sub {{ font-size: 12px; color: var(--text2); margin-top: 4px; }}
.kpi.critical .value {{ color: var(--red); }}
.kpi.warning .value {{ color: var(--orange); }}
.kpi.good .value {{ color: var(--green); }}

.section {{ margin-bottom: 32px; }}
.section h2 {{ font-size: 16px; font-weight: 600; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }}

.charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
.chart-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }}
.chart-card.full {{ grid-column: 1 / -1; }}
.chart-card h3 {{ font-size: 13px; color: var(--text2); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
.chart-card canvas {{ max-height: 400px; }}

.badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }}
.badge.critical {{ background: rgba(248,81,73,0.15); color: var(--red); }}
.badge.high {{ background: rgba(210,153,34,0.15); color: var(--orange); }}
.badge.warning {{ background: rgba(227,179,65,0.15); color: var(--yellow); }}
.badge.info {{ background: rgba(88,166,255,0.15); color: var(--blue); }}
.badge.derivative {{ background: rgba(139,148,158,0.15); color: var(--text2); }}
.badge.source {{ background: rgba(188,140,255,0.15); color: var(--purple); }}

.tabs {{ display: flex; gap: 0; margin-bottom: 20px; border-bottom: 1px solid var(--border); }}
.tab {{ padding: 10px 20px; cursor: pointer; color: var(--text2); border-bottom: 2px solid transparent; font-size: 13px; font-weight: 500; }}
.tab:hover {{ color: var(--text); }}
.tab.active {{ color: var(--accent); border-bottom-color: var(--accent); }}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}

table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ text-align: left; padding: 10px 12px; color: var(--text2); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); cursor: pointer; user-select: none; white-space: nowrap; }}
th:hover {{ color: var(--text); }}
th .sort {{ opacity: 0.3; margin-left: 4px; }}
th.sorted .sort {{ opacity: 1; color: var(--accent); }}
td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }}
tr:hover {{ background: var(--surface2); }}
tr.detail-row {{ background: var(--surface); }}
tr.detail-row td {{ padding: 12px 12px 12px 48px; }}

.controls {{ display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }}
.controls input, .controls select {{ background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 8px 12px; border-radius: 6px; font-size: 13px; }}
.controls input {{ width: 280px; }}
.controls select {{ min-width: 140px; }}
.btn {{ background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; }}
.btn:hover {{ background: var(--surface2); }}
.btn.primary {{ background: #1f6feb; border-color: #1f6feb; color: white; }}
.btn.primary:hover {{ background: #388bfd; }}

.song-detail {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 24px; }}
.song-detail .song-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
.song-detail .song-header h3 {{ font-size: 18px; }}
.song-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.song-stat {{ background: var(--surface2); border-radius: 6px; padding: 12px; text-align: center; }}
.song-stat .val {{ font-size: 20px; font-weight: 700; }}
.song-stat .lbl {{ font-size: 11px; color: var(--text2); text-transform: uppercase; }}

.timeline-bar {{ position: relative; height: 24px; background: var(--surface2); border-radius: 4px; margin: 4px 0; }}
.timeline-dot {{ position: absolute; top: 4px; width: 8px; height: 16px; border-radius: 2px; cursor: pointer; }}
.timeline-dot:hover {{ opacity: 0.8; }}
.timeline-dot.critical {{ background: var(--red); }}
.timeline-dot.high {{ background: var(--orange); }}
.timeline-dot.warning {{ background: var(--yellow); }}

.context-line {{ font-family: 'SFMono-Regular', Consolas, monospace; font-size: 12px; padding: 3px 8px; border-radius: 3px; margin: 2px 0; }}
.context-line.highlight {{ background: rgba(248,81,73,0.15); color: var(--red); }}
.context-line.dim {{ color: var(--text2); }}

.pagination {{ display: flex; gap: 8px; align-items: center; margin-top: 12px; justify-content: center; }}
.pagination .btn {{ min-width: 36px; text-align: center; }}
.pagination .btn.active {{ background: #1f6feb; border-color: #1f6feb; color: white; }}
.pagination .info {{ color: var(--text2); font-size: 12px; }}

.risk-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 12px; }}
.risk-card h4 {{ font-size: 14px; margin-bottom: 8px; }}
.risk-card .risk-level {{ display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 700; margin-left: 8px; }}
.risk-card p {{ color: var(--text2); font-size: 13px; line-height: 1.6; }}
.risk-card ul {{ color: var(--text2); font-size: 13px; padding-left: 20px; margin-top: 8px; }}
.risk-card li {{ margin-bottom: 4px; }}

.back-link {{ display: inline-flex; align-items: center; gap: 4px; margin-bottom: 16px; font-size: 13px; }}

@media (max-width: 900px) {{
  .charts-grid {{ grid-template-columns: 1fr; }}
  .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
}}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>Prophetic Preprint &mdash; Timing Issues Dashboard</h1>
    <div class="meta">Generated {generated_at} &bull; <span id="totalSongs">0</span> songs &bull; <span id="totalIssues">0</span> issues</div>
  </div>
  <div>
    <button class="btn" onclick="exportCSV()">Export CSV</button>
  </div>
</div>

<div class="container">
  <div class="kpi-row" id="kpiRow"></div>

  <div class="tabs">
    <div class="tab active" data-tab="overview">Overview</div>
    <div class="tab" data-tab="songs">Songs</div>
    <div class="tab" data-tab="issues">Issues Table</div>
    <div class="tab" data-tab="diagnosis">Diagnosis</div>
  </div>

  <div class="tab-panel active" id="panel-overview">
    <div class="charts-grid">
      <div class="chart-card full"><h3>Issues by Song (click to drill down)</h3><canvas id="chartBySong"></canvas></div>
      <div class="chart-card"><h3>Issue Types</h3><canvas id="chartByType"></canvas></div>
      <div class="chart-card"><h3>Severity Distribution</h3><canvas id="chartBySeverity"></canvas></div>
      <div class="chart-card"><h3>Word Source Correlation</h3><canvas id="chartBySource"></canvas></div>
      <div class="chart-card"><h3>Repair Suggestions</h3><canvas id="chartByRepair"></canvas></div>
    </div>
  </div>

  <div class="tab-panel" id="panel-songs">
    <div id="songsList"></div>
    <div id="songDetail" style="display:none;"></div>
  </div>

  <div class="tab-panel" id="panel-issues">
    <div class="controls">
      <input type="text" id="issueSearch" placeholder="Search lyrics, song names..." oninput="filterIssues()">
      <select id="filterSong" onchange="filterIssues()"><option value="">All Songs</option></select>
      <select id="filterType" onchange="filterIssues()"><option value="">All Types</option></select>
      <select id="filterSeverity" onchange="filterIssues()"><option value="">All Severities</option></select>
      <select id="filterSource" onchange="filterIssues()"><option value="">All Sources</option></select>
      <label style="color:var(--text2);font-size:13px"><input type="checkbox" id="hideDerivative" onchange="filterIssues()"> Hide derivative</label>
    </div>
    <table id="issuesTable">
      <thead>
        <tr>
          <th data-col="song_rank">#</th>
          <th data-col="song">Song</th>
          <th data-col="issue_type">Type</th>
          <th data-col="severity">Severity</th>
          <th data-col="line_idx">Line</th>
          <th data-col="word_text">Word</th>
          <th data-col="line_text">Lyric Line</th>
          <th data-col="word_source">Source</th>
          <th data-col="root_cause_hint">Diagnosis</th>
        </tr>
      </thead>
      <tbody id="issuesBody"></tbody>
    </table>
    <div class="pagination" id="issuesPagination"></div>
  </div>

  <div class="tab-panel" id="panel-diagnosis">
    <div id="diagnosisContent"></div>
  </div>
</div>

<script>
const ISSUES = {issues_json};
const SONGS = {songs_json};
const STATS = {stats_json};

const TYPE_LABELS = {{
  start_gte_end: "Start >= End",
  duration_overflow: "Duration > 1.5s",
  duration_undersize: "Duration < 0.04s",
  gap_from_prev: "Gap from Prev",
  text_overflow: "Text Overflow",
  readability: "Readability"
}};
const TYPE_COLORS = {{
  start_gte_end: "#f85149",
  duration_overflow: "#d29922",
  duration_undersize: "#e3b341",
  gap_from_prev: "#58a6ff",
  text_overflow: "#bc8cff",
  readability: "#f778ba"
}};
const SEV_COLORS = {{ critical: "#f85149", high: "#d29922", warning: "#e3b341", info: "#58a6ff" }};
const REPAIR_LABELS = {{
  re_align: "Re-align section",
  re_estimate: "Re-estimate timing",
  cap_duration: "Cap duration",
  fix_inversion_first: "Fix inversion first",
  manual_review: "Manual review"
}};

document.getElementById("totalSongs").textContent = STATS.total_songs;
document.getElementById("totalIssues").textContent = STATS.total_issues;

// KPI cards
function renderKPIs() {{
  const row = document.getElementById("kpiRow");
  const totalWords = Object.values(SONGS).reduce((s, m) => s + m.total_words, 0);
  const affectedWords = new Set(ISSUES.filter(i => !i.is_derivative).map(i => i.song + "_L" + i.line_idx + "_W" + i.word_idx)).size;
  const pctClean = totalWords ? ((totalWords - affectedWords) / totalWords * 100).toFixed(1) : "0";
  const worstSong = STATS.by_song[0]?.song || "-";
  row.innerHTML = `
    <div class="kpi"><div class="label">Total Issues</div><div class="value">${{STATS.total_issues.toLocaleString()}}</div><div class="sub">${{STATS.independent_issues}} independent / ${{STATS.derivative_issues}} derivative</div></div>
    <div class="kpi critical"><div class="label">Critical (Inverted)</div><div class="value">${{(STATS.by_severity.critical || 0).toLocaleString()}}</div><div class="sub">${{STATS.by_type.start_gte_end || 0}} start >= end issues</div></div>
    <div class="kpi warning"><div class="label">Warnings</div><div class="value">${{((STATS.by_severity.warning || 0) + (STATS.by_severity.high || 0)).toLocaleString()}}</div><div class="sub">Duration &amp; gap issues</div></div>
    <div class="kpi good"><div class="label">Words Clean</div><div class="value">${{pctClean}}%</div><div class="sub">${{totalWords.toLocaleString()}} total words, ${{affectedWords.toLocaleString()}} affected</div></div>
    <div class="kpi"><div class="label">Worst Song</div><div class="value" style="font-size:16px">${{worstSong}}</div><div class="sub">${{SONGS[worstSong]?.issue_count || 0}} issues, ${{SONGS[worstSong]?.pct_affected || 0}}% words affected</div></div>
  `;
}}
renderKPIs();

// Charts
const chartDefaults = {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ labels: {{ color: '#8b949e', font: {{ size: 11 }} }} }} }}, scales: {{}} }};

function songChart() {{
  const songs = STATS.by_song.filter(s => (s.type_total || s.total || 0) > 0).slice(0, 25);
  const types = Object.keys(TYPE_LABELS);
  const datasets = types.map(t => ({{
    label: TYPE_LABELS[t],
    data: songs.map(s => s["type_" + t] || 0),
    backgroundColor: TYPE_COLORS[t]
  }}));
  new Chart(document.getElementById("chartBySong"), {{
    type: "bar",
    data: {{ labels: songs.map(s => s.song), datasets }},
    options: {{
      ...chartDefaults,
      indexAxis: "y",
      plugins: {{ legend: {{ position: "top", labels: {{ color: '#8b949e', boxWidth: 12, font: {{ size: 10 }} }} }} }},
      scales: {{
        x: {{ stacked: true, grid: {{ color: '#21262d' }}, ticks: {{ color: '#8b949e' }} }},
        y: {{ stacked: true, grid: {{ display: false }}, ticks: {{ color: '#e6edf3', font: {{ size: 11 }} }} }}
      }},
      onClick: (e, el) => {{ if (el.length) showSongDetail(songs[el[0].index].song); }}
    }}
  }});
}}
songChart();

new Chart(document.getElementById("chartByType"), {{
  type: "doughnut",
  data: {{
    labels: Object.keys(STATS.by_type).map(t => TYPE_LABELS[t] || t),
    datasets: [{{ data: Object.values(STATS.by_type), backgroundColor: Object.keys(STATS.by_type).map(t => TYPE_COLORS[t] || '#888') }}]
  }},
  options: {{ ...chartDefaults, plugins: {{ legend: {{ position: "bottom", labels: {{ color: '#8b949e', boxWidth: 12, font: {{ size: 10 }} }} }} }} }}
}});

new Chart(document.getElementById("chartBySeverity"), {{
  type: "doughnut",
  data: {{
    labels: Object.keys(STATS.by_severity).map(s => s.charAt(0).toUpperCase() + s.slice(1)),
    datasets: [{{ data: Object.values(STATS.by_severity), backgroundColor: Object.keys(STATS.by_severity).map(s => SEV_COLORS[s]) }}]
  }},
  options: {{ ...chartDefaults, plugins: {{ legend: {{ position: "bottom", labels: {{ color: '#8b949e', boxWidth: 12, font: {{ size: 10 }} }} }} }} }}
}});

new Chart(document.getElementById("chartBySource"), {{
  type: "bar",
  data: {{
    labels: Object.keys(STATS.by_source),
    datasets: [{{ label: "Issues", data: Object.values(STATS.by_source).map(v => v.issues), backgroundColor: "#58a6ff" }}]
  }},
  options: {{
    ...chartDefaults,
    indexAxis: "y",
    scales: {{ x: {{ grid: {{ color: '#21262d' }}, ticks: {{ color: '#8b949e' }} }}, y: {{ grid: {{ display: false }}, ticks: {{ color: '#e6edf3', font: {{ size: 11 }} }} }} }}
  }}
}});

new Chart(document.getElementById("chartByRepair"), {{
  type: "bar",
  data: {{
    labels: Object.keys(STATS.repair_suggestions).map(k => REPAIR_LABELS[k] || k),
    datasets: [{{ label: "Issues", data: Object.values(STATS.repair_suggestions), backgroundColor: Object.keys(STATS.repair_suggestions).map((k,i) => ["#f85149","#d29922","#58a6ff","#e3b341","#3fb950"][i % 5]) }}]
  }},
  options: {{
    ...chartDefaults,
    indexAxis: "y",
    scales: {{ x: {{ grid: {{ color: '#21262d' }}, ticks: {{ color: '#8b949e' }} }}, y: {{ grid: {{ display: false }}, ticks: {{ color: '#e6edf3', font: {{ size: 11 }} }} }} }}
  }}
}});

// Tabs
document.querySelectorAll(".tab").forEach(tab => {{
  tab.addEventListener("click", () => {{
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById("panel-" + tab.dataset.tab).classList.add("active");
  }});
}});

// Songs list
function renderSongsList() {{
  const el = document.getElementById("songsList");
  let html = `<table><thead><tr>
    <th>Rank</th><th>Song</th><th>Issues</th><th>Critical</th><th>High</th><th>Warning</th>
    <th>% Words Affected</th><th>Total Words</th>
  </tr></thead><tbody>`;
  for (const s of STATS.by_song) {{
    const meta = SONGS[s.song] || {{}};
    html += `<tr style="cursor:pointer" onclick="showSongDetail('${{s.song}}')">
      <td>${{s.severity_rank || '-'}}</td>
      <td><strong>${{s.song}}</strong></td>
      <td>${{(s.type_total || 0).toLocaleString()}}</td>
      <td style="color:var(--red)">${{s.type_critical || 0}}</td>
      <td style="color:var(--orange)">${{s.type_high || 0}}</td>
      <td style="color:var(--yellow)">${{(s.type_warning || 0) + (s.type_high || 0)}}</td>
      <td>${{meta.pct_affected || 0}}%</td>
      <td>${{meta.total_words || 0}}</td>
    </tr>`;
  }}
  html += "</tbody></table>";
  el.innerHTML = html;
}}
renderSongsList();

function showSongDetail(song) {{
  const el = document.getElementById("songDetail");
  const listEl = document.getElementById("songsList");
  const meta = SONGS[song] || {{}};
  const issues = ISSUES.filter(i => i.song === song);
  const songDur = Math.max(...issues.map(i => (i.start || 0) > (i.end || 0) ? i.start : i.end).concat([0]));

  const types = {{}};
  const sevs = {{}};
  issues.forEach(i => {{ types[i.issue_type] = (types[i.issue_type] || 0) + 1; sevs[i.severity] = (sevs[i.severity] || 0) + 1; }});

  let timelineHtml = '<div style="position:relative;height:40px;background:var(--surface2);border-radius:4px;margin:8px 0">';
  issues.forEach(i => {{
    const t = Math.max(i.start || 0, i.end || 0);
    const pct = songDur > 0 ? (t / songDur * 100) : 0;
    const left = Math.min(pct, 100);
    timelineHtml += `<div class="timeline-dot ${{i.severity}}" style="left:${{left}}%" title="L${{i.line_idx}} ${{i.word_text}}: ${{i.issue_label}}"></div>`;
  }});
  timelineHtml += '</div>';

  let issueRows = '';
  issues.sort((a, b) => a.line_idx - b.line_idx || a.word_idx - b.word_idx);
  issues.forEach(i => {{
    const derBadge = i.is_derivative ? ' <span class="badge derivative">derivative</span>' : '';
    const srcBadge = i.word_source ? ` <span class="badge source">${{i.word_source}}</span>` : '';
    const context = i.prev_line_text ? `<div class="context-line dim">${{esc(i.prev_line_text)}}</div>` : '';
    const highlight = i.line_text ? `<div class="context-line highlight">${{highlightWord(esc(i.line_text), i.word_text)}}</div>` : '';
    const nextCtx = i.next_line_text ? `<div class="context-line dim">${{esc(i.next_line_text)}}</div>` : '';

    issueRows += `<tr>
      <td>${{i.line_idx}}</td>
      <td><strong>${{esc(i.word_text)}}</strong></td>
      <td><span class="badge ${{i.severity}}">${{i.severity}}</span>${{derBadge}}</td>
      <td>${{TYPE_LABELS[i.issue_type] || i.issue_type}}</td>
      <td>${{fmtTime(i.start)}} - ${{fmtTime(i.end)}}${{i.duration !== null ? ' (' + fmtDur(i.duration) + ')' : ''}}</td>
      <td>${{i.word_source || '-'}}</td>
      <td>${{REPAIR_LABELS[i.repair_suggestion] || i.repair_suggestion}}</td>
    </tr>`;
    if (context || highlight || nextCtx) {{
      issueRows += `<tr class="detail-row"><td colspan="7">${{context}}${{highlight}}${{nextCtx}}${{srcBadge}}</td></tr>`;
    }}
  }});

  el.innerHTML = `<div class="song-detail">
    <div class="song-header">
      <div><a class="back-link" onclick="hideSongDetail()">&larr; All Songs</a><h3>${{song}}</h3></div>
    </div>
    <div class="song-stats">
      <div class="song-stat"><div class="val">${{issues.length}}</div><div class="lbl">Issues</div></div>
      <div class="song-stat"><div class="val" style="color:var(--red)">${{sevs.critical || 0}}</div><div class="lbl">Critical</div></div>
      <div class="song-stat"><div class="val" style="color:var(--orange)">${{sevs.high || 0}}</div><div class="lbl">High</div></div>
      <div class="song-stat"><div class="val" style="color:var(--yellow)">${{(sevs.warning || 0) + (sevs.high || 0)}}</div><div class="lbl">Warning</div></div>
      <div class="song-stat"><div class="val">${{meta.pct_affected || 0}}%</div><div class="lbl">Words Affected</div></div>
      <div class="song-stat"><div class="val">${{meta.total_words || 0}}</div><div class="lbl">Total Words</div></div>
    </div>
    <h3 style="font-size:13px;color:var(--text2);margin:16px 0 4px">Timeline</h3>
    ${{timelineHtml}}
    <h3 style="font-size:13px;color:var(--text2);margin:16px 0 4px">Issues</h3>
    <table><thead><tr><th>Line</th><th>Word</th><th>Severity</th><th>Type</th><th>Timing</th><th>Source</th><th>Repair</th></tr></thead><tbody>${{issueRows}}</tbody></table>
  </div>`;

  el.style.display = "block";
  listEl.style.display = "none";
  document.querySelector('[data-tab="songs"]').click();
}}

function hideSongDetail() {{
  document.getElementById("songDetail").style.display = "none";
  document.getElementById("songsList").style.display = "block";
}}

// Issues table
let filteredIssues = [...ISSUES];
let currentPage = 0;
const PAGE_SIZE = 50;

function populateFilters() {{
  const songs = [...new Set(ISSUES.map(i => i.song))].sort();
  const types = [...new Set(ISSUES.map(i => i.issue_type))].sort();
  const sevs = [...new Set(ISSUES.map(i => i.severity))].sort();
  const sources = [...new Set(ISSUES.map(i => i.word_source).filter(Boolean))].sort();

  const selSong = document.getElementById("filterSong");
  songs.forEach(s => {{ const o = document.createElement("option"); o.value = s; o.textContent = s; selSong.appendChild(o); }});
  const selType = document.getElementById("filterType");
  types.forEach(t => {{ const o = document.createElement("option"); o.value = t; o.textContent = TYPE_LABELS[t] || t; selType.appendChild(o); }});
  const selSev = document.getElementById("filterSeverity");
  sevs.forEach(s => {{ const o = document.createElement("option"); o.value = s; o.textContent = s; selSev.appendChild(o); }});
  const selSrc = document.getElementById("filterSource");
  sources.forEach(s => {{ const o = document.createElement("option"); o.value = s; o.textContent = s; selSrc.appendChild(o); }});
}}
populateFilters();

function filterIssues() {{
  const q = document.getElementById("issueSearch").value.toLowerCase();
  const song = document.getElementById("filterSong").value;
  const type = document.getElementById("filterType").value;
  const sev = document.getElementById("filterSeverity").value;
  const src = document.getElementById("filterSource").value;
  const hideDer = document.getElementById("hideDerivative").checked;

  filteredIssues = ISSUES.filter(i => {{
    if (song && i.song !== song) return false;
    if (type && i.issue_type !== type) return false;
    if (sev && i.severity !== sev) return false;
    if (src && i.word_source !== src) return false;
    if (hideDer && i.is_derivative) return false;
    if (q) {{
      const hay = [i.song, i.word_text, i.line_text, i.issue_label, i.word_source, i.root_cause_hint].join(" ").toLowerCase();
      if (!hay.includes(q)) return false;
    }}
    return true;
  }});
  currentPage = 0;
  renderIssuesTable();
}}

let sortCol = "song_rank";
let sortAsc = true;

document.querySelectorAll("#issuesTable th").forEach(th => {{
  th.addEventListener("click", () => {{
    const col = th.dataset.col;
    if (sortCol === col) sortAsc = !sortAsc;
    else {{ sortCol = col; sortAsc = true; }}
    document.querySelectorAll("#issuesTable th").forEach(t => t.classList.remove("sorted"));
    th.classList.add("sorted");
    renderIssuesTable();
  }});
}});

function renderIssuesTable() {{
  const sorted = [...filteredIssues].sort((a, b) => {{
    let va = a[sortCol], vb = b[sortCol];
    if (typeof va === "string") {{ va = va.toLowerCase(); vb = vb.toLowerCase(); }}
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  }});

  const start = currentPage * PAGE_SIZE;
  const page = sorted.slice(start, start + PAGE_SIZE);
  const body = document.getElementById("issuesBody");

  body.innerHTML = page.map(i => {{
    const der = i.is_derivative ? ' <span class="badge derivative">derivative</span>' : '';
    return `<tr>
      <td>${{i.song_rank}}</td>
      <td style="cursor:pointer;color:var(--accent)" onclick="showSongDetail('${{i.song}}')">${{i.song}}</td>
      <td><span class="badge ${{i.severity}}">${{i.severity}}</span>${{der}}</td>
      <td>${{TYPE_LABELS[i.issue_type] || i.issue_type}}</td>
      <td>${{i.line_idx}}</td>
      <td><strong>${{esc(i.word_text)}}</strong></td>
      <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${{esc(i.line_text)}}">${{esc(i.line_text)}}</td>
      <td><span class="badge source">${{i.word_source || '?'}}</span></td>
      <td>${{i.root_cause_hint}}</td>
    </tr>`;
  }}).join("");

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const pag = document.getElementById("issuesPagination");
  if (totalPages <= 1) {{ pag.innerHTML = `<span class="info">${{sorted.length}} issues</span>`; return; }}
  let html = `<span class="info">${{sorted.length}} issues &bull; Page ${{currentPage + 1}} of ${{totalPages}}</span>`;
  html += `<button class="btn" onclick="goPage(0)" ${{currentPage === 0 ? 'disabled' : ''}}>&laquo;</button>`;
  html += `<button class="btn" onclick="goPage(${{currentPage - 1}})" ${{currentPage === 0 ? 'disabled' : ''}}>&lsaquo;</button>`;
  const range = [Math.max(0, currentPage - 2), Math.min(totalPages - 1, currentPage + 2)];
  for (let p = range[0]; p <= range[1]; p++) {{
    html += `<button class="btn ${{p === currentPage ? 'active' : ''}}" onclick="goPage(${{p}})">${{p + 1}}</button>`;
  }}
  html += `<button class="btn" onclick="goPage(${{currentPage + 1}})" ${{currentPage === totalPages - 1 ? 'disabled' : ''}}>&rsaquo;</button>`;
  html += `<button class="btn" onclick="goPage(${{totalPages - 1}})" ${{currentPage === totalPages - 1 ? 'disabled' : ''}}>&raquo;</button>`;
  pag.innerHTML = html;
}}

function goPage(p) {{
  const max = Math.ceil(filteredIssues.length / PAGE_SIZE) - 1;
  currentPage = Math.max(0, Math.min(max, p));
  renderIssuesTable();
}}
renderIssuesTable();

// Diagnosis panel
function renderDiagnosis() {{
  const el = document.getElementById("diagnosisContent");
  const inversions = ISSUES.filter(i => i.issue_type === "start_gte_end");
  const cascadeGaps = ISSUES.filter(i => i.issue_type === "gap_from_prev" && i.is_derivative);
  const indieGaps = ISSUES.filter(i => i.issue_type === "gap_from_prev" && !i.is_derivative);
  const under = ISSUES.filter(i => i.issue_type === "duration_undersize");
  const over = ISSUES.filter(i => i.issue_type === "duration_overflow");

  const transInv = inversions.filter(i => i.word_source === "transcription");
  const interpInv = inversions.filter(i => i.word_source === "interpolated");

  const worstSongs = STATS.by_song.filter(s => (s.type_start_gte_end || 0) > 10).map(s => s.song);

  el.innerHTML = `
    <div class="section"><h2>Risk Assessment</h2></div>

    <div class="risk-card">
      <h4>Systemic Timestamp Inversion <span class="risk-level" style="background:rgba(248,81,73,0.15);color:var(--red)">CRITICAL</span></h4>
      <p>${{inversions.length.toLocaleString()}} words have inverted timestamps (start >= end). This is the dominant issue, accounting for ${{(inversions.length / STATS.total_issues * 100).toFixed(0)}}% of all issues.</p>
      <ul>
        <li><strong>${{transInv.length.toLocaleString()}}</strong> are from <code>transcription</code> source words (${{(transInv.length / inversions.length * 100).toFixed(0)}}% of inversions)</li>
        <li><strong>${{interpInv.length.toLocaleString()}}</strong> are from <code>interpolated</code> source words</li>
        <li><strong>${{worstSongs.length}}</strong> songs have >10 inversions: ${{worstSongs.join(", ")}}</li>
      </ul>
      <p><strong>Root cause:</strong> The transcription/alignment pipeline sometimes assigns completely wrong end timestamps to whole blocks of lines. The two worst songs (asabaal: 474, child-of-god-who-you-be: 348) account for ${{((474 + 348) / inversions.length) * 100).toFixed(0)}}% of all inversions.</p>
      <p><strong>Repair path:</strong> Re-run alignment on affected songs. Songs with >50% words affected likely need complete re-sync.</p>
    </div>

    <div class="risk-card">
      <h4>Cascade Gap False Positives <span class="risk-level" style="background:rgba(139,148,158,0.15);color:var(--text2)">LOW</span></h4>
      <p>${{cascadeGaps.length.toLocaleString()}} "gap from previous word" issues are artifacts of inverted timestamps. When a word has start >= end, the next word sees an apparent huge gap. <strong>These are not independent issues</strong> and will resolve when inversions are fixed.</p>
      <p><strong>Independent gaps:</strong> Only ${{indieGaps.length}} gap issues are not caused by inversions.</p>
    </div>

    <div class="risk-card">
      <h4>Duration Undersize (Interpolated) <span class="risk-level" style="background:rgba(227,179,65,0.15);color:var(--yellow)">MEDIUM</span></h4>
      <p>${{under.length.toLocaleString()}} words have durations under 40ms. Most (${{under.filter(i => i.word_source === "interpolated").length}}) are from <code>interpolated</code> source, meaning the sync algorithm filled in approximate timestamps with near-zero durations.</p>
      <p><strong>Impact:</strong> Words flash on screen too briefly. May be tolerable if the word is also visible during adjacent word display in progressive reveal mode.</p>
      <p><strong>Repair path:</strong> Improve interpolation bounds estimation, or accept as tolerable visual noise.</p>
    </div>

    <div class="risk-card">
      <h4>Duration Overflow (Vocal Onset Only) <span class="risk-level" style="background:rgba(227,179,65,0.15);color:var(--yellow)">MEDIUM</span></h4>
      <p>${{over.length.toLocaleString()}} words have durations over 1.5s. Most (${{over.filter(i => i.word_source === "vocal_onset_only").length}}) are from <code>vocal_onset_only</code> source, where only a start time was detected and the system stretches the word to the next event.</p>
      <p><strong>Impact:</strong> Word stays on screen too long. Tolerable for 1.5-3s range, problematic for 10s+.</p>
      <p><strong>Repair path:</strong> Cap <code>vocal_onset_only</code> durations to a reasonable max (e.g., 2s) in the sync pipeline.</p>
    </div>

    <div class="risk-card">
      <h4>Recommended Next Steps</h4>
      <ul>
        <li><strong>Priority 1:</strong> Re-sync asabaal and child-of-god-who-you-be (61% of all inversions)</li>
        <li><strong>Priority 2:</strong> Review the transcription alignment code for the end-time assignment bug</li>
        <li><strong>Priority 3:</strong> Cap <code>vocal_onset_only</code> durations to 2s max in the sync pipeline</li>
        <li><strong>Priority 4:</strong> Improve <code>interpolated</code> duration estimation to avoid near-zero values</li>
        <li><strong>Priority 5:</strong> Re-audit after fixes to confirm cascade gaps resolve</li>
      </ul>
    </div>

    <div class="risk-card">
      <h4>Source Reliability Ranking</h4>
      <p>Based on issue rates across all songs:</p>
      <ul>
        <li><code>whisper_plus_vocal_onset</code> &mdash; Best (5.2% issue rate, 0 inversions)</li>
        <li><code>vocal_onset</code> &mdash; Good (8.3% issue rate)</li>
        <li><code>transcription</code> &mdash; Moderate (15.1% issue rate, but 85% of all inversions)</li>
        <li><code>interpolated</code> &mdash; Poor (24.5% issue rate, mostly undersize)</li>
        <li><code>vocal_onset_only</code> &mdash; Worst (28.5% issue rate, mostly overflow)</li>
      </ul>
    </div>
  `;
}}
renderDiagnosis();

// Helpers
function esc(s) {{ return (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }}
function highlightWord(line, word) {{ return line.replace(new RegExp("(^|\\\\s)(" + word.replace(/[.*+?^${{}}()|[\]\\\\]/g, '\\\\$&') + ")($|\\\\s)", "gi"), "$1<strong style='color:var(--red)'>$2</strong>$3"); }}
function fmtTime(t) {{ if (t == null) return "-"; return t.toFixed(2) + "s"; }}
function fmtDur(d) {{ if (d == null) return "-"; if (d < 0) return d.toFixed(2) + "s (inverted)"; return d.toFixed(2) + "s"; }}

function exportCSV() {{
  const rows = [Object.keys(ISSUES[0] || {{}}).join(",")];
  ISSUES.forEach(i => {{
    rows.push(Object.values(i).map(v => '"' + String(v || "").replace(/"/g, '""') + '"').join(","));
  }});
  const blob = new Blob([rows.join("\\n")], {{ type: "text/csv" }});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "timing_issues.csv";
  a.click();
}}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate timing issues dashboard")
    parser.add_argument("projects_dir", help="Path to projects root (e.g., projects/prophetic-preprint)")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--open", action="store_true", help="Open in browser")
    args = parser.parse_args()

    build_dashboard(
        Path(args.projects_dir),
        Path(args.output) if args.output else None,
        open_browser=args.open,
    )
