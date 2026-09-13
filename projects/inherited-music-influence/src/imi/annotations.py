"""User annotation layer — the ONLY writer of the annotations table."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from .db import connect

RECOGNITION = ("unreviewed", "definitely_recognize", "not_sure",
               "definitely_do_not_recognize")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def set_note(root: Path, song_id: str, updates: dict[str, Any]) -> dict:
    conn = connect(root / "data" / "imi.sqlite")
    try:
        song = conn.execute("SELECT song_id FROM songs WHERE song_id = ?",
                            (song_id,)).fetchone()
        if not song:
            raise ValueError(f"unknown song_id: {song_id}")
        if "recognition_status" in updates:
            if updates["recognition_status"] not in RECOGNITION:
                raise ValueError(f"recognition_status must be one of {RECOGNITION}")
        cur = conn.execute(
            "SELECT * FROM annotations WHERE song_id = ?", (song_id,)).fetchone()
        first_reviewed_at = None
        if cur is None:
            row = conn.execute(
                "INSERT INTO annotations (song_id, recognition_status, updated_at)"
                " VALUES (?, 'unreviewed', ?)", (song_id, _now()))
            cur = conn.execute(
                "SELECT * FROM annotations WHERE song_id = ?", (song_id,)).fetchone()
            first_reviewed_at = _now()
        updates = {k: v for k, v in updates.items() if v is not None or k in (
            "listening_note", "memory_note", "musical_features",
            "possible_influence_note")}
        if "recognition_status" in updates and cur["first_reviewed_at"] is None:
            first_reviewed_at = first_reviewed_at or _now()
        sets, params = [], []
        for k, v in updates.items():
            if k == "listened":
                v = 1 if v in (1, "1", True, "yes", "true") else 0 if v in (0, "0", False, "no", "false") else None
            if k == "first_reviewed_at":
                continue
            sets.append(f"{k} = ?")
            params.append(v)
        if first_reviewed_at:
            sets.append("first_reviewed_at = COALESCE(first_reviewed_at, ?)")
            params.append(first_reviewed_at)
        sets.append("updated_at = ?")
        params.append(_now())
        params.append(song_id)
        conn.execute(f"UPDATE annotations SET {', '.join(sets)} WHERE song_id = ?", params)
        conn.commit()
        return dict(conn.execute(
            "SELECT * FROM annotations WHERE song_id = ?", (song_id,)).fetchone())
    finally:
        conn.close()


def get_note(root: Path, song_id: str) -> dict | None:
    conn = connect(root / "data" / "imi.sqlite")
    try:
        row = conn.execute("SELECT * FROM annotations WHERE song_id = ?",
                           (song_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
