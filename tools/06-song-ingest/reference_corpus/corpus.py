"""Reference-corpus structure and composition ingestion (spec §7)."""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@dataclass
class RenderLog:
    """Per-target render log template (spec §10.7). Intentionally blank
    until a human fills it after the Suno render."""
    suno_model_version: str = ""
    render_id: str = ""
    generation_date: str = ""
    keeper: str = ""            # keeper | reject | pending
    deviations: str = ""
    extraction_performed: bool = False
    extracted_target_path: str = ""
    extracted_target_sha256: str = ""
    midi_extracted: bool = False
    notes: str = ""


@dataclass
class TargetEntry:
    target_id: str
    name: str
    category: str
    is_beta: bool
    directory: str


CORPUS_ROOT = Path("projects") / "reference-corpus"
CANONICAL_DIR = CORPUS_ROOT / "canonical-piece"


def init_corpus(repo_root: Path, *, composition_source: Path,
                targets: dict[str, Any]) -> dict:
    """Create/refresh the corpus layout:

        projects/reference-corpus/canonical-piece/
          composition-version.json
          movement-map.json
          event_manifest.json (hash-linked; full file committed — it is JSON)
          prompt-book/
          targets/<slug>/{prompt.txt, exclude.txt, metadata.json, analysis/}

    `composition_source` is music_creation's reference_composition/output/.
    """
    repo_root = Path(repo_root)
    piece = repo_root / CANONICAL_DIR
    (piece / "prompt-book").mkdir(parents=True, exist_ok=True)
    (piece / "targets").mkdir(parents=True, exist_ok=True)

    copied = {}
    for name in ("composition_version.json", "movement_map.json",
                 "event_manifest.json", "canonical_reference_piece.mid"):
        src = composition_source / name
        if src.is_file():
            shutil.copy(src, piece / name)
            copied[name] = {"sha256": sha256(piece / name),
                            "bytes": (piece / name).stat().st_size}

    # one directory per documented Suno target
    entries = []
    for target_id, t in sorted(targets.items()):
        slug = t.slug if hasattr(t, "slug") else target_id.replace("_", "-")
        tdir = piece / "targets" / slug
        tdir.mkdir(exist_ok=True)
        (tdir / "analysis").mkdir(exist_ok=True)
        meta = {
            "target_id": target_id,
            "name": t.name if hasattr(t, "name") else t.get("name"),
            "category": t.category if hasattr(t, "category")
            else t.get("category"),
            "is_beta": t.is_beta if hasattr(t, "is_beta")
            else t.get("is_beta", False),
            "composition_version": copied.get("composition_version.json"),
            "render_log": asdict(RenderLog()),
        }
        (tdir / "metadata.json").write_text(
            json.dumps(meta, indent=2) + "\n")
        entries.append(TargetEntry(
            target_id=target_id, name=meta["name"], category=meta["category"],
            is_beta=meta["is_beta"], directory=str(tdir.relative_to(repo_root))))

    index = {
        "schema": "content-tools/reference-corpus/index",
        "schema_version": "0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_piece": "canonical-piece",
        "composition_artifacts": copied,
        "targets": [asdict(e) for e in entries],
    }
    (piece / "corpus-index.json").write_text(json.dumps(index, indent=2) + "\n")
    return index
