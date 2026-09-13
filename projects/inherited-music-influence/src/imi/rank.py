"""Dad-first ranking, queue generation, exports, and annotation writes."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from .db import connect

RANK_SQL = """
SELECT s.song_id, s.canonical_artist, s.canonical_title, s.first_release_year,
       s.dad_source_count, s.dad_favorite_source_count,
       s.appears_on_dad_favorite_source, s.curated_tape_known_count,
       s.dad_format_count, s.popularity_score, s.popularity_status,
       r.title AS release_title, r.date_first AS release_date,
       a.recognition_status, a.listening_note, a.memory_note
FROM songs s
LEFT JOIN dad_appearances da ON da.song_id = s.song_id
LEFT JOIN releases r ON r.release_id = da.release_id
LEFT JOIN dad_sources ds ON ds.dad_source_id = da.dad_source_id
LEFT JOIN annotations a ON a.song_id = s.song_id
GROUP BY s.song_id
ORDER BY
    s.dad_favorite_source_count DESC,
    s.appears_on_dad_favorite_source DESC,
    s.curated_tape_known_count DESC,
    s.dad_source_count DESC,
    (s.popularity_score IS NULL) ASC,
    s.popularity_score DESC,
    s.first_release_year ASC,
    s.song_id ASC
"""


def rank(root: Path) -> list[dict]:
    conn = connect(root / "data" / "imi.sqlite")
    rows = [dict(r) for r in conn.execute(RANK_SQL).fetchall()]
    for i, r in enumerate(rows, 1):
        r["queue_rank"] = i
    conn.close()
    return rows


def aggregate_dad_sources(rows: list[dict], root: Path) -> list[dict]:
    """Group queue rows by song, collecting every Greg source under each song."""
    conn = connect(root / "data" / "imi.sqlite")
    by_song: dict[str, dict] = {}
    for r in rows:
        sid = r["song_id"]
        entry = by_song.setdefault(sid, {
            "queue_rank": r["queue_rank"], "song_id": sid,
            "canonical_artist": r["canonical_artist"],
            "canonical_title": r["canonical_title"],
            "first_release_year": r["first_release_year"],
            "dad_favorite_source_count": r["dad_favorite_source_count"],
            "dad_source_count": r["dad_source_count"],
            "appears_on_dad_favorite_source": r["appears_on_dad_favorite_source"],
            "popularity_score": r["popularity_score"],
            "popularity_status": r["popularity_status"],
            "recognition_status": r["recognition_status"] or "unreviewed",
            "listening_note": r["listening_note"], "memory_note": r["memory_note"],
            "dad_sources": [],
        })
        srcs = conn.execute(
            """SELECT ds.dad_source_id, ds.sheet_row, ds.artist_raw, ds.title_raw,
                      ds.year_raw, ds.media_raw, ds.favorite_raw,
                      ds.resolution_status, da.release_id, da.certainty
               FROM dad_appearances da JOIN dad_sources ds
                 ON ds.dad_source_id = da.dad_source_id
               WHERE da.song_id = ?""",
            (sid,),
        ).fetchall()
        seen = set()
        for s in srcs:
            key = (s["dad_source_id"], s["release_id"])
            if key in seen:
                continue
            seen.add(key)
            entry["dad_sources"].append(dict(s))
    conn.close()
    return list(by_song.values())


def export_views(root: Path, *, top_n: int = 300) -> dict:
    root = Path(root)
    rows = rank(root)
    agg = aggregate_dad_sources(rows, root)
    conn = connect(root / "data" / "imi.sqlite")

    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    derived = root / "data" / "derived"
    derived.mkdir(parents=True, exist_ok=True)

    # full queue CSV + JSONL (machine-readable canonical exports)
    with (derived / "listening-queue-full.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "queue_rank", "song_id", "canonical_artist", "canonical_title",
            "first_release_year", "dad_favorite_source_count", "dad_source_count",
            "appears_on_dad_favorite_source", "popularity_score", "popularity_status",
            "recognition_status"])
        w.writeheader()
        for e in agg:
            w.writerow({k: e[k] for k in w.fieldnames})
    with (derived / "listening-queue-full.jsonl").open("w", encoding="utf-8") as fh:
        for e in agg:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")

    top = agg[:top_n]
    lines = ["# Top 300 Recognition Queue (generated)", "",
             "Dad evidence first, popularity second (lexicographic; see research/design.md).",
             "Recognition: mark with `imi note --song <song_id> --recognize definitely_recognize`.", ""]
    lines.append(_md_table(
        ["#", "song_id", "artist", "title", "year", "dad_src", "fav_src", "pop"],
        [[e["queue_rank"], e["song_id"], e["canonical_artist"], e["canonical_title"],
          e["first_release_year"] or "?", e["dad_source_count"],
          e["dad_favorite_source_count"],
          e["popularity_score"] if e["popularity_score"] is not None else "—"]
         for e in top]))
    (out_dir / "top-300.md").write_text("\n".join(lines))

    full = ["# Full Listening Queue (generated)", ""]
    full.append(_md_table(
        ["#", "artist", "title", "year", "dad_src", "fav_src", "recognition"],
        [[e["queue_rank"], e["canonical_artist"], e["canonical_title"],
          e["first_release_year"] or "?", e["dad_source_count"],
          e["dad_favorite_source_count"], e["recognition_status"]] for e in agg]))
    (out_dir / "full-listening-queue.md").write_text("\n".join(full))

    # archive summary
    n_sources = conn.execute("SELECT COUNT(*) FROM dad_sources").fetchone()[0]
    fav_sources = conn.execute(
        "SELECT COUNT(*) FROM dad_sources WHERE favorite_raw = 1").fetchone()[0]
    n_songs = conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]
    n_tracks = conn.execute("SELECT COUNT(*) FROM release_tracks").fetchone()[0]
    counts = dict(conn.execute(
        "SELECT resolution_status, COUNT(*) FROM dad_sources GROUP BY resolution_status").fetchall())
    ann = dict(conn.execute(
        "SELECT recognition_status, COUNT(*) FROM annotations GROUP BY recognition_status").fetchall())
    summary = {
        "dad_sources": n_sources, "favorite_sources": fav_sources,
        "songs": n_songs, "release_tracks": n_tracks,
        "resolution": counts, "annotations": ann,
        "queue_length": len(agg), "top300_length": len(top),
    }
    (out_dir / "archive-summary.md").write_text(
        "# Archive summary (generated)\n\n```json\n"
        + json.dumps(summary, indent=2) + "\n```\n")
    conn.close()
    return summary


def _md_table(headers, rows):
    def cell(v):
        return ("" if v is None else str(v)).replace("|", "\\|").replace("\n", " ")
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    out += ["| " + " | ".join(cell(v) for v in r) + " |" for r in rows]
    return "\n".join(out) + "\n"
