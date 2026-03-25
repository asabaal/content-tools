"""
IO functions for loading and saving data files.

Updated to support ProjectConfig for path resolution while maintaining
backward compatibility with direct path arguments.
"""

import json
from pathlib import Path
from typing import Optional, Union

from .models import Transcript, Project
from .project_config import ProjectConfig, get_default_project_path


def load_transcript(path: str | Path, video_id: str | None = None) -> Transcript:
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


def load_project(path: str | Path | None = None) -> Project:
    """Load a project from a JSON file."""
    if path is None:
        path = get_default_project_path()
    else:
        path = Path(path)
    
    if not path.exists():
        return Project()
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return Project.from_dict(data)


def save_project(project: Project, path: str | Path | None = None) -> None:
    """Save a project to a JSON file."""
    if path is None:
        path = get_default_project_path()
    else:
        path = Path(path)
    
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(project.to_dict(), f, indent=2, ensure_ascii=False)


def discover_videos(data_dir: str | Path | None = None,
                    config: ProjectConfig | None = None) -> list[dict]:
    """
    Discover video files in the data/raw directory.
    
    Args:
        data_dir: Direct path to data directory (mutually exclusive with config)
        config: ProjectConfig instance for path resolution
    
    Returns list of dicts with video_id and path.
    """
    if config is not None:
        raw_dir = config.raw_dir
    elif data_dir is not None:
        raw_dir = Path(data_dir) / "raw"
    else:
        raw_dir = get_default_project_path().parent / "raw"
    
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


def discover_transcripts(data_dir: str | Path | None = None,
                         config: ProjectConfig | None = None) -> list[dict]:
    """
    Discover transcript files in the data/transcripts directory.
    
    Args:
        data_dir: Direct path to data directory (mutually exclusive with config)
        config: ProjectConfig instance for path resolution
    
    Returns list of dicts with video_id and path.
    """
    if config is not None:
        transcripts_dir = config.transcripts_dir
    elif data_dir is not None:
        transcripts_dir = Path(data_dir) / "transcripts"
    else:
        transcripts_dir = get_default_project_path().parent / "transcripts"
    
    if not transcripts_dir.exists():
        return []
    
    transcripts = []
    for transcript_path in transcripts_dir.glob("*.json"):
        transcripts.append({
            "video_id": transcript_path.stem,
            "path": str(transcript_path)
        })
    
    return sorted(transcripts, key=lambda t: t["video_id"])


def get_video_path(video_id: str, 
                   data_dir: str | Path | None = None,
                   config: ProjectConfig | None = None) -> Path | None:
    """
    Get the path to a video file by its ID.
    
    Args:
        video_id: Video identifier (filename without extension)
        data_dir: Direct path to data directory (mutually exclusive with config)
        config: ProjectConfig instance for path resolution
    """
    if config is not None:
        raw_dir = config.raw_dir
    elif data_dir is not None:
        raw_dir = Path(data_dir) / "raw"
    else:
        raw_dir = get_default_project_path().parent / "raw"
    
    for ext in [".mp4", ".mkv", ".mov", ".webm"]:
        path = raw_dir / f"{video_id}{ext}"
        if path.exists():
            return path
    
    return None


def get_transcript_path(video_id: str,
                        data_dir: str | Path | None = None,
                        config: ProjectConfig | None = None) -> Path | None:
    """
    Get the path to a transcript file by video ID.
    
    Args:
        video_id: Video identifier
        data_dir: Direct path to data directory (mutually exclusive with config)
        config: ProjectConfig instance for path resolution
    """
    if config is not None:
        transcripts_dir = config.transcripts_dir
    elif data_dir is not None:
        transcripts_dir = Path(data_dir) / "transcripts"
    else:
        transcripts_dir = get_default_project_path().parent / "transcripts"
    
    path = transcripts_dir / f"{video_id}.json"
    
    if path.exists():
        return path
    
    return None
