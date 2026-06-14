import numpy as np
import pytest

from lyrics.onset_refiner import (
    BREATH_DURATION_THRESHOLD,
    MIN_SEGMENT_DURATION,
    MIN_WORD_DURATION,
    ONSET_MERGE_THRESHOLD,
    SNAP_TOLERANCE_INTERPOLATED,
    SNAP_TOLERANCE_TRANSCRIPTION,
    OnsetSegment,
    WordAssignment,
    assign_onset_segments_to_words,
    assign_onsets_to_words,
    build_onset_segments,
    build_word_assignments,
    classify_segments,
    compute_energy,
    compute_segment_word_confidence,
    merge_close_onsets,
    refine_line,
    refine_synced_lines,
    snap_words_to_onsets,
)
from lyrics.synchronizer import SyncResult, SyncedLine, SyncedWord


def _w(text="word", start=0.0, end=1.0, source="transcription"):
    return SyncedWord(text=text, start=start, end=end, source=source)


def _make_peaks(duration=2.0, pps=100, value=0.5):
    return [value] * int(duration * pps)


class TestMergeCloseOnsets:
    def test_empty(self):
        assert merge_close_onsets([]) == []

    def test_single(self):
        assert merge_close_onsets([1.0]) == [1.0]

    def test_two_close_onsets_merged(self):
        result = merge_close_onsets([1.0, 1.03], threshold=0.05)
        assert len(result) == 1
        assert result[0] == pytest.approx(1.015)

    def test_two_distant_onsets_kept(self):
        result = merge_close_onsets([1.0, 1.1], threshold=0.05)
        assert result == [1.0, 1.1]

    def test_three_close_onsets_merged_into_one(self):
        result = merge_close_onsets([1.0, 1.02, 1.04], threshold=0.05)
        assert len(result) == 1

    def test_chain_merge(self):
        result = merge_close_onsets([1.0, 1.02, 1.04, 1.06], threshold=0.05)
        assert len(result) == 1

    def test_multiple_groups(self):
        onsets = [1.0, 1.03, 2.0, 2.03, 3.0]
        result = merge_close_onsets(onsets, threshold=0.05)
        assert len(result) == 3
        assert result[0] == pytest.approx(1.015)
        assert result[1] == pytest.approx(2.015)
        assert result[2] == 3.0

    def test_default_threshold(self):
        close = [1.0, 1.0 + ONSET_MERGE_THRESHOLD - 0.001]
        result = merge_close_onsets(close)
        assert len(result) == 1

    def test_custom_threshold(self):
        result = merge_close_onsets([1.0, 1.2], threshold=0.3)
        assert len(result) == 1

    def test_unsorted_input_merges_adjacent(self):
        result = merge_close_onsets([1.0, 0.5, 1.5], threshold=0.05)
        assert len(result) == 2


class TestSnapWordsToOnsets:
    def test_single_word_snap(self):
        words = [_w("hello", start=1.02, end=1.5)]
        onsets = [1.0]
        result = snap_words_to_onsets(words, onsets, 0.0, 2.0)
        assert result[0].start == 1.0
        assert result[0].source == "whisper_plus_vocal_onset"

    def test_no_matching_onset_within_tolerance(self):
        words = [_w("hello", start=0.5, end=1.0, source="transcription")]
        onsets = [1.8]
        result = snap_words_to_onsets(words, onsets, 0.0, 2.0)
        assert result[0].start == 0.5
        assert result[0].source == "transcription"

    def test_interpolated_tolerance_is_wider(self):
        words = [_w("hello", start=0.5, end=1.0, source="interpolated")]
        onsets = [0.7]
        result = snap_words_to_onsets(words, onsets, 0.0, 2.0)
        assert result[0].start == 0.7
        assert result[0].source == "interpolated"

    def test_interpolated_tolerance_beyond_range(self):
        words = [_w("hello", start=0.5, end=1.0, source="interpolated")]
        onsets = [0.8]
        result = snap_words_to_onsets(words, onsets, 0.0, 2.0)
        assert result[0].start == 0.5

    def test_interpolated_outside_tolerance(self):
        words = [_w("hello", start=0.5, end=1.0, source="interpolated")]
        onsets = [0.8 + SNAP_TOLERANCE_INTERPOLATED + 0.01]
        result = snap_words_to_onsets(words, onsets, 0.0, 2.0)
        assert result[0].start == 0.5

    def test_multiple_words_multiple_onsets(self):
        words = [_w("hello", start=1.0, end=1.5), _w("world", start=2.0, end=2.5)]
        onsets = [1.02, 2.01]
        result = snap_words_to_onsets(words, onsets, 0.0, 3.0)
        assert result[0].start == 1.02
        assert result[1].start == 2.01

    def test_onset_not_reused_with_overlap_resolution(self):
        words = [_w("a", start=1.0, end=1.3), _w("b", start=1.05, end=1.5)]
        onsets = [1.02]
        result = snap_words_to_onsets(words, onsets, 0.0, 2.0)
        assert result[0].start == 1.02
        assert result[0].end <= result[1].start

    def test_last_word_end_set_to_line_end(self):
        words = [_w("hello", start=1.0, end=1.5)]
        onsets = [1.02]
        result = snap_words_to_onsets(words, onsets, 0.0, 2.5)
        assert result[0].end == 2.5

    def test_overlap_resolution(self):
        words = [_w("a", start=1.0, end=1.6), _w("b", start=1.4, end=2.0)]
        onsets = []
        result = snap_words_to_onsets(words, onsets, 0.0, 2.0)
        assert result[0].end <= result[1].start

    def test_start_after_end_gets_min_duration(self):
        words = [_w("a", start=1.5, end=1.3, source="transcription")]
        onsets = [1.5]
        result = snap_words_to_onsets(words, onsets, 0.0, 2.0)
        assert result[0].end - result[0].start >= MIN_WORD_DURATION

    def test_vocal_onset_source_upgrade(self):
        words = [_w("a", start=1.0, end=1.5, source="vocal_onset")]
        onsets = [1.02]
        result = snap_words_to_onsets(words, onsets, 0.0, 2.0)
        assert result[0].source == "whisper_plus_vocal_onset"


