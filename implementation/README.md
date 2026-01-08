# Transcript Core - Phase 1

## What Phase 1 Does

This is a pure Python transcript logic core that handles:

- **Transcript segments**: Represent chunks of transcript with text and timing
- **Word timing redistribution**: Automatically realign word timings when text changes
- **Grouping**: Organize segments and takes into groups
- **Take selection**: Deterministic rules for selecting which take plays
- **Alignment logic**: Proportional redistribution of timing based on character counts

## What Phase 1 Does NOT Do

- No HTML rendering
- No JavaScript execution
- No browser automation
- No video or audio playback
- No UI rendering or interaction
- No network or API calls

## How to Run Tests

```bash
cd implementation
python -m pytest tests/ -v
```

Run with coverage:

```bash
python -m pytest tests/ --cov=transcript_core --cov-report=html
```

## How Later Phases Will Consume This Core

Later phases can import and use the core logic:

```python
from transcript_core import (
    SegmentManager,
    TimingManager,
    GroupManager,
    SelectionManager,
    Segment, Word, Take, Group
)

# Create and manage transcript segments
manager = SegmentManager()
segment = Segment(id="s1", text="Hello world", start_time=0.0, end_time=1.0)
manager.add_segment(segment)

# Redistribute timing when text changes
new_words = TimingManager.redistribute_word_timings(segment, "Goodbye world")

# Group takes for selection
group_manager = GroupManager()
group = group_manager.create_group("g1")
take1 = Take(id="t1", segment=segment, is_active=True)
group_manager.add_take_to_group("g1", take1)

# Switch between takes
selection = SelectionManager(group_manager.get_all_groups())
selection.select_take("t2", "g1")
```

The core provides all deterministic logic for:
- Which take should be active
- When each word should start and end
- How groups should maintain integrity
- How timing should adjust to edits

Phase 2 will build a Flask server that calls this core and displays results.
Phase 3 will add minimal JavaScript to express user intent events.
Phase 4 will add UI for exactly one interaction surface.

## Module Overview

- `models.py`: Core data structures (Segment, Word, Take, Group, Transcript)
- `segments.py`: Segment CRUD operations and queries
- `timing.py`: Word timing redistribution and adjustment
- `grouping.py`: Group management and take operations
- `selection.py`: Take selection logic and state management
