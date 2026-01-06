"""
Test suite for take_selector data loader.
"""

import json
import tempfile
import pytest
from pathlib import Path

from take_selector import Segment, Transcript, load_transcript, load_transcript_from_data_directory


@pytest.fixture
def sample_transcript_data():
    """
    Sample transcript data for testing.
    """
    return {
        "language": "en",
        "duration": 30.0,
        "segments": [
            {
                "text": "Hello world",
                "start": 0.0,
                "end": 5.0,
                "segment_id": "seg_001",
                "speaker": None
            },
            {
                "text": "This is a test",
                "start": 5.5,
                "end": 10.0,
                "segment_id": "seg_002",
                "speaker": None
            },
            {
                "text": "Another segment",
                "start": 10.5,
                "end": 15.0,
                "segment_id": "seg_003",
                "speaker": "speaker1"
            }
        ]
    }


@pytest.fixture
def sample_transcript_file(sample_transcript_data):
    """
    Create a temporary transcript file for testing.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_transcript_data, f)
        return f.name


class TestSegment:
    """Tests for Segment dataclass."""
    
    def test_segment_creation(self):
        """Test creating a Segment object."""
        segment = Segment(
            segment_id="test_001",
            start_time=0.0,
            end_time=5.0,
            text="Test text"
        )
        
        assert segment.segment_id == "test_001"
        assert segment.start_time == 0.0
        assert segment.end_time == 5.0
        assert segment.text == "Test text"
    
    def test_segment_duration_calculation(self):
        """Test segment duration calculation."""
        segment = Segment(
            segment_id="test_001",
            start_time=2.5,
            end_time=7.5,
            text="Test text"
        )
        
        assert segment.duration == 5.0


class TestTranscript:
    """Tests for Transcript dataclass."""
    
    def test_transcript_creation(self, sample_transcript_data):
        """Test creating a Transcript object."""
        segments = [
            Segment(
                segment_id=item['segment_id'],
                start_time=item['start'],
                end_time=item['end'],
                text=item['text']
            )
            for item in sample_transcript_data['segments']
        ]
        
        transcript = Transcript(
            language=sample_transcript_data['language'],
            duration=sample_transcript_data['duration'],
            segments=segments
        )
        
        assert transcript.language == "en"
        assert transcript.duration == 30.0
        assert len(transcript.segments) == 3
        assert transcript.segments[0].text == "Hello world"


class TestLoadTranscript:
    """Tests for load_transcript function."""
    
    def test_load_valid_transcript_file(self, sample_transcript_file):
        """Test loading a valid transcript file."""
        transcript = load_transcript(sample_transcript_file)
        
        assert isinstance(transcript, Transcript)
        assert transcript.language == "en"
        assert transcript.duration == 30.0
        assert len(transcript.segments) == 3
        
        # Verify first segment
        assert transcript.segments[0].segment_id == "seg_001"
        assert transcript.segments[0].start_time == 0.0
        assert transcript.segments[0].end_time == 5.0
        assert transcript.segments[0].text == "Hello world"
        assert transcript.segments[0].duration == 5.0
        
        # Verify second segment
        assert transcript.segments[1].segment_id == "seg_002"
        assert transcript.segments[1].start_time == 5.5
        assert transcript.segments[1].end_time == 10.0
        assert transcript.segments[1].text == "This is a test"
        assert transcript.segments[1].duration == 4.5
        
        # Verify third segment (with speaker field, which should be ignored)
        assert transcript.segments[2].segment_id == "seg_003"
        assert transcript.segments[2].start_time == 10.5
        assert transcript.segments[2].end_time == 15.0
        assert transcript.segments[2].text == "Another segment"
        assert transcript.segments[2].duration == 4.5
    
    def test_load_nonexistent_file(self):
        """Test loading a file that does not exist."""
        with pytest.raises(FileNotFoundError, match="Transcript file not found"):
            load_transcript("/nonexistent/path/transcript.json")
    
    def test_load_invalid_json(self):
        """Test loading a file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json {{{")
            invalid_file = f.name
        
        with pytest.raises(json.JSONDecodeError):
            load_transcript(invalid_file)
        
        Path(invalid_file).unlink()
    
    def test_load_missing_segments_field(self):
        """Test loading a transcript without segments field."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"language": "en", "duration": 10.0}, f)
            invalid_file = f.name
        
        with pytest.raises(ValueError, match="missing 'segments' field"):
            load_transcript(invalid_file)
        
        Path(invalid_file).unlink()
    
    def test_load_segment_missing_required_field(self):
        """Test loading a transcript with segments missing required fields."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "language": "en",
                "duration": 10.0,
                "segments": [
                    {
                        "text": "Missing segment_id",
                        "start": 0.0,
                        "end": 5.0
                    }
                ]
            }, f)
            invalid_file = f.name
        
        with pytest.raises(ValueError, match="missing required fields"):
            load_transcript(invalid_file)
        
        Path(invalid_file).unlink()
    
    def test_load_segment_with_extra_fields(self, sample_transcript_data):
        """Test that extra fields in segment data are ignored."""
        # Add extra fields to sample data
        sample_transcript_data['segments'][0]['extra_field'] = 'ignored'
        sample_transcript_data['segments'][0]['another_field'] = 123
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_transcript_data, f)
            test_file = f.name
        
        transcript = load_transcript(test_file)
        
        # Should load successfully despite extra fields
        assert len(transcript.segments) == 3
        assert transcript.segments[0].segment_id == "seg_001"
        
        Path(test_file).unlink()
    
    def test_load_preserves_timestamp_precision(self, sample_transcript_data):
        """Test that floating point timestamps are preserved."""
        # Set precise timestamps
        sample_transcript_data['segments'][0]['start'] = 1.23456789
        sample_transcript_data['segments'][0]['end'] = 5.67890123
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_transcript_data, f)
            test_file = f.name
        
        transcript = load_transcript(test_file)
        
        # Verify precision is preserved
        assert transcript.segments[0].start_time == 1.23456789
        assert transcript.segments[0].end_time == 5.67890123
        
        Path(test_file).unlink()
    
    def test_load_empty_segments_list(self):
        """Test loading a transcript with no segments."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"language": "en", "duration": 0.0, "segments": []}, f)
            test_file = f.name
        
        transcript = load_transcript(test_file)
        
        assert isinstance(transcript, Transcript)
        assert len(transcript.segments) == 0
        
        Path(test_file).unlink()
    
    def test_load_transcript_from_data_directory(self):
        """Test loading the default transcript from data directory."""
        transcript = load_transcript_from_data_directory()
        
        assert isinstance(transcript, Transcript)
        assert transcript.language == "en"
        assert len(transcript.segments) > 0
        assert isinstance(transcript.segments[0], Segment)