class TestAssignOnsetsToWords:
    def test_empty_words(self):
        result = assign_onsets_to_words([], [1.0, 2.0], 0.0, 3.0)
        assert result == []

    def test_empty_onsets(self):
        words = [_w("hello", 1.0, 2.0)]
        result = assign_onsets_to_words(words, [], 0.0, 3.0)
        assert result[0].source == "interpolated"

    def test_equal_words_onsets(self):
        words = [_w("hello", 0.0, 1.0), _w("world", 1.0, 2.0)]
        onsets = [1.0, 2.0]
        result = assign_onsets_to_words(words, onsets, 0.0, 3.0)
        assert result[0].source == "vocal_onset_only"
        assert result[1].source == "vocal_onset_only"

    def test_more_onsets_than_words(self):
        words = [_w("hello", 0.5, 1.5)]
        onsets = [0.5, 1.0, 1.5]
        result = assign_onsets_to_words(words, onsets, 0.0, 2.0)
        assert result[0].source == "vocal_onset_only"

    def test_more_words_than_onsets(self):
        words = [_w("a", 0.5, 1.0), _w("b", 1.0, 1.5), _w("c", 1.5, 2.0)]
        onsets = [1.0]
        result = assign_onsets_to_words(words, onsets, 0.0, 2.0)
        sources = [w.source for w in result]
        assert "vocal_onset_only" in sources

    def test_single_word_single_onset(self):
        words = [_w("hello", 0.0, 2.0)]
        onsets = [1.0]
        result = assign_onsets_to_words(words, onsets, 0.0, 2.0)
        assert result[0].start == 1.0
        assert result[0].source == "vocal_onset_only"
        assert result[0].end == 2.0

    def test_zero_length_text_words(self):
        words = [_w("", 0.5, 1.0), _w("", 1.0, 1.5)]
        onsets = [0.5, 1.0]
        result = assign_onsets_to_words(words, onsets, 0.0, 2.0)
        assert len(result) == 2


class TestBuildOnsetSegments:
    def test_no_onsets_produces_single_segment(self):
        segs = build_onset_segments([], 1.0, 3.0)
        assert len(segs) == 1
        assert segs[0].start == 1.0
        assert segs[0].end == 3.0
        assert segs[0].duration == 2.0

    def test_no_onsets_tiny_duration(self):
        segs = build_onset_segments([], 1.0, 1.001)
        assert len(segs) == 0

    def test_single_onset(self):
        segs = build_onset_segments([1.5], 1.0, 2.0)
        assert len(segs) == 2
        assert segs[0].start == 1.0
        assert segs[0].end == 1.5
        assert segs[1].start == 1.5
        assert segs[1].end == 2.0

    def test_multiple_onsets(self):
        segs = build_onset_segments([1.0, 2.0, 3.0], 0.0, 4.0)
        assert len(segs) == 4
        assert segs[0].start == 0.0
        assert segs[-1].end == 4.0

    def test_segment_below_min_duration_skipped(self):
        segs = build_onset_segments([1.0, 1.001], 0.0, 2.0)
        assert all(s.duration >= MIN_SEGMENT_DURATION for s in segs)

    def test_with_peaks_energy(self):
        peaks = _make_peaks(duration=4.0, pps=100, value=0.8)
        segs = build_onset_segments([1.0, 2.0], 0.0, 3.0, peaks, pps=100)
        for seg in segs:
            assert seg.energy > 0

    def test_without_peaks_zero_energy(self):
        segs = build_onset_segments([1.0], 0.0, 2.0)
        for seg in segs:
            assert seg.energy == 0.0

    def test_segment_indices_sequential(self):
        segs = build_onset_segments([1.0, 2.0], 0.0, 3.0)
        indices = [s.segment_idx for s in segs]
        assert indices == sorted(indices)


