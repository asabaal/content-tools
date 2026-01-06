# Integrated Component Architecture Development Plan

## CRITICAL CONSTRAINT: DO NOT TOUCH EXISTING COMPONENTS
- **Existing directory:** `/home/asabaal/episode3_combined/timeline_timing_editor/`
- **All 6 component HTML files remain untouched**
- **New directory:** `/home/asabaal/episode3_combined/integrated_components/`
- **New components will be built alongside, not replacing existing ones**

## ARCHITECTURE DOCUMENTATION

### 1. Shared Data Layer Architecture

#### File: core/DataManager.js
```javascript
class DataManager {
    constructor() {
        this.segments = []; // Loads from combined_transcript.json
        this.metadata = {};
        this.eventListeners = new Map();
    }
    
    // Standardized data interface
    getSegment(id) { /* ... */ }
    updateSegment(id, changes) { /* ... */ }
    redistributeWords(segmentId) { /* ... */ }
    on(event, callback) { /* ... */ }
    emit(event, data) { /* ... */ }
}
```

### 2. Component Interface Specification

#### File: core/Component.js
```javascript
class Component {
    constructor(dataManager, config = {}) {
        this.data = dataManager;
        this.config = config;
        this.element = null;
        this.isInitialized = false;
    }
    
    // Required methods for all components
    initialize(container) { /* ... */ }
    render() { /* ... */ }
    destroy() { /* ... */ }
    onDataChanged(event, data) { /* ... */ }
}
```

### 3. Event-Driven Communication Protocol

#### File: core/Events.js
```javascript
// Standardized events all components must handle
const EVENTS = {
    SEGMENT_UPDATED: 'segmentUpdated',
    SEGMENT_SELECTED: 'segmentSelected',
    WORD_TIMING_CHANGED: 'wordTimingChanged',
    TIMELINE_ZOOM_CHANGED: 'timelineZoomChanged',
    PLAYBACK_POSITION_CHANGED: 'playbackPositionChanged'
};
```

## COMPONENT DEVELOPMENT SPECIFICATIONS

### New Component 1: TimelineViewer
- **Location:** `TimelineViewer/TimelineViewer.js`
- **Dependencies:** DataManager only
- **Integration Points:** Emits SEGMENT_SELECTED, responds to SEGMENT_UPDATED
- **Testing:** Must load real combined_transcript.json data
- **Verification:** Timeline renders 220+ segments correctly

### New Component 2: InteractiveBoundaries  
- **Location:** `InteractiveBoundaries/InteractiveBoundaries.js`
- **Dependencies:** DataManager, TimelineViewer
- **Integration Points:** Listens to SEGMENT_SELECTED, emits WORD_TIMING_CHANGED
- **Testing:** Must work with TimelineViewer component simultaneously
- **Verification:** Dragging boundaries updates data in real-time

### New Component 3: WordRedistribution
- **Location:** `WordRedistribution/WordRedistribution.js`
- **Dependencies:** DataManager
- **Integration Points:** Responds to WORD_TIMING_CHANGED, emits SEGMENT_UPDATED
- **Testing:** Must integrate with InteractiveBoundaries component
- **Verification:** Word timing redistributes when boundaries change

### New Component 4: AudioPreview
- **Location:** `AudioPreview/AudioPreview.js`
- **Dependencies:** DataManager
- **Integration Points:** Responds to SEGMENT_SELECTED, emits PLAYBACK_POSITION_CHANGED
- **Testing:** Must work with TimelineViewer + actual episode 3 audio files
- **Verification:** Audio syncs with timeline selection

### New Component 5: DataManagement
- **Location:** `DataManagement/DataManagement.js`
- **Dependencies:** DataManager
- **Integration Points:** Can import/export, emits SEGMENT_UPDATED on data changes
- **Testing:** Must work with all other components active
- **Verification:** Data changes reflect across all components

### New Component 6: TranscriptEditor
- **Location:** `TranscriptEditor/TranscriptEditor.js`
- **Dependencies:** DataManager, WordRedistribution
- **Integration Points:** Emits SEGMENT_UPDATED, responds to SEGMENT_SELECTED
- **Testing:** Must integrate with all components simultaneously
- **Verification:** Text changes trigger word redistribution across system

## INTEGRATION TESTING PROTOCOL

### Component Isolation Testing
Each component must pass these tests:
```javascript
describe('TimelineViewer', () => {
    test('loads real combined_transcript.json data');
    test('renders without other components');
    test('emits correct events');
    test('responds to DataManager events');
});
```

### Component Integration Testing
Test combinations:
- TimelineViewer + InteractiveBoundaries
- TimelineViewer + InteractiveBoundaries + WordRedistribution
- Continue adding until all 6 components work together

## FILE STRUCTURE
```
integrated_components/
├── core/
│   ├── DataManager.js
│   ├── Component.js
│   └── Events.js
├── TimelineViewer/
│   ├── TimelineViewer.js
│   ├── TimelineViewer.css
│   └── TimelineViewer.test.html
├── InteractiveBoundaries/
│   ├── InteractiveBoundaries.js
│   ├── InteractiveBoundaries.css
│   └── InteractiveBoundaries.test.html
├── WordRedistribution/
│   ├── WordRedistribution.js
│   ├── WordRedistribution.css
│   └── WordRedistribution.test.html
├── AudioPreview/
│   ├── AudioPreview.js
│   ├── AudioPreview.css
│   └── AudioPreview.test.html
├── DataManagement/
│   ├── DataManagement.js
│   ├── DataManagement.css
│   └── DataManagement.test.html
├── TranscriptEditor/
│   ├── TranscriptEditor.js
│   ├── TranscriptEditor.css
│   └── TranscriptEditor.test.html
└── integration_tests/
    ├── component1+2.html
    ├── component1+2+3.html
    └── all_components.html
```

## SUCCESS CRITERIA
1. **No existing components are modified**
2. **Each new component works standalone**
3. **Each new component integrates with previous components**
4. **Real episode 3 data works throughout**
5. **Final integration test passes with all 6 components**

## DEVELOPMENT PHASES

### Phase 1: Core Architecture
- Create core directory and base classes
- Implement DataManager with real data loading
- Set up event system
- Test data layer with combined_transcript.json

### Phase 2: Component Development (Sequential)
1. Build TimelineViewer component
2. Build InteractiveBoundaries component (integrates with #1)
3. Build WordRedistribution component (integrates with #1,#2)
4. Build AudioPreview component (integrates with #1)
5. Build DataManagement component (integrates with all)
6. Build TranscriptEditor component (integrates with all)

### Phase 3: Integration Testing
- Test each component standalone
- Test incremental integration
- Test full system integration
- Verify with real episode 3 data

### Phase 4: Final Integration
- Combine all components into complete tool
- Performance testing with 220+ segments
- Documentation and cleanup

## DATA INTEGRATION NOTES

### Real Data Source
- **File:** `../combined_transcript.json`
- **Structure:** 220+ segments with word-level timing
- **Duration:** 220.45 seconds
- **Format:** Standardized segment/word structure

### Audio/Video Files
- **Location:** `../audio/` directory
- **Files:** segment1.m4a, segment2.m4a, etc.
- **Integration:** AudioPreview component must access these files

## TESTING REQUIREMENTS

### Each Component Must:
1. Load and display real episode 3 data
2. Work independently without other components
3. Integrate properly with previously built components
4. Handle event-driven communication correctly
5. Maintain data consistency across the system

### Integration Tests Must:
1. Verify data flow between components
2. Test event propagation
3. Ensure UI consistency
4. Validate performance with full dataset
5. Test error handling and recovery