"""Release resolution + canonical-song construction (MusicBrainz v1)."""

from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

from .db import connect
from .parse_workbook import flip_person_name, norm_text

UA = "InheritedMusicInfluenceArchive/0.1 (autobiographical research; contact: archive owner)"
RATE_LIMIT_S = 1.05
CACHE_DIR_NAME = "mb-cache"
RESOLVED_T = 0.82
PROBABLE_T = 0.60


def _cache_put(cache_dir: Path, url: str, payload: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()
    (cache_dir / f"{key}.json").write_text(
        json.dumps({"url": url, "payload": payload}, ensure_ascii=False), encoding="utf-8"
    )


def _cache_get(cache_dir: Path, url: str) -> dict | None:
    key = hashlib.sha1(url.encode()).hexdigest()
    p = cache_dir / f"{key}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))["payload"]
    return None


def mb_get(url: str, cache_dir: Path, *, force: bool = False) -> dict:
    cached = None if force else _cache_get(cache_dir, url)
    if cached is not None:
        return cached
    payload = None
    for attempt in range(5):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code in (503, 502, 429) and attempt < 4:
                time.sleep([3, 8, 20, 45][attempt])
                continue
            raise
    if payload is None:
        raise RuntimeError(f"musicbrainz unreachable after retries: {url}")
    _cache_put(cache_dir, url, payload)
    time.sleep(RATE_LIMIT_S)
    return payload


def song_id_for(norm_artist: str, norm_title: str) -> str:
    digest = hashlib.sha1(f"{norm_artist}||{norm_title}".encode()).hexdigest()
    return "S" + digest[:10]


def clean_track_title(title: str) -> tuple[str, str | None]:
    """Split 'Song (live)' -> ('Song', 'live')."""
    m = re.match(r"^(.*?)\s*[\(\[]([^)\]]*)[\)\]]\s*$", title)
    if m and re.search(r"live|remix|version|edit|mono|stereo|demo|remaster", m.group(2), re.I):
        return m.group(1).strip(), m.group(2).strip()
    return title.strip(), None


def _sim(a: str, b: str) -> float:
    a, b = norm_text(a), norm_text(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.9
    sa, sb = set(a.split()), set(b.split())
    inter = len(sa & sb)
    return 2 * inter / max(1, len(sa) + len(sb))


def score_candidates(cands: list[dict], artist: str, title: str, year: str | None) -> list[dict]:
    out = []
    artist = flip_person_name(artist)
    for c in cands:
        s = _sim(c.get("title", ""), title) * 0.6 + _sim(
            c.get("artist-credit", [{}])[0].get("name", "") if c.get("artist-credit") else c.get("artist", ""),
            artist,
        ) * 0.4
        if year:
            cyear = (c.get("date") or "")[:4]
            if cyear.isdigit():
                s *= 1.0 if abs(int(cyear) - int(year)) <= 2 else 0.75
        out.append({"score": round(min(1.0, s), 4), "candidate": c})
    return sorted(out, key=lambda x: x["score"], reverse=True)




def collapse_to_release_groups(scored: list[dict]) -> list[dict]:
    """Collapse country-edition duplicates that share a release-group.

    Keeps the best-scored candidate per release-group; a 'group_best' score is
    the group's best. Order by group_best desc.
    """
    groups: dict[str, dict] = {}
    for entry in scored:
        c = entry["candidate"]
        rg = (c.get("release-group") or {}).get("id") or c.get("id") or c.get("title", "?")
        if rg not in groups or entry["score"] > groups[rg]["score"]:
            groups[rg] = {**entry, "release_group": rg}
    return sorted(groups.values(), key=lambda x: x["score"], reverse=True)


def repair_appearance_flags(conn: sqlite3.Connection) -> None:
    """Appearance favorite flags mirror the source row (never accumulated)."""
    conn.execute(
        """UPDATE dad_appearances SET appears_on_dad_favorite_source =
          (SELECT ds.favorite_raw FROM dad_sources ds
           WHERE ds.dad_source_id = dad_appearances.dad_source_id)"""
    )


def run_enrichment(project_root: Path, *, limit: int | None = None,
                   only: list[str] | None = None, force: bool = False) -> dict:
    root = Path(project_root)
    data = root / "data"
    cache_dir = data / "mb-cache"
    conn = connect(root / "data" / "imi.sqlite")

    if isinstance(only, str):
        only = [x.strip() for x in only.split(',') if x.strip()]
    sql = ("SELECT * FROM dad_sources WHERE row_kind = 'commercial' "
           "AND resolution_status IN ('unresolved')")
    params: list = []
    if only:
        sql += f" AND dad_source_id IN ({','.join('?' * len(only))})"
        params = list(only)
    if not force:
        pass  # unresolved-only is already the resume behavior
    sql += " ORDER BY favorite_raw DESC, sheet_row"
    if limit:
        sql += f" LIMIT {int(limit)}"
    todo = conn.execute(sql, params).fetchall()

    counts = {"resolved": 0, "probable": 0, "ambiguous": 0, "unresolved": 0}
    for row in todo:
        artist_q = flip_person_name(row["artist_raw"])
        query = f'artist:{artist_q} AND release:{row["title_raw"]}'
        url = ("https://musicbrainz.org/ws/2/release/?query="
               + urllib.parse.quote(query)
               + "&fmt=json&limit=25")
        try:
            payload = mb_get(url, cache_dir)
        except Exception as exc:
            conn.execute(
                "UPDATE dad_sources SET resolution_notes = ? WHERE dad_source_id = ?",
                (f"search error: {exc}", row["dad_source_id"]),
            )
            conn.commit()
            counts["unresolved"] += 1
            continue

        cands = payload.get("releases", [])
        scored = collapse_to_release_groups(
            score_candidates(cands, row["artist_raw"], row["title_raw"], row["year_raw"]))
        if not scored:
            conn.execute(
                "UPDATE dad_sources SET resolution_status='unresolved',"
                " resolution_notes='no MusicBrainz candidates' WHERE dad_source_id=?",
                (row["dad_source_id"],))
            conn.commit()
            counts["unresolved"] += 1
            continue
        top = scored[0]
        ties = [c for c in scored if c["score"] >= top["score"] - 0.02]
        cand_meta = [
            {"title": c["candidate"].get("title"),
             "artist": (c["candidate"].get("artist-credit") or [{}])[0].get("name"),
             "date": c["candidate"].get("date"), "mbid": c["candidate"].get("id"),
             "release_group": c.get("release_group"), "score": c["score"]}
            for c in scored[:5]
        ]
        if top["score"] >= RESOLVED_T and len(ties) == 1:
            status, mbid = "resolved", top["candidate"]["id"]
        elif top["score"] >= PROBABLE_T and len(ties) == 1:
            status, mbid = "probable", top["candidate"]["id"]
        else:
            status, mbid = "ambiguous", (top["candidate"]["id"] if top["score"] >= PROBABLE_T else None)
            if mbid is None:
                conn.execute(
                    "UPDATE dad_sources SET resolution_status='ambiguous',"
                    " resolution_notes=? WHERE dad_source_id=?",
                    (json.dumps(cand_meta, ensure_ascii=False), row["dad_source_id"]))
                conn.commit()
                counts["ambiguous"] += 1
                continue

        detail_url = (f"https://musicbrainz.org/ws/2/release/{mbid}"
                      "?inc=recordings+media+artist-credits+labels&fmt=json")
        try:
            detail = mb_get(detail_url, cache_dir)
        except Exception as exc:
            conn.execute(
                "UPDATE dad_sources SET resolution_notes = ? WHERE dad_source_id = ?",
                (f"detail error: {exc}", row["dad_source_id"]),
            )
            conn.commit()
            counts["unresolved"] += 1
            continue

        labels = [
            (li.get("label", {}).get("name"), li.get("catalog-number"))
            for li in detail.get("label-info", []) if li.get("label")
        ]
        date = detail.get("date")
        conn.execute(
            """INSERT INTO releases (release_id, mbid, title, artist, artist_mbid,
               date_first, country, labels_json, source_provider, source_url,
               retrieved_at, match_score, dad_source_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(release_id) DO UPDATE SET
                 title=excluded.title, artist=excluded.artist,
                 date_first=COALESCE(excluded.date_first, date_first),
                 country=COALESCE(excluded.country, country),
                 labels_json=excluded.labels_json,
                 retrieved_at=excluded.retrieved_at""",
            (
                "R" + mbid.replace("-", ""), mbid,
                detail.get("title", row["title_raw"]),
                (detail.get("artist-credit") or [{}])[0].get("name", flip_person_name(row["artist_raw"])),
                ((detail.get("artist-credit") or [{}])[0].get("artist") or {}).get("id"),
                date, detail.get("country"),
                json.dumps(labels, ensure_ascii=False),
                "musicbrainz",
                f"https://musicbrainz.org/release/{mbid}",
                time.strftime("%Y-%m-%d"),
                top["score"], row["dad_source_id"],
            ),
        )
        release_id = "R" + mbid.replace("-", "")

        # tracks -> songs
        for medium in detail.get("media", []):
            disc = medium.get("position", 1)
            for track in medium.get("tracks", []):
                rec_title = track.get("title", "")
                title, variant = clean_track_title(rec_title)
                track_artist = (track.get("artist-credit") or detail.get("artist-credit") or [{}])[0].get("name", "")
                canon_artist = track_artist or flip_person_name(row["artist_raw"])
                sid = song_id_for(norm_text(canon_artist), norm_text(title))
                conn.execute(
                    """INSERT OR IGNORE INTO songs (song_id, canonical_artist,
                       canonical_title, norm_artist, norm_title)
                       VALUES (?,?,?,?,?)""",
                    (sid, canon_artist, title,
                     norm_text(canon_artist), norm_text(title)),
                )
                # sid is a pure function of (norm_artist, norm_title); after the
                # ignore-or-insert it is guaranteed present. Variant info stays on
                # release_tracks.track_title_printed (provenance), not the song key.
                conn.execute(
                    """INSERT INTO release_tracks (release_id, disc, track_no,
                       track_title_printed, song_id) VALUES (?,?,?,?,?)
                       ON CONFLICT (release_id, disc, track_no) DO UPDATE SET
                       track_title_printed=excluded.track_title_printed""",
                    (release_id, disc, track.get("position", 0), rec_title, sid),
                )
                fav = 1 if row["favorite_raw"] else 0
                conn.execute(
                    """INSERT INTO dad_appearances (song_id, dad_source_id, release_id,
                       appears_on_dad_favorite_source, certainty)
                       VALUES (?,?,?,?,?)
                       ON CONFLICT (song_id, dad_source_id) DO UPDATE SET
                       appears_on_dad_favorite_source=excluded.appears_on_dad_favorite_source,
                       certainty=excluded.certainty""",
                    (sid, row["dad_source_id"], release_id, fav,
                     "verified" if status == "resolved" else "probable"),
                )

        conn.execute(
            "UPDATE dad_sources SET resolution_status=?, release_id=?,"
            " resolution_notes=? WHERE dad_source_id=?",
            (status, release_id, json.dumps(cand_meta, ensure_ascii=False),
             row["dad_source_id"]),
        )
        conn.commit()
        counts[status] += 1

    repair_appearance_flags(conn)
    recompute_song_dad_stats(conn)
    conn.commit()
    return counts


def recompute_song_dad_stats(conn: sqlite3.Connection) -> None:
    """Recompute per-song Dad-evidence aggregates from dad_appearances."""
    conn.execute(
        """UPDATE songs SET
             dad_source_count = (SELECT COUNT(*) FROM dad_appearances da
                                 WHERE da.song_id = songs.song_id),
             dad_favorite_source_count = (SELECT COUNT(*) FROM dad_appearances da
                 JOIN dad_sources ds ON ds.dad_source_id = da.dad_source_id
                 WHERE da.song_id = songs.song_id AND ds.favorite_raw = 1),
             appears_on_dad_favorite_source = (SELECT EXISTS (
                 SELECT 1 FROM dad_appearances da
                 JOIN dad_sources ds ON ds.dad_source_id = da.dad_source_id
                 WHERE da.song_id = songs.song_id AND ds.favorite_raw = 1)),
             curated_tape_known_count = 0,
             dad_format_count = (SELECT COUNT(DISTINCT ds.media_raw) FROM dad_appearances da
                 JOIN dad_sources ds ON ds.dad_source_id = da.dad_source_id
                 WHERE da.song_id = songs.song_id)"""
    )
