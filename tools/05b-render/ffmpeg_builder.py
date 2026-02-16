#!/usr/bin/env python3
"""Generate ffmpeg filter graph for captions."""

import os
from typing import List, Dict, Any, Optional


def escape_ffmpeg_text(text: str) -> str:
    """Escape special characters for ffmpeg drawtext filter."""
    text = text.replace('\\', '\\\\')
    text = text.replace("'", "\\'")
    text = text.replace(':', '\\:')
    text = text.replace('%', '\\%')
    return text


def hex_to_ffmpeg(hex_color: str) -> str:
    """Convert hex color to ffmpeg format (without #)."""
    return hex_color.lstrip('#')


def get_font_size(size_name: str) -> int:
    """Get pixel size for font size name."""
    sizes = {
        'small': 28,
        'medium': 36,
        'large': 48
    }
    return sizes.get(size_name, 36)


def get_y_position(position_name: str, font_size: int) -> str:
    """Get y position expression for drawtext."""
    padding = 20
    box_height = font_size + 20
    
    if position_name == 'bottom':
        return f"h-{padding + box_height}"
    elif position_name == 'lower_third':
        return f"h-{padding + box_height + 40}"
    else:
        return f"(h-text_h)/2"


def build_drawtext_filter(
    text: str,
    start_time: float,
    end_time: float,
    output_start: float,
    font_path: str,
    font_size: int,
    color: str,
    position: str,
    background: str,
    index: int
) -> str:
    """Build a single drawtext filter string."""
    escaped_text = escape_ffmpeg_text(text)
    ffmpeg_color = hex_to_ffmpeg(color)
    y_pos = get_y_position(position, font_size)
    
    enable_expr = f"between(t,{output_start:.3f},{end_time:.3f})"
    
    filter_str = f"drawtext=text='{escaped_text}':fontfile='{font_path}':fontsize={font_size}:fontcolor={ffmpeg_color}:x=(w-text_w)/2:y={y_pos}"
    
    if background == 'dark_box':
        filter_str += f":box=1:boxcolor=black@0.7:boxborderw=10"
    elif background == 'outline':
        filter_str += f":borderw=2:bordercolor=black"
    
    filter_str += f":enable='{enable_expr}'"
    
    return filter_str


def build_colored_word_filters(
    words: List[Dict[str, Any]],
    output_start: float,
    font_path: str,
    font_size: int,
    position: str,
    background: str,
    base_index: int
) -> List[str]:
    """Build drawtext filters for words with individual colors.
    
    This creates filters that show all words in a line, each with its own color.
    """
    filters = []
    
    if not words:
        return filters
    
    char_width = font_size * 0.5
    words_with_offsets = []
    x_offset = 0
    
    for word in words:
        words_with_offsets.append({
            **word,
            'x_offset': x_offset
        })
        x_offset += len(word.get('text', '')) * char_width + char_width
    
    total_width = max(0, x_offset - char_width)
    start_x = f"(w-{total_width})/2"
    
    y_pos = get_y_position(position, font_size)
    
    for i, word in enumerate(words_with_offsets):
        text = word.get('text', '')
        color = word.get('color', '#ffffff')
        word_start = word.get('start', 0)
        word_end = word.get('end', 0)
        
        escaped_text = escape_ffmpeg_text(text)
        ffmpeg_color = hex_to_ffmpeg(color)
        
        x_expr = f"{start_x}+{word['x_offset']:.0f}"
        
        enable_expr = f"between(t,{output_start:.3f},{output_start + (word_end - word_start):.3f})"
        
        filter_str = f"drawtext=text='{escaped_text}':fontfile='{font_path}':fontsize={font_size}:fontcolor={ffmpeg_color}:x={x_expr}:y={y_pos}"
        
        if background == 'dark_box':
            filter_str += f":box=1:boxcolor=black@0.7:boxborderw=5"
        elif background == 'outline':
            filter_str += f":borderw=2:bordercolor=black"
        
        filter_str += f":enable='{enable_expr}'"
        
        filters.append(filter_str)
    
    return filters


