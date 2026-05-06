from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


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