class TestComputeEnergy:
    def test_none_peaks(self):
        assert compute_energy(0.0, 1.0, None, 100) == 0.0

    def test_empty_peaks(self):
        assert compute_energy(0.0, 1.0, [], 100) == 0.0

    def test_zero_pps(self):
        assert compute_energy(0.0, 1.0, [0.5] * 100, 0) == 0.0

    def test_valid_peaks(self):
        peaks = [1.0] * 200
        energy = compute_energy(0.0, 1.0, peaks, 100)
        assert energy == pytest.approx(1.0)

    def test_partial_overlap(self):
        peaks = [0.0] * 50 + [1.0] * 50 + [0.0] * 100
        energy = compute_energy(0.5, 1.0, peaks, 100)
        assert energy == pytest.approx(1.0)

    def test_out_of_range_returns_zero(self):
        peaks = [0.5] * 100
        assert compute_energy(5.0, 6.0, peaks, 100) == 0.0

    def test_segment_shorter_than_one_sample(self):
        peaks = [0.5] * 100
        energy = compute_energy(0.5, 0.505, peaks, 100)
        assert energy == 0.0


class TestAssignOnsetSegmentsToWords:
    def test_no_overlap(self):
        segs = [OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0)]
        words = [_w("hello", start=2.0, end=3.0)]
        assign_onset_segments_to_words(segs, words)
        assert segs[0].assigned_word_indices == []
        assert segs[0].assigned_text == ""

    def test_full_overlap(self):
        segs = [OnsetSegment(segment_idx=0, start=0.0, end=2.0, duration=2.0)]
        words = [_w("hello", start=0.0, end=1.0), _w("world", start=1.0, end=2.0)]
        assign_onset_segments_to_words(segs, words)
        assert segs[0].assigned_word_indices == [0, 1]
        assert segs[0].assigned_text == "hello world"

    def test_partial_overlap(self):
        segs = [OnsetSegment(segment_idx=0, start=0.5, end=1.5, duration=1.0)]
        words = [_w("hello", start=0.0, end=1.0)]
        assign_onset_segments_to_words(segs, words)
        assert segs[0].assigned_word_indices == [0]

    def test_multiple_segments(self):
        segs = [
            OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0),
            OnsetSegment(segment_idx=1, start=1.0, end=2.0, duration=1.0),
        ]
        words = [_w("hello", start=0.0, end=1.0), _w("world", start=1.0, end=2.0)]
        assign_onset_segments_to_words(segs, words)
        assert segs[0].assigned_word_indices == [0]
        assert segs[1].assigned_word_indices == [1]

    def test_resets_previous_assignments(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=2.0, duration=2.0,
                           assigned_word_indices=[99], assigned_text="old")
        words = [_w("hello", start=0.0, end=1.0)]
        assign_onset_segments_to_words([seg], words)
        assert seg.assigned_word_indices == [0]
        assert seg.assigned_text == "hello"


class TestClassifySegments:
    def test_lyric_classification(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=2.0, duration=2.0,
                           assigned_word_indices=[0])
        words = [_w("hello", start=0.0, end=2.0)]
        classify_segments([seg], words)
        assert seg.classification == "lyric"
        assert seg.confidence >= 0.5

    def test_breath_classification(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=0.05, duration=0.05,
                           assigned_word_indices=[])
        words = [_w("hello", start=1.0, end=2.0)]
        classify_segments([seg], words)
        assert seg.classification == "breath"

    def test_noise_classification(self):
        high_seg = OnsetSegment(segment_idx=0, start=0.0, end=0.5, duration=0.5,
                                assigned_word_indices=[0], energy=0.9)
        low_seg = OnsetSegment(segment_idx=1, start=0.5, end=0.8, duration=0.3,
                               assigned_word_indices=[], energy=0.001)
        words = [_w("hello", start=0.0, end=0.5)]
        classify_segments([high_seg, low_seg], words)
        assert low_seg.classification == "noise"

    def test_unassigned_classification(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=0.5, duration=0.5,
                           assigned_word_indices=[], energy=0.5)
        words = [_w("hello", start=1.0, end=2.0)]
        classify_segments([seg], words)
        assert seg.classification == "unassigned"

    def test_unknown_classification_unassigned(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=0.2, duration=0.2,
                           assigned_word_indices=[], energy=0.5)
        words = [_w("hello", start=1.0, end=2.0)]
        classify_segments([seg], words)
        assert seg.classification == "unknown"

    def test_low_confidence_assigned(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=2.0, duration=2.0,
                           assigned_word_indices=[0])
        words = [_w("hello", start=1.9, end=2.0)]
        classify_segments([seg], words)
        assert seg.classification == "unknown"
        assert "low_confidence_assignment" in seg.warnings

    def test_empty_segments(self):
        classify_segments([], [])
        assert True

    def test_breath_boundary(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=BREATH_DURATION_THRESHOLD - 0.01,
                           duration=BREATH_DURATION_THRESHOLD - 0.01,
                           assigned_word_indices=[])
        classify_segments([seg], [])
        assert seg.classification == "breath"


