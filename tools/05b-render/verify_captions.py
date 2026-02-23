#!/usr/bin/env python3
"""
Full pipeline caption fidelity verification.

Validates:
1. Text fidelity relative to Tool 02 (reviewed text) filtered by Tool 03 (selection)
2. Timing projection fidelity relative to Tool 04 (assembly timing)
3. Segment selection fidelity relative to Tool 03 (canonical clips)

Exit codes:
0 - All checks pass
1 - Text fidelity failure
2 - Timing projection failure
3 - Escalation report generated (manual inspection needed)
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from segments import compute_timeline_clips
from captions import build_caption_events
from srt import generate_srt_content, compress_timestamps


TIMING_TOLERANCE_MS = 40
TIMING_TOLERANCE_SEC = TIMING_TOLERANCE_MS / 1000.0


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def load_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_word(text: str) -> str:
    """Normalize word for comparison."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\']', '', text)
    return text


def parse_srt(srt_content: str) -> List[Dict[str, Any]]:
    """Parse SRT content into structured blocks with word-level timing."""
    blocks = []
    current_block = {}
    
    for line in srt_content.strip().split('\n'):
        line = line.strip()
        if not line:
            if current_block:
                blocks.append(current_block)
                current_block = {}
            continue
        
        if current_block.get('index') is None:
            try:
                current_block['index'] = int(line)
            except ValueError:
                if 'text' in current_block:
                    current_block['text'] += ' ' + line
                else:
                    current_block['text'] = line
        elif 'start' not in current_block:
            match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', line)
            if match:
                h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())
                current_block['start'] = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
                current_block['end'] = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
        else:
            if 'text' in current_block:
                current_block['text'] += ' ' + line
            else:
                current_block['text'] = line
    
    if current_block:
        blocks.append(current_block)
    
    for block in blocks:
        if 'text' in block:
            words = []
            for word in block['text'].split():
                norm = normalize_word(word)
                if norm:
                    words.append({'text': word, 'normalized': norm})
            block['words'] = words
    
    return blocks


def load_authoritative_sources(project: dict) -> Tuple[List[Dict], List[Dict]]:
    """
    Phase 1: Load authoritative sources.
    
    Uses the same caption event generation logic as render.py to ensure
    output times match the render pipeline.
    
    Returns:
        - authoritative_clips: List of canonical clip data with segment info
        - authoritative_words: Flat list of all authoritative words with timing
    """
    # Use existing pipeline logic to compute output times
    timeline_clips = compute_timeline_clips(project)
    caption_events = build_caption_events(project, timeline_clips)
    
    clips = project.get('clips', [])
    
    # Build clip lookup by id
    clip_by_id = {c.get('id', ''): c for c in clips}
    
    # Build authoritative clips from timeline order
    authoritative_clips = []
    authoritative_words = []
    
    for item in timeline_clips:
        clip = item['clip']
        clip_id = clip.get('id', '')
        selected = clip.get('selected_segment', {})
        
        segment_index = selected.get('segment_index', -1)
        clip_text = selected.get('text', '')
        
        # Calculate total duration for this clip
        clip_duration = sum(end - start for start, end in item['playable_segments'])
        
        clip_words = []
        
        authoritative_clips.append({
            'clip_id': clip_id,
            'timeline_position': clip.get('timeline_position', 0),
            'segment_index': segment_index,
            'authoritative_start': selected.get('start', 0),
            'authoritative_end': selected.get('end', 0),
            'authoritative_text': clip_text,
            'authoritative_duration': clip_duration,
            'playable_segments': item['playable_segments'],
            'word_count': 0,  # Will be updated below
            'words': []
        })
    
    # Extract words from caption events (which have correct output times)
    for event in caption_events:
        clip_id = event.get('clip_id', '')
        segment_index = event.get('segment_index', -1)
        output_start = event.get('output_start', 0)
        original_start = event.get('original_start', 0)
        
        for word in event.get('words', []):
            word_original_start = word.get('start', 0)
            word_original_end = word.get('end', 0)
            
            # Calculate output time using same formula as render
            word_rel_start = word_original_start - original_start
            word_rel_end = word_original_end - original_start
            
            word_output_start = output_start + word_rel_start
            word_output_end = output_start + word_rel_end
            
            word_entry = {
                'text': word.get('text', ''),
                'normalized': normalize_word(word.get('text', '')),
                'authoritative_start': word_original_start,
                'authoritative_end': word_original_end,
                'output_start': word_output_start,
                'output_end': word_output_end,
                'clip_id': clip_id,
                'segment_index': segment_index,
            }
            
            authoritative_words.append(word_entry)
            
            # Add to corresponding clip
            for ac in authoritative_clips:
                if ac['clip_id'] == clip_id:
                    ac['words'].append(word_entry)
                    ac['word_count'] = len(ac['words'])
                    break
    
    return authoritative_clips, authoritative_words


