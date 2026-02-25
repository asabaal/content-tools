#!/usr/bin/env python3
"""
Manual FFmpeg Proof Construction

Construct FFmpeg commands directly from authoritative pipeline data
without using existing command builders. This is a clean-room proof
that the render can faithfully represent the edited narrative.

Authoritative sources:
- Tool 02: project['transcript'] - reviewed text and word timing
- Tool 03: project['clips'] - selected segments
- Tool 04: project['clips'] with deleted_regions - assembly timing
- Tool 05: project['word_colors'], project['caption_style'] - styling
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set
from datetime import datetime


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def load_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# === Authoritative Data Loading ===

def load_authoritative_data(root: Path) -> Dict[str, Any]:
    """Load all authoritative sources from project."""
    project_path = root / 'data' / 'project.json'
    if not project_path.exists():
        raise FileNotFoundError(f"project.json not found at {project_path}")
    
    project = load_json(project_path)
    
    return {
        'transcript': project.get('transcript', {}),
        'clips': project.get('clips', []),
        'word_colors': project.get('word_colors', {}),
        'caption_style': project.get('caption_style', {}),
        'caption_breaks': project.get('caption_breaks', {}),
        'video_path': root / 'data' / 'video_combined.mp4'
    }


# === Playable Segment Computation (Tool 04 logic) ===

def compute_playable_segments(trim_start: float, trim_end: float,
                              deleted_regions: List[Dict]) -> List[Tuple[float, float]]:
    """
    Compute playable segments by subtracting deleted regions from trim range.
    This is the Tool 04 assembly timing logic.
    """
    segments = [(trim_start, trim_end)]
    
    for del_region in sorted(deleted_regions, key=lambda r: r['start']):
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


def get_clips_playable_segments(data: Dict) -> List[Dict]:
    """
    Get all playable segments from clips in timeline order.
    
    Returns list of dicts with:
    - clip_id, clip_name
    - playable_segments: [(start, end), ...]
    - segment_index: transcript segment index
    - original_video_id
    """
    clips = data['clips']
    result = []
    
    # Sort by timeline position
    sorted_clips = sorted(
        [c for c in clips if c.get('enabled', True) and c.get('in_timeline', True)],
        key=lambda c: c.get('timeline_position', 0)
    )
    
    for clip in sorted_clips:
        sel = clip.get('selected_segment', {})
        if not sel:
            continue
        
        trim_start = clip.get('trim_start', sel.get('start', 0))
        trim_end = clip.get('trim_end', sel.get('end', 0))
        deleted_regions = clip.get('deleted_regions', [])
        
        playable = compute_playable_segments(trim_start, trim_end, deleted_regions)
        
        result.append({
            'clip_id': clip.get('id', ''),
            'clip_name': clip.get('name', ''),
            'segment_index': sel.get('segment_index'),
            'original_video_id': sel.get('original_video_id', ''),
            'playable_segments': playable
        })
    
    return result


# === Surviving Word Computation ===

def compute_surviving_words(data: Dict) -> Tuple[List[Dict], float]:
    """
    Compute words that survive Tool 03 selection + Tool 04 deletions.
    
    This matches the logic in captions.py build_caption_events():
    - For each playable segment, find matching transcript segment by:
      1. Same original_video_id as clip's selected_segment
      2. Playable segment start falls within transcript segment bounds
    - Extract words that start within the playable segment
    
    Returns:
    - List of word dicts with output timing
    - Total output duration
    """
    transcript = data['transcript']
    segments = transcript.get('segments', [])
    clips_playable = get_clips_playable_segments(data)
    word_colors = data['word_colors']
    caption_breaks = data['caption_breaks']
    
    surviving_words = []
    output_time = 0.0
    
    for clip_info in clips_playable:
        original_video_id = clip_info['original_video_id']
        
        for play_start, play_end in clip_info['playable_segments']:
            play_duration = play_end - play_start
            
            # Find matching transcript segment (same logic as captions.py)
            matching_segment = None
            matching_seg_idx = -1
            for seg_idx, seg in enumerate(segments):
                if (seg.get('original_video_id') == original_video_id and
                    seg.get('start') <= play_start < seg.get('end')):
                    matching_segment = seg
                    matching_seg_idx = seg_idx
                    break
            
            if not matching_segment:
                # No matching segment - skip this playable segment (same as captions.py)
                output_time += play_duration
                continue
            
            # Extract words that start within playable range
            for word_idx, word in enumerate(matching_segment.get('words', [])):
                word_start = word.get('start', 0)
                word_end = word.get('end', 0)
                
                # Only include if word starts in playable range
                if play_start <= word_start < play_end:
                    # Calculate output timing
                    word_output_start = output_time + (word_start - play_start)
                    word_output_end = output_time + (min(word_end, play_end) - play_start)
                    
                    seg_idx = matching_seg_idx
                    
                    # Get color from styling
                    color_key = f"{seg_idx}_{word_idx}"
                    color = word_colors.get(color_key)
                    
                    # Check for caption break
                    seg_breaks = caption_breaks.get(str(seg_idx), [])
                    is_break = word_idx in seg_breaks
                    
                    surviving_words.append({
                        'text': word.get('text', ''),
                        'original_start': word_start,
                        'original_end': word_end,
                        'output_start': word_output_start,
                        'output_end': word_output_end,
                        'segment_index': seg_idx,
                        'word_index': word_idx,
                        'color': color,
                        'is_caption_break': is_break,
                        'clip_id': clip_info['clip_id']
                    })
            
            output_time += play_duration
    
    # Sort by output_start for proper ordering
    surviving_words.sort(key=lambda w: (w['output_start'], w['segment_index'], w['word_index']))
    
    return surviving_words, output_time


# === Caption Line Grouping ===

def group_words_into_lines(words: List[Dict], 
                           max_chars: int = 40,
                           min_gap: float = 0.3) -> List[Dict]:
    """
    Group words into caption lines based on timing gaps.
    
    Each line contains words that appear together on screen.
    """
    if not words:
        return []
    
    lines = []
    current_line = {
        'words': [words[0]],
        'output_start': words[0]['output_start'],
        'output_end': words[0]['output_end']
    }
    
    for word in words[1:]:
        # Check for explicit caption break
        prev_word = current_line['words'][-1]
        if prev_word.get('is_caption_break'):
            lines.append(current_line)
            current_line = {
                'words': [word],
                'output_start': word['output_start'],
                'output_end': word['output_end']
            }
            continue
        
        # Check for timing gap
        gap = word['output_start'] - current_line['output_end']
        if gap > min_gap:
            lines.append(current_line)
            current_line = {
                'words': [word],
                'output_start': word['output_start'],
                'output_end': word['output_end']
            }
        else:
            current_line['words'].append(word)
            current_line['output_end'] = max(current_line['output_end'], word['output_end'])
    
    lines.append(current_line)
    return lines


# === FFmpeg Text Escaping ===

def escape_ffmpeg_text(text: str) -> str:
    """
    Escape text for FFmpeg drawtext filter.
    Critical: apostrophes in words like "God's" must be escaped correctly.
    
    For filter_complex_script (file-based), we use single quotes for text
    and escape apostrophes with \\'
    """
    # Escape backslashes first
    text = text.replace('\\', '\\\\')
    # Escape apostrophes - for single-quoted text in filter
    text = text.replace("'", "\\'")
    return text


# === Filter Construction ===

def build_drawbox_filter(line: Dict, font_size: int, y_position: int) -> str:
    """
    Build drawbox filter for line background.
    
    Box spans from line start to line end, covers all words in line.
    """
    # Calculate box width based on total text length
    total_text = ' '.join(w['text'] for w in line['words'])
    # Approximate: font_size * 0.5 pixels per char, plus padding
    char_count = len(total_text)
    box_width = int(char_count * font_size * 0.5 + 20)
    box_height = font_size + 16
    
    output_start = line['output_start']
    output_end = line['output_end']
    
    return (
        f"drawbox=x=(w-{box_width})/2:y={y_position}:"
        f"width={box_width}:height={box_height}:"
        f"color=black@0.6:t=fill:"
        f"enable='between(t,{output_start:.3f},{output_end:.3f})'"
    )


def build_drawtext_filter(word: Dict, 
                          font_path: str,
                          font_size: int,
                          x_expr: str,
                          y_position: int,
                          line_end: float,
                          default_color: str) -> str:
    """
    Build drawtext filter for single word.
    
    Progressive reveal: word appears at its start, disappears at line end.
    """
    escaped_text = escape_ffmpeg_text(word['text'])
    color = word.get('color') or default_color
    
    # Word appears at its own start, disappears when line ends
    word_start = word['output_start']
    word_end = line_end
    
    return (
        f"drawtext=text='{escaped_text}':"
        f"fontfile={font_path}:"
        f"fontsize={font_size}:"
        f"fontcolor={color}:"
        f"x={x_expr}:"
        f"y={y_position}:"
        f"enable='between(t,{word_start:.3f},{word_end:.3f})'"
    )


def build_caption_filters(lines: List[Dict],
                          font_path: str,
                          caption_style: Dict,
                          default_y: int = 650) -> str:
    """
    Build all caption filters (drawbox + drawtext).
    
    Returns comma-separated filter chain.
    """
    font_size = 36
    if caption_style.get('font_size') == 'small':
        font_size = 28
    elif caption_style.get('font_size') == 'large':
        font_size = 44
    
    default_color = caption_style.get('default_color', '#ffffff')
    
    filters = []
    
    for line in lines:
        # Add drawbox for line background
        box_filter = build_drawbox_filter(line, font_size, default_y)
        filters.append(box_filter)
        
        # Calculate starting X position for words in this line
        total_text = ' '.join(w['text'] for w in line['words'])
        total_width = len(total_text) * font_size * 0.5
        
        # Position words - calculate x offset for each word
        x_offset = 0
        word_filters = []
        
        for word in line['words']:
            word_width = len(word['text']) * font_size * 0.5
            
            # Center the line, then offset by word position
            # x = (w - total_width) / 2 + x_offset
            if x_offset == 0:
                x_expr = f"(w-{int(total_width)})/2"
            else:
                x_expr = f"(w-{int(total_width)})/2+{int(x_offset)}"
            
            line_end = line['output_end']
            
            drawtext = build_drawtext_filter(
                word, font_path, font_size, x_expr, 
                default_y + 8, line_end, default_color
            )
            word_filters.append(drawtext)
            
            # Add space width for next word
            x_offset += word_width + font_size * 0.3
        
        filters.extend(word_filters)
    
    return ',\n'.join(filters)


def build_trim_concat_filters(clips_playable: List[Dict],
                               video_input: str = "0:v",
                               audio_input: str = "0:a") -> Tuple[str, str, int]:
    """
    Build trim and concat filters for video assembly.
    
    Returns:
    - Video filter chain ending with [v_base]
    - Audio filter chain ending with [a_base]
    - Number of segments
    """
    # Collect all playable segments from all clips
    all_segments = []
    for clip_info in clips_playable:
        all_segments.extend(clip_info['playable_segments'])
    
    # Sort by start time
    all_segments = sorted(all_segments, key=lambda s: s[0])
    
    if not all_segments:
        return "[0:v]null[v_base]", "[0:a]anull[a_base]", 0
    
    if len(all_segments) == 1:
        # Single segment - simple trim
        start, end = all_segments[0]
        v_filter = f"[{video_input}]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[v_base]"
        a_filter = f"[{audio_input}]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a_base]"
        return v_filter, a_filter, 1
    
    # Multiple segments - need concat
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
            f"[{video_input}]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS[{v_label}]"
        )
        a_filters.append(
            f"[{audio_input}]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[{a_label}]"
        )
    
    n = len(all_segments)
    v_concat = f"{''.join(v_labels)}concat=n={n}:v=1:a=0[v_base]"
    a_concat = f"{''.join(a_labels)}concat=n={n}:v=0:a=1[a_base]"
    
    v_chain = ';\n'.join(v_filters + [v_concat])
    a_chain = ';\n'.join(a_filters + [a_concat])
    
    return v_chain, a_chain, n


# === Full Command Construction ===

def build_full_ffmpeg_command(root: Path) -> Tuple[str, str, Dict]:
    """
    Build complete FFmpeg command for all surviving words.
    
    Returns:
    - command: full FFmpeg command string
    - filter_complex: the filter graph string
    - summary: dict with counts and durations
    """
    data = load_authoritative_data(root)
    
    # Compute surviving words
    words, total_duration = compute_surviving_words(data)
    
    # Group into lines
    lines = group_words_into_lines(words)
    
    # Build trim/concat filters
    clips_playable = get_clips_playable_segments(data)
    v_trim, a_trim, n_segments = build_trim_concat_filters(clips_playable)
    
    # Build caption filters
    font_path = root / 'tools' / '05b-render' / 'fonts' / 'Bangers-Regular.ttf'
    caption_filters = build_caption_filters(lines, str(font_path), data['caption_style'])
    
    # Combine all filters
    if n_segments <= 1:
        filter_complex = f"{v_trim},\n{caption_filters}[vout];\n{a_trim}"
    else:
        filter_complex = f"{v_trim};\n[v_base]{caption_filters}[vout];\n{a_trim}"
    
    # Build command
    video_path = data['video_path']
    filter_script_path = root / 'data' / 'output' / 'manual_proof_full_filter.txt'
    output_path = root / 'data' / 'output' / 'manual_proof_output.mp4'
    
    cmd = (
        f"ffmpeg -y "
        f"-i {video_path} "
        f"-filter_complex_script {filter_script_path} "
        f"-map '[vout]' -map '[a_base]' "
        f"-c:v libx264 -preset medium -crf 23 "
        f"-c:a aac -b:a 128k "
        f"{output_path}"
    )
    
    # Count filters
    total_filters = filter_complex.count('drawtext') + filter_complex.count('drawbox')
    
    summary = {
        'total_words': len(words),
        'total_playable_segments': n_segments,
        'total_lines': len(lines),
        'total_duration': total_duration,
        'total_filters': total_filters
    }
    
    return cmd, filter_complex, summary


# === Command File Generation ===

def generate_command_file(
    command: str,
    filter_content: str,
    output_path: Path,
    filter_path: Path,
    title: str,
    summary: Dict
) -> None:
    """
    Generate a file containing both the ffmpeg command and its filter script.
    """
    separator = "=" * 80
    
    # Build summary section based on available data
    summary_lines = []
    if 'total_words' in summary:
        summary_lines.append(f"Total surviving words: {summary['total_words']}")
    if 'total_playable_segments' in summary:
        summary_lines.append(f"Total playable segments: {summary['total_playable_segments']}")
    if 'total_lines' in summary:
        summary_lines.append(f"Total caption lines: {summary['total_lines']}")
    if 'total_duration' in summary:
        summary_lines.append(f"Total output duration: {summary['total_duration']:.2f}s")
    if 'word_count' in summary:
        summary_lines.append(f"Words: {summary['word_count']} ({', '.join(w['text'] for w in summary.get('words', []))})")
    if 'orig_start' in summary:
        summary_lines.append(f"Original video range: {summary['orig_start']:.3f}s - {summary['orig_end']:.3f}s")
    if 'duration' in summary:
        summary_lines.append(f"Output duration: {summary['duration']:.3f}s")
    
    summary_text = '\n'.join(f"  {line}" for line in summary_lines)
    
    content = f"""{separator}
