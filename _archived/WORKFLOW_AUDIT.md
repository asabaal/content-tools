# Content Tools Workflow Audit Report

**Date**: February 12, 2026
**Auditor**: AI Analysis (GLM-5)

---

## Environment Status

| Dependency | Status | Notes |
|------------|--------|-------|
| Flask | ✅ Installed | v3.1.2 |
| pytest | ✅ Installed | v9.0.2 |
| pytest-cov | ✅ Installed | v0.0.0 |
| jsdom (npm) | ✅ Installed | For JS testing |
| Node.js | ✅ Available | v20.19.5 |
| Video data file | ✅ Exists | `data/video_combined.mp4` (400MB) |
| Transcript data | ✅ Exists | `data/transcript_combined.json` |

**Test Results**:
- Python tests: 167 passed, 1 failed (network server test)
- JavaScript tests: Passing

---

## User Workflows Identified

Based on codebase analysis, the following workflows are intended:

### WORKFLOW A: Transcript Review & Playback
View transcript with synchronized video playback, click segments to jump.

### WORKFLOW B: Inline Text Editing
Edit transcript text directly, with automatic word timing redistribution.

### WORKFLOW C: Segment Split/Merge
Split segments at word boundaries or merge adjacent segments.

### WORKFLOW D: Group Management
Create, rename, delete groups; assign segments to groups.

### WORKFLOW E: Duplicate Analysis & Selection
AI-powered duplicate detection with side-by-side video comparison.

### WORKFLOW F: Timeline Boundary Editing
Visual timeline with draggable segment boundaries and word timing.

### WORKFLOW G: Multi-Select Bulk Operations
Select multiple segments for bulk group assignment, merge, or delete.

### WORKFLOW H: Group Playback Queue
Play all segments in a group sequentially as a playlist.

### WORKFLOW I: Take Selection (Flask Backend)
Server-side take selection with state persistence.

---

## Workflow Status Matrix

| Workflow | Status | Blocking Issues | Effort |
|----------|--------|-----------------|--------|
| A: Review & Playback | ⚠️ PARTIAL | Hardcoded video path | Low |
| B: Inline Editing | ⚠️ PARTIAL | Minor function gaps | None |
| C: Split/Merge | ❌ BROKEN | Undefined functions | Medium |
| D: Group Management | ❌ BROKEN | Functions + path | Medium |
| E: Duplicate Analysis | ⚠️ PARTIAL | Path + 1 function | Low |
| F: Timeline Editing | ❌ BROKEN | Missing JS, CSS issues | High |
| G: Multi-Select Bulk | ⚠️ PARTIAL | Undefined functions | Medium |
| H: Group Playback | ❌ BROKEN | Entire system missing | High |
| I: Take Selection (Flask) | ✅ WORKING | Uses demo data | None |

---

## Detailed Findings by Tool

### HTML Tools (reference/)

#### Critical Issue: Hardcoded Video Path
**Files Affected**: 5 of 6 HTML tools
**Problem**: Video source points to `/home/asabaal/episode3_combined/combined_video.mp4`
**Solution**: Change to relative path `../../data/video_combined.mp4`

#### `reference/editors/inline_editing_complete.html`
- **Status**: PARTIAL
- **Working**: Edit mode toggle, contenteditable, save/download
- **Broken**: `openSegmentGroupMenu()`, `enableInlineEdit()`, `splitSegmentAtCursor()`, `toggleMergeMode()`, `playSegment()` undefined

#### `reference/editors/split_merge_final.html`
- **Status**: BROKEN
- **Issues**: `openSplitDialog()`, `playSegment()` undefined; `playbackModes`, `groupSelector`, `clipQueue` variables undefined; hardcoded path

#### `reference/editors/group_management_enhanced.html`
- **Status**: BROKEN
- **Issues**: `playSegment()`, `playGroupClips()`, `updatePlaylistDisplay()` undefined; `playbackModes`, `groupSelector` undefined; hardcoded path

