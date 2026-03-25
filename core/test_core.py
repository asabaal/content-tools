"""Tests for core module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    Word, Segment, Transcript, SegmentRef, Clip, Video, Project,
    load_transcript, format_time, parse_time, word_count
)


def test_word():
    w = Word(text="Hello", start=1.0, end=1.5)
    assert w.text == "Hello"
    assert w.duration == 0.5
    assert w.to_dict() == {"text": "Hello", "start": 1.0, "end": 1.5}
    
    w2 = Word.from_dict({"text": "World", "start": 2.0, "end": 2.5})
    assert w2.text == "World"


def test_segment():
    words = [Word("Hello", 0, 0.5), Word("world", 0.5, 1.0)]
    s = Segment(id="seg_0", text="Hello world", start=0, end=1.0, words=words)
    
    assert s.word_count == 2
    assert s.duration == 1.0
    assert s.to_dict()["segment_id"] == "seg_0"


def test_format_time():
    assert format_time(0) == "0:00"
    assert format_time(61) == "1:01"
    assert format_time(3661) == "1:01:01"
    assert format_time(5.5, "ms") == "0:05.500"
    assert format_time(10, "short") == "10s"


def test_parse_time():
    assert parse_time("30") == 30
    assert parse_time("1:30") == 90
    assert parse_time("1:30:00") == 5400
    assert parse_time("45s") == 45


def test_segment_ref():
    ref = SegmentRef(video_id="vid1", segment_id="seg_0")
    d = ref.to_dict()
    assert d == {"video_id": "vid1", "segment_id": "seg_0"}
    
    ref2 = SegmentRef.from_dict(d)
    assert ref2.video_id == "vid1"


def test_clip():
    clip = Clip(id="clip_1", name="Intro")
    assert clip.include == True
    
    clip.segments.append(SegmentRef("vid1", "seg_0"))
    d = clip.to_dict()
    assert d["name"] == "Intro"
    assert len(d["segments"]) == 1


def test_project():
    p = Project()
    assert p.version == 1
    assert len(p.videos) == 0
    
    p.videos.append(Video(id="vid1", path="data/raw/vid1.mp4"))
    d = p.to_dict()
    assert len(d["videos"]) == 1
    
    p2 = Project.from_dict(d)
    assert p2.videos[0].id == "vid1"


def test_load_transcript():
    t = load_transcript("data/transcript_combined.json", "test")
    assert t.video_id == "test"
    assert len(t.segments) > 0
    assert t.segments[0].word_count > 0


if __name__ == "__main__":
    test_word()
    test_segment()
    test_format_time()
    test_parse_time()
    test_segment_ref()
    test_clip()
    test_project()
    test_load_transcript()
    print("All tests passed!")
