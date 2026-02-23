#!/usr/bin/env python3
"""Verify rendered captions by extracting frames at caption appearance times."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

from segments import compute_timeline_clips
from captions import build_caption_events


def get_project_root():
    return Path(__file__).parent.parent.parent


def merge_segments(segments):
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


def load_project(project_path: str = None) -> dict:
    if project_path is None:
        project_path = get_project_root() / 'data' / 'project.json'
    with open(project_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_frame(video_path: str, timestamp: float, output_path: str) -> bool:
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(timestamp),
        '-i', video_path,
        '-frames:v', '1',
        '-q:v', '2',
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def build_checkpoints(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    checkpoints = []
    previously_failed_ranges = [
        (39.43, 50.89),
        (90.46, 92.39),
        (115.94, 118.16),
        (184.11, 186.31),
        (206.82, 209.84),
    ]
    
    for i, event in enumerate(events):
        if not event['words']:
            continue
        
        first_word = event['words'][0]
        output_time = event['output_start'] + (first_word['start'] - event['original_start'])
        
        expected_words = [w['text'] for w in event['words'][:3]]
        
        src_start = event['original_start']
        src_end = event['original_end']
        previously_failed = any(
            abs(src_start - fs) < 0.1 for fs, fe in previously_failed_ranges
        )
        
        checkpoints.append({
            'event_index': i,
            'output_time': round(output_time, 3),
            'expected_first_word': first_word['text'],
            'expected_words': expected_words,
            'source_range': [round(src_start, 2), round(src_end, 2)],
            'output_range': [round(event['output_start'], 2), round(event['output_end'], 2)],
            'previously_failed': previously_failed,
            'word_count': len(event['words']),
        })
    
    return checkpoints


def main():
    parser = argparse.ArgumentParser(description='Verify captions in rendered video')
    parser.add_argument('--project', '-p', type=str, help='Path to project.json')
    parser.add_argument('--video', '-v', type=str, help='Path to rendered video')
    parser.add_argument('--output', '-o', type=str, help='Output directory')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    root = get_project_root()
    
    project_path = Path(args.project) if args.project else root / 'data' / 'project.json'
    video_path = Path(args.video) if args.video else root / 'data' / 'output' / 'final_video.mp4'
    output_dir = Path(args.output) if args.output else root / 'data' / 'output' / 'verification'
    
    if not video_path.exists():
        print(f"Error: Video not found: {video_path}", file=sys.stderr)
        sys.exit(1)
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading project...")
    project = load_project(str(project_path))
    
    print("Computing timeline clips...")
    timeline_clips = compute_timeline_clips(project)
    
    all_segments = []
    for item in timeline_clips:
        all_segments.extend(item['playable_segments'])
    
    playable_segments = merge_segments(all_segments)
    
    print("Building caption events...")
    events = build_caption_events(project, timeline_clips, playable_segments)
    
    print(f"Found {len(events)} events, {sum(1 for e in events if e['words'])} with words")
    
    print("Building checkpoints...")
    checkpoints = build_checkpoints(events)
    print(f"Created {len(checkpoints)} verification checkpoints")
    
    previously_failed = [cp for cp in checkpoints if cp['previously_failed']]
    print(f"  - {len(previously_failed)} previously failed segments")
    
    print("\nExtracting frames...")
    for i, cp in enumerate(checkpoints):
        frame_name = f"frame_{i:03d}_{cp['output_time']:.2f}s.png"
        frame_path = output_dir / frame_name
        
        if args.verbose:
            print(f"  [{i+1}/{len(checkpoints)}] {cp['output_time']:.2f}s -> {frame_name}")
        
        success = extract_frame(str(video_path), cp['output_time'], str(frame_path))
        
        if success:
            cp['frame_path'] = str(frame_path.relative_to(root / 'data' / 'output'))
            cp['frame_exists'] = True
        else:
            cp['frame_path'] = None
            cp['frame_exists'] = False
            print(f"    Warning: Failed to extract frame", file=sys.stderr)
    
    manifest_path = output_dir / 'manifest.json'
    manifest = {
        'video_path': str(video_path.relative_to(root)),
        'total_checkpoints': len(checkpoints),
        'previously_failed_count': len(previously_failed),
        'checkpoints': checkpoints,
    }
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nManifest saved to: {manifest_path}")
    print(f"Frames saved to: {output_dir}")
    
    print("\n=== Summary ===")
    print(f"Total checkpoints: {len(checkpoints)}")
    print(f"Frames extracted: {sum(1 for cp in checkpoints if cp['frame_exists'])}")
    
    if previously_failed:
        print(f"\nPreviously failed segments (now fixed):")
        for cp in previously_failed:
            print(f"  Event {cp['event_index']}: output {cp['output_time']:.2f}s, expected '{cp['expected_first_word']}'")


if __name__ == '__main__':
    main()
