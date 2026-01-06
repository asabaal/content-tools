# Take Selector v2 - Backend

Python backend for transcript data loading and segment management.

## Structure

```
backend/
└── take_selector/
    ├── __init__.py
    ├── data_loader.py
    └── tests/
        ├── __init__.py
        ├── pytest.ini
        └── test_data_loader.py
```

## Usage

```python
from take_selector import load_transcript, Segment, Transcript

# Load transcript from file
transcript = load_transcript('../../data/transcript_episode3.json')

# Access segments
for segment in transcript.segments:
    print(f"{segment.segment_id}: {segment.text} ({segment.start_time:.2f}s - {segment.end_time:.2f}s)")
    print(f"  Duration: {segment.duration:.2f}s")
```

## Running Tests

From the `backend/` directory:

```bash
cd take_selector
python -m pytest tests/ -v
```

Or with verbose output:

```bash
python -m pytest tests/ -v --tb=long
```

## Data Models

### Segment

Represents a single transcript segment.

Attributes:
- `segment_id` (str): Unique identifier
- `start_time` (float): Start time in seconds
- `end_time` (float): End time in seconds
- `text` (str): Transcript text content

Properties:
- `duration` (float): Calculated duration (end_time - start_time)

### Transcript

Represents a complete transcript with metadata.

Attributes:
- `language` (str): Language code (e.g., 'en')
- `duration` (float): Total duration in seconds
- `segments` (List[Segment]): List of Segment objects

## Dependencies

- Python 3.8+
- Standard library only (no external dependencies)
- pytest for testing
