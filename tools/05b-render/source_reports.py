#!/usr/bin/env python3
"""
Generate isolated authoritative source reports for verification debugging.

Produces HTML reports for each authoritative data source:
- Tool 02: Review text authority
- Tool 03: Clip selection authority  
- Tool 04: Assembly timing authority
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from segments import compute_timeline_clips
from captions import build_caption_events


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def load_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_css() -> str:
    """Shared CSS for all reports."""
    return """
    <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f5; }
    .container { max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
    h2 { color: #555; margin-top: 30px; }
    .meta { color: #666; font-size: 14px; margin-bottom: 20px; }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }
    .stat { background: #e9ecef; padding: 15px; border-radius: 4px; text-align: center; }
    .stat-value { font-size: 24px; font-weight: bold; color: #333; }
    .stat-label { font-size: 11px; color: #666; text-transform: uppercase; margin-top: 5px; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }
    th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }
    th { background: #4CAF50; color: white; position: sticky; top: 0; }
    tr:nth-child(even) { background: #f9f9f9; }
    tr:hover { background: #f0f0f0; }
    .table-container { max-height: 600px; overflow-y: auto; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; background: #e9ecef; }
    .badge.assigned { background: #d4edda; color: #155724; }
    .badge.unassigned { background: #fff3cd; color: #856404; }
    .nav { margin-bottom: 20px; padding: 10px; background: #f8f9fa; border-radius: 4px; }
    .nav a { margin-right: 15px; text-decoration: none; color: #4CAF50; }
    .nav a:hover { text-decoration: underline; }
    </style>
    """


def generate_tool02_report(project: dict, output_dir: Path) -> Dict[str, Any]:
    """
    Generate Tool 02 - Review Text Authority Report.
    
    Maps transcript words to clip assignments.
    """
    segments = project.get('transcript', {}).get('segments', [])
    clips = project.get('clips', [])
    
    # Build segment -> clip mapping
    segment_to_clip = {}
    for clip in clips:
        sel = clip.get('selected_segment', {})
        seg_idx = sel.get('segment_index')
        if seg_idx is not None:
            segment_to_clip[seg_idx] = clip.get('id', '')
    
    # Extract all words
    words = []
    word_idx = 0
    for seg_idx, seg in enumerate(segments):
        seg_words = seg.get('words', [])
        clip_id = segment_to_clip.get(seg_idx, '')
        
        for w in seg_words:
            words.append({
                'word_index': word_idx,
                'text': w.get('text', ''),
                'segment_index': seg_idx,
                'segment_text': seg.get('text', '')[:50] + '...' if len(seg.get('text', '')) > 50 else seg.get('text', ''),
                'clip_id': clip_id,
                'original_start': w.get('start', 0),
                'original_end': w.get('end', 0)
            })
            word_idx += 1
    
    # Calculate metrics
    total_words = len(words)
    unique_segments = len(set(w['segment_index'] for w in words))
    assigned_words = sum(1 for w in words if w['clip_id'])
    unassigned_words = total_words - assigned_words
    
    # Build HTML
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        '<title>Tool 02 - Review Text Authority</title>',
        get_css(),
        '</head>',
        '<body>',
        '<div class="container">',
        '<h1>Tool 02 - Review Text Authority Report</h1>',
        f'<div class="meta">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>',
        
        '<div class="nav">',
        f'<a href="authoritative_sources_summary.html">Summary</a>',
        f'<a href="tool03_take_selection_report.html">Tool 03 - Clip Selection</a>',
        f'<a href="tool04_assembly_timing_report.html">Tool 04 - Assembly Timing</a>',
        '</div>',
        
        '<h2>Summary Metrics</h2>',
        '<div class="summary">',
        f'<div class="stat"><div class="stat-value">{total_words}</div><div class="stat-label">Total Words</div></div>',
        f'<div class="stat"><div class="stat-value">{unique_segments}</div><div class="stat-label">Unique Segments</div></div>',
        f'<div class="stat"><div class="stat-value">{assigned_words}</div><div class="stat-label">Assigned to Clips</div></div>',
        f'<div class="stat"><div class="stat-value">{unassigned_words}</div><div class="stat-label">Unassigned</div></div>',
        '</div>',
        
        '<h2>Word-Level Text Authority</h2>',
        '<div class="table-container">',
        '<table>',
        '<tr><th>Word Index</th><th>Text</th><th>Segment Index</th><th>Segment Preview</th><th>Clip Assignment</th><th>Original Start</th><th>Original End</th></tr>',
    ]
    
    for w in words[:2000]:  # Limit to prevent huge files
        clip_badge = f'<span class="badge assigned">{w["clip_id"]}</span>' if w['clip_id'] else '<span class="badge unassigned">unassigned</span>'
        html_parts.append(
            f'<tr>'
            f'<td>{w["word_index"]}</td>'
            f'<td><strong>{w["text"]}</strong></td>'
            f'<td>{w["segment_index"]}</td>'
            f'<td>{w["segment_text"]}</td>'
            f'<td>{clip_badge}</td>'
            f'<td>{w["original_start"]:.3f}</td>'
            f'<td>{w["original_end"]:.3f}</td>'
            f'</tr>'
        )
    
    html_parts.extend([
        '</table></div>',
        '</div>',
        '</body>',
        '</html>'
    ])
    
    output_path = output_dir / 'tool02_review_text_report.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))
    
    return {
        'path': str(output_path),
        'total_words': total_words,
        'unique_segments': unique_segments,
        'assigned_words': assigned_words,
        'unassigned_words': unassigned_words
    }


def generate_tool03_report(project: dict, output_dir: Path) -> Dict[str, Any]:
    """
    Generate Tool 03 - Clip Selection Authority Report.
    
    Shows clip ordering and segment selection.
    """
    clips = project.get('clips', [])
    segments = project.get('transcript', {}).get('segments', [])
    
    # Filter to clips with selection
    selected_clips = [c for c in clips if c.get('selected_segment')]
    
    # Sort by timeline position
    selected_clips.sort(key=lambda c: c.get('timeline_position', 0))
    
    # Build segment lookup
    segment_lookup = {i: seg for i, seg in enumerate(segments)}
    
    # Calculate metrics
    total_clips = len(selected_clips)
    segment_indices = set()
    for clip in selected_clips:
        sel = clip.get('selected_segment', {})
        seg_idx = sel.get('segment_index')
        if seg_idx is not None:
            segment_indices.add(seg_idx)
    total_segments = len(segment_indices)
    
    # Build HTML
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        '<title>Tool 03 - Take Selection Authority</title>',
        get_css(),
        '</head>',
        '<body>',
        '<div class="container">',
        '<h1>Tool 03 - Take Selection Authority Report</h1>',
        f'<div class="meta">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>',
        
        '<div class="nav">',
        f'<a href="authoritative_sources_summary.html">Summary</a>',
        f'<a href="tool02_review_text_report.html">Tool 02 - Text Authority</a>',
        f'<a href="tool04_assembly_timing_report.html">Tool 04 - Assembly Timing</a>',
        '</div>',
        
        '<h2>Summary Metrics</h2>',
        '<div class="summary">',
        f'<div class="stat"><div class="stat-value">{total_clips}</div><div class="stat-label">Total Clips</div></div>',
        f'<div class="stat"><div class="stat-value">{total_segments}</div><div class="stat-label">Segments Included</div></div>',
        f'<div class="stat"><div class="stat-value">{len(segments)}</div><div class="stat-label">Total Transcript Segments</div></div>',
        f'<div class="stat"><div class="stat-value">{len(segments) - total_segments}</div><div class="stat-label">Excluded Segments</div></div>',
        '</div>',
        
        '<h2>Clip Selection Order</h2>',
        '<div class="table-container">',
        '<table>',
        '<tr><th>Order</th><th>Clip ID</th><th>Clip Name</th><th>Segment Index</th><th>Segment Start</th><th>Segment End</th><th>Text Preview</th></tr>',
    ]
    
    for order, clip in enumerate(selected_clips):
        sel = clip.get('selected_segment', {})
        seg_idx = sel.get('segment_index')
        
        seg = segment_lookup.get(seg_idx, {}) if seg_idx is not None else {}
        
        html_parts.append(
            f'<tr>'
            f'<td>{order}</td>'
            f'<td><code>{clip.get("id", "")}</code></td>'
            f'<td>{clip.get("name", "")}</td>'
            f'<td>{seg_idx if seg_idx is not None else "-"}</td>'
            f'<td>{sel.get("start", 0):.3f}s</td>'
            f'<td>{sel.get("end", 0):.3f}s</td>'
            f'<td>{sel.get("text", "")[:60]}...</td>'
            f'</tr>'
        )
    
    html_parts.extend([
        '</table></div>',
        '</div>',
        '</body>',
        '</html>'
    ])
    
    output_path = output_dir / 'tool03_take_selection_report.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))
    
    return {
        'path': str(output_path),
        'total_clips': total_clips,
        'segments_included': total_segments,
        'segments_excluded': len(segments) - total_segments
    }


def generate_tool04_report(
    project: dict, 
    timeline_clips: List[Dict],
    caption_events: List[Dict],
    output_dir: Path
) -> Dict[str, Any]:
    """
    Generate Tool 04 - Assembly Timing Authority Report.
    
    Shows word-level and clip-level timing from assembly.
    """
    
    # Extract word timing data
    words = []
    word_idx = 0
    for event in caption_events:
        output_start = event.get('output_start', 0)
        original_start = event.get('original_start', 0)
        
        for w in event.get('words', []):
            word_output_start = output_start + (w.get('start', 0) - original_start)
            word_output_end = output_start + (w.get('end', 0) - original_start)
            
            words.append({
                'word_index': word_idx,
                'text': w.get('text', ''),
                'clip_id': event.get('clip_id', ''),
                'segment_index': event.get('segment_index', -1),
                'assembly_start': word_output_start,
                'assembly_end': word_output_end,
                'duration': word_output_end - word_output_start
            })
            word_idx += 1
    
    # Extract clip boundary data
    clips = []
    for item in timeline_clips:
        clip = item.get('clip', {})
        playable = item.get('playable_segments', [])
        
        for seg_start, seg_end in playable:
            clips.append({
                'clip_id': clip.get('id', ''),
                'clip_name': clip.get('name', ''),
                'assembly_start': seg_start,
                'assembly_end': seg_end,
                'duration': seg_end - seg_start
            })
    
    # Calculate metrics
    total_words = len(words)
    total_clips = len(clips)
    
    durations = [w['duration'] for w in words]
    mean_duration = sum(durations) / len(durations) if durations else 0
    max_duration = max(durations) if durations else 0
    min_duration = min(durations) if durations else 0
    
    # Build HTML
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        '<title>Tool 04 - Assembly Timing Authority</title>',
        get_css(),
        '</head>',
        '<body>',
        '<div class="container">',
        '<h1>Tool 04 - Assembly Timing Authority Report</h1>',
        f'<div class="meta">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>',
        
        '<div class="nav">',
        f'<a href="authoritative_sources_summary.html">Summary</a>',
        f'<a href="tool02_review_text_report.html">Tool 02 - Text Authority</a>',
        f'<a href="tool03_take_selection_report.html">Tool 03 - Clip Selection</a>',
        '</div>',
        
        '<h2>Summary Metrics</h2>',
        '<div class="summary">',
        f'<div class="stat"><div class="stat-value">{total_words}</div><div class="stat-label">Total Words</div></div>',
        f'<div class="stat"><div class="stat-value">{total_clips}</div><div class="stat-label">Clip Segments</div></div>',
        f'<div class="stat"><div class="stat-value">{mean_duration*1000:.0f}ms</div><div class="stat-label">Mean Word Duration</div></div>',
        f'<div class="stat"><div class="stat-value">{max_duration*1000:.0f}ms</div><div class="stat-label">Max Word Duration</div></div>',
        '</div>',
        
        '<h2>Word Timing Table</h2>',
        '<div class="table-container">',
        '<table>',
        '<tr><th>Word Index</th><th>Text</th><th>Clip ID</th><th>Segment Index</th><th>Assembly Start</th><th>Assembly End</th><th>Duration</th></tr>',
    ]
    
    for w in words[:2000]:  # Limit
        html_parts.append(
            f'<tr>'
            f'<td>{w["word_index"]}</td>'
            f'<td><strong>{w["text"]}</strong></td>'
            f'<td><code>{w["clip_id"]}</code></td>'
            f'<td>{w["segment_index"]}</td>'
            f'<td>{w["assembly_start"]:.3f}s</td>'
            f'<td>{w["assembly_end"]:.3f}s</td>'
            f'<td>{w["duration"]*1000:.0f}ms</td>'
            f'</tr>'
        )
    
    html_parts.extend([
        '</table></div>',
        
        '<h2>Clip Boundary Table</h2>',
        '<div class="table-container">',
        '<table>',
        '<tr><th>Clip ID</th><th>Clip Name</th><th>Assembly Start</th><th>Assembly End</th><th>Duration</th></tr>',
    ])
    
    for c in clips[:500]:  # Limit
        html_parts.append(
            f'<tr>'
            f'<td><code>{c["clip_id"]}</code></td>'
            f'<td>{c["clip_name"]}</td>'
            f'<td>{c["assembly_start"]:.3f}s</td>'
            f'<td>{c["assembly_end"]:.3f}s</td>'
            f'<td>{c["duration"]:.3f}s</td>'
            f'</tr>'
        )
    
    html_parts.extend([
        '</table></div>',
        '</div>',
        '</body>',
        '</html>'
    ])
    
    output_path = output_dir / 'tool04_assembly_timing_report.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))
    
    return {
        'path': str(output_path),
        'total_words': total_words,
        'total_clip_segments': total_clips,
        'mean_word_duration_ms': mean_duration * 1000,
        'max_word_duration_ms': max_duration * 1000,
        'min_word_duration_ms': min_duration * 1000
    }


def generate_summary_report(
    tool02_metrics: Dict,
    tool03_metrics: Dict,
    tool04_metrics: Dict,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Generate summary report with cross-reference.
    """
    
    # Check for mismatches
    mismatches = []
    
    # Tool 02 words should match Tool 04 words
    if tool02_metrics['total_words'] != tool04_metrics['total_words']:
        mismatches.append(
            f"Word count mismatch: Tool 02 has {tool02_metrics['total_words']} words, "
            f"Tool 04 has {tool04_metrics['total_words']} words"
        )
    
    # Build HTML
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        '<title>Authoritative Sources Summary</title>',
        get_css(),
        '</head>',
        '<body>',
        '<div class="container">',
        '<h1>Authoritative Sources Summary</h1>',
        f'<div class="meta">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>',
        
        '<h2>Cross-Reference Summary</h2>',
        '<div class="summary">',
        f'<div class="stat"><div class="stat-value">{tool02_metrics["total_words"]}</div><div class="stat-label">Tool 02 Words</div></div>',
        f'<div class="stat"><div class="stat-value">{tool03_metrics["total_clips"]}</div><div class="stat-label">Tool 03 Clips</div></div>',
        f'<div class="stat"><div class="stat-value">{tool04_metrics["total_words"]}</div><div class="stat-label">Tool 04 Words</div></div>',
        f'<div class="stat"><div class="stat-value">{tool04_metrics["total_clip_segments"]}</div><div class="stat-label">Tool 04 Clip Segments</div></div>',
        '</div>',
        
        '<h2>Report Links</h2>',
        '<ul>',
        f'<li><a href="tool02_review_text_report.html">Tool 02 - Review Text Authority</a> - {tool02_metrics["total_words"]} words, {tool02_metrics["unique_segments"]} segments</li>',
        f'<li><a href="tool03_take_selection_report.html">Tool 03 - Take Selection</a> - {tool03_metrics["total_clips"]} clips, {tool03_metrics["segments_included"]} segments</li>',
        f'<li><a href="tool04_assembly_timing_report.html">Tool 04 - Assembly Timing</a> - {tool04_metrics["total_words"]} words, mean duration {tool04_metrics["mean_word_duration_ms"]:.0f}ms</li>',
        '</ul>',
    ]
    
    if mismatches:
        html_parts.extend([
            '<h2>Mismatches Detected</h2>',
            '<ul>',
        ])
        for m in mismatches:
            html_parts.append(f'<li style="color: red;">{m}</li>')
        html_parts.append('</ul>')
    else:
        html_parts.append('<h2>Consistency Check</h2><p style="color: green;">All sources consistent.</p>')
    
    html_parts.extend([
        '<h2>Detailed Metrics</h2>',
        '<table>',
        '<tr><th>Source</th><th>Metric</th><th>Value</th></tr>',
        
        '<tr><td rowspan="4">Tool 02 - Text</td><td>Total Words</td><td>' + str(tool02_metrics['total_words']) + '</td></tr>',
        '<tr><td>Unique Segments</td><td>' + str(tool02_metrics['unique_segments']) + '</td></tr>',
        '<tr><td>Assigned Words</td><td>' + str(tool02_metrics['assigned_words']) + '</td></tr>',
        '<tr><td>Unassigned Words</td><td>' + str(tool02_metrics['unassigned_words']) + '</td></tr>',
        
        '<tr><td rowspan="3">Tool 03 - Selection</td><td>Total Clips</td><td>' + str(tool03_metrics['total_clips']) + '</td></tr>',
        '<tr><td>Segments Included</td><td>' + str(tool03_metrics['segments_included']) + '</td></tr>',
        '<tr><td>Segments Excluded</td><td>' + str(tool03_metrics['segments_excluded']) + '</td></tr>',
        
        '<tr><td rowspan="4">Tool 04 - Timing</td><td>Total Words</td><td>' + str(tool04_metrics['total_words']) + '</td></tr>',
        '<tr><td>Clip Segments</td><td>' + str(tool04_metrics['total_clip_segments']) + '</td></tr>',
        '<tr><td>Mean Word Duration</td><td>' + f'{tool04_metrics["mean_word_duration_ms"]:.1f}ms' + '</td></tr>',
        '<tr><td>Max Word Duration</td><td>' + f'{tool04_metrics["max_word_duration_ms"]:.1f}ms' + '</td></tr>',
        
        '</table>',
        '</div>',
        '</body>',
        '</html>'
    ])
    
    output_path = output_dir / 'authoritative_sources_summary.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))
    
    return {
        'path': str(output_path),
        'mismatches': mismatches,
        'consistent': len(mismatches) == 0
    }


def run_source_reports(project_root: Path) -> Dict[str, Any]:
    """
    Main entry point - generate all source reports.
    """
    # Setup paths
    project_path = project_root / 'data' / 'project.json'
    output_dir = project_root / 'data' / 'output' / 'verification' / 'source_reports'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load project
    project = load_json(project_path)
    
    # Compute timeline and caption events for Tool 04
    timeline_clips = compute_timeline_clips(project)
    caption_events = build_caption_events(project, timeline_clips)
    
    # Generate reports
    print("Generating Tool 02 - Text Authority Report...")
    tool02_metrics = generate_tool02_report(project, output_dir)
    
    print("Generating Tool 03 - Clip Selection Report...")
    tool03_metrics = generate_tool03_report(project, output_dir)
    
    print("Generating Tool 04 - Assembly Timing Report...")
    tool04_metrics = generate_tool04_report(project, timeline_clips, caption_events, output_dir)
    
    print("Generating Summary Report...")
    summary_metrics = generate_summary_report(tool02_metrics, tool03_metrics, tool04_metrics, output_dir)
    
    return {
        'success': True,
        'output_dir': str(output_dir),
        'tool02': tool02_metrics,
        'tool03': tool03_metrics,
        'tool04': tool04_metrics,
        'summary': summary_metrics
    }


def print_source_report_summary(result: Dict[str, Any]) -> None:
    """Print summary to terminal."""
    print("\n" + "=" * 60)
    print("AUTHORITATIVE SOURCE REPORTS")
    print("=" * 60)
    
    print(f"\nOutput directory: {result['output_dir']}")
    
    print("\nGenerated reports:")
    print(f"  Tool 02 - Text Authority:    {result['tool02']['total_words']} words")
    print(f"  Tool 03 - Clip Selection:   {result['tool03']['total_clips']} clips")
    print(f"  Tool 04 - Assembly Timing:  {result['tool04']['total_words']} words")
    
    if result['summary']['consistent']:
        print("\nConsistency: ALL SOURCES CONSISTENT")
    else:
        print("\nConsistency: MISMATCHES DETECTED")
        for m in result['summary']['mismatches']:
            print(f"  - {m}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate source reports')
    parser.add_argument('--project', '-p', type=str, help='Path to project root')
    args = parser.parse_args()
    
    root = Path(args.project) if args.project else get_project_root()
    
    result = run_source_reports(root)
    print_source_report_summary(result)
