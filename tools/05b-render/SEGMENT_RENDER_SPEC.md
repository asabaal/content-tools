# First Segment Render Specification

**Document Purpose**: Authoritative specification of what the first caption-bearing segment should contain when rendered. This document represents the expected behavior based on code analysis. Actual render output should be compared against this spec to identify discrepancies.

**Created**: 2026-03-07
**Status**: Belief/Expectation - To Be Verified

---

## Source Data (from project.json)

### Clip Metadata

| Field | Value |
|-------|-------|
| Clip ID | `clip_mlmz73gu_7` |
| Timeline Position | 0 |
| Trim Range | 0.000 → 218.731 |
| Deleted Regions | 54 regions |
| Selected Segment Index | 0 (points to transcript segment 0) |

### First Deleted Regions (affecting start of clip)

| # | Start | End | Duration |
|---|-------|-----|----------|
| 1 | 1.262 | 1.721 | 0.459s |
| 2 | 4.293 | 5.327 | 1.034s |
| 3 | 6.453 | 8.147 | 1.694s |

### Playable Segments (computed by segments.py)

The clip has 55 playable segments after subtracting 54 deleted regions from the trim range.

| # | Start | End | Duration | Has Words |
|---|-------|-----|----------|-----------|
| 1 | 0.000 | 1.262 | 1.262s | NO (silence) |
| **2** | **1.721** | **4.293** | **2.572s** | **YES - First captions** |
| 3 | 5.327 | 6.453 | 1.126s | YES |
| 4 | 8.147 | 10.802 | 2.655s | YES |
| ... | ... | ... | ... | ... |

---

## First Caption-Bearing Segment (Playable Segment #2)

This is the segment we are testing.

### Segment Bounds

| Property | Value |
|----------|-------|
| Source Start | 1.721 seconds (in video_combined.mp4) |
| Source End | 4.293 seconds |
| Duration | 2.572 seconds |
| Output Start | 0.000 seconds (start of rendered output) |
| Output End | 2.572 seconds |

### Why Start Is 1.721 (Not 0.000 or 1.620)

1. Trim start is 0.000
2. First deleted region covers 1.262 → 1.721
3. Therefore, first playable content starts at 1.721 (after the first deletion ends)

Note: There is a 1.262s silent playable segment before this (0.000-1.262), but it has no transcript words.

### Why End Is 4.293 (Not 5.236 or 6.080)

1. Second deleted region covers 4.293 → 5.327
2. The playable segment must end at 4.293 (where the deletion begins)
3. The word "folk," originally extends to 5.236, but is truncated at 4.293

---

## Caption Word Data

### Source: Transcript Segment 0

```
Text: "Where there was not God's folk, and then there was."
Full segment range: 1.620 → 6.080
```

### Words in First Playable Segment (1.721 → 4.293)

| # | Word | Source Start | Source End | Visible Start | Visible End | Output Start | Output End | Duration | Color |
|---|------|--------------|------------|---------------|-------------|--------------|------------|----------|-------|
| 1 | Where | 1.926 | 2.180 | 1.926 | 2.180 | 0.205 | 0.459 | 0.254s | #cb697f |
| 2 | there | 2.180 | 2.400 | 2.180 | 2.400 | 0.459 | 0.679 | 0.220s | #cb697f |
| 3 | was | 2.400 | 2.580 | 2.400 | 2.580 | 0.679 | 0.859 | 0.180s | #cb697f |
| 4 | not | 2.580 | 3.344 | 2.580 | 3.344 | 0.859 | 1.623 | 0.764s | #cb697f |
| 5 | God's | 3.344 | 3.660 | 3.344 | 3.660 | 1.623 | 1.939 | 0.316s | #cb697f |
| 6 | folk, | 3.660 | 5.236 | **3.660** | **4.293** | **1.939** | **2.572** | **0.633s** | #cb697f |

### Key Observations

