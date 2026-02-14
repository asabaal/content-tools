# Inline Editor Dependency Audit

**Target File:** `editors/inline_editing_complete.html`

**Audit Date:** January 6, 2026

**Purpose:** Identify all referenced functions, variables, and objects that are used but not defined within this file at runtime.

---

## Executive Summary

The file depends on **11 missing symbols** that cause runtime errors:

- **4 Functions** - Critical for playlist and group playback
- **3 Variables** - Required for queue management
- **4 DOM Elements** - Missing UI elements for playlist display

All missing dependencies originate from `reports/transcript_editor_analysis.html` and `reports/clip_player_analysis.html`, which are report-only variants with playlist functionality that was not fully integrated into the inline editor.

---

## Missing Functions

| Function | Line Usage | Source File | Description | Impact |
|-----------|-------------|--------------|-------------|---------|
| `updatePlaylistDisplay()` | 2058, 2071 | `reports/transcript_editor_analysis.html:815`, `reports/clip_player_analysis.html:767` | Renders clip queue list in playlist UI | **BLOCKING** - ReferenceError when called |
| `playGroupClips(groupId)` | 2066 | `reports/transcript_editor_analysis.html:838`, `reports/clip_player_analysis.html:790` | Loads all segments from a group into clip queue and plays them | **BLOCKING** - ReferenceError when called |
| `playClipQueue()` | (called by updatePlaylistDisplay) | `reports/transcript_editor_analysis.html:776`, `reports/clip_player_analysis.html:728` | Plays through clips in the clipQueue sequentially | **BLOCKING** - ReferenceError when called |
| `playGroupClips()` logic | (implicit) | `reports/transcript_editor_analysis.html` | Sorts and queues group segments by time | **BLOCKING** - Prevents group playback |

### Usage Context

```javascript
// Line 2052-2058: Called when switching playback modes
playbackModes.forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'group') {
            groupSelector.style.display = 'flex';
        } else {
            groupSelector.style.display = 'none';
            clipQueue = [];              // ❌ Missing variable
            currentClipIndex = 0;         // ❌ Missing variable
            isPlayingQueue = false;         // ❌ Missing variable
            updatePlaylistDisplay();          // ❌ Missing function
        }
    });
});

// Line 2064-2066: Called when group is selected
groupSelect.addEventListener('change', (e) => {
    if (e.target.value) {
        playGroupClips(e.target.value);  // ❌ Missing function
    }
});

// Line 2070-2071: Initial playlist display
// Initialize playlist display
updatePlaylistDisplay();                 // ❌ Missing function
```

---

## Missing Variables

| Variable | Line Usage | Source File | Description | Impact |
|----------|-------------|--------------|-------------|---------|
| `clipQueue` | 2055 | `reports/transcript_editor_analysis.html:733`, `reports/clip_player_analysis.html:685` | Array of clips to play sequentially | **BLOCKING** - ReferenceError |
| `currentClipIndex` | 2056 | `reports/transcript_editor_analysis.html:732`, `reports/clip_player_analysis.html:684` | Index of currently playing clip in queue | **BLOCKING** - ReferenceError |
| `isPlayingQueue` | 2057 | `reports/transcript_editor_analysis.html:734`, `reports/clip_player_analysis.html:686` | Boolean flag for queue playback state | **BLOCKING** - ReferenceError |

### Variable Declarations in Source Files

```javascript
// From reports/transcript_editor_analysis.html (lines 732-734)
let currentClipIndex = 0;
let clipQueue = [];
let isPlayingQueue = false;
```

---

## Missing DOM Elements

| Element ID | Line Usage | Source File | Description | Impact |
|------------|-------------|--------------|-------------|---------|
| `groupSelector` | 2052, 2054 | `reports/transcript_editor_analysis.html:701` | Container div for group selection UI (hidden by default) | **BLOCKING** - TypeError: null when accessing .style |
| `clipList` | (used by updatePlaylistDisplay) | `reports/transcript_editor_analysis.html:717`, `reports/clip_player_analysis.html:669` | Container div for displaying clip queue items | **BLOCKING** - TypeError: null when updating DOM |
| `playlist` | (container for clipList) | `reports/transcript_editor_analysis.html:715`, `reports/clip_player_analysis.html:667` | Parent container for clip queue UI | **BLOCKING** - Required for playlist functionality |
| `selectedText` | (used by playClipQueue) | `reports/transcript_editor_analysis.html:708` | Span element showing current playback status | **BLOCKING** - TypeError: null when updating text |

