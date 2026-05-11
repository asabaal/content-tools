from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional


SUPPORTED_AUDIO = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}
SUPPORTED_LYRICS = {".srt", ".lrc", ".txt"}
SUPPORTED_MIDI = {".mid", ".midi"}


class InputTier(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    FULL = "full"


@dataclass
class StemInfo:
    name: str
    stem_type: str
    path: str
    format: str = "wav"

    def to_dict(self) -> dict:
        return {"name": self.name, "stem_type": self.stem_type, "path": self.path, "format": self.format}


@dataclass
class MidiFileInfo:
    name: str
    path: str
    instrument: str = ""
    note_count: int = 0
    duration: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "instrument": self.instrument,
            "note_count": self.note_count,
            "duration": self.duration,
        }


@dataclass
class IngestResult:
    tier: str = "basic"
    audio_path: Optional[str] = None
    lyrics_path: Optional[str] = None
    stems: list = field(default_factory=list)
    midi_files: list = field(default_factory=list)
    has_tempo_locked_stems: bool = False

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "audio_path": self.audio_path,
            "lyrics_path": self.lyrics_path,
            "stems": [s.to_dict() if hasattr(s, "to_dict") else s for s in self.stems],
            "midi_files": [m.to_dict() if hasattr(m, "to_dict") else m for m in self.midi_files],
            "has_tempo_locked_stems": self.has_tempo_locked_stems,
        }


@dataclass
class ProjectPaths:
    audio: Optional[str] = None
    lyrics: Optional[str] = None
    data_dir: Optional[str] = None

    def resolve_audio(self, base_dir: Path) -> Optional[Path]:
        if self.audio is None:
            return None
        p = base_dir / self.audio
        return p if p.exists() else None

    def resolve_lyrics(self, base_dir: Path) -> Optional[Path]:
        if self.lyrics is None:
            return None
        p = base_dir / self.lyrics
        return p if p.exists() else None


@dataclass
class AudioInfo:
    duration: float = 0.0
    bpm: float = 0.0
    sample_rate: int = 0
    beat_count: int = 0
    onset_count: int = 0
    midi_bpm: Optional[float] = None


@dataclass
class LyricsInfo:
    total_lines: int = 0
    total_words: int = 0
    format: str = ""
    first_line_time: Optional[float] = None
    last_line_time: Optional[float] = None
    has_sections: bool = False
    section_count: int = 0


STAGE_ORDER = ["ingest", "analyze", "sync", "structure", "design", "render"]


@dataclass
class StageStatus:
    ingest: str = "pending"
    analyze: str = "pending"
    sync: str = "pending"
    structure: str = "pending"
    design: str = "pending"
    render: str = "pending"

    def mark_complete(self, stage: str) -> None:
        if hasattr(self, stage):
            setattr(self, stage, "complete")

    def is_complete(self, stage: str) -> bool:
        return getattr(self, stage, "pending") == "complete"

    def next_pending(self) -> Optional[str]:
        for s in STAGE_ORDER:
            if getattr(self, s, "pending") != "complete":
                return s
        return None


