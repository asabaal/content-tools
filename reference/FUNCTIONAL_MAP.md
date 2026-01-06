# Functional Map - Content Editing Tools

This document provides an inventory of all tools in the repository to help you decide which file to open for a specific task.

---

## Table of Contents

- [Reports](#reports)
- [Editors](#editors)
- [Tools](#tools)
  - [Timeline Components](#timeline-components)
  - [Timeline Integrated](#timeline-integrated)
  - [Take Selection Tool](#take-selection-tool)
  - [Video Grid](#video-grid)
  - [Clip Player](#clip-player)
- [Data](#data)
- [Experiments](#experiments)

---

## Reports

### Duplicate Analysis Tools

| File | Description | Level | Type | Notes |
|------|-------------|-------|------|-------|
| `reports/duplicate_analysis_simple.html` | Basic duplicate detection report with video player | transcript | report-only | Simple layout, shows duplicate groups |
| `reports/duplicate_analysis_improved.html` | Enhanced duplicate detection report | transcript | report-only | Improved styling and layout |
| `reports/duplicate_analysis_noai.html` | Duplicate analysis without AI processing | transcript | report-only | Uses simple_text_similarity |
| `reports/duplicate_analysis_ai.html` | AI-powered duplicate detection report | transcript | report-only | Uses llama3.1:8b model |
| `reports/duplicate_analysis_basic.html` | Basic variant of duplicate analysis | transcript | report-only | Similar to simple_report |
| `reports/duplicate_analysis_interactive.html` | Interactive duplicate analysis with editing | transcript | editor-capable | Allows inline transcript editing |
| `reports/duplicate_analysis_updated.html` | Updated version of duplicate report | transcript | report-only | Improved version |
| `reports/transcript_duplicates.html` | Shows duplicates in transcript format | transcript | report-only | Alternative format for duplicates |

### Other Analysis Reports

| File | Description | Level | Type | Notes |
|------|-------------|-------|------|-------|
| `reports/clip_player_analysis.html` | Report with clip player functionality | video/clip | report-only | Includes video playback for clips |
| `reports/paragraph_edit_analysis.html` | Report focused on paragraph editing | paragraph | report-only | Shows paragraph-level analysis |
| `reports/paragraph_edit_final.html` | Final paragraph editing report | paragraph | report-only | Complete paragraph editing analysis |
| `reports/transcript_editor_analysis.html` | Analysis of transcript editor features | transcript | report-only | Documents editor capabilities |

---

## Editors

### Inline Editing Tools

| File | Description | Level | Type | Notes |
|------|-------------|-------|------|-------|
| `editors/inline_editing_complete.html` | Complete inline editing with all features | word | editor-capable | **Most complete inline editor** |
| `editors/inline_editing_updated.html` | Updated version of inline editor | word | editor-capable | Improved from complete version |
| `editors/transcript_fixed.html` | Fixed transcript editor | transcript | editor-capable | Has video player with transcript |
| `editors/transcript_with_video.html` | Transcript editor with video integration | transcript | editor-capable | Video + transcript editing |

### Split/Merge Tools

| File | Description | Level | Type | Notes |
|------|-------------|-------|------|-------|
| `editors/split_merge_fixed.html` | Split and merge functionality - fixed | word | editor-capable | Fixed version of split/merge |
| `editors/split_merge_functionality.html` | Split and merge functionality | word | editor-capable | Core split/merge features |
| `editors/split_merge_corrected.html` | Corrected split and merge | word | editor-capable | Bug fixes applied |
| `editors/split_merge_final.html` | Final version of split/merge | word | editor-capable | Production-ready version |
| `editors/split_merge_controls_fixed.html` | Split/merge with fixed controls | word | editor-capable | UI controls improved |
| `editors/split_merge_improved.html` | Improved split and merge | word | editor-capable | Enhanced functionality |
| `editors/split_merge_working.html` | Working split and merge implementation | word | editor-capable | Tested working version |

### Group Management

| File | Description | Level | Type | Notes |
|------|-------------|-------|------|-------|
| `editors/group_management_enhanced.html` | Enhanced group management | transcript | editor-capable | Full CRUD for groups |
| `editors/group_management_multiselect.html` | Multi-select group management | transcript | editor-capable | Bulk operations on groups |

### Other Editors

| File | Description | Level | Type | Notes |
|------|-------------|-------|------|-------|
| `editors/controls_shortcut_fixed.html` | Fixed keyboard shortcuts | transcript | editor-capable | Improved keyboard controls |

---

## Tools

### Timeline Components

**Location:** `tools/timeline_components/`

**Purpose:** Visual timeline editing for word-level timing adjustments

| File | Description | Level | Type | Notes |
|------|-------------|-------|------|-------|
| `component1_basic_timeline.html` | Basic timeline viewer | timeline | experimental | Shows segments on timeline |
| `component2_interactive_boundaries.html` | Interactive segment boundaries | timeline | experimental | Draggable boundaries |
| `component3_word_redistribution.html` | Word timing redistribution | word | experimental | Adjusts word timing |
| `component4_audio_preview_v1.html` | Audio preview v1 | timeline | experimental | Audio sync with timeline |
| `component4_audio_preview_v2.html` | Audio preview v2 | timeline | experimental | Improved audio preview |
| `component4_audio_preview_v2.5.html` | Audio preview v2.5 | timeline | experimental | Further improvements |
| `component4_audio_preview_v3.html` | Audio preview v3 | timeline | experimental | Latest audio preview |
| `component5_data_management.html` | Data management | transcript | experimental | Import/export timing data |
| `component6_transcript_editor.html` | Transcript editor integration | transcript | experimental | Full transcript editing |
| `timeline_word_timing_editor_complete.html` | Complete timeline editor | timeline | usable | **Main timeline editor** |
| `debug_loading.html` | Debug loading | timeline | experimental | Testing data loading |
| `test_loading.html` | Test loading | timeline | experimental | Loading tests |
| `test_syntax.html` | Test syntax | timeline | experimental | Syntax validation |
| `development_plan.md` | Development plan | - | - | Documentation |
| `DEVELOPMENT_PLAN.md` | Original development plan | - | - | Documentation |

### Timeline Integrated

**Location:** `tools/timeline_integrated/`

**Purpose:** Component-based architecture for integrated timeline editing

| File | Description | Level | Type | Notes |
|------|-------------|-------|------|-------|
| `comprehensive_test.html` | Comprehensive integration test | timeline | experimental | Tests all components |
| `data_test.html` | Data layer test | timeline | experimental | Tests DataManager |
| `debug_fixed.html` | Fixed debug version | timeline | experimental | Debug tool |
| `debug.html` | Debug tool | timeline | experimental | General debugging |
| `import_test.html` | Import test | timeline | experimental | Tests data import |
| `minimal_test.html` | Minimal test | timeline | experimental | Basic component test |
| `simple_test.html` | Simple test | timeline | experimental | Simple integration test |
| `test_browser.html` | Browser compatibility test | timeline | experimental | Cross-browser testing |
| `validate_modules.html` | Module validation | timeline | experimental | Validates components |
| `start_server.sh` | Local server script | - | - | Starts development server |
| `DEVELOPMENT_PLAN.md` | Development plan | - | - | Architecture documentation |

**Subdirectories:**

| Path | Description | Type |
|------|-------------|------|
| `core/` | Shared data layer and component base classes | experimental |
| `integration_tests/` | Integration test files | experimental |
| `InteractiveBoundaries/` | Interactive boundary component | experimental |
| `TimelineViewer/` | Timeline viewer component | experimental |
| `WordRedistribution/` | Word redistribution component | experimental |

### Take Selection Tool

**Location:** `tools/take_selection/`

**Purpose:** Incremental build of take selection and editing tool

| File | Description | Level | Type | Notes |
|------|-------------|-------|------|-------|
| `v1_basic.html` | Basic structure | transcript | experimental | HTML structure only |
| `v2_playback.html` | Video playback | transcript | experimental | Adds video playback |
| `v3_edit.html` | Text editing | transcript | experimental | Adds inline editing |
| `v4_groups.html` | Group assignment | transcript | experimental | Adds group management |
| `v5_merge.html` | Merge/split | transcript | experimental | Adds merge/split |
| `v6_multiselect.html` | Multi-select | transcript | experimental | Multi-select mode |
| `v6_complete_transcript.html` | Complete transcript v6 | transcript | experimental | Full transcript |
| `v6_dynamic_groups.html` | Dynamic groups v6 | transcript | experimental | Dynamic group creation |
| `v7_fixed_groups.html` | Fixed groups v7 | transcript | experimental | Group fixes |
| `v8_video_grid.html` | Video grid v8 | video/clip | experimental | Adds video grid |
| `development_plan.md` | Development plan | - | - | Build documentation |
| `build_plan.md` | Original build plan | - | - | Build steps |

### Video Grid

**Location:** `tools/video_grid/`

**Purpose:** Grid-based video player for multiple clip viewing

| File | Description | Level | Type | Notes |
|------|-------------|-------|------|-------|
| `video_grid_basic.html` | Basic video grid | video/clip | usable | Shows multiple videos in grid |
| `video_grid_fixed.html` | Fixed video grid | video/clip | usable | Bug fixes applied |
| `video_grid_with_ai.html` | Video grid with AI integration | video/clip | usable | Includes AI features |
| `video_grid_individual.html` | Video grid with individual controls | video/clip | usable | Individual video controls |

### Clip Player

**Location:** `tools/clip_player/`

**Purpose:** Individual clip playback with editing capabilities

| Directory Status | Notes |
|-----------------|-------|
| Empty | No tools currently in this directory |

---

## Data

| File | Description | Format | Notes |
|------|-------------|--------|-------|
| `data/transcript_episode3.json` | Episode 3 transcript | JSON | 32 segments, 220.45s duration |
| `data/transcript_combined.json` | Combined transcript | JSON | 220+ segments with word-level timing |
| `data/duplicates_analysis.json` | AI duplicate detection results | JSON | Groups of similar segments |
| `data/video_file_list.txt` | List of video files | TXT | File inventory |
| `data/video_combined.mp4` | Combined video file | MP4 | 400MB video file |

**Audio Directory:** `data/audio/`

| File | Description |
|------|-------------|
| `full_audio.mp4` | Full episode audio |
| `segment1.m4a` | Audio segment 1 |
| `segment2.m4a` | Audio segment 2 |
| `segment3.m4a` | Audio segment 3 |
| `segment4.m4a` | Audio segment 4 |

---

## Experiments

| File | Description | Level | Type | Notes |
|------|-------------|-------|------|-------|
| `experiments/debug_test.html` | Debug test | - | experimental | General debugging |
| `experiments/debug_words.html` | Debug words | word | experimental | Word-level debugging |
| `experiments/test_minimal.html` | Minimal test | - | experimental | Basic test |
| `experiments/test_words.html` | Test words | word | experimental | Word testing |
| `experiments/working_test.html` | Working test | - | experimental | Verified working |

---

## Archive

| File | Description | Notes |
|------|-------------|-------|
| `archive/implementation_summary.md` | Summary of inline editing implementation | Documents complete features |
| `archive/improvements_summary.md` | Summary of improvements | Documents changes |
| `archive/controls_fix_summary.md` | Controls fix documentation | Fixes applied |
| `archive/multi_select_improvements.md` | Multi-select improvements | Enhancement documentation |

---

## Naming Conventions Proposal

### Stable Naming Convention for Future Tools

**Format:** `[tool_category]_[primary_function]_[variant]`

**Examples:**
- `duplicate_analysis_interactive.html`
- `video_grid_with_ai.html`
- `inline_editing_complete.html`
- `timeline_editor_basic.html`

**Categories:**
- `report` - Static or interactive analysis reports
- `editor` - Tools for editing/manipulating content
- `tool` - Functional tools with specific capabilities
- `viewer` - Display-only tools
- `analyzer` - Analysis tools

### Tools vs Reports Classification Rule

**Tools (`tools/`):**
- Functional, interactive applications
- Enable user to perform operations
- Have editable state or controls
- Examples: Video grid, timeline editor, clip player

**Reports (`reports/`):**
- Read-only or primarily for viewing
- Analysis results and summaries
- Limited or no editing capabilities
- Examples: Duplicate analysis reports, statistics

**Editors (`editors/`):**
- Specifically designed for editing
- Primary purpose is content manipulation
- Rich editing capabilities
- Examples: Inline editors, split/merge tools, group management

### When to Archive vs Evolve

**Archive (`archive/`):**
- Old documentation files
- Summaries of completed work
- Historical records
- Implementation notes
- Never current working code

**Evolve:**
- Incremental improvements (v1, v2, v3...)
- Bug fixes and corrections
- Feature additions
- Working tools

**Keep in Experiments:**
- Proof of concept
- Debugging tools
- Test files
- Experimental features

---

## Quick Reference: Which File to Open?

### "I want to edit transcript text inline"
→ `editors/inline_editing_complete.html` (most complete)

### "I want to split or merge transcript segments"
→ `editors/split_merge_final.html` (production-ready)

### "I want to see duplicate analysis"
→ `reports/duplicate_analysis_ai.html` (AI-powered)
→ `reports/duplicate_analysis_noai.html` (no AI)

### "I want to view multiple videos in a grid"
→ `tools/video_grid/video_grid_individual.html` (most complete)

### "I want to edit timeline boundaries"
→ `tools/timeline_components/timeline_word_timing_editor_complete.html`

### "I want to assign segments to groups"
→ `editors/group_management_enhanced.html`

### "I want to understand the timeline architecture"
→ `tools/timeline_integrated/DEVELOPMENT_PLAN.md`

### "I want to test new features incrementally"
→ `tools/take_selection/` (v1 through v8)

---

## Uncertain Classifications

The following files have uncertain status or require clarification:

- **Timeline components**: Most components in `tools/timeline_components/` are marked experimental, but `timeline_word_timing_editor_complete.html` appears usable. Confirm which are production-ready.

- **Timeline integrated**: The component-based architecture in `tools/timeline_integrated/` is well-documented but appears incomplete. Determine status of each component.

- **Video grid variants**: Multiple variants exist (`basic`, `fixed`, `with_ai`, `individual`). Determine which is current recommendation.

---

*Last Updated: January 6, 2026*
*Status: First-pass organization complete*
