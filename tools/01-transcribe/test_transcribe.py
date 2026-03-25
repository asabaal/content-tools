"""Tests for transcription tool."""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import load_transcript


def test_individual_transcript_format():
    """Test that individual transcript has correct format."""
    transcript_path = Path("data/transcripts/20251008_150654.json")
    
    if not transcript_path.exists():
        print("SKIP: No individual transcript file found (run transcribe.py first)")
        return
    
    with open(transcript_path) as f:
        data = json.load(f)
    
    assert "video_id" in data, "Missing video_id"
    assert "language" in data, "Missing language"
    assert "duration" in data, "Missing duration"
    assert "segments" in data, "Missing segments"
    
    assert len(data["segments"]) > 0, "No segments"
    seg = data["segments"][0]
    assert "id" in seg, "Segment missing id"
    assert "text" in seg, "Segment missing text"
    assert "start" in seg, "Segment missing start"
    assert "end" in seg, "Segment missing end"
    assert "words" in seg, "Segment missing words"
    
    if len(seg["words"]) > 0:
        word = seg["words"][0]
        assert "text" in word, "Word missing text"
        assert "start" in word, "Word missing start"
        assert "end" in word, "Word missing end"
    
    print(f"Individual transcript OK: {data['video_id']}")
    print(f"  Duration: {data['duration']:.1f}s")
    print(f"  Segments: {len(data['segments'])}")


def test_combined_transcript_format():
    """Test that combined transcript has correct format with sources."""
    transcript_path = Path("data/transcript_combined.json")
    
    if not transcript_path.exists():
        print("SKIP: No combined transcript found (run transcribe.py first)")
        return
    
    with open(transcript_path) as f:
        data = json.load(f)
    
    assert data["video_id"] == "combined", "video_id should be 'combined'"
    assert "sources" in data, "Missing sources"
    assert "segments" in data, "Missing segments"
    
    assert len(data["sources"]) > 0, "No sources"
    assert len(data["segments"]) > 0, "No segments"
    
    src = data["sources"][0]
    assert "video_id" in src, "Source missing video_id"
    assert "start" in src, "Source missing start"
    assert "end" in src, "Source missing end"
    assert "duration" in src, "Source missing duration"
    
    seg = data["segments"][0]
    assert "original_video_id" in seg, "Segment missing original_video_id"
    assert "original_id" in seg, "Segment missing original_id"
    
    print(f"Combined transcript OK")
    print(f"  Sources: {len(data['sources'])}")
    print(f"  Segments: {len(data['segments'])}")
    print(f"  Duration: {data['duration']:.1f}s")


def test_timestamps_sequential():
    """Test that combined transcript timestamps are sequential."""
    transcript_path = Path("data/transcript_combined.json")
    
    if not transcript_path.exists():
        print("SKIP: No combined transcript found")
        return
    
    with open(transcript_path) as f:
        data = json.load(f)
    
    prev_end = 0
    for seg in data["segments"]:
        assert seg["start"] >= prev_end - 0.5, f"Segment {seg['id']} starts before previous ends"
        assert seg["end"] > seg["start"], f"Segment {seg['id']} has invalid duration"
        prev_end = seg["end"]
    
    print("Timestamps sequential: OK")


def test_source_boundaries():
    """Test that source boundaries are correct."""
    transcript_path = Path("data/transcript_combined.json")
    
    if not transcript_path.exists():
        print("SKIP: No combined transcript found")
        return
    
    with open(transcript_path) as f:
        data = json.load(f)
    
    total_from_sources = sum(s["duration"] for s in data["sources"])
    assert abs(total_from_sources - data["duration"]) < 1.0, "Duration mismatch"
    
    for i, src in enumerate(data["sources"]):
        if i > 0:
            prev = data["sources"][i-1]
            assert abs(src["start"] - prev["end"]) < 0.1, f"Source {i} start doesn't match previous end"
    
    print("Source boundaries: OK")


if __name__ == "__main__":
    test_individual_transcript_format()
    test_combined_transcript_format()
    test_timestamps_sequential()
    test_source_boundaries()
    print("\nAll tests passed!")

