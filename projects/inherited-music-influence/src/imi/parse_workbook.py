"""Parse the preserved Music.xls (via its converted xlsx) into dad_sources rows."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from .db import connect

# Greg's named homemade-tape series (artist field carries the series name).
TAPE_SERIES_RE = re.compile(
    r"^(fm rock|party tape|mellow tape|instrumentals|oldies|christmas medley)\b", re.I
)


def norm_text(value: str) -> str:
    """Aggressive normalization for matching keys (not for display)."""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return value.strip()


def flip_person_name(artist: str) -> str:
    """'Abdul, Paula' -> 'Paula Abdul'; leaves band names untouched."""
    if "," in artist:
        last, _, first = artist.partition(",")
        first, last = first.strip(), last.strip()
        if first and last and len(first.split()) <= 3:
            return f"{first} {last}"
    return artist


def is_custom_tape(media: str, artist: str, title: str) -> bool:
    """Custom tape = MEDIA Tape whose ARTIST carries a known series name.

    artist==title alone is NOT sufficient: Greg owned self-titled commercial
    albums on cassette (Asia, Metallica, Alias...). Known series: FM Rock,
    Party Tape, Mellow Tape, Instrumentals, Oldies, Christmas Medley.
    'Southern Rock' (Tape, no year) is suspected homemade but unconfirmed —
    it stays commercial and is flagged for manual review.
    """
    if media != "Tape":
        return False
    return bool(TAPE_SERIES_RE.search(norm_text(artist)))


def source_group(artist: str, title: str) -> str | None:
    for pattern, name in [
        (r"^fm rock\b", "FM Rock"),
        (r"^party tape\b", "Party Tape"),
        (r"^mellow tape\b", "Mellow Tape"),
        (r"^instrumentals\b", "Instrumentals"),
        (r"^oldies\b", "Oldies"),
    ]:
        if re.search(pattern, title, re.I) or re.search(pattern, artist, re.I):
            return name
    return None


def parse_project(project_root: Path) -> dict:
    """Parse data/raw/Music.xlsx -> dad_sources. Returns counts."""
    import openpyxl

    root = Path(project_root)
    xlsx = root / "data" / "raw" / "Music.xlsx"
    if not xlsx.exists():
        raise FileNotFoundError(
            f"{xlsx} not found — run the documented LibreOffice conversion of "
            "source/Music.xls first (see README)"
        )
    wb = openpyxl.load_workbook(xlsx, data_only=True, read_only=True)
    ws = wb["Main"]

    db_path = root / "data" / "imi.sqlite"
    conn = connect(db_path)
    counts = {"rows": 0, "custom_tape": 0, "commercial": 0, "favorite": 0}

    with conn:
        parsed_ids = []
        for sheet_row, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not row or all(v is None or str(v).strip() == "" for v in row):
                continue
            cells = [str(v).strip() if v is not None else "" for v in row]
            while len(cells) < 14:
                cells.append("")
            (num, artist_raw, band_name, various_misc, title_raw, edition_q,
             year_raw, media_raw, tape1, tape2, tape_order, special, misc_flag,
             favorite_raw) = cells[:14]

            artist_clean = artist_raw.strip()
            title_clean = title_raw.strip()
            if not artist_clean and not title_clean:
                continue
            kind = ("custom_tape"
                    if is_custom_tape(media_raw, artist_clean, title_clean)
                    else "commercial")
            artist_search = norm_text(flip_person_name(artist_clean))
            title_search = norm_text(title_clean)
            dad_source_id = f"D{sheet_row:04d}"
            parsed_ids.append(dad_source_id)
            conn.execute(
                """INSERT OR REPLACE INTO dad_sources
                   (dad_source_id, sheet_row, num, artist_raw, band_name_raw,
                    various_misc_raw, title_raw, edition_qualifier_raw, year_raw,
                    media_raw, tape1, tape2, tape_order, special, misc_flag,
                    favorite_raw, row_kind, source_group, artist_search,
                    title_search, resolution_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    dad_source_id, sheet_row, num, artist_clean,
                    band_name or None, various_misc or None, title_clean,
                    edition_q or None, year_raw or None, media_raw or None,
                    tape1 or None, tape2 or None, tape_order or None,
                    special or None, misc_flag or None,
                    1 if favorite_raw.lower() == "favorite" else 0,
                    kind, source_group(artist_clean, title_clean),
                    artist_search, title_search,
                    "non_commercial" if kind == "custom_tape" else "unresolved",
                ),
            )
            counts["rows"] += 1
            counts[kind] += 1
            if favorite_raw.lower() == "favorite":
                counts["favorite"] += 1
        # drop rows no longer in the workbook (FK-safe: only when unreferenced)
        if parsed_ids:
            qmarks = ",".join("?" for _ in parsed_ids)
            conn.execute(
                f"DELETE FROM dad_sources WHERE dad_source_id NOT IN ({qmarks})",
                parsed_ids)

    conn.execute(
        "INSERT INTO meta (key, value) VALUES ('parse_counts', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (json.dumps(counts),),
    )
    conn.close()
    return counts
