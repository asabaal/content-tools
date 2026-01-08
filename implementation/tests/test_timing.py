import pytest
from transcript_core.models import Segment, Word
from transcript_core.timing import TimingManager


@pytest.fixture
def segment_with_words():
    words = [
        Word(id="w1", text="Hello", start_time=0.0, end_time=0.5),
        Word(id="w2", text="world", start_time=0.5, end_time=1.0),
        Word(id="w3", text="there", start_time=1.0, end_time=1.5),
    ]
    return Segment(id="s1", text="Hello world there", start_time=0.0, end_time=1.5, words=words)


class TestTimingManager:
    def test_redistribute_same_word_count(self, segment_with_words):
        new_text = "Hello world there"
        new_words = TimingManager.redistribute_word_timings(segment_with_words, new_text)
        
        assert len(new_words) == 3
        assert new_words[0].text == "Hello"
        assert new_words[1].text == "world"
        assert new_words[2].text == "there"
        assert new_words[0].start_time == 0.0
        assert new_words[2].end_time == 1.5

    def test_redistribute_fewer_words(self, segment_with_words):
        new_text = "Hello there"
        new_words = TimingManager.redistribute_word_timings(segment_with_words, new_text)
        
        assert len(new_words) == 2
        assert new_words[0].text == "Hello"
        assert new_words[1].text == "there"
        assert new_words[0].start_time == 0.0
        assert new_words[1].end_time == 1.5

    def test_redistribute_more_words(self, segment_with_words):
        new_text = "Hello world there now"
        new_words = TimingManager.redistribute_word_timings(segment_with_words, new_text)
        
        assert len(new_words) == 4
        assert new_words[0].text == "Hello"
        assert new_words[3].text == "now"
        assert new_words[0].start_time == 0.0
        assert new_words[3].end_time == 1.5

    def test_redistribute_to_single_word(self, segment_with_words):
        new_text = "Hello"
        new_words = TimingManager.redistribute_word_timings(segment_with_words, new_text)
        
        assert len(new_words) == 1
        assert new_words[0].text == "Hello"
        assert new_words[0].start_time == 0.0
        assert new_words[0].end_time == 1.5

    def test_redistribute_empty_text(self, segment_with_words):
        new_words = TimingManager.redistribute_word_timings(segment_with_words, "")
        assert len(new_words) == 0

    def test_redistribute_segment_no_words(self):
        segment = Segment(id="s1", text="test", start_time=0.0, end_time=1.0)
        new_words = TimingManager.redistribute_word_timings(segment, "new text")
        assert len(new_words) == 0

    def test_shift_segment_forward(self, segment_with_words):
        TimingManager.shift_segment_timings(segment_with_words, 1.0)
        
        assert segment_with_words.start_time == 1.0
        assert segment_with_words.end_time == 2.5
        assert segment_with_words.words[0].start_time == 1.0
        assert segment_with_words.words[2].end_time == 2.5

    def test_shift_segment_backward(self, segment_with_words):
        TimingManager.shift_segment_timings(segment_with_words, -0.5)
        
        assert segment_with_words.start_time == -0.5
        assert segment_with_words.end_time == 1.0
        assert segment_with_words.words[0].start_time == -0.5
        assert segment_with_words.words[2].end_time == 1.0

    def test_shift_segment_zero(self, segment_with_words):
        original_start = segment_with_words.start_time
        original_end = segment_with_words.end_time
        TimingManager.shift_segment_timings(segment_with_words, 0.0)
        
        assert segment_with_words.start_time == original_start
        assert segment_with_words.end_time == original_end

    def test_set_segment_duration_shorter(self, segment_with_words):
        TimingManager.set_segment_duration(segment_with_words, 0.75)
        
        assert segment_with_words.duration == 0.75
        assert segment_with_words.start_time == 0.0
        assert segment_with_words.end_time == 0.75

    def test_set_segment_duration_longer(self, segment_with_words):
        TimingManager.set_segment_duration(segment_with_words, 3.0)
        
        assert segment_with_words.duration == 3.0
        assert segment_with_words.start_time == 0.0
        assert segment_with_words.end_time == 3.0

    def test_set_segment_duration_negative(self, segment_with_words):
        with pytest.raises(ValueError):
            TimingManager.set_segment_duration(segment_with_words, -1.0)

    def test_set_segment_duration_zero(self, segment_with_words):
        with pytest.raises(ValueError):
            TimingManager.set_segment_duration(segment_with_words, 0.0)

    def test_get_word_at_time(self, segment_with_words):
        word = TimingManager.get_word_at_time(segment_with_words, 0.25)
        assert word is not None
        assert word.id == "w1"

    def test_get_word_at_time_boundary(self, segment_with_words):
        word = TimingManager.get_word_at_time(segment_with_words, 0.5)
        assert word is not None
        assert word.id == "w1"

    def test_get_word_at_time_not_found(self, segment_with_words):
        word = TimingManager.get_word_at_time(segment_with_words, 2.0)
        assert word is None

    def test_adjust_segment_boundaries(self, segment_with_words):
        TimingManager.adjust_segment_boundaries(segment_with_words, 1.0, 3.0)
        
        assert segment_with_words.start_time == 1.0
        assert segment_with_words.end_time == 3.0
        assert segment_with_words.duration == 2.0

    def test_adjust_segment_boundaries_shorter(self, segment_with_words):
        original_end = segment_with_words.end_time
        TimingManager.adjust_segment_boundaries(segment_with_words, 0.0, 1.0)
        
        assert segment_with_words.duration == 1.0
        assert segment_with_words.end_time == 1.0

    def test_adjust_segment_boundaries_invalid(self, segment_with_words):
        with pytest.raises(ValueError):
            TimingManager.adjust_segment_boundaries(segment_with_words, 2.0, 1.0)

    def test_adjust_segment_boundaries_equal(self, segment_with_words):
        with pytest.raises(ValueError):
            TimingManager.adjust_segment_boundaries(segment_with_words, 1.0, 1.0)

    def test_proportional_distribution_char_based(self):
        words = [
            Word(id="w1", text="hi", start_time=0.0, end_time=0.33),
            Word(id="w2", text="there", start_time=0.33, end_time=1.0),
        ]
        segment = Segment(id="s1", text="hi there", start_time=0.0, end_time=1.0, words=words)
        
        new_words = TimingManager.redistribute_word_timings(segment, "hi")
        
        assert len(new_words) == 1
        assert new_words[0].text == "hi"
        assert new_words[0].duration == 1.0

    def test_segment_no_words_adjust_boundaries(self):
        segment = Segment(id="s1", text="test", start_time=0.0, end_time=1.0)
        TimingManager.adjust_segment_boundaries(segment, 0.5, 2.0)
        
        assert segment.start_time == 0.5
        assert segment.end_time == 2.0

    def test_segment_no_words_set_duration(self):
        segment = Segment(id="s1", text="test", start_time=0.0, end_time=1.0)
        TimingManager.set_segment_duration(segment, 2.0)
        
        assert segment.duration == 2.0
