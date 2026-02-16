#!/usr/bin/env python3
"""Compute playable segments from trim + deleted_regions."""

from typing import List, Tuple


def get_playable_segments(clip: dict) -> List[Tuple[float, float]]:
    """Return list of (start, end) tuples for playable video.
    
    Takes trim points and subtracts deleted regions to get final playable segments.
    """
    trim_start = clip.get('trim_start', clip.get('selected_segment', {}).get('start', 0))
    trim_end = clip.get('trim_end', clip.get('selected_segment', {}).get('end', 0))
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
