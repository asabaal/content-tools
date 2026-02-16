#!/usr/bin/env python3
"""Generate SRT subtitle file."""

from typing import List, Dict, Any


def format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def compress_timestamps(
    events: List[Dict[str, Any]],
    min_duration: float = 1.0,
    max_duration: float = 4.0,
    gap_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """Compress word timestamps into subtitle blocks.
    
    Groups words into reasonable subtitle blocks:
    - Minimum duration per block
    - Maximum duration per block
    - Merge short gaps
    """
    all_words = []
    
    for event in events:
        output_start = event['output_start']
        original_start = event['original_start']
        
        for word in event.get('words', []):
            word_rel_start = word['start'] - original_start
            word_rel_end = word['end'] - original_start
            
            all_words.append({
                'text': word.get('text', ''),
                'start': output_start + word_rel_start,
                'end': output_start + word_rel_end
            })
    
    if not all_words:
        return []
    
    blocks = []
    current_block = {
        'text': all_words[0]['text'],
        'start': all_words[0]['start'],
        'end': all_words[0]['end']
    }
    
    for word in all_words[1:]:
        gap = word['start'] - current_block['end']
        potential_duration = word['end'] - current_block['start']
        
        if gap < gap_threshold and potential_duration < max_duration:
            current_block['text'] += ' ' + word['text']
            current_block['end'] = word['end']
        else:
            if current_block['end'] - current_block['start'] < min_duration:
                current_block['end'] = current_block['start'] + min_duration
            
            blocks.append(current_block)
            current_block = {
                'text': word['text'],
                'start': word['start'],
                'end': word['end']
            }
    
    if current_block['end'] - current_block['start'] < min_duration:
        current_block['end'] = current_block['start'] + min_duration
    blocks.append(current_block)
    
    return blocks


def generate_srt(
    events: List[Dict[str, Any]],
    output_path: str
) -> None:
    """Generate SRT file from caption events."""
    blocks = compress_timestamps(events)
    
    lines = []
    for i, block in enumerate(blocks, 1):
        lines.append(str(i))
        lines.append(f"{format_srt_time(block['start'])} --> {format_srt_time(block['end'])}")
        lines.append(block['text'])
        lines.append('')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def generate_srt_content(events: List[Dict[str, Any]]) -> str:
    """Generate SRT content string from caption events."""
    blocks = compress_timestamps(events)
    
    lines = []
    for i, block in enumerate(blocks, 1):
        lines.append(str(i))
        lines.append(f"{format_srt_time(block['start'])} --> {format_srt_time(block['end'])}")
        lines.append(block['text'])
        lines.append('')
    
    return '\n'.join(lines)
