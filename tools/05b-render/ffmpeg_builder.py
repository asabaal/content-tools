#!/usr/bin/env python3
"""Generate ffmpeg commands for segmented caption rendering."""

from pathlib import Path
from typing import List, Dict, Any, Optional


def escape_ffmpeg_text(text: str) -> str:
    """Escape special characters for ffmpeg drawtext filter.
    
    For filter_complex_script mode with single-quoted text values,
    we use a workaround for apostrophes: replace straight quote (U+0027)
    with right single quotation mark (U+2019) which looks identical but
    doesn't conflict with the quote delimiter.
    """
    text = text.replace("'", "\u2019")
    return text


def escape_filter_value(value: str) -> str:
    """Escape special characters for filter option values in script mode."""
    return value.replace(',', '\\,')


def hex_to_ffmpeg(hex_color: str) -> str:
    """Convert hex color to ffmpeg format (without #)."""
    return hex_color.lstrip('#')


def get_font_size(size_name: str) -> int:
    """Get pixel size for font size name.
    
    Scales web app CSS sizes to match visual appearance at full render resolution.
    
    Analysis from reference screenshot (in-app-screenshot-line1.png):
    - Reference is 398x715 showing web app preview
    - Web app shows 1080x1920 video scaled down to preview
    - Visual analysis: font height is ~8.3% of frame (160px in 1920px frame)
    - This requires approximately 120pt at full 1080p resolution
    
    Correct scaling to match web app visual appearance:
    """
    sizes = {
        'small': 81,
        'medium': 108,
        'large': 135
    }
    return sizes.get(size_name, 120)


def get_y_position(position_name: str, font_size: int) -> int:
    """Get y position in pixels for drawtext.
    
    Returns actual pixel value instead of expression,
    since drawbox doesn't properly evaluate expressions in filter_complex_script mode.
    """
    VIDEO_HEIGHT = 1920
    padding = 20
    box_height = font_size + 20
    
    if position_name == 'bottom':
        return int(VIDEO_HEIGHT * 0.92)
    elif position_name == 'lower_third':
        return int(VIDEO_HEIGHT * 0.85)
    else:
        return VIDEO_HEIGHT // 2


def build_caption_filters(
    caption_events: List[Dict[str, Any]],
    caption_style: dict,
    font_path: str,
    caption_breaks: Optional[Dict[str, List[int]]] = None
) -> str:
    """Build caption overlay filters (drawbox + drawtext).
    
    Args:
        caption_events: List of caption events with words
        caption_style: Style settings (font_size, position, etc.)
        font_path: Path to font file
        caption_breaks: Dict mapping segment_index to list of word indices where lines break
                       e.g., {"0": [3, 5]} means segment 0 breaks after word indices 3 and 5
    
    Returns:
        Comma-separated filter string, or empty string if no captions
    """
    VIDEO_WIDTH = 1080
    VIDEO_HEIGHT = 1920
    
    filters = []
    
    font_size = get_font_size(caption_style.get('font_size', 'medium'))
    position = caption_style.get('position', 'lower_third')
    background = caption_style.get('background', 'dark_box')
    default_color = caption_style.get('default_color', '#ffffff')
    
    for event in caption_events:
        words = event.get('words', [])
        output_start = event['output_start']
        segment_index = event.get('segment_index', -1)
        
        if not words:
            continue
        
        words_sorted = sorted(words, key=lambda w: w['start'])
        char_width = font_size * 0.4
        
        seg_breaks = []
        if caption_breaks:
            seg_breaks = caption_breaks.get(str(segment_index), [])
        
        if seg_breaks:
            lines = []
            current_line = []
            for i, word in enumerate(words_sorted):
                current_line.append(word)
                if i in seg_breaks:
                    lines.append(current_line)
                    current_line = []
            if current_line:
                lines.append(current_line)
        else:
            lines = []
            current_line = []
            line_width = 0
            max_width = 800
            
            for word in words_sorted:
                word_width = len(word.get('text', '')) * char_width + char_width
                if line_width + word_width > max_width and current_line:
                    lines.append(current_line)
                    current_line = []
                    line_width = 0
                current_line.append(word)
                line_width += word_width
            
            if current_line:
                lines.append(current_line)
        
        for line_idx, line in enumerate(lines):
            line_y_offset = 0
            
            line_start = min(output_start + (word['start'] - event['original_start']) for word in line)
            line_end = max(output_start + (word['end'] - event['original_start']) for word in line)
            
            x_offset = 0
            line_text = ' '.join(word.get('text', '') for word in line)
            total_width = len(line_text) * char_width
            
            if background == 'dark_box':
                box_padding = 8
                box_w = int(total_width + box_padding * 2)
                box_h = font_size + box_padding * 2
                
                box_x = (VIDEO_WIDTH - box_w) // 2
                
                y_base = get_y_position(position, font_size)
                box_y = y_base - box_padding
                
                box_filter = f"drawbox=x={box_x}:y={box_y}:width={box_w}:height={box_h}:color=black@0.7:t=fill:enable='between(t,{line_start:.3f},{line_end:.3f})'"
                filters.append(box_filter)
            
            for word in line:
                text = word.get('text', '')
                color = word.get('color', default_color)
                
                word_output_start = output_start + (word['start'] - event['original_start'])
                
                escaped_text = escape_ffmpeg_text(text)
                ffmpeg_color = hex_to_ffmpeg(color)
                
                base_x = (VIDEO_WIDTH - int(total_width)) // 2
                if x_offset > 0:
                    x_pixel = base_x + int(x_offset)
                else:
                    x_pixel = base_x
                
                y_base = get_y_position(position, font_size)
                y_pixel = y_base
                
                filter_str = f"drawtext=text='{escaped_text}':fontfile={font_path}:fontsize={font_size}:fontcolor={ffmpeg_color}:x={x_pixel}:y={y_pixel}"
                
                if background == 'outline':
                    filter_str += f":borderw=2:bordercolor=black"
                
                filter_str += f":enable='between(t,{word_output_start:.3f},{line_end:.3f})'"
                filters.append(filter_str)
                
                x_offset += len(text) * char_width + char_width
    
    if not filters:
        return ""
    
    return ",".join(filters)