MANUAL FFMPEG PROOF - {title}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{separator}

=== FFMPEG COMMAND ===
{command}

=== FILTER SCRIPT ({filter_path.name}) ===
{filter_content}

=== SUMMARY ===
{summary_text}

{separator}
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)


# === Minimal Command Construction (First Line Only) ===

def build_minimal_ffmpeg_command(root: Path) -> Tuple[str, str, Dict]:
    """
    Build minimal FFmpeg command for first caption line.
    
    Uses first contiguous caption line for simplicity and verifiability.
    This ensures all words are from the same time range in source video.
    """
    data = load_authoritative_data(root)
    
    # Compute all surviving words
    all_words, _ = compute_surviving_words(data)
    
    if not all_words:
        return "", "", {'error': 'No surviving words found'}
    
    # Group into lines first
    all_lines = group_words_into_lines(all_words)
    
    if not all_lines:
        return "", "", {'error': 'No caption lines found'}
    
    # Take first line only (contiguous words in output timeline)
    first_line = all_lines[0]
    first_line_words = first_line['words']
    
    # Find the ORIGINAL video time range for these words
    # Words in a line are contiguous in output, but may span playable segment boundaries
    # For simplicity, find min original_start and max original_end
    orig_start = min(w['original_start'] for w in first_line_words)
    orig_end = max(w['original_end'] for w in first_line_words)
    
    # The output time range for this line
    output_start = first_line['output_start']
    output_end = first_line['output_end']
    output_duration = output_end - output_start
    
    # When we trim from orig_start, the filter timeline starts at 0
    # So we need to adjust output times: filter_time = output_time - output_start + offset
    # But actually, we need to figure out where these words fall in the trimmed video
    
    # The trimmed video starts at orig_start and lasts for (orig_end - orig_start)
    # But the words have output times that assume full timeline compression
    # We need to recalculate: in the trimmed segment, what time does each word appear?
    
    # For a minimal proof, let's use a simpler approach:
    # - Trim the video to just cover these words' original time range
    # - Use the original word timing relative to trim point
    
    # Create adjusted words with timing relative to trim point
    adjusted_words = []
    for w in first_line_words:
        adjusted_words.append({
            **w,
            'output_start': w['original_start'] - orig_start,
            'output_end': w['original_end'] - orig_start
        })
    
    # Create single line with adjusted words
    adjusted_line = {
        'words': adjusted_words,
        'output_start': 0,
        'output_end': orig_end - orig_start
    }
    
    # Build trim filter
    trim_duration = orig_end - orig_start + 0.5
    trim_filter = f"[0:v]trim=start={orig_start:.3f}:end={orig_end + 0.5:.3f},setpts=PTS-STARTPTS[vt]"
    atrim_filter = f"[0:a]atrim=start={orig_start:.3f}:end={orig_end + 0.5:.3f},asetpts=PTS-STARTPTS[at]"
    
    # Build caption filters for single line
    font_path = root / 'tools' / '05b-render' / 'fonts' / 'Bangers-Regular.ttf'
    caption_filters = build_caption_filters([adjusted_line], str(font_path), data['caption_style'])
    
    # Combine
    filter_complex = f"{trim_filter};\n[vt]{caption_filters}[vout];\n{atrim_filter}"
    
    # Build command using -filter_complex_script
    video_path = data['video_path']
    filter_script_path = root / 'data' / 'output' / 'manual_proof_minimal_filter.txt'
    output_path = root / 'data' / 'output' / 'manual_proof_first10.mp4'
    
    cmd = (
        f"ffmpeg -y "
        f"-ss {orig_start:.3f} "
        f"-i {video_path} "
        f"-t {trim_duration:.3f} "
        f"-filter_complex_script {filter_script_path} "
        f"-map '[vout]' -map '[at]' "
        f"-c:v libx264 -preset medium -crf 23 "
        f"-c:a aac -b:a 128k "
        f"{output_path}"
    )
    
    summary = {
        'start_time': output_start,
        'end_time': output_end,
        'duration': output_duration,
        'words': first_line_words,
        'orig_start': orig_start,
        'orig_end': orig_end,
        'word_count': len(first_line_words)
    }
    
    return cmd, filter_complex, summary


