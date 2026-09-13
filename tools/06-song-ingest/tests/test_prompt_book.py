"""Prompt-book generation tests: every MAIN/EXCLUDE in 900–1000, invariants
present, determinism."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reference_corpus.build_book import build_all  # noqa: E402
from reference_corpus.checker import (  # noqa: E402
    MAX_CHARS, MIN_CHARS, check_book)

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def built():
    return build_all(REPO_ROOT)


def test_book_builds(built):
    assert built, "book failed to build (is the canonical composition ingested?)"


def test_covers_full_documented_ontology(built):
    assert len(built["prompts"]) >= 86
    assert "organ" in built["prompts"]
    assert "lead_vocal" in built["prompts"]
    assert "synth_pad" in built["prompts"]


def test_every_prompt_within_hard_range(built):
    report = check_book(built["prompts"])
    assert report["all_ok"], [c for c in report["checks"] if not c["ok"]]
    for c in report["checks"]:
        assert MIN_CHARS <= c["char_count"] <= MAX_CHARS


def test_every_main_names_target_and_invariants(built):
    for target_id, target in built["targets"].items():
        main = built["prompts"][target_id]["main"]
        assert target.name in main
        assert "The Steward's Calibration" in main
        assert "nine movements" in main
        assert "100 BPM" in main


def test_exclude_is_target_specific(built):
    targets = built["targets"]
    # same-category confusables appear in the EXCLUDE text
    assert "Electric piano" in built["prompts"]["piano"]["exclude"] or \
        "harpsichord" in built["prompts"]["piano"]["exclude"].lower()
    # non-vocal targets reject vocals
    assert "vocal" in built["prompts"]["organ"]["exclude"].lower()
    # vocal targets do NOT get the blanket no-vocals line
    assert "No sung vocals" not in built["prompts"]["lead_vocal"]["exclude"]


def test_generation_is_deterministic(built):
    rebuilt = build_all(REPO_ROOT)
    assert rebuilt["prompts"] == built["prompts"]
