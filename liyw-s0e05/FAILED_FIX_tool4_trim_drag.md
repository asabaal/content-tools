# Failed Fix Attempt: Tool 4 Trim Handle Drag

**Date:** 2026-03-24
**Branch:** develop
**Tool:** tools/04-assemble/index.html
**Issue:** Blue trim handles (vertical bars on waveform edges) are not draggable in develop branch. They work correctly in render-good branch.

## Comparison

Both branches have identical:
- CSS for `.trim-handle`
- HTML structure (trimStart, trimEnd elements inside waveformWrapper)
- mousedown/mousemove/mouseup event handlers
- `getEffectiveTimes()` function
- `renderFullWaveform()` clip boundary rendering logic

## Key difference

The develop branch introduced `waveformClipMapping` — a mapping from selected clips to a concatenated "selected timeline" waveform. This means:

1. **Waveform duration** is the total selected timeline duration (concatenated clips), not the original video duration
2. **Clip positions on waveform** are in output timeline coordinates (via `waveformClipMapping`)
3. **But `trim_start`/`trim_end` on clips** are stored in original video coordinates
4. **The trim drag handler** converts mouse X to a time using `waveformData.duration` (timeline duration) but sets `clip.trim_start`/`clip.trim_end` directly — these are in different coordinate spaces

## Attempted Fix (FAILED)

Converted mouse position from selected timeline coordinates back to original video coordinates:

```javascript
let newTrimTime;
const mapping = waveformClipMapping?.find(m => m.clip_id === clip.id);
if (mapping) {
    const offset = outputTime - mapping.output_start;
    newTrimTime = mapping.original_start + offset;
} else {
    newTrimTime = outputTime;
}
```

Also changed bounds clamping from timeline duration to segment boundaries.

**Result:** Still did not work. User reverted the change.

## Root cause still unknown

The coordinate mapping theory was correct in principle, but the fix didn't resolve the issue. Something else may be interfering — possibly the `renderFullWaveform` re-rendering on each mousemove, or the way `waveformClipMapping` interacts with `getEffectiveTimes` during drag.
