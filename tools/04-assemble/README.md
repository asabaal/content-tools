# Tool 04: Assemble Timeline

Order selected clips into final timeline, trim boundaries, and export.

## Usage

1. **Generate waveforms** (first time only):
   ```bash
   python tools/04-assemble/generate_waveforms.py
   ```

2. **Start server:**
   ```bash
   python serve.py
   ```

3. **Open tool:**
   ```
   http://localhost:8000/tools/04-assemble/
   ```

## Features

- **Clip Pool** (left sidebar) - Clips not in timeline, click [+] to add
- **Timeline** - Drag clips to reorder, click × to remove
- **Video Preview** - Preview selected clip
- **Waveform** - Visual audio display with trim handles
- **Trim Start/End** - Drag handles to adjust clip boundaries
- **Split Clip** - Split at current playhead position
- **Toggle On/Off** - Enable/disable clips in final output
- **Preview All** - Play all enabled clips sequentially
- **Export EDL** - Generate EDL file for video editors
- **Save** - Save project state

## Data Model

Clips in `project.json` gain these fields:

```json
{
  "in_timeline": true,
  "timeline_position": 0,
  "trim_start": null,
  "trim_end": null,
  "enabled": true,
  "split_parent_id": null
}
```

## Output

- `data/project.json` - Updated with timeline state
- `data/assembly.edl` - EDL export for kdenlive/blender
