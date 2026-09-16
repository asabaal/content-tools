"""Calibration Prompt Bible tests (TIMING addendum successor strategy:
Solo/Lead ~60 s generation prompts, one instrument at a time)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reference_corpus.build_calibration_bible import (
    SEQUENCE, load_briefs, compose_solo, compose_lead)
from reference_corpus.ontology import load_targets

REPO_ROOT = Path(__file__).resolve().parents[3]
BOOK = (REPO_ROOT / "projects" / "reference-corpus" / "canonical-piece" /
        "prompt-book" / "SUNO_CALIBRATION_PROMPT_BIBLE.md")
CAL_JSON = (REPO_ROOT / "projects" / "reference-corpus" / "canonical-piece" /
            "prompt-book" / "calibration_prompts.json")
STALE = ["4:48", "288 seconds", "288-second", "120 bars", "120-bar"]


@pytest.fixture(scope="module")
def built():
    targets = load_targets()
    briefs = load_briefs()
    out = {}
    for tid in SEQUENCE:
        t = targets[tid]
        out[tid] = {
            "name": t.name, "category": t.category,
            "solo": compose_solo(t.name, briefs[tid]),
            "lead": compose_lead(t.name, briefs[tid]),
        }
    return out


def test_all_documented_targets_covered(built):
    targets = load_targets()
    assert set(built) == set(targets)
    assert len(built) == 90


def test_sequence_defined_and_starts_with_organ():
    assert SEQUENCE[0] == "organ"
    assert len(SEQUENCE) == 90
    assert len(set(SEQUENCE)) == 90


@pytest.mark.parametrize("field", ["solo", "lead"])
def test_every_prompt_within_suno_ceiling(built, field):
    for tid, d in built.items():
        assert 0 < len(d[field]) <= 1000, (tid, field, len(d[field]))


def test_solo_prompts_demand_isolation(built):
    banned_in_solo = ["backing track", "accompaniment", "second instrument"]
    for tid, d in built.items():
        solo = d["solo"].lower()
        assert d["name"].lower() in solo, tid
        assert "unaccompanied" in solo or "alone" in solo or \
            "no backing track" in solo, tid
        for banned in banned_in_solo:
            if banned == "second instrument":
                continue
            assert "no " + banned in solo or "unaccompanied" in solo, \
                (tid, banned)


def test_solo_prompts_are_reference_not_song(built):
    for tid, d in built.items():
        assert "not a song" in d["solo"].lower() or \
            "reference performance" in d["solo"].lower(), tid


def test_lead_prompts_demand_dominance(built):
    for tid, d in built.items():
        lead = d["lead"].lower()
        assert "unmistakable lead" in lead
        assert "never disappears" in lead or "never competes" in lead or \
            "not a full song" in lead
        assert "sixty seconds" in lead


def test_vocal_targets_use_non_lexical_vocalise(built):
    for tid in ("lead_vocal", "backing_vocal", "choir", "vocoder"):
        assert "no lyrics" in built[tid]["solo"].lower()
        assert "non-lexical" in built[tid]["solo"].lower()


def test_percussion_solo_rejects_melodic_contamination(built):
    for tid in ("drums", "kick", "snare", "bongos", "taiko"):
        assert "no drum-kit" not in built[tid]["solo"].lower()
    # percussion SOLO must not request pitched/harmonic backing
    lead = built["drums"]["lead"].lower()
    assert "sparse" in lead or "none" in lead


def test_committed_bible_file_matches_generated(built):
    assert BOOK.is_file()
    data = json.loads(CAL_JSON.read_text())
    assert data["calibration_sequence"][0] == "organ"
    assert set(data["prompts"]) == set(built)
    for tid, d in built.items():
        assert data["prompts"][tid]["solo"] == d["solo"]
        assert data["prompts"][tid]["lead"] == d["lead"]


def test_committed_bible_has_no_stale_duration_references():
    text = BOOK.read_text()
    for bad in STALE:
        assert bad not in text.lower()


def test_conditioning_book_carries_supersession_banner():
    old_book = (REPO_ROOT / "projects" / "reference-corpus" /
                "canonical-piece" / "prompt-book" /
                "SUNO_RENDERING_PROMPT_BOOK.md")
    text = old_book.read_text()
    assert "CALIBRATION GENERATION SUPERSEDED" in text
    assert "SUNO_CALIBRATION_PROMPT_BIBLE.md" in text


def test_render_log_template_present_per_target():
    text = BOOK.read_text()
    assert text.count("### Render log") == 90
    assert text.count("| keeper/reject | |") == 90
