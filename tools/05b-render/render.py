#!/usr/bin/env python3
"""Render final video with burned-in captions using segmented approach."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from segments import compute_timeline_clips, get_total_duration
from captions import build_caption_events
from ffmpeg_builder import build_segment_render_command, build_concat_command
from srt import generate_srt


def get_project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


def load_project_from_config(config) -> dict:
    """Load project.json using ProjectConfig."""
    with open(config.path, 'r', encoding='utf-8') as f:
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


def render_segmented(
    input_video: Path,
    output_video: Path,
    output_dir: Path,
    timeline_clips: list,
    caption_events: list,
    caption_style: dict,
    font_path: Path,
    caption_breaks: dict | None = None,
    verbose: bool = False,
    keep_segments: bool = False,
    dry_run: bool = False
) -> bool:
    """Render video using segmented approach."""
    temp_dir = output_dir / 'segments'
    
    output_dir.mkdir(exist_ok=True, parents=True)
    temp_dir.mkdir(exist_ok=True)
    
    if dry_run:
        print(f"Dry run: would render to {temp_dir}")
    
    segment_files = []
    total_segments = sum(len(tc.get('playable_segments', [])) for tc in timeline_clips)
    current_segment = 0
    
    print(f"\nRendering {total_segments} segments...")
    
    for clip_item in timeline_clips:
        for seg_start, seg_end in clip_item['playable_segments']:
            current_segment += 1
            seg_duration = seg_end - seg_start
            
            print(f"  Segment {current_segment}/{total_segments} ({seg_duration:.2f}s)...")
            
            seg_captions = [
                e for e in caption_events 
                if abs(e.get('original_start', -1) - seg_start) < 0.001 
                and abs(e.get('original_end', -1) - seg_end) < 0.001
            ]
            
            for event in seg_captions:
                for word in event.get('words', []):
                    word['start'] = word['start'] - seg_start
                    word['end'] = word['end'] - seg_start
                event['output_start'] = 0.0
                event['original_start'] = 0.0
            
            seg_file = temp_dir / f'seg_{current_segment:03d}.mp4'
            segment_files.append(seg_file)
            
            filter_script_path = temp_dir / f'seg_{current_segment:03d}_filter.txt'
            
            cmd = build_segment_render_command(
                str(input_video),
                str(seg_file),
                seg_start,
                seg_end,
                seg_captions,
                caption_style,
                str(font_path),
                caption_breaks,
                filter_script_path=str(filter_script_path)
            )
            
            if verbose or dry_run:
                print(f"\n    Command for segment {current_segment}:")
                print(' '.join(cmd))
                if dry_run:
                    continue
            
            result = subprocess.run(cmd, capture_output=not verbose, text=True)
            
            if result.returncode != 0:
                print(f"Segment {current_segment} failed: {result.stderr}", file=sys.stderr)
                return False
            
            if not seg_file.exists():
                print(f"Segment {current_segment} file not created: {seg_file}", file=sys.stderr)
                return False
    
    if dry_run:
        print("\n(Dry run - stopping before concat)")
        return False
    
    if len(segment_files) == 1:
        print("\nSingle segment - moving to output...")
        shutil.move(str(segment_files[0]), str(output_video))
        
        if not keep_segments:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")
        
        return True
    
    concat_list_path = temp_dir / 'concat_list.txt'
    with open(concat_list_path, 'w') as f:
        for seg_file in segment_files:
            f.write(f"file '{seg_file.name}'\n")
    
    print(f"\nConcatenating {len(segment_files)} segments...")
    
    cmd = build_concat_command(str(concat_list_path), str(output_video))
    
    if verbose:
        print(f"\nConcat command:")
        print(' '.join(cmd))
    
    result = subprocess.run(cmd, capture_output=not verbose, text=True)
    
    if result.returncode != 0:
        print(f"Concat failed: {result.stderr}", file=sys.stderr)
        return False
    
    if not keep_segments:
        shutil.rmtree(temp_dir)
        print(f"Cleaned up temporary directory: {temp_dir}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Render video with captions')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Show commands without running')
    parser.add_argument('--output', '-o', type=str, help='Output directory')
    parser.add_argument('--project', '-p', type=str, 
                        default='data',
                        help='Path to project directory (default: data)')
    parser.add_argument('--skip-verification', action='store_true', 
                        help='Skip post-render verification')
    parser.add_argument('--keep-segments', action='store_true', 
                        help='Keep temporary segment files for debugging')
    parser.add_argument('--segment', type=str, 
                        help='Render only this segment (index number or clip_id)')
    args = parser.parse_args()
    
    root = get_project_root()
    
    sys.path.insert(0, str(root))
    from core.project_config import ProjectConfig
    
    project_path = Path(args.project)
    if project_path.is_file() and project_path.name == 'project.json':
        config_path = project_path
    else:
        config_path = project_path / 'project.json'
    
    if not config_path.exists():
        print(f"Error: Project not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    config = ProjectConfig.load(config_path)
    
    print(f"Project: {config.name}")
    print(f"Data directory: {config.data_dir}")
    
    input_video = config.combined_video
    output_dir = Path(args.output) if args.output else config.output_dir
    output_video = output_dir / 'final_video.mp4'
    output_srt = output_dir / 'captions.srt'
    
    font_path = root / 'tools' / '05b-render' / 'fonts' / 'Bangers-Regular.ttf'
    
    if not input_video.exists():
        print(f"Error: Input video not found: {input_video}", file=sys.stderr)
        sys.exit(1)
    
    if not font_path.exists():
        print(f"Error: Font not found: {font_path}", file=sys.stderr)
        sys.exit(1)
    
    print("Loading project...")
    project = load_project_from_config(config)
    
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
    output_dir.mkdir(exist_ok=True, parents=True)
    generate_srt(caption_events, str(output_srt))
    print(f"SRT saved to: {output_srt}")
    
    render_success = render_segmented(
        input_video=input_video,
        output_video=output_video,
        output_dir=output_dir,
        timeline_clips=timeline_clips,
        caption_events=caption_events,
        caption_style=caption_style,
        font_path=font_path,
        caption_breaks=caption_breaks,
        verbose=args.verbose,
        keep_segments=args.keep_segments,
        dry_run=args.dry_run
    )
    
    if args.dry_run:
        return
    
    if not render_success:
        if not args.skip_verification:
            print("\nVerification skipped due to render failure.")
        sys.exit(1)
    
    print(f"\nDone! Output saved to:")
    print(f"  Video: {output_video}")
    print(f"  SRT:   {output_srt}")
    
    if not args.skip_verification:
        print("\nRunning post-render verification...")
        run_verification(root, verbose=args.verbose)


if __name__ == '__main__':
    main()
