"""
IO functions for loading and saving data files.
"""

import json
from pathlib import Path
from typing import Optional

from .models import Transcript, Project


DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"


def load_transcript(path: str | Path, video_id: str = None) -> Transcript:
    """Load a transcript from a JSON file."""
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Transcript not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if video_id is None:
        video_id = path.stem
    
    return Transcript.from_dict(data, video_id)


def save_transcript(transcript: Transcript, path: str | Path) -> None:
    """Save a transcript to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(transcript.to_dict(), f, indent=2, ensure_ascii=False)


def load_project(path: str | Path = None) -> Project:
    """Load a project from a JSON file."""
    if path is None:
        path = DEFAULT_DATA_DIR / "project.json"
    else:
        path = Path(path)
    
    if not path.exists():
        return Project()
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return Project.from_dict(data)


def save_project(project: Project, path: str | Path = None) -> None:
    """Save a project to a JSON file."""
    if path is None:
        path = DEFAULT_DATA_DIR / "project.json"
    else:
        path = Path(path)
    
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(project.to_dict(), f, indent=2, ensure_ascii=False)


def discover_videos(data_dir: str | Path = None) -> list[dict]:
    """
    Discover video files in the data/raw directory.
    Returns list of dicts with video_id and path.
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    
    raw_dir = Path(data_dir) / "raw"
    
    if not raw_dir.exists():
        return []
    
    videos = []
    for ext in ["*.mp4", "*.mkv", "*.mov", "*.webm"]:
        for video_path in raw_dir.glob(ext):
            videos.append({
                "video_id": video_path.stem,
                "path": str(video_path)
            })
    
    return sorted(videos, key=lambda v: v["video_id"])


def discover_transcripts(data_dir: str | Path = None) -> list[dict]:
    """
    Discover transcript files in the data/transcripts directory.
    Returns list of dicts with video_id and path.
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    
    transcripts_dir = Path(data_dir) / "transcripts"
    
    if not transcripts_dir.exists():
        return []
    
    transcripts = []
    for transcript_path in transcripts_dir.glob("*.json"):
        transcripts.append({
            "video_id": transcript_path.stem,
            "path": str(transcript_path)
        })
    
    return sorted(transcripts, key=lambda t: t["video_id"])


def get_video_path(video_id: str, data_dir: str | Path = None) -> Optional[Path]:
    """Get the path to a video file by its ID."""
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    
    raw_dir = Path(data_dir) / "raw"
    
    for ext in [".mp4", ".mkv", ".mov", ".webm"]:
        path = raw_dir / f"{video_id}{ext}"
        if path.exists():
            return path
    
    return None


def get_transcript_path(video_id: str, data_dir: str | Path = None) -> Optional[Path]:
    """Get the path to a transcript file by video ID."""
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    
    transcripts_dir = Path(data_dir) / "transcripts"
    path = transcripts_dir / f"{video_id}.json"
    
    if path.exists():
        return path
    
    return None
