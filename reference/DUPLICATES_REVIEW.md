# Duplicates Review - Content Editing Tools

This document identifies files that appear to be variants, duplicates, or experimentally related versions of the same tool.

---

## Executive Summary

Total duplicate groups identified: **8 groups** containing **28 files**

**Note:** No files have been deleted or merged. This is a review document only.

---

## Duplicate Group 1: Duplicate Analysis Reports

**Category:** Reports - Duplicate Detection
**Functional Level:** Transcript
**Total Files:** 8 files

### Files in Group:
1. `reports/duplicate_analysis_simple.html` (formerly `episode3_full_noai_report.html`)
2. `reports/duplicate_analysis_improved.html` (formerly `episode3_improved_report.html`)
3. `reports/duplicate_analysis_noai.html` (formerly `episode3_noai_report.html`)
4. `reports/duplicate_analysis_ai.html` (formerly `episode3_combined/ai_report.html`)
5. `reports/duplicate_analysis_basic.html` (formerly `episode3_combined/simple_report.html`)
6. `reports/duplicate_analysis_interactive.html` (formerly `episode3_combined/interactive_report.html`)
7. `reports/duplicate_analysis_updated.html` (formerly `episode3_combined/updated_report.html`)
8. `reports/transcript_duplicates.html` (formerly `episode3_combined/combined_transcript.duplicates.html`)

### How They Appear to Differ:
- **simple.html** vs **basic.html**: Nearly identical structure, both show duplicate analysis results with video player
- **improved.html**: Enhanced styling and layout compared to simple/basic versions
- **noai.html**: Uses `simple_text_similarity` instead of AI model
- **ai.html**: Uses `llama3.1:8b` AI model for duplicate detection
- **interactive.html**: Includes inline transcript editing capabilities (more functional than others)
- **updated.html**: Updated version with improvements
- **transcript_duplicates.html**: Same analysis but formatted as transcript display

### Why Suspected Duplicates:
All files display duplicate analysis with:
- Video player
- Summary cards (total segments, duplicate groups, processing time)
- Segment cards with play buttons
- Similar CSS styling (gradient backgrounds, card layouts)

**Key Difference:** `interactive.html` has editing capabilities, making it more feature-rich than the others.

**Recommendation:** Keep `duplicate_analysis_interactive.html` as primary (most feature-rich), `duplicate_analysis_ai.html` for AI analysis, `duplicate_analysis_noai.html` for simple analysis. Archive others.

---

## Duplicate Group 2: Inline Editing Tools

**Category:** Editors - Inline Text Editing
**Functional Level:** Word
**Total Files:** 2 files

### Files in Group:
1. `editors/inline_editing_complete.html` (formerly `episode3_combined/complete_inline_editing.html`)
2. `editors/inline_editing_updated.html` (formerly `episode3_combined/updated_inline_editing.html`)

### How They Appear to Differ:
- **complete.html**: According to `IMPLEMENTATION_SUMMARY.md`, this is the final working implementation with all features
- **updated.html**: File size slightly smaller (160,923 vs 163,043 bytes), suggests it may be an earlier or alternative version

### Why Suspected Duplicates:
Both provide:
- Inline text editing with ✏️ buttons
- Segment split/merge functionality
- Group management
- Video playback
- Auto-save to browser storage

**Recommendation:** Use `inline_editing_complete.html` as documented in implementation summary. Verify if updated.html has any unique features.

---

## Duplicate Group 3: Split/Merge Tools

**Category:** Editors - Split/Merge
**Functional Level:** Word
**Total Files:** 7 files

### Files in Group:
1. `editors/split_merge_fixed.html` (formerly `episode3_combined/split_merge_fixed.html`)
2. `editors/split_merge_functionality.html` (formerly `episode3_combined/split_merge_functionality.html`)
3. `editors/split_merge_corrected.html` (formerly `episode3_combined/corrected_split_merge.html`)
4. `editors/split_merge_final.html` (formerly `episode3_combined/final_split_merge.html`)
5. `editors/split_merge_controls_fixed.html` (formerly `episode3_combined/fixed_split_merge.html`)
6. `editors/split_merge_improved.html` (formerly `episode3_combined/improved_split_merge.html`)
7. `editors/split_merge_working.html` (formerly `episode3_combined/working_split_merge.html`)