class TestComputeSegmentWordConfidence:
    def test_no_assigned_words(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0,
                           assigned_word_indices=[])
        assert compute_segment_word_confidence(seg, []) == 0.0

    def test_full_coverage(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0,
                           assigned_word_indices=[0])
        words = [_w("hello", start=0.0, end=1.0)]
        conf = compute_segment_word_confidence(seg, words)
        assert conf > 0.5

    def test_partial_coverage(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=2.0, duration=2.0,
                           assigned_word_indices=[0])
        words = [_w("hello", start=0.0, end=0.5)]
        conf = compute_segment_word_confidence(seg, words)
        assert 0.0 < conf < 1.0

    def test_zero_duration_segment(self):
        seg = OnsetSegment(segment_idx=0, start=1.0, end=1.0, duration=0.0,
                           assigned_word_indices=[0])
        words = [_w("hello", start=0.0, end=1.0)]
        assert compute_segment_word_confidence(seg, words) == 0.0

    def test_multiple_assigned_words(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=2.0, duration=2.0,
                           assigned_word_indices=[0, 1])
        words = [_w("hello", start=0.0, end=1.0), _w("world", start=1.0, end=2.0)]
        conf = compute_segment_word_confidence(seg, words)
        assert conf > 0.8


class TestBuildWordAssignments:
    def test_basic_assignments(self):
        words = [_w("hello", 0.0, 1.0), _w("world", 1.0, 2.0)]
        segs = [
            OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0),
            OnsetSegment(segment_idx=1, start=1.0, end=2.0, duration=1.0),
        ]
        result = build_word_assignments(words, segs, 0.0, 2.0)
        assert len(result) == 2
        assert result[0].text == "hello"
        assert result[1].text == "world"

    def test_confidence_by_source(self):
        words = [_w("a", 0.0, 1.0, "whisper_plus_vocal_onset")]
        segs = [OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0)]
        result = build_word_assignments(words, segs, 0.0, 1.0)
        assert result[0].confidence == 0.8

    def test_transcription_confidence(self):
        words = [_w("a", 0.0, 1.0, "transcription")]
        segs = [OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0)]
        result = build_word_assignments(words, segs, 0.0, 1.0)
        assert result[0].confidence == 0.7

    def test_vocal_onset_only_confidence(self):
        words = [_w("a", 0.0, 1.0, "vocal_onset_only")]
        segs = [OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0)]
        result = build_word_assignments(words, segs, 0.0, 1.0)
        assert result[0].confidence == 0.6

    def test_interpolated_confidence(self):
        words = [_w("a", 0.0, 1.0, "interpolated")]
        segs = [OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0)]
        result = build_word_assignments(words, segs, 0.0, 1.0)
        assert result[0].confidence == 0.3

    def test_unknown_source_gets_default(self):
        words = [_w("a", 0.0, 1.0, "something_else")]
        segs = [OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0)]
        result = build_word_assignments(words, segs, 0.0, 1.0)
        assert result[0].source == "interpolated"

    def test_grouping_same_segments(self):
        words = [_w("a", 0.0, 0.5), _w("b", 0.5, 1.0)]
        segs = [OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0)]
        result = build_word_assignments(words, segs, 0.0, 1.0)
        assert result[0].group_id == result[1].group_id
        assert result[0].group_text == "a b"

    def test_no_segments_no_group(self):
        words = [_w("a", 0.0, 1.0)]
        result = build_word_assignments(words, [], 0.0, 1.0)
        assert result[0].group_id is None
        assert result[0].group_text is None

    def test_empty_words(self):
        result = build_word_assignments([], [], 0.0, 1.0)
        assert result == []

    def test_assignment_indices(self):
        words = [_w("a", 0.0, 1.0), _w("b", 1.0, 2.0), _w("c", 2.0, 3.0)]
        segs = [OnsetSegment(segment_idx=0, start=0.0, end=3.0, duration=3.0)]
        result = build_word_assignments(words, segs, 0.0, 3.0)
        assert [a.assignment_idx for a in result] == [0, 1, 2]


