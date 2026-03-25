# Pipeline Trace: How FFmpeg Commands Are Derived

This document traces the data transformation through each stage of the rendering pipeline, showing exactly how the FFmpeg command parameters are computed from project.json to final render commands.

**Created**: 2026-03-09
**Related**: SEGMENT_RENDER_SPEC.md

---

## Stage 0: Raw Data (project.json)

```
CLIP DATA:
  clip_id: clip_mlmz73gu_7
  trim_start: 0
  trim_end: 218.731
  selected_segment.segment_index: 0
  selected_segment.start: 1.620
  selected_segment.end: 6.080
  deleted_regions: 54 regions

TRANSCRIPT SEGMENT [0]:
  text: "Where there was not God's folk, and then there was."
  start: 1.620, end: 6.080
  words: 10 words total
    [0] 'Where'  [1.926, 2.180]
    [1] 'there'  [2.180, 2.400]
    [2] 'was'    [2.400, 2.580]
    [3] 'not'    [2.580, 3.344]
    [4] 'God's'  [3.344, 3.660]
    [5] 'folk,'  [3.660, 5.236]
    [6] 'and'    [5.236, 5.500]
    [7] 'then'   [5.500, 5.660]
    [8] 'there'  [5.660, 5.840]
    [9] 'was.'   [5.840, 6.349]

CAPTION STYLE:
  position: lower_third
  font_size: medium (36px)
  background: dark_box

WORD COLORS:
  0_0 through 0_5: #cb697f (pink)
```

---

## Stage 1: compute_timeline_clips() [render.py:171]

**Purpose**: Filter clips to enabled + in_timeline, sort by timeline_position

**Code Location**: `segments.py:72-95`

**Input**: `project.clips[]` (27 clips total)

**Processing**:
```python
timeline_clips = []
for clip in clips:
    if not clip.get('enabled', True) or not clip.get('in_timeline', True):
        continue  # Skip disabled clips
    
    playable = get_playable_segments(clip)  # Stage 2
    if playable:
        timeline_clips.append({
            'clip': clip,
            'playable_segments': playable,
            'timeline_position': clip.get('timeline_position', 0)
        })

timeline_clips.sort(key=lambda x: x['timeline_position'])
```

**Output**: 
```python
timeline_clips = [
    {
        'clip': {...},  # Full clip data
        'playable_segments': [(1.721, 4.293), (5.327, 6.08), ...],
        'timeline_position': 0
    },
    # ... 26 more clips
]
```

**Transformation**: 27 clips → 27 timeline_clips (sorted)

---

## Stage 2: get_playable_segments() [segments.py:10-69]

**Purpose**: Compute playable regions = (trim range ∩ selected_segment) - deleted regions

**Code Location**: `segments.py:10-69`

**Input**:
```
trim_start: 0
trim_end: 218.731
selected_segment bounds: [1.620, 6.080]
deleted_regions: 54 regions
  [0]: [1.262, 1.721]
  [1]: [4.293, 5.327]
  [2]: [6.453, 8.147]
  ...
```

### Step 2a: Clamping (lines 22-45)

**Purpose**: Ensure trim range doesn't exceed selected_segment bounds

```python
# Line 32
trim_start = max(min(raw_trim_start, sel_end), sel_start)
           = max(min(0, 6.080), 1.620)
           = max(0, 1.620)
           = 1.620

# Line 43
trim_end = min(max(raw_trim_end, sel_start), sel_end)
         = min(max(218.731, 1.620), 6.080)
         = min(218.731, 6.080)
         = 6.080
```

**Result after clamping**: `[1.620, 6.080]`

**⚠️ WARNING**: This clamping discards content outside selected_segment. The user's trim range (0-218s) is reduced to just 4.5 seconds.

### Step 2b: Subtract Deletions (lines 47-67)

**Purpose**: Remove deleted regions from the clamped range

```python
segments = [(1.620, 6.080)]  # Start with clamped range

# Process deletion [1.262, 1.721]
for seg_start, seg_end in segments:  # (1.620, 6.080)
    if del_end <= seg_start or del_start >= seg_end:
        # No overlap
    elif del_start <= seg_start and del_end >= seg_end:
        # Fully deleted
    else:
        # Partial overlap - split
        if del_start > seg_start:  # 1.262 > 1.620? No
            pass
        if del_end < seg_end:  # 1.721 < 6.080? Yes
            new_segments.append((del_end, seg_end))  # (1.721, 6.080)

segments = [(1.721, 6.080)]

# Process deletion [4.293, 5.327]
for seg_start, seg_end in segments:  # (1.721, 6.080)
    # 4.293 > 1.721, so split:
    new_segments.append((1.721, 4.293))  # Before deletion
    new_segments.append((5.327, 6.080))  # After deletion

segments = [(1.721, 4.293), (5.327, 6.080)]
```