### How They Appear to Differ:
- **functionality.html**: Core split/merge implementation
- **fixed.html**: Fixed version of functionality.html
- **corrected.html**: Bug fixes applied
- **final.html**: Marked as final version (based on filename)
- **controls_fixed.html**: Focus on UI controls fixes
- **improved.html**: Enhanced features
- **working.html**: Tested working version

### Why Suspected Duplicates:
Based on file structure and names, these appear to be iterative improvements on the same core functionality. File sizes are all very similar (~129-130 KB except corrected at 153 KB), suggesting incremental changes.

**Recommendation:** Keep `split_merge_final.html` as production version. Archive others as historical progression.

---

## Duplicate Group 4: Video Grid Tools

**Category:** Tools - Video Grid
**Functional Level:** Video/Clip
**Total Files:** 4 files

### Files in Group:
1. `tools/video_grid/video_grid_basic.html` (formerly `episode3_combined/video_grid_report.html`)
2. `tools/video_grid/video_grid_fixed.html` (formerly `episode3_combined/video_grid_report_fixed.html`)
3. `tools/video_grid/video_grid_with_ai.html` (formerly `episode3_combined/video_grid_report_fixed_ai.html`)
4. `tools/video_grid/video_grid_individual.html` (formerly `episode3_combined/video_grid_individual_controls.html`)

### How They Appear to Differ:
- **basic.html**: Basic video grid implementation
- **fixed.html**: Fixed version of basic.html
- **with_ai.html**: Includes AI integration (based on filename)
- **individual.html**: Has individual video controls (based on filename)

### Why Suspected Duplicates:
All display videos in grid format with similar naming patterns. The "report_fixed" vs "fixed" naming suggests iterative bug fixing.

**Recommendation:** Keep `video_grid_individual.html` (most feature-rich with individual controls). Verify AI integration in with_ai.html for unique features.

---

## Duplicate Group 5: Group Management Tools

**Category:** Editors - Group Management
**Functional Level:** Transcript
**Total Files:** 2 files

### Files in Group:
1. `editors/group_management_enhanced.html` (formerly `episode3_combined/enhanced_group_management.html`)
2. `editors/group_management_multiselect.html` (formerly `episode3_combined/multi_select_groups.html`)

### How They Appear to Differ:
- **enhanced.html**: Enhanced group management features (95,938 bytes)
- **multiselect.html**: Multi-select functionality (167,737 bytes - larger)

### Why Suspected Duplicates:
Both handle group assignment and management. The multiselect version is significantly larger, suggesting it may include all enhanced features plus multi-select.

**Recommendation:** Keep `group_management_multiselect.html` (more features). Verify enhanced.html for any unique functionality.

---

## Duplicate Group 6: Audio Preview Components

**Category:** Timeline Components
**Functional Level:** Timeline
**Total Files:** 4 files

### Files in Group:
1. `tools/timeline_components/component4_audio_preview_v1.html`
2. `tools/timeline_components/component4_audio_preview_v2.html`
3. `tools/timeline_components/component4_audio_preview_v2.5.html`
4. `tools/timeline_components/component4_audio_preview_v3.html`

### How They Appear to Differ:
- **v1**: First version
- **v2**: Second version (improvements)
- **v2.5**: Minor update to v2
- **v3**: Third version (latest)

### Why Suspected Duplicates:
Clear version history with incremental improvements. All are part of the "component4" audio preview feature in timeline editor development.

**Recommendation:** Keep `component4_audio_preview_v3.html` as current version. Archive v1, v2, v2.5.

---

## Duplicate Group 7: Take Selection Tool Versions

