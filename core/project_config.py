"""
Project configuration and path resolution.

Provides a unified interface for project settings, paths, and v1→v2 migration.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
import json
from datetime import datetime
import shutil


DEFAULT_PATHS = {
    "raw": "raw",
    "transcripts": "transcripts",
    "combined_video": "video_combined.mp4",
    "combined_transcript": "transcript_combined.json",
    "waveforms": "waveforms.json",
    "output": "output"
}


@dataclass
class ProjectConfig:
    """Project configuration with path resolution and migration support."""
    
    path: Path
    data_dir: Path
    name: str = "Untitled Project"
    season: Optional[int] = None
    episode: Optional[int] = None
    description: str = ""
    schema_version: str = "2.0"
    paths: dict = field(default_factory=lambda: DEFAULT_PATHS.copy())
    _raw_data: dict = field(default_factory=dict, repr=False)
    created: Optional[str] = None
    modified: Optional[str] = None
    
    @property
    def raw_dir(self) -> Path:
        return self.data_dir / self.paths["raw"]
    
    @property
    def transcripts_dir(self) -> Path:
        return self.data_dir / self.paths["transcripts"]
    
    @property
    def combined_video(self) -> Path:
        return self.data_dir / self.paths["combined_video"]
    
    @property
    def combined_transcript(self) -> Path:
        return self.data_dir / self.paths["combined_transcript"]
    
    @property
    def waveforms(self) -> Path:
        return self.data_dir / self.paths["waveforms"]
    
    @property
    def output_dir(self) -> Path:
        return self.data_dir / self.paths["output"]
    
    def resolve_path(self, key: str) -> Path:
        """Resolve a path key to absolute path."""
        if key not in self.paths:
            raise KeyError(f"Unknown path key: {key}")
        return self.data_dir / self.paths[key]
    
    def to_dict(self) -> dict:
        """Convert to full project.json format."""
        result = {
            "schema_version": self.schema_version,
            "project": {
                "name": self.name,
                "created": self.created,
                "modified": self.modified
            },
            "paths": self.paths
        }
        
        if self.season is not None:
            result["project"]["season"] = self.season
        if self.episode is not None:
            result["project"]["episode"] = self.episode
        if self.description:
            result["project"]["description"] = self.description
        
        for key in ["videos", "clips", "timeline_order", "caption_style", 
                    "word_colors", "caption_breaks"]:
            if key in self._raw_data:
                result[key] = self._raw_data[key]
        
        return result
    
    def to_api_dict(self) -> dict:
        """Return resolved paths for /api/config response (HTML tools)."""
        return {
            "project": {
                "name": self.name,
                "season": self.season,
                "episode": self.episode,
                "description": self.description
            },
            "paths": {
                "combined_video": f"/data/{self.paths['combined_video']}",
                "combined_transcript": f"/data/{self.paths['combined_transcript']}",
                "output_dir": "/data/output",
                "raw_dir": f"/data/{self.paths['raw']}",
                "transcripts_dir": f"/data/{self.paths['transcripts']}"
            }
        }
    
    def save(self) -> None:
        """Save project.json."""
        self.modified = datetime.now().isoformat()[:10]
        data = self.to_dict()
        self._raw_data = data.copy()
        
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, path: Path | str) -> "ProjectConfig":
        """Load project.json, auto-migrating v1 → v2 if needed."""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Project file not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        schema_version = data.get("schema_version", "1.0")
        
        if schema_version == "1.0":
            data = cls.migrate_v1_to_v2(data, path)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Migrated {path} v1 → v2")
        
        return cls.from_dict(data, path)
    
    @classmethod
    def from_dict(cls, data: dict, path: Path) -> "ProjectConfig":
        """Create ProjectConfig from v2 schema dict."""
        project = data.get("project", {})
        paths = {**DEFAULT_PATHS, **data.get("paths", {})}
        
        instance = cls(
            path=path,
            data_dir=path.parent,
            name=project.get("name", "Untitled Project"),
            season=project.get("season"),
            episode=project.get("episode"),
            description=project.get("description", ""),
            schema_version=data.get("schema_version", "2.0"),
            paths=paths,
            created=project.get("created"),
            modified=project.get("modified"),
            _raw_data=data.copy()
        )
        
        return instance
    
    @classmethod
    def migrate_v1_to_v2(cls, data: dict, path: Path) -> dict:
        """Add schema_version, project metadata, paths to v1 data."""
        now = datetime.now().isoformat()[:10]
        dir_name = path.parent.name
        
        migrated = {
            "schema_version": "2.0",
            "project": {
                "name": dir_name.replace("-", " ").replace("_", " ").title(),
                "created": now,
                "modified": now
            },
            "paths": DEFAULT_PATHS.copy()
        }
        
        for key in ["videos", "clips", "timeline_order", "caption_style",
                    "word_colors", "caption_breaks", "version"]:
            if key in data:
                migrated[key] = data[key]
        
        return migrated
    
    @classmethod
    def create(cls, data_dir: Path | str, name: str, 
               season: Optional[int] = None,
               episode: Optional[int] = None,
               description: str = "") -> "ProjectConfig":
        """Create new project with directory structure."""
        data_dir = Path(data_dir)
        path = data_dir / "project.json"
        
        if path.exists():
            raise FileExistsError(f"Project already exists: {path}")
        
        now = datetime.now().isoformat()[:10]
        
        instance = cls(
            path=path,
            data_dir=data_dir,
            name=name,
            season=season,
            episode=episode,
            description=description,
            created=now,
            modified=now,
            _raw_data={}
        )
        
        for subdir in ["raw", "transcripts", "output"]:
            (data_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        instance.save()
        
        return instance


def get_default_project_path() -> Path:
    """Get default project.json path (data/project.json)."""
    return Path(__file__).parent.parent / "data" / "project.json"