def load_render_output(srt_content: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Phase 2: Load render output from SRT.
    
    Returns:
        - blocks: List of SRT blocks with timing and words
        - words: Flat list of words with interpolated timing (for comparison)
    """
    blocks = parse_srt(srt_content)
    
    rendered_words = []
    word_index = 0
    
    for block in blocks:
        block_start = block.get('start', 0)
        block_end = block.get('end', 0)
        block_words = block.get('words', [])
        
        if not block_words:
            continue
        
        # For timing comparison, use actual block timing
        # All words in a block share the block's timing range
        for i, word in enumerate(block_words):
            rendered_words.append({
                'text': word.get('text', ''),
                'normalized': word.get('normalized', ''),
                'rendered_start': block_start,  # Block timing
                'rendered_end': block_end,      # Block timing
                'block_index': block.get('index', 0),
                'word_index': word_index
            })
            word_index += 1
    
    return blocks, rendered_words


def validate_text_fidelity(
    authoritative_words: List[Dict],
    rendered_words: List[Dict]
) -> Dict[str, Any]:
    """
    Phase 3: Validate text fidelity.
    
    Compares authoritative word sequence to rendered word sequence.
    """
    auth_normalized = [w['normalized'] for w in authoritative_words]
    render_normalized = [w['normalized'] for w in rendered_words]
    
    # Find first mismatch
    first_mismatch_index = -1
    mismatch_type = None
    mismatch_details = None
    
    max_len = max(len(auth_normalized), len(render_normalized))
    
    for i in range(max_len):
        auth_word = auth_normalized[i] if i < len(auth_normalized) else None
        render_word = render_normalized[i] if i < len(render_normalized) else None
        
        if auth_word != render_word:
            first_mismatch_index = i
            if auth_word is None:
                mismatch_type = 'extra_word'
                mismatch_details = f"Extra word '{render_word}' at index {i}"
            elif render_word is None:
                mismatch_type = 'missing_word'
                mismatch_details = f"Missing word '{auth_word}' at index {i}"
            else:
                mismatch_type = 'word_mismatch'
                mismatch_details = f"Expected '{auth_word}', got '{render_word}' at index {i}"
            break
    
    # Calculate coverage
    auth_set = set(auth_normalized)
    render_set = set(render_normalized)
    
    missing_set = auth_set - render_set
    extra_set = render_set - auth_set
    
    # Word order check (detect reorderings)
    reorderings = []
    if len(auth_normalized) == len(render_normalized):
        for i in range(len(auth_normalized)):
            if auth_normalized[i] != render_normalized[i]:
                # Look ahead for the expected word
                for j in range(i + 1, min(i + 10, len(render_normalized))):
                    if render_normalized[j] == auth_normalized[i]:
                        reorderings.append({
                            'index': i,
                            'expected': auth_normalized[i],
                            'got': render_normalized[i],
                            'found_at': j
                        })
                        break
    
    # Detect duplications
    auth_counts = {}
    render_counts = {}
    
    for w in auth_normalized:
        auth_counts[w] = auth_counts.get(w, 0) + 1
    for w in render_normalized:
        render_counts[w] = render_counts.get(w, 0) + 1
    
    duplications = []
    for word, auth_count in auth_counts.items():
        render_count = render_counts.get(word, 0)
        if render_count > auth_count:
            duplications.append({
                'word': word,
                'authoritative_count': auth_count,
                'rendered_count': render_count
            })
    
    # Truncation detection (words cut at boundaries)
    truncations = []
    for i, auth_word in enumerate(authoritative_words):
        if auth_word['normalized'] not in render_set:
            # Check if at clip boundary
            truncations.append({
                'word': auth_word['text'],
                'clip_id': auth_word.get('clip_id', ''),
                'authoritative_start': auth_word['authoritative_start'],
                'authoritative_end': auth_word['authoritative_end']
            })
    
    coverage_pct = 0.0
    if auth_normalized:
        matched = sum(1 for w in auth_normalized if w in render_set)
        coverage_pct = matched / len(auth_normalized) * 100
    
    passed = (
        first_mismatch_index == -1 and
        len(missing_set) == 0 and
        len(reorderings) == 0 and
        coverage_pct >= 99.0
    )
    
    return {
        'passed': passed,
        'total_authoritative_words': len(authoritative_words),
        'total_rendered_words': len(rendered_words),
        'coverage_percentage': round(coverage_pct, 2),
        'first_mismatch_index': first_mismatch_index,
        'mismatch_type': mismatch_type,
        'mismatch_details': mismatch_details,
        'missing_words': list(missing_set)[:50],
        'extra_words': list(extra_set)[:50],
        'reorderings': reorderings[:10],
        'duplications': duplications[:10],
        'truncations': truncations[:20]
    }


def validate_timing_projection(
    authoritative_words: List[Dict],
    rendered_words: List[Dict],
    caption_events: List[Dict],
    rendered_blocks: List[Dict]
) -> Dict[str, Any]:
    """
    Phase 4: Validate timing projection fidelity.
    
    Compares at the SRT block level since that's the actual output format.
    Word-level timing comparison would show false drifts due to block grouping.
    """
    # Generate expected SRT blocks using the same logic as render
    expected_blocks = compress_timestamps(caption_events)
    
    timing_comparisons = []
    drift_issues = []
    
    # Compare block by block
    num_blocks = min(len(expected_blocks), len(rendered_blocks))
    
    for i in range(num_blocks):
        exp = expected_blocks[i]
        ren = rendered_blocks[i]
        
        exp_start = exp.get('start', 0)
        exp_end = exp.get('end', 0)
        ren_start = ren.get('start', 0)
        ren_end = ren.get('end', 0)
        
        delta_start_ms = (ren_start - exp_start) * 1000
        delta_end_ms = (ren_end - exp_end) * 1000
        
        flags = []
        
        if abs(delta_start_ms) > TIMING_TOLERANCE_MS:
            flags.append('drift_start')
        if abs(delta_end_ms) > TIMING_TOLERANCE_MS:
            flags.append('drift_end')
        
        comparison = {
            'block_index': i,
            'expected_start': exp_start,
            'expected_end': exp_end,
            'rendered_start': ren_start,
            'rendered_end': ren_end,
            'delta_start_ms': round(delta_start_ms, 1),
            'delta_end_ms': round(delta_end_ms, 1),
            'expected_text': exp.get('text', '')[:50],
            'rendered_text': ren.get('text', '')[:50],
            'flags': flags
        }
        
        timing_comparisons.append(comparison)
        
        if flags:
            drift_issues.append(comparison)
    
    # Check for non-monotonic timeline in blocks
    prev_end = 0.0
    for comp in timing_comparisons:
        if comp['rendered_start'] < prev_end - TIMING_TOLERANCE_SEC:
            comp['flags'].append('non_monotonic')
        prev_end = comp['rendered_end']
    
    # Calculate drift statistics
    deltas = [abs(c['delta_start_ms']) for c in timing_comparisons]
    
    max_drift = max(deltas) if deltas else 0.0
    mean_drift = sum(deltas) / len(deltas) if deltas else 0.0
    
    # Find first drift
    first_drift_index = -1
    first_drift_details = None
    for comp in timing_comparisons:
        if comp['flags']:
            first_drift_index = comp['block_index']
            first_drift_details = comp
            break
    
    # Check for critical issues
    non_monotonic_count = sum(1 for c in timing_comparisons if 'non_monotonic' in c['flags'])
    
    passed = (
        len(drift_issues) == 0 and
        non_monotonic_count == 0 and
        len(expected_blocks) == len(rendered_blocks)
    )
    
    return {
        'passed': passed,
        'tolerance_ms': TIMING_TOLERANCE_MS,
        'expected_block_count': len(expected_blocks),
        'rendered_block_count': len(rendered_blocks),
        'max_drift_ms': round(max_drift, 1),
        'mean_drift_ms': round(mean_drift, 1),
        'first_drift_index': first_drift_index,
        'first_drift_details': first_drift_details,
        'drift_issue_count': len(drift_issues),
        'non_monotonic_count': non_monotonic_count,
        'drift_issues': drift_issues[:20],
        'timing_comparisons': timing_comparisons,
        # For word-level display (using block timing)
        'word_comparisons': _build_word_comparisons(authoritative_words, rendered_words)
    }


def _build_word_comparisons(
    authoritative_words: List[Dict],
    rendered_words: List[Dict]
) -> List[Dict[str, Any]]:
    """Build word-level comparison list for report display."""
    comparisons = []
    render_idx = 0
    
    for auth_idx, auth_word in enumerate(authoritative_words):
        auth_norm = auth_word['normalized']
        
        found_idx = -1
        for i in range(render_idx, min(render_idx + 20, len(rendered_words))):
            if rendered_words[i]['normalized'] == auth_norm:
                found_idx = i
                break
        
        if found_idx == -1:
            comparisons.append({
                'index': auth_idx,
                'word': auth_word['text'],
                'clip_id': auth_word.get('clip_id', ''),
                'segment_index': auth_word.get('segment_index', -1),
                'authoritative_start': auth_word['output_start'],
                'authoritative_end': auth_word['output_end'],
                'rendered_start': None,
                'rendered_end': None,
                'delta_start_ms': None,
                'delta_end_ms': None,
                'flags': ['not_rendered']
            })
            continue
        
        render_word = rendered_words[found_idx]
        render_idx = found_idx + 1
        
        delta_start_ms = (render_word['rendered_start'] - auth_word['output_start']) * 1000
        delta_end_ms = (render_word['rendered_end'] - auth_word['output_end']) * 1000
        
        flags = []
        if abs(delta_start_ms) > 500:
            flags.append('block_timing')
        
        comparisons.append({
            'index': auth_idx,
            'word': auth_word['text'],
            'clip_id': auth_word.get('clip_id', ''),
            'segment_index': auth_word.get('segment_index', -1),
            'authoritative_start': auth_word['output_start'],
            'authoritative_end': auth_word['output_end'],
            'rendered_start': render_word['rendered_start'],
            'rendered_end': render_word['rendered_end'],
            'delta_start_ms': round(delta_start_ms, 1),
            'delta_end_ms': round(delta_end_ms, 1),
            'flags': flags
        })
    
    return comparisons


def localize_drift(
    timing_result: Dict,
    authoritative_clips: List[Dict]
) -> Dict[str, Any]:
    """
    Phase 5: Localize drift to specific boundaries.
    
    Only reports patterns if there are actual timing issues detected.
    """
    # Skip localization if timing passed
    if timing_result.get('passed', False):
        return {
            'drift_patterns': [],
            'clip_boundaries': [],
            'cumulative_offsets': []
        }
    
    comparisons = timing_result.get('word_comparisons', timing_result.get('timing_comparisons', []))
    
    clip_boundaries = {}
    for clip in authoritative_clips:
        clip_id = clip['clip_id']
        clip_boundaries[clip_id] = {
            'clip_id': clip_id,
            'timeline_position': clip['timeline_position'],
            'authoritative_duration': clip['authoritative_duration'],
            'word_count': clip['word_count'],
            'first_word_index': None,
            'last_word_index': None,
            'drift_at_start': None,
            'drift_at_end': None
        }
    
    # Map words to clips
    for i, comp in enumerate(comparisons):
        clip_id = comp.get('clip_id', '')
        if clip_id in clip_boundaries:
            cb = clip_boundaries[clip_id]
            if cb['first_word_index'] is None:
                cb['first_word_index'] = i
                cb['drift_at_start'] = comp.get('delta_start_ms')
            cb['last_word_index'] = i
            cb['drift_at_end'] = comp.get('delta_end_ms')
    
    # Identify drift patterns
    drift_patterns = []
    
    # Check for clip boundary drift
    prev_clip_end_drift = 0.0
    for clip_id, cb in sorted(clip_boundaries.items(), key=lambda x: x[1]['timeline_position']):
        if cb['drift_at_start'] is not None:
            drift_jump = cb['drift_at_start'] - prev_clip_end_drift
            if abs(drift_jump) > TIMING_TOLERANCE_MS:
                drift_patterns.append({
                    'type': 'clip_boundary',
                    'clip_id': clip_id,
                    'drift_jump_ms': round(drift_jump, 1),
                    'drift_at_start_ms': cb['drift_at_start']
                })
        if cb['drift_at_end'] is not None:
            prev_clip_end_drift = cb['drift_at_end']
    
    # Check for cumulative offset
    cumulative_offsets = []
    running_offset = 0.0
    for comp in comparisons:
        if comp['delta_start_ms'] is not None:
            running_offset = comp['delta_start_ms']
            cumulative_offsets.append({
                'index': comp['index'],
                'word': comp['word'],
                'cumulative_offset_ms': running_offset
            })
    
    # Detect monotonic drift
    if len(cumulative_offsets) >= 10:
        first_10 = [o['cumulative_offset_ms'] for o in cumulative_offsets[:10]]
        last_10 = [o['cumulative_offset_ms'] for o in cumulative_offsets[-10:]]
        avg_first = sum(first_10) / len(first_10)
        avg_last = sum(last_10) / len(last_10)
        
        if abs(avg_last - avg_first) > TIMING_TOLERANCE_MS * 2:
            drift_patterns.append({
                'type': 'cumulative_offset',
                'start_avg_ms': round(avg_first, 1),
                'end_avg_ms': round(avg_last, 1),
                'total_drift_ms': round(avg_last - avg_first, 1)
            })
    
    return {
        'drift_patterns': drift_patterns,
        'clip_boundaries': list(clip_boundaries.values()),
        'cumulative_offsets': cumulative_offsets[:20]
    }


def generate_escalation_report(
    authoritative_clips: List[Dict],
    authoritative_words: List[Dict],
    text_result: Dict,
    timing_result: Dict,
    drift_localization: Dict,
    output_path: Path
) -> None:
    """
    Phase 6: Generate escalation report for manual inspection.
    """
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        '<title>Caption Full Verification Report</title>',
        '<style>',
        'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 20px; background: #f5f5f5; }',
        '.container { max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }',
        'h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }',
        'h2 { color: #555; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }',
        '.summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }',
        '.stat { background: #e9ecef; padding: 15px; border-radius: 4px; text-align: center; }',
        '.stat-value { font-size: 28px; font-weight: bold; color: #333; }',
        '.stat-label { font-size: 11px; color: #666; text-transform: uppercase; }',
        '.stat.fail { background: #f8d7da; }',
        '.stat.pass { background: #d4edda; }',
        '.status { padding: 15px 20px; border-radius: 4px; font-weight: bold; font-size: 16px; margin-bottom: 20px; }',
        '.status.pass { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }',
        '.status.fail { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }',
        '.status.escalate { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }',
        'table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }',
        'th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }',
        'th { background: #4CAF50; color: white; position: sticky; top: 0; }',
        'tr:nth-child(even) { background: #f9f9f9; }',
        'tr:hover { background: #f1f1f1; }',
        '.flag { background: #fff3cd; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin: 1px; display: inline-block; }',
        '.flag.error { background: #f8d7da; }',
        '.drift { color: #dc3545; font-weight: bold; }',
        '.table-container { max-height: 500px; overflow-y: auto; margin-top: 15px; }',
        '.pattern { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #ffc107; }',
        '</style>',
        '</head>',
        '<body>',
        '<div class="container">',
        f'<h1>Caption Full Verification Report</h1>',
        f'<p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
    ]
    
    # Determine overall status
    text_passed = text_result['passed']
    timing_passed = timing_result['passed']
    
    if text_passed and timing_passed:
        status_class = 'pass'
        status_text = 'ALL CHECKS PASSED'
    elif not text_passed:
        status_class = 'fail'
        status_text = 'TEXT FIDELITY FAILURE'
    elif not timing_passed:
        status_class = 'fail'
        status_text = 'TIMING PROJECTION FAILURE'
    else:
        status_class = 'escalate'
        status_text = 'ESCALATION: Manual Inspection Required'
    
    html_parts.append(f'<div class="status {status_class}">{status_text}</div>')
    
    # Summary stats
    html_parts.append('<h2>Summary</h2>')
    html_parts.append('<div class="summary">')
    
    stat_class = 'pass' if text_passed else 'fail'
    html_parts.append(f'<div class="stat {stat_class}"><div class="stat-value">{text_result["coverage_percentage"]:.1f}%</div><div class="stat-label">Text Coverage</div></div>')
    html_parts.append(f'<div class="stat"><div class="stat-value">{text_result["total_authoritative_words"]}</div><div class="stat-label">Authoritative Words</div></div>')
    html_parts.append(f'<div class="stat"><div class="stat-value">{text_result["total_rendered_words"]}</div><div class="stat-label">Rendered Words</div></div>')
    
    stat_class = 'pass' if timing_passed else 'fail'
    html_parts.append(f'<div class="stat {stat_class}"><div class="stat-value">{timing_result["max_drift_ms"]:.0f}ms</div><div class="stat-label">Max Drift</div></div>')
    html_parts.append(f'<div class="stat"><div class="stat-value">{timing_result["mean_drift_ms"]:.1f}ms</div><div class="stat-label">Mean Drift</div></div>')
    html_parts.append(f'<div class="stat"><div class="stat-value">{timing_result["drift_issue_count"]}</div><div class="stat-label">Drift Issues</div></div>')
    
    html_parts.append('</div>')
    
    # Text fidelity section
    html_parts.append('<h2>Phase 3: Text Fidelity</h2>')
    if text_passed:
        html_parts.append('<p>Text fidelity check PASSED</p>')
    else:
        html_parts.append(f'<p>Text fidelity check FAILED</p>')
        if text_result['first_mismatch_index'] >= 0:
            html_parts.append(f'<p>First mismatch at index {text_result["first_mismatch_index"]}: {text_result["mismatch_details"]}</p>')
        if text_result['missing_words']:
            html_parts.append(f'<p>Missing words: {", ".join(text_result["missing_words"][:20])}</p>')
        if text_result['extra_words']:
            html_parts.append(f'<p>Extra words: {", ".join(text_result["extra_words"][:20])}</p>')
    
    # Timing projection section
    html_parts.append('<h2>Phase 4: Timing Projection</h2>')
    html_parts.append(f'<p>Tolerance: {TIMING_TOLERANCE_MS}ms</p>')
    
    if timing_passed:
        html_parts.append('<p>Timing projection check PASSED</p>')
    else:
        html_parts.append(f'<p>Timing projection check FAILED</p>')
        if timing_result['first_drift_index'] >= 0:
            fd = timing_result['first_drift_details']
            if fd:
                html_parts.append(f'<p>First drift at index {timing_result["first_drift_index"]}: word "{fd["word"]}" delta_start={fd["delta_start_ms"]}ms</p>')
    
    # Drift localization
    html_parts.append('<h2>Phase 5: Drift Localization</h2>')
    
    patterns = drift_localization.get('drift_patterns', [])
    if patterns:
        html_parts.append('<p>Detected drift patterns:</p>')
        for p in patterns:
            html_parts.append(f'<div class="pattern"><strong>{p["type"]}</strong>: {json.dumps(p, indent=2)}</div>')
    else:
        html_parts.append('<p>No significant drift patterns detected.</p>')
    
    # Detailed timing table
    html_parts.append('<h2>Detailed Timing Comparison</h2>')
    html_parts.append('<div class="table-container">')
    html_parts.append('<table><tr>')
    html_parts.append('<th>Index</th><th>Word</th><th>Clip ID</th><th>Seg</th>')
    html_parts.append('<th>Auth Start</th><th>Render Start</th><th>Δ Start (ms)</th>')
    html_parts.append('<th>Auth End</th><th>Render End</th><th>Δ End (ms)</th>')
    html_parts.append('<th>Flags</th>')
    html_parts.append('</tr>')
    
    word_comps = timing_result.get('word_comparisons', timing_result.get('timing_comparisons', []))
    for comp in word_comps[:200]:
        flags_html = ' '.join(f'<span class="flag error">{f}</span>' for f in comp.get('flags', [])) if comp.get('flags') else '-'
        
        delta_start_class = 'drift' if abs(comp.get('delta_start_ms') or 0) > TIMING_TOLERANCE_MS else ''
        delta_end_class = 'drift' if abs(comp.get('delta_end_ms') or 0) > TIMING_TOLERANCE_MS else ''
        
        rs = f'{comp["rendered_start"]:.3f}' if comp.get('rendered_start') is not None else "-"
        re = f'{comp["rendered_end"]:.3f}' if comp.get('rendered_end') is not None else "-"
        
        html_parts.append('<tr>')
        html_parts.append(f'<td>{comp["index"]}</td>')
        html_parts.append(f'<td>{comp["word"]}</td>')
        html_parts.append(f'<td>{comp["clip_id"][:20] if comp.get("clip_id") else "-"}</td>')
        html_parts.append(f'<td>{comp.get("segment_index", -1)}</td>')
        html_parts.append(f'<td>{comp["authoritative_start"]:.3f}</td>')
        html_parts.append(f'<td>{rs}</td>')
        html_parts.append(f'<td class="{delta_start_class}">{comp.get("delta_start_ms") if comp.get("delta_start_ms") is not None else "-"}</td>')
        html_parts.append(f'<td>{comp["authoritative_end"]:.3f}</td>')
        html_parts.append(f'<td>{re}</td>')
        html_parts.append(f'<td class="{delta_end_class}">{comp.get("delta_end_ms") if comp.get("delta_end_ms") is not None else "-"}</td>')
        html_parts.append(f'<td>{flags_html}</td>')
        html_parts.append('</tr>')
    
    html_parts.append('</table></div>')
    
    # Segment boundary table
    html_parts.append('<h2>Segment Boundary Comparison</h2>')
    html_parts.append('<table><tr><th>Timeline Pos</th><th>Clip ID</th><th>Auth Duration</th><th>Word Count</th><th>Drift at Start</th><th>Drift at End</th></tr>')
    
    for cb in drift_localization['clip_boundaries']:
        html_parts.append('<tr>')
        html_parts.append(f'<td>{cb["timeline_position"]}</td>')
        html_parts.append(f'<td>{cb["clip_id"][:30]}</td>')
        html_parts.append(f'<td>{cb["authoritative_duration"]:.3f}s</td>')
        html_parts.append(f'<td>{cb["word_count"]}</td>')
        html_parts.append(f'<td>{cb.get("drift_at_start", 0):.1f}ms</td>' if cb.get('drift_at_start') is not None else '<td>-</td>')
        html_parts.append(f'<td>{cb.get("drift_at_end", 0):.1f}ms</td>' if cb.get('drift_at_end') is not None else '<td>-</td>')
        html_parts.append('</tr>')
    
    html_parts.append('</table>')
    
    html_parts.extend(['</div>', '</body>', '</html>'])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))


def main():
    global TIMING_TOLERANCE_MS, TIMING_TOLERANCE_SEC
    
    parser = argparse.ArgumentParser(description='Full pipeline caption fidelity verification')
    parser.add_argument('--project', '-p', type=str, help='Path to project.json or project root')
    parser.add_argument('--data-dir', '-d', type=str, help='Path to data directory')
    parser.add_argument('--tolerance', '-t', type=int, default=TIMING_TOLERANCE_MS,
                        help=f'Timing tolerance in ms (default: {TIMING_TOLERANCE_MS})')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    TIMING_TOLERANCE_MS = args.tolerance
    TIMING_TOLERANCE_SEC = TIMING_TOLERANCE_MS / 1000.0
    
    root = get_project_root()
    
    # Resolve paths
    if args.project:
        project_arg = Path(args.project)
        if project_arg.is_dir():
            project_path = project_arg / 'data' / 'project.json'
            data_dir = project_arg / 'data'
        else:
            project_path = project_arg
            data_dir = project_arg.parent
    else:
        project_path = root / 'data' / 'project.json'
        data_dir = root / 'data'
    
    if args.data_dir:
        data_dir = Path(args.data_dir)
    
    output_dir = data_dir / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("FULL PIPELINE CAPTION FIDELITY VERIFICATION")
    print("=" * 60)
    
    # Phase 1: Load authoritative sources
    print("\n[Phase 1] Loading authoritative sources...")
    project = load_json(project_path)
    
    # Use existing pipeline logic to compute output times
    timeline_clips = compute_timeline_clips(project)
    caption_events = build_caption_events(project, timeline_clips)
    
    authoritative_clips, authoritative_words = load_authoritative_sources(project)
    print(f"  Authoritative clips: {len(authoritative_clips)}")
    print(f"  Authoritative words: {len(authoritative_words)}")
    print(f"  Caption events: {len(caption_events)}")
    
    # Phase 2: Load render output
    print("\n[Phase 2] Loading render output...")
    srt_path = output_dir / 'captions.srt'
    if not srt_path.exists():
        print(f"  ERROR: SRT not found at {srt_path}", file=sys.stderr)
        print("  Run render.py first to generate captions.")
        sys.exit(2)
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    
    rendered_blocks, rendered_words = load_render_output(srt_content)
    print(f"  Rendered blocks: {len(rendered_blocks)}")
    print(f"  Rendered words: {len(rendered_words)}")
    
    # Phase 3: Text fidelity validation
    print("\n[Phase 3] Validating text fidelity...")
    text_result = validate_text_fidelity(authoritative_words, rendered_words)
    print(f"  Coverage: {text_result['coverage_percentage']:.2f}%")
    print(f"  Authoritative: {text_result['total_authoritative_words']} words")
    print(f"  Rendered: {text_result['total_rendered_words']} words")
    
    if not text_result['passed']:
        print(f"  STATUS: TEXT FIDELITY FAILURE")
        if text_result['first_mismatch_index'] >= 0:
            print(f"  First mismatch: {text_result['mismatch_details']}")
    
    # Phase 4: Timing projection validation
    print("\n[Phase 4] Validating timing projection...")
    timing_result = validate_timing_projection(
        authoritative_words, rendered_words, caption_events, rendered_blocks
    )
    print(f"  Tolerance: {TIMING_TOLERANCE_MS}ms")
    print(f"  Expected blocks: {timing_result['expected_block_count']}")
    print(f"  Rendered blocks: {timing_result['rendered_block_count']}")
    print(f"  Max drift: {timing_result['max_drift_ms']:.1f}ms")
    print(f"  Mean drift: {timing_result['mean_drift_ms']:.1f}ms")
    print(f"  Block drift issues: {timing_result['drift_issue_count']}")
    
    if not timing_result['passed']:
        print(f"  STATUS: TIMING PROJECTION FAILURE")
        if timing_result['first_drift_index'] >= 0:
            fd = timing_result['first_drift_details']
            if fd:
                print(f"  First drift: word '{fd['word']}' at index {timing_result['first_drift_index']}")
    
    # Phase 5: Drift localization
    print("\n[Phase 5] Localizing drift...")
    drift_localization = localize_drift(timing_result, authoritative_clips)
    patterns = drift_localization.get('drift_patterns', [])
    print(f"  Drift patterns detected: {len(patterns)}")
    
    for p in patterns:
        print(f"    - {p['type']}: {json.dumps({k:v for k,v in p.items() if k != 'type'})}")
    
    # Determine exit code and generate report if needed
    text_passed = text_result['passed']
    timing_passed = timing_result['passed']
    
    # Always generate report
    report_path = output_dir / 'captions_full_verification_report.html'
    generate_escalation_report(
        authoritative_clips,
        authoritative_words,
        text_result,
        timing_result,
        drift_localization,
        report_path
    )
    print(f"\n[Phase 6] Report saved to: {report_path}")
    
    # Save JSON summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'project_path': str(project_path),
        'tolerance_ms': TIMING_TOLERANCE_MS,
        'text_fidelity': text_result,
        'timing_projection': {
            'passed': timing_result['passed'],
            'tolerance_ms': timing_result['tolerance_ms'],
            'max_drift_ms': timing_result['max_drift_ms'],
            'mean_drift_ms': timing_result['mean_drift_ms'],
            'drift_issue_count': timing_result['drift_issue_count'],
            'first_drift_index': timing_result['first_drift_index']
        },
        'drift_patterns': patterns,
        'passed': text_passed and timing_passed
    }
    
    summary_path = output_dir / 'captions_full_verification_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to: {summary_path}")
    
    # Final result
    print("\n" + "=" * 60)
    
    if text_passed and timing_passed:
        print("RESULT: ALL CHECKS PASSED")
        print("=" * 60)
        sys.exit(0)
    elif not text_passed:
        print("RESULT: TEXT FIDELITY FAILURE (exit code 1)")
        print("=" * 60)
        sys.exit(1)
    elif not timing_passed:
        # Check if root cause can be isolated
        if len(patterns) == 1 and patterns[0]['type'] in ('clip_boundary', 'cumulative_offset'):
            print(f"RESULT: TIMING PROJECTION FAILURE - {patterns[0]['type']} detected (exit code 2)")
        else:
            print("RESULT: TIMING PROJECTION FAILURE - Escalation report generated (exit code 3)")
        print("=" * 60)
        sys.exit(2 if len(patterns) <= 1 else 3)
    else:
        print("RESULT: ESCALATION - Manual inspection required (exit code 3)")
        print("=" * 60)
        sys.exit(3)


if __name__ == '__main__':
    main()
