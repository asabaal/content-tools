# Tool 01: Transcribe

Generate transcripts from video files using Whisper (faster-whisper).

## Requirements

- Python 3.10+
- ffmpeg (for audio extraction)
- faster-whisper (auto-installed)

## Usage

```bash
# Transcribe all videos in data/raw/
python tools/01-transcribe/transcribe.py

# Transcribe specific video
python tools/01-transcribe/transcribe.py data/raw/video.mp4

# Use larger model for better accuracy
python tools/01-transcribe/transcribe.py --model small

# Specify language (faster, more accurate)
python tools/01-transcribe/transcribe.py --lang en

# List available videos
python tools/01-transcribe/transcribe.py --list
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--model, -m` | Whisper model size (tiny/base/small/medium/large) | base |
| `--lang, -l` | Language code (en, es, fr, etc.) | auto-detect |
| `--output, -o` | Output directory | data/transcripts/ |
| `--keep-audio` | Keep temporary audio files | false |
| `--list` | List available videos and exit | - |

## Output Format

Transcripts are saved to `data/transcripts/{video_name}.json`:

```json
{
  "video_id": "20251008_150255",
  "language": "en",
  "duration": 45.2,
  "segments": [
    {
      "id": 0,
      "text": "Hello and welcome to the show.",
      "start": 0.5,
      "end": 3.2,
      "words": [
        {"text": "Hello", "start": 0.5, "end": 0.9},
        {"text": "and", "start": 1.0, "end": 1.2},
        {"text": "welcome", "start": 1.3, "end": 1.8},
        {"text": "to", "start": 1.9, "end": 2.0},
        {"text": "the", "start": 2.1, "end": 2.3},
        {"text": "show.", "start": 2.4, "end": 3.2}
      ]
    }
  ]
}
```

## Model Sizes

| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | ~1GB | Fastest | Good |
| base | ~1GB | Fast | Better |
| small | ~2GB | Medium | Good |
| medium | ~5GB | Slow | Better |
| large | ~10GB | Slowest | Best |

For most use cases, `base` is a good balance. Use `small` or `medium` if you need better accuracy.

## Testing

Run transcription on your raw videos:

```bash
# First, check what videos are available
python tools/01-transcribe/transcribe.py --list

# Then transcribe all
python tools/01-transcribe/transcribe.py

# Or test with just one
python tools/01-transcribe/transcribe.py data/raw/20251008_150255.mp4
```
