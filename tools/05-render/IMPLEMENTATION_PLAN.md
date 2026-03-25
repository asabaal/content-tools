# Step 5: CAPTION + RENDER

**Created**: February 16, 2026
**Status**: In Progress

---

## Overview

This step adds caption styling and final video rendering to the pipeline.

### Components

| Tool | Type | Purpose |
|------|------|---------|
| **05a-capstyle** | Browser HTML | Preview + style captions with word-level colors |
| **05b-render** | Python CLI | Render final video with burned-in captions + SRT |

### Data Flow

```
project.json (from 04-assemble)
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     05a-capstyle (UI)                            │
│                                                                  │
│  - Load video with transcript                                    │
│  - Display caption overlay on video                              │
│  - Multi-select words (click, shift+click, ctrl+click)          │
│  - Apply colors to selected words                                │
│  - Live preview of styled captions                               │
│  - Save caption_style + word_colors to project.json              │
└──────────────────────────────────────────────────────────────────┘
       │
       │ (project.json with color metadata)
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     05b-render (Python)                          │
│                                                                  │
│  1. Load project.json                                            │
│  2. Compute playable segments (trim - deleted_regions)           │
│  3. Extract words with colors for each segment                   │
│  4. Generate ffmpeg filter graph with drawtext filters          │
│  5. Execute ffmpeg to render video                               │
│  6. Generate SRT file with compressed timestamps                 │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│  Output:                                                         │
│  - data/output/final_video.mp4 (burned-in captions)             │
│  - data/output/captions.srt (compressed timestamps)             │
└──────────────────────────────────────────────────────────────────┘
```

---

## Tool 05a: CAPTION STYLER

**File**: `tools/05a-capstyle/index.html`

### Features