**Output**: 
```python
playable_segments = [(1.721, 4.293), (5.327, 6.080)]
```

**Transformation**: 
```
[0, 218.731] + deletions → [(1.721, 4.293), (5.327, 6.080)]
(clamped + subtracted)
```

---

## Stage 3: build_caption_events() [captions.py:60-140]

**Purpose**: Map transcript words to output timeline with colors

**Code Location**: `captions.py:60-140`

**Input**: `timeline_clips[0]` with `playable_segments = [(1.721, 4.293), (5.327, 6.080)]`

### Processing For Playable Segment [1.721, 4.293]

#### Step 3a: Find transcript segment (lines 88-111)

```python
authoritative_segment_index = 0  # From selected_segment.segment_index

# Check if segment[0] overlaps with [1.721, 4.293]
candidate = segments[0]  # range [1.620, 6.080]

if candidate['start'] < 4.293 and candidate['end'] > 1.721:
    # 1.620 < 4.293 and 6.080 > 1.721 → True
    matching_segment = candidate
```

**Result**: Use `segments[0]` as matching segment

#### Step 3b: Get words in range (lines 18-57)

**Code Location**: `captions.py:18-57` (`get_words_in_range()`)

```python
words = matching_segment.get('words', [])
result = []

for idx, word in enumerate(words):
    word_start = word.get('start', 0)
    word_end = word.get('end', 0)
    
    # Overlap check (line 44): word overlaps [1.721, 4.293]?
    if word_start < 4.293 and word_end > 1.721:
        visible_start = max(word_start, 1.721)
        visible_end = min(word_end, 4.293)
        result.append({
            'text': word['text'],
            'start': visible_start,      # Clamped to playable bounds
            'end': visible_end,          # Clamped to playable bounds
            'original_start': word_start,
            'original_end': word_end,
            'word_index': idx
        })
```

**Word-by-word check**:
```
'Where' [1.926, 2.180]: 1.926 < 4.293 and 2.180 > 1.721 → INCLUDE
  visible: [1.926, 2.180] (unchanged)
  
'there' [2.180, 2.400]: 2.180 < 4.293 and 2.400 > 1.721 → INCLUDE
  visible: [2.180, 2.400] (unchanged)
  
'was'   [2.400, 2.580]: 2.400 < 4.293 and 2.580 > 1.721 → INCLUDE
  visible: [2.400, 2.580] (unchanged)
  
'not'   [2.580, 3.344]: 2.580 < 4.293 and 3.344 > 1.721 → INCLUDE
  visible: [2.580, 3.344] (unchanged)
  
'God's' [3.344, 3.660]: 3.344 < 4.293 and 3.660 > 1.721 → INCLUDE
  visible: [3.344, 3.660] (unchanged)
  
'folk,' [3.660, 5.236]: 3.660 < 4.293 and 5.236 > 1.721 → INCLUDE
  visible: [3.660, 4.293] ← TRUNCATED! (5.236 clamped to 4.293)
  
'and'   [5.236, 5.500]: 5.236 < 4.293? No → EXCLUDE
'then'  [5.500, 5.660]: 5.500 < 4.293? No → EXCLUDE
'there' [5.660, 5.840]: 5.660 < 4.293? No → EXCLUDE
'was.'  [5.840, 6.349]: 5.840 < 4.293? No → EXCLUDE
```

**Output**: 6 words included, 4 words excluded

#### Step 3c: Apply word colors (lines 119-125)

```python
word_colors = project.get('word_colors', {})
default_color = '#ffffff'

for word in words:
    key = f"{segment_index}_{word['word_index']}"  # e.g., "0_0"
    word['color'] = word_colors.get(key, default_color)
```

**Color assignment**:
```
'Where' (idx 0): key="0_0" → #cb697f
'there' (idx 1): key="0_1" → #cb697f
'was'   (idx 2): key="0_2" → #cb697f
'not'   (idx 3): key="0_3" → #cb697f
'God's' (idx 4): key="0_4" → #cb697f
'folk,' (idx 5): key="0_5" → #cb697f
```

