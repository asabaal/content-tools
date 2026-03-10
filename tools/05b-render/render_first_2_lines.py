#!/usr/bin/env python3
"""Render first 2 caption lines (segment 0) using two-pass method."""

import subprocess
import sys
from pathlib import Path

from segments import compute_timeline_clips, get_total_duration
from captions import build_caption_events
from ffmpeg_builder import (
    build_pass2_caption_filter,
    build_pass1_assembly_filter,
    build_pass1_command,
    build_pass2_command
)
from srt import generate_srt
from render import load_project, get_project_root


def main():
    root = get_project_root()
    input_video = root / 'data' / 'video_combined.mp4'
    output_dir = root / 'data' / 'output'
    assembled_video = output_dir / 'assembled.mp4'
    output_video = output_dir / 'first_2_lines_manual.mp4'
    output_srt = output_dir / 'captions.srt'
    font_path = root / 'tools' / '05b-render' / 'fonts' / 'Bangers-Regular.ttf'
    
    if not input_video.exists():
        print(f"Error: Input video not found: {input_video}", file=sys.stderr)
        sys.exit(1)
    
    if not font_path.exists():
        print(f"Error: Font not found: {font_path}", file=sys.stderr)
        sys.exit(1)
    
    print("Loading project...")
    project = load_project()
    caption_style = project.get('caption_style', {})
    caption_breaks = project.get('caption_breaks', {})
    
    print("Computing timeline clips for segment 0...")
    timeline_clips = compute_timeline_clips(project)
    timeline_clips = [tc for tc in timeline_clips 
                      if tc['clip'].get('timeline_position') == 0]
    
    if not timeline_clips:
        print("Error: No clips found for segment 0", file=sys.stderr)
        sys.exit(1)
    
    total_duration = get_total_duration(timeline_clips)
    print(f"Duration: {total_duration:.2f}s")
    
    print("Building caption events...")
    caption_events = build_caption_events(project, timeline_clips)
    print(f"Generated {len(caption_events)} caption events")
    
    print("Generating SRT file...")
    generate_srt(caption_events, str(output_srt))
    
    print("\n=== PASS 1: Timeline Assembly (filter-based) ===")
    v_filter, a_filter, n_segs = build_pass1_assembly_filter(timeline_clips)
    print(f"Assembling {n_segs} segments...")
    
    pass1_filter_path = output_dir / 'pass1_filter.txt'
    with open(pass1_filter_path, 'w') as f:
        f.write(f"{v_filter};\n{a_filter}")
    
    cmd1 = build_pass1_command(str(input_video), str(assembled_video), str(pass1_filter_path))
    result = subprocess.run(cmd1, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Pass 1 failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Pass 1 complete: {assembled_video}")
    
    print("\n=== PASS 2: Caption Overlay ===")
    caption_filter = build_pass2_caption_filter(
        caption_events, caption_style, str(font_path), caption_breaks
    )
    
    if not caption_filter:
        print("No caption filter generated", file=sys.stderr)
        sys.exit(1)
    
    pass2_filter_path = output_dir / 'pass2_filter.txt'
    with open(pass2_filter_path, 'w') as f:
        f.write(f"[0:v]{caption_filter}[vout]")
    print(f"Filter saved: {pass2_filter_path}")
    
    cmd2 = build_pass2_command(str(assembled_video), str(output_video), str(pass2_filter_path))
    result = subprocess.run(cmd2, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Pass 2 failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Pass 2 complete: {output_video}")
    
    print(f"\n=== Done ===")
    print(f"Output: {output_video}")
    print(f"SRT: {output_srt}")


if __name__ == '__main__':
    main()
