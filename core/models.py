"""
Core data models for content-tools.

These models represent the data structures used throughout the pipeline:
- Word: Single word with timing
- Segment: A segment of speech with words
- Transcript: Full transcript for a video
- Clip: A grouping of segment references
- Project: Master state for an editing project
"""

from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class Word:
    text: str
    start: float
    end: float

    def to_dict(self) -> dict:
        return {"text": self.text, "start": self.start, "end": self.end}

    @classmethod
    def from_dict(cls, data: dict) -> "Word":
        return cls(
            text=data["text"],
            start=data["start"],
            end=data["end"]
        )

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class Segment:
    id: str
    text: str
    start: float
    end: float
    words: list[Word] = field(default_factory=list)
    speaker: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "segment_id": self.id,
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "words": [w.to_dict() for w in self.words],
            "speaker": self.speaker
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Segment":
        return cls(
            id=data.get("segment_id", data.get("id", "")),
            text=data["text"],
            start=data["start"],
            end=data["end"],
            words=[Word.from_dict(w) for w in data.get("words", [])],
            speaker=data.get("speaker")
        )

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def word_count(self) -> int:
        return len(self.words)


@dataclass
class Transcript:
    video_id: str
    duration: float
    segments: list[Segment] = field(default_factory=list)
    language: str = "en"

    def to_dict(self) -> dict:
        return {
            "video_id": self.video_id,
            "duration": self.duration,
            "language": self.language,
            "segments": [s.to_dict() for s in self.segments]
        }

    @classmethod
    def from_dict(cls, data: dict, video_id: str = None) -> "Transcript":
        segments = [Segment.from_dict(s) for s in data.get("segments", [])]
        return cls(
            video_id=video_id or data.get("video_id", ""),
            duration=data.get("duration", 0),
            language=data.get("language", "en"),
            segments=segments
        )

    def get_segment(self, segment_id: str) -> Optional[Segment]:
        for seg in self.segments:
            if seg.id == segment_id:
                return seg
        return None


@dataclass
class SegmentRef:
    """Reference to a segment in a specific video."""
    video_id: str
    segment_id: str

    def to_dict(self) -> dict:
        return {"video_id": self.video_id, "segment_id": self.segment_id}

    @classmethod
    def from_dict(cls, data: dict) -> "SegmentRef":
        return cls(video_id=data["video_id"], segment_id=data["segment_id"])


@dataclass
class Clip:
    """A clip groups segments (takes) of the same content from different videos."""
    id: str
    name: str
    segments: list[SegmentRef] = field(default_factory=list)
    selected_segment: Optional[SegmentRef] = None
    include: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "segments": [s.to_dict() for s in self.segments],
            "selected_segment": self.selected_segment.to_dict() if self.selected_segment else None,
            "include": self.include
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Clip":
        segments = [SegmentRef.from_dict(s) for s in data.get("segments", [])]
        selected = None
        if data.get("selected_segment"):
            selected = SegmentRef.from_dict(data["selected_segment"])
        return cls(
            id=data["id"],
            name=data["name"],
            segments=segments,
            selected_segment=selected,
            include=data.get("include", True)
        )


@dataclass
class Video:
    """Reference to a source video file."""
    id: str
    path: str
    transcript_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path": self.path,
            "transcript_path": self.transcript_path
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Video":
        return cls(
            id=data["id"],
            path=data["path"],
            transcript_path=data.get("transcript_path")
        )


@dataclass
class Project:
    """Master state for an editing project."""
    version: int = 1
    videos: list[Video] = field(default_factory=list)
    clips: list[Clip] = field(default_factory=list)
    timeline_order: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "videos": [v.to_dict() for v in self.videos],
            "clips": [c.to_dict() for c in self.clips],
            "timeline_order": self.timeline_order
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        return cls(
            version=data.get("version", 1),
            videos=[Video.from_dict(v) for v in data.get("videos", [])],
            clips=[Clip.from_dict(c) for c in data.get("clips", [])],
            timeline_order=data.get("timeline_order", [])
        )

    def get_clip(self, clip_id: str) -> Optional[Clip]:
        for clip in self.clips:
            if clip.id == clip_id:
                return clip
        return None

    def get_video(self, video_id: str) -> Optional[Video]:
        for video in self.videos:
            if video.id == video_id:
                return video
        return None