#### `reference/tools/timeline_components/timeline_word_timing_editor_complete.html`
- **Status**: BROKEN
- **Issues**:
  - Missing external file `full_transcript_data.js`
  - `fullTranscriptData`, `transcriptSegments`, `timelineWords` undefined
  - CSS class mismatch: JS uses `.segment`, CSS defines `.timeline-segment`
  - CSS classes `.segment-handle`, `.word-marker` not defined
  - Duplicate `renderTimeRuler()` function definition
  - Hardcoded path

#### `reference/tools/video_grid/video_grid_individual.html`
- **Status**: BROKEN
- **Issues**: `playGroupClips()`, `updatePlaylistDisplay()` undefined; `playbackModes`, `groupSelector`, `clipQueue` undefined; hardcoded path

#### `reference/reports/duplicate_analysis_interactive.html`
- **Status**: PARTIAL
- **Working**: Duplicate groups display, similarity badges
- **Broken**: `showAddSegmentDialog()` undefined; hardcoded path

---

### Python Backend (implementation/)

#### `implementation/transcript_core/`
- **Status**: ✅ WORKING
- **Tests**: 125+ tests passing
- **Modules**: models, segments, timing, grouping, selection

#### `implementation/web_app/`
- **Status**: ✅ WORKING (with demo data)
- **Routes**: `/` (index), `/intent` (POST for actions)
- **Limitations**: Uses hardcoded demo data, in-memory state

---

## Common Issues

### 1. Hardcoded Absolute Paths
Found in: `split_merge_final.html`, `group_management_enhanced.html`, `timeline_word_timing_editor_complete.html`, `video_grid_individual.html`, `duplicate_analysis_interactive.html`

```html
<!-- Current (broken) -->
<source src="/home/asabaal/episode3_combined/combined_video.mp4" type="video/mp4">

<!-- Should be -->
<source src="../../data/video_combined.mp4" type="video/mp4">
```

### 2. Missing Playback Mode System
Several files reference variables that are never defined:
- `playbackModes` - radio button collection
- `groupSelector` - DOM element
- `clipQueue`, `currentClipIndex`, `isPlayingQueue` - queue state

This appears to be code copied from a template without dependencies.

### 3. Undefined Segment Control Functions
These functions are called but never defined:
- `openSegmentGroupMenu()` - Group assignment dialog
- `openSplitDialog()` / `splitSegmentAtCursor()` - Split functionality
- `toggleMergeMode()` - Merge mode toggle
- `playSegment()` - Video playback by segment

### 4. Timeline Editor Data Loading
The timeline editor expects `full_transcript_data.js` but this file needs to be generated from `data/transcript_combined.json`.

---

## Recommended Fix Priority

### Phase 1: Quick Wins (Low Effort)
1. Fix hardcoded video path in all 5 affected files
   - **Impact**: Restores video playback for workflows A, D, E, F

### Phase 2: Core Functionality (Medium Effort)
2. Define missing segment control functions
   - `openSegmentGroupMenu()`
   - `splitSegmentAtCursor()`
   - `toggleMergeMode()`
   - **Impact**: Restores workflows C, D, G

3. Fix timeline editor data loading
   - Generate `full_transcript_data.js` from JSON
   - Fix CSS class names
   - **Impact**: Restores workflow F

### Phase 3: Optional Enhancements (High Effort)
4. Implement playback queue system
   - Define `playbackModes`, `groupSelector`, `clipQueue`, etc.
   - Implement `playGroupClips()`, `playClipQueue()`, `updatePlaylistDisplay()`
   - **Impact**: Restores workflow H

5. Connect Flask to real data
   - Load `data/transcript_combined.json`
   - Add persistent storage
   - **Impact**: Makes workflow I useful with real data

---

## Testing Instructions

### Workflow I: Take Selection (Flask Backend)

This is the only fully functional workflow. To test:

```bash
cd /mnt/storage/repos/content-tools/implementation
python -m web_app.app
```

Then open http://127.0.0.1:5000/ in a browser.

**Expected behavior**:
1. Page loads showing segments and groups table
2. Click a segment row to select it (shows [SELECTED])
3. Click "Switch to this take" to change active take
4. Page reloads with updated selection state

**Known limitations**:
- Uses demo data (3 hardcoded segments), not your real transcript
- State is in-memory only (lost on server restart)
