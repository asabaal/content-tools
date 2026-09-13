"""Reference-corpus structure tests (spec §7)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reference_corpus.corpus import init_corpus  # noqa: E402
from reference_corpus.ontology import load_targets  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
PIECE = REPO_ROOT / "projects" / "reference-corpus" / "canonical-piece"


def test_corpus_layout_exists():
    # created by reference_corpus.bootstrap against the real repos
    assert (PIECE / "composition_version.json").is_file()
    assert (PIECE / "movement_map.json").is_file()
    assert (PIECE / "event_manifest.json").is_file()
    assert (PIECE / "canonical_reference_piece.mid").is_file()
    assert (PIECE / "corpus-index.json").is_file()
    assert (PIECE / "prompt-book" / "SUNO_RENDERING_PROMPT_BOOK.md").is_file()
    assert (PIECE / "ontology-linkage.json").is_file()


def test_every_documented_target_has_a_directory():
    targets = load_targets()
    for target_id, t in targets.items():
        tdir = PIECE / "targets" / (t.slug if hasattr(t, "slug")
                                    else target_id.replace("_", "-"))
        assert tdir.is_dir(), target_id
        assert (tdir / "metadata.json").is_file()
        assert (tdir / "prompt.txt").is_file()
        assert (tdir / "exclude.txt").is_file()
        meta = json.loads((tdir / "metadata.json").read_text())
        assert set(meta["render_log"]) >= {
            "suno_model_version", "render_id", "generation_date", "keeper",
            "deviations", "extraction_performed", "extracted_target_path",
            "extracted_target_sha256", "midi_extracted", "notes"}


def test_composition_version_hashes_match():
    version = json.loads((PIECE / "composition_version.json").read_text())
    import hashlib
    midi = PIECE / "canonical_reference_piece.mid"
    assert (hashlib.sha256(midi.read_bytes()).hexdigest()
            == version["artifacts"]["canonical_reference_piece.mid"]["sha256"])
    assert version["deterministic"] is True


def test_ontology_linkage_records_authoritative_vocab():
    link = json.loads((PIECE / "ontology-linkage.json").read_text())
    assert link["ontology"]["targets"] >= 86
    assert "music_creation" in link["ontology"]["source_repo"]


# ---- hard 4:00 / 100-bar contract (spec correction) -------------------------

STALE_REFERENCES = ["4:48", "288 seconds", "288-second", "120 bars"]


def test_exact_four_minute_contract():
    """HARD: the active corpus must never regress to 4:48 / 288 s / 120 bars."""
    mmap = json.loads((PIECE / "movement_map.json").read_text())
    assert mmap["duration_seconds"] == 240.0
    assert mmap["total_bars"] == 100
    version = json.loads((PIECE / "composition_version.json").read_text())
    assert version["tempo_bpm"] == 100
    events = json.loads((PIECE / "event_manifest.json").read_text())["events"]
    for e in events:
        assert e["onset_seconds"] + e["duration_seconds"] <= 240.001


def test_conditioning_renders_are_exactly_240s():
    notes = json.loads((PIECE / "conditioning_render_notes.json").read_text())
    for name, r in notes["renders"].items():
        assert r["validation"]["exactly_240"] is True, name
        assert r["validation"]["not_clipped"] is True, name
        assert r["validation"]["all_sections_audible"] is True, name


def test_no_stale_duration_references_in_generated_outputs():
    """The generated prompt book, every prompt/exclude file, and the
    ontology linkage must be free of superseded duration wording."""
    checked = []
    book = PIECE / "prompt-book" / "SUNO_RENDERING_PROMPT_BOOK.md"
    checked.append(("prompt book", book.read_text()))
    checked.append(("ontology-linkage",
                    (PIECE / "ontology-linkage.json").read_text()))
    checked.append(("movement map",
                    (PIECE / "movement_map.json").read_text()))
    checked.append(("composition version",
                    (PIECE / "composition_version.json").read_text()))
    for tdir in (PIECE / "targets").iterdir():
        for fname in ("prompt.txt", "exclude.txt", "metadata.json"):
            f = tdir / fname
            if f.is_file():
                checked.append((f"{tdir.name}/{fname}", f.read_text()))
    failures = []
    for name, text in checked:
        for bad in STALE_REFERENCES:
            if bad.lower() in text.lower():
                failures.append(f"{name}: {bad!r}")
    assert not failures, failures
