#!/usr/bin/env python3
"""Generate ffmpeg filter graph for captions with timeline assembly."""

from typing import List, Dict, Any, Optional, Tuple


def escape_ffmpeg_text(text: str) -> str:
    """Escape special characters for ffmpeg drawtext filter.
    
    For filter_complex_script mode:
    - Single quotes inside single-quoted strings need special handling
    - Use '\'' to break out of quote, add literal quote, resume quote
    """
    text = text.replace('\\', '\\\\')
    text = text.replace("'", "'\\''")
    text = text.replace(':', '\\:')
    text = text.replace('%', '\\%')
    text = text.replace(',', '\\,')
    return text


def escape_filter_value(value: str) -> str:
    """Escape special characters for filter option values in script mode."""
    return value.replace(',', '\\,')


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


def build_timeline_assembly_filter(
    timeline_clips: List[Dict[str, Any]]
) -> Tuple[str, str, int]:
    """
    Build trim/concat filters to assemble video from playable segments.
    
    This transforms the raw video into the assembled timeline that matches
    the caption timing projection.
    
    Args:
        timeline_clips: Output from compute_timeline_clips(), sorted by timeline_position
        
    Returns:
        (video_filter_chain, audio_filter_chain, segment_count)
        video_filter_chain ends with [v_base]
        audio_filter_chain ends with [a_base]
    """
    all_segments = []
    for item in timeline_clips:
        for start, end in item['playable_segments']:
            all_segments.append((start, end))
    
    if not all_segments:
        return "[0:v]null[v_base]", "[0:a]anull[a_base]", 0
    
    if len(all_segments) == 1:
        start, end = all_segments[0]
        v_filter = f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[v_base]"
        a_filter = f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a_base]"
        return v_filter, a_filter, 1
    
    v_filters = []
    a_filters = []
    v_labels = []
    a_labels = []
    
    for i, (start, end) in enumerate(all_segments):
        v_label = f"v{i}"
        a_label = f"a{i}"
        v_labels.append(f"[{v_label}]")
        a_labels.append(f"[{a_label}]")
        
        v_filters.append(
            f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[{v_label}]"
        )
        a_filters.append(
            f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[{a_label}]"
        )
    
    n = len(all_segments)
    v_concat = f"{''.join(v_labels)}concat=n={n}:v=1:a=0[v_base]"
    a_concat = f"{''.join(a_labels)}concat=n={n}:v=0:a=1[a_base]"
    
    v_chain = ';\n'.join(v_filters + [v_concat])
    a_chain = ';\n'.join(a_filters + [a_concat])
    
    return v_chain, a_chain, n


def build_caption_filters(
    caption_events: List[Dict[str, Any]],
    caption_style: dict,
    font_path: str
) -> str:
    """Build caption overlay filters (drawbox + drawtext).
    
    These filters are applied AFTER timeline assembly.
    Input: [v_base]
    Output: filters that modify [v_base] and output to [vout]
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
            
            line_start = min(output_start + (w['start'] - event['original_start']) for w in line)
            line_end = max(output_start + (w['end'] - event['original_start']) for w in line)
            
            x_offset = 0
            line_text = ' '.join(w.get('text', '') for w in line)
            total_width = len(line_text) * char_width
            
            if background == 'dark_box':
                box_padding = 8
                box_w = int(total_width + box_padding * 2)
                box_h = font_size + box_padding * 2
                
                box_x_expr = f"(w-{box_w})/2"
                
                y_base = get_y_position(position, font_size)
                if line_y_offset > 0:
                    box_y_expr = f"{y_base}-{line_y_offset}-{box_padding}"
                else:
                    box_y_expr = f"{y_base}-{box_padding}"
                
                box_filter = f"drawbox=x={box_x_expr}:y={box_y_expr}:width={box_w}:height={box_h}:color=black@0.7:t=fill:enable='between(t,{line_start:.3f},{line_end:.3f})'"
                filters.append(box_filter)
            
            for word in line:
                text = word.get('text', '')
                color = word.get('color', default_color)
                
                word_output_start = output_start + (word['start'] - event['original_start'])
                
                escaped_text = escape_ffmpeg_text(text)
                ffmpeg_color = hex_to_ffmpeg(color)
                
                base_x = f"(w-{total_width:.0f})/2"
                if x_offset > 0:
                    x_expr = f"{base_x}+{x_offset:.0f}"
                else:
                    x_expr = base_x
                
                y_base = get_y_position(position, font_size)
                y_expr = f"{y_base}-{line_y_offset}"
                
                filter_str = f"drawtext=text='{escaped_text}':fontfile={font_path}:fontsize={font_size}:fontcolor={ffmpeg_color}:x={x_expr}:y={y_expr}"
                
                if background == 'outline':
                    filter_str += f":borderw=2:bordercolor=black"
                
                filter_str += f":enable='between(t,{word_output_start:.3f},{line_end:.3f})'"
                filters.append(filter_str)
                
                x_offset += len(text) * char_width + char_width
    
    if not filters:
        return ""
    
    return ",".join(filters)


def build_filter_graph(
    caption_events: List[Dict[str, Any]],
    caption_style: dict,
    font_path: str,
    input_video: str,
    output_video: str,
    timeline_clips: Optional[List[Dict[str, Any]]] = None
) -> str:
    """Build complete ffmpeg filter graph string.
    
    If timeline_clips is provided, builds:
      [0:v] -> trim/concat -> [v_base] -> captions -> [vout]
      [0:a] -> atrim/concat -> [a_base]
    
    If timeline_clips is None (legacy mode), builds:
      [0:v] -> captions -> output (no timeline assembly)
    """
    if timeline_clips:
        v_assembly, a_assembly, n_segs = build_timeline_assembly_filter(timeline_clips)
        
        caption_filters = build_caption_filters(caption_events, caption_style, font_path)
        
        if caption_filters:
            if n_segs == 1:
                filter_complex = f"{v_assembly},\n{caption_filters}[vout];\n{a_assembly}"
            else:
                filter_complex = f"{v_assembly};\n[v_base]{caption_filters}[vout];\n{a_assembly}"
        else:
            if n_segs == 1:
                filter_complex = f"{v_assembly};\n{a_assembly}"
            else:
                filter_complex = f"{v_assembly};\n{a_assembly}"
        
        return filter_complex
    
    caption_filters = build_caption_filters(caption_events, caption_style, font_path)
    
    if not caption_filters:
        return "copy"
    
    return caption_filters


def build_ffmpeg_command(
    input_video: str,
    output_video: str,
    filter_script_path: str,
    timeline_clips: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """Build complete ffmpeg command.
    
    If timeline_clips is provided, uses assembled output with explicit maps.
    If timeline_clips is None (legacy mode), uses simple output.
    """
    cmd = [
        'ffmpeg',
        '-y',
        '-i', input_video,
        '-filter_complex_script', filter_script_path,
    ]
    
    if timeline_clips:
        cmd.extend([
            '-map', '[vout]',
            '-map', '[a_base]',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            output_video
        ])
    else:
        cmd.extend([
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            output_video
        ])
    
    return cmd