#### Step 3d: Compute output timeline position (lines 81, 132-138)

```python
output_time = 0.0  # Initialize at start of first clip

for seg_start, seg_end in playable_segments:  # (1.721, 4.293)
    seg_duration = seg_end - seg_start  # 2.572
    
    event = {
        'segment_index': 0,
        'clip_id': 'clip_mlmz73gu_7',
        'original_start': 1.721,      # Source video time
        'original_end': 4.293,        # Source video time
        'output_start': output_time,  # 0.0 (output timeline)
        'output_end': output_time + seg_duration,  # 2.572
        'words': [...],  # 6 words with colors
        'text': "Where there was not God's folk, and then there was."
    }
    
    events.append(event)
    output_time += seg_duration  # Advance to 2.572 for next segment
```

**Output**: `caption_events[0]` for first playable segment

```
Event 0:
  original: [1.721, 4.293]  (source video time)
  output:   [0.000, 2.572]  (output timeline time)
  words: 6 words
```

---

## Stage 4: generate_concat_demuxer_list() [ffmpeg_builder.py:617-649]

**Purpose**: Generate FFmpeg concat demuxer file for Pass 1 assembly

**Code Location**: `ffmpeg_builder.py:617-649`

**Input**: `playable_segments = [(1.721, 4.293), (5.327, 6.080)]`

**Processing** (lines 641-648):
```python
all_segments = []
for item in timeline_clips:
    for start, end in item['playable_segments']:
        all_segments.append((start, end))

# all_segments = [(1.721, 4.293), (5.327, 6.080)]

with open(list_path, 'w') as f:
    for start, end in all_segments:
        f.write(f"file '{input_video}'\n")
        f.write(f"inpoint {start:.6f}\n")
        f.write(f"outpoint {end:.6f}\n")
```

**Output**: `concat_list.txt`
```
file 'data/video_combined.mp4'
inpoint 1.721000
outpoint 4.293000
file 'data/video_combined.mp4'
inpoint 5.327000
outpoint 6.080000
```

**Transformation**: `[(1.721, 4.293), (5.327, 6.08)]` → concat demuxer list

---

## Stage 5: build_pass2_caption_filter() [ffmpeg_builder.py:480-581]

**Purpose**: Build drawtext/drawbox filters for caption overlay

**Code Location**: `ffmpeg_builder.py:480-581`

**Input**: `caption_events[0]` (first event)

### Step 5a: Compute style params (lines 492-495)

```python
font_size = get_font_size('medium')  # 36px
position = 'lower_third'
background = 'dark_box'
default_color = '#ffffff'
```

### Step 5b: Group words into lines (lines 507-522)

```python
max_width = 800
char_width = font_size * 0.5  # 36 * 0.5 = 18px

lines = []
current_line = []
line_width = 0

for word in words_sorted:
    word_width = len(word['text']) * char_width + char_width
    # word_width = 5 * 18 + 18 = 108px for "Where"
    
    if line_width + word_width > max_width and current_line:
        lines.append(current_line)
        current_line = []
        line_width = 0
    
    current_line.append(word)
    line_width += word_width

if current_line:
    lines.append(current_line)
```

**Line grouping**:
```
Word widths:
  'Where': 5*18 + 18 = 108px
  'there': 5*18 + 18 = 108px
  'was':   3*18 + 18 = 72px
  'not':   3*18 + 18 = 72px
  'God's': 5*18 + 18 = 108px
  'folk,': 5*18 + 18 = 108px
  
Cumulative:
  'Where' → 108px
  'there' → 216px
  'was'   → 288px
  'not'   → 360px
  'God's' → 468px
  'folk,' → 576px (all fit in one line, 576 < 800)
```

**Output**: 1 line with 6 words, `total_width = 576px`

### Step 5c: Compute line timing (lines 527-528)

```python
output_start = event['output_start']  # 0.0
original_start = event['original_start']  # 1.721

for line in lines:
    # For each word, compute when it appears in output timeline
    line_start = min(
        output_start + (w['start'] - original_start) 
        for w in line
    )
    line_end = max(
        output_start + (w['end'] - original_start) 
        for w in line
    )
```

