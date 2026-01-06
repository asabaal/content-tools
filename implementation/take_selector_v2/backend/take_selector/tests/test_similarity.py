"""
Test suite for similarity scoring module.
"""

import pytest

from take_selector import Segment, compute_segment_similarity, find_candidate_duplicates


class TestComputeSegmentSimilarity:
    """Tests for compute_segment_similarity function."""
    
    def test_identical_text_high_similarity(self):
        """Test that identical segments have similarity of 1.0."""
        segment_a = Segment("1", 0.0, 5.0, "hello world")
        segment_b = Segment("2", 0.0, 5.0, "hello world")
        
        similarity = compute_segment_similarity(segment_a, segment_b)
        
        assert similarity == 1.0
    
    def test_identical_text_different_case(self):
        """Test case insensitivity - identical text with different cases."""
        segment_a = Segment("1", 0.0, 5.0, "Hello World")
        segment_b = Segment("2", 0.0, 5.0, "hello world")
        
        similarity = compute_segment_similarity(segment_a, segment_b)
        
        assert similarity == 1.0
    
    def test_very_different_text_low_similarity(self):
        """Test that completely different text has low similarity."""
        segment_a = Segment("1", 0.0, 5.0, "hello world")
        segment_b = Segment("2", 0.0, 5.0, "foo bar baz")
        
        similarity = compute_segment_similarity(segment_a, segment_b)
        
        assert similarity == 0.0
    
    def test_partial_word_overlap(self):
        """Test partial overlap of words."""
        segment_a = Segment("1", 0.0, 5.0, "hello world test")
        segment_b = Segment("2", 0.0, 5.0, "hello universe test")
        
        similarity = compute_segment_similarity(segment_a, segment_b)
        
        assert similarity == 0.5  # 2 words out of 4
    
    def test_empty_text_both(self):
        """Test that two empty segments are considered similar."""
        segment_a = Segment("1", 0.0, 5.0, "")
        segment_b = Segment("2", 0.0, 5.0, "")
        
        similarity = compute_segment_similarity(segment_a, segment_b)
        
        assert similarity == 1.0
    
    def test_empty_text_one_side(self):
        """Test that empty text vs non-empty text has zero similarity."""
        segment_a = Segment("1", 0.0, 5.0, "")
        segment_b = Segment("2", 0.0, 5.0, "hello world")
        
        similarity = compute_segment_similarity(segment_a, segment_b)
        
        assert similarity == 0.0
    
    def test_whitespace_only(self):
        """Test that whitespace-only text is treated as empty."""
        segment_a = Segment("1", 0.0, 5.0, "   ")
        segment_b = Segment("2", 0.0, 5.0, "hello world")
        
        similarity = compute_segment_similarity(segment_a, segment_b)
        
        assert similarity == 0.0
    
    def test_whitespace_both(self):
        """Test that two whitespace-only segments are considered similar."""
        segment_a = Segment("1", 0.0, 5.0, "   ")
        segment_b = Segment("2", 0.0, 5.0, "  \t\n  ")
        
        similarity = compute_segment_similarity(segment_a, segment_b)
        
        assert similarity == 1.0
    
    def test_single_word_identical(self):
        """Test similarity with single identical word."""
        segment_a = Segment("1", 0.0, 5.0, "hello")
        segment_b = Segment("2", 0.0, 5.0, "hello")
        
        similarity = compute_segment_similarity(segment_a, segment_b)
        
        assert similarity == 1.0
    
    def test_single_word_different(self):
        """Test similarity with single different word."""
        segment_a = Segment("1", 0.0, 5.0, "hello")
        segment_b = Segment("2", 0.0, 5.0, "world")
        
        similarity = compute_segment_similarity(segment_a, segment_b)
        
        assert similarity == 0.0
    
    def test_symmetry(self):
        """Test that similarity is symmetric (A,B == B,A)."""
        segment_a = Segment("1", 0.0, 5.0, "hello world test")
        segment_b = Segment("2", 0.0, 5.0, "hello universe test")
        
        similarity_ab = compute_segment_similarity(segment_a, segment_b)
        similarity_ba = compute_segment_similarity(segment_b, segment_a)
        
        assert similarity_ab == similarity_ba
    
    def test_score_bounds(self):
        """Test that all similarity scores are within [0.0, 1.0]."""
        segment_a = Segment("1", 0.0, 5.0, "hello world")
        segment_b = Segment("2", 0.0, 5.0, "hello world")
        segment_c = Segment("3", 0.0, 5.0, "completely different")
        segment_d = Segment("4", 0.0, 5.0, "")
        
        score_1 = compute_segment_similarity(segment_a, segment_b)
        score_2 = compute_segment_similarity(segment_a, segment_c)
        score_3 = compute_segment_similarity(segment_a, segment_d)
        
        assert 0.0 <= score_1 <= 1.0
        assert 0.0 <= score_2 <= 1.0
        assert 0.0 <= score_3 <= 1.0
    
    def test_repeated_words(self):
        """Test that repeated words are handled correctly (set semantics)."""
        segment_a = Segment("1", 0.0, 5.0, "hello hello hello")
        segment_b = Segment("2", 0.0, 5.0, "hello")
        
        similarity = compute_segment_similarity(segment_a, segment_b)
        
        assert similarity == 1.0  # Sets are identical
    
    def test_high_similarity_threshold(self):
        """Test segments with high similarity but not identical."""
        segment_a = Segment("1", 0.0, 5.0, "hello world test")
        segment_b = Segment("2", 0.0, 5.0, "hello world test another")
        
        similarity = compute_segment_similarity(segment_a, segment_b)
        
        assert 0.7 < similarity < 1.0


