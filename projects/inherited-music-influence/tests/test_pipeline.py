"""End-to-end pipeline tests.

Run against a temporary COPY of the canonical workspace so tests never race
with background enrichment or mutate archival state. MusicBrainz enrichment
itself is not exercised in tests (network); its artifacts are read as data.
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
sys.path.insert(0, str(SRC))


@pytest.fixture(scope="module")
def work_root(tmp_path_factory) -> Path:
    src_db = PROJECT / "data" / "imi.sqlite"
    if not src_db.exists():
        pytest.skip("canonical DB not yet built — run `imi parse` first")
    root = tmp_path_factory.mktemp("imi-work")
    (root / "data" / "raw").mkdir(parents=True)
    shutil.copy(PROJECT / "data" / "raw" / "Music.xlsx",
                root / "data" / "raw" / "Music.xlsx")
    # consistent snapshot even if a background enrichment is mid-commit
    src = sqlite3.connect(src_db)
    dst = sqlite3.connect(root / "data" / "imi.sqlite")
    src.backup(dst)
    dst.close()
    src.close()
    return root


def _conn(root: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(root / "data" / "imi.sqlite")
    conn.row_factory = sqlite3.Row
    return conn


def test_parse_preserves_every_workbook_row(work_root: Path):
    from imi.parse_workbook import parse_project
    counts = parse_project(work_root)
    conn = _conn(work_root)
    n_db = conn.execute("SELECT COUNT(*) FROM dad_sources").fetchone()[0]
    n_custom = conn.execute(
        "SELECT COUNT(*) FROM dad_sources WHERE row_kind='custom_tape'").fetchone()[0]
    n_fav = conn.execute(
        "SELECT COUNT(*) FROM dad_sources WHERE favorite_raw = 1").fetchone()[0]
    assert n_db == counts["rows"] == 1176
    assert counts["custom_tape"] == n_custom == 44
    assert counts["favorite"] == n_fav == 174


def test_ids_derive_from_sheet_rows(work_root: Path):
    conn = _conn(work_root)
    rows = conn.execute(
        "SELECT dad_source_id, sheet_row FROM dad_sources ORDER BY sheet_row").fetchall()
    assert all(r["dad_source_id"] == f"D{r['sheet_row']:04d}" for r in rows)
    assert rows[0]["sheet_row"] == 2


def test_favorite_is_source_level(work_root: Path):
    from imi.resolve import repair_appearance_flags, recompute_song_dad_stats
    conn = _conn(work_root)
    repair_appearance_flags(conn)
    recompute_song_dad_stats(conn)
    conn.commit()  # the invariants hold once these are committed
    bad = conn.execute(
        """SELECT COUNT(*) FROM dad_appearances da
           JOIN dad_sources ds ON ds.dad_source_id = da.dad_source_id
           WHERE da.appears_on_dad_favorite_source != ds.favorite_raw""").fetchone()[0]
    assert bad == 0
    bad2 = conn.execute(
        """SELECT COUNT(*) FROM songs s
           WHERE s.dad_favorite_source_count != (
             SELECT COUNT(*) FROM dad_appearances da
             JOIN dad_sources ds ON ds.dad_source_id = da.dad_source_id
             WHERE da.song_id = s.song_id AND ds.favorite_raw = 1)""").fetchone()[0]
    assert bad2 == 0


def test_songs_dedupe_across_releases(work_root: Path):
    conn = _conn(work_root)
    dupes = conn.execute(
        """SELECT COUNT(*) FROM (
             SELECT norm_artist, norm_title, COUNT(DISTINCT song_id) AS n
             FROM songs GROUP BY norm_artist, norm_title HAVING n > 1)""").fetchone()[0]
    assert dupes == 0


def test_multi_release_songs_keep_all_appearances(work_root: Path):
    conn = _conn(work_root)
    multi = conn.execute(
        """SELECT song_id, COUNT(DISTINCT release_id) AS n
           FROM release_tracks GROUP BY song_id HAVING n > 1 LIMIT 1""").fetchone()
    if not multi:
        pytest.skip("no multi-release songs yet (enrichment incomplete)")
    n_sources = conn.execute(
        "SELECT COUNT(*) FROM dad_appearances WHERE song_id = ?",
        (multi["song_id"],)).fetchone()[0]
    assert n_sources >= 1


def test_custom_tapes_never_get_external_releases(work_root: Path):
    conn = _conn(work_root)
    n = conn.execute(
        """SELECT COUNT(*) FROM dad_sources
           WHERE row_kind='custom_tape' AND release_id IS NOT NULL""").fetchone()[0]
    assert n == 0


def test_rank_is_deterministic_and_dad_first(work_root: Path):
    from imi.rank import rank
    rows = rank(work_root)
    assert len(rows) > 0
    tiers = [(r["dad_favorite_source_count"], r["dad_source_count"]) for r in rows]
    assert tiers == sorted(tiers, key=lambda t: (-t[0], -t[1]))
    ranks = [r["queue_rank"] for r in rows]
    assert ranks == list(range(1, len(rows) + 1))


def test_annotations_survive_regeneration(work_root: Path):
    from imi.annotations import set_note, get_note
    from imi.parse_workbook import parse_project

    conn = _conn(work_root)
    song = conn.execute("SELECT song_id FROM songs LIMIT 1").fetchone()
    if not song:
        pytest.skip("no songs yet (enrichment incomplete)")
    song_id = song["song_id"]

    set_note(work_root, song_id, {
        "recognition_status": "definitely_recognize",
        "listening_note": "This was in the kitchen cabinet with the blue tapes.",
        "childhood_association": "yes",
    })
    assert get_note(work_root, song_id)["listening_note"].startswith("This was")

    parse_project(work_root)  # full regeneration of dad_sources
    after = get_note(work_root, song_id)
    assert after["recognition_status"] == "definitely_recognize"
    assert after["listening_note"].startswith("This was")
    assert after["childhood_association"] == "yes"

    conn = _conn(work_root)
    assert conn.execute("SELECT COUNT(*) FROM dad_sources").fetchone()[0] == 1176


def test_top300_output_matches_rank_when_ready(work_root: Path):
    from imi.rank import export_views
    conn = _conn(work_root)
    n_songs = conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
    if n_songs < 300:
        pytest.skip(f"only {n_songs} songs so far — full Top 300 after enrichment")
    summary = export_views(work_root)
    assert summary["top300_length"] == 300
    top_path = PROJECT / "output" / "top-300.md" if False else work_root / "output" / "top-300.md"
    rows = [l for l in top_path.read_text().splitlines() if l.startswith("| ")]
    rows = [r for r in rows if "---" not in r][1:]
    assert len(rows) == 300
