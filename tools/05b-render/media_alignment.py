#!/usr/bin/env python3
"""
Media Alignment Report

Proves or falsifies alignment across three timeline domains:
  - Audio output timeline
  - Video output timeline
  - Caption output timeline

For each surviving word, shows timestamps in all clock domains
and computes drift metrics.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent))

from segments import compute_timeline_clips, get_playable_segments, get_total_duration
from captions import build_caption_events


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def load_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_selected_segment_indices(project: dict) -> set:
    """Get set of segment indices that are in Tool 03 selection."""
    clips = project.get('clips', [])
    selected = set()
    for clip in clips:
        if clip.get('enabled', True) and clip.get('in_timeline', True):
            sel = clip.get('selected_segment', {})
            seg_idx = sel.get('segment_index')
            if seg_idx is not None:
                selected.add(seg_idx)
    return selected


def get_deleted_time_ranges(project: dict) -> List[Tuple[float, float]]:
    """Get list of (start, end) tuples for all deleted regions."""
    clips = project.get('clips', [])
    deleted = []
    for clip in clips:
        if clip.get('enabled', True) and clip.get('in_timeline', True):
            for dr in clip.get('deleted_regions', []):
                deleted.append((dr.get('start', 0), dr.get('end', 0)))
    return deleted


def is_word_in_deleted_region(word_start: float, word_end: float, 
                               deleted_ranges: List[Tuple[float, float]]) -> bool:
    """Check if a word falls within any deleted region."""
    for del_start, del_end in deleted_ranges:
        if del_start <= word_start < del_end:
            return True
        if del_start < word_end <= del_end:
            return True
    return False


def build_word_alignment_table(project: dict, timeline_clips: List[dict], 
                                caption_events: List[dict]) -> List[Dict[str, Any]]:
    """
    Build complete alignment table for all surviving words.
    
    For each word, includes timestamps in all clock domains.
    """
    transcript = project.get('transcript', {})
    segments = transcript.get('segments', [])
    selected_indices = get_selected_segment_indices(project)
    deleted_ranges = get_deleted_time_ranges(project)
    
    table = []
    word_id = 0
    
    for event in caption_events:
        output_start = event['output_start']
        output_end = event['output_end']
        original_start = event['original_start']
        original_end = event['original_end']
        segment_index = event.get('segment_index', -1)
        clip_id = event.get('clip_id', '')
        
        is_selected = segment_index in selected_indices
        
        for word in event.get('words', []):
            word_text = word.get('text', '')
            word_orig_start = word.get('start', 0)
            word_orig_end = word.get('end', 0)
            word_idx = word.get('word_index', -1)
            
            word_output_start = output_start + (word_orig_start - original_start)
            word_output_end = output_start + (word_orig_end - original_start)
            
            is_pruned = is_word_in_deleted_region(word_orig_start, word_orig_end, deleted_ranges)
            
            audio_out_start = word_orig_start
            audio_out_end = word_orig_end
            video_out_start = word_orig_start
            video_out_end = word_orig_end
            
            caption_minus_audio_ms = (word_output_start - audio_out_start) * 1000
            caption_minus_video_ms = (word_output_start - video_out_start) * 1000
            audio_minus_video_ms = 0.0
            
            row = {
                'word_id': word_id,
                'segment_index': segment_index,
                'word_index': word_idx,
                'text': word_text,
                't02_start': word_orig_start,
                't02_end': word_orig_end,
                'selected': is_selected,
                'pruned': is_pruned,
                'assembly_start': word_output_start,
                'assembly_end': word_output_end,
                'caption_start': word_output_start,
                'caption_end': word_output_end,
                'audio_out_start': audio_out_start,
                'audio_out_end': audio_out_end,
                'video_out_start': video_out_start,
                'video_out_end': video_out_end,
                'caption_minus_audio_ms': caption_minus_audio_ms,
                'caption_minus_video_ms': caption_minus_video_ms,
                'audio_minus_video_ms': audio_minus_video_ms,
                'clip_id': clip_id
            }
            
            table.append(row)
            word_id += 1
    
    return table


def compute_alignment_summary(table: List[Dict], project: dict, 
                               timeline_clips: List[dict]) -> Dict[str, Any]:
    """Compute summary metrics for alignment report."""
    
    if not table:
        return {
            'total_words': 0,
            'mean_caption_audio_drift_ms': 0,
            'max_caption_audio_drift_ms': 0,
            'min_caption_audio_drift_ms': 0,
            'mean_caption_video_drift_ms': 0,
            'max_caption_video_drift_ms': 0,
            'audio_video_drift_ms': 0,
            'clock_unified': False
        }
    
    caption_audio_drifts = [row['caption_minus_audio_ms'] for row in table]
    caption_video_drifts = [row['caption_minus_video_ms'] for row in table]
    
    transcript = project.get('transcript', {})
    segments = transcript.get('segments', [])
    raw_duration = max((seg.get('end', 0) for seg in segments), default=0)
    playable_duration = get_total_duration(timeline_clips)
    
    caption_duration = 0
    if table:
        caption_duration = max(row['caption_end'] for row in table)
    
    return {
        'total_words': len(table),
        'mean_caption_audio_drift_ms': sum(abs(d) for d in caption_audio_drifts) / len(caption_audio_drifts),
        'max_caption_audio_drift_ms': max(abs(d) for d in caption_audio_drifts),
        'min_caption_audio_drift_ms': min(abs(d) for d in caption_audio_drifts),
        'mean_caption_video_drift_ms': sum(abs(d) for d in caption_video_drifts) / len(caption_video_drifts),
        'max_caption_video_drift_ms': max(abs(d) for d in caption_video_drifts),
        'audio_video_drift_ms': 0,
        'raw_video_duration': raw_duration,
        'playable_duration': playable_duration,
        'caption_output_duration': caption_duration,
        'clock_unified': False
    }


def analyze_clock_unification(project: dict, timeline_clips: List[dict]) -> Dict[str, Any]:
    """
    Analyze how FFmpeg operations affect clock unification.
    
    Returns information about:
    - Audio timestamp operations
    - Video timestamp operations
    - Whether audio and video share unified time base
    """
    audio_ops = [
        "render.py: -c:a copy (no timing modification)",
        "manual_ffmpeg_proof.py: atrim=start:X:end=Y, asetpts=PTS-STARTPTS",
        "manual_ffmpeg_proof.py: concat=n=N:v=0:a=1"
    ]
    
    video_ops = [
        "render.py: drawtext overlays (no timing modification)", 
        "render.py: -c:v libx264 (re-encode, preserves timestamps)",
        "manual_ffmpeg_proof.py: trim=start:X:end=Y, setpts=PTS-STARTPTS",
        "manual_ffmpeg_proof.py: concat=n=N:v=1:a=0"
    ]
    
    playable_duration = get_total_duration(timeline_clips)
    
    transcript = project.get('transcript', {})
    segments = transcript.get('segments', [])
    raw_duration = max((seg.get('end', 0) for seg in segments), default=0)
    
    unified = raw_duration == playable_duration
    mechanism = None
    root_cause = None
    
    if unified:
        mechanism = "Audio and video output durations match - clocks are unified"
    else:
        root_cause = (
            f"Clock MISMATCH detected: "
            f"raw video duration ({raw_duration:.2f}s) != "
            f"playable segment sum ({playable_duration:.2f}s). "
            f"render.py uses original video without trim/concat, but caption timing "
            f"assumes assembly-projected timeline. This causes caption drift."
        )
    
    return {
        'audio_operations': audio_ops,
        'video_operations': video_ops,
        'unified': unified,
        'mechanism': mechanism,
        'root_cause_candidate': root_cause,
        'raw_video_duration': raw_duration,
        'playable_duration': playable_duration,
        'duration_mismatch': raw_duration - playable_duration
    }


def get_css() -> str:
    return '''<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: #1a1a2e;
        color: #eee;
        min-height: 100vh;
    }
    
    .container {
        max-width: 1800px;
        margin: 0 auto;
        padding: 20px;
    }
    
    header {
        margin-bottom: 30px;
        border-bottom: 2px solid #4cc9f0;
        padding-bottom: 15px;
    }
    
    h1 { color: #4cc9f0; margin-bottom: 5px; }
    h2 { color: #4cc9f0; margin: 25px 0 15px 0; font-size: 18px; }
    h3 { color: #4cc9f0; margin: 15px 0 10px 0; font-size: 14px; }
    .meta { color: #888; font-size: 13px; }
    
    .alert {
        padding: 15px 20px;
        border-radius: 6px;
        margin-bottom: 20px;
        font-weight: bold;
    }
    
    .alert.error {
        background: #f56565;
        color: white;
    }
    
    .alert.success {
        background: #48bb78;
        color: white;
    }
    
    .alert.warning {
        background: #ecc94b;
        color: #333;
    }
    
    .summary {
        background: #16213e;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px;
    }
    
    .metric-card {
        background: #1a1a2e;
        border-radius: 6px;
        padding: 12px;
        text-align: center;
    }
    
    .metric-card h4 {
        font-size: 10px;
        text-transform: uppercase;
        color: #888;
        margin-bottom: 6px;
    }
    
    .metric-value {
        font-size: 20px;
        font-weight: bold;
        color: #4cc9f0;
    }
    
    .metric-card.drift .metric-value { color: #f56565; }
    .metric-card.success .metric-value { color: #48bb78; }
    .metric-card.warning .metric-value { color: #ecc94b; }
    
    .clock-proof {
        background: #16213e;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .clock-proof pre {
        background: #0f0f1a;
        padding: 15px;
        border-radius: 4px;
        overflow-x: auto;
        font-size: 12px;
        line-height: 1.5;
    }
    
    .clock-proof code {
        color: #4cc9f0;
    }
    
    .timeline-section {
        background: #16213e;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        overflow-x: auto;
    }
    
    .timeline-container {
        position: relative;
        min-width: 1200px;
    }
    
    .time-ruler {
        height: 30px;
        background: #0f0f1a;
        border-radius: 4px;
        margin-bottom: 15px;
        position: relative;
    }
    
    .time-mark {
        position: absolute;
        bottom: 0;
        font-size: 10px;
        color: #888;
        transform: translateX(-50%);
    }
    
    .track-container {
        margin-bottom: 8px;
    }
    
    .track-label {
        font-size: 11px;
        color: #888;
        margin-bottom: 4px;
    }
    
    .timeline-track {
        height: 40px;
        background: #0f0f1a;
        border-radius: 4px;
        position: relative;
        overflow: hidden;
    }
    
    .segment-bar {
        position: absolute;
        height: 30px;
        top: 5px;
        border-radius: 3px;
        cursor: pointer;
    }
    
    .segment-bar.video { background: rgba(76, 201, 240, 0.6); border: 1px solid #4cc9f0; }
    .segment-bar.audio { background: rgba(72, 187, 120, 0.6); border: 1px solid #48bb78; }
    .segment-bar.caption { background: rgba(236, 201, 75, 0.6); border: 1px solid #ecc94b; }
    
    .word-marker {
        position: absolute;
        height: 16px;
        top: 12px;
        background: #4cc9f0;
        border-radius: 2px;
        cursor: pointer;
        transition: transform 0.1s;
        min-width: 2px;
    }
    
    .word-marker:hover {
        transform: scaleY(1.5);
        z-index: 100;
    }
    
    .word-marker.drift {
        background: #f56565;
    }
    
    .cursor-line {
        position: absolute;
        top: 0;
        bottom: 0;
        width: 1px;
        background: #f56565;
        pointer-events: none;
        display: none;
        z-index: 50;
    }
    
    .cursor-info {
        position: absolute;
        background: #16213e;
        border: 1px solid #f56565;
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 11px;
        pointer-events: none;
        display: none;
        z-index: 100;
        white-space: nowrap;
    }
    
    .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin-bottom: 15px;
        padding: 10px;
        background: #0f0f1a;
        border-radius: 4px;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 11px;
    }
    
    .legend-color {
        width: 20px;
        height: 10px;
        border-radius: 2px;
    }
    
    .table-section {
        background: #16213e;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .table-container {
        max-height: 600px;
        overflow-y: auto;
        overflow-x: auto;
    }
    
    .alignment-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
        white-space: nowrap;
    }
    
    .alignment-table th,
    .alignment-table td {
        padding: 6px 8px;
        text-align: left;
        border-bottom: 1px solid #2a2a4a;
    }
    
    .alignment-table th {
        background: #0f0f1a;
        color: #4cc9f0;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    
    .alignment-table th.category {
        background: #16213e;
        text-align: center;
        border-bottom: 2px solid #4cc9f0;
    }
    
    .alignment-table tr:hover {
        background: rgba(76, 201, 240, 0.1);
    }
    
    .alignment-table .drift-value {
        color: #f56565;
        font-weight: bold;
    }
    
    .alignment-table .zero-drift {
        color: #48bb78;
    }
    
    .alignment-table .text-col {
        max-width: 80px;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .tooltip {
        position: fixed;
        background: #16213e;
        border: 1px solid #4cc9f0;
        border-radius: 6px;
        padding: 10px 15px;
        font-size: 12px;
        pointer-events: none;
        z-index: 1000;
        display: none;
        max-width: 350px;
    }
    
    .tooltip h5 {
        color: #4cc9f0;
        margin-bottom: 5px;
    }
    
    .tooltip p {
        margin: 3px 0;
        color: #ccc;
    }
    
    .tooltip .drift {
        color: #f56565;
    }
    
    .operations-list {
        list-style: none;
        padding: 0;
    }
    
    .operations-list li {
        padding: 6px 0;
        border-bottom: 1px solid #2a2a4a;
        font-size: 12px;
    }
    
    .operations-list code {
        background: #0f0f1a;
        padding: 2px 6px;
        border-radius: 3px;
        color: #4cc9f0;
    }
</style>'''


def get_javascript(data: Dict) -> str:
    return f'''<script>
    const alignmentData = {json.dumps(data)};
    
    const tooltip = document.getElementById('tooltip');
    const cursorLine = document.getElementById('cursorLine');
    const cursorInfo = document.getElementById('cursorInfo');
    
    function showCursorAtPosition(x, word) {{
        if (!cursorLine || !cursorInfo) return;
        
        cursorLine.style.left = x + 'px';
        cursorLine.style.display = 'block';
        
        cursorInfo.style.left = (x + 10) + 'px';
        cursorInfo.style.top = '10px';
        cursorInfo.innerHTML = `
            <div><strong>At cursor:</strong></div>
            <div>Audio out: ${{word.audio_out_start.toFixed(3)}}s</div>
            <div>Video out: ${{word.video_out_start.toFixed(3)}}s</div>
            <div>Caption out: ${{word.caption_start.toFixed(3)}}s</div>
            <div class="drift">Drift: ${{word.caption_minus_audio_ms.toFixed(1)}}ms</div>
        `;
        cursorInfo.style.display = 'block';
    }}
    
    function hideCursor() {{
        if (cursorLine) cursorLine.style.display = 'none';
        if (cursorInfo) cursorInfo.style.display = 'none';
    }}
    
    document.querySelectorAll('.word-marker').forEach(marker => {{
        marker.addEventListener('mouseenter', (e) => {{
            const wordId = parseInt(marker.dataset.wordId);
            const word = alignmentData.table.find(w => w.word_id === wordId);
            
            if (word) {{
                const rect = marker.getBoundingClientRect();
                const container = document.getElementById('timelineContainer');
                const containerRect = container.getBoundingClientRect();
                const x = rect.left - containerRect.left + rect.width / 2;
                
                showCursorAtPosition(x, word);
                
                const driftClass = Math.abs(word.caption_minus_audio_ms) > 100 ? 'drift' : '';
                tooltip.innerHTML = `
                    <h5>"${{word.text}}"</h5>
                    <p><strong>Word ID:</strong> ${{word.word_id}}</p>
                    <p><strong>Segment:</strong> ${{word.segment_index}}, Word: ${{word.word_index}}</p>
                    <hr style="border-color: #2a2a4a; margin: 8px 0;">
                    <p><strong>T02 (original):</strong> ${{word.t02_start.toFixed(3)}} - ${{word.t02_end.toFixed(3)}}s</p>
                    <p><strong>Assembly:</strong> ${{word.assembly_start.toFixed(3)}} - ${{word.assembly_end.toFixed(3)}}s</p>
                    <hr style="border-color: #2a2a4a; margin: 8px 0;">
                    <p><strong>Audio out:</strong> ${{word.audio_out_start.toFixed(3)}} - ${{word.audio_out_end.toFixed(3)}}s</p>
                    <p><strong>Video out:</strong> ${{word.video_out_start.toFixed(3)}} - ${{word.video_out_end.toFixed(3)}}s</p>
                    <p><strong>Caption:</strong> ${{word.caption_start.toFixed(3)}} - ${{word.caption_end.toFixed(3)}}s</p>
                    <hr style="border-color: #2a2a4a; margin: 8px 0;">
                    <p class="${{driftClass}}"><strong>Caption - Audio:</strong> ${{word.caption_minus_audio_ms.toFixed(1)}}ms</p>
                    <p class="${{driftClass}}"><strong>Caption - Video:</strong> ${{word.caption_minus_video_ms.toFixed(1)}}ms</p>
                    <p><strong>Audio - Video:</strong> ${{word.audio_minus_video_ms.toFixed(1)}}ms</p>
                `;
                tooltip.style.display = 'block';
            }}
        }});
        
        marker.addEventListener('mousemove', (e) => {{
            tooltip.style.left = (e.clientX + 15) + 'px';
            tooltip.style.top = (e.clientY + 15) + 'px';
        }});
        
        marker.addEventListener('mouseleave', () => {{
            tooltip.style.display = 'none';
            hideCursor();
        }});
    }});
    
    document.querySelectorAll('.segment-bar').forEach(bar => {{
        bar.addEventListener('mouseenter', (e) => {{
            const start = parseFloat(bar.dataset.start);
            const end = parseFloat(bar.dataset.end);
            const type = bar.dataset.type;
            tooltip.innerHTML = `
                <h5>${{type.charAt(0).toUpperCase() + type.slice(1)}} Segment</h5>
                <p>Start: ${{start.toFixed(3)}}s</p>
                <p>End: ${{end.toFixed(3)}}s</p>
                <p>Duration: ${{(end - start).toFixed(3)}}s</p>
            `;
            tooltip.style.display = 'block';
        }});
        
        bar.addEventListener('mousemove', (e) => {{
            tooltip.style.left = (e.clientX + 15) + 'px';
            tooltip.style.top = (e.clientY + 15) + 'px';
        }});
        
        bar.addEventListener('mouseleave', () => {{
            tooltip.style.display = 'none';
        }});
    }});
</script>'''


def generate_html_report(table: List[Dict], summary: Dict, clock_analysis: Dict,
                          caption_events: List[Dict], timeline_clips: List[dict],
                          project: dict) -> str:
    """Generate interactive HTML visualization."""
    
    transcript = project.get('transcript', {})
    segments = transcript.get('segments', [])
    raw_duration = max((seg.get('end', 0) for seg in segments), default=0)
    
    max_duration = max(raw_duration, summary.get('caption_output_duration', 0))
    
    def pct(t):
        return (t / max_duration * 100) if max_duration > 0 else 0
    
    clock_unified = clock_analysis.get('unified', False)
    root_cause = clock_analysis.get('root_cause_candidate')
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media Alignment Report</title>
    {get_css()}
</head>
<body>
    <div class="container">
        <header>
            <h1>Media Alignment Report</h1>
            <p class="meta">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </header>
'''
    
    if not clock_unified and root_cause:
        html += f'''
        <div class="alert error">
            <strong>CLOCK MISMATCH DETECTED:</strong> {root_cause}
        </div>
'''
    elif clock_unified:
        html += f'''
        <div class="alert success">
            <strong>CLOCKS UNIFIED:</strong> Audio, video, and caption timelines are aligned.
        </div>
'''
    
    html += f'''
        <section class="summary">
            <h2>Summary Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h4>Total Words</h4>
                    <div class="metric-value">{summary.get('total_words', 0)}</div>
                </div>
                <div class="metric-card">
                    <h4>Raw Video</h4>
                    <div class="metric-value">{summary.get('raw_video_duration', 0):.1f}s</div>
                </div>
                <div class="metric-card">
                    <h4>Playable Sum</h4>
                    <div class="metric-value">{summary.get('playable_duration', 0):.1f}s</div>
                </div>
                <div class="metric-card">
                    <h4>Caption Output</h4>
                    <div class="metric-value">{summary.get('caption_output_duration', 0):.1f}s</div>
                </div>
                <div class="metric-card drift">
                    <h4>Mean Caption-Audio Drift</h4>
                    <div class="metric-value">{summary.get('mean_caption_audio_drift_ms', 0):.0f}ms</div>
                </div>
                <div class="metric-card drift">
                    <h4>Max Caption-Audio Drift</h4>
                    <div class="metric-value">{summary.get('max_caption_audio_drift_ms', 0):.0f}ms</div>
                </div>
                <div class="metric-card {'success' if clock_unified else 'drift'}">
                    <h4>Clock Unified?</h4>
                    <div class="metric-value">{'YES' if clock_unified else 'NO'}</div>
                </div>
                <div class="metric-card">
                    <h4>Audio-Video Drift</h4>
                    <div class="metric-value">0ms</div>
                </div>
            </div>
        </section>
        
        <section class="clock-proof">
            <h2>Clock Unification Proof</h2>
            
            <h3>Audio Timestamp Operations</h3>
            <ul class="operations-list">
'''
    for op in clock_analysis.get('audio_operations', []):
        html += f'                <li><code>{op}</code></li>\n'
    
    html += f'''            </ul>
            
            <h3>Video Timestamp Operations</h3>
            <ul class="operations-list">
'''
    for op in clock_analysis.get('video_operations', []):
        html += f'                <li><code>{op}</code></li>\n'
    
    html += f'''            </ul>
            
            <h3>Unification Status</h3>
            <pre>
'''
    if clock_unified:
        html += f"STATUS: UNIFIED\nMECHANISM: {clock_analysis.get('mechanism', 'Unknown')}"
    else:
        html += f"STATUS: NOT UNIFIED\n\nROOT CAUSE CANDIDATE:\n{clock_analysis.get('root_cause_candidate', 'Unknown')}"
    
    html += f'''            </pre>
            
            <h3>Duration Comparison</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h4>Raw Video Duration</h4>
                    <div class="metric-value">{clock_analysis.get('raw_video_duration', 0):.2f}s</div>
                </div>
                <div class="metric-card">
                    <h4>Playable Segments Sum</h4>
                    <div class="metric-value">{clock_analysis.get('playable_duration', 0):.2f}s</div>
                </div>
                <div class="metric-card {'success' if clock_analysis.get('duration_mismatch', 1) == 0 else 'warning'}">
                    <h4>Duration Mismatch</h4>
                    <div class="metric-value">{clock_analysis.get('duration_mismatch', 0):.2f}s</div>
                </div>
            </div>
        </section>
        
        <section class="timeline-section">
            <h2>Timeline Visualization</h2>
            
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background: rgba(76, 201, 240, 0.6);"></div>
                    <span>Video Output</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: rgba(72, 187, 120, 0.6);"></div>
                    <span>Audio Output</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: rgba(236, 201, 75, 0.6);"></div>
                    <span>Caption Output</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f56565;"></div>
                    <span>Word with Drift</span>
                </div>
            </div>
            
            <div class="timeline-container" id="timelineContainer">
                <div class="time-ruler" id="timeRuler">
'''
    
    for t in range(0, int(max_duration) + 1, max(1, int(max_duration / 25))):
        html += f'<span class="time-mark" style="left: {pct(t):.1f}%;">{t}s</span>\n'
    
    html += '''                </div>
'''
    
    html += f'''
                <div class="track-container">
                    <div class="track-label">Video Output Timeline (original video_combined.mp4)</div>
                    <div class="timeline-track" id="videoTrack">
                        <div class="segment-bar video" data-type="video" data-start="0" data-end="{raw_duration:.2f}" 
                             style="left: 0%; width: {pct(raw_duration):.1f}%"></div>
                    </div>
                </div>
                
                <div class="track-container">
                    <div class="track-label">Audio Output Timeline (same as video, -c:a copy)</div>
                    <div class="timeline-track" id="audioTrack">
                        <div class="segment-bar audio" data-type="audio" data-start="0" data-end="{raw_duration:.2f}"
                             style="left: 0%; width: {pct(raw_duration):.1f}%"></div>
                    </div>
                </div>
                
                <div class="track-container">
                    <div class="track-label">Caption Output Timeline (assembly-projected, 0-based)</div>
                    <div class="timeline-track" id="captionTrack">
'''
    
    for event in caption_events[:200]:
        start = event['output_start']
        end = event['output_end']
        html += f'''                        <div class="segment-bar caption" data-type="caption" data-start="{start:.3f}" data-end="{end:.3f}"
                             style="left: {pct(start):.2f}%; width: {pct(end) - pct(start):.2f}%"></div>
'''
    
    for word in table[:500]:
        left = pct(word['caption_start'])
        width = max(0.15, pct(word['caption_end']) - left)
        has_drift = abs(word['caption_minus_audio_ms']) > 100
        css_class = 'word-marker drift' if has_drift else 'word-marker'
        
        html += f'''                        <div class="{css_class}" data-word-id="{word['word_id']}"
                             style="left: {left:.2f}%; width: {width:.2f}%"></div>
'''
    
    html += '''                    </div>
                </div>
                
                <div class="cursor-line" id="cursorLine"></div>
                <div class="cursor-info" id="cursorInfo"></div>
            </div>
        </section>
'''
    
    html += f'''
        <section class="table-section">
            <h2>Word Alignment Table</h2>
            <p class="meta">Showing all {len(table)} surviving words with timestamps in each clock domain</p>
            
            <div class="table-container">
                <table class="alignment-table">
                    <thead>
                        <tr>
                            <th class="category" colspan="4">Identity</th>
                            <th class="category" colspan="2">Tool 02 (Original)</th>
                            <th class="category" colspan="2">Tool 03/04 Status</th>
                            <th class="category" colspan="2">Assembly Projected</th>
                            <th class="category" colspan="2">Caption Output</th>
                            <th class="category" colspan="2">Audio Output</th>
                            <th class="category" colspan="2">Video Output</th>
                            <th class="category" colspan="3">Drift Metrics (ms)</th>
                        </tr>
                        <tr>
                            <th>ID</th>
                            <th>Seg</th>
                            <th>W#</th>
                            <th>Text</th>
                            <th>t02_start</th>
                            <th>t02_end</th>
                            <th>Selected</th>
                            <th>Pruned</th>
                            <th>asm_start</th>
                            <th>asm_end</th>
                            <th>cap_start</th>
                            <th>cap_end</th>
                            <th>audio_start</th>
                            <th>audio_end</th>
                            <th>video_start</th>
                            <th>video_end</th>
                            <th>cap-audio</th>
                            <th>cap-video</th>
                            <th>audio-video</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    
    for row in table:
        selected_str = 'Y' if row['selected'] else 'N'
        pruned_str = 'Y' if row['pruned'] else 'N'
        
        cap_audio_class = 'drift-value' if abs(row['caption_minus_audio_ms']) > 100 else 'zero-drift'
        cap_video_class = 'drift-value' if abs(row['caption_minus_video_ms']) > 100 else 'zero-drift'
        av_class = 'zero-drift'
        
        html += f'''                        <tr>
                            <td>{row['word_id']}</td>
                            <td>{row['segment_index']}</td>
                            <td>{row['word_index']}</td>
                            <td class="text-col" title="{row['text']}">{row['text'][:15]}{'...' if len(row['text']) > 15 else ''}</td>
                            <td>{row['t02_start']:.3f}</td>
                            <td>{row['t02_end']:.3f}</td>
                            <td>{selected_str}</td>
                            <td>{pruned_str}</td>
                            <td>{row['assembly_start']:.3f}</td>
                            <td>{row['assembly_end']:.3f}</td>
                            <td>{row['caption_start']:.3f}</td>
                            <td>{row['caption_end']:.3f}</td>
                            <td>{row['audio_out_start']:.3f}</td>
                            <td>{row['audio_out_end']:.3f}</td>
                            <td>{row['video_out_start']:.3f}</td>
                            <td>{row['video_out_end']:.3f}</td>
                            <td class="{cap_audio_class}">{row['caption_minus_audio_ms']:.1f}</td>
                            <td class="{cap_video_class}">{row['caption_minus_video_ms']:.1f}</td>
                            <td class="{av_class}">{row['audio_minus_video_ms']:.1f}</td>
                        </tr>
'''
    
    html += '''                    </tbody>
                </table>
            </div>
        </section>
        
        <div class="tooltip" id="tooltip"></div>
    </div>
'''
    
    data_export = {
        'table': table[:100],
        'summary': summary,
        'clock_analysis': {
            'unified': clock_analysis.get('unified'),
            'root_cause_candidate': clock_analysis.get('root_cause_candidate')
        }
    }
    
    html += get_javascript(data_export)
    
    html += '''
</body>
</html>'''
    
    return html


def generate_json_export(table: List[Dict], summary: Dict, clock_analysis: Dict) -> Dict[str, Any]:
    """Generate JSON export of alignment data."""
    return {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'tool': 'media_alignment.py'
        },
        'summary': summary,
        'clock_analysis': clock_analysis,
        'word_count': len(table),
        'words': table
    }


def run_media_alignment(root: Path) -> Dict[str, Any]:
    """Main entry point - generate media alignment visualization."""
    
    output_dir = root / 'data' / 'output' / 'verification' / 'media_alignment'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    project_path = root / 'data' / 'project.json'
    if not project_path.exists():
        return {'success': False, 'error': 'project.json not found'}
    
    project = load_json(project_path)
    
    print("Computing timeline clips...")
    timeline_clips = compute_timeline_clips(project)
    
    print("Building caption events...")
    caption_events = build_caption_events(project, timeline_clips)
    
    print("Building word alignment table...")
    table = build_word_alignment_table(project, timeline_clips, caption_events)
    
    print("Computing alignment summary...")
    summary = compute_alignment_summary(table, project, timeline_clips)
    
    print("Analyzing clock unification...")
    clock_analysis = analyze_clock_unification(project, timeline_clips)
    
    print("Generating HTML report...")
    html = generate_html_report(table, summary, clock_analysis, caption_events, timeline_clips, project)
    html_path = output_dir / 'media_alignment_report.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Generating JSON export...")
    json_data = generate_json_export(table, summary, clock_analysis)
    json_path = output_dir / 'media_alignment_data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    
    return {
        'success': True,
        'output_dir': str(output_dir),
        'html_path': str(html_path),
        'json_path': str(json_path),
        'summary': summary,
        'clock_analysis': clock_analysis,
        'word_count': len(table)
    }


def print_alignment_summary(result: Dict[str, Any]) -> None:
    """Print summary to terminal."""
    print("\n" + "=" * 70)
    print("MEDIA ALIGNMENT REPORT")
    print("=" * 70)
    
    print(f"\nOutput directory: {result['output_dir']}")
    print(f"HTML report: {result['html_path']}")
    
    summary = result.get('summary', {})
    clock = result.get('clock_analysis', {})
    
    print(f"\nWord Count: {result.get('word_count', 0)}")
    
    print("\nDuration Comparison:")
    print(f"  Raw video duration:     {summary.get('raw_video_duration', 0):.2f}s")
    print(f"  Playable segments sum:  {summary.get('playable_duration', 0):.2f}s")
    print(f"  Caption output:         {summary.get('caption_output_duration', 0):.2f}s")
    print(f"  Duration mismatch:      {clock.get('duration_mismatch', 0):.2f}s")
    
    print("\nDrift Metrics:")
    print(f"  Mean caption-audio:     {summary.get('mean_caption_audio_drift_ms', 0):.0f}ms")
    print(f"  Max caption-audio:      {summary.get('max_caption_audio_drift_ms', 0):.0f}ms")
    print(f"  Mean caption-video:     {summary.get('mean_caption_video_drift_ms', 0):.0f}ms")
    print(f"  Audio-video drift:      0ms (same clock)")
    
    print("\nClock Unification:")
    unified = clock.get('unified', False)
    if unified:
        print(f"  Status: UNIFIED")
        print(f"  Mechanism: {clock.get('mechanism', 'Unknown')}")
    else:
        print(f"  Status: NOT UNIFIED")
        print(f"  Root cause: {clock.get('root_cause_candidate', 'Unknown')[:100]}...")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate media alignment visualization')
    parser.add_argument('--project', '-p', type=str, help='Path to project root')
    args = parser.parse_args()
    
    root = Path(args.project) if args.project else get_project_root()
    
    result = run_media_alignment(root)
    print_alignment_summary(result)
