"""
Content Tools Core Library

Provides data models and IO functions for the video editing pipeline.
"""

from .models import Word, Segment, Transcript, SegmentRef, Clip, Video, Project
from .io import (
    load_transcript,
    save_transcript,
    load_project,
    save_project,
    discover_videos,
    discover_transcripts,
    get_video_path,
    get_transcript_path,
)
from .utils import format_time, parse_time, word_count, truncate_text

__all__ = [
    "Word",
    "Segment",
    "Transcript",
    "SegmentRef",
    "Clip",
    "Video",
    "Project",
    "load_transcript",
    "save_transcript",
    "load_project",
    "save_project",
    "discover_videos",
    "discover_transcripts",
    "get_video_path",
    "get_transcript_path",
    "format_time",
    "parse_time",
    "word_count",
    "truncate_text",
]
