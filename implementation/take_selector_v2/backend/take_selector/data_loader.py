"""
Data loader for transcript files.

Loads transcript data from JSON files and converts to structured Segment objects.
"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Segment:
    """
    Represents a single transcript segment.
    
    Attributes:
        segment_id: Unique identifier for the segment
        start_time: Start time in seconds
        end_time: End time in seconds
        text: Transcript text content
    """
    segment_id: str
    start_time: float
    end_time: float
    text: str
    
    @property
    def duration(self) -> float:
        """Calculate segment duration in seconds."""
        return self.end_time - self.start_time


@dataclass
class Transcript:
    """
    Represents a complete transcript with metadata and segments.
    
    Attributes:
        language: Language code (e.g., 'en')
        duration: Total duration in seconds
        segments: List of Segment objects
    """
    language: str
    duration: float
    segments: List[Segment]


def load_transcript(file_path: str) -> Transcript:
    """
    Load transcript from a JSON file.
    
    Args:
        file_path: Path to the JSON transcript file
        
    Returns:
        Transcript object with parsed segments
        
    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
        ValueError: If required fields are missing
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Transcript file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validate required top-level fields
    if 'segments' not in data:
        raise ValueError("Transcript file missing 'segments' field")
    
    language = data.get('language', 'en')
    duration = data.get('duration', 0.0)
    
    # Parse segments
    segments = []
    for item in data['segments']:
        # Validate required segment fields
        if not all(field in item for field in ['text', 'start', 'end', 'segment_id']):
            raise ValueError(f"Segment missing required fields: {item}")
        
        segment = Segment(
            segment_id=item['segment_id'],
            start_time=float(item['start']),
            end_time=float(item['end']),
            text=item['text']
        )
        segments.append(segment)
    
    return Transcript(
        language=language,
        duration=duration,
        segments=segments
    )


def load_transcript_from_data_directory() -> Transcript:
    """
    Load default transcript from the data directory.
    
    Looks for transcript_episode3.json in the data directory.
    
    Returns:
        Transcript object with parsed segments
    """
    data_dir = Path(__file__).parent.parent.parent.parent.parent / 'data'
    transcript_file = data_dir / 'transcript_episode3.json'
    
    return load_transcript(str(transcript_file))
