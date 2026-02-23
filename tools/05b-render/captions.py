#!/usr/bin/env python3
"""Extract caption data with colors for rendering."""

from typing import List, Dict, Any, Optional


def get_word_color(
    segment_index: int,
    word_index: int,
    word_colors: dict,
    default_color: str = '#ffffff'
) -> str:
    """Get color for a specific word."""
    key = f"{segment_index}_{word_index}"
    return word_colors.get(key, default_color)


def get_words_in_range(
    segment: dict,
    start_time: float,
    end_time: float
) -> List[Dict[str, Any]]:
    """Get words that overlap with the given time range.
    
    Returns list of dicts with:
    - text: word text
    - start: word start time
    - end: word end time
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
    timeline_clips: List[dict]
) -> List[Dict[str, Any]]:
    """Build list of caption events for rendering.
    
    Each event contains:
    - segment_index: transcript segment index
    - clip_id: clip this belongs to
    - original_start: start in original video
    - original_end: end in original video
    - output_start: start in output video (computed later)
    - output_end: end in output video (computed later)
    - words: list of word data with colors
    """
    segments = project.get('transcript', {}).get('segments', [])
    word_colors = project.get('word_colors', {})
    caption_style = project.get('caption_style', {})
    default_color = caption_style.get('default_color', '#ffffff')
    
    events = []
    output_time = 0.0
    
    for item in timeline_clips:
        clip = item['clip']
        clip_id = clip.get('id', '')
        selected = clip.get('selected_segment', {})
        original_video_id = selected.get('original_video_id', '')
        
        for seg_start, seg_end in item['playable_segments']:
            seg_duration = seg_end - seg_start
            
            matching_segment = None
            segment_index = -1
            for idx, seg in enumerate(segments):
                if (seg.get('original_video_id') == original_video_id and
                    seg.get('start') <= seg_start < seg.get('end')):
                    matching_segment = seg
                    segment_index = idx
                    break
            
            if not matching_segment:
                continue
            
            words = get_words_in_range(matching_segment, seg_start, seg_end)
            
            for word in words:
                word['color'] = get_word_color(
                    segment_index,
                    word['word_index'],
                    word_colors,
                    default_color
                )
            
            events.append({
                'segment_index': segment_index,
                'clip_id': clip_id,
                'original_start': seg_start,
                'original_end': seg_end,
                'output_start': output_time,
                'output_end': output_time + seg_duration,
                'words': words,
                'text': matching_segment.get('text', '')
            })
            
            output_time += seg_duration
    
    return events


def group_words_by_time(
    words: List[Dict[str, Any]],
    min_gap: float = 0.3
) -> List[Dict[str, Any]]:
    """Group words that appear together on screen.
    
    Returns list of groups, each with:
    - words: list of word data
    - start: group start time
    - end: group end time
    """
    if not words:
        return []
    
    words = sorted(words, key=lambda w: w['start'])
    groups = []
    current_group = {
        'words': [words[0]],
        'start': words[0]['start'],
        'end': words[0]['end']
    }
    
    for word in words[1:]:
        if word['start'] - current_group['end'] < min_gap:
            current_group['words'].append(word)
            current_group['end'] = max(current_group['end'], word['end'])
        else:
            groups.append(current_group)
            current_group = {
                'words': [word],
                'start': word['start'],
                'end': word['end']
            }
    
    groups.append(current_group)
    return groups