def build_segment_render_command(
    input_video: str,
    output_video: str,
    seg_start: float,
    seg_end: float,
    caption_events: List[Dict[str, Any]],
    caption_style: dict,
    font_path: str,
    caption_breaks: Optional[Dict[str, List[int]]] = None,
    filter_script_path: Optional[str] = None
) -> List[str]:
    """Build ffmpeg command for rendering a single segment with captions.
    
    Uses -ss before -i for fast seeking, then applies captions to trimmed segment.
    Always uses -filter_complex_script to avoid quote escaping issues.
    
    Args:
        input_video: Path to source video
        output_video: Path for output segment file
        seg_start: Start time in source video (seconds)
        seg_end: End time in source video (seconds)
        caption_events: Caption events for THIS segment only (with output_start=0)
        caption_style: Style settings
        font_path: Path to font file
        caption_breaks: Line break mappings
        filter_script_path: Path to save filter script (REQUIRED if captions exist)
    
    Returns:
        List of command arguments for subprocess
    """
    caption_filters = build_caption_filters(
        caption_events, caption_style, font_path, caption_breaks
    )
    
    duration = seg_end - seg_start
    
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(seg_start),
        '-i', input_video,
        '-t', str(duration),
    ]
    
    if caption_filters:
        if not filter_script_path:
            raise ValueError("filter_script_path is required when caption_filters exist")
        
        filter_graph = f"[0:v]setpts=PTS-STARTPTS,{caption_filters}[vout];[0:a]asetpts=PTS-STARTPTS[aout]"
        
        with open(filter_script_path, 'w') as f:
            f.write(filter_graph)
        
        cmd.extend([
            '-filter_complex_script', filter_script_path,
            '-map', '[vout]',
            '-map', '[aout]',
        ])
    
    cmd.extend([
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '128k',
        output_video
    ])
    
    return cmd


def build_concat_command(
    concat_list_path: str,
    output_video: str
) -> List[str]:
    """Build ffmpeg command to concatenate segments with re-encode.
    
    Args:
        concat_list_path: Path to concat list file
        output_video: Path for final output video
    
    Returns:
        List of command arguments for subprocess
    """
    return [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_list_path,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        output_video
    ]
