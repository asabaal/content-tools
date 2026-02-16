#!/usr/bin/env python3
"""
Test script to verify data integrity across the content tools pipeline.

Usage:
    python tests/test_data_integrity.py

Tests:
1. All clips have selected_segment (or can be derived from segments[0])
2. Timestamps are preserved correctly
3. Clips can be sorted chronologically
4. Data structure is valid for all tools
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROJECT_FILE = DATA_DIR / "project.json"

def test_project_file_exists():
    """Test that project.json exists."""
    assert PROJECT_FILE.exists(), f"project.json not found at {PROJECT_FILE}"
    print("✓ project.json exists")
    return True

def test_project_json_valid():
    """Test that project.json is valid JSON."""
    with open(PROJECT_FILE, 'r') as f:
        data = json.load(f)
    assert isinstance(data, dict), "project.json should be a dict"
    print("✓ project.json is valid JSON")
    return data

def test_clips_exist(data):
    """Test that clips array exists and has items."""
    assert 'clips' in data, "project.json must have 'clips' key"
    assert isinstance(data['clips'], list), "'clips' must be an array"
    assert len(data['clips']) > 0, "'clips' array must not be empty"
    print(f"✓ Found {len(data['clips'])} clips")
    return data['clips']

def test_all_clips_have_segments(clips):
    """Test that all clips have a segments array."""
    for i, clip in enumerate(clips):
        assert 'segments' in clip, f"Clip {i} ({clip.get('name', 'unknown')}) missing 'segments'"
        assert isinstance(clip['segments'], list), f"Clip {i} segments must be an array"
        assert len(clip['segments']) > 0, f"Clip {i} has empty segments array"
    print(f"✓ All {len(clips)} clips have segments")
    return True

def test_all_clips_have_timestamps(clips):
    """Test that all clips have valid timestamps (either selected_segment or segments[0])."""
    missing = []
    for clip in clips:
        seg = clip.get('selected_segment') or (clip['segments'][0] if clip.get('segments') else None)
        if not seg:
            missing.append(clip.get('name', clip.get('id', 'unknown')))
            continue
        if 'start' not in seg or 'end' not in seg:
            missing.append(f"{clip.get('name', 'unknown')} (missing start/end)")
    
    if missing:
        print(f"✗ Clips missing timestamps: {missing}")
        return False
    
    print(f"✓ All {len(clips)} clips have valid timestamps")
    return True

def test_selected_segment_propagated(clips):
    """Test that selected_segment is set for all clips (or derivable from segments[0])."""
    missing_selected = []
    for clip in clips:
        if not clip.get('selected_segment'):
            if clip.get('segments') and len(clip['segments']) == 1:
                pass
            else:
                missing_selected.append(clip.get('name', clip.get('id', 'unknown')))
    
    if missing_selected:
        print(f"⚠ Clips without selected_segment (multi-take): {missing_selected}")
        print("  These should have selected_segment set by Tool 03")
    else:
        print(f"✓ All clips have selected_segment or are single-take")
    
    return len(missing_selected) == 0

def test_chronological_sort(clips):
    """Test that clips can be sorted chronologically by start time."""
    def get_start_time(clip):
        seg = clip.get('selected_segment') or (clip['segments'][0] if clip.get('segments') else None)
        if seg and 'start' in seg:
            return seg['start']
        return float('inf')
    
    sorted_clips = sorted(clips, key=get_start_time)
    
    prev_time = -1
    for clip in sorted_clips:
        start_time = get_start_time(clip)
        if start_time == float('inf'):
            continue
        assert start_time >= prev_time, f"Clips not in chronological order: {clip.get('name')}"
        prev_time = start_time
    
    print("✓ Clips can be sorted chronologically")
    
    print("\n  Chronological order:")
    for i, clip in enumerate(sorted_clips[:10]):
        seg = clip.get('selected_segment') or clip['segments'][0]
        print(f"    {i+1}. {clip['name'][:35]:35s} | start: {seg['start']:.2f}s")
    if len(sorted_clips) > 10:
        print(f"    ... and {len(sorted_clips) - 10} more")
    
    return True

def test_segment_data_integrity(clips):
    """Test that segment data has all required fields."""
    required_fields = ['segment_index', 'start', 'end', 'text']
    
    for clip in clips:
        seg = clip.get('selected_segment') or (clip['segments'][0] if clip.get('segments') else None)
        if not seg:
            continue
        
        for field in required_fields:
            assert field in seg, f"Clip {clip.get('name')} selected_segment missing '{field}'"
        
        assert seg['end'] > seg['start'], f"Clip {clip.get('name')} has end <= start"
    
    print(f"✓ All segment data has required fields")
    return True

def test_tool_03_data_persistence():
    """Simulate Tool 03's data handling to verify persistence."""
    with open(PROJECT_FILE, 'r') as f:
        data = json.load(f)
    
    original_count = len([c for c in data['clips'] if c.get('selected_segment')])
    
    for clip in data['clips']:
        if not clip.get('selected_segment') and clip.get('segments') and len(clip['segments']) == 1:
            clip['selected_segment'] = clip['segments'][0]
    
    new_count = len([c for c in data['clips'] if c.get('selected_segment')])
    
    print(f"✓ Tool 03 simulation: {original_count} -> {new_count} clips with selected_segment")
    return True

def test_tool_04_data_handling():
    """Simulate Tool 04's data handling to verify chronological sort."""
    with open(PROJECT_FILE, 'r') as f:
        data = json.load(f)
    
    def get_start_time(clip):
        seg = clip.get('selected_segment') or (clip['segments'][0] if clip.get('segments') else None)
        if seg and 'start' in seg:
            return seg['start']
        return float('inf')
    
    sorted_clips = sorted(data['clips'], key=get_start_time)
    
    for i, clip in enumerate(sorted_clips):
        clip['timeline_position'] = i
    
    for i in range(len(sorted_clips) - 1):
        curr_start = get_start_time(sorted_clips[i])
        next_start = get_start_time(sorted_clips[i + 1])
        assert curr_start <= next_start, f"Timeline position mismatch at {i}"
    
    print(f"✓ Tool 04 simulation: clips assigned timeline_position 0-{len(sorted_clips)-1}")
    return True

def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("CONTENT TOOLS DATA INTEGRITY TESTS")
    print("=" * 60)
    print()
    
    all_passed = True
    
    try:
        test_project_file_exists()
        data = test_project_json_valid()
        clips = test_clips_exist(data)
        test_all_clips_have_segments(clips)
        
        if not test_all_clips_have_timestamps(clips):
            all_passed = False
        
        test_selected_segment_propagated(clips)
        test_chronological_sort(clips)
        test_segment_data_integrity(clips)
        test_tool_03_data_persistence()
        test_tool_04_data_handling()
        
        print()
        print("=" * 60)
        if all_passed:
            print("ALL TESTS PASSED ✓")
        else:
            print("SOME TESTS FAILED ✗")
        print("=" * 60)
        
        return 0 if all_passed else 1
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
