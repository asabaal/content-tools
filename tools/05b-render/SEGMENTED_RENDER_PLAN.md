# Segmented Rendering Implementation Plan

## Problem

The current two-pass rendering approach causes memory crashes when rendering the full video:
- Pass 1: Assembles all 28 segments into one video
- Pass 2: Adds ALL captions (300+ drawtext filters) to the full video
- Result: FFmpeg filter graph with 300+ simultaneous drawtext filters causes memory exhaustion

The `render_first_2_lines.py` test succeeded because it only processed 1 segment (~15 drawtext filters).

## Solution: Segmented Rendering

Instead of "assemble all → caption all", use "render segments individually → concat with re-encode":

```
Source video → Segment 0 (trim + 10 captions) → seg_0.mp4
             → Segment 1 (trim + 12 captions) → seg_1.mp4
             → ... (28 segments total)
             → Segment N (trim + 8 captions)  → seg_N.mp4
             
seg_0.mp4 + seg_1.mp4 + ... + seg_N.mp4 → concat with re-encode → final_video.mp4
```

**Benefits:**
- Bounded filter complexity per-segment (~10-15 drawtext filters, same as successful test)
- Reuses existing caption logic unchanged
- Final concat is trivial (no filters, just file joining)
- Re-encodes for clean segment boundaries

## Implementation Details

### Files Modified

#### 1. `ffmpeg_builder.py`

**Added:**
- `build_segment_render_command()` - builds ffmpeg command for single segment with trim + captions

**Removed:**
- `build_pass1_assembly_filter()` (lines 412-522)
- `build_pass1_command()` (lines 656-670)
- `build_pass2_command()` (lines 673-686)
- `build_pass2_caption_filter()` (lines 525-653)
- `build_timeline_assembly_filter()` (lines 69-194) - only used by broken single-pass approach

**Kept:**
- `build_caption_filters()` - reused for per-segment captions
- Helper functions (escape, color conversion, positioning, etc.)

#### 2. `render.py`

**Added:**
```python
def render_segmented(
    input_video: Path,
    output_video: Path,
    output_dir: Path,
    timeline_clips: list,
    caption_events: list,
    caption_style: dict,
    font_path: Path,
    caption_breaks: dict,
    verbose: bool,
    keep_segments: bool
) -> bool:
```
Orchestrates the segment rendering loop and final concat.

**Modified:**
- `main()` - removed two-pass logic, always use segmented approach
- Added `--keep-segments` flag for debugging
- Kept `--segment` flag for testing individual segments

**Removed:**
- `render_two_pass()` function (lines 54-136)
- `--two-pass` flag logic (lines 146-147, 212-244)

### Technical Flow

#### Segment Render Command Builder
```python
def build_segment_render_command(
    input_video: str,
    output_video: str,
    seg_start: float,
    seg_end: float,
    caption_events: List[Dict],  # Only events for THIS segment
    caption_style: dict,
    font_path: str,
    caption_breaks: dict
) -> List[str]:
```

Key: Use `-ss` before `-i` for fast seeking, then apply caption filter to the trimmed segment.

#### Segment Rendering Loop
1. Create temp directory for segments
2. For each playable segment:
   - Extract caption events for that specific segment only
   - Build ffmpeg command with trim + captions
   - Render to temp file (e.g., `seg_1.mp4`)
   - Show progress: "Rendering segment X/Y..."
   - Fail immediately if any segment fails
3. Concat all segments with re-encode for clean joins

#### Final Concat
```bash
ffmpeg -y -f concat -safe 0 -i concat.txt \
  -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 128k \
  output_video.mp4
```

#### Cleanup
- Delete temp segment directory unless `--keep-segments` flag is set

### Command Line Interface

```bash
# Normal full render
python 05b-render/render.py

# Render specific segment (for testing)
python 05b-render/render.py --segment 5

# Keep temporary segments for debugging
python 05b-render/render.py --keep-segments

# Verbose output
python 05b-render/render.py --verbose

# Dry run (show commands without executing)
python 05b-render/render.py --dry-run
```

### Edge Cases

1. **Empty playable segments:** Skip (shouldn't happen, but defensive)
2. **No captions for segment:** Still render segment, just without caption filter
3. **Single segment:** Skip concat step, just rename segment file to output
4. **Concurrent rendering:** NOT in initial implementation (can add later if needed)

### Testing Strategy

1. **Unit test:** `--segment 0` should produce identical output to current `render_first_2_lines.py`
2. **Integration test:** Full render should complete without memory crash
3. **Visual verification:** Compare final output quality against expected style
4. **Timing verification:** Run post-render verification (already exists in codebase)

### Code Stats

- `render.py`: ~150 lines modified/removed, ~100 lines added
- `ffmpeg_builder.py`: ~250 lines removed, ~50 lines added
- Net reduction: ~250 lines of code (simpler!)

## Decision Log

1. **Re-encode vs stream copy:** Re-encode for clean segment joins (user decision)
2. **Progress visibility:** Show "Rendering segment X/Y..." (user decision)
3. **Error handling:** Stop immediately on segment failure (user decision)
4. **Cleanup:** Delete segments by default, add `--keep-segments` flag (user decision)
5. **Remove old code:** Yes, delete two-pass code entirely to avoid confusion (user decision)
