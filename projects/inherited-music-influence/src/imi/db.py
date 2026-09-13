"""Canonical SQLite datastore for the Inherited Music Influence Archive."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dad_sources (
    dad_source_id TEXT PRIMARY KEY,
    sheet_row INTEGER NOT NULL UNIQUE,
    num TEXT,
    artist_raw TEXT NOT NULL,
    band_name_raw TEXT,
    various_misc_raw TEXT,
    title_raw TEXT NOT NULL,
    edition_qualifier_raw TEXT,
    year_raw TEXT,
    media_raw TEXT,
    tape1 TEXT,
    tape2 TEXT,
    tape_order TEXT,
    special TEXT,
    misc_flag TEXT,
    favorite_raw INTEGER NOT NULL DEFAULT 0,
    row_kind TEXT NOT NULL DEFAULT 'commercial'
        CHECK (row_kind IN ('commercial','custom_tape')),
    source_group TEXT,
    artist_search TEXT,
    title_search TEXT,
    resolution_status TEXT NOT NULL DEFAULT 'unresolved'
        CHECK (resolution_status IN ('unresolved','probable','resolved',
                                     'ambiguous','non_commercial')),
    release_id TEXT,
    resolution_notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_dad_sources_status ON dad_sources(resolution_status);

CREATE TABLE IF NOT EXISTS releases (
    release_id TEXT PRIMARY KEY,
    mbid TEXT UNIQUE,
    title TEXT NOT NULL,
    artist TEXT,
    artist_mbid TEXT,
    date_first TEXT,
    country TEXT,
    labels_json TEXT NOT NULL DEFAULT '[]',
    source_provider TEXT NOT NULL DEFAULT 'musicbrainz',
    source_url TEXT,
    retrieved_at TEXT,
    match_score REAL,
    dad_source_id TEXT REFERENCES dad_sources(dad_source_id)
);

CREATE TABLE IF NOT EXISTS songs (
    song_id TEXT PRIMARY KEY,
    canonical_artist TEXT NOT NULL,
    canonical_title TEXT NOT NULL,
    norm_artist TEXT NOT NULL,
    norm_title TEXT NOT NULL,
    recording_variant TEXT,
    first_release_year INTEGER,
    dad_source_count INTEGER NOT NULL DEFAULT 0,
    dad_favorite_source_count INTEGER NOT NULL DEFAULT 0,
    appears_on_dad_favorite_source INTEGER NOT NULL DEFAULT 0,
    curated_tape_known_count INTEGER NOT NULL DEFAULT 0,
    dad_format_count INTEGER NOT NULL DEFAULT 0,
    popularity_method TEXT,
    popularity_score REAL,
    popularity_status TEXT NOT NULL DEFAULT 'not_enriched',
    UNIQUE (norm_artist, norm_title)
);
CREATE INDEX IF NOT EXISTS idx_songs_norm ON songs(norm_artist, norm_title);

CREATE TABLE IF NOT EXISTS release_tracks (
    release_id TEXT NOT NULL REFERENCES releases(release_id) ON DELETE CASCADE,
    disc INTEGER NOT NULL DEFAULT 1,
    track_no INTEGER NOT NULL,
    track_title_printed TEXT NOT NULL,
    song_id TEXT REFERENCES songs(song_id),
    PRIMARY KEY (release_id, disc, track_no)
);

CREATE TABLE IF NOT EXISTS dad_appearances (
    song_id TEXT NOT NULL REFERENCES songs(song_id) ON DELETE CASCADE,
    dad_source_id TEXT NOT NULL REFERENCES dad_sources(dad_source_id),
    release_id TEXT REFERENCES releases(release_id),
    appears_on_dad_favorite_source INTEGER NOT NULL DEFAULT 0,
    certainty TEXT NOT NULL DEFAULT 'probable',
    notes TEXT,
    PRIMARY KEY (song_id, dad_source_id)
);

CREATE TABLE IF NOT EXISTS popularity (
    song_id TEXT NOT NULL REFERENCES songs(song_id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    popularity_score REAL,
    provider_rank INTEGER,
    listeners INTEGER,
    payload_json TEXT NOT NULL DEFAULT '{}',
    retrieved_at TEXT NOT NULL,
    PRIMARY KEY (song_id, provider)
);

CREATE TABLE IF NOT EXISTS annotations (
    song_id TEXT PRIMARY KEY REFERENCES songs(song_id) ON DELETE CASCADE,
    recognition_status TEXT NOT NULL DEFAULT 'unreviewed'
        CHECK (recognition_status IN ('unreviewed','definitely_recognize',
                                      'not_sure','definitely_do_not_recognize')),
    childhood_association TEXT
        CHECK (childhood_association IN ('yes','maybe','no','unknown') OR childhood_association IS NULL),
    listened INTEGER,
    first_reviewed_at TEXT,
    last_listened_at TEXT,
    listening_note TEXT,
    memory_note TEXT,
    musical_features TEXT,
    possible_influence_note TEXT,
    influence_confidence TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS search_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage TEXT NOT NULL,
    dad_source_id TEXT,
    detail TEXT NOT NULL,
    logged_at TEXT NOT NULL
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