class TestRefineLine:
    def test_no_words(self):
        words, segs, assigns, warns = refine_line([], [1.0], 0.0, 2.0)
        assert words == []
        assert segs == []
        assert assigns == []

    def test_no_onsets_interpolated_fallback(self):
        words = [_w("hello", 0.5, 1.5)]
        result_words, segs, assigns, warns = refine_line(words, [], 0.0, 2.0)
        assert "no_onsets_in_line" in warns

    def test_transcription_words_snapped(self):
        words = [_w("hello", 1.02, end=2.0, source="transcription")]
        onsets = [1.0]
        result_words, segs, assigns, warns = refine_line(words, onsets, 0.0, 2.0)
        assert result_words[0].start == 1.0
        assert result_words[0].source == "whisper_plus_vocal_onset"

    def test_interpolated_words_dp_assigned(self):
        words = [_w("hello", 0.5, 1.5, source="interpolated"),
                 _w("world", 1.5, 2.5, source="interpolated")]
        onsets = [1.0, 2.0]
        result_words, segs, assigns, warns = refine_line(words, onsets, 0.0, 3.0)
        assert any(w.source == "vocal_onset_only" for w in result_words)

    def test_short_word_warning(self):
        words = [_w("a", 1.0, 1.02, source="transcription"),
                 _w("b", 1.5, 2.0, source="transcription")]
        onsets = [1.0, 1.5]
        _, _, _, warns = refine_line(words, onsets, 0.0, 2.5)
        assert any("word_duration_very_short" in w for w in warns)

    def test_long_word_warning(self):
        words = [_w("a" * 50, 0.0, 3.0, source="transcription")]
        onsets = [0.0]
        _, _, _, warns = refine_line(words, onsets, 0.0, 3.5)
        assert any("word_duration_very_long" in w for w in warns)

    def test_onset_count_mismatch_warning(self):
        words = [_w("a", 0.0, 0.5), _w("b", 0.5, 1.0)]
        onsets = [0.1, 0.2, 0.3, 0.4]
        _, _, _, warns = refine_line(words, onsets, 0.0, 1.0)
        assert any("onset_count_mismatch" in w for w in warns)

    def test_returns_segments_and_assignments(self):
        words = [_w("hello", 1.0, 2.0, source="transcription")]
        onsets = [1.0]
        _, segs, assigns, _ = refine_line(words, onsets, 0.0, 2.0)
        assert len(segs) > 0
        assert len(assigns) > 0


class TestRefineSyncedLines:
    def test_basic_refinement(self):
        words = [_w("hello", 1.02, 1.5, "transcription"),
                 _w("world", 1.52, 2.0, "transcription")]
        line = SyncedLine(text="hello world", start=1.0, end=2.0, words=words)
        sr = SyncResult(lines=[line])
        onsets = np.array([1.0, 1.5])
        result = refine_synced_lines(sr, onsets)
        assert len(result.lines) == 1
        assert result.lines[0].words[0].start == 1.0

    def test_empty_line_skipped(self):
        line = SyncedLine(text="", start=0.0, end=1.0, words=[])
        sr = SyncResult(lines=[line])
        result = refine_synced_lines(sr, np.array([0.5]))
        assert result.lines[0].words == []

    def test_multiple_lines(self):
        l1 = SyncedLine(text="hello", start=0.0, end=1.0,
                        words=[_w("hello", 0.0, 1.0, "transcription")])
        l2 = SyncedLine(text="world", start=1.0, end=2.0,
                        words=[_w("world", 1.0, 2.0, "transcription")])
        sr = SyncResult(lines=[l1, l2])
        onsets = np.array([0.0, 1.0])
        result = refine_synced_lines(sr, onsets)
        assert len(result.lines) == 2

    def test_min_word_duration_enforcement(self):
        words = [_w("a", 1.0, 1.005, "transcription")]
        line = SyncedLine(text="a", start=1.0, end=2.0, words=words)
        sr = SyncResult(lines=[line])
        result = refine_synced_lines(sr, np.array([1.0]))
        assert result.lines[0].words[0].end - result.lines[0].words[0].start >= MIN_WORD_DURATION

    def test_overlap_fixup(self):
        words = [_w("a", 1.0, 1.5, "transcription"),
                 _w("b", 1.3, 2.0, "transcription")]
        line = SyncedLine(text="a b", start=1.0, end=2.0, words=words)
        sr = SyncResult(lines=[line])
        result = refine_synced_lines(sr, np.array([1.0, 1.3]))
        w = result.lines[0].words
        assert w[0].end <= w[1].start

    def test_last_word_trimmed_not_stretched_to_line_end(self):
        words = [_w("hello", 1.0, 1.5, "transcription")]
        line = SyncedLine(text="hello", start=1.0, end=3.0, words=words)
        sr = SyncResult(lines=[line])
        result = refine_synced_lines(sr, np.array([1.0]))
        last = result.lines[0].words[-1]
        assert last.end < 3.0
        assert last.end == 2.5

    def test_with_waveform_peaks(self):
        peaks = [0.5] * 300
        words = [_w("hello", 0.5, 1.5, "transcription")]
        line = SyncedLine(text="hello", start=0.0, end=2.0, words=words)
        sr = SyncResult(lines=[line])
        result = refine_synced_lines(sr, np.array([0.5]), waveform_peaks=peaks, peaks_per_second=100)
        assert result.lines[0].onset_segments is not None

    def test_onsets_outside_line_ignored(self):
        words = [_w("hello", 1.0, 2.0, "transcription")]
        line = SyncedLine(text="hello", start=1.0, end=2.0, words=words)
        sr = SyncResult(lines=[line])
        result = refine_synced_lines(sr, np.array([0.0, 5.0]))
        assert "no_onsets_in_line" in result.lines[0].warnings

    def test_empty_sync_result(self):
        sr = SyncResult(lines=[])
        result = refine_synced_lines(sr, np.array([1.0]))
        assert result.lines == []