| # | Feature | Details |
|---|---------|---------|
| 1 | Video preview | video_combined.mp4 with caption overlay |
| 2 | Caption overlay | HTML/CSS positioned at lower third |
| 3 | Word list | Scrollable grid of all words |
| 4 | Multi-select | Click (single), Shift+click (add), Ctrl+click (toggle) |
| 5 | Color picker | Native color input + preset swatches |
| 6 | Color presets | Brand (#cb697f), Accent (#4cc9f0), White (#ffffff) |
| 7 | Segment color | Color all words in current segment |
| 8 | Live preview | Selected colors immediately visible |
| 9 | Font rendering | Bangers font via CSS @font-face |
| 10 | Save button | Persist caption_style + word_colors |
| 11 | Render button | Trigger Python render via /api/render |

### UI Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CAPTION STYLER                              [Save] [Render]                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │                          VIDEO PREVIEW                              │   │
│  │                                                                     │   │
│  │            ┌───────────────────────────────────────┐               │   │
│  │            │   Where there was not God's folk,     │               │   │
│  │            │         and then there was.           │               │   │
│  │            └───────────────────────────────────────┘               │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [▶ Play] [⏸ Pause] [⏮] [⏭]   Timeline: ═════════○═══════════════════     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STYLE                                    WORDS                             │
│  ┌────────────────────────┐             ┌─────────────────────────────────┐│
│  │ Font: Bangers          │             │ Clip: [All clips ▼]             ││
│  │ Size: [Medium     ▼]   │             │                                 ││
│  │ Position: [Lower ▼]    │             │  Where  there  was   not   God's││
│  │ Background: [Dark ▼]   │             │  folk,  and   then  there  was. ││
│  │                        │             │  Welcome to   Life   is    your ││
│  │ Default: [■ #ffffff ]  │             │  word   episode  three.  In    ││
│  │                        │             │  this   show,   we     build   ││
│  │ PRESETS                │             │  up     our     ...            ││
│  │ ■ #cb697f  Brand       │             │                                 ││
│  │ ■ #4cc9f0  Accent      │             │  Selection: 3 words selected    ││
│  │ ■ #ffffff  White       │             │  [■ #cb697f        ] [Apply]    ││
│  │                        │             │                                 ││
│  │ [+ Add preset]         │             │  [Color segment] [Reset]        ││
│  └────────────────────────┘             └─────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Multi-Select Behavior

| Action | Result |
|--------|--------|
| Click word | Select single word (clear previous) |
| Shift+Click | Add to selection (range select) |
| Ctrl+Click | Toggle word in/out of selection |
| Click color | Apply color to all selected words |
| "Color segment" | Select + color all words in segment |

---

## Tool 05b: RENDER

**Directory**: `tools/05b-render/`

### Files

| File | Purpose |
|------|---------|
| `render.py` | CLI entry point, orchestrates render |
| `segments.py` | Compute playable segments from trim + deleted_regions |
| `captions.py` | Extract caption data with colors |
| `ffmpeg_builder.py` | Generate ffmpeg filter graph |
| `srt.py` | Generate SRT file |
| `fonts/Bangers-Regular.ttf` | Caption font |
| `README.md` | Usage documentation |

### Processing Flow

```
1. Load project.json
       │
2. Filter clips (enabled, in_timeline) → sort by timeline_position
       │
3. For each clip:
       │
       ├─ Get playable_segments (trim - deleted_regions)
       │
       └─ For each playable segment:
             │
             ├─ Get words in time range
             ├─ Get color per word
             ├─ Generate drawtext filter
             └─ Track for SRT (compressed time)
       │
4. Build ffmpeg filter graph:
       │
       ├─ trim filters for segments
       ├─ drawtext filters for captions
       └─ concat filter
       │
5. Execute ffmpeg
       │
6. Generate SRT
       │
7. Output files
```

### Playable Segment Algorithm

```python
def get_playable_segments(clip):
    """Return list of (start, end) tuples for playable video."""
    trim_start = clip.get('trim_start', clip['selected_segment']['start'])
    trim_end = clip.get('trim_end', clip['selected_segment']['end'])
    deleted = sorted(clip.get('deleted_regions', []), key=lambda r: r['start'])
    
    segments = [(trim_start, trim_end)]
    
    for del_region in deleted:
        new_segments = []
        for seg_start, seg_end in segments:
            if del_region['end'] <= seg_start or del_region['start'] >= seg_end:
                new_segments.append((seg_start, seg_end))
            elif del_region['start'] <= seg_start and del_region['end'] >= seg_end:
                pass  # Fully deleted
            else:
                if del_region['start'] > seg_start:
                    new_segments.append((seg_start, del_region['start']))
                if del_region['end'] < seg_end:
                    new_segments.append((del_region['end'], seg_end))
        segments = new_segments
    
    return segments
```

### Caption Style Configuration

```json
{
  "caption_style": {
    "font_family": "Bangers",
    "font_path": "tools/05b-render/fonts/Bangers-Regular.ttf",
    "font_size": "medium",
    "position": "lower_third",
    "background": "dark_box",
    "default_color": "#ffffff",
    "color_presets": [
      {"name": "Brand", "color": "#cb697f"},
      {"name": "Accent", "color": "#4cc9f0"},
      {"name": "White", "color": "#ffffff"}
    ]
  },
  "word_colors": {
    "0_0": "#cb697f",
    "0_1": "#ffffff",
    "0_4": "#4cc9f0"
  }
}
```

Key format: `"{segment_index}_{word_index}"`

### ffmpeg Filter Example

```bash
ffmpeg -i video_combined.mp4 -filter_complex "
  [0:v]trim=0:1.262,setpts=PTS-STARTPTS,
    drawtext=text='Where':fontfile=Bangers-Regular.ttf:
      fontcolor=cb697f:fontsize=48:x=(w-text_w)/2:y=h-150:
      box=1:boxcolor=black@0.7:enable='between(t,0,0.25)',
    drawtext=...[v1];
  [0:v]trim=1.721:4.293,setpts=STARTPTS,
    drawtext=...[v2];
  [v1][v2]concat=n=2:v=1[outv]
" -map "[outv]" -map 0:a -c:v libx264 -c:a copy output.mp4
```

### CLI Usage

```bash
# Basic render
python tools/05b-render/render.py

# Options
python tools/05b-render/render.py --verbose
python tools/05b-render/render.py --dry-run
python tools/05b-render/render.py --output /custom/path/
```

### Output Files

| File | Description |
|------|-------------|
| `data/output/final_video.mp4` | Rendered video with burned-in captions |
| `data/output/captions.srt` | SRT subtitles (compressed timestamps) |

---

## API Endpoint

### /api/render (POST)

Triggers render from Caption Styler UI.

**Request**: Empty POST body

**Response**:
```json
{"status": "rendering_started"}
```

**Implementation**: Added to `serve.py`

```python
def handle_render(self):
    import subprocess
    import threading
    
    def run_render():
        subprocess.run([sys.executable, 'tools/05b-render/render.py'])
    
    threading.Thread(target=run_render).start()
    
    self.send_response(200)
    self.send_header('Content-Type', 'application/json')
    self.end_headers()
    self.wfile.write(b'{"status": "rendering_started"}')
```

---

## Implementation Checklist

### Phase 1: Setup
- [x] Create `tools/05a-capstyle/` directory
- [x] Create `tools/05b-render/` directory
- [x] Copy Bangers font to `tools/05b-render/fonts/`
- [x] Add `/api/render` endpoint to `serve.py`

### Phase 2: Caption Styler UI
- [x] Basic HTML structure
- [x] Load project.json and transcript
- [x] Video player integration
- [x] Caption overlay (HTML positioned)
- [x] Word list rendering
- [x] Single-click selection
- [x] Multi-select (Shift, Ctrl)
- [x] Color picker
- [x] Apply color to selection
- [x] Live preview update
- [x] Segment coloring
- [x] Save functionality
- [x] Render button (API call)
- [x] Font loading (Bangers)

### Phase 3: Render Script
- [x] `segments.py` - Playable segment computation
- [x] `captions.py` - Caption extraction
- [x] `ffmpeg_builder.py` - Filter graph generation
- [x] `srt.py` - SRT generation
- [x] `render.py` - CLI entry point

### Phase 4: Integration
- [ ] End-to-end test
- [ ] Error handling
- [ ] Documentation

---

## Dependencies

| Dependency | Purpose | Notes |
|------------|---------|-------|
| ffmpeg | Video rendering | System package |
| Bangers font | Caption font | Copied from ~/.local/share/fonts/ |

---

## Estimated Effort

| Phase | Time |
|-------|------|
| Setup | 15 min |
| Caption Styler | 3-4 hours |
| Render Script | 2-3 hours |
| Integration | 1 hour |
| **Total** | **6-8 hours** |
