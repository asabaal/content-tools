# Render Pipeline Issues

## Issue #001: Word Right-Edge Clipping

**Date:** 2026-03-10
**Status:** UNRESOLVED

### Description
Individual caption words appear to be **slightly cut off on their right edge** during FFmpeg render. This affects EACH word independently - not just the last word in a line.

### Visual Symptoms
- Each word's right side appears clipped/cut off
- Not related to word spacing or background box sizing
- Occurs consistently across all words in all lines
- Approximate clipping: 1-3 pixels per word

### Attempted Fix #1: Increase Character Width Multiplier

**Change:** `ffmpeg_builder.py` line 235, 561
```python
# From:
char_width = font_size * 0.4

# To:
char_width = font_size * 0.5
```

**Rationale:** Bangers is a bold display font; assumed char_width estimate was too small, causing word overlap.

**Result:** FAILED ❌
- Increased spacing BETWEEN words
- Did NOT fix clipping of individual word rendering
- Words still appear cut off on right edge
- Box became too wide (1042px, nearly full video width)

**Reverted:** 2026-03-10

### Root Cause Hypotheses

1. **FFmpeg drawtext filter intrinsic clipping**
   - Drawtext may have default bounding/clipping behavior
   - May need explicit `text_align` or `text_shaping` options

2. **Font rendering in ffmpeg**
   - Bangers TTF may have glyph metadata issues
   - Font may not be fully compatible with ffmpeg's font renderer

3. **Character width calculation affects word BOUNDARIES, not rendering**
   - char_width only controls spacing between words
   - Does not affect how ffmpeg renders each word's glyphs

### Next Steps to Investigate

1. **Test with different font** (e.g., Arial) to rule out font-specific issue
2. **Check ffmpeg drawtext documentation** for:
   - `textfile` vs `text` parameter differences
   - `text_shaping` option
   - `borderw` affecting text bounds
   - `fix_bounds` or similar options
3. **Test single word in isolation** to see if clipping still occurs
4. **Try ASS/SSA subtitle filter** instead of drawtext
5. **Check if `box=1` drawtext option** helps with text bounds calculation

### Related Files
- `tools/05b-render/ffmpeg_builder.py` (lines 235, 561: char_width calculation)
- `tools/05b-render/render_first_2_lines.py` (render script)
- `data/output/verification/first_2_lines/` (validation frames)

---

## Issue #002: [Template for next issue]

**Date:** 
**Status:** 

### Description


### Visual Symptoms


### Attempted Fixes


### Root Cause


### Resolution


---