**Category:** Tools - Take Selection
**Functional Level:** Transcript
**Total Files:** 8 files

### Files in Group:
1. `tools/take_selection/v1_basic.html` - Basic structure only
2. `tools/take_selection/v2_playback.html` - Adds video playback
3. `tools/take_selection/v3_edit.html` - Adds text editing
4. `tools/take_selection/v4_groups.html` - Adds group assignment
5. `tools/take_selection/v5_merge.html` - Adds merge/split
6. `tools/take_selection/v6_multiselect.html` - Adds multi-select
7. `tools/take_selection/v6_complete_transcript.html` - Complete transcript v6
8. `tools/take_selection/v6_dynamic_groups.html` - Dynamic groups v6
9. `tools/take_selection/v7_fixed_groups.html` - Fixed groups v7
10. `tools/take_selection/v8_video_grid.html` - Video grid v8

**Note:** This is intentional version control, not accidental duplication. According to `build_plan.md`, these were built incrementally as part of a rebuild process.

### How They Appear to Differ:
Each version adds specific functionality as documented in the build plan:
- v1 → v2 → v3 → v4 → v5 → v6 (with variants) → v7 → v8

### Why Suspected Duplicates:
All build toward the same tool but represent different development stages. Two v6 variants exist (complete_transcript vs dynamic_groups).

**Recommendation:** Keep `v8_video_grid.html` as final version. Archive v1-v7 as development history unless specific versions are needed for reference.

---

## Duplicate Group 8: Test/Debug Files

**Category:** Experiments
**Functional Level:** Various
**Total Files:** 5 files

### Files in Group:
1. `experiments/debug_test.html`
2. `experiments/debug_words.html`
3. `experiments/test_minimal.html`
4. `experiments/test_words.html`
5. `experiments/working_test.html`

### How They Appear to Differ:
- **debug_test.html**: General debugging test
- **debug_words.html**: Word-level debugging
- **test_minimal.html**: Minimal test (941 bytes - smallest)
- **test_words.html**: Word testing
- **working_test.html**: Working version of a test

### Why Suspected Duplicates:
All are test/debug files with overlapping purposes. Some may be duplicates created during development.

**Recommendation:** Keep `working_test.html` as verified working. Archive others. Consider if specific debug tools are still needed.

---

## Additional Potential Duplicates

### Paragraph Edit Reports
- `reports/paragraph_edit_analysis.html`
- `reports/paragraph_edit_final.html`
- `reports/transcript_editor_analysis.html`

These appear to be related reports on paragraph/transcript editing capabilities. May be worth consolidating.

---

## Summary Table

| Group | Category | Files | Recommended Keep | Notes |
|-------|----------|-------|------------------|-------|
| 1 | Duplicate Analysis | 8 | interactive.html, ai.html, noai.html | Archive others |
| 2 | Inline Editing | 2 | complete.html | Verify updated.html |
| 3 | Split/Merge | 7 | final.html | Archive others |
| 4 | Video Grid | 4 | individual.html | Verify AI features |
| 5 | Group Management | 2 | multiselect.html | Verify enhanced.html |
| 6 | Audio Preview | 4 | v3.html | Archive v1-v2.5 |
| 7 | Take Selection | 10 | v8.html | Archive v1-v7 |
| 8 | Test/Debug | 5 | working_test.html | Archive others |

---

## Next Steps for Human Review

1. **Verify unique features** in "verify" recommendations above
2. **Test functionality** of recommended keepers
3. **Archive** clearly outdated versions
4. **Consolidate** reports if content overlaps significantly
5. **Remove** truly duplicate files (exact copies with no differences)
6. **Update** FUNCTIONAL_MAP.md after decisions

---

**Total Files to Review:** 28 files across 8 groups
**Estimated Files to Keep:** 8-12 files
**Estimated Files to Archive:** 16-20 files

---

*Review Date: January 6, 2026*
*Status: Ready for human decision*