# === Main Entry Point ===

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Manual FFmpeg proof construction')
    parser.add_argument('--project', '-p', type=str, help='Path to project root')
    args = parser.parse_args()
    
    root = Path(args.project) if args.project else get_project_root()
    
    # Ensure output directory exists
    output_dir = root / 'data' / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("MANUAL FFMPEG PROOF CONSTRUCTION")
    print("=" * 60)
    print()
    
    # Build full command
    print("Building full FFmpeg command...")
    full_cmd, full_filter, full_summary = build_full_ffmpeg_command(root)
    
    # Define file paths
    full_filter_path = root / 'data' / 'output' / 'manual_proof_full_filter.txt'
    full_command_path = root / 'data' / 'output' / 'manual_proof_full_command.txt'
    
    # Write full filter to file
    with open(full_filter_path, 'w', encoding='utf-8') as f:
        f.write(full_filter)
    print(f"Full filter written to: {full_filter_path}")
    
    # Generate full command file (command + filter)
    generate_command_file(
        command=full_cmd,
        filter_content=full_filter,
        output_path=full_command_path,
        filter_path=full_filter_path,
        title="Full Render",
        summary=full_summary
    )
    print(f"Full command file written to: {full_command_path}")
    
    # Build minimal command
    print("Building minimal FFmpeg command (first caption line)...")
    min_cmd, min_filter, min_summary = build_minimal_ffmpeg_command(root)
    
    # Define file paths
    min_filter_path = root / 'data' / 'output' / 'manual_proof_minimal_filter.txt'
    min_command_path = root / 'data' / 'output' / 'manual_proof_minimal_command.txt'
    
    # Write minimal filter to file
    with open(min_filter_path, 'w', encoding='utf-8') as f:
        f.write(min_filter)
    print(f"Minimal filter written to: {min_filter_path}")
    
    # Generate minimal command file (command + filter)
    generate_command_file(
        command=min_cmd,
        filter_content=min_filter,
        output_path=min_command_path,
        filter_path=min_filter_path,
        title="Minimal (First Caption Line)",
        summary=min_summary
    )
    print(f"Minimal command file written to: {min_command_path}")
    
    # Print summary
    print()
    print("=== SUMMARY ===")
    print(f"Total surviving words: {full_summary['total_words']}")
    print(f"Total playable segments: {full_summary['total_playable_segments']}")
    print(f"Total caption lines: {full_summary['total_lines']}")
    print(f"Total output duration: {full_summary['total_duration']:.2f}s")
    print(f"Total filter count: {full_summary['total_filters']}")
    
    print()
    print("=== FIRST CAPTION LINE ===")
    print(f"Word count: {min_summary.get('word_count', 0)}")
    print(f"Output time range: {min_summary['start_time']:.3f}s - {min_summary['end_time']:.3f}s")
    print(f"Duration: {min_summary['duration']:.3f}s")
    print(f"Original video range: {min_summary['orig_start']:.3f}s - {min_summary['orig_end']:.3f}s")
    print(f"Words: {[w['text'] for w in min_summary['words']]}")
    
    # Print combined command files
    print()
    print("=" * 80)
    print("MINIMAL COMMAND AND FILTER")
    print("=" * 80)
    with open(min_command_path, 'r', encoding='utf-8') as f:
        print(f.read())
    
    print()
    print("=" * 80)
    print("FULL COMMAND AND FILTER")
    print("=" * 80)
    print(f"(Full output in: {full_command_path})")
    print()
    print("=== FFMPEG COMMAND ===")
    print(full_cmd)
    print()
    print(f"=== FILTER SCRIPT ({full_filter_path.name}) ===")
    print(f"(Filter script has {len(full_filter.splitlines())} lines, see {full_filter_path})")
    print()
    print("First 10 lines of filter:")
    for line in full_filter.splitlines()[:10]:
        print(f"  {line}")
    print("  ...")
    
    print()
    print("=== OUTPUT FILES ===")
    print(f"Full command:    {full_command_path}")
    print(f"Full filter:     {full_filter_path}")
    print(f"Minimal command: {min_command_path}")
    print(f"Minimal filter:  {min_filter_path}")
    
    print()
    print("=" * 60)


if __name__ == '__main__':
    main()
