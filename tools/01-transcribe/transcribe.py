"""
Transcription Tool - Generate transcripts from video files using Whisper.

Usage:
    python transcribe.py [options] [video_files...]

Examples:
    python transcribe.py                          # Process all videos, auto-combine
    python transcribe.py video1.mp4               # Process specific video
    python transcribe.py --no-combine             # Don't combine after transcription
    python transcribe.py --combined-name episode_3  # Name combined output
    python transcribe.py --model large --lang en  # Use larger model

Output:
    Individual transcripts: data/transcripts/{video_name}.json
    Combined transcript: data/transcript_combined.json
    Combined video: data/video_combined.mp4
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.models import Transcript, Segment, Word

DATA_DIR = Path(__file__).parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"


def extract_audio(video_path: Path, audio_path: Path) -> bool:
    """Extract audio from video file using ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(audio_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def transcribe_audio(
    audio_path: Path,
    model_size: str = "base",
    language: Optional[str] = None
) -> dict:
    """Transcribe audio using faster-whisper."""
    from faster_whisper import WhisperModel
    
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    segments, info = model.transcribe(
        str(audio_path),
        language=language,
        word_timestamps=True
    )
    
    result_segments = []
    for seg in segments:
        words = []
        if seg.words:
            for w in seg.words:
                words.append({
                    "text": w.word.strip(),
                    "start": w.start,
                    "end": w.end
                })
        
        result_segments.append({
            "id": seg.id,
            "text": seg.text.strip(),
            "start": seg.start,
            "end": seg.end,
            "words": words
        })
    
    return {
        "language": info.language,
        "duration": info.duration,
        "segments": result_segments
    }


def process_video(
    video_path: Path,
    output_dir: Path,
    model_size: str = "base",
    language: Optional[str] = None,
    keep_audio: bool = False
) -> Optional[dict]:
    """Process a single video file. Returns transcript data dict."""
    video_id = video_path.stem
    print(f"\nProcessing: {video_id}")
    print(f"  Video: {video_path}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = Path(tmp.name)
    
    print(f"  Extracting audio...")
    if not extract_audio(video_path, audio_path):
        print(f"  ERROR: Failed to extract audio")
        return None
    
    try:
        print(f"  Transcribing (model={model_size})...")
        result = transcribe_audio(audio_path, model_size, language)
        
        transcript_data = {
            "video_id": video_id,
            "language": result["language"],
            "duration": result["duration"],
            "segments": result["segments"]
        }
        
        output_path = output_dir / f"{video_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        print(f"  Saved: {output_path}")
        print(f"  Segments: {len(result['segments'])}")
        print(f"  Duration: {result['duration']:.1f}s")
        
        return transcript_data
    
    finally:
        if not keep_audio and audio_path.exists():
            audio_path.unlink()


def combine_videos(
    video_paths: list[Path],
    output_path: Path
) -> bool:
    """Concatenate videos using ffmpeg."""
    print(f"\nCombining {len(video_paths)} videos...")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for vp in video_paths:
            f.write(f"file '{vp.absolute()}'\n")
        concat_list = Path(f.name)
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"  Saved: {output_path} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"  ERROR: {result.stderr}")
            return False
    finally:
        concat_list.unlink()


def combine_transcripts(
    transcripts: list[dict],
    video_paths: list[Path],
    output_path: Path
) -> bool:
    """Combine multiple transcripts with time offsets."""
    print(f"\nCombining {len(transcripts)} transcripts...")
    
    combined_segments = []
    sources = []
    current_offset = 0.0
    segment_counter = 0
    
    for transcript, video_path in zip(transcripts, video_paths):
        video_id = transcript["video_id"]
        duration = transcript["duration"]
        
        sources.append({
            "video_id": video_id,
            "start": current_offset,
            "end": current_offset + duration,
            "duration": duration
        })
        
        for seg in transcript["segments"]:
            adjusted_segment = {
                "id": segment_counter,
                "original_id": seg["id"],
                "original_video_id": video_id,
                "text": seg["text"],
                "start": seg["start"] + current_offset,
                "end": seg["end"] + current_offset,
                "words": [
                    {
                        "text": w["text"],
                        "start": w["start"] + current_offset,
                        "end": w["end"] + current_offset
                    }
                    for w in seg.get("words", [])
                ]
            }
            combined_segments.append(adjusted_segment)
            segment_counter += 1
        
        current_offset += duration
    
    combined = {
        "video_id": "combined",
        "language": transcripts[0].get("language", "en") if transcripts else "en",
        "duration": current_offset,
        "sources": sources,
        "segments": combined_segments
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    
    print(f"  Saved: {output_path}")
    print(f"  Total segments: {len(combined_segments)}")
    print(f"  Total duration: {current_offset:.1f}s")
    
    return True


def discover_videos(raw_dir: Path) -> list[Path]:
    """Find all video files in the raw directory."""
    videos = []
    for ext in ["*.mp4", "*.mkv", "*.mov", "*.webm", "*.avi"]:
        videos.extend(raw_dir.glob(ext))
    return sorted(videos)


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe video files using Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "videos",
        nargs="*",
        help="Video files to transcribe (default: all in data/raw/)"
    )
    parser.add_argument(
        "--model", "-m",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)"
    )
    parser.add_argument(
        "--lang", "-l",
        default=None,
        help="Language code (e.g., 'en'). Auto-detected if not specified."
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory for individual transcripts (default: data/transcripts/)"
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="Keep temporary audio files"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available videos and exit"
    )
    parser.add_argument(
        "--no-combine",
        action="store_true",
        help="Don't combine videos and transcripts after transcription"
    )
    parser.add_argument(
        "--combined-name",
        default="combined",
        help="Base name for combined output files (default: combined)"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output) if args.output else TRANSCRIPTS_DIR
    
    if args.list:
        videos = discover_videos(RAW_DIR)
        print(f"Videos in {RAW_DIR}:")
        for v in videos:
            size_mb = v.stat().st_size / (1024 * 1024)
            print(f"  {v.name} ({size_mb:.1f} MB)")
        print(f"\nTotal: {len(videos)} videos")
        return
    
    if args.videos:
        videos = [Path(v) for v in args.videos]
    else:
        videos = discover_videos(RAW_DIR)
    
    if not videos:
        print(f"No videos found in {RAW_DIR}")
        print("Add video files to data/raw/ or specify files on the command line")
        sys.exit(1)
    
    print(f"Found {len(videos)} video(s) to process")
    print(f"Model: {args.model}")
    print(f"Output: {output_dir}")
    print(f"Combine: {'No' if args.no_combine else 'Yes'}")
    
    transcripts = []
    success_count = 0
    
    for video_path in videos:
        if not video_path.exists():
            print(f"\nSkipping: {video_path} (not found)")
            continue
        
        result = process_video(
            video_path,
            output_dir,
            model_size=args.model,
            language=args.lang,
            keep_audio=args.keep_audio
        )
        
        if result:
            transcripts.append(result)
            success_count += 1
    
    print(f"\n{'='*50}")
    print(f"Transcription complete: {success_count}/{len(videos)} videos")
    
    if success_count < len(videos):
        sys.exit(1)
    
    if not args.no_combine and len(transcripts) > 1:
        print(f"\n{'='*50}")
        print("Combining...")
        
        combined_video_path = DATA_DIR / f"video_{args.combined_name}.mp4"
        combined_transcript_path = DATA_DIR / f"transcript_{args.combined_name}.json"
        
        video_ok = combine_videos(videos, combined_video_path)
        transcript_ok = combine_transcripts(transcripts, videos, combined_transcript_path)
        
        if video_ok and transcript_ok:
            print(f"\n{'='*50}")
            print(f"Combine complete!")
            print(f"  Video: {combined_video_path}")
            print(f"  Transcript: {combined_transcript_path}")
        else:
            print("\nCombine failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()
