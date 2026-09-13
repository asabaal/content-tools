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


def test_every_main_names_target_and_family_piece(built):
    for target_id, target in built["targets"].items():
        main = built["prompts"][target_id]["main"]
        assert target.name in main
        routing = built["routed"][target_id]
        if routing.primary == "percussion_timing":
            assert "Percussion Timing Reference" in main
            assert "2:00" in main
            assert "120 BPM" in main
        elif routing.primary == "vocal_timing":
            assert "Vocal Timing Reference" in main
            assert "2:00" in main
            assert "120 BPM" in main
            assert "'ah'" in main
        else:
            assert "The Steward's Calibration" in main
            assert "nine movements" in main
            assert "4:00" in main
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


# ---- ontology → calibration-family routing (timing addendum §4) --------------

def test_routing_built_into_book(built):
    from reference_corpus.families import (
        PITCHED, PERCUSSION, VOCAL, route, FAMILY_META)
    # spot-check the documented routing rules
    assert route("drums", "percussion").primary == PERCUSSION
    assert route("kick", "percussion").primary == PERCUSSION
    assert route("lead_vocal", "vocal").primary == VOCAL
    assert route("choir", "vocal").primary == VOCAL
    assert route("piano", "keyboard").primary == PITCHED
    assert route("organ", "keyboard").primary == PITCHED
    assert route("bass", "bass").primary == PITCHED
    # multi-family targets
    bells = route("bells", "percussion")
    assert bells.multi and PERCUSSION in bells.all_families \
        and PITCHED in bells.all_families
    voc = route("vocoder", "vocal")
    assert voc.multi and VOCAL in voc.all_families


def test_book_covers_three_families(built):
    from reference_corpus.families import PITCHED, PERCUSSION, VOCAL
    by_family = {}
    for tid, routing in built["routed"].items():
        by_family.setdefault(routing.primary, []).append(tid)
    assert by_family[PERCUSSION], "no percussion-family targets"
    assert by_family[VOCAL], "no vocal-family targets"
    assert len(by_family[PITCHED]) > len(by_family[PERCUSSION])


def test_family_prompts_describe_their_own_reference(built):
    from reference_corpus.families import PITCHED, PERCUSSION, VOCAL
    for tid, routing in built["routed"].items():
        main = built["prompts"][tid]["main"]
        if routing.primary == PERCUSSION:
            assert "Percussion Timing Reference" in main
            assert "The Steward's Calibration" not in main
        elif routing.primary == VOCAL:
            assert "Vocal Timing Reference" in main
            assert "The Steward's Calibration" not in main
        else:
            assert "The Steward's Calibration" in main