@dataclass
class MusicVideoProject:
    schema_version: str = "1.0"
    name: str = ""
    artist: str = ""
    created: Optional[str] = None
    modified: Optional[str] = None
    paths: ProjectPaths = field(default_factory=ProjectPaths)
    input_tier: str = "basic"
    audio_info: AudioInfo = field(default_factory=AudioInfo)
    lyrics_info: LyricsInfo = field(default_factory=LyricsInfo)
    stages: StageStatus = field(default_factory=StageStatus)
    _project_dir: Optional[Path] = field(default=None, repr=False)

    @property
    def project_dir(self) -> Path:
        if self._project_dir is None:
            raise ValueError("Project directory not set")
        return self._project_dir

    @project_dir.setter
    def project_dir(self, value: Path) -> None:
        self._project_dir = value

    @property
    def data_dir(self) -> Path:
        return self.project_dir / "data"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def assets_dir(self) -> Path:
        return self.data_dir / "assets"

    @property
    def output_dir(self) -> Path:
        return self.data_dir / "output"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def project_file(self) -> Path:
        return self.data_dir / "mvp_project.json"

    @property
    def ingest_file(self) -> Path:
        return self.data_dir / "ingest.json"

    @property
    def analysis_file(self) -> Path:
        return self.data_dir / "analysis.json"

    @property
    def waveforms_file(self) -> Path:
        return self.data_dir / "waveforms.json"

    @property
    def lyrics_raw_file(self) -> Path:
        return self.data_dir / "lyrics_raw.json"

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def save(self) -> None:
        self.modified = self._now()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "schema_version": self.schema_version,
            "name": self.name,
            "artist": self.artist,
            "created": self.created,
            "modified": self.modified,
            "paths": asdict(self.paths),
            "input_tier": self.input_tier,
            "audio_info": asdict(self.audio_info),
            "lyrics_info": asdict(self.lyrics_info),
            "stages": asdict(self.stages),
        }
        self.project_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, project_dir: Path) -> "MusicVideoProject":
        project_file = project_dir / "data" / "mvp_project.json"
        if not project_file.exists():
            raise FileNotFoundError(f"No project found at {project_dir}")
        data = json.loads(project_file.read_text(encoding="utf-8"))
        proj = cls(
            schema_version=data.get("schema_version", "1.0"),
            name=data.get("name", ""),
            artist=data.get("artist", ""),
            created=data.get("created"),
            modified=data.get("modified"),
            paths=ProjectPaths(**data.get("paths", {})),
            input_tier=data.get("input_tier", "basic"),
            audio_info=AudioInfo(**data.get("audio_info", {})),
            lyrics_info=LyricsInfo(**data.get("lyrics_info", {})),
            stages=StageStatus(**data.get("stages", {})),
        )
        proj._project_dir = project_dir.resolve()
        return proj

    @classmethod
    def create(
        cls,
        project_dir: Path,
        name: str,
        artist: str = "",
        audio_path: Optional[Path] = None,
        lyrics_path: Optional[Path] = None,
        data_dir: Optional[Path] = None,
    ) -> "MusicVideoProject":
        now = cls._now()
        proj = cls(
            name=name,
            artist=artist,
            created=now,
            modified=now,
        )
        proj._project_dir = project_dir.resolve()

        for d in [proj.data_dir, proj.raw_dir, proj.assets_dir, proj.output_dir, proj.cache_dir]:
            d.mkdir(parents=True, exist_ok=True)

        if data_dir is not None:
            proj.paths.data_dir = str(data_dir.resolve())
        elif audio_path is not None:
            dest = proj.raw_dir / audio_path.name
            if not dest.exists():
                dest.write_bytes(audio_path.read_bytes())
            proj.paths.audio = f"raw/{audio_path.name}"

        if lyrics_path is not None:
            dest = proj.raw_dir / lyrics_path.name
            if not dest.exists():
                dest.write_bytes(lyrics_path.read_bytes())
            proj.paths.lyrics = f"raw/{lyrics_path.name}"

        proj.stages.mark_complete("ingest")
        proj.save()
        return proj


CORE_SECTION_TYPES = [
    "verse", "chorus", "bridge", "intro", "outro",
    "pre_chorus", "hook", "interlude", "instrumental",
]


@dataclass
class SectionVisual:
    background_type: str = "solid"
    background_color: str = "#1a1a2e"
    gradient_colors: Optional[List[str]] = None
    gradient_direction: str = "vertical_top_bottom"
    texture_type: str = "none"
    texture_opacity: float = 0.15
    text_color: Optional[str] = None
    text_auto_contrast: bool = True
    font_size: int = 48
    animation_type: str = "fade"
    animation_speed: float = 1.0
    reactivity: List[str] = field(default_factory=lambda: ["vocals"])

    def to_dict(self) -> dict:
        d = {
            "background_type": self.background_type,
            "background_color": self.background_color,
            "gradient_direction": self.gradient_direction,
            "texture_type": self.texture_type,
            "texture_opacity": self.texture_opacity,
            "text_auto_contrast": self.text_auto_contrast,
            "font_size": self.font_size,
            "animation_type": self.animation_type,
            "animation_speed": self.animation_speed,
            "reactivity": self.reactivity,
        }
        if self.gradient_colors is not None:
            d["gradient_colors"] = self.gradient_colors
        if self.text_color is not None:
            d["text_color"] = self.text_color
        return d

    @classmethod
    def from_dict(cls, d: dict) -> SectionVisual:
        return cls(
            background_type=d.get("background_type", "solid"),
            background_color=d.get("background_color", "#1a1a2e"),
            gradient_colors=d.get("gradient_colors"),
            gradient_direction=d.get("gradient_direction", "vertical_top_bottom"),
            texture_type=d.get("texture_type", "none"),
            texture_opacity=d.get("texture_opacity", 0.15),
            text_color=d.get("text_color"),
            text_auto_contrast=d.get("text_auto_contrast", True),
            font_size=d.get("font_size", 48),
            animation_type=d.get("animation_type", "fade"),
            animation_speed=d.get("animation_speed", 1.0),
            reactivity=d.get("reactivity", ["vocals"]),
        )


@dataclass
class StructureSection:
    id: str
    type: str
    name: str
    start_line: int
    end_line: int
    custom_type: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    visual: SectionVisual = field(default_factory=SectionVisual)

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "tags": self.tags,
            "visual": self.visual.to_dict(),
        }
        if self.custom_type is not None:
            d["custom_type"] = self.custom_type
        return d

    @classmethod
    def from_dict(cls, d: dict) -> StructureSection:
        visual = SectionVisual.from_dict(d.get("visual", {}))
        return cls(
            id=d["id"],
            type=d["type"],
            name=d["name"],
            start_line=d["start_line"],
            end_line=d["end_line"],
            custom_type=d.get("custom_type"),
            tags=d.get("tags", []),
            visual=visual,
        )
