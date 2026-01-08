import pytest
from transcript_core.models import Segment, Word
from transcript_core.segments import SegmentManager


@pytest.fixture
def sample_segment():
    words = [
        Word(id="w1", text="Hello", start_time=0.0, end_time=0.5),
        Word(id="w2", text="world", start_time=0.5, end_time=1.0),
    ]
    return Segment(id="s1", text="Hello world", start_time=0.0, end_time=1.0, words=words)


@pytest.fixture
def sample_manager():
    manager = SegmentManager()
    words = [
        Word(id="w1", text="Hello", start_time=0.0, end_time=0.5),
        Word(id="w2", text="world", start_time=0.5, end_time=1.0),
    ]
    segment = Segment(id="s1", text="Hello world", start_time=0.0, end_time=1.0, words=words)
    manager.add_segment(segment)
    return manager


class TestSegmentManager:
    def test_add_segment(self, sample_manager):
        words = [Word(id="w3", text="test", start_time=1.0, end_time=1.5)]
        segment = Segment(id="s2", text="test", start_time=1.0, end_time=1.5, words=words)
        sample_manager.add_segment(segment)
        assert len(sample_manager.get_all_segments()) == 2

    def test_remove_segment(self, sample_manager):
        assert sample_manager.remove_segment("s1") is True
        assert len(sample_manager.get_all_segments()) == 0

    def test_remove_nonexistent_segment(self, sample_manager):
        assert sample_manager.remove_segment("s999") is False

    def test_get_segment(self, sample_manager):
        segment = sample_manager.get_segment("s1")
        assert segment is not None
        assert segment.id == "s1"
        assert segment.text == "Hello world"

    def test_get_nonexistent_segment(self, sample_manager):
        segment = sample_manager.get_segment("s999")
        assert segment is None

    def test_update_text(self, sample_manager):
        assert sample_manager.update_text("s1", "Goodbye world") is True
        segment = sample_manager.get_segment("s1")
        assert segment.text == "Goodbye world"

    def test_update_text_nonexistent(self, sample_manager):
        assert sample_manager.update_text("s999", "new text") is False

    def test_get_segment_at_time(self, sample_manager):
        segment = sample_manager.get_segment_at_time(0.5)
        assert segment is not None
        assert segment.id == "s1"

    def test_get_segment_at_time_before(self, sample_manager):
        segment = sample_manager.get_segment_at_time(-1.0)
        assert segment is None

    def test_get_segment_at_time_after(self, sample_manager):
        segment = sample_manager.get_segment_at_time(2.0)
        assert segment is None

    def test_get_segments_in_range(self, sample_manager):
        manager = sample_manager
        words = [Word(id="w3", text="test", start_time=1.0, end_time=2.0)]
        segment2 = Segment(id="s2", text="test", start_time=1.0, end_time=2.0, words=words)
        manager.add_segment(segment2)
        
        segments = manager.get_segments_in_range(0.5, 1.5)
        assert len(segments) == 2

    def test_get_segments_in_range_empty(self, sample_manager):
        segments = sample_manager.get_segments_in_range(5.0, 10.0)
        assert len(segments) == 0

    def test_reorder_segments(self):
        manager = SegmentManager()
        words = [Word(id="w1", text="a", start_time=0.0, end_time=0.5)]
        s1 = Segment(id="s1", text="a", start_time=0.0, end_time=0.5, words=words)
        words2 = [Word(id="w2", text="b", start_time=0.5, end_time=1.0)]
        s2 = Segment(id="s2", text="b", start_time=0.5, end_time=1.0, words=words2)
        manager.add_segment(s1)
        manager.add_segment(s2)
        
        assert manager.reorder_segments(["s2", "s1"]) is True
        segments = manager.get_all_segments()
        assert segments[0].id == "s2"
        assert segments[1].id == "s1"

    def test_reorder_segments_invalid_id(self):
        manager = SegmentManager()
        words = [Word(id="w1", text="a", start_time=0.0, end_time=0.5)]
        s1 = Segment(id="s1", text="a", start_time=0.0, end_time=0.5, words=words)
        manager.add_segment(s1)
        
        assert manager.reorder_segments(["s999"]) is False

    def test_reorder_segments_incomplete(self):
        manager = SegmentManager()
        words = [Word(id="w1", text="a", start_time=0.0, end_time=0.5)]
        s1 = Segment(id="s1", text="a", start_time=0.0, end_time=0.5, words=words)
        words2 = [Word(id="w2", text="b", start_time=0.5, end_time=1.0)]
        s2 = Segment(id="s2", text="b", start_time=0.5, end_time=1.0, words=words2)
        manager.add_segment(s1)
        manager.add_segment(s2)
        
        assert manager.reorder_segments(["s1"]) is False

    def test_create_segment_from_words(self):
        words = [
            Word(id="w1", text="Hello", start_time=0.0, end_time=0.5),
            Word(id="w2", text="world", start_time=0.5, end_time=1.0),
        ]
        manager = SegmentManager()
        segment = manager.create_segment_from_words("s1", words)
        
        assert segment.id == "s1"
        assert segment.text == "Hello world"
        assert segment.start_time == 0.0
        assert segment.end_time == 1.0
        assert len(segment.words) == 2

    def test_create_segment_from_words_custom_text(self):
        words = [
            Word(id="w1", text="Hello", start_time=0.0, end_time=0.5),
        ]
        manager = SegmentManager()
        segment = manager.create_segment_from_words("s1", words, text="Custom text")
        
        assert segment.text == "Custom text"

    def test_create_segment_from_empty_words(self):
        manager = SegmentManager()
        with pytest.raises(ValueError):
            manager.create_segment_from_words("s1", [])


class TestSegment:
    def test_segment_duration(self, sample_segment):
        assert sample_segment.duration == 1.0

    def test_segment_word_count(self, sample_segment):
        assert sample_segment.word_count == 2

    def test_empty_segment_duration(self):
        segment = Segment(id="s1", text="test", start_time=0.0, end_time=0.5)
        assert segment.duration == 0.5
