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

---

# Flask Web App - Phase 2

## Purpose of the Flask Layer

Phase 2 adds a minimal Flask web application that:
- Imports and uses the transcript_core logic from Phase 1
- Loads example transcript data
- Renders results in a simple, readable HTML page
- Provides debug visibility into core logic output

This is a read-only UI designed for:
- Verifying that Phase 1 logic works end-to-end
- Debugging transcript data processing
- Providing a stable bridge between logic and UI

## How It Uses transcript_core

The web app imports all Phase 1 modules and uses them to:

1. Create sample transcript segments with words and timing
2. Build groups with multiple takes
3. Set active take selections
4. Format results for display

See `web_app/views.py` for the complete example of using transcript_core.

## How to Run the App

```bash
cd implementation
python -m web_app.app
```

The app will be available at: http://localhost:5000/

## How to Run Tests

```bash
cd implementation
python -m pytest tests/test_web_app.py -v
```

Run all tests including Phase 1:

```bash
python -m pytest tests/ -v
```

## What Phase 2 Explicitly Does NOT Support

- No editing capabilities
- No drag and drop
- No timeline canvas
- No video or audio playback
- No browser automation
- No AI features
- No JavaScript-driven logic
- No user input forms
- No API endpoints beyond `/`

This is intentional. Phase 2 is for debugging and verification only.

## Phase 2 Structure

- `web_app/app.py`: Flask application factory
- `web_app/routes.py`: Route definitions
- `web_app/views.py`: Logic that calls transcript_core
- `templates/index.html`: Simple HTML template for display
- `tests/test_web_app.py`: Server-side tests using Flask test client

---

# User Intent - Phase 3

## What Phase 3 Adds

Phase 3 adds minimal JavaScript to capture user intent without introducing:
- Layout logic
- Timeline logic
- Video playback
- Drag interactions
- Browser automation

User intent means: "The user clicked something, and the system recorded that intent correctly."

## User Intent Supported

Phase 3 supports exactly two user actions:

1. **Select a transcript segment**: Clicking a segment marks it as selected
   - Only one segment may be selected at a time
   - Selection is tracked in server state
   - Page reload shows updated selection

2. **Change active take**: If a segment has multiple takes, clicking a control switches the active take
   - Selection logic remains deterministic
   - Uses transcript_core for all decisions
   - State updates immediately

## How Intent Flows from Browser to Server

1. User clicks a segment or take switch control
2. JavaScript in `static/js/intent.js` captures the click
3. JavaScript emits an intent event via `fetch()` POST to `/intent`
4. Server receives intent with payload:
   ```json
   {
     "intent_type": "select_segment" | "switch_take",
     "segment_id": "s1",
     "take_id": "t2"
   }
   ```
5. Server updates state using `transcript_core` logic:
   - `views.handle_select_segment()` for segment selection
   - `views.handle_switch_take()` for take switching
6. State is re-rendered on next page load

## Key Principle: JavaScript is "Dumb"

The JavaScript layer:
- **Does not compute** logic
- **Does not decide** which take should be active
- **Does not synchronize** state
- **Just emits** events describing user intent

All logic lives in `transcript_core`. The server remains the source of truth.

## What Phase 3 Intentionally Does NOT Support

- No editing of text
- No timeline visuals
- No drag or resize interactions
- No video or audio playback
- No browser automation
- No client-side state machines
- No real-time updates (no websockets)
- No CSS beyond trivial readability

## How to Run Phase 3

The Flask app starts the same way as Phase 2:

```bash
cd implementation
python -m web_app.app
```

The app will be available at: http://127.0.0.1:5000/

Now you can:
1. Click on any segment row to select it
2. Click "Switch to this take" to change the active take
3. Reload the page to see selections persist

## How to Run Tests

Python tests (server-side):

```bash
cd implementation
python -m pytest tests/test_web_app.py -v
```

JavaScript tests (intent logic):

```bash
cd implementation
npm run test:js
# or directly:
node tests/test_intent.js
```

Run all tests:

```bash
python -m pytest tests/ -v
```

## Phase 3 Structure (Additions)

- `static/js/intent.js`: Minimal JavaScript for intent capture
  - `sendIntent()`: Emits intent events via fetch()
  - `selectSegment()`: Captures segment selection
  - `switchTake()`: Captures take switching
  - Event listeners attached on DOMContentLoaded
- `tests/test_intent.js`: DOM-level tests for intent logic
  - Tests payload structure
  - Tests intent type emission
  - Stubs `fetch()` - no real browser
- `package.json`: NPM configuration for JS testing
- `templates/index.html`: Updated with:
  - `data-segment-id` attributes on segment rows
  - `data-take-switch` attributes on switch controls
  - Selection column showing [SELECTED] status
  - Simple switch controls for inactive takes
  - JavaScript include
- `web_app/routes.py`: Added `/intent` POST route
- `web_app/views.py`: Added state management and intent handlers
- `tests/test_web_app.py`: Extended with:
  - Tests for `/intent` route
  - Tests for state persistence
  - Tests for Phase 3 UI elements
