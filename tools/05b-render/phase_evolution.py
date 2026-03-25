#!/usr/bin/env python3
"""
Phase Evolution Visualization

Generate visual diff-based evolution report showing how transcript text
and timing transform across each editorial stage prior to render output.

Phases:
  Phase 0 - Raw transcription (Tool 01)
  Phase 1 - Reviewed transcription (Tool 02)  
  Phase 2 - Take selection (Tool 03)
  Phase 3 - Assembly timing (Tool 04)
  Phase 4 - Render styling layer (Tool 05)
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def load_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# === Data Loading ===

def load_raw_transcript(root: Path) -> Dict[str, Any]:
    """Load Phase 0 - Raw transcription from combined transcript."""
    raw_path = root / 'data' / 'transcript_combined.json'
    if not raw_path.exists():
        return {'segments': [], 'duration': 0, 'error': 'Raw transcript not found'}
    
    raw = load_json(raw_path)
    return {
        'source': str(raw_path),
        'segments': raw.get('segments', []),
        'duration': raw.get('duration', 0),
        'sources': raw.get('sources', [])
    }


def load_reviewed_transcript(project: Dict) -> Dict[str, Any]:
    """Load Phase 1 - Reviewed transcription from project."""
    transcript = project.get('transcript', {})
    return {
        'segments': transcript.get('segments', []),
        'duration': transcript.get('duration', 0)
    }


def load_take_selection(project: Dict) -> List[Dict[str, Any]]:
    """Load Phase 2 - Take selection from project clips."""
    clips = project.get('clips', [])
    
    selected = []
    for clip in clips:
        if not clip.get('enabled', True) or not clip.get('in_timeline', True):
            continue
        
        sel = clip.get('selected_segment', {})
        if not sel:
            continue
        
        selected.append({
            'clip_id': clip.get('id', ''),
            'clip_name': clip.get('name', ''),
            'timeline_position': clip.get('timeline_position', 0),
            'segment_index': sel.get('segment_index'),
            'start': sel.get('start', 0),
            'end': sel.get('end', 0),
            'text': sel.get('text', ''),
            'original_video_id': sel.get('original_video_id', '')
        })
    
    return sorted(selected, key=lambda x: x['timeline_position'])


def load_assembly_data(project: Dict) -> Dict[str, Any]:
    """Load Phase 3 - Assembly timing with trim and deleted regions."""
    clips = project.get('clips', [])
    
    assembly_clips = []
    for clip in clips:
        if not clip.get('enabled', True) or not clip.get('in_timeline', True):
            continue
        
        sel = clip.get('selected_segment', {})
        if not sel:
            continue
        
        trim_start = clip.get('trim_start', sel.get('start', 0))
        trim_end = clip.get('trim_end', sel.get('end', 0))
        deleted_regions = clip.get('deleted_regions', [])
        
        playable_segments = compute_playable_segments(trim_start, trim_end, deleted_regions)
        
        assembly_clips.append({
            'clip_id': clip.get('id', ''),
            'clip_name': clip.get('name', ''),
            'timeline_position': clip.get('timeline_position', 0),
            'segment_index': sel.get('segment_index'),
            'trim_start': trim_start,
            'trim_end': trim_end,
            'deleted_regions': deleted_regions,
            'playable_segments': playable_segments,
            'original_video_id': sel.get('original_video_id', '')
        })
    
    return {
        'clips': sorted(assembly_clips, key=lambda x: x['timeline_position'])
    }


def compute_playable_segments(trim_start: float, trim_end: float, 
                              deleted_regions: List[Dict]) -> List[Tuple[float, float]]:
    """Compute playable segments by subtracting deleted regions from trim range."""
    segments = [(trim_start, trim_end)]
    
    for del_region in sorted(deleted_regions, key=lambda r: r['start']):
        new_segments = []
        del_start = del_region['start']
        del_end = del_region['end']
        
        for seg_start, seg_end in segments:
            if del_end <= seg_start or del_start >= seg_end:
                new_segments.append((seg_start, seg_end))
            elif del_start <= seg_start and del_end >= seg_end:
                pass
            else:
                if del_start > seg_start:
                    new_segments.append((seg_start, del_start))
                if del_end < seg_end:
                    new_segments.append((del_end, seg_end))
        
        segments = new_segments
    
    return segments


def load_waveform_data(root: Path) -> Dict[str, Any]:
    """Load waveform peaks for Phase 3 visualization."""
    waveform_path = root / 'data' / 'waveforms.json'
    if not waveform_path.exists():
        return {'peaks': [], 'duration': 0, 'error': 'Waveform data not found'}
    
    wf = load_json(waveform_path)
    return {
        'peaks': wf.get('peaks', []),
        'duration': wf.get('duration', 0),
        'peaks_per_second': wf.get('peaks_per_second', 100)
    }


def load_styling_data(project: Dict) -> Dict[str, Any]:
    """Load Phase 4 - Styling metadata."""
    return {
        'word_colors': project.get('word_colors', {}),
        'caption_style': project.get('caption_style', {}),
        'caption_breaks': project.get('caption_breaks', {})
    }


# === Word Survival Computation ===

def compute_word_survival(project: Dict) -> Dict[str, Any]:
    """
    Compute word counts at each pipeline stage using the same logic as render.
    
    Returns accurate word counts after each tool's filtering:
    - Phase 0: Raw transcript words
    - Phase 1: Reviewed transcript words
    - Phase 2: Words in selected segments only
    - Phase 3: Words in playable segments after deletions
    - Phase 4: Styled words from Phase 3 survivors
    """
    from segments import compute_timeline_clips
    from captions import build_caption_events
    
    transcript = project.get('transcript', {})
    segments = transcript.get('segments', [])
    
    # Phase 0: Raw transcript words (same as Phase 1 for combined transcript)
    phase_1_count = sum(len(seg.get('words', [])) for seg in segments)
    
    # Phase 2: Words in selected segments only
    clips = project.get('clips', [])
    selected_indices = set()
    for clip in clips:
        if clip.get('enabled', True) and clip.get('in_timeline', True):
            sel = clip.get('selected_segment', {})
            seg_idx = sel.get('segment_index')
            if seg_idx is not None:
                selected_indices.add(seg_idx)
    
    phase_2_count = 0
    for i, seg in enumerate(segments):
        if i in selected_indices:
            phase_2_count += len(seg.get('words', []))
    
    # Phase 3: Words surviving after deletions (using render pipeline logic)
    timeline_clips = compute_timeline_clips(project)
    caption_events = build_caption_events(project, timeline_clips)
    phase_3_count = sum(len(event.get('words', [])) for event in caption_events)
    
    # Phase 4: Styled words that exist in Phase 3 survivors
    word_colors = project.get('word_colors', {})
    
    # Build set of surviving word keys from caption_events
    surviving_keys = set()
    for event in caption_events:
        seg_idx = event.get('segment_index', -1)
        for word in event.get('words', []):
            word_idx = word.get('word_index', -1)
            if seg_idx >= 0 and word_idx >= 0:
                surviving_keys.add(f"{seg_idx}_{word_idx}")
    
    # Count styled words that are in survivors
    phase_4_styled = sum(1 for key in word_colors.keys() if key in surviving_keys)
    
    return {
        'phase_0': phase_1_count,  # Raw = reviewed for combined transcript
        'phase_1': phase_1_count,
        'phase_2': phase_2_count,
        'phase_3': phase_3_count,
        'phase_4_styled': phase_4_styled,
        'loss_phase_01': 0,  # No loss between raw and reviewed
        'loss_phase_12': phase_1_count - phase_2_count,
        'loss_phase_23': phase_2_count - phase_3_count,
        'total_loss': phase_1_count - phase_3_count,
        'surviving_keys': surviving_keys
    }


# === Diff Computation ===

def compute_phase01_diff(raw: Dict, reviewed: Dict) -> Dict[str, Any]:
    """Compute diff between Phase 0 (raw) and Phase 1 (reviewed)."""
    raw_segments = raw.get('segments', [])
    reviewed_segments = reviewed.get('segments', [])
    
    raw_words = extract_all_words(raw_segments)
    reviewed_words = extract_all_words(reviewed_segments)
    
    raw_texts = [w['text'].lower().strip('.,!?;:') for w in raw_words]
    reviewed_texts = [w['text'].lower().strip('.,!?;:') for w in reviewed_words]
    
    raw_set = set(raw_texts)
    reviewed_set = set(reviewed_texts)
    
    added_words = reviewed_set - raw_set
    deleted_words = raw_set - reviewed_set
    
    timing_modified = []
    for i in range(min(len(raw_words), len(reviewed_words))):
        rw = raw_words[i]
        pw = reviewed_words[i]
        
        start_shift = pw['start'] - rw['start']
        end_shift = pw['end'] - rw['end']
        
        if abs(start_shift) > 0.001 or abs(end_shift) > 0.001:
            timing_modified.append({
                'word_index': i,
                'text': pw['text'],
                'raw_start': rw['start'],
                'raw_end': rw['end'],
                'reviewed_start': pw['start'],
                'reviewed_end': pw['end'],
                'start_shift_ms': start_shift * 1000,
                'end_shift_ms': end_shift * 1000
            })
    
    return {
        'total_raw_words': len(raw_words),
        'total_reviewed_words': len(reviewed_words),
        'words_added': len(added_words),
        'words_deleted': len(deleted_words),
        'added_samples': list(added_words)[:20],
        'deleted_samples': list(deleted_words)[:20],
        'timing_modified_count': len(timing_modified),
        'timing_modified': timing_modified[:50]
    }


def extract_all_words(segments: List[Dict]) -> List[Dict]:
    """Extract all words from segments with timing."""
    words = []
    for seg in segments:
        for w in seg.get('words', []):
            words.append({
                'text': w.get('text', ''),
                'start': w.get('start', 0),
                'end': w.get('end', 0),
                'segment_index': seg.get('id', seg.get('original_id', -1))
            })
    return words


def compute_phase12_selection(reviewed: Dict, clips: List[Dict], word_survival: Dict) -> Dict[str, Any]:
    """Compute Phase 1 to Phase 2 - segment selection changes."""
    segments = reviewed.get('segments', [])
    total_segments = len(segments)
    
    selected_indices = set()
    for clip in clips:
        seg_idx = clip.get('segment_index')
        if seg_idx is not None:
            selected_indices.add(seg_idx)
    
    excluded_indices = set(range(total_segments)) - selected_indices
    
    # Count words in excluded segments for reporting
    excluded_word_count = 0
    for i in excluded_indices:
        if i < len(segments):
            excluded_word_count += len(segments[i].get('words', []))
    
    return {
        'total_segments': total_segments,
        'segments_included': len(selected_indices),
        'segments_excluded': len(excluded_indices),
        'included_indices': sorted(selected_indices),
        'excluded_indices': sorted(excluded_indices),
        'phase_2_word_count': word_survival.get('phase_2', 0),
        'words_lost_from_phase_1': word_survival.get('loss_phase_12', 0)
    }


def compute_phase23_timing(reviewed: Dict, assembly: Dict, word_survival: Dict) -> Dict[str, Any]:
    """Compute Phase 2 to Phase 3 - timing shifts from assembly edits."""
    clips = assembly.get('clips', [])
    
    all_shifts = []
    for clip in clips:
        deleted = clip.get('deleted_regions', [])
        if deleted:
            for region in deleted:
                all_shifts.append({
                    'clip_id': clip['clip_id'],
                    'type': 'deleted_region',
                    'start': region['start'],
                    'end': region['end'],
                    'duration': region['end'] - region['start']
                })
    
    total_deleted_duration = sum(s['duration'] for s in all_shifts if s['type'] == 'deleted_region')
    
    clips_with_trim = sum(1 for c in clips if c.get('trim_start') is not None or c.get('trim_end') is not None)
    clips_with_deletions = sum(1 for c in clips if c.get('deleted_regions'))
    total_deleted_regions = sum(len(c.get('deleted_regions', [])) for c in clips)
    
    return {
        'clips_with_trim': clips_with_trim,
        'clips_with_deletions': clips_with_deletions,
        'total_deleted_regions': total_deleted_regions,
        'total_deleted_duration': total_deleted_duration,
        'shifts': all_shifts[:100],
        'phase_3_word_count': word_survival.get('phase_3', 0),
        'words_lost_from_phase_2': word_survival.get('loss_phase_23', 0)
    }


def compute_phase34_styling(project: Dict, word_survival: Dict) -> Dict[str, Any]:
    """Compute Phase 3 to Phase 4 - styling application with validation."""
    word_colors = project.get('word_colors', {})
    caption_breaks = project.get('caption_breaks', {})
    caption_style = project.get('caption_style', {})
    
    total_breaks = sum(len(breaks) for breaks in caption_breaks.values())
    segments_with_breaks = len(caption_breaks)
    
    # Get counts from word_survival
    phase_3_count = word_survival.get('phase_3', 0)
    surviving_keys = word_survival.get('surviving_keys', set())
    
    # Count styled words that are in survivors
    surviving_styled_count = sum(1 for key in word_colors.keys() if key in surviving_keys)
    
    # Check for mismatch
    total_styled_in_project = len(word_colors)
    mismatch_warning = None
    
    if surviving_styled_count != phase_3_count:
        mismatch_warning = (
            f"STYLED WORD COUNT MISMATCH: {surviving_styled_count} styled words "
            f"vs {phase_3_count} surviving words. "
            f"Total styled entries in project: {total_styled_in_project}"
        )
    
    return {
        'styled_word_count': total_styled_in_project,
        'surviving_styled_count': surviving_styled_count,
        'phase_3_surviving_count': phase_3_count,
        'caption_break_count': total_breaks,
        'segments_with_breaks': segments_with_breaks,
        'caption_style': caption_style,
        'word_colors_sample': dict(list(word_colors.items())[:20]),
        'mismatch_warning': mismatch_warning
    }


# === Unified Timeline ===

def build_unified_timeline(raw: Dict, reviewed: Dict, selection: List, 
                           assembly: Dict, styling: Dict, 
                           waveform: Dict, diffs: Dict) -> Dict[str, Any]:
    """Build unified timeline data for visualization."""
    
    max_duration = max(
        raw.get('duration', 0),
        reviewed.get('duration', 0),
        waveform.get('duration', 0)
    )
    
    phase0_words = build_phase_words(raw.get('segments', []), 0)
    phase1_words = build_phase_words(reviewed.get('segments', []), 1)
    
    timing_modified_set = set()
    for tm in diffs['phase01'].get('timing_modified', []):
        timing_modified_set.add(tm['word_index'])
    
    for i, w in enumerate(phase1_words):
        if i in timing_modified_set:
            w['timing_modified'] = True
    
    phase2_segments = build_phase2_segments(reviewed.get('segments', []), 
                                            diffs['phase12']['included_indices'])
    
    phase3_regions = build_phase3_regions(assembly.get('clips', []))
    
    phase4_styling = build_phase4_styling(reviewed.get('segments', []), styling)
    
    return {
        'duration': max_duration,
        'phase_0': {
            'name': 'Raw Transcription',
            'words': phase0_words
        },
        'phase_1': {
            'name': 'Reviewed Transcription',
            'words': phase1_words
        },
        'phase_2': {
            'name': 'Take Selection',
            'segments': phase2_segments
        },
        'phase_3': {
            'name': 'Assembly Timing',
            'regions': phase3_regions,
            'waveform': waveform.get('peaks', [])[:5000]
        },
        'phase_4': {
            'name': 'Render Styling',
            'styling': phase4_styling
        }
    }


def build_phase_words(segments: List[Dict], phase: int) -> List[Dict]:
    """Build word list for a phase."""
    words = []
    global_idx = 0
    
    for seg_idx, seg in enumerate(segments):
        for w in seg.get('words', []):
            words.append({
                'global_index': global_idx,
                'segment_index': seg_idx,
                'text': w.get('text', ''),
                'start': w.get('start', 0),
                'end': w.get('end', 0),
                'phase': phase
            })
            global_idx += 1
    
    return words


def build_phase2_segments(segments: List[Dict], included_indices: set) -> List[Dict]:
    """Build segment data for Phase 2 visualization."""
    result = []
    for i, seg in enumerate(segments):
        result.append({
            'segment_index': i,
            'text': seg.get('text', '')[:50],
            'start': seg.get('start', 0),
            'end': seg.get('end', 0),
            'included': i in included_indices,
            'word_count': len(seg.get('words', []))
        })
    return result


def build_phase3_regions(clips: List[Dict]) -> List[Dict]:
    """Build timing regions for Phase 3 visualization."""
    regions = []
    for clip in clips:
        regions.append({
            'clip_id': clip['clip_id'],
            'clip_name': clip['clip_name'],
            'timeline_position': clip['timeline_position'],
            'playable_segments': clip['playable_segments'],
            'deleted_regions': clip['deleted_regions']
        })
    return regions


def build_phase4_styling(segments: List[Dict], styling: Dict) -> List[Dict]:
    """Build styling data for Phase 4 visualization."""
    word_colors = styling.get('word_colors', {})
    caption_breaks = styling.get('caption_breaks', {})
    
    result = []
    for seg_idx, seg in enumerate(segments):
        seg_breaks = caption_breaks.get(str(seg_idx), [])
        
        for word_idx, w in enumerate(seg.get('words', [])):
            key = f"{seg_idx}_{word_idx}"
            color = word_colors.get(key)
            
            is_break = word_idx in seg_breaks
            
            result.append({
                'segment_index': seg_idx,
                'word_index': word_idx,
                'text': w.get('text', ''),
                'start': w.get('start', 0),
                'end': w.get('end', 0),
                'color': color,
                'is_caption_break': is_break
            })
    
    return result


# === HTML Generation ===

def generate_html_report(unified: Dict, diffs: Dict) -> str:
    """Generate interactive HTML visualization."""
    
    css = get_css()
    js = get_javascript()
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phase Evolution Report</title>
    {css}
</head>
<body>
    <div class="container">
        <header>
            <h1>Phase Evolution Report</h1>
            <p class="meta">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </header>
        
        <section class="summary">
            <h2>Summary Metrics</h2>
            <div class="metrics-grid">
                {generate_metrics_html(diffs)}
            </div>
        </section>
        
        <section class="controls">
            <h2>Timeline Controls</h2>
            <div class="control-row">
                <label>Zoom: <input type="range" id="zoomSlider" min="1" max="10" value="1" step="0.5"></label>
                <span id="zoomValue">1x</span>
            </div>
            <div class="control-row toggles">
                <label><input type="checkbox" id="toggle0" checked> Phase 0: Raw</label>
                <label><input type="checkbox" id="toggle1" checked> Phase 1: Reviewed</label>
                <label><input type="checkbox" id="toggle2" checked> Phase 2: Selection</label>
                <label><input type="checkbox" id="toggle3" checked> Phase 3: Assembly</label>
                <label><input type="checkbox" id="toggle4" checked> Phase 4: Styling</label>
            </div>
        </section>
        
        <section class="timeline-section">
            <h2>Unified Timeline</h2>
            <div class="timeline-container" id="timelineContainer">
                <div class="time-ruler" id="timeRuler"></div>
                {generate_timeline_html(unified)}
            </div>
        </section>
        
        <section class="diff-section">
            <h2>Phase Differences</h2>
            {generate_diff_html(diffs, unified)}
        </section>
        
        <div class="tooltip" id="tooltip"></div>
    </div>
    
    <script>
        const unifiedData = {json.dumps(unified)};
        const diffsData = {json.dumps(diffs)};
    </script>
    {js}
</body>
</html>'''
    
    return html


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
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            margin-bottom: 30px;
            border-bottom: 2px solid #4cc9f0;
            padding-bottom: 15px;
        }
        
        h1 { color: #4cc9f0; margin-bottom: 5px; }
        h2 { color: #4cc9f0; margin: 20px 0 15px 0; font-size: 18px; }
        .meta { color: #888; font-size: 13px; }
        
        .summary {
            background: #16213e;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
        }
        
        .metric-card {
            background: #1a1a2e;
            border-radius: 6px;
            padding: 15px;
            text-align: center;
        }
        
        .metric-card h3 {
            font-size: 11px;
            text-transform: uppercase;
            color: #888;
            margin-bottom: 8px;
        }
        
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            color: #4cc9f0;
        }
        
        .metric-card.added .metric-value { color: #48bb78; }
        .metric-card.deleted .metric-value { color: #f56565; }
        .metric-card.modified .metric-value { color: #ecc94b; }
        .metric-card.styled .metric-value { color: #cb697f; }
        
        .controls {
            background: #16213e;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .control-row {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
        }
        
        .control-row:last-child { margin-bottom: 0; }
        
        .toggles label {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            margin-right: 20px;
            cursor: pointer;
        }
        
        input[type="range"] {
            width: 200px;
            cursor: pointer;
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
            min-height: 400px;
        }
        
        .time-ruler {
            height: 30px;
            background: #0f0f1a;
            border-radius: 4px;
            margin-bottom: 10px;
            position: relative;
        }
        
        .time-mark {
            position: absolute;
            bottom: 0;
            font-size: 10px;
            color: #888;
            transform: translateX(-50%);
        }
        
        .phase-layer {
            height: 60px;
            background: #0f0f1a;
            border-radius: 4px;
            margin-bottom: 8px;
            position: relative;
            overflow: hidden;
        }
        
        .phase-label {
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 11px;
            color: #888;
            z-index: 10;
            background: rgba(15, 15, 26, 0.8);
            padding: 2px 6px;
            border-radius: 3px;
        }
        
        .word-block {
            position: absolute;
            height: 40px;
            top: 10px;
            background: #4cc9f0;
            border-radius: 3px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: #0f0f1a;
            overflow: hidden;
            cursor: pointer;
            transition: transform 0.1s, z-index 0.1s;
        }
        
        .word-block:hover {
            transform: scaleY(1.2);
            z-index: 100;
        }
        
        .word-block.added { background: #48bb78; }
        .word-block.deleted { background: #f56565; text-decoration: line-through; }
        .word-block.modified { background: #ecc94b; }
        
        .segment-block {
            position: absolute;
            height: 50px;
            top: 5px;
            border-radius: 3px;
            display: flex;
            align-items: center;
            padding: 0 8px;
            font-size: 10px;
            overflow: hidden;
        }
        
        .segment-block.included { background: rgba(72, 187, 120, 0.3); border: 1px solid #48bb78; }
        .segment-block.excluded { background: rgba(100, 100, 100, 0.3); border: 1px solid #666; }
        
        .deleted-region {
            position: absolute;
            height: 50px;
            top: 5px;
            background: rgba(245, 101, 101, 0.3);
            border: 1px dashed #f56565;
        }
        
        .waveform-canvas {
            height: 50px;
            width: 100%;
            background: #0f0f1a;
        }
        
        .styled-word {
            display: inline-block;
            padding: 2px 4px;
            margin: 1px;
            border-radius: 3px;
            font-size: 11px;
        }
        
        .caption-break {
            border-right: 2px solid #ecc94b;
            margin-right: 4px;
        }
        
        .diff-section {
            background: #16213e;
            border-radius: 8px;
            padding: 20px;
        }
        
        .diff-phase {
            margin-bottom: 30px;
        }
        
        .diff-phase h3 {
            color: #4cc9f0;
            margin-bottom: 10px;
            font-size: 14px;
        }
        
        .diff-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }
        
        .diff-table th, .diff-table td {
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #2a2a4a;
        }
        
        .diff-table th {
            background: #0f0f1a;
            color: #4cc9f0;
        }
        
        .diff-table tr:hover {
            background: rgba(76, 201, 240, 0.1);
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
            max-width: 300px;
        }
        
        .tooltip h4 {
            color: #4cc9f0;
            margin-bottom: 5px;
        }
        
        .tooltip p {
            margin: 3px 0;
            color: #ccc;
        }
        
        .color-swatch {
            display: inline-block;
            width: 14px;
            height: 14px;
            border-radius: 2px;
            margin-right: 4px;
            vertical-align: middle;
        }
    </style>'''


def get_javascript() -> str:
    return '''<script>
        const tooltip = document.getElementById('tooltip');
        const zoomSlider = document.getElementById('zoomSlider');
        const zoomValue = document.getElementById('zoomValue');
        const container = document.getElementById('timelineContainer');
        
        let currentZoom = 1;
        const baseWidth = 1000;
        
        zoomSlider.addEventListener('input', (e) => {
            currentZoom = parseFloat(e.target.value);
            zoomValue.textContent = currentZoom + 'x';
            updateTimelineWidth();
        });
        
        function updateTimelineWidth() {
            const width = baseWidth * currentZoom;
            container.style.width = width + 'px';
            
            document.querySelectorAll('.phase-layer').forEach(layer => {
                layer.style.width = width + 'px';
            });
            
            document.querySelector('.time-ruler').style.width = width + 'px';
            
            updateTimeRuler();
        }
        
        function updateTimeRuler() {
            const ruler = document.getElementById('timeRuler');
            const duration = unifiedData.duration;
            const width = baseWidth * currentZoom;
            
            ruler.innerHTML = '';
            
            const step = duration > 100 ? 20 : 10;
            for (let t = 0; t <= duration; t += step) {
                const mark = document.createElement('div');
                mark.className = 'time-mark';
                mark.style.left = (t / duration * 100) + '%';
                mark.textContent = t.toFixed(0) + 's';
                ruler.appendChild(mark);
            }
        }
        
        document.querySelectorAll('[id^="toggle"]').forEach(toggle => {
            toggle.addEventListener('change', (e) => {
                const phaseNum = e.target.id.replace('toggle', '');
                const layer = document.querySelector('.phase-layer[data-phase="' + phaseNum + '"]');
                if (layer) {
                    layer.style.display = e.target.checked ? 'block' : 'none';
                }
            });
        });
        
        document.querySelectorAll('.word-block').forEach(block => {
            block.addEventListener('mouseenter', (e) => {
                const idx = parseInt(block.dataset.index);
                const word = unifiedData.phase_0?.words?.[idx] || unifiedData.phase_1?.words?.[idx];
                
                if (word) {
                    tooltip.innerHTML = `
                        <h4>"${word.text}"</h4>
                        <p>Segment: ${word.segment_index}</p>
                        <p>Start: ${word.start.toFixed(3)}s</p>
                        <p>End: ${word.end.toFixed(3)}s</p>
                        <p>Duration: ${((word.end - word.start) * 1000).toFixed(1)}ms</p>
                    `;
                    tooltip.style.display = 'block';
                }
            });
            
            block.addEventListener('mousemove', (e) => {
                tooltip.style.left = (e.clientX + 15) + 'px';
                tooltip.style.top = (e.clientY + 15) + 'px';
            });
            
            block.addEventListener('mouseleave', () => {
                tooltip.style.display = 'none';
            });
        });
        
        updateTimelineWidth();
    </script>'''


def generate_metrics_html(diffs: Dict) -> str:
    """Generate metrics summary HTML."""
    p01 = diffs.get('phase01', {})
    p12 = diffs.get('phase12', {})
    p23 = diffs.get('phase23', {})
    p34 = diffs.get('phase34', {})
    ws = diffs.get('word_survival', {})
    
    timing_shifts = p01.get('timing_modified', [])
    mean_shift = 0
    max_shift = 0
    if timing_shifts:
        shifts = [abs(t['start_shift_ms']) + abs(t['end_shift_ms']) for t in timing_shifts]
        mean_shift = sum(shifts) / len(shifts)
        max_shift = max(shifts)
    
    # Generate warning banner if mismatch
    warning_html = ''
    if p34.get('mismatch_warning'):
        warning_html = f'''
        <div class="warning-banner" style="background:#f56565;color:white;padding:15px;border-radius:6px;margin-bottom:20px;">
            <strong>WARNING:</strong> {p34['mismatch_warning']}
        </div>
        '''
    
    return f'''
        {warning_html}
        
        <div class="survival-section" style="background:#0f0f1a;padding:15px;border-radius:6px;margin-bottom:15px;">
            <h3 style="color:#4cc9f0;margin-bottom:10px;font-size:14px;">Word Survival Summary</h3>
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:13px;">
                <span style="background:#16213e;padding:8px 12px;border-radius:4px;">
                    <strong>Phase 0:</strong> {ws.get('phase_0', 0)}
                </span>
                <span style="color:#888;">→</span>
                <span style="background:#16213e;padding:8px 12px;border-radius:4px;">
                    <strong>Phase 1:</strong> {ws.get('phase_1', 0)}
                    <span style="color:#888;font-size:11px;">({ws.get('loss_phase_01', 0)} lost)</span>
                </span>
                <span style="color:#888;">→</span>
                <span style="background:#16213e;padding:8px 12px;border-radius:4px;">
                    <strong>Phase 2:</strong> {ws.get('phase_2', 0)}
                    <span style="color:#f56565;font-size:11px;">(-{ws.get('loss_phase_12', 0)})</span>
                </span>
                <span style="color:#888;">→</span>
                <span style="background:#16213e;padding:8px 12px;border-radius:4px;">
                    <strong>Phase 3:</strong> {ws.get('phase_3', 0)}
                    <span style="color:#f56565;font-size:11px;">(-{ws.get('loss_phase_23', 0)})</span>
                </span>
                <span style="color:#888;">→</span>
                <span style="background:#cb697f;color:#0f0f1a;padding:8px 12px;border-radius:4px;">
                    <strong>Final:</strong> {ws.get('phase_3', 0)} rendered
                </span>
            </div>
            <p style="margin-top:10px;color:#888;font-size:12px;">
                Total attrition: <strong style="color:#f56565;">-{ws.get('total_loss', 0)} words</strong> 
                ({(ws.get('total_loss', 0) / max(1, ws.get('phase_0', 1)) * 100):.1f}% of original)
            </p>
        </div>
        
        <div class="metric-card">
            <h3>Raw Words (Phase 0)</h3>
            <div class="metric-value">{p01.get('total_raw_words', 0)}</div>
        </div>
        <div class="metric-card">
            <h3>Reviewed Words (Phase 1)</h3>
            <div class="metric-value">{p01.get('total_reviewed_words', 0)}</div>
        </div>
        <div class="metric-card">
            <h3>After Selection (Phase 2)</h3>
            <div class="metric-value">{ws.get('phase_2', 0)}</div>
        </div>
        <div class="metric-card">
            <h3>After Deletions (Phase 3)</h3>
            <div class="metric-value" style="color:#48bb78;">{ws.get('phase_3', 0)}</div>
        </div>
        <div class="metric-card deleted">
            <h3>Lost to Selection</h3>
            <div class="metric-value">-{ws.get('loss_phase_12', 0)}</div>
        </div>
        <div class="metric-card deleted">
            <h3>Lost to Deletions</h3>
            <div class="metric-value">-{ws.get('loss_phase_23', 0)}</div>
        </div>
        <div class="metric-card modified">
            <h3>Timing Modified</h3>
            <div class="metric-value">{p01.get('timing_modified_count', 0)}</div>
        </div>
        <div class="metric-card">
            <h3>Mean Timing Shift</h3>
            <div class="metric-value">{mean_shift:.1f}ms</div>
        </div>
        <div class="metric-card">
            <h3>Max Timing Shift</h3>
            <div class="metric-value">{max_shift:.1f}ms</div>
        </div>
        <div class="metric-card styled">
            <h3>Styled Words</h3>
            <div class="metric-value">{p34.get('surviving_styled_count', p34.get('styled_word_count', 0))}</div>
        </div>
        <div class="metric-card styled">
            <h3>Caption Breaks</h3>
            <div class="metric-value">{p34.get('caption_break_count', 0)}</div>
        </div>
    '''


def generate_timeline_html(unified: Dict) -> str:
    """Generate timeline layers HTML."""
    duration = unified.get('duration', 100)
    
    layers = []
    
    layers.append(generate_phase0_layer(unified.get('phase_0', {}), duration))
    layers.append(generate_phase1_layer(unified.get('phase_1', {}), duration))
    layers.append(generate_phase2_layer(unified.get('phase_2', {}), duration))
    layers.append(generate_phase3_layer(unified.get('phase_3', {}), duration))
    layers.append(generate_phase4_layer(unified.get('phase_4', {}), duration))
    
    return '\n'.join(layers)


def generate_phase0_layer(phase: Dict, duration: float) -> str:
    """Generate Phase 0 timeline layer."""
    words = phase.get('words', [])
    
    word_blocks = []
    for w in words[:500]:
        left = (w['start'] / duration) * 100
        width = ((w['end'] - w['start']) / duration) * 100
        
        word_blocks.append(
            f'<div class="word-block" style="left:{left:.3f}%;width:{width:.3f}%" '
            f'data-index="{w["global_index"]}" title="{w["text"]}">@</div>'
        )
    
    return f'''
        <div class="phase-layer" data-phase="0">
            <span class="phase-label">Phase 0: Raw</span>
            {"".join(word_blocks)}
        </div>
    '''


def generate_phase1_layer(phase: Dict, duration: float) -> str:
    """Generate Phase 1 timeline layer with diff highlighting."""
    words = phase.get('words', [])
    
    word_blocks = []
    for w in words[:500]:
        left = (w['start'] / duration) * 100
        width = ((w['end'] - w['start']) / duration) * 100
        
        css_class = 'word-block'
        if w.get('timing_modified'):
            css_class += ' modified'
        
        word_blocks.append(
            f'<div class="{css_class}" style="left:{left:.3f}%;width:{width:.3f}%" '
            f'data-index="{w["global_index"]}" title="{w["text"]}">@</div>'
        )
    
    return f'''
        <div class="phase-layer" data-phase="1">
            <span class="phase-label">Phase 1: Reviewed</span>
            {"".join(word_blocks)}
        </div>
    '''


def generate_phase2_layer(phase: Dict, duration: float) -> str:
    """Generate Phase 2 timeline layer with selection indicators."""
    segments = phase.get('segments', [])
    
    seg_blocks = []
    for s in segments:
        left = (s['start'] / duration) * 100
        width = ((s['end'] - s['start']) / duration) * 100
        
        css_class = 'segment-block included' if s['included'] else 'segment-block excluded'
        
        seg_blocks.append(
            f'<div class="{css_class}" style="left:{left:.3f}%;width:{width:.3f}%">'
            f'{s["segment_index"]}</div>'
        )
    
    return f'''
        <div class="phase-layer" data-phase="2">
            <span class="phase-label">Phase 2: Selection</span>
            {"".join(seg_blocks)}
        </div>
    '''


def generate_phase3_layer(phase: Dict, duration: float) -> str:
    """Generate Phase 3 timeline layer with deleted regions."""
    regions = phase.get('regions', [])
    
    deleted_blocks = []
    for r in regions:
        for dr in r.get('deleted_regions', []):
            left = (dr['start'] / duration) * 100
            width = ((dr['end'] - dr['start']) / duration) * 100
            
            deleted_blocks.append(
                f'<div class="deleted-region" style="left:{left:.3f}%;width:{width:.3f}%"></div>'
            )
    
    return f'''
        <div class="phase-layer" data-phase="3">
            <span class="phase-label">Phase 3: Assembly</span>
            {"".join(deleted_blocks[:200])}
        </div>
    '''


def generate_phase4_layer(phase: Dict, duration: float) -> str:
    """Generate Phase 4 timeline layer with styling indicators."""
    styling = phase.get('styling', [])
    
    styled_blocks = []
    for s in styling[:300]:
        if s.get('color') or s.get('is_caption_break'):
            left = (s['start'] / duration) * 100
            width = max(0.3, ((s['end'] - s['start']) / duration) * 100)
            
            bg_color = s['color'] if s.get('color') else '#888'
            extra_class = ' caption-break' if s.get('is_caption_break') else ''
            
            styled_blocks.append(
                f'<div class="word-block{extra_class}" style="left:{left:.3f}%;width:{width:.3f}%;'
                f'background:{bg_color}" title="{s["text"]}">@</div>'
            )
    
    if not styled_blocks:
        styled_blocks = ['<div class="phase-label" style="left:50px">No custom styling</div>']
    
    return f'''
        <div class="phase-layer" data-phase="4">
            <span class="phase-label">Phase 4: Styling</span>
            {"".join(styled_blocks)}
        </div>
    '''


def generate_diff_html(diffs: Dict, unified: Dict) -> str:
    """Generate detailed diff section HTML."""
    
    p01 = diffs.get('phase01', {})
    p12 = diffs.get('phase12', {})
    p23 = diffs.get('phase23', {})
    p34 = diffs.get('phase34', {})
    ws = diffs.get('word_survival', {})
    
    timing_rows = []
    for tm in p01.get('timing_modified', [])[:20]:
        timing_rows.append(f'''
            <tr>
                <td>{tm['word_index']}</td>
                <td>"{tm['text']}"</td>
                <td>{tm['raw_start']:.3f} - {tm['raw_end']:.3f}</td>
                <td>{tm['reviewed_start']:.3f} - {tm['reviewed_end']:.3f}</td>
                <td>{tm['start_shift_ms']:.1f}ms</td>
                <td>{tm['end_shift_ms']:.1f}ms</td>
            </tr>
        ''')
    
    styling_rows = []
    for key, color in p34.get('word_colors_sample', {}).items():
        styling_rows.append(f'''
            <tr>
                <td>{key}</td>
                <td><span class="color-swatch" style="background:{color}"></span>{color}</td>
            </tr>
        ''')
    
    mismatch_alert = ''
    if p34.get('mismatch_warning'):
        mismatch_alert = f'''
        <div style="background:#f56565;color:white;padding:10px;border-radius:4px;margin-top:10px;">
            <strong>WARNING:</strong> {p34['mismatch_warning']}
        </div>
        '''
    
    return f'''
        <div class="diff-phase">
            <h3>Phase 0 → Phase 1: Text & Timing Changes</h3>
            <p>Words: {ws.get('phase_0', 0)} → {ws.get('phase_1', 0)} ({ws.get('loss_phase_01', 0)} lost)</p>
            <p>Text changes - Added: {p01.get('words_added', 0)} | Deleted: {p01.get('words_deleted', 0)} | Timing modified: {p01.get('timing_modified_count', 0)}</p>
            
            <h4 style="margin-top:15px;color:#ecc94b">Timing Modifications (first 20)</h4>
            <table class="diff-table">
                <tr><th>Index</th><th>Word</th><th>Raw Timing</th><th>Reviewed Timing</th><th>Start Shift</th><th>End Shift</th></tr>
                {"".join(timing_rows)}
            </table>
        </div>
        
        <div class="diff-phase">
            <h3>Phase 1 → Phase 2: Segment Selection (Tool 03)</h3>
            <p><strong>Word count: {ws.get('phase_1', 0)} → {ws.get('phase_2', 0)} (lost {ws.get('loss_phase_12', 0)} words)</strong></p>
            <p>Segments included: {p12.get('segments_included', 0)} | Segments excluded: {p12.get('segments_excluded', 0)}</p>
            <p>Excluded segment indices: {", ".join(map(str, p12.get('excluded_indices', [])[:20]))}</p>
        </div>
        
        <div class="diff-phase">
            <h3>Phase 2 → Phase 3: Assembly Timing (Tool 04)</h3>
            <p><strong>Word count: {ws.get('phase_2', 0)} → {ws.get('phase_3', 0)} (lost {ws.get('loss_phase_23', 0)} words)</strong></p>
            <p>Clips with trim: {p23.get('clips_with_trim', 0)} | Clips with deletions: {p23.get('clips_with_deletions', 0)} | Total deleted regions: {p23.get('total_deleted_regions', 0)}</p>
            <p>Total deleted duration: {p23.get('total_deleted_duration', 0):.2f}s</p>
        </div>
        
        <div class="diff-phase">
            <h3>Phase 3 → Phase 4: Styling Applied (Tool 05)</h3>
            <p><strong>Surviving words to render: {ws.get('phase_3', 0)} | Styled: {p34.get('surviving_styled_count', 0)}</strong></p>
            <p>Caption breaks: {p34.get('caption_break_count', 0)} | Segments with breaks: {p34.get('segments_with_breaks', 0)}</p>
            {mismatch_alert}
            
            <h4 style="margin-top:15px;color:#cb697f">Word Color Assignments</h4>
            <table class="diff-table">
                <tr><th>Word Key</th><th>Color</th></tr>
                {"".join(styling_rows)}
            </table>
        </div>
    '''


def generate_json_export(unified: Dict, diffs: Dict) -> Dict[str, Any]:
    """Generate JSON export of all phase data."""
    ws = diffs.get('word_survival', {})
    p34 = diffs.get('phase34', {})
    
    return {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'tool': 'phase_evolution.py'
        },
        'phases': {
            'phase_0_raw': {
                'word_count': ws.get('phase_0', 0),
                'words': unified.get('phase_0', {}).get('words', [])[:100]
            },
            'phase_1_reviewed': {
                'word_count': ws.get('phase_1', 0),
                'words': unified.get('phase_1', {}).get('words', [])[:100]
            },
            'phase_2_selection': {
                'word_count': ws.get('phase_2', 0),
                'segments': unified.get('phase_2', {}).get('segments', [])
            },
            'phase_3_assembly': {
                'word_count': ws.get('phase_3', 0),
                'regions': unified.get('phase_3', {}).get('regions', [])
            },
            'phase_4_styling': {
                'styled_count': p34.get('surviving_styled_count', 0),
                'styling': unified.get('phase_4', {}).get('styling', [])[:100]
            }
        },
        'diffs': diffs,
        'word_survival': ws,
        'summary': {
            'phase_0_words': ws.get('phase_0', 0),
            'phase_1_words': ws.get('phase_1', 0),
            'phase_2_words': ws.get('phase_2', 0),
            'phase_3_words': ws.get('phase_3', 0),
            'final_rendered_words': ws.get('phase_3', 0),
            'loss_phase_01': ws.get('loss_phase_01', 0),
            'loss_phase_12': ws.get('loss_phase_12', 0),
            'loss_phase_23': ws.get('loss_phase_23', 0),
            'total_loss': ws.get('total_loss', 0),
            'words_added': diffs.get('phase01', {}).get('words_added', 0),
            'words_deleted': diffs.get('phase01', {}).get('words_deleted', 0),
            'segments_excluded': diffs.get('phase12', {}).get('segments_excluded', 0),
            'timing_modified_count': diffs.get('phase01', {}).get('timing_modified_count', 0),
            'styled_word_count': p34.get('surviving_styled_count', 0),
            'caption_break_count': p34.get('caption_break_count', 0),
            'mismatch_warning': p34.get('mismatch_warning')
        }
    }


# === Main Entry Point ===

def run_phase_evolution(root: Path) -> Dict[str, Any]:
    """Main entry point - generate all phase evolution reports."""
    
    output_dir = root / 'data' / 'output' / 'verification' / 'phase_evolution'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    project_path = root / 'data' / 'project.json'
    if not project_path.exists():
        return {'success': False, 'error': 'project.json not found'}
    
    project = load_json(project_path)
    
    print("Loading Phase 0 - Raw transcription...")
    raw = load_raw_transcript(root)
    
    print("Loading Phase 1 - Reviewed transcription...")
    reviewed = load_reviewed_transcript(project)
    
    print("Loading Phase 2 - Take selection...")
    selection = load_take_selection(project)
    
    print("Loading Phase 3 - Assembly timing...")
    assembly = load_assembly_data(project)
    
    print("Loading waveform data...")
    waveform = load_waveform_data(root)
    
    print("Loading Phase 4 - Styling...")
    styling = load_styling_data(project)
    
    print("Computing word survival across phases...")
    word_survival = compute_word_survival(project)
    
    print("Computing diffs...")
    diffs = {
        'phase01': compute_phase01_diff(raw, reviewed),
        'phase12': compute_phase12_selection(reviewed, selection, word_survival),
        'phase23': compute_phase23_timing(reviewed, assembly, word_survival),
        'phase34': compute_phase34_styling(project, word_survival),
        'word_survival': {
            'phase_0': word_survival['phase_0'],
            'phase_1': word_survival['phase_1'],
            'phase_2': word_survival['phase_2'],
            'phase_3': word_survival['phase_3'],
            'phase_4_styled': word_survival['phase_4_styled'],
            'loss_phase_01': word_survival['loss_phase_01'],
            'loss_phase_12': word_survival['loss_phase_12'],
            'loss_phase_23': word_survival['loss_phase_23'],
            'total_loss': word_survival['total_loss']
        }
    }
    
    # Check for mismatch warning
    if diffs['phase34'].get('mismatch_warning'):
        print(f"WARNING: {diffs['phase34']['mismatch_warning']}")
    
    print("Building unified timeline...")
    unified = build_unified_timeline(raw, reviewed, selection, assembly, 
                                     styling, waveform, diffs)
    
    print("Generating HTML report...")
    html = generate_html_report(unified, diffs)
    html_path = output_dir / 'phase_evolution_report.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Generating JSON export...")
    json_data = generate_json_export(unified, diffs)
    json_path = output_dir / 'phase_evolution_data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    
    return {
        'success': True,
        'output_dir': str(output_dir),
        'html_path': str(html_path),
        'json_path': str(json_path),
        'summary': json_data['summary']
    }


def print_phase_summary(result: Dict[str, Any]) -> None:
    """Print summary to terminal."""
    print("\n" + "=" * 60)
    print("PHASE EVOLUTION REPORT")
    print("=" * 60)
    
    if not result.get('success'):
        print(f"\nERROR: {result.get('error', 'Unknown error')}")
        return
    
    print(f"\nOutput directory: {result['output_dir']}")
    print(f"HTML report: {result['html_path']}")
    print(f"JSON export: {result['json_path']}")
    
    summary = result.get('summary', {})
    
    print("\n" + "-" * 40)
    print("WORD SURVIVAL ACROSS PHASES:")
    print("-" * 40)
    print(f"  Phase 0 (Raw):           {summary.get('phase_0_words', 0)} words")
    print(f"  Phase 1 (Reviewed):      {summary.get('phase_1_words', 0)} words ({summary.get('loss_phase_01', 0)} lost)")
    print(f"  Phase 2 (Selection):     {summary.get('phase_2_words', 0)} words (-{summary.get('loss_phase_12', 0)})")
    print(f"  Phase 3 (Deletions):     {summary.get('phase_3_words', 0)} words (-{summary.get('loss_phase_23', 0)})")
    print(f"  Final Rendered:          {summary.get('final_rendered_words', 0)} words")
    print(f"\n  Total attrition:         -{summary.get('total_loss', 0)} words")
    
    print("\n" + "-" * 40)
    print("OTHER METRICS:")
    print("-" * 40)
    print(f"  Timing modified: {summary.get('timing_modified_count', 0)}")
    print(f"  Styled words: {summary.get('styled_word_count', 0)}")
    print(f"  Caption breaks: {summary.get('caption_break_count', 0)}")
    
    if summary.get('mismatch_warning'):
        print(f"\n  WARNING: {summary['mismatch_warning']}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate phase evolution visualization')
    parser.add_argument('--project', '-p', type=str, help='Path to project root')
    args = parser.parse_args()
    
    root = Path(args.project) if args.project else get_project_root()
    
    result = run_phase_evolution(root)
    print_phase_summary(result)
    
    sys.exit(0 if result['success'] else 1)
