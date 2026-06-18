#!/usr/bin/env python3
"""Review Dashboard Generator — aggregates transcription review flags with
audio playback, waveforms, and all transcription variants.

Reads needs_review.json, lyrics_synced.json, vocal_transcription_*.json,
waveforms.json, vocal_waveforms.json, and ingest.json from every project.
Generates a self-contained HTML report with interactive audio playback.

Usage:
    python scripts/review_dashboard.py projects/prophetic-preprint
    python scripts/review_dashboard.py projects/prophetic-preprint --open

For audio playback, serve the project root via HTTP:
    cd projects/prophetic-preprint && python -m http.server 8000
    Then open the dashboard through http://localhost:8000/output/dashboard/review_dashboard.html
"""

from __future__ import annotations

import html
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent


def _normalize(text: str) -> str:
    return text.lower().strip()


def collect_song_data(song_dir: Path) -> Optional[dict]:
    """Load all relevant data for a single song."""
    data_dir = song_dir / "data"

    needs_review_path = data_dir / "needs_review.json"
    if not needs_review_path.exists():
        return None

    nr_data = json.loads(needs_review_path.read_text(encoding="utf-8"))
    nr_lines = nr_data.get("lines", nr_data) if isinstance(nr_data, dict) else nr_data
    if not isinstance(nr_lines, list) or not nr_lines:
        return None

    synced = {}
    synced_path = data_dir / "lyrics_synced.json"
    if synced_path.exists():
        sd = json.loads(synced_path.read_text(encoding="utf-8"))
        for li, line in enumerate(sd.get("lines", [])):
            synced[li] = {"start": line.get("start", 0), "end": line.get("end", 0)}

    transcriptions = {}
    for f in sorted(os.listdir(data_dir)):
        if not f.startswith("vocal_transcription") or not f.endswith(".json"):
            continue
        stem = f.replace("vocal_transcription_", "").replace(".json", "")
        if stem == "":
            stem = "active"
        try:
            td = json.loads((data_dir / f).read_text(encoding="utf-8"))
            model = td.get("whisper_model", "?")
            if isinstance(model, dict):
                model = model.get(stem, model.get("combined_vocals", "?"))
            transcriptions[stem] = {
                "model": str(model),
                "segments": td.get("segments", []),
            }
        except (json.JSONDecodeError, OSError):
            continue

    ingest = {}
    ingest_path = data_dir / "ingest.json"
    if ingest_path.exists():
        try:
            ingest = json.loads(ingest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    audio_paths = {}
    stems_dir = data_dir / "cache" / "stems"
    combined_mix = stems_dir / "combined_mix.wav"
    if combined_mix.exists():
        audio_paths["combined_mix"] = str(combined_mix.relative_to(song_dir.parent.parent))
    combined_vocals = stems_dir / "combined_vocals.wav"
    if combined_vocals.exists():
        audio_paths["combined_vocals"] = str(combined_vocals.relative_to(song_dir.parent.parent))
    for s in ingest.get("stems", []):
        stype = s.get("stem_type", "")
        sname = s.get("name", stype)
        spath = s.get("path", "")
        if spath and "vocal" in stype.lower() and Path(spath).exists():
            audio_paths[stype] = str(Path(spath).relative_to(song_dir.parent.parent))

    waveforms = {}
    wf_path = data_dir / "waveforms.json"
    if wf_path.exists():
        try:
            wf = json.loads(wf_path.read_text(encoding="utf-8"))
            waveforms["combined_mix"] = wf.get("peaks", [])
        except (json.JSONDecodeError, OSError):
            pass
    vwf_path = data_dir / "vocal_waveforms.json"
    if vwf_path.exists():
        try:
            vwf = json.loads(vwf_path.read_text(encoding="utf-8"))
            waveforms["combined_vocals"] = vwf.get("peaks", [])
        except (json.JSONDecodeError, OSError):
            pass

    flags = []
    for entry in nr_lines:
        if not isinstance(entry, dict):
            continue
        li = entry.get("line_index", entry.get("line", -1))
        line_ts = synced.get(li, {"start": 0, "end": 0})

        nearby_transcriptions = []
        for stem_name, trans in transcriptions.items():
            for seg in trans["segments"]:
                seg_start = seg.get("start", 0)
                seg_end = seg.get("end", 0)
                if seg_end >= line_ts["start"] - 1 and seg_start <= line_ts["end"] + 1:
                    nearby_transcriptions.append({
                        "stem": stem_name,
                        "model": trans["model"],
                        "text": seg.get("text", ""),
                        "start": round(seg_start, 2),
                        "end": round(seg_end, 2),
                        "gap_fill": seg.get("gap_fill", False),
                        "gap_region": seg.get("gap_region", ""),
                    })

        pps = 100
        region_peaks = {}
        for wf_source, peaks in waveforms.items():
            si = max(0, int((line_ts["start"] - 3) * pps))
            ei = min(len(peaks), int((line_ts["end"] + 3) * pps))
            region_peaks[wf_source] = peaks[si:ei]

        flag = dict(entry)
        flag["song"] = song_dir.name
        flag["line_index"] = li
        flag["timestamp"] = {
            "start": round(line_ts["start"], 2),
            "end": round(line_ts["end"], 2),
        }
        flag["transcriptions"] = nearby_transcriptions
        flag["waveforms"] = region_peaks
        flag["audio_paths"] = audio_paths
        flags.append(flag)

    return {"song": song_dir.name, "flags": flags, "audio_paths": audio_paths}


def generate_html(all_data: List[dict], projects_dir: Path) -> str:
    total_flags = sum(len(d["flags"]) for d in all_data)
    all_flags_json = json.dumps(all_data, ensure_ascii=False)

    by_song_html = []
    for data in all_data:
        song = data["song"]
        flags = data["flags"]
        if not flags:
            continue

        type_counts = Counter(
            f.get("discrepancy_type") or f.get("reason", "unknown")
            for f in flags
        )

        flag_cards = []
        for f in flags:
            li = f["line_index"]
            ts = f["timestamp"]
            lyric = html.escape(f.get("text", ""))[:70]
            reason = f.get("reason", f.get("discrepancy_type", "?"))
            disc_type = f.get("discrepancy_type", "")
            desc = html.escape(f.get("discrepancy_description", ""))
            suggestion = html.escape(f.get("suggestion", ""))

            trans_rows = []
            for t in f.get("transcriptions", []):
                tstem = html.escape(t["stem"])
                tmodel = html.escape(t["model"])
                ttext = html.escape(t["text"])[:60]
                tstart = t["start"]
                tend = t["end"]
                origin = "gap-fill" if t.get("gap_fill") else "initial"
                origin_class = "origin-gapfill" if t.get("gap_fill") else "origin-initial"
                gap_region = f' <span class="gap-region">({html.escape(t.get("gap_region",""))})</span>' if t.get("gap_fill") and t.get("gap_region") else ""
                trans_rows.append(f"""
                    <tr>
                        <td class="t-stem">{tstem}</td>
                        <td class="t-model">{tmodel}</td>
                        <td class="t-origin {origin_class}">{origin}{gap_region}</td>
                        <td class="t-text">{ttext}</td>
                        <td class="t-time">{tstart:.1f}-{tend:.1f}s</td>
                        <td><button class="mini-play" data-start="{tstart}" data-end="{tend}" data-song="{song}">▶</button></td>
                    </tr>""")

            if not trans_rows:
                trans_rows.append('<tr><td colspan="6" class="muted">No transcription segments found in this region</td></tr>')

            trans_table = f"""
                <table class="trans-comparison">
                    <thead><tr><th>Source</th><th>Model</th><th>Origin</th><th>Text</th><th>Time</th><th></th></tr></thead>
                    <tbody>{"".join(trans_rows)}</tbody>
                </table>"""

            wf_sources = list(f.get("waveforms", {}).keys())
            wf_options = " ".join(
                f'<option value="{ws}">{ws.replace("_", " ").title()}</option>'
                for ws in wf_sources
            )

            audio_sources = f.get("audio_paths", {})
            audio_options = " ".join(
                f'<option value="{html.escape(p)}">{html.escape(k.replace("_", " ").title())}</option>'
                for k, p in audio_sources.items()
            )

            peak_data = json.dumps(f.get("waveforms", {}))

            flag_cards.append(f"""
                <div class="flag-card" data-song="{song}" data-line="{li}"
                     data-start="{ts["start"]}" data-end="{ts["end"]}"
                     data-peaks='{html.escape(peak_data)}'
                     data-audio-paths='{html.escape(json.dumps(audio_sources))}'>
                    <div class="flag-header">
                        <span class="line-badge">L{li}</span>
                        <span class="time-badge">{ts["start"]:.1f}s – {ts["end"]:.1f}s</span>
                        <span class="reason-badge reason-{html.escape(reason)}">{html.escape(reason)}</span>
                    </div>
                    <div class="lyric-line">Lyrics: <strong>{lyric}</strong></div>
                    {trans_table}
                    <div class="audio-controls">
                        <select class="audio-source-select">{audio_options}</select>
                        <button class="play-region-btn" data-start="{ts["start"]}" data-end="{ts["end"]}">▶ Play {ts["start"]:.1f}-{ts["end"]:.1f}s</button>
                        <canvas class="waveform-canvas" width="400" height="40"></canvas>
                    </div>
                    {f'<div class="desc">{desc}</div>' if desc else ''}
                    {f'<div class="suggestion">💡 {suggestion}</div>' if suggestion else ''}
                </div>""")

        by_song_html.append(f"""
            <div class="song-section">
                <div class="song-header" onclick="toggleSong('{song}')">
                    <span class="song-name">{song}</span>
                    <span class="flag-count">{len(flags)} flags</span>
                    <span class="toggle-icon">[show]</span>
                </div>
                <div class="song-detail" id="song-{song}" style="display:none;">
                    {''.join(flag_cards)}
                </div>
            </div>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Transcription Review — {projects_dir.name}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 20px; line-height: 1.5; }}
h1 {{ color: #e94560; margin-bottom: 4px; }}
.subtitle {{ color: #888; margin-bottom: 8px; font-size: 14px; }}
.note {{ background: #16213e; border-left: 3px solid #e94560; padding: 8px 14px; margin-bottom: 16px; font-size: 13px; color: #aaa; border-radius: 0 4px 4px 0; }}
.summary {{ background: #16213e; border-radius: 8px; padding: 14px 20px; margin-bottom: 20px; display: flex; gap: 20px; align-items: center; }}
.summary .total {{ font-size: 24px; font-weight: bold; color: #e94560; }}
.song-section {{ background: #16213e; border-radius: 6px; margin-bottom: 6px; overflow: hidden; }}
.song-header {{ display: flex; align-items: center; gap: 12px; padding: 10px 16px; cursor: pointer; }}
.song-header:hover {{ background: #1a2744; }}
.song-name {{ font-weight: 600; min-width: 200px; }}
.flag-count {{ color: #e94560; font-weight: bold; }}
.toggle-icon {{ color: #888; font-size: 12px; margin-left: auto; }}
.song-detail {{ padding: 0 16px 16px; }}
.flag-card {{ background: #0f1626; border-radius: 6px; padding: 12px 14px; margin-bottom: 10px; border-left: 3px solid #333; }}
.flag-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }}
.line-badge {{ font-family: monospace; color: #888; font-size: 13px; }}
.time-badge {{ background: #2a3a5e; color: #8ab4f8; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-family: monospace; }}
.reason-badge {{ padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.reason-misheard_text, .reason-misheard {{ background: #e74c3c; color: #fff; }}
.reason-repetition_mismatch {{ background: #e67e22; color: #fff; }}
.reason-all_words_interpolated, .reason-majority_interpolated {{ background: #f39c12; color: #333; }}
.reason-missing_section {{ background: #95a5a6; color: #fff; }}
.lyric-line {{ margin-bottom: 8px; font-size: 14px; }}
.lyric-line strong {{ color: #e0e0e0; }}
table.trans-comparison {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 8px; }}
table.trans-comparison th {{ text-align: left; padding: 4px 6px; color: #666; border-bottom: 1px solid #2a3a5e; font-size: 10px; text-transform: uppercase; }}
table.trans-comparison td {{ padding: 4px 6px; border-bottom: 1px solid #1a2744; vertical-align: top; }}
.t-stem {{ color: #8ab4f8; font-weight: 600; white-space: nowrap; }}
.t-model {{ color: #888; font-size: 11px; }}
.t-origin {{ font-size: 11px; }}
.origin-initial {{ color: #888; }}
.origin-gapfill {{ color: #4ecca3; font-weight: 600; }}
.gap-region {{ color: #555; font-size: 10px; }}
.t-text {{ color: #ccc; font-style: italic; }}
.t-time {{ color: #666; font-family: monospace; font-size: 11px; white-space: nowrap; }}
.muted {{ color: #555; font-style: italic; }}
.mini-play {{ background: none; border: 1px solid #333; color: #8ab4f8; cursor: pointer; padding: 2px 6px; border-radius: 3px; font-size: 11px; }}
.mini-play:hover {{ background: #1a2744; }}
.audio-controls {{ display: flex; align-items: center; gap: 8px; margin-top: 6px; flex-wrap: wrap; }}
.audio-source-select, .play-region-btn {{ background: #1a2744; color: #e0e0e0; border: 1px solid #2a3a5e; padding: 3px 8px; border-radius: 4px; font-size: 12px; cursor: pointer; }}
.play-region-btn {{ color: #4ecca3; border-color: #4ecca3; }}
.play-region-btn:hover {{ background: #4ecca3; color: #0f1626; }}
.waveform-canvas {{ background: #0a0f1a; border-radius: 3px; }}
.desc {{ color: #e94560; font-size: 12px; margin-top: 4px; }}
.suggestion {{ color: #4ecca3; font-size: 12px; margin-top: 2px; }}
</style>
</head>
<body>
<h1>Transcription Review Dashboard</h1>
<p class="subtitle">{projects_dir.name} — {len(all_data)} songs, {total_flags} flags</p>
<div class="note">
    💡 For audio playback: run <code>python -m http.server</code> from <code>{projects_dir.name}</code> root,
    then open this file via <code>http://localhost:8000/output/dashboard/review_dashboard.html</code>
</div>
<div class="summary">
    <div class="total">{total_flags}</div>
    <div>flags requiring review</div>
</div>
{''.join(by_song_html)}
<audio id="hidden-audio" preload="none"></audio>
<script>
const ALL_DATA = {all_flags_json};
let currentSong = null;

function toggleSong(song) {{
    const el = document.getElementById('song-' + song);
    const icon = event.currentTarget.querySelector('.toggle-icon');
    if (el.style.display === 'none') {{
        el.style.display = 'block';
        icon.textContent = '[hide]';
    }} else {{
        el.style.display = 'none';
        icon.textContent = '[show]';
    }}
}}

const audio = document.getElementById('hidden-audio');
let pauseTimer = null;

function playRegion(start, end, audioPath) {{
    if (audioPath) {{
        const basePath = window.location.pathname.replace('/output/dashboard/review_dashboard.html', '/');
        audio.src = basePath + audioPath;
    }}
    audio.currentTime = start;
    audio.play().catch(e => console.log('Playback error:', e));
    if (pauseTimer) clearTimeout(pauseTimer);
    pauseTimer = setTimeout(() => audio.pause(), (end - start + 0.5) * 1000);
}}

document.addEventListener('click', (e) => {{
    const playBtn = e.target.closest('.play-region-btn');
    if (playBtn) {{
        const card = playBtn.closest('.flag-card');
        const start = parseFloat(card.dataset.start);
        const end = parseFloat(card.dataset.end);
        const select = card.querySelector('.audio-source-select');
        const audioPath = select.value;
        playRegion(start, end, audioPath);
        drawWaveform(card);
        return;
    }}

    const miniBtn = e.target.closest('.mini-play');
    if (miniBtn) {{
        const start = parseFloat(miniBtn.dataset.start);
        const end = parseFloat(miniBtn.dataset.end);
        const song = miniBtn.dataset.song;
        const card = miniBtn.closest('.flag-card');
        const select = card.querySelector('.audio-source-select');
        const audioPath = select.value;
        playRegion(start, end, audioPath);
        return;
    }}
}});

document.addEventListener('change', (e) => {{
    if (e.target.classList.contains('audio-source-select')) {{
        const card = e.target.closest('.flag-card');
        drawWaveform(card);
    }}
}});

function drawWaveform(card) {{
    const canvas = card.querySelector('.waveform-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const peaksData = JSON.parse(card.dataset.peaks || '{{}}');
    const select = card.querySelector('.audio-source-select');
    const source = select.value.replace(/\\/g, '').split('/').pop().replace('.wav', '').replace(/\\s/g, '_').toLowerCase();

    let peaks = null;
    for (const [ws, p] of Object.entries(peaksData)) {{
        if (source.includes(ws.replace('_', '')) || ws.replace('_', '').includes(source)) {{
            peaks = p;
            break;
        }}
    }}
    if (!peaks && Object.keys(peaksData).length > 0) {{
        peaks = Object.values(peaksData)[0];
    }}

    if (!peaks || peaks.length === 0) {{
        ctx.fillStyle = '#333';
        ctx.fillRect(0, h/2-1, w, 2);
        ctx.fillStyle = '#555';
        ctx.font = '10px sans-serif';
        ctx.fillText('No waveform data for this source', 4, h/2+12);
        return;
    }}

    const barW = w / peaks.length;
    const start = parseFloat(card.dataset.start);
    const end = parseFloat(card.dataset.end);
    const pps = 100;
    const regionStart = Math.max(0, (start - 3)) * pps;
    const regionEnd = Math.min(peaks.length, (end + 3) * pps);

    for (let i = 0; i < peaks.length; i++) {{
        const barH = Math.max(1, peaks[i] * (h * 0.45));
        const x = i * barW;
        const inRegion = i >= regionStart && i <= regionEnd;
        ctx.fillStyle = inRegion ? '#e94560' : '#2a3a5e';
        ctx.fillRect(x, h/2 - barH, Math.max(1, barW - 0.5), barH * 2);
    }}
}}
</script>
</body>
</html>"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/review_dashboard.py <projects_dir> [--open]")
        sys.exit(1)

    projects_dir = Path(sys.argv[1]).resolve()
    open_browser = "--open" in sys.argv

    if not projects_dir.is_dir():
        print(f"Error: {projects_dir} is not a directory")
        sys.exit(1)

    songs_dir = projects_dir / "projects"
    if not songs_dir.exists():
        songs_dir = projects_dir

    all_data = []
    for song_dir in sorted(songs_dir.iterdir()):
        if not song_dir.is_dir():
            continue
        data = collect_song_data(song_dir)
        if data and data["flags"]:
            all_data.append(data)

    total_flags = sum(len(d["flags"]) for d in all_data)
    if total_flags == 0:
        print("No review flags found.")
        sys.exit(0)

    html_content = generate_html(all_data, projects_dir)

    output_dir = projects_dir / "output" / "dashboard"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "review_dashboard.html"
    output_path.write_text(html_content, encoding="utf-8")

    print(f"  Collected {total_flags} review flags from {len(all_data)} songs")
    print(f"  Wrote {output_path}")

    if open_browser:
        import webbrowser
        webbrowser.open(f"file://{output_path.absolute()}")


if __name__ == "__main__":
    main()
