#!/usr/bin/env python3
"""Render final video with burned-in captions."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from segments import compute_timeline_clips, get_total_duration
from captions import build_caption_events
from ffmpeg_builder import build_filter_graph, build_ffmpeg_command
from srt import generate_srt


def get_project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


def load_project(project_path: str = None) -> dict:
    """Load project.json."""
    if project_path is None:
        project_path = get_project_root() / 'data' / 'project.json'
    
    with open(project_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_segments(segments):
    """Merge overlapping segments into non-overlapping ranges."""
    if not segments:
        return []
    
    segments = sorted(segments, key=lambda x: x[0])
    merged = [segments[0]]
    
    for start, end in segments[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    
    return merged


def main():
    parser = argparse.ArgumentParser(description='Render video with captions')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Show command without running')
    parser.add_argument('--output', '-o', type=str, help='Output directory')
    parser.add_argument('--project', '-p', type=str, help='Path to project.json')
    args = parser.parse_args()
    
    root = get_project_root()
    
    input_video = root / 'data' / 'video_combined.mp4'
    output_dir = Path(args.output) if args.output else root / 'data' / 'output'
    output_video = output_dir / 'final_video.mp4'
    output_srt = output_dir / 'captions.srt'
    
    os.makedirs(output_dir, exist_ok=True)
    
    font_path = root / 'tools' / '05b-render' / 'fonts' / 'Bangers-Regular.ttf'
    
    if not input_video.exists():
        print(f"Error: Input video not found: {input_video}", file=sys.stderr)
        sys.exit(1)
    
    if not font_path.exists():
        print(f"Error: Font not found: {font_path}", file=sys.stderr)
        sys.exit(1)
    
    print("Loading project...")
    project = load_project(args.project)
    
    caption_style = project.get('caption_style', {})
    
    print("Computing timeline clips...")
    timeline_clips = compute_timeline_clips(project)
    
    if not timeline_clips:
        print("Error: No clips in timeline", file=sys.stderr)
        sys.exit(1)
    
    all_segments = []
    for item in timeline_clips:
        all_segments.extend(item['playable_segments'])
    
    playable_segments = merge_segments(all_segments)
    total_duration = sum(end - start for start, end in playable_segments)
    print(f"Playable segments: {len(all_segments)} -> {len(playable_segments)} merged")
    print(f"Output duration: {total_duration:.2f}s")
    
    print("Building caption events...")
    caption_events = build_caption_events(project, timeline_clips, playable_segments)
    
    print(f"Generated {len(caption_events)} caption events")
    
    print("Generating SRT file...")
    generate_srt(caption_events, str(output_srt))
    print(f"SRT saved to: {output_srt}")
    
    print("Building ffmpeg filter graph...")
    filter_graph = build_filter_graph(
        caption_events,
        caption_style,
        str(font_path),
        playable_segments
    )
    
    if args.verbose:
        print(f"Filter graph ({len(filter_graph)} chars)")
        lines = filter_graph.split(';\n')
        for i, line in enumerate(lines[:5]):
            print(f"  [{i}]: {line[:100]}...")
        if len(lines) > 5:
            print(f"  ... and {len(lines) - 5} more filter chains")
    
    cmd, filter_file = build_ffmpeg_command(
        str(input_video),
        str(output_video),
        filter_graph,
        use_filter_script=True
    )
    
    filter_file_path = output_dir / 'filter.txt'
    with open(filter_file_path, 'w') as f:
        f.write(filter_graph)
    print(f"Filter written to: {filter_file_path}")
    
    if args.dry_run or args.verbose:
        print("\nffmpeg command:")
        print(' '.join(cmd))
        if args.dry_run:
            return
    
    print("\nRendering video...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=not args.verbose,
            text=True
        )
        
        if result.returncode != 0:
            print(f"ffmpeg error: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        
        print(f"\nDone! Output saved to:")
        print(f"  Video: {output_video}")
        print(f"  SRT:   {output_srt}")
        
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install ffmpeg.", file=sys.stderr)
        sys.exit(1)
    finally:
        if filter_file and os.path.exists(filter_file):
            os.remove(filter_file)


if __name__ == '__main__':
    main()
