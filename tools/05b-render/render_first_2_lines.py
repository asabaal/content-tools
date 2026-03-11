#!/usr/bin/env python3
"""Render first 2 caption lines (segment 0) using segmented approach."""

import subprocess
import sys
from pathlib import Path

from segments import compute_timeline_clips, get_total_duration
from captions import build_caption_events
from ffmpeg_builder import build_segment_render_command
from srt import generate_srt
from render import load_project, get_project_root


def main():
    root = get_project_root()
    input_video = root / 'data' / 'video_combined.mp4'
    output_dir = root / 'data' / 'output'
    output_video = output_dir / 'first_2_lines.mp4'
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
    
    for clip_item in timeline_clips:
        for seg_start, seg_end in clip_item['playable_segments']:
            seg_captions = [
                e for e in caption_events 
                if abs(e['original_start'] - seg_start) < 0.001 
                and abs(e['original_end'] - seg_end) < 0.001
            ]
            
            for event in seg_captions:
                event['output_start'] = 0.0
            
            print(f"\nRendering segment {seg_start:.3f}-{seg_end:.3f}...")
            
            filter_script_path = output_dir / 'first_2_lines_filter.txt'
            
            cmd = build_segment_render_command(
                str(input_video),
                str(output_video),
                seg_start,
                seg_end,
                seg_captions,
                caption_style,
                str(font_path),
                caption_breaks,
                filter_script_path=str(filter_script_path)
            )
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Render failed: {result.stderr}", file=sys.stderr)
                sys.exit(1)
            
            print(f"Render complete: {output_video}")
            print(f"SRT: {output_srt}")
            return
    
    print("No playable segments found", file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
    main()
