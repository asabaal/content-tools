# Test Results: First Segment Render

**Date**: 2026-03-09
**Test**: Render first caption-bearing segment using manually constructed commands

---

## Commands Executed

### Pass 1: Extract Segment
```bash
ffmpeg -y -i data/video_combined.mp4 \
  -ss 1.721 -t 2.572 \
  -c:v libx264 -preset fast -crf 18 \
  -c:a aac -b:a 128k \
  data/output/segment_test_assembled.mp4
```

### Pass 2: Add Captions
```bash
ffmpeg -y -i data/output/segment_test_assembled.mp4 \
  -filter_complex_script data/output/pass2_filter.txt \
  -map "[vout]" -map 0:a \
  -c:v libx264 -preset medium -crf 23 \
  -c:a copy \
  data/output/segment_test_final.mp4
```

### Filter File Contents (pass2_filter.txt)
```
[0:v]drawbox=x=(w-574)/2:y=h-116-8:width=574:height=52:color=black@0.7:t=fill:enable='between(t,0.205,2.572)',drawtext=text='Where':fontfile=tools/05b-render/fonts/Bangers-Regular.ttf:fontsize=36:fontcolor=cb697f:x=(w-558)/2:y=h-116:enable='between(t,0.205,2.572)',drawtext=text='there':fontfile=tools/05b-render/fonts/Bangers-Regular.ttf:fontsize=36:fontcolor=cb697f:x=(w-558)/2+108:y=h-116:enable='between(t,0.459,2.572)',drawtext=text='was':fontfile=tools/05b-render/fonts/Bangers-Regular.ttf:fontsize=36:fontcolor=cb697f:x=(w-558)/2+216:y=h-116:enable='between(t,0.679,2.572)',drawtext=text='not':fontfile=tools/05b-render/fonts/Bangers-Regular.ttf:fontsize=36:fontcolor=cb697f:x=(w-558)/2+288:y=h-116:enable='between(t,0.859,2.572)',drawtext=text='God'\''s':fontfile=tools/05b-render/fonts/Bangers-Regular.ttf:fontsize=36:fontcolor=cb697f:x=(w-558)/2+360:y=h-116:enable='between(t,1.623,2.572)',drawtext=text='folk,':fontfile=tools/05b-render/fonts/Bangers-Regular.ttf:fontsize=36:fontcolor=cb697f:x=(w-558)/2+468:y=h-116:enable='between(t,1.939,2.572)'[vout]
```

---

## Output Files

| File | Size | Duration |
|------|------|----------|
| `data/output/segment_test_assembled.mp4` | 3.3 MB | 2.581s |
| `data/output/segment_test_final.mp4` | 1.5 MB | 2.581s |

---

## ISSUES FOUND

### Issue 1: "God's" Did Not Render

**Status**: ❌ FAIL

**Description**: The word "God's" did not appear in the rendered video output, despite being included in the filter with the correct timing (enable='between(t,1.623,2.572)').

**Potential causes** (not yet investigated):
- Apostrophe escaping issue in filter_complex_script
- Timing overlap with other words
- X-position calculation error

---

### Issue 2: Font Size Not Maintained

**Status**: ❌ FAIL

**Description**: The font size used in the render (36px for "medium") does not match what appears in the web app during caption styling (05a-capstyle).

**Expected**: Font size should match the visual appearance in the caption styling tool.

**Actual**: Font appears different/larger/smaller (needs visual comparison confirmation).

**Potential causes** (not yet investigated):
- Font size calculation in code differs from web app CSS
- `get_font_size()` function returns wrong values
- Web app uses different font rendering than FFmpeg

---

### Issue 3: Segment Content Incorrect

**Status**: ❌ FAIL

**Description**: The first renderable segment was expected to contain only "Where there was not" but continued past that, including additional words ("God's", "folk,").

**Expected**: First segment = "Where there was not" only

**Actual**: Rendered segment included "Where there was not God's folk,"

**This indicates the playable segment boundaries or word filtering logic is incorrect.**

**Potential causes** (not yet investigated):
- `get_words_in_range()` overlap logic including too many words
- Playable segment end time (4.293) is wrong
- Selected segment binding including words beyond intended boundary
- Deleted regions not being applied correctly to word filtering

---

## Summary

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Video duration | 2.572s | 2.581s | ✅ Pass |
| "God's" renders | Yes | No | ❌ FAIL |
| Font size matches web app | Yes | No | ❌ FAIL |
| Segment ends at "not" | Yes | Continued to "folk," | ❌ FAIL |

**3 of 4 checks FAILED**

---

## Next Steps

1. Investigate why "God's" did not render (apostrophe escaping?)
2. Compare font size calculation with web app styling
3. Trace playable segment boundary calculation to understand why extra words were included
4. Re-run test after fixes and verify all issues resolved

---

## Files for Review

- `data/output/segment_test_final.mp4` - Final video with captions (contains issues)
- `data/output/segment_test_assembled.mp4` - Raw segment without captions
- `data/output/pass2_filter.txt` - Filter used for Pass 2
