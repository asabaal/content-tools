"""Suno Advanced Split target ontology loader.

The ontology lives in the Suno Stem Target Recommender (music_creation
repository) and is the AUTHORITATIVE target vocabulary. Generic
AudioSet/PANNs labels are never used as the target taxonomy here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

DEFAULT_REPO = os.environ.get(
    "SUNO_RECOMMENDER_REPO",
    str(Path(__file__).resolve().parents[4] / "music_creation"))
TARGETS_DIR = Path(DEFAULT_REPO) / "analytics" / "suno_stem_target_recommender" / "targets"


@dataclass(frozen=True)
class SunoTarget:
    target_id: str
    name: str
    category: str
    description: str = ""
    parent: Optional[str] = None
    is_beta: bool = False
    extras: dict = field(default_factory=dict)

    @property
    def slug(self) -> str:
        return self.target_id.replace("_", "-")


def load_targets(targets_dir: Path | None = None) -> dict[str, SunoTarget]:
    """Load standard + beta targets, deduplicated by id (beta wins for
    extra metadata; both share the documented Suno vocabulary)."""
    targets_dir = targets_dir or TARGETS_DIR
    out: dict[str, SunoTarget] = {}
    for filename, is_beta in (("standard.yaml", False), ("beta.yaml", True)):
        path = targets_dir / filename
        data = yaml.safe_load(path.read_text())
        for t in data.get("targets", []):
            out[t["id"]] = SunoTarget(
                target_id=t["id"], name=t["name"],
                category=t.get("category", "other"),
                description=t.get("description", ""),
                parent=t.get("parent"), is_beta=is_beta,
                extras={k: v for k, v in t.items()
                        if k not in ("id", "name", "category", "description",
                                     "parent", "children")})
    return out