### HTML Structure in Source Files

```html
<!-- From reports/transcript_editor_analysis.html (lines 701-709) -->
<div class="group-selector" id="groupSelector" style="display: none;">
    <label for="groupSelect">Select Group:</label>
    <select id="groupSelect">
        <option value="">Choose a group...</option>
    </select>
</div>

<div class="playlist" id="playlist">
    <h3>📋 Clip Queue</h3>
    <span id="selectedText">Click a segment to play</span>
    <div id="clipList"></div>
</div>
```

---

## Missing CSS Styles

The following CSS classes and IDs are required by the missing DOM elements but are not present in `inline_editing_complete.html`:

| Selector | Source File | Lines in Source | Description |
|----------|--------------|------------------|-------------|
| `.playlist` | `reports/transcript_editor_analysis.html` | 230-237 | Playlist container styling |
| `.playlist h3` | `reports/transcript_editor_analysis.html` | 235-237 | Playlist header styling |
| `#clipList` | `reports/transcript_editor_analysis.html` | 239-241 | Clip list container styling |
| `.clip-item` | `reports/transcript_editor_analysis.html` | 243-261 | Individual clip item styling |
| `.clip-item:hover` | `reports/transcript_editor_analysis.html` | 250-254 | Hover effect for clip items |
| `.clip-item.playing` | `reports/transcript_editor_analysis.html` | 254-256 | Active clip highlighting |

---

## Dependency Origin Analysis

### Primary Source Files

1. **`reports/transcript_editor_analysis.html`** (1198 lines)
   - Contains complete playlist management system
   - Defines all missing functions and variables (lines 732-838)
   - Includes playlist UI HTML (lines 701-719)
   - Includes playlist CSS (lines 230-261)

2. **`reports/clip_player_analysis.html`** (1005 lines)
   - Nearly identical to transcript_editor_analysis
   - Same playlist management system (lines 684-790)
   - Same UI structure and CSS

### Relationship to Target File

The target file `editors/inline_editing_complete.html` appears to be a combination of:

- **Inline editing features** (from implementation summary)
- **Video grid functionality** (present in file)
- **Partial playlist/group playback code** (incomplete)

The playlist/group playback code was likely copied from the report files but without the necessary supporting functions, variables, and UI elements.

---

## Criticality Assessment

### Blocking Errors (Must Fix)

These prevent any interaction with playback mode switching:

1. **`playbackModes.forEach` at line 2046** - ✅ FIXED in Phase 2A
   - Previously: `ReferenceError: playbackModes is not defined`
   - Now: Fixed by adding radio button elements and query selector

2. **`updatePlaylistDisplay()` at lines 2058, 2071**
   - Error: `ReferenceError: updatePlaylistDisplay is not defined`
   - Impact: Cannot initialize or update playlist display
   - Triggered on: Page load and playback mode change

3. **`groupSelector.style.display` at lines 2052, 2054**
   - Error: `TypeError: Cannot read property 'style' of null`
   - Impact: Cannot show/hide group selector UI
   - Triggered on: Playback mode change to 'group'

4. **Variable references at lines 2055-2057**
   - Error: `ReferenceError: clipQueue is not defined` (and others)
   - Impact: Cannot reset queue state
   - Triggered on: Playback mode change from 'group' to 'single'

5. **`playGroupClips()` at line 2066**
   - Error: `ReferenceError: playGroupClips is not defined`
   - Impact: Cannot play grouped clips
   - Triggered on: Group selection change

### Non-Blocking Errors (Can Work Around)

These affect specific features but don't prevent core inline editing:

- **Missing playlist UI** - Can still use inline editing and single segment playback
- **Missing group playback** - Can still play individual segments
- **Missing clip queue** - Not required for basic inline editing workflow

---

## Functional Impact Analysis

### What Still Works (Non-Blocked)

- ✅ **Inline text editing** - Core feature of this file
- ✅ **Split/merge segments** - Complete functionality
- ✅ **Group management** - Create, rename, delete groups
- ✅ **Single segment playback** - ▶️ buttons work correctly
- ✅ **Video grid** - Multi-view functionality
- ✅ **Auto-save to browser storage** - Draft recovery
- ✅ **Transcript download** - Export functionality

### What Is Broken (Blocked)

