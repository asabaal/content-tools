"""Song package manifest with provenance for every artifact."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .detectors import sha256_file


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_entry(path: Path, role: str) -> dict[str, Any]:
    path = Path(path)
    entry: dict[str, Any] = {"path": str(path), "role": role}
    if path.is_file():
        entry.update({"bytes": path.stat().st_size,
                      "sha256": sha256_file(path)})
    return entry


def build_manifest(project_dir: Path, *, source: dict, analysis: dict,
                   derived: dict, tool_versions: dict) -> dict[str, Any]:
    return {
        "schema": "content-tools/song-analysis-package",
        "schema_version": "0.1",
        "generated_at": now_iso(),
        "project_dir": str(project_dir),
        "generator": {"tool": "tools/06-song-ingest",
                      "package_version": __version__,
                      "components": tool_versions},
        "source": source,
        "analysis": analysis,
        "derived": derived,
        "provenance_rules": [
            "reference MIDI files are external reference artifacts, not ground truth",
            "raw model outputs are preserved; reconciliation is stored separately",
            "derived artifacts can be regenerated when models improve",
        ],
    }


def write_json(path: Path, obj) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n")
    return path
