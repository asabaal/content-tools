# Tool 02: Review

Watch video with synced transcript (read-only).

## Features

- Video player with custom controls
- Transcript sidebar with segment highlighting
- **Video source markers** showing where each source video begins
- Click segment → video jumps to timestamp
- Play video → current segment auto-highlights and scrolls into view
- Keyboard shortcuts: Space (play/pause), Arrow keys (skip ±5s)

## How to Run

You must serve the files over HTTP (required for JSON/video loading).

```bash
cd /mnt/storage/repos/content-tools
python serve.py
```

Then open: http://localhost:8000/tools/02-review/

## Data Files

This tool uses the combined output from the transcribe tool:
- Video: `data/video_combined.mp4`
- Transcript: `data/transcript_combined.json`

The transcript includes source markers showing where each original video begins in the combined timeline.

## Usage

1. Video plays in the left panel
2. Transcript appears on the right with source video markers (blue headers)
3. Click any segment to jump to that point in the video
4. As video plays, the current segment highlights automatically
5. The transcript scrolls to keep the active segment visible

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| Left Arrow | Skip back 5s |
| Right Arrow | Skip forward 5s |

## Next Steps

This is the foundation for:
- Tool 03: Assign (add segment grouping)
- Tool 04: Select (add take comparison)
- Tool 05: Assemble (add timeline editing)
