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
from ffmpeg_builder import (
    build_filter_graph, build_ffmpeg_command,
    build_pass1_assembly_filter, build_pass2_caption_filter,
    build_pass1_command, build_pass2_command,
    generate_concat_demuxer_list, build_concat_demuxer_command
)
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


def render_two_pass(
    input_video: Path,
    output_video: Path,
    output_dir: Path,
    timeline_clips: list,
    caption_events: list,
    caption_style: dict,
    font_path: Path,
    caption_breaks: dict | None = None,
    verbose: bool = False,
    dry_run: bool = False
) -> bool:
    """Two-pass render: 1) assemble timeline, 2) add captions."""
    
    assembled_video = output_dir / 'assembled.mp4'
    concat_list_path = output_dir / 'concat_list.txt'
    pass2_filter_path = output_dir / 'pass2_filter.txt'
    
    print("\n=== PASS 1: Timeline Assembly (concat demuxer) ===")
    concat_list, n_segs = generate_concat_demuxer_list(
        timeline_clips, str(input_video), output_dir
    )
    print(f"Pass 1: {n_segs} segments -> {concat_list}")
    
    cmd1 = build_concat_demuxer_command(str(concat_list), str(assembled_video), str(input_video))
    
    if verbose or dry_run:
        print(f"\nPass 1 command:")
        print(' '.join(cmd1))
        if dry_run:
            print("\n(Dry run - stopping here)")
            return False
    
    print(f"Assembling {n_segs} segments...")
    result = subprocess.run(cmd1, capture_output=not verbose, text=True)
    
    if result.returncode != 0:
        print(f"Pass 1 failed: {result.stderr}", file=sys.stderr)
        return False
    
    print(f"Pass 1 complete: {assembled_video}")
    
    print("\n=== PASS 2: Caption Overlay ===")
    caption_filter = build_pass2_caption_filter(caption_events, caption_style, str(font_path), caption_breaks)
    
    if not caption_filter:
        print("No captions to render, copying assembled video...")
        import shutil
        shutil.copy(str(assembled_video), str(output_video))
        return True
    
    pass2_filter = f"[0:v]{caption_filter}[vout]"
    
    with open(pass2_filter_path, 'w') as f:
        f.write(pass2_filter)
    print(f"Pass 2 filter saved to: {pass2_filter_path}")
    
    cmd2 = build_pass2_command(str(assembled_video), str(output_video), str(pass2_filter_path))
    
    if verbose:
        print(f"\nPass 2 command:")
        print(' '.join(cmd2))
    
    print("Adding captions...")
    result = subprocess.run(cmd2, capture_output=not verbose, text=True)
    
    if result.returncode != 0:
        print(f"Pass 2 failed: {result.stderr}", file=sys.stderr)
        return False
    
    print(f"Pass 2 complete: {output_video}")
    
    try:
        assembled_video.unlink()
        print(f"Cleaned up intermediate file: {assembled_video}")
    except:
        pass
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Render video with captions')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Show command without running')
    parser.add_argument('--output', '-o', type=str, help='Output directory')
    parser.add_argument('--project', '-p', type=str, help='Path to project.json')
    parser.add_argument('--skip-verification', action='store_true', help='Skip post-render verification')
    parser.add_argument('--two-pass', action='store_true', 
                        help='Use two-pass rendering (assembly then captions) - recommended for many segments')
    parser.add_argument('--segment', type=str, 
                        help='Render only this segment (index number or clip_id)')
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
    caption_breaks = project.get('caption_breaks', {})
    
    print("Computing timeline clips...")
    timeline_clips = compute_timeline_clips(project)
    
    if not timeline_clips:
        print("Error: No clips in timeline", file=sys.stderr)
        sys.exit(1)
    
    if args.segment:
        if args.segment.isdigit():
            target_idx = int(args.segment)
            timeline_clips = [tc for tc in timeline_clips 
                            if tc['clip'].get('timeline_position') == target_idx]
        else:
            timeline_clips = [tc for tc in timeline_clips 
                            if tc['clip'].get('id') == args.segment]
        
        if not timeline_clips:
            print(f"Error: Segment '{args.segment}' not found", file=sys.stderr)
            sys.exit(1)
        
        print(f"Filtered to segment: {args.segment}")
    
    total_duration = get_total_duration(timeline_clips)
    print(f"Total duration: {total_duration:.2f}s")
    
    print("Building caption events...")
    caption_events = build_caption_events(project, timeline_clips)
    
    print(f"Generated {len(caption_events)} caption events")
    
    print("Generating SRT file...")
    generate_srt(caption_events, str(output_srt))
    print(f"SRT saved to: {output_srt}")
    
    total_segments = sum(len(tc.get('playable_segments', [])) for tc in timeline_clips)
    
    if args.two_pass or total_segments > 20:
        if total_segments > 20 and not args.two_pass:
            print(f"\nNote: Using two-pass rendering for {total_segments} segments (use --two-pass to force)")
        
        render_success = render_two_pass(
            input_video=input_video,
            output_video=output_video,
            output_dir=output_dir,
            timeline_clips=timeline_clips,
            caption_events=caption_events,
            caption_style=caption_style,
            font_path=font_path,
            caption_breaks=caption_breaks,
            verbose=args.verbose,
            dry_run=args.dry_run
        )
        
        if args.dry_run:
            return
        
        if not render_success:
            print("\nVerification skipped due to render failure.")
            sys.exit(1)
        
        print(f"\nDone! Output saved to:")
        print(f"  Video: {output_video}")
        print(f"  SRT:   {output_srt}")
        
        if not args.skip_verification:
            print("\nRunning post-render verification...")
            run_verification(root, verbose=args.verbose)
        
        return
    
    print("Building ffmpeg filter graph...")
    filter_graph = build_filter_graph(
        caption_events,
        caption_style,
        str(font_path),
        str(input_video),
        str(output_video),
        timeline_clips=timeline_clips,
        caption_breaks=caption_breaks
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
    
    if render_success and not args.skip_verification:
        print("\nRunning post-render verification...")
        run_verification(root, verbose=args.verbose)


if __name__ == '__main__':
    main()
