# Tool 03: Select Takes

Choose the best take for each clip.

## Purpose

After grouping segments into clips in Tool 02 (Review & Assign), use this tool to select which specific take/version to use for each clip.

## How to Run

```bash
cd /mnt/storage/repos/content-tools
python serve.py
```

Then open: http://localhost:8000/tools/03-select/

## Prerequisites

You must have:
- `data/project.json` - Created by Tool 02 (Review & Assign)
- `data/video_combined.mp4` - Combined video file

## Features

### Clips Panel (Left)
- **Multi-take clips** - Clips with multiple takes appear first, highlighted in blue
- **Single-take clips** - Shown below; auto-selected since there's only one take
- **Selection indicator** - Green checkmark shows which clips have a selected take

### Video Grid (Center)
- **Side-by-side comparison** - All takes for the selected clip shown as video cards
- **Individual playback** - Each video has its own controls
- **Play All** - Start all videos simultaneously for comparison
- **Select button** - Click to mark that take as the selected one

### Transcripts Panel (Right)
- **Text comparison** - See transcript text for each take side-by-side
- **Click to select** - Click transcript to select that take

## Workflow

1. **Review clips list** - Multi-take clips appear first (need your decision)
2. **Click a clip** - Video grid shows all takes for comparison
3. **Play and compare** - Watch each take, read transcripts
4. **Select best take** - Click "Select" on the best version
5. **Save** - Click Save to persist your selections

## Output

Updates `project.json` with `selected_segment` for each clip:

```json
{
  "clips": [
    {
      "id": "clip_1",
      "name": "intro",
      "segments": [...],
      "selected_segment": {
        "segment_index": 5,
        "original_video_id": "20251008_150325",
        "start": 39.47,
        "end": 41.07,
        "text": "While a wind of God,"
      }
    }
  ]
}
```

## Next Step

After selecting takes, use Tool 04 (Assemble) to order clips into a final timeline.