def build_segment_caption_filter(
    event: Dict[str, Any],
    font_path: str,
    caption_style: dict,
    index: int
) -> Optional[str]:
    """Build caption filter for a segment event."""
    words = event.get('words', [])
    if not words:
        return None
    
    font_size = get_font_size(caption_style.get('font_size', 'medium'))
    position = caption_style.get('position', 'lower_third')
    background = caption_style.get('background', 'dark_box')
    
    output_start = event['output_start']
    output_end = event['output_end']
    
    filter_str = f"drawtext=text='':fontfile='{font_path}':fontsize={font_size}:fontcolor=white:x=(w-text_w)/2:y={get_y_position(position, font_size)}"
    filter_str += f":enable='between(t,{output_start:.3f},{output_end:.3f})'"
    
    return filter_str


def build_filter_graph(
    caption_events: List[Dict[str, Any]],
    caption_style: dict,
    font_path: str,
    input_video: str,
    output_video: str
) -> str:
    """Build complete ffmpeg filter graph string.
    
    For now, this builds a simple approach:
    - One drawtext per word that shows during its time
    - Words are positioned to form lines
    """
    filters = []
    
    font_size = get_font_size(caption_style.get('font_size', 'medium'))
    position = caption_style.get('position', 'lower_third')
    background = caption_style.get('background', 'dark_box')
    default_color = caption_style.get('default_color', '#ffffff')
    
    for event in caption_events:
        words = event.get('words', [])
        output_start = event['output_start']
        
        if not words:
            continue
        
        words_sorted = sorted(words, key=lambda w: w['start'])
        
        lines = []
        current_line = []
        line_width = 0
        max_width = 800
        char_width = font_size * 0.5
        
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
            line_y_offset = line_idx * (font_size + 10)
            
            x_offset = 0
            line_text = ' '.join(w.get('text', '') for w in line)
            total_width = len(line_text) * char_width
            
            for word in line:
                text = word.get('text', '')
                color = word.get('color', default_color)
                word_rel_start = word['start'] - event['original_start']
                word_rel_end = word['end'] - event['original_start']
                
                word_output_start = output_start + word_rel_start
                word_output_end = output_start + word_rel_end
                
                escaped_text = escape_ffmpeg_text(text)
                ffmpeg_color = hex_to_ffmpeg(color)
                
                base_x = f"(w-{total_width:.0f})/2"
                if x_offset > 0:
                    x_expr = f"{base_x}+{x_offset:.0f}"
                else:
                    x_expr = base_x
                
                y_base = get_y_position(position, font_size)
                y_expr = f"{y_base}-{line_y_offset}"
                
                filter_str = f"drawtext=text='{escaped_text}':fontfile='{font_path}':fontsize={font_size}:fontcolor={ffmpeg_color}:x={x_expr}:y={y_expr}"
                
                if background == 'dark_box':
                    filter_str += f":box=1:boxcolor=black@0.7:boxborderw=8"
                elif background == 'outline':
                    filter_str += f":borderw=2:bordercolor=black"
                
                filter_str += f":enable='between(t,{word_output_start:.3f},{word_output_end:.3f})'"
                filters.append(filter_str)
                
                x_offset += len(text) * char_width + char_width
    
    if not filters:
        return "copy"
    
    return ",".join(filters)


def build_ffmpeg_command(
    input_video: str,
    output_video: str,
    filter_graph: str,
    copy_audio: bool = True
) -> List[str]:
    """Build complete ffmpeg command."""
    cmd = [
        'ffmpeg',
        '-y',
        '-i', input_video,
        '-vf', filter_graph,
    ]
    
    if copy_audio:
        cmd.extend(['-c:a', 'copy'])
    
    cmd.extend([
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        output_video
    ])
    
    return cmd