**Word timing calculation**:
```
Formula: output_time = 0.0 + (word_visible_start - 1.721)

'Where' [1.926, 2.180]:
  output_start = 0.0 + (1.926 - 1.721) = 0.205
  output_end   = 0.0 + (2.180 - 1.721) = 0.459
  
'there' [2.180, 2.400]:
  output_start = 0.0 + (2.180 - 1.721) = 0.459
  output_end   = 0.0 + (2.400 - 1.721) = 0.679
  
'was' [2.400, 2.580]:
  output_start = 0.0 + (2.400 - 1.721) = 0.679
  output_end   = 0.0 + (2.580 - 1.721) = 0.859
  
'not' [2.580, 3.344]:
  output_start = 0.0 + (2.580 - 1.721) = 0.859
  output_end   = 0.0 + (3.344 - 1.721) = 1.623
  
'God's' [3.344, 3.660]:
  output_start = 0.0 + (3.344 - 1.721) = 1.623
  output_end   = 0.0 + (3.660 - 1.721) = 1.939
  
'folk,' [3.660, 4.293]:  ← Note: visible_end is 4.293 (clamped)
  output_start = 0.0 + (3.660 - 1.721) = 1.939
  output_end   = 0.0 + (4.293 - 1.721) = 2.572
```

**Line timing**:
```
line_start = min(0.205, 0.459, 0.679, 0.859, 1.623, 1.939) = 0.205
line_end   = max(0.459, 0.679, 0.859, 1.623, 1.939, 2.572) = 2.572
```

### Step 5d: Build drawbox filter (lines 534-548)

```python
line_text = ' '.join(w['text'] for w in line)  # "Where there was not God's folk,"
total_width = len(line_text) * char_width
            = 31 * 18 = 558px

box_padding = 8
box_w = int(total_width + box_padding * 2)  # 558 + 16 = 574
box_h = font_size + box_padding * 2         # 36 + 16 = 52

y_base = get_y_position('lower_third', 36)  # "h-116"

box_filter = (
    f"drawbox="
    f"x=(w-{box_w})/2:"           # Center horizontally
    f"y={y_base}-{box_padding}:"  # h-116-8
    f"width={box_w}:"
    f"height={box_h}:"
    f"color=black@0.7:"
    f"t=fill:"
    f"enable='between(t,{line_start:.3f},{line_end:.3f})'"
)
```

**Output**:
```
drawbox=x=(w-574)/2:y=h-116-8:width=574:height=52:color=black@0.7:t=fill:enable='between(t,0.205,2.572)'
```

### Step 5e: Build drawtext filters (lines 550-576)

```python
x_offset = 0

for word in line:
    text = word['text']
    word_output_start = output_start + (word['start'] - original_start)
    
    base_x = f"(w-{total_width:.0f})/2"  # "(w-558)/2"
    if x_offset > 0:
        x_expr = f"{base_x}+{x_offset:.0f}"
    else:
        x_expr = base_x
    
    filter_str = (
        f"drawtext="
        f"text='{text}':"
        f"fontfile={font_path}:"
        f"fontsize={font_size}:"
        f"fontcolor={hex_to_ffmpeg(word['color'])}:"
        f"x={x_expr}:"
        f"y={y_base}:"
        f"enable='between(t,{word_output_start:.3f},{line_end:.3f})'"
    )
    
    x_offset += len(text) * char_width + char_width
```

**Output**: 6 drawtext filters
```
drawtext=text='Where':...:x=(w-558)/2:y=h-116:enable='between(t,0.205,2.572)'
drawtext=text='there':...:x=(w-558)/2+108:y=h-116:enable='between(t,0.459,2.572)'
drawtext=text='was':...:x=(w-558)/2+216:y=h-116:enable='between(t,0.679,2.572)'
drawtext=text='not':...:x=(w-558)/2+288:y=h-116:enable='between(t,0.859,2.572)'
drawtext=text='God\'s':...:x=(w-558)/2+360:y=h-116:enable='between(t,1.623,2.572)'
drawtext=text='folk,':...:x=(w-558)/2+468:y=h-116:enable='between(t,1.939,2.572)'
```

**X-offset calculation**:
```
'Where' → x_offset = 0, then += 5*18+18 = 108
'there' → x_offset = 108, then += 5*18+18 = 216
'was'   → x_offset = 216, then += 3*18+18 = 288
'not'   → x_offset = 288, then += 3*18+18 = 360
'God's' → x_offset = 360, then += 5*18+18 = 468
'folk,' → x_offset = 468
```