class TestFindCandidateDuplicates:
    """Tests for find_candidate_duplicates function."""
    
    def test_empty_segment_list(self):
        """Test with empty list of segments."""
        candidates = find_candidate_duplicates([], threshold=0.7)
        
        assert candidates == []
    
    def test_single_segment(self):
        """Test with single segment (no pairs possible)."""
        segments = [Segment("1", 0.0, 5.0, "hello world")]
        
        candidates = find_candidate_duplicates(segments, threshold=0.7)
        
        assert candidates == []
    
    def test_no_duplicates_below_threshold(self):
        """Test when all similarities are below threshold."""
        segments = [
            Segment("1", 0.0, 5.0, "hello world"),
            Segment("2", 0.0, 5.0, "foo bar baz"),
            Segment("3", 0.0, 5.0, "different text")
        ]
        
        candidates = find_candidate_duplicates(segments, threshold=0.9)
        
        assert candidates == []
    
    def test_identical_segments_found(self):
        """Test that identical segments are found as duplicates."""
        segments = [
            Segment("1", 0.0, 5.0, "hello world"),
            Segment("2", 0.0, 5.0, "hello world"),
            Segment("3", 0.0, 5.0, "different text")
        ]
        
        candidates = find_candidate_duplicates(segments, threshold=0.9)
        
        assert len(candidates) == 1
        assert candidates[0][0] == "1"
        assert candidates[0][1] == "2"
        assert candidates[0][2] == 1.0
    
    def test_multiple_duplicate_pairs(self):
        """Test with multiple duplicate pairs."""
        segments = [
            Segment("1", 0.0, 5.0, "hello world"),
            Segment("2", 0.0, 5.0, "hello world"),
            Segment("3", 0.0, 5.0, "foo bar"),
            Segment("4", 0.0, 5.0, "foo bar")
        ]
        
        candidates = find_candidate_duplicates(segments, threshold=0.9)
        
        assert len(candidates) == 2
        assert set((c[0], c[1]) for c in candidates) == {("1", "2"), ("3", "4")}
    
    def test_sorted_by_similarity(self):
        """Test that results are sorted by similarity in descending order."""
        segments = [
            Segment("1", 0.0, 5.0, "hello world"),
            Segment("2", 0.0, 5.0, "hello world"),
            Segment("3", 0.0, 5.0, "hello world test"),
            Segment("4", 0.0, 5.0, "hello")
        ]
        
        candidates = find_candidate_duplicates(segments, threshold=0.5)
        
        assert len(candidates) >= 2
        for i in range(len(candidates) - 1):
            assert candidates[i][2] >= candidates[i+1][2]
    
    def test_threshold_boundary(self):
        """Test that threshold boundary is correctly applied."""
        segments = [
            Segment("1", 0.0, 5.0, "hello world test"),
            Segment("2", 0.0, 5.0, "hello world another")
        ]
        
        candidates = find_candidate_duplicates(segments, threshold=0.5)
        assert len(candidates) > 0
        
        candidates_strict = find_candidate_duplicates(segments, threshold=0.51)
        assert len(candidates_strict) == 0
    
    def test_default_threshold(self):
        """Test that default threshold (0.7) is used when not specified."""
        segments = [
            Segment("1", 0.0, 5.0, "hello world"),
            Segment("2", 0.0, 5.0, "hello world test"),
            Segment("3", 0.0, 5.0, "foo bar baz")
        ]
        
        candidates = find_candidate_duplicates(segments)
        
        assert isinstance(candidates, list)
    
    def test_invalid_threshold_too_high(self):
        """Test that threshold > 1.0 raises ValueError."""
        segments = [Segment("1", 0.0, 5.0, "hello world")]
        
        with pytest.raises(ValueError, match="Threshold must be between 0.0 and 1.0"):
            find_candidate_duplicates(segments, threshold=1.1)
    
    def test_invalid_threshold_too_low(self):
        """Test that threshold < 0.0 raises ValueError."""
        segments = [Segment("1", 0.0, 5.0, "hello world")]
        
        with pytest.raises(ValueError, match="Threshold must be between 0.0 and 1.0"):
            find_candidate_duplicates(segments, threshold=-0.1)
    
    def test_zero_threshold_all_pairs(self):
        """Test with threshold=0.0 returns all segment pairs."""
        segments = [
            Segment("1", 0.0, 5.0, "hello"),
            Segment("2", 0.0, 5.0, "world"),
            Segment("3", 0.0, 5.0, "test")
        ]
        
        candidates = find_candidate_duplicates(segments, threshold=0.0)
        
        assert len(candidates) == 3  # C(3,2) = 3
    
    def test_pair_structure(self):
        """Test that returned tuples have correct structure."""
        segments = [
            Segment("seg_a", 0.0, 5.0, "hello world"),
            Segment("seg_b", 0.0, 5.0, "hello world")
        ]
        
        candidates = find_candidate_duplicates(segments, threshold=0.9)
        
        assert len(candidates) == 1
        segment_id_a, segment_id_b, similarity = candidates[0]
        
        assert isinstance(segment_id_a, str)
        assert isinstance(segment_id_b, str)
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0
    
    def test_no_self_comparison(self):
        """Test that segments are not compared to themselves."""
        segments = [
            Segment("1", 0.0, 5.0, "hello world"),
            Segment("2", 0.0, 5.0, "hello world")
        ]
        
        candidates = find_candidate_duplicates(segments, threshold=1.0)
        
        assert len(candidates) == 1
        assert candidates[0][0] != candidates[0][1]