class TestOnsetSegmentDataclass:
    def test_defaults(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0)
        assert seg.classification == "unknown"
        assert seg.assigned_word_indices == []
        assert seg.assigned_text == ""
        assert seg.confidence == 0.0
        assert seg.warnings == []
        assert seg.energy == 0.0

    def test_to_dict(self):
        seg = OnsetSegment(segment_idx=0, start=0.12345, end=1.23456,
                           duration=1.11111, classification="lyric",
                           assigned_word_indices=[0, 1], assigned_text="hello world",
                           confidence=0.8765, energy=0.12345)
        d = seg.to_dict()
        assert d["segment_idx"] == 0
        assert d["start"] == 0.123
        assert d["end"] == 1.235
        assert d["duration"] == 1.111
        assert d["classification"] == "lyric"
        assert d["assigned_word_indices"] == [0, 1]
        assert d["assigned_text"] == "hello world"
        assert d["confidence"] == round(0.8765, 3)
        assert d["energy"] == round(0.12345, 4)

    def test_to_dict_with_warnings(self):
        seg = OnsetSegment(segment_idx=0, start=0.0, end=1.0, duration=1.0,
                           warnings=["test_warning"])
        d = seg.to_dict()
        assert d["warnings"] == ["test_warning"]

    def test_custom_fields(self):
        seg = OnsetSegment(segment_idx=5, start=1.0, end=2.0, duration=1.0,
                           classification="breath", confidence=0.5,
                           assigned_word_indices=[2], assigned_text="hi",
                           energy=0.1, warnings=["a", "b"])
        assert seg.segment_idx == 5
        assert seg.classification == "breath"
        assert seg.confidence == 0.5
        assert len(seg.warnings) == 2


class TestWordAssignmentDataclass:
    def test_defaults(self):
        wa = WordAssignment(assignment_idx=0, text="hello", word_index=0)
        assert wa.group_id is None
        assert wa.group_text is None
        assert wa.segment_indices == []
        assert wa.start == 0.0
        assert wa.end == 0.0
        assert wa.source == "interpolated"
        assert wa.confidence == 0.0
        assert wa.warnings == []

    def test_to_dict_basic(self):
        wa = WordAssignment(assignment_idx=0, text="hello", word_index=0,
                            segment_indices=[0, 1], start=1.0, end=2.0,
                            source="whisper_plus_vocal_onset", confidence=0.8)
        d = wa.to_dict()
        assert d["assignment_idx"] == 0
        assert d["text"] == "hello"
        assert d["word_index"] == 0
        assert d["segment_indices"] == [0, 1]
        assert d["start"] == 1.0
        assert d["end"] == 2.0
        assert d["source"] == "whisper_plus_vocal_onset"
        assert d["confidence"] == 0.8
        assert "group_id" not in d
        assert "group_text" not in d
        assert "warnings" not in d

    def test_to_dict_with_group(self):
        wa = WordAssignment(assignment_idx=0, text="hello", word_index=0,
                            group_id=1, group_text="hello world")
        d = wa.to_dict()
        assert d["group_id"] == 1
        assert d["group_text"] == "hello world"

    def test_to_dict_with_warnings(self):
        wa = WordAssignment(assignment_idx=0, text="hello", word_index=0,
                            warnings=["warn1"])
        d = wa.to_dict()
        assert d["warnings"] == ["warn1"]

    def test_to_dict_no_warnings_key_when_empty(self):
        wa = WordAssignment(assignment_idx=0, text="hello", word_index=0)
        d = wa.to_dict()
        assert "warnings" not in d

    def test_rounding_in_to_dict(self):
        wa = WordAssignment(assignment_idx=0, text="x", word_index=0,
                            start=1.23456, end=2.34567, confidence=0.87654)
        d = wa.to_dict()
        assert d["start"] == round(1.23456, 3)
        assert d["end"] == round(2.34567, 3)
        assert d["confidence"] == round(0.87654, 3)