---

## Stage 6: Pass 1 Command Assembly [ffmpeg_builder.py:652-669]

**Purpose**: Assemble FFmpeg command for timeline assembly

**Code Location**: `ffmpeg_builder.py:652-669` (`build_concat_demuxer_command()`)

**Input**: `concat_list.txt` from Stage 4

**Code**:
```python
def build_concat_demuxer_command(list_path, output_video, input_video):
    return [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_path,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '128k',
        output_video
    ]
```

**Output**: Pass 1 Command
```bash
ffmpeg -y \
  -f concat \
  -safe 0 \
  -i data/output/concat_list.txt \
  -c:v libx264 -preset fast -crf 18 \
  -c:a aac -b:a 128k \
  data/output/assembled.mp4
```

**What it does**:
- Reads `concat_list.txt`
- Extracts segments from `video_combined.mp4` at specified inpoint/outpoint
- Concatenates them into `assembled.mp4`
- Output duration: 2.572 + 0.753 = 3.325 seconds

---

## Stage 7: Pass 2 Command Assembly [ffmpeg_builder.py:601-614]

**Purpose**: Assemble FFmpeg command for caption overlay

**Code Location**: `ffmpeg_builder.py:601-614` (`build_pass2_command()`)

**Input**: 
- `assembled.mp4` (output of Pass 1)
- Caption filter string from Stage 5

**Code**:
```python
def build_pass2_command(input_video, output_video, filter_script_path):
    return [
        'ffmpeg', '-y',
        '-i', input_video,
        '-filter_complex_script', filter_script_path,
        '-map', '[vout]',
        '-map', '0:a',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'copy',
        output_video
    ]
```

**Filter wrapper** (from `render.py:105`):
```python
pass2_filter = f"[0:v]{caption_filter}[vout]"
# Written to pass2_filter.txt
```

**Output**: Pass 2 Command
```bash
ffmpeg -y \
  -i data/output/assembled.mp4 \
  -filter_complex_script data/output/pass2_filter.txt \
  -map '[vout]' \
  -map 0:a \
  -c:v libx264 -preset medium -crf 23 \
  -c:a copy \
  data/output/final_video.mp4
```

**What it does**:
- Takes `assembled.mp4` as input
- Applies drawbox and drawtext filters from `pass2_filter.txt`
- Maps video output `[vout]` and audio from input
- Outputs to `final_video.mp4`

---

## The Key Formula

For any word in a playable segment:

```
output_time = output_timeline_position + (word_visible_start - segment_original_start)
```

Where:
- `output_timeline_position` = cumulative time from previous segments (0.0 for first segment)
- `word_visible_start` = `max(word.original_start, playable_segment.start)`
- `segment_original_start` = playable segment's start in source video

### Example: "Where"

```
output_timeline_position = 0.0
segment_original_start = 1.721
word_visible_start = max(1.926, 1.721) = 1.926

output_time = 0.0 + (1.926 - 1.721) = 0.205
```

### Example: "folk," (truncated word)

```
output_timeline_position = 0.0
segment_original_start = 1.721
word_visible_start = max(3.660, 1.721) = 3.660
word_visible_end = min(5.236, 4.293) = 4.293  ← Clamped to segment end

output_start = 0.0 + (3.660 - 1.721) = 1.939
output_end = 0.0 + (4.293 - 1.721) = 2.572
```

---

## Why Two Passes Are Required

### Pass 1: Creates the Output Timeline

**Purpose**: Transform source video into assembled timeline

- Concatenates playable segments in sequence
- Each segment gets its position in output time
- Output time starts at 0.000
- Duration = sum of all playable segment durations

**Input**: `video_combined.mp4` (source, with gaps/deletions)

**Output**: `assembled.mp4` (continuous, no gaps)

### Pass 2: Overlays Captions Using Output Timeline

**Purpose**: Add visual captions to assembled video

- Captions are positioned in **output time**, not source time
- `enable='between(t,X,Y)'` refers to output timeline
- Without Pass 1, we wouldn't know X and Y values

**Input**: `assembled.mp4` (from Pass 1)

**Output**: `final_video.mp4` (with captions)

### The Key Insight

Caption timing is **RELATIVE** to the assembled video, not the source video.

The assembly (Pass 1) establishes the output timeline; captions (Pass 2) reference that timeline.

