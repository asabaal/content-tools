"""Exact prompt-length checker tests (spec §10.6)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reference_corpus.checker import (  # noqa: E402
    MAX_CHARS, MIN_CHARS, check_book, check_prompt)


@pytest.mark.parametrize("count,ok", [
    (0, False), (899, False), (900, True), (950, True), (1000, True),
    (1001, False),
])
def test_boundaries(count, ok):
    text = "x" * count
    check = check_prompt(text, "t", "MAIN")
    assert check.ok is ok
    assert check.char_count == count


def test_exact_character_counting_includes_spaces():
    text = "a b\nc"          # 5 characters incl. space and newline
    assert check_prompt(text, "t", "MAIN").char_count == 5


def test_empty_prompt_fails():
    assert not check_prompt("", "t", "MAIN").ok


def test_check_book_reports_every_prompt():
    book = {
        "organ": {"main": "m" * 950, "exclude": "e" * 920},
        "piano": {"main": "m" * 899, "exclude": "e" * 1001},
    }
    report = check_book(book)
    assert report["targets"] == 2
    assert report["prompt_count"] == 4
    assert report["all_ok"] is False
    failed = [c for c in report["checks"] if not c["ok"]]
    assert {(c["target_id"], c["field"]) for c in failed} == {
        ("piano", "MAIN"), ("piano", "EXCLUDE")}
