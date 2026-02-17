#!/usr/bin/env python3
"""Extract caption data with colors for rendering."""

from typing import List, Dict, Any, Optional, Tuple


def get_word_color(
    segment_index: int,
    word_index: int,
    word_colors: dict,
    default_color: str = '#ffffff'
) -> str:
    """Get color for a specific word."""
    key = f"{segment_index}_{word_index}"
    return word_colors.get(key, default_color)


def find_overlapping_segments(
    segments: List[dict],
    play_start: float,
    play_end: float
) -> List[Tuple[int, dict]]:
    """Find all transcript segments that overlap with playable segment.
    
    Returns list of (segment_index, segment_data) tuples sorted by segment start time.
    """
    overlapping = []
    for idx, seg in enumerate(segments):
        seg_start = seg.get('start', 0)
        seg_end = seg.get('end', 0)
        if seg_end > play_start and seg_start < play_end:
            overlapping.append((idx, seg))
    return overlapping


def get_words_in_range(
    segment: dict,
    start_time: float,
    end_time: float
) -> List[Dict[str, Any]]:
    """Get words that overlap with the given time range.
    
    Returns list of dicts with:
    - text: word text
    - start: word start time (source)
    - end: word end time (source)
    - word_index: index in segment
    """
    words = segment.get('words', [])
    result = []
    
    for idx, word in enumerate(words):
        word_start = word.get('start', 0)
        word_end = word.get('end', 0)
        
        if word_end > start_time and word_start < end_time:
            result.append({
                'text': word.get('text', ''),
                'start': word_start,
                'end': word_end,
                'word_index': idx
            })
    
    return result


def build_caption_events(
    project: dict,
    timeline_clips: List[dict],
    playable_segments: Optional[List[Tuple[float, float]]] = None
) -> List[Dict[str, Any]]:
    """Build list of caption events for rendering.
    
    Each event corresponds to a playable segment and contains:
    - segment_index: transcript segment index
    - clip_id: clip this belongs to
    - original_start: start in source video
    - original_end: end in source video
    - output_start: start in final output video (cumulative)
    - output_end: end in final output video (cumulative)
    - words: list of word data with colors (timestamps are source times)
    - text: full segment text
    """
    segments = project.get('transcript', {}).get('segments', [])
    word_colors = project.get('word_colors', {})
    caption_style = project.get('caption_style', {})
    default_color = caption_style.get('default_color', '#ffffff')
    
    events = []
    output_time = 0.0
    
    for seg_start, seg_end in playable_segments or []:
        seg_duration = seg_end - seg_start
        
        overlapping = find_overlapping_segments(segments, seg_start, seg_end)
        
        if not overlapping:
            events.append({
                'segment_index': -1,
                'clip_id': '',
                'original_start': seg_start,
                'original_end': seg_end,
                'output_start': output_time,
                'output_end': output_time + seg_duration,
                'words': [],
                'text': ''
            })
            output_time += seg_duration
            continue
        
        all_words = []
        for seg_idx, matching_segment in overlapping:
            words = get_words_in_range(matching_segment, seg_start, seg_end)
            for word in words:
                word['color'] = get_word_color(
                    seg_idx,
                    word['word_index'],
                    word_colors,
                    default_color
                )
            all_words.extend(words)
        
        all_words.sort(key=lambda w: w['start'])
        
        primary_segment_index = overlapping[0][0]
        primary_segment = overlapping[0][1]
        
        events.append({
            'segment_index': primary_segment_index,
            'clip_id': '',
            'original_start': seg_start,
            'original_end': seg_end,
            'output_start': output_time,
            'output_end': output_time + seg_duration,
            'words': all_words,
            'text': primary_segment.get('text', '')
        })
        
        output_time += seg_duration
    
    return events