class TestEdgeCases:
    def test_onsets_exactly_at_boundaries(self):
        segs = build_onset_segments([0.0, 2.0], 0.0, 2.0)
        assert len(segs) >= 1

    def test_word_exact_match_onset(self):
        words = [_w("hello", start=1.0, end=2.0, source="transcription")]
        onsets = [1.0]
        result = snap_words_to_onsets(words, onsets, 0.0, 2.0)
        assert result[0].start == 1.0

    def test_very_close_onsets_not_merged(self):
        onsets = [1.0, 1.0 + ONSET_MERGE_THRESHOLD + 0.001]
        result = merge_close_onsets(onsets)
        assert len(result) == 2

    def test_segment_overlap_with_word_at_boundary(self):
        seg = OnsetSegment(segment_idx=0, start=1.0, end=2.0, duration=1.0)
        words = [_w("hello", start=2.0, end=3.0)]
        seg.assigned_word_indices = []
        for wi, w in enumerate(words):
            overlap_start = max(seg.start, w.start)
            overlap_end = min(seg.end, w.end)
            assert not (overlap_end > overlap_start)
        assert seg.assigned_word_indices == []

    def test_refine_line_interpolated_fallback_warning(self):
        words = [_w("a", 0.5, 1.0, "interpolated"), _w("b", 1.0, 1.5, "interpolated")]
        onsets = []
        _, _, _, warns = refine_line(words, onsets, 0.0, 2.0)
        assert "no_onsets_in_line" in warns

    def test_compute_energy_with_list(self):
        peaks = [0.5] * 200
        energy = compute_energy(0.0, 1.0, peaks, 100)
        assert energy == pytest.approx(0.5)

    def test_refine_synced_lines_with_peaks_slicing(self):
        peaks = [0.5] * 300
        words = [_w("hello", 0.5, 1.5, "transcription")]
        line = SyncedLine(text="hello", start=0.0, end=2.0, words=words)
        sr = SyncResult(lines=[line])
        result = refine_synced_lines(sr, np.array([0.5]), waveform_peaks=peaks, peaks_per_second=100)
        assert result.lines[0].onset_segments is not None


class TestRefineSyncedLinesEdgeCases:
    def test_short_word_duration_enforced(self):
        words = [_w("a", 1.95, 2.0, "transcription"), _w("b", 2.0, 2.5, "transcription")]
        line = SyncedLine(text="a b", start=1.9, end=2.5, words=words)
        sr = SyncResult(lines=[line])
        result = refine_synced_lines(sr, np.array([1.99, 2.1]))
        assert result.lines[0].words[0].end - result.lines[0].words[0].start >= MIN_WORD_DURATION - 0.001

    def test_overlapping_words_after_duration_fix(self):
        words = [_w("a", 1.97, 1.98, "transcription"), _w("b", 1.98, 1.99, "transcription")]
        line = SyncedLine(text="a b", start=1.9, end=2.5, words=words)
        sr = SyncResult(lines=[line])
        result = refine_synced_lines(sr, np.array([1.97, 1.98]))
        for i in range(len(result.lines[0].words) - 1):
            assert result.lines[0].words[i].end <= result.lines[0].words[i + 1].start


