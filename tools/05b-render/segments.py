#!/usr/bin/env python3
"""Compute playable segments from trim + deleted_regions."""

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


def get_playable_segments(clip: dict) -> List[Tuple[float, float]]:
    """Return list of (start, end) tuples for playable video.
    
    Takes trim points and subtracts deleted regions to get final playable segments.
    
    INVARIANT: playable trim range must never exceed selected_segment bounds.
    If trim_start/trim_end exceed bounds, they are clamped and a warning is logged.
    """
    selected = clip.get('selected_segment', {})
    sel_start = selected.get('start', 0)
    sel_end = selected.get('end', 0)
    
    raw_trim_start = clip.get('trim_start')
    raw_trim_end = clip.get('trim_end')
    
    if raw_trim_start is not None:
        if raw_trim_start < sel_start or raw_trim_start > sel_end:
            logger.warning(
                f"Clip '{clip.get('id', '?')}' trim_start ({raw_trim_start:.3f}) "
                f"exceeds selected_segment bounds ({sel_start:.3f}-{sel_end:.3f}). "
                f"Clamping to {sel_start:.3f}."
            )
        trim_start = max(min(raw_trim_start, sel_end), sel_start)
    else:
        trim_start = sel_start
    
    if raw_trim_end is not None:
        if raw_trim_end < sel_start or raw_trim_end > sel_end:
            logger.warning(
                f"Clip '{clip.get('id', '?')}' trim_end ({raw_trim_end:.3f}) "
                f"exceeds selected_segment bounds ({sel_start:.3f}-{sel_end:.3f}). "
                f"Clamping to {sel_end:.3f}."
            )
        trim_end = min(max(raw_trim_end, sel_start), sel_end)
    else:
        trim_end = sel_end
    
    deleted = sorted(clip.get('deleted_regions', []), key=lambda r: r['start'])
    
    segments = [(trim_start, trim_end)]
    
    for del_region in deleted:
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


def compute_timeline_clips(project: dict) -> List[dict]:
    """Get clips sorted by timeline position with playable segments.
    
    Returns list of dicts with:
    - clip: original clip data
    - playable_segments: list of (start, end) tuples
    """
    clips = project.get('clips', [])
    
    timeline_clips = []
    for clip in clips:
        if not clip.get('enabled', True) or not clip.get('in_timeline', True):
            continue
        
        playable = get_playable_segments(clip)
        if playable:
            timeline_clips.append({
                'clip': clip,
                'playable_segments': playable,
                'timeline_position': clip.get('timeline_position', 0)
            })
    
    timeline_clips.sort(key=lambda x: x['timeline_position'])
    return timeline_clips


def get_total_duration(timeline_clips: List[dict]) -> float:
    """Calculate total duration of all playable segments."""
    total = 0.0
    for item in timeline_clips:
        for start, end in item['playable_segments']:
            total += (end - start)
    return total