1. **Output time calculation**: `output_time = source_time - segment_start = source_time - 1.721`
2. **Word truncation**: "folk," visible duration (0.633s) is less than original duration (1.576s) because the segment ends at 4.293
3. **All words end at 2.572**: The `enable='between(t,start,2.572)'` means all captions disappear when the segment ends
4. **First word appears at 0.205**: Not at 0.000 (there's silence before "Where" starts)

---

## Timeline Visualization

```
SOURCE VIDEO TIMELINE (video_combined.mp4)
═══════════════════════════════════════════════════════════════════════════
0.000        1.262   1.620   1.721   1.926   2.18   2.40   2.58   3.34   3.66   4.293   5.236   5.327
│              │       │       │       │       │      │      │      │      │      │       │       │
│  PLAYABLE    │       │       │       │       │      │      │      │      │      │       │       │
│  (silence)   │ DELETED│       │       │       │      │      │      │      │      │       │       │
│              │       │       │       │       │      │      │      │      │      │       │       │
└──────────────┘       │       └───────┴───────┴──────┴──────┴──────┴──────┴───────┘       │
                       │               ▲       ▲      ▲      ▲      ▲      ▲               │
                       │               │       │      │      │      │      │               │
                       │            Where   there   was    not   God's  folk,          DELETED
                       │                                                               │
                       └───────────────────────────────────────────────────────────────┘
                                              PLAYABLE SEGMENT #2

OUTPUT VIDEO TIMELINE (rendered segment)
═══════════════════════════════════════════════════════════════════════════
0.000                    0.205    0.459  0.679  0.859  1.623  1.939       2.572
│                          │       │      │      │      │      │           │
│      (silence)           │ Where │there │ was  │ not  │God's │ folk,     │ END
│                          │       │      │      │      │      │           │
└──────────────────────────┴───────┴──────┴──────┴──────┴──────┴───────────┘
```

---

## Expected FFmpeg Commands

### Pass 1: Extract Segment (No Captions)

```bash
ffmpeg -y \
  -i data/video_combined.mp4 \
  -ss 1.721 -t 2.572 \
  -c:v libx264 -preset fast -crf 18 \
  -c:a aac -b:a 128k \
  data/output/segment_test_assembled.mp4
```

**Expected Output**:
- Duration: 2.572 seconds
- Content: Video from 1.721-4.293 of source
- No captions burned in

### Pass 2: Add Captions

```bash
ffmpeg -y \
  -i data/output/segment_test_assembled.mp4 \
  -filter_complex "[0:v]\
drawbox=x=(w-574)/2:y=h-116-8:width=574:height=52:color=black@0.7:t=fill:enable='between(t,0.205,2.572)',\
drawtext=text='Where':fontfile=tools/05b-render/fonts/Bangers-Regular.ttf:fontsize=36:fontcolor=cb697f:x=(w-558)/2:y=h-116:enable='between(t,0.205,2.572)',\
drawtext=text='there':fontfile=tools/05b-render/fonts/Bangers-Regular.ttf:fontsize=36:fontcolor=cb697f:x=(w-558)/2+108:y=h-116:enable='between(t,0.459,2.572)',\
drawtext=text='was':fontfile=tools/05b-render/fonts/Bangers-Regular.ttf:fontsize=36:fontcolor=cb697f:x=(w-558)/2+216:y=h-116:enable='between(t,0.679,2.572)',\
drawtext=text='not':fontfile=tools/05b-render/fonts/Bangers-Regular.ttf:fontsize=36:fontcolor=cb697f:x=(w-558)/2+288:y=h-116:enable='between(t,0.859,2.572)',\
drawtext=text='God\\'s':fontfile=tools/05b-render/fonts/Bangers-Regular.ttf:fontsize=36:fontcolor=cb697f:x=(w-558)/2+360:y=h-116:enable='between(t,1.623,2.572)',\
drawtext=text='folk,':fontfile=tools/05b-render/fonts/Bangers-Regular.ttf:fontsize=36:fontcolor=cb697f:x=(w-558)/2+468:y=h-116:enable='between(t,1.939,2.572)'\
[vout]" \
  -map "[vout]" -map 0:a \
  -c:v libx264 -preset medium -crf 23 \
  -c:a copy \
  data/output/segment_test_final.mp4
```

**Expected Output**:
- Duration: 2.572 seconds
- Caption "Where" appears at 0.205s
- All 6 captions visible by 1.939s
- All captions disappear at 2.572s
- Caption position: lower_third (y = h-116)

---

## Verification Checklist

After running the render, verify:

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| Video duration | 2.572s | | |
| First caption appears at | 0.205s | | |
| "Where" visible at 0.205s | Yes | | |
| "there" visible at 0.500s | Yes | | |
| "was" visible at 0.700s | Yes | | |
| "not" visible at 1.000s | Yes | | |
| "God's" visible at 1.700s | Yes | | |
| "folk," visible at 2.000s | Yes | | |
| All captions gone at 2.572s | Yes | | |
| Caption color | #cb697f (pink) | | |
| Caption position | Lower third | | |

---

## Known Issues / Potential Problems

### 1. Clamping Bug in segments.py

The code clamps `trim_start` and `trim_end` to `selected_segment` bounds:

```python
# segments.py:32
trim_start = max(min(raw_trim_start, sel_end), sel_start)

# segments.py:43  
trim_end = min(max(raw_trim_end, sel_start), sel_end)
```

**Impact**: If trim range extends beyond selected_segment (as it does here: trim 0-218 vs selected 1.62-6.08), content outside is lost.

**Current Behavior**: Clamps to 1.620-6.080, then applies deletions.

**Expected Behavior**: Should use full trim range, not clamp to selected_segment.

### 2. Caption Event Selection Logic

In `captions.py:88-111`, the code tries to find matching transcript segment:
1. First tries `authoritative_segment_index` from selected_segment
2. Falls back to time-based search if no overlap

**Potential Issue**: For playable segment at 1.721-4.293, the authoritative segment (0) DOES overlap (1.620-6.080), so it should work correctly.

### 3. Word Color Lookup

Colors are stored as `f"{segment_index}_{word_index}"` keys in `word_colors` dict.

**Verify**: That segment_index=0 and word_index 0-5 have correct color entries.

---

## Code References

| File | Line | Purpose |
|------|------|---------|
| segments.py | 10-69 | `get_playable_segments()` - computes playable regions |
| segments.py | 32, 43 | Clamping to selected_segment bounds (potential bug) |
| captions.py | 60-140 | `build_caption_events()` - maps words to output timeline |
| captions.py | 18-57 | `get_words_in_range()` - finds words in playable segment |
| ffmpeg_builder.py | 617-649 | `generate_concat_demuxer_list()` - builds concat list |
| ffmpeg_builder.py | 480-581 | `build_pass2_caption_filter()` - builds drawtext filters |

---

## Conclusion

This specification documents what **should** happen when rendering the first caption-bearing segment. Any deviation between this spec and actual render output indicates a bug in the rendering pipeline.

Next steps:
1. Run the render
2. Compare output against this spec
3. Document any discrepancies
4. Trace code to find root cause of discrepancies