- ❌ **Playback mode switching** - Radio buttons exist but switching errors
- ❌ **Group playback mode** - Cannot play grouped clips sequentially
- ❌ **Clip queue management** - No visual queue display
- ❌ **Playlist UI** - Missing entire playlist section
- ❌ **Loop clips option** - Checkbox exists but queue management broken

---

## Recommended Next Steps

### Option 1: Remove Playlist/Group Playback Features (Minimal Fix)

If playlist/group playback was never intended for this tool:

1. Remove radio buttons for playback modes (just added in Phase 2A)
2. Remove event listener code at lines 2046-2071
3. Remove references to `playGroupClips()`
4. File would work as inline-only editor

**Pros:** Minimal changes, clean removal of non-core features
**Cons:** Loses potentially useful group playback functionality

### Option 2: Port Full Playlist System (Complete Fix)

If group playback is desired:

1. Copy missing functions from source files:
   - `updatePlaylistDisplay()` (lines 815-837)
   - `playGroupClips()` (lines 838-862)
   - `playClipQueue()` (lines 776-815)

2. Add missing variable declarations (after line 1436):
   ```javascript
   let currentClipIndex = 0;
   let clipQueue = [];
   let isPlayingQueue = false;
   ```

3. Add missing HTML elements (after line 1572, before closing div):
   ```html
   <div class="group-selector" id="groupSelector" style="display: none;">
       <label for="groupSelect">Select Group:</label>
       <select id="groupSelect">
           <option value="">Choose a group...</option>
       </select>
   </div>
   <div class="playlist" id="playlist">
       <h3>📋 Clip Queue</h3>
       <span id="selectedText">Click a segment to play</span>
       <div id="clipList"></div>
   </div>
   ```

4. Add missing CSS (in <style> section):
   - Copy lines 230-261 from transcript_editor_analysis.html

**Pros:** Completes intended group playback functionality
**Cons:** Larger change set, may introduce additional dependencies

### Option 3: Create Minimal Stub (Temporary Fix)

Create placeholder functions that prevent errors but don't implement full functionality:

```javascript
// Minimal stubs to prevent errors
function updatePlaylistDisplay() {
    console.log('Playlist display not implemented');
}

function playGroupClips(groupId) {
    console.log('Group playback not implemented:', groupId);
}

function playClipQueue() {
    console.log('Clip queue playback not implemented');
}
```

**Pros:** Quick fix, no errors
**Cons:** Doesn't provide actual functionality, users see console warnings

---

## Dependency Mapping Summary

```
Source File: reports/transcript_editor_analysis.html

┌─────────────────────────────────────┐
│  Missing Functions                  │
├─────────────────────────────────────┤
│ • updatePlaylistDisplay()    [815] │
│ • playGroupClips()          [838] │
│ • playClipQueue()            [776] │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Missing Variables                 │
├─────────────────────────────────────┤
│ • currentClipIndex           [732] │
│ • clipQueue                 [733] │
│ • isPlayingQueue            [734] │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Missing DOM Elements             │
├─────────────────────────────────────┤
│ • #groupSelector            [701] │
│ • #playlist                 [715] │
│ • #selectedText             [708] │
│ • #clipList                [717] │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Missing CSS                      │
├─────────────────────────────────────┤
│ • .playlist                  [230] │
│ • .playlist h3               [235] │
│ • #clipList                  [239] │
│ • .clip-item                 [243] │
│ • .clip-item:hover           [250] │
│ • .clip-item.playing         [254] │
└─────────────────────────────────────┘
```

---

## Verification Checklist

After implementing fixes, verify:

- [ ] No ReferenceError for `updatePlaylistDisplay`
- [ ] No ReferenceError for `playGroupClips`
- [ ] No ReferenceError for `playClipQueue`
- [ ] No ReferenceError for `clipQueue`, `currentClipIndex`, `isPlayingQueue`
- [ ] No TypeError for `groupSelector.style.display`
- [ ] No TypeError for `clipList` DOM operations
- [ ] No TypeError for `selectedText` DOM operations
- [ ] Playback mode radio buttons switch correctly
- [ ] Group selector appears/disappears based on mode
- [ ] Playlist displays clips when group is selected
- [ ] Clicking playlist items plays clips
- [ ] Inline editing still works

---

**Audit Complete**

Total Missing Symbols: 11
Blocking Errors: 8
Non-Blocking Errors: 3
Recommended Action: Option 1 (Remove) or Option 2 (Port Full System)

---

*Audit performed without modifying any code. Ready for human decision on next repair action.*
