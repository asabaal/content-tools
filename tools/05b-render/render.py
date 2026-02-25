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


def load_project(project_path: str | Path | None = None) -> dict:
    """Load project.json."""
    if project_path is None:
        project_path = get_project_root() / 'data' / 'project.json'
    else:
        project_path = Path(project_path)
        if project_path.is_dir():
            project_path = project_path / 'data' / 'project.json'
    
    with open(str(project_path), 'r', encoding='utf-8') as f:
        return json.load(f)


def run_verification(root: Path, verbose: bool = False) -> dict:
    """Run post-render verification."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from post_render import run_post_render_verification, print_verification_summary
        
        result = run_post_render_verification(root, verbose=verbose)
        print_verification_summary(result)
        return result
    except Exception as e:
        print(f"\nVerification execution failed: {e}", file=sys.stderr)
        print("Verification execution failed but render completed successfully.")
        return {'success': False, 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='Render video with captions')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Show command without running')
    parser.add_argument('--output', '-o', type=str, help='Output directory')
    parser.add_argument('--project', '-p', type=str, help='Path to project.json')
    parser.add_argument('--skip-verification', action='store_true', help='Skip post-render verification')
    args = parser.parse_args()
    
    root = get_project_root()
    
    input_video = root / 'data' / 'video_combined.mp4'
    output_dir = Path(args.output) if args.output else root / 'data' / 'output'
    output_video = output_dir / 'final_video.mp4'
    output_srt = output_dir / 'captions.srt'
    filter_script = output_dir / 'filter.txt'
    
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
    
    total_duration = get_total_duration(timeline_clips)
    print(f"Total duration: {total_duration:.2f}s")
    
    print("Building caption events...")
    caption_events = build_caption_events(project, timeline_clips)
    
    print(f"Generated {len(caption_events)} caption events")
    
    print("Generating SRT file...")
    generate_srt(caption_events, str(output_srt))
    print(f"SRT saved to: {output_srt}")
    
    print("Building ffmpeg filter graph...")
    filter_graph = build_filter_graph(
        caption_events,
        caption_style,
        str(font_path),
        str(input_video),
        str(output_video),
        timeline_clips=timeline_clips
    )
    
    if args.verbose:
        print(f"Filter graph ({len(filter_graph)} chars)")
    
    with open(filter_script, 'w') as f:
        f.write(filter_graph)
    print(f"Filter script saved to: {filter_script}")
    
    cmd = build_ffmpeg_command(
        str(input_video),
        str(output_video),
        str(filter_script),
        timeline_clips=timeline_clips
    )
    
    if args.dry_run or args.verbose:
        print("\nffmpeg command:")
        print(' '.join(cmd))
        if args.dry_run:
            return
    
    print("\nRendering video...")
    render_success = False
    try:
        result = subprocess.run(
            cmd,
            capture_output=not args.verbose,
            text=True
        )
        
        if result.returncode != 0:
            print(f"ffmpeg error: {result.stderr}", file=sys.stderr)
            print("\nVerification skipped due to render failure.")
            sys.exit(1)
        
        render_success = True
        print(f"\nDone! Output saved to:")
        print(f"  Video: {output_video}")
        print(f"  SRT:   {output_srt}")
        
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install ffmpeg.", file=sys.stderr)
        print("\nVerification skipped due to render failure.")
        sys.exit(1)
    
    # Run post-render verification
    if render_success and not args.skip_verification:
        print("\nRunning post-render verification...")
        run_verification(root, verbose=args.verbose)


if __name__ == '__main__':
    main()