class TestAssignOnsetsToWordsEdgeCases:
    def test_dp_many_onsets_few_words(self):
        words = [_w("a", 0.0, 0.5, "interpolated"), _w("b", 0.5, 1.0, "interpolated")]
        onsets = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        result = assign_onsets_to_words(words, onsets, 0.0, 1.0)
        assert len(result) == 2

    def test_last_onset_only_word_boundary(self):
        words = [_w("a", 0.0, 0.5, "interpolated"), _w("b", 0.5, 1.0, "interpolated"), _w("c", 1.0, 1.5, "interpolated")]
        onsets = [0.1, 0.9]
        result = assign_onsets_to_words(words, onsets, 0.0, 1.5)
        assert len(result) == 3
        assert result[1].source == "vocal_onset_only"

    def test_single_word_single_onset(self):
        words = [_w("hello", 0.0, 1.0, "interpolated")]
        onsets = [0.5]
        result = assign_onsets_to_words(words, onsets, 0.0, 1.0)
        assert result[0].source == "vocal_onset_only"

    def test_onset_first_then_interpolated_no_onset_ahead(self):
        words = [_w("longwordhere", 0.0, 0.33, "interpolated"),
                 _w("b", 0.33, 0.67, "interpolated"),
                 _w("c", 0.67, 1.0, "interpolated")]
        onsets = [0.05]
        result = assign_onsets_to_words(words, onsets, 0.0, 1.0)
        assert result[0].source == "vocal_onset_only"
        assert result[1].source == "interpolated"
        assert result[2].source == "interpolated"


class TestInterpolateWordsFunction:
    def test_basic_interpolation(self):
        words = [_w("a", 0.0, 0.5, "onset"), _w("b", 0.5, 1.0, "onset")]
        from lyrics.onset_refiner import _interpolate_words
        result = _interpolate_words(words, 0.0, 2.0)
        assert len(result) == 2
        assert result[0].start == 0.0
        assert result[1].end == 2.0
        assert result[0].source == "interpolated"
        assert result[1].source == "interpolated"

    def test_empty_words(self):
        from lyrics.onset_refiner import _interpolate_words
        result = _interpolate_words([], 0.0, 1.0)
        assert result == []


class TestAssignOnsetsNoOverlap:
    def _check_no_overlap(self, words):
        for i in range(len(words) - 1):
            for j in range(i + 1, len(words)):
                assert words[i].end <= words[j].start + 0.001, (
                    f"W{i} \"{words[i].text}\" end={words[i].end:.3f} overlaps "
                    f"W{j} \"{words[j].text}\" start={words[j].start:.3f}"
                )

    def _check_temporal_order(self, words):
        for i in range(len(words) - 1):
            assert words[i].start <= words[i + 1].start + 0.001, (
                f"W{i} start={words[i].start:.3f} > W{i+1} start={words[i+1].start:.3f}"
            )

    def test_sparse_onsets_no_overlap(self):
        words = [_w("Closing", 0.0, 0.1), _w("the", 0.1, 0.2),
                 _w("gaps", 0.2, 0.3), _w("of", 0.3, 0.4),
                 _w("my", 0.4, 0.5), _w("origin", 0.5, 0.6)]
        onsets = [0.02, 0.3]
        result = assign_onsets_to_words(words, onsets, 0.0, 0.6)
        self._check_no_overlap(result)
        self._check_temporal_order(result)

    def test_onset_word_duration_capped(self):
        words = [_w("A", 0.0, 0.5), _w("B", 0.5, 1.0)]
        onsets = [0.01, 0.9]
        result = assign_onsets_to_words(words, onsets, 0.0, 1.0)
        assert result[0].source == "vocal_onset_only"
        assert result[0].end < 0.9

    def test_all_interpolated_after_onsets(self):
        words = [_w("one", 0.0, 0.25), _w("two", 0.25, 0.5),
                 _w("three", 0.5, 0.75), _w("four", 0.75, 1.0)]
        onsets = [0.1]
        result = assign_onsets_to_words(words, onsets, 0.0, 1.0)
        self._check_no_overlap(result)
        self._check_temporal_order(result)
        onset_words = [w for w in result if w.source == "vocal_onset_only"]
        interp_words = [w for w in result if w.source == "interpolated"]
        assert len(onset_words) >= 1
        assert len(interp_words) >= 1

    def test_multiple_onset_groups(self):
        words = [_w("a", 0.0, 0.1), _w("b", 0.1, 0.2), _w("c", 0.2, 0.3),
                 _w("d", 0.3, 0.4), _w("e", 0.4, 0.5)]
        onsets = [0.05, 0.35]
        result = assign_onsets_to_words(words, onsets, 0.0, 0.5)
        self._check_no_overlap(result)
        self._check_temporal_order(result)

    def test_no_overlap_through_refine(self):
        words = [_w("Closing", 63.95, 64.01), _w("the", 64.01, 64.07),
                 _w("gaps", 64.07, 64.13), _w("of", 64.13, 64.19),
                 _w("my", 64.19, 64.25), _w("origin", 64.25, 64.31)]
        line = SyncedLine(text="Closing the gaps of my origin", start=63.95, end=64.31, words=words)
        sr = SyncResult(lines=[line])
        result = refine_synced_lines(sr, np.array([63.968, 64.267]))
        self._check_no_overlap(result.lines[0].words)
        self._check_temporal_order(result.lines[0].words)