If we tried to do this in one pass, we'd need to:
1. Extract segment
2. Reset timestamps to start at 0
3. Apply captions with adjusted timing
4. Repeat for each segment
5. Concatenate

This is more complex and harder to debug. Two passes separate concerns cleanly.

---

## Data Flow Diagram

```
project.json
    │
    ├── clips[0].trim_start/end ──────────────────┐
    ├── clips[0].deleted_regions ─────────────────┤
    ├── clips[0].selected_segment ────────────────┤
    │                                             ▼
    │                                  STAGE 2: get_playable_segments()
    │                                             │
    │                                             ▼
    │                                  playable_segments: [(1.721, 4.293), (5.327, 6.08)]
    │                                             │
    │                                             ├─────────────────────────────┐
    │                                             │                             │
    │                                             ▼                             ▼
    │                                  STAGE 4: concat list          STAGE 3: caption events
    │                                             │                             │
    │                                             ▼                             │
    │                                  file/inpoint/outpoint                    │
    │                                             │                             │
    │                                             ▼                             │
    │                                  ┌──────────────────┐                      │
    │                                  │  PASS 1 COMMAND  │                      │
    │                                  │  (assembly)      │                      │
    │                                  └────────┬─────────┘                      │
    │                                           │                                │
    │                                           ▼                                │
    │                                  assembled.mp4                             │
    │                                                                          │
    │                                                                          ▼
    │                                                              STAGE 5: caption filter
    │                                                                          │
    │                                                                          ▼
    │                                                              drawbox/drawtext filters
    │                                                                          │
    │                                                                          ▼
    │                                                              ┌──────────────────┐
    │                                                              │  PASS 2 COMMAND  │
    │                                                              │  (captions)      │
    │                                                              └────────┬─────────┘
    │                                                                       │
    │                                                                       ▼
    │                                                              final_video.mp4
```

---

## Summary: Stage Transformations

| Stage | Function | Input | Output | Key Transformation |
|-------|----------|-------|--------|-------------------|
| 0 | Raw data | - | project.json | Source of truth |
| 1 | `compute_timeline_clips()` | clips[] | timeline_clips[] | Filter + sort |
| 2 | `get_playable_segments()` | trim + deletions | [(1.721, 4.293), ...] | Clamp + subtract |
| 3 | `build_caption_events()` | playable + transcript | caption_events[] | Time translation |
| 4 | `generate_concat_demuxer_list()` | playable segments | concat_list.txt | inpoint/outpoint |
| 5 | `build_pass2_caption_filter()` | caption_events | filter string | drawtext params |
| 6 | `build_concat_demuxer_command()` | concat_list | Pass 1 cmd | FFmpeg assembly |
| 7 | `build_pass2_command()` | filter | Pass 2 cmd | FFmpeg overlay |

---

## Command Value Derivations

### Pass 1 Values

| Value | Source | Derivation |
|-------|--------|------------|
| `inpoint 1.721` | `playable_segments[0][0]` | After deletion [1.262, 1.721] |
| `outpoint 4.293` | `playable_segments[0][1]` | Before deletion [4.293, 5.327] |

### Pass 2 Values

| Value | Source | Derivation |
|-------|--------|------------|
| `t=0.205` (Where) | `0.0 + (1.926 - 1.721)` | word_start - segment_start |
| `t=0.459` (there) | `0.0 + (2.180 - 1.721)` | word_start - segment_start |
| `t=0.679` (was) | `0.0 + (2.400 - 1.721)` | word_start - segment_start |
| `t=0.859` (not) | `0.0 + (2.580 - 1.721)` | word_start - segment_start |
| `t=1.623` (God's) | `0.0 + (3.344 - 1.721)` | word_start - segment_start |
| `t=1.939` (folk,) | `0.0 + (3.660 - 1.721)` | word_start - segment_start |
| `t=2.572` (all end) | `0.0 + (4.293 - 1.721)` | segment_end - segment_start |

---

## Conclusion

This pipeline trace shows the exact derivation of every value in the FFmpeg commands. The key insight is that:

1. **Playable segments** are computed from (trim ∩ selected_segment) - deletions
2. **Output timeline** is a 0-based timeline where segments are concatenated
3. **Caption timing** = output_timeline_position + (word_time - segment_start)
4. **Two passes** separate assembly from overlay for cleaner logic

Any bug in the render must trace back to one of these stages.
