#!/usr/bin/env python3
"""Generate ffmpeg filter graph for captions."""

from typing import List, Dict, Any, Optional, Tuple


VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920


def escape_ffmpeg_text(text: str) -> str:
    """Escape special characters for ffmpeg drawtext filter.
    
    When text is in single quotes, most chars are safe.
    Only escape single quotes by closing/reopening.
    """
    text = text.replace("'", "'\\''")
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
    """Get y position for drawtext (explicit pixel value for vertical video)."""
    padding = 20
    box_height = font_size + 20
    
    if position_name == 'bottom':
        return str(VIDEO_HEIGHT - padding - box_height)
    elif position_name == 'lower_third':
        return str(VIDEO_HEIGHT - padding - box_height - 40)
    else:
        return f"({VIDEO_HEIGHT}-text_h)/2"


def build_segment_filter_chain(
    segment_idx: int,
    source_start: float,
    source_end: float,
    caption_event: Dict[str, Any],
    font_path: str,
    caption_style: dict
) -> Tuple[str, str]:
    """Build filter chain for one segment: trim -> setpts -> drawtext(s).
    
    Returns (video_chain, audio_chain) strings.
    """
    font_size = get_font_size(caption_style.get('font_size', 'medium'))
    position = caption_style.get('position', 'lower_third')
    background = caption_style.get('background', 'dark_box')
    default_color = caption_style.get('default_color', '#ffffff')
    
    video_label = f"v{segment_idx}"
    audio_label = f"a{segment_idx}"
    
    video_parts = [f"[0:v]trim=start={source_start:.3f}:end={source_end:.3f},setpts=PTS-STARTPTS"]
    
    words = caption_event.get('words', [])
    if words:
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
        
        original_start = caption_event['original_start']
        
        for line_idx, line in enumerate(lines):
            line_y_offset = line_idx * (font_size + 10)
            
            x_offset = 0
            line_text = ' '.join(w.get('text', '') for w in line)
            total_width = len(line_text) * char_width
            
            for word in line:
                text = word.get('text', '')
                color = word.get('color', default_color)
                
                word_local_start = word['start'] - original_start
                word_local_end = word['end'] - original_start
                
                escaped_text = escape_ffmpeg_text(text)
                ffmpeg_color = hex_to_ffmpeg(color)
                
                base_x = f"({VIDEO_WIDTH}-{total_width:.0f})/2"
                if x_offset > 0:
                    x_expr = f"{base_x}+{x_offset:.0f}"
                else:
                    x_expr = base_x
                
                y_base = get_y_position(position, font_size)
                y_expr = f"{y_base}-{line_y_offset}"
                
                drawtext = f"drawtext=text='{escaped_text}':fontfile={font_path}:fontsize={font_size}:fontcolor={ffmpeg_color}:x={x_expr}:y={y_expr}"
                
                if background == 'dark_box':
                    drawtext += f":box=1:boxcolor=black@0.7:boxborderw=8"
                elif background == 'outline':
                    drawtext += f":borderw=2:bordercolor=black"
                
                drawtext += f":enable='between(t\\,{word_local_start:.3f}\\,{word_local_end:.3f})'"
                video_parts.append(drawtext)
                
                x_offset += len(text) * char_width + char_width
    
    video_chain = ",".join(video_parts) + f"[{video_label}]"
    
    audio_chain = f"[0:a]atrim=start={source_start:.3f}:end={source_end:.3f},asetpts=PTS-STARTPTS[{audio_label}]"
    
    return video_chain, audio_chain


def build_filter_graph(
    caption_events: List[Dict[str, Any]],
    caption_style: dict,
    font_path: str,
    playable_segments: List[Tuple[float, float]]
) -> str:
    """Build complete ffmpeg filter graph with trim/setpts/drawtext/concat.
    
    Structure:
    [0:v]trim=start:end,setpts,drawtext=...[v0];
    [0:a]atrim=start:end,asetpts[a0];
    [0:v]trim=start:end,setpts,drawtext=...[v1];
    [0:a]atrim=start:end,asetpts[a1];
    ...[v0][a0][v1][a1]...concat=n=N:v=1:a=1[outv][outa]
    """
    if not playable_segments:
        return "copy"
    
    if len(playable_segments) != len(caption_events):
        pass
    
    video_chains = []
    audio_chains = []
    video_labels = []
    audio_labels = []
    
    for idx, (seg_start, seg_end) in enumerate(playable_segments):
        caption_event = caption_events[idx] if idx < len(caption_events) else {'words': [], 'original_start': seg_start}
        
        video_chain, audio_chain = build_segment_filter_chain(
            idx,
            seg_start,
            seg_end,
            caption_event,
            font_path,
            caption_style
        )
        
        video_chains.append(video_chain)
        audio_chains.append(audio_chain)
        video_labels.append(f"v{idx}")
        audio_labels.append(f"a{idx}")
    
    all_chains = video_chains + audio_chains
    filter_parts = [chain.rstrip(']').replace('[0:v]', '[0:v]', 1).replace('[0:a]', '[0:a]', 1) for chain in all_chains]
    
    filter_parts = []
    for i, (vc, ac) in enumerate(zip(video_chains, audio_chains)):
        filter_parts.append(vc)
        filter_parts.append(ac)
    
    num_segments = len(playable_segments)
    concat_input_labels = "".join(f"[{v}][{a}]" for v, a in zip(video_labels, audio_labels))
    concat_filter = f"{concat_input_labels}concat=n={num_segments}:v=1:a=1[outv][outa]"
    filter_parts.append(concat_filter)
    
    return ";\n".join(filter_parts)


def build_ffmpeg_command(
    input_video: str,
    output_video: str,
    filter_graph: str,
    use_filter_script: bool = True
) -> Tuple[List[str], Optional[str]]:
    """Build ffmpeg command with filter_complex.
    
    Returns (command, filter_file_path) - filter_file_path is set if use_filter_script is True.
    """
    cmd = [
        'ffmpeg',
        '-y',
        '-i', input_video,
    ]
    
    filter_file = None
    if use_filter_script:
        import tempfile
        import os
        filter_file = tempfile.mktemp(suffix='.txt', prefix='ffmpeg_filter_')
        with open(filter_file, 'w') as f:
            f.write(filter_graph)
        cmd.extend(['-filter_complex_script', filter_file])
    else:
        cmd.extend(['-filter_complex', filter_graph])
    
    cmd.extend([
        '-map', '[outv]',
        '-map', '[outa]',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'aac',
        output_video
    ])
    
    return cmd, filter_file
