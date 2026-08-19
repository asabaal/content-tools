"""SQLite catalog for Calvary Spokane archive inventory and crawl history."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .models import (
    ARCHIVE_STATUSES,
    STATUS_AUDIO_ONLY,
    STATUS_DISCOVERED,
    STATUS_DOWNLOADED,
    STATUS_DOWNLOADING,
    STATUS_FAILED,
    STATUS_METADATA_COMPLETE,
    STATUS_NEEDS_REVIEW,
    STATUS_NO_MEDIA,
    STATUS_QUEUED,
    STATUS_VERIFIED,
    SermonRecord,
    normalize_status,
)
from .utils import canonicalize_url, parse_sermon_date, sha256_file, utc_timestamp


class ArchiveDBError(RuntimeError):
    """Base exception for catalog operations."""


class SermonNotFound(ArchiveDBError):
    """Raised when an operation references an unknown sermon ID."""


class InvalidStatusTransition(ArchiveDBError):
    """Raised when a lifecycle transition would skip a required state."""


class RetryLimitExceeded(ArchiveDBError):
    """Raised by strict retry callers after the configured limit."""


LEGAL_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    STATUS_DISCOVERED: frozenset(
        {STATUS_METADATA_COMPLETE, STATUS_NO_MEDIA, STATUS_FAILED, STATUS_NEEDS_REVIEW}
    ),
    STATUS_METADATA_COMPLETE: frozenset(
        {STATUS_QUEUED, STATUS_AUDIO_ONLY, STATUS_NO_MEDIA, STATUS_FAILED, STATUS_NEEDS_REVIEW}
    ),
    STATUS_QUEUED: frozenset(
        {STATUS_DOWNLOADING, STATUS_METADATA_COMPLETE, STATUS_FAILED, STATUS_NEEDS_REVIEW}
    ),
    STATUS_DOWNLOADING: frozenset(
        {STATUS_DOWNLOADED, STATUS_AUDIO_ONLY, STATUS_FAILED, STATUS_NEEDS_REVIEW}
    ),
    STATUS_DOWNLOADED: frozenset(
        {STATUS_VERIFIED, STATUS_AUDIO_ONLY, STATUS_FAILED, STATUS_NEEDS_REVIEW}
    ),
    STATUS_VERIFIED: frozenset({STATUS_DOWNLOADED, STATUS_NEEDS_REVIEW}),
    STATUS_AUDIO_ONLY: frozenset(
        {STATUS_QUEUED, STATUS_VERIFIED, STATUS_FAILED, STATUS_NEEDS_REVIEW}
    ),
    STATUS_NO_MEDIA: frozenset(
        {STATUS_DISCOVERED, STATUS_METADATA_COMPLETE, STATUS_NEEDS_REVIEW}
    ),
    STATUS_FAILED: frozenset(
        {STATUS_QUEUED, STATUS_METADATA_COMPLETE, STATUS_NO_MEDIA, STATUS_NEEDS_REVIEW}
    ),
    STATUS_NEEDS_REVIEW: frozenset(
        {
            STATUS_DISCOVERED,
            STATUS_METADATA_COMPLETE,
            STATUS_QUEUED,
            STATUS_DOWNLOADED,
            STATUS_VERIFIED,
            STATUS_AUDIO_ONLY,
            STATUS_NO_MEDIA,
            STATUS_FAILED,
        }
    ),
}

_METADATA_FIELDS = (
    "platform",
    "source_platform",
    "item_id",
    "platform_item_id",
    "series_id",
    "platform_series_id",
    "title",
    "speaker",
    "sermon_date",
    "year",
    "series",
    "scripture",
    "scripture_reference",
    "bible_book",
    "book_of_bible",
    "topic",
    "service_type",
    "description",
    "duration_seconds",
    "has_video",
    "has_audio",
    "canonical_url",
    "source_url",
    "series_url",
    "media_url",
    "audio_url",
    "audio_source_url",
    "video_url",
    "video_source_url",
    "thumbnail_url",
    "original_media_filename",
    "media_type",
    "media_format",
    "mime_type",
    "in_scope",
    "notes",
)
_IDENTITY_FIELDS = {
    "platform",
    "item_id",
    "platform_item_id",
    "series_id",
    "platform_series_id",
}
_LOCAL_FACT_FIELDS = (
    "local_path",
    "local_media_path",
    "audio_path",
    "video_path",
    "filename",
    "file_size_bytes",
    "filesize",
    "sha256",
    "download_attempts",
    "max_retries",
    "last_error",
    "error",
    "next_retry_at",
    "queued_at",
    "download_started_at",
    "downloaded_at",
    "verified_at",
)

_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS series (
    series_id TEXT PRIMARY KEY,
    platform TEXT,
    platform_series_id TEXT,
    short_code TEXT,
    title TEXT,
    canonical_url TEXT,
    description TEXT,
    advertised_count INTEGER,
    raw_metadata TEXT NOT NULL DEFAULT '{{}}',
    discovered_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_series_platform_identifier
    ON series(platform, platform_series_id)
    WHERE platform IS NOT NULL AND platform_series_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_series_title ON series(title COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS sermons (
    sermon_id TEXT PRIMARY KEY,
    platform TEXT,
    source_platform TEXT,
    item_id TEXT,
    platform_item_id TEXT,
    series_id TEXT REFERENCES series(series_id) ON UPDATE CASCADE ON DELETE SET NULL,
    platform_series_id TEXT,
    title TEXT NOT NULL DEFAULT '',
    speaker TEXT,
    sermon_date TEXT,
    year INTEGER,
    series TEXT,
    scripture TEXT,
    scripture_reference TEXT,
    bible_book TEXT,
    book_of_bible TEXT,
    topic TEXT,
    description TEXT,
    service_type TEXT,
    duration_seconds INTEGER CHECK(duration_seconds IS NULL OR duration_seconds >= 0),
    has_video INTEGER NOT NULL DEFAULT 0,
    has_audio INTEGER NOT NULL DEFAULT 0,
    canonical_url TEXT,
    source_url TEXT,
    series_url TEXT,
    media_url TEXT,
    audio_url TEXT,
    audio_source_url TEXT,
    video_url TEXT,
    video_source_url TEXT,
    thumbnail_url TEXT,
    original_media_filename TEXT,
    media_type TEXT,
    media_format TEXT,
    mime_type TEXT,
    status TEXT NOT NULL DEFAULT '{STATUS_DISCOVERED}'
        CHECK(status IN ({", ".join(repr(status) for status in sorted(ARCHIVE_STATUSES))})),
    download_status TEXT,
    in_scope INTEGER NOT NULL DEFAULT 1,
    local_path TEXT,
    local_media_path TEXT,
    audio_path TEXT,
    video_path TEXT,
    filename TEXT,
    file_size_bytes INTEGER CHECK(file_size_bytes IS NULL OR file_size_bytes >= 0),
    filesize INTEGER CHECK(filesize IS NULL OR filesize >= 0),
    sha256 TEXT,
    download_attempts INTEGER NOT NULL DEFAULT 0 CHECK(download_attempts >= 0),
    max_retries INTEGER NOT NULL DEFAULT 3 CHECK(max_retries >= 0),
    last_error TEXT,
    error TEXT,
    next_retry_at TEXT,
    discovered_at TEXT NOT NULL,
    metadata_updated_at TEXT NOT NULL,
    queued_at TEXT,
    download_started_at TEXT,
    downloaded_at TEXT,
    verified_at TEXT,
    updated_at TEXT NOT NULL,
    notes TEXT,
    raw_metadata TEXT NOT NULL DEFAULT '{{}}',
    raw_metadata_json TEXT NOT NULL DEFAULT '{{}}'
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_sermons_platform_item
    ON sermons(platform, platform_item_id)
    WHERE platform IS NOT NULL AND platform_item_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sermons_canonical_url
    ON sermons(canonical_url) WHERE canonical_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sermons_date ON sermons(sermon_date);
CREATE INDEX IF NOT EXISTS idx_sermons_status_date ON sermons(status, sermon_date);
CREATE INDEX IF NOT EXISTS idx_sermons_exact_metadata
    ON sermons(sermon_date, title COLLATE NOCASE, speaker COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_sermons_media_url ON sermons(media_url);
CREATE INDEX IF NOT EXISTS idx_sermons_series ON sermons(series_id);

CREATE TABLE IF NOT EXISTS sermon_sources (
    source_id TEXT PRIMARY KEY,
    sermon_id TEXT NOT NULL REFERENCES sermons(sermon_id) ON UPDATE CASCADE ON DELETE CASCADE,
    source_platform TEXT NOT NULL,
    platform_item_id TEXT,
    source_url TEXT,
    archived_source_url TEXT,
    listing_url TEXT,
    archived_listing_url TEXT,
    series_url TEXT,
    audio_url TEXT,
    audio_available INTEGER,
    audio_status_code INTEGER,
    video_url TEXT,
    video_available INTEGER,
    video_status_code INTEGER,
    discovered_at TEXT NOT NULL,
    checked_at TEXT,
    updated_at TEXT NOT NULL,
    notes TEXT,
    raw_metadata TEXT NOT NULL DEFAULT '{{}}'
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_sermon_sources_platform_item
    ON sermon_sources(source_platform, platform_item_id, sermon_id)
    WHERE platform_item_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sermon_sources_sermon
    ON sermon_sources(sermon_id, source_platform);

CREATE TABLE IF NOT EXISTS crawl_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TEXT NOT NULL,
    completed_at TEXT,
    pages_seen INTEGER NOT NULL DEFAULT 0,
    items_seen INTEGER NOT NULL DEFAULT 0,
    items_added INTEGER NOT NULL DEFAULT 0,
    items_updated INTEGER NOT NULL DEFAULT 0,
    series_found INTEGER NOT NULL DEFAULT 0,
    item_pages INTEGER NOT NULL DEFAULT 0,
    api_records INTEGER NOT NULL DEFAULT 0,
    target_records INTEGER NOT NULL DEFAULT 0,
    missing_date_records INTEGER NOT NULL DEFAULT 0,
    out_of_range_records INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    metadata TEXT NOT NULL DEFAULT '{{}}'
);

CREATE TABLE IF NOT EXISTS listing_audit (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES crawl_runs(run_id) ON DELETE CASCADE,
    listing_url TEXT NOT NULL,
    page_number INTEGER,
    expected_count INTEGER,
    observed_count INTEGER NOT NULL,
    item_ids TEXT NOT NULL DEFAULT '[]',
    observed_at TEXT NOT NULL,
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_listing_audit_run ON listing_audit(run_id, page_number);

CREATE TABLE IF NOT EXISTS legacy_media_assets (
    media_id TEXT PRIMARY KEY,
    media_url TEXT NOT NULL UNIQUE,
    normalized_url TEXT NOT NULL,
    source_root TEXT NOT NULL,
    parent_index_url TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    media_kind TEXT NOT NULL CHECK(media_kind IN ('audio', 'video')),
    extension TEXT NOT NULL,
    listed_last_modified TEXT,
    listed_size TEXT,
    first_discovered_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    ffprobe_metadata TEXT NOT NULL DEFAULT '{{}}',
    probed_at TEXT,
    probe_error TEXT
);
CREATE INDEX IF NOT EXISTS idx_legacy_media_assets_normalized_url
    ON legacy_media_assets(normalized_url);
CREATE INDEX IF NOT EXISTS idx_legacy_media_assets_filename
    ON legacy_media_assets(filename COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS legacy_media_observations (
    run_id INTEGER NOT NULL REFERENCES crawl_runs(run_id) ON DELETE CASCADE,
    media_id TEXT NOT NULL REFERENCES legacy_media_assets(media_id) ON DELETE CASCADE,
    parent_index_url TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    PRIMARY KEY(run_id, media_id)
);
CREATE INDEX IF NOT EXISTS idx_legacy_media_observations_media
    ON legacy_media_observations(media_id, run_id);

CREATE TABLE IF NOT EXISTS legacy_media_matches (
    match_id TEXT PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES crawl_runs(run_id) ON DELETE CASCADE,
    media_id TEXT NOT NULL REFERENCES legacy_media_assets(media_id) ON DELETE CASCADE,
    sermon_id TEXT REFERENCES sermons(sermon_id) ON DELETE CASCADE,
    classification TEXT NOT NULL,
    match_rule TEXT NOT NULL,
    confidence TEXT NOT NULL,
    evidence TEXT NOT NULL DEFAULT '{{}}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_legacy_media_matches_run
    ON legacy_media_matches(run_id, classification, media_id);
CREATE INDEX IF NOT EXISTS idx_legacy_media_matches_sermon
    ON legacy_media_matches(sermon_id, media_id);

CREATE TABLE IF NOT EXISTS status_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sermon_id TEXT NOT NULL REFERENCES sermons(sermon_id) ON DELETE CASCADE,
    from_status TEXT,
    to_status TEXT NOT NULL,
    event_at TEXT NOT NULL,
    error TEXT,
    details TEXT NOT NULL DEFAULT '{{}}'
);
CREATE INDEX IF NOT EXISTS idx_status_events_sermon
    ON status_events(sermon_id, event_id);
"""

_REQUIRED_COLUMNS: dict[str, dict[str, str]] = {
    "series": {
        "short_code": "TEXT",
        "advertised_count": "INTEGER",
    },
    "crawl_runs": {
        "series_found": "INTEGER NOT NULL DEFAULT 0",
        "item_pages": "INTEGER NOT NULL DEFAULT 0",
        "api_records": "INTEGER NOT NULL DEFAULT 0",
        "target_records": "INTEGER NOT NULL DEFAULT 0",
        "missing_date_records": "INTEGER NOT NULL DEFAULT 0",
        "out_of_range_records": "INTEGER NOT NULL DEFAULT 0",
    },
    "sermons": {
        "source_platform": "TEXT",
        "year": "INTEGER",
        "scripture_reference": "TEXT",
        "bible_book": "TEXT",
        "book_of_bible": "TEXT",
        "topic": "TEXT",
        "service_type": "TEXT",
        "has_video": "INTEGER NOT NULL DEFAULT 0",
        "has_audio": "INTEGER NOT NULL DEFAULT 0",
        "series_url": "TEXT",
        "audio_source_url": "TEXT",
        "video_source_url": "TEXT",
        "original_media_filename": "TEXT",
        "download_status": "TEXT",
        "in_scope": "INTEGER NOT NULL DEFAULT 1",
        "local_media_path": "TEXT",
        "media_format": "TEXT",
        "filesize": "INTEGER",
        "error": "TEXT",
        "raw_metadata_json": "TEXT NOT NULL DEFAULT '{}'",
    },
}


class ArchiveDB:
    """Persistent SQLite inventory.

    ``db_path`` is intentionally required.  Production callers should pass the
    canonical ``<archive_root>/data/sermons.sqlite`` path; tests may pass
    ``:memory:`` or a temporary file.  Methods can be used directly or through
    ``with ArchiveDB(path) as db``.  The context manager closes the connection.
    """

    def __init__(self, db_path: str | os.PathLike[str], *, timeout: float = 30.0) -> None:
        raw_path = os.fspath(db_path)
        if not raw_path:
            raise ValueError("db_path must not be empty")
        self.path: str | Path = ":memory:" if raw_path == ":memory:" else Path(raw_path)
        self.timeout = timeout
        self._connection: sqlite3.Connection | None = None
        self._lock = threading.RLock()

    def connect(self) -> sqlite3.Connection:
        """Open and initialize the database, returning the shared connection."""

        with self._lock:
            if self._connection is not None:
                return self._connection
            if isinstance(self.path, Path):
                self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(
                os.fspath(self.path),
                timeout=self.timeout,
                isolation_level=None,
            )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 30000")
            if self.path != ":memory:":
                connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(_SCHEMA)
            self._migrate_schema(connection)
            self._connection = connection
            return connection

    @staticmethod
    def _migrate_schema(connection: sqlite3.Connection) -> None:
        """Add newly normalized audit columns without discarding existing archives."""

        for table, columns in _REQUIRED_COLUMNS.items():
            existing = {
                str(row[1])
                for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
            }
            for column, declaration in columns.items():
                if column not in existing:
                    connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")
        connection.execute("DROP INDEX IF EXISTS uq_sermons_canonical_url")
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_sermons_canonical_url "
            "ON sermons(canonical_url) WHERE canonical_url IS NOT NULL"
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_sermons_year ON sermons(year)")
        connection.execute(
            """UPDATE sermons SET
                source_platform = COALESCE(source_platform, platform),
                year = COALESCE(year, CAST(substr(sermon_date, 1, 4) AS INTEGER)),
                scripture_reference = COALESCE(scripture_reference, scripture),
                bible_book = COALESCE(bible_book, book_of_bible),
                book_of_bible = COALESCE(book_of_bible, bible_book),
                has_video = CASE WHEN video_source_url IS NOT NULL OR video_url IS NOT NULL THEN 1 ELSE has_video END,
                has_audio = CASE WHEN audio_source_url IS NOT NULL OR audio_url IS NOT NULL THEN 1 ELSE has_audio END,
                audio_source_url = COALESCE(audio_source_url, audio_url),
                video_source_url = COALESCE(video_source_url, video_url),
                download_status = COALESCE(download_status, status),
                local_media_path = COALESCE(local_media_path, local_path),
                filesize = COALESCE(filesize, file_size_bytes),
                error = COALESCE(error, last_error),
                raw_metadata_json = CASE WHEN raw_metadata_json = '{}' THEN raw_metadata ELSE raw_metadata_json END
            """
        )

    def initialize(self) -> "ArchiveDB":
        """Create missing tables/indexes and return ``self`` for chaining."""

        self.connect()
        return self

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the initialized SQLite connection."""

        return self.connect()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Run a write transaction, rolling back on any exception."""

        connection = self.connect()
        with self._lock:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except BaseException:
                connection.rollback()
                raise
            else:
                connection.commit()

    def close(self) -> None:
        """Close the current connection; a later method call may reopen it."""

        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    def __enter__(self) -> "ArchiveDB":
        self.connect()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._connection is not None and exc is not None:
            self._connection.rollback()
        self.close()

    @staticmethod
    def _json_dump(value: Any, default: Any) -> str:
        payload = default if value is None else value
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _json_object(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        if isinstance(value, Mapping):
            return dict(value)
        if isinstance(value, str):
            try:
                decoded = json.loads(value)
            except json.JSONDecodeError:
                return {"value": value}
            return decoded if isinstance(decoded, dict) else {"value": decoded}
        return {} if value is None else {"value": value}

    @classmethod
    def _row_to_record(cls, row: sqlite3.Row | None) -> SermonRecord | None:
        if row is None:
            return None
        values = dict(row)
        values["raw_metadata"] = cls._json_object(values.get("raw_metadata"))
        return SermonRecord.from_mapping(values)

    @staticmethod
    def _clean_record(record: SermonRecord) -> dict[str, Any]:
        values = record.to_dict()
        for key, value in tuple(values.items()):
            if isinstance(value, str):
                stripped = value.strip()
                values[key] = stripped if stripped else None
        values["sermon_id"] = record.sermon_id
        values["title"] = (record.title or "").strip()
        # Canonicalize only the comparison URL. Source and media URLs are
        # provenance/transfer facts; reordering or dropping their query values can
        # invalidate signed public resources.
        values["canonical_url"] = canonicalize_url(values.get("canonical_url"))
        values["source_platform"] = values.get("source_platform") or values.get("platform")
        values["year"] = values.get("year") or (
            int(values["sermon_date"][:4]) if values.get("sermon_date") else None
        )
        values["scripture_reference"] = values.get("scripture_reference") or values.get("scripture")
        values["book_of_bible"] = values.get("book_of_bible") or values.get("bible_book")
        values["bible_book"] = values.get("bible_book") or values.get("book_of_bible")
        values["audio_source_url"] = values.get("audio_source_url") or values.get("audio_url")
        values["video_source_url"] = values.get("video_source_url") or values.get("video_url")
        values["has_audio"] = int(bool(values.get("has_audio") or values.get("audio_source_url")))
        values["has_video"] = int(bool(values.get("has_video") or values.get("video_source_url")))
        values["original_media_filename"] = values.get("original_media_filename") or values.get("original_filename")
        values["download_status"] = values.get("status")
        values["in_scope"] = int(bool(values.get("in_scope", True)))
        values["local_media_path"] = values.get("local_media_path") or values.get("local_path")
        values["filesize"] = values.get("filesize") or values.get("file_size_bytes")
        values["error"] = values.get("error") or values.get("last_error")
        return values

    @staticmethod
    def _coerce_record(
        record: SermonRecord | Mapping[str, Any] | None, fields: Mapping[str, Any]
    ) -> SermonRecord:
        if isinstance(record, SermonRecord):
            if fields:
                values = record.to_dict(dates_as_iso=False)
                values.update(fields)
                return SermonRecord.from_mapping(values)
            return record
        values = dict(record or {})
        values.update(fields)
        return SermonRecord.from_mapping(values)

    @staticmethod
    def _ensure_series(connection: sqlite3.Connection, values: Mapping[str, Any], now: str) -> None:
        series_id = values.get("series_id")
        if not series_id:
            return
        connection.execute(
            """
            INSERT INTO series (
                series_id, platform, platform_series_id, title,
                raw_metadata, discovered_at, updated_at
            ) VALUES (?, ?, ?, ?, '{}', ?, ?)
            ON CONFLICT(series_id) DO UPDATE SET
                platform = COALESCE(series.platform, excluded.platform),
                platform_series_id = COALESCE(series.platform_series_id, excluded.platform_series_id),
                title = COALESCE(excluded.title, series.title),
                updated_at = excluded.updated_at
            """,
            (
                series_id,
                values.get("platform"),
                values.get("platform_series_id"),
                values.get("series"),
                now,
                now,
            ),
        )

    @staticmethod
    def _find_duplicate_row(
        connection: sqlite3.Connection,
        values: Mapping[str, Any],
        *,
        exclude_sermon_id: str | None = None,
    ) -> sqlite3.Row | None:
        exclusion = " AND sermon_id <> ?" if exclude_sermon_id else ""
        exclusion_params: tuple[Any, ...] = (exclude_sermon_id,) if exclude_sermon_id else ()
        incoming_platform = values.get("platform")
        incoming_platform_id = values.get("platform_item_id") or values.get("item_id")

        def fallback_allowed(row: sqlite3.Row | None) -> bool:
            if row is None:
                return False
            existing_platform_id = row["platform_item_id"] or row["item_id"]
            same_platform_conflict = (
                incoming_platform
                and incoming_platform_id
                and row["platform"] == incoming_platform
                and existing_platform_id
                and existing_platform_id != incoming_platform_id
            )
            return not same_platform_conflict

        sermon_id = values.get("sermon_id")
        if sermon_id:
            row = connection.execute(
                "SELECT * FROM sermons WHERE sermon_id = ?", (sermon_id,)
            ).fetchone()
            if row is not None:
                return row

        platform = values.get("platform")
        platform_item_id = values.get("platform_item_id") or values.get("item_id")
        if platform and platform_item_id:
            row = connection.execute(
                f"""SELECT * FROM sermons
                    WHERE platform = ? AND (platform_item_id = ? OR item_id = ?){exclusion}
                    ORDER BY sermon_id LIMIT 1""",
                (platform, platform_item_id, platform_item_id, *exclusion_params),
            ).fetchone()
            if row is not None:
                return row

        canonical_url = values.get("canonical_url")
        if canonical_url:
            row = connection.execute(
                f"SELECT * FROM sermons WHERE canonical_url = ?{exclusion} ORDER BY sermon_id LIMIT 1",
                (canonical_url, *exclusion_params),
            ).fetchone()
            if fallback_allowed(row):
                return row

        sermon_date = values.get("sermon_date")
        title = values.get("title")
        speaker = values.get("speaker")
        if sermon_date and title and speaker:
            row = connection.execute(
                f"""SELECT * FROM sermons
                    WHERE sermon_date = ?
                      AND title = ? COLLATE NOCASE
                      AND speaker = ? COLLATE NOCASE{exclusion}
                    ORDER BY sermon_id LIMIT 1""",
                (sermon_date, title, speaker, *exclusion_params),
            ).fetchone()
            if fallback_allowed(row):
                return row

        media_urls = []
        for key in (
            "media_url", "video_url", "video_source_url", "audio_url", "audio_source_url"
        ):
            url = values.get(key)
            if url and url not in media_urls:
                media_urls.append(url)
        for media_url in media_urls:
            row = connection.execute(
                f"""SELECT * FROM sermons
                    WHERE (media_url = ? OR video_url = ? OR video_source_url = ?
                           OR audio_url = ? OR audio_source_url = ?){exclusion}
                    ORDER BY sermon_id LIMIT 1""",
                (media_url, media_url, media_url, media_url, media_url, *exclusion_params),
            ).fetchone()
            if fallback_allowed(row):
                return row
        return None

    def find_duplicate(
        self,
        record: SermonRecord | Mapping[str, Any] | str | None = None,
        **fields: Any,
    ) -> SermonRecord | None:
        """Find an existing row by strong IDs, URL, exact metadata, or media URL.

        Date/title matching is deliberately used only when a non-empty speaker
        also matches.  Title-only and date/title-only guesses are not treated as
        duplicates.
        """

        if isinstance(record, str):
            record = {"sermon_id": record}
        lookup_values = dict(record or {}) if not isinstance(record, SermonRecord) else None
        if lookup_values is not None:
            lookup_values.update(fields)
            lookup_only = not lookup_values.get("sermon_id")
            if lookup_only:
                lookup_values["sermon_id"] = "__duplicate_lookup__"
            normalized = self._coerce_record(lookup_values, {})
            values = self._clean_record(normalized)
            if lookup_only:
                values["sermon_id"] = None
        else:
            normalized = self._coerce_record(record, fields)
            values = self._clean_record(normalized)
        row = self._find_duplicate_row(self.connect(), values)
        return self._row_to_record(row)

    def is_duplicate(
        self, record: SermonRecord | Mapping[str, Any] | str | None = None, **fields: Any
    ) -> bool:
        """Return whether :meth:`find_duplicate` finds a catalog row."""

        return self.find_duplicate(record, **fields) is not None

    def upsert_sermon(
        self,
        record: SermonRecord | Mapping[str, Any] | None = None,
        **fields: Any,
    ) -> SermonRecord:
        """Insert or refresh remote metadata and return the canonical row.

        Existing local paths, checksums, sizes, attempts, errors, and lifecycle
        timestamps are never replaced by a metadata refresh.  A duplicate found
        through a fallback key is merged into the existing canonical sermon ID.
        """

        normalized = self._coerce_record(record, fields)
        values = self._clean_record(normalized)
        now = utc_timestamp()
        values["discovered_at"] = values.get("discovered_at") or now
        values["metadata_updated_at"] = now
        values["updated_at"] = now
        values["raw_metadata"] = self._json_object(values.get("raw_metadata"))

        with self.transaction() as connection:
            existing = self._find_duplicate_row(connection, values)
            canonical_id = existing["sermon_id"] if existing is not None else values["sermon_id"]
            values["sermon_id"] = canonical_id
            self._ensure_series(connection, values, now)

            if existing is None:
                columns = (
                    "sermon_id",
                    "platform",
                    "source_platform",
                    "item_id",
                    "platform_item_id",
                    "series_id",
                    "platform_series_id",
                    "title",
                    "speaker",
                    "sermon_date",
                    "year",
                    "series",
                    "scripture",
                    "scripture_reference",
                    "bible_book",
                    "book_of_bible",
                    "topic",
                    "description",
                    "service_type",
                    "duration_seconds",
                    "has_video",
                    "has_audio",
                    "canonical_url",
                    "source_url",
                    "series_url",
                    "media_url",
                    "audio_url",
                    "audio_source_url",
                    "video_url",
                    "video_source_url",
                    "thumbnail_url",
                    "original_media_filename",
                    "media_type",
                    "media_format",
                    "mime_type",
                    "status",
                    "download_status",
                    "in_scope",
                    *_LOCAL_FACT_FIELDS,
                    "discovered_at",
                    "metadata_updated_at",
                    "updated_at",
                    "notes",
                    "raw_metadata",
                    "raw_metadata_json",
                )
                insert_values = []
                for column in columns:
                    value = values.get(column)
                    if column in {"raw_metadata", "raw_metadata_json"}:
                        value = self._json_dump(values.get("raw_metadata"), {})
                    insert_values.append(value)
                placeholders = ", ".join("?" for _ in columns)
                connection.execute(
                    f"INSERT INTO sermons ({', '.join(columns)}) VALUES ({placeholders})",
                    insert_values,
                )
                connection.execute(
                    """INSERT INTO status_events
                       (sermon_id, from_status, to_status, event_at, details)
                       VALUES (?, NULL, ?, ?, ?)""",
                    (canonical_id, values["status"], now, '{"reason":"discovered"}'),
                )
            else:
                updates: dict[str, Any] = {}
                existing_values = dict(existing)
                existing_platform_id = (
                    existing_values.get("platform_item_id") or existing_values.get("item_id")
                )
                incoming_platform_id = values.get("platform_item_id") or values.get("item_id")
                same_source_identity = bool(
                    existing_values.get("platform") == values.get("platform")
                    and existing_platform_id
                    and existing_platform_id == incoming_platform_id
                )
                for field in _METADATA_FIELDS:
                    incoming = values.get(field)
                    if field in _IDENTITY_FIELDS and existing_values.get(field):
                        continue
                    if field == "title" and not incoming:
                        continue
                    if same_source_identity or incoming is not None:
                        updates[field] = incoming

                incoming_status = values["status"]
                current_status = existing_values["status"]
                has_local_media = bool(
                    existing_values.get("local_media_path") or existing_values.get("local_path")
                )
                protected_status = current_status in {
                    STATUS_QUEUED,
                    STATUS_DOWNLOADING,
                    STATUS_DOWNLOADED,
                    STATUS_VERIFIED,
                    STATUS_FAILED,
                } or (current_status == STATUS_AUDIO_ONLY and has_local_media)
                if not protected_status and incoming_status != current_status:
                    updates["status"] = incoming_status

                old_raw = self._json_object(existing_values.get("raw_metadata"))
                old_raw.update(values["raw_metadata"])
                updates["raw_metadata"] = self._json_dump(old_raw, {})
                updates["raw_metadata_json"] = updates["raw_metadata"]
                updates["download_status"] = updates.get("status", current_status)
                updates["metadata_updated_at"] = now
                updates["updated_at"] = now

                assignments = ", ".join(f"{column} = ?" for column in updates)
                connection.execute(
                    f"UPDATE sermons SET {assignments} WHERE sermon_id = ?",
                    (*updates.values(), canonical_id),
                )
                if updates.get("status") and updates["status"] != current_status:
                    connection.execute(
                        """INSERT INTO status_events
                           (sermon_id, from_status, to_status, event_at, details)
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            canonical_id,
                            current_status,
                            updates["status"],
                            now,
                            '{"reason":"metadata_upsert"}',
                        ),
                    )

            row = connection.execute(
                "SELECT * FROM sermons WHERE sermon_id = ?", (canonical_id,)
            ).fetchone()
        result = self._row_to_record(row)
        assert result is not None
        return result

    def upsert_metadata(
        self, record: SermonRecord | Mapping[str, Any] | None = None, **fields: Any
    ) -> SermonRecord:
        """Alias for :meth:`upsert_sermon`."""

        return self.upsert_sermon(record, **fields)

    def get_sermon(self, sermon_id: str) -> SermonRecord | None:
        """Return one sermon by canonical ID, or ``None``."""

        row = self.connect().execute(
            "SELECT * FROM sermons WHERE sermon_id = ?", (sermon_id,)
        ).fetchone()
        return self._row_to_record(row)

    def upsert_source_evidence(
        self,
        *,
        source_id: str,
        sermon_id: str,
        source_platform: str,
        platform_item_id: str | None = None,
        source_url: str | None = None,
        archived_source_url: str | None = None,
        listing_url: str | None = None,
        archived_listing_url: str | None = None,
        series_url: str | None = None,
        audio_url: str | None = None,
        audio_available: bool | None = None,
        audio_status_code: int | None = None,
        video_url: str | None = None,
        video_available: bool | None = None,
        video_status_code: int | None = None,
        checked_at: str | None = None,
        notes: str | None = None,
        raw_metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Insert or refresh one source-specific provenance record.

        Transfer URLs are stored exactly as observed.  Availability is tri-state:
        ``1`` is publicly reachable, ``0`` was checked and unavailable, and
        ``NULL`` has not been checked.
        """

        source_id = str(source_id).strip()
        source_platform = str(source_platform).strip()
        if not source_id:
            raise ValueError("source_id must not be empty")
        if not source_platform:
            raise ValueError("source_platform must not be empty")
        self.require_sermon(sermon_id)
        now = utc_timestamp()
        with self.transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM sermon_sources WHERE source_id = ?", (source_id,)
            ).fetchone()
            old_raw = self._json_object(existing["raw_metadata"]) if existing else {}
            old_raw.update(dict(raw_metadata or {}))
            discovered_at = existing["discovered_at"] if existing else now
            values = (
                source_id,
                sermon_id,
                source_platform,
                platform_item_id,
                source_url,
                archived_source_url,
                listing_url,
                archived_listing_url,
                series_url,
                audio_url,
                None if audio_available is None else int(audio_available),
                audio_status_code,
                video_url,
                None if video_available is None else int(video_available),
                video_status_code,
                discovered_at,
                checked_at,
                now,
                notes,
                self._json_dump(old_raw, {}),
            )
            connection.execute(
                """
                INSERT INTO sermon_sources (
                    source_id, sermon_id, source_platform, platform_item_id,
                    source_url, archived_source_url, listing_url, archived_listing_url,
                    series_url, audio_url, audio_available, audio_status_code,
                    video_url, video_available, video_status_code, discovered_at,
                    checked_at, updated_at, notes, raw_metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    sermon_id = excluded.sermon_id,
                    source_platform = excluded.source_platform,
                    platform_item_id = COALESCE(excluded.platform_item_id, sermon_sources.platform_item_id),
                    source_url = COALESCE(excluded.source_url, sermon_sources.source_url),
                    archived_source_url = COALESCE(excluded.archived_source_url, sermon_sources.archived_source_url),
                    listing_url = COALESCE(excluded.listing_url, sermon_sources.listing_url),
                    archived_listing_url = COALESCE(excluded.archived_listing_url, sermon_sources.archived_listing_url),
                    series_url = COALESCE(excluded.series_url, sermon_sources.series_url),
                    audio_url = COALESCE(excluded.audio_url, sermon_sources.audio_url),
                    audio_available = COALESCE(excluded.audio_available, sermon_sources.audio_available),
                    audio_status_code = COALESCE(excluded.audio_status_code, sermon_sources.audio_status_code),
                    video_url = COALESCE(excluded.video_url, sermon_sources.video_url),
                    video_available = COALESCE(excluded.video_available, sermon_sources.video_available),
                    video_status_code = COALESCE(excluded.video_status_code, sermon_sources.video_status_code),
                    checked_at = COALESCE(excluded.checked_at, sermon_sources.checked_at),
                    updated_at = excluded.updated_at,
                    notes = COALESCE(excluded.notes, sermon_sources.notes),
                    raw_metadata = excluded.raw_metadata
                """,
                values,
            )
            row = connection.execute(
                "SELECT * FROM sermon_sources WHERE source_id = ?", (source_id,)
            ).fetchone()
        result = dict(row)
        result["raw_metadata"] = self._json_object(result["raw_metadata"])
        return result

    def list_source_evidence(self, sermon_id: str | None = None) -> list[dict[str, Any]]:
        """Return source-specific provenance ordered by sermon and source ID."""

        parameters: tuple[Any, ...] = ()
        where = ""
        if sermon_id is not None:
            where = " WHERE sermon_id = ?"
            parameters = (sermon_id,)
        rows = self.connect().execute(
            f"SELECT * FROM sermon_sources{where} ORDER BY sermon_id, source_platform, source_id",
            parameters,
        ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            values = dict(row)
            values["raw_metadata"] = self._json_object(values["raw_metadata"])
            result.append(values)
        return result

    def upsert_legacy_media_asset(
        self, asset: Mapping[str, Any], *, run_id: int
    ) -> tuple[dict[str, Any], bool]:
        """Persist one file exposed by a public legacy-media directory index.

        The exact transfer URL is retained separately from ``normalized_url``,
        which exists only for cross-source comparisons. Probe metadata survives
        later index crawls until the file is explicitly probed again.
        """

        required = (
            "media_id",
            "media_url",
            "normalized_url",
            "source_root",
            "parent_index_url",
            "relative_path",
            "filename",
            "media_kind",
            "extension",
        )
        values = {key: asset.get(key) for key in required}
        missing = [key for key, value in values.items() if not str(value or "").strip()]
        if missing:
            raise ValueError(f"legacy media asset is missing: {', '.join(missing)}")
        if values["media_kind"] not in {"audio", "video"}:
            raise ValueError("legacy media kind must be audio or video")

        now = utc_timestamp()
        with self.transaction() as connection:
            existing = connection.execute(
                "SELECT media_id FROM legacy_media_assets WHERE media_id = ?",
                (values["media_id"],),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO legacy_media_assets (
                    media_id, media_url, normalized_url, source_root,
                    parent_index_url, relative_path, filename, media_kind,
                    extension, listed_last_modified, listed_size,
                    first_discovered_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(media_id) DO UPDATE SET
                    media_url = excluded.media_url,
                    normalized_url = excluded.normalized_url,
                    source_root = excluded.source_root,
                    parent_index_url = excluded.parent_index_url,
                    relative_path = excluded.relative_path,
                    filename = excluded.filename,
                    media_kind = excluded.media_kind,
                    extension = excluded.extension,
                    listed_last_modified = COALESCE(
                        excluded.listed_last_modified,
                        legacy_media_assets.listed_last_modified
                    ),
                    listed_size = COALESCE(excluded.listed_size, legacy_media_assets.listed_size),
                    last_seen_at = excluded.last_seen_at
                """,
                (
                    values["media_id"],
                    values["media_url"],
                    values["normalized_url"],
                    values["source_root"],
                    values["parent_index_url"],
                    values["relative_path"],
                    values["filename"],
                    values["media_kind"],
                    values["extension"],
                    asset.get("listed_last_modified"),
                    asset.get("listed_size"),
                    now,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO legacy_media_observations
                    (run_id, media_id, parent_index_url, observed_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(run_id, media_id) DO UPDATE SET
                    parent_index_url = excluded.parent_index_url,
                    observed_at = excluded.observed_at
                """,
                (run_id, values["media_id"], values["parent_index_url"], now),
            )
            row = connection.execute(
                "SELECT * FROM legacy_media_assets WHERE media_id = ?",
                (values["media_id"],),
            ).fetchone()
        assert row is not None
        result = dict(row)
        result["ffprobe_metadata"] = self._json_object(result["ffprobe_metadata"])
        return result, existing is None

    def set_legacy_media_probe(
        self,
        media_id: str,
        *,
        metadata: Mapping[str, Any] | None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Store the latest bounded metadata probe for one exposed media file."""

        now = utc_timestamp()
        with self.transaction() as connection:
            connection.execute(
                """UPDATE legacy_media_assets
                   SET ffprobe_metadata = ?, probed_at = ?, probe_error = ?
                   WHERE media_id = ?""",
                (self._json_dump(metadata, {}), now, error, media_id),
            )
            row = connection.execute(
                "SELECT * FROM legacy_media_assets WHERE media_id = ?", (media_id,)
            ).fetchone()
            if row is None:
                raise ArchiveDBError(f"unknown legacy media asset: {media_id}")
        result = dict(row)
        result["ffprobe_metadata"] = self._json_object(result["ffprobe_metadata"])
        return result

    def replace_legacy_media_matches(
        self,
        *,
        run_id: int,
        media_id: str,
        matches: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Replace one run's classifications for an exposed media file."""

        now = utc_timestamp()
        prepared = [dict(match) for match in matches]
        if not prepared:
            raise ValueError("at least one legacy media match classification is required")
        with self.transaction() as connection:
            connection.execute(
                "DELETE FROM legacy_media_matches WHERE run_id = ? AND media_id = ?",
                (run_id, media_id),
            )
            for match in prepared:
                connection.execute(
                    """
                    INSERT INTO legacy_media_matches (
                        match_id, run_id, media_id, sermon_id, classification,
                        match_rule, confidence, evidence, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        match["match_id"],
                        run_id,
                        media_id,
                        match.get("sermon_id"),
                        match["classification"],
                        match["match_rule"],
                        match["confidence"],
                        self._json_dump(match.get("evidence"), {}),
                        now,
                        now,
                    ),
                )
            rows = connection.execute(
                """SELECT * FROM legacy_media_matches
                   WHERE run_id = ? AND media_id = ? ORDER BY match_id""",
                (run_id, media_id),
            ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            values = dict(row)
            values["evidence"] = self._json_object(values["evidence"])
            results.append(values)
        return results

    def attach_public_media(
        self,
        sermon_id: str,
        *,
        media_kind: str,
        media_url: str,
        media_format: str | None = None,
        duration_seconds: int | None = None,
        evidence: Mapping[str, Any] | None = None,
        replace_existing: bool = False,
    ) -> SermonRecord:
        """Attach a currently verified public file.

        ``replace_existing`` is reserved for a stronger exact source match that
        proves the canonical remote-media assignment is wrong.  Local download
        facts and protected lifecycle states remain untouched.
        """

        if media_kind not in {"audio", "video"}:
            raise ValueError("media_kind must be audio or video")
        self.require_sermon(sermon_id)
        now = utc_timestamp()
        with self.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM sermons WHERE sermon_id = ?", (sermon_id,)
            ).fetchone()
            assert row is not None
            existing = dict(row)
            current_status = str(existing["status"])
            protected_status = current_status in {
                STATUS_QUEUED,
                STATUS_DOWNLOADING,
                STATUS_DOWNLOADED,
                STATUS_VERIFIED,
                STATUS_FAILED,
            } or bool(existing.get("local_media_path") or existing.get("local_path"))
            updates: dict[str, Any] = {
                f"has_{media_kind}": 1,
                f"{media_kind}_url": media_url,
                f"{media_kind}_source_url": media_url,
                "media_format": media_format or existing.get("media_format"),
                "original_media_filename": (
                    Path(urlparse(media_url).path).name
                    if replace_existing
                    else existing.get("original_media_filename")
                    or Path(urlparse(media_url).path).name
                ),
                "metadata_updated_at": now,
                "updated_at": now,
            }
            if replace_existing or not existing.get("media_url") or media_kind == "video":
                updates["media_url"] = media_url
            if duration_seconds is not None and not existing.get("duration_seconds"):
                updates["duration_seconds"] = max(0, int(duration_seconds))
            has_audio = bool(existing.get("has_audio")) or media_kind == "audio"
            has_video = bool(existing.get("has_video")) or media_kind == "video"
            updates["media_type"] = (
                "audio_video" if has_audio and has_video else "video" if has_video else "audio"
            )
            if not protected_status:
                new_status = STATUS_METADATA_COMPLETE if has_video else STATUS_AUDIO_ONLY
                updates["status"] = new_status
                updates["download_status"] = new_status
            raw = self._json_object(existing.get("raw_metadata"))
            raw.setdefault("legacy_media_recoveries", []).append(dict(evidence or {}))
            updates["raw_metadata"] = self._json_dump(raw, {})
            updates["raw_metadata_json"] = updates["raw_metadata"]
            assignments = ", ".join(f"{column} = ?" for column in updates)
            connection.execute(
                f"UPDATE sermons SET {assignments} WHERE sermon_id = ?",
                (*updates.values(), sermon_id),
            )
            if updates.get("status") and updates["status"] != current_status:
                connection.execute(
                    """INSERT INTO status_events
                       (sermon_id, from_status, to_status, event_at, details)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        sermon_id,
                        current_status,
                        updates["status"],
                        now,
                        self._json_dump({"reason": "legacy_media_recovery"}, {}),
                    ),
                )
            updated = connection.execute(
                "SELECT * FROM sermons WHERE sermon_id = ?", (sermon_id,)
            ).fetchone()
        result = self._row_to_record(updated)
        assert result is not None
        return result

    def require_sermon(self, sermon_id: str) -> SermonRecord:
        """Return one sermon, raising :class:`SermonNotFound` if absent."""

        record = self.get_sermon(sermon_id)
        if record is None:
            raise SermonNotFound(f"unknown sermon_id: {sermon_id}")
        return record

    get_by_id = get_sermon

    @staticmethod
    def _filter_sql(
        *,
        status: str | None = None,
        statuses: Iterable[str] | None = None,
        start_date: date | datetime | str | None = None,
        end_date: date | datetime | str | None = None,
        speaker: str | None = None,
        series_id: str | None = None,
        platform: str | None = None,
        query: str | None = None,
    ) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if status is not None and statuses is not None:
            raise ValueError("pass status or statuses, not both")
        if status is not None:
            clauses.append("status = ?")
            parameters.append(normalize_status(status))
        if statuses is not None:
            normalized_statuses = sorted({normalize_status(value) for value in statuses})
            if not normalized_statuses:
                clauses.append("0")
            else:
                clauses.append(f"status IN ({', '.join('?' for _ in normalized_statuses)})")
                parameters.extend(normalized_statuses)

        for column, raw_bound, operator in (
            ("sermon_date", start_date, ">="),
            ("sermon_date", end_date, "<="),
        ):
            if raw_bound is None:
                continue
            parsed = parse_sermon_date(raw_bound)
            if parsed is None:
                raise ValueError(f"invalid date bound: {raw_bound!r}")
            clauses.append(f"{column} {operator} ?")
            parameters.append(parsed.isoformat())
        if start_date is not None and end_date is not None:
            parsed_start = parse_sermon_date(start_date)
            parsed_end = parse_sermon_date(end_date)
            if parsed_start is not None and parsed_end is not None and parsed_start > parsed_end:
                clauses.append("0")

        if speaker:
            clauses.append("speaker = ? COLLATE NOCASE")
            parameters.append(speaker.strip())
        if series_id:
            clauses.append("series_id = ?")
            parameters.append(series_id)
        if platform:
            clauses.append("platform = ?")
            parameters.append(platform)
        if query:
            clauses.append("(title LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\')")
            escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            parameters.extend((f"%{escaped}%", f"%{escaped}%"))
        return (" WHERE " + " AND ".join(clauses) if clauses else "", parameters)

    def list_sermons(
        self,
        *,
        status: str | None = None,
        statuses: Iterable[str] | None = None,
        start_date: date | datetime | str | None = None,
        end_date: date | datetime | str | None = None,
        speaker: str | None = None,
        series_id: str | None = None,
        platform: str | None = None,
        query: str | None = None,
        limit: int | None = None,
        offset: int = 0,
        newest_first: bool = False,
    ) -> list[SermonRecord]:
        """List sermons using inclusive dates and optional metadata/status filters."""

        where, parameters = self._filter_sql(
            status=status,
            statuses=statuses,
            start_date=start_date,
            end_date=end_date,
            speaker=speaker,
            series_id=series_id,
            platform=platform,
            query=query,
        )
        direction = "DESC" if newest_first else "ASC"
        sql = (
            f"SELECT * FROM sermons{where} "
            f"ORDER BY sermon_date IS NULL, sermon_date {direction}, title COLLATE NOCASE, sermon_id"
        )
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            sql += " LIMIT ? OFFSET ?"
            parameters.extend((limit, max(0, offset)))
        elif offset:
            sql += " LIMIT -1 OFFSET ?"
            parameters.append(max(0, offset))
        rows = self.connect().execute(sql, parameters).fetchall()
        return [record for row in rows if (record := self._row_to_record(row)) is not None]

    filter_sermons = list_sermons

    def count_sermons(
        self,
        *,
        status: str | None = None,
        statuses: Iterable[str] | None = None,
        start_date: date | datetime | str | None = None,
        end_date: date | datetime | str | None = None,
        speaker: str | None = None,
        series_id: str | None = None,
        platform: str | None = None,
        query: str | None = None,
    ) -> int:
        """Count sermons using the same filters as :meth:`list_sermons`."""

        where, parameters = self._filter_sql(
            status=status,
            statuses=statuses,
            start_date=start_date,
            end_date=end_date,
            speaker=speaker,
            series_id=series_id,
            platform=platform,
            query=query,
        )
        row = self.connect().execute(f"SELECT COUNT(*) FROM sermons{where}", parameters).fetchone()
        return int(row[0])

    def counts_by_status(self) -> dict[str, int]:
        """Return all lifecycle states with zero-filled counts."""

        counts = {status: 0 for status in sorted(ARCHIVE_STATUSES)}
        rows = self.connect().execute(
            "SELECT status, COUNT(*) AS count FROM sermons GROUP BY status"
        ).fetchall()
        counts.update({row["status"]: int(row["count"]) for row in rows})
        return counts

    @staticmethod
    def can_transition(current_status: str, new_status: str) -> bool:
        """Return whether a lifecycle edge is legal (same-state is idempotent)."""

        current = normalize_status(current_status)
        new = normalize_status(new_status)
        return current == new or new in LEGAL_STATUS_TRANSITIONS[current]

    @staticmethod
    def _transition_row(
        connection: sqlite3.Connection,
        sermon_id: str,
        new_status: str,
        *,
        error: str | None = None,
        details: Mapping[str, Any] | None = None,
        increment_attempt: bool = False,
        updates: Mapping[str, Any] | None = None,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM sermons WHERE sermon_id = ?", (sermon_id,)
        ).fetchone()
        if row is None:
            raise SermonNotFound(f"unknown sermon_id: {sermon_id}")
        current_status = row["status"]
        target_status = normalize_status(new_status)
        if not ArchiveDB.can_transition(current_status, target_status):
            raise InvalidStatusTransition(
                f"illegal sermon status transition: {current_status} -> {target_status}"
            )

        now = utc_timestamp()
        changed: dict[str, Any] = dict(updates or {})
        changed["status"] = target_status
        changed["download_status"] = target_status
        changed["updated_at"] = now
        timestamp_columns = {
            STATUS_QUEUED: "queued_at",
            STATUS_DOWNLOADING: "download_started_at",
            STATUS_DOWNLOADED: "downloaded_at",
            STATUS_VERIFIED: "verified_at",
        }
        if target_status in timestamp_columns:
            changed.setdefault(timestamp_columns[target_status], now)
        if increment_attempt:
            changed["download_attempts"] = int(row["download_attempts"]) + 1
        if error is not None:
            changed["last_error"] = str(error)
            changed["error"] = str(error)

        assignments = ", ".join(f"{column} = ?" for column in changed)
        connection.execute(
            f"UPDATE sermons SET {assignments} WHERE sermon_id = ?",
            (*changed.values(), sermon_id),
        )
        if target_status != current_status:
            connection.execute(
                """INSERT INTO status_events
                   (sermon_id, from_status, to_status, event_at, error, details)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    sermon_id,
                    current_status,
                    target_status,
                    now,
                    error,
                    ArchiveDB._json_dump(details, {}),
                ),
            )
        updated = connection.execute(
            "SELECT * FROM sermons WHERE sermon_id = ?", (sermon_id,)
        ).fetchone()
        assert updated is not None
        return updated

    def transition_status(
        self,
        sermon_id: str,
        new_status: str,
        *,
        error: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> SermonRecord:
        """Apply one validated lifecycle transition and record an event."""

        target = normalize_status(new_status)
        with self.transaction() as connection:
            row = self._transition_row(
                connection,
                sermon_id,
                target,
                error=error,
                details=details,
                increment_attempt=target == STATUS_FAILED,
            )
        result = self._row_to_record(row)
        assert result is not None
        return result

    def queue_sermon(self, sermon_id: str) -> SermonRecord:
        """Move a metadata-complete sermon to the download queue."""

        return self.transition_status(sermon_id, STATUS_QUEUED)

    def start_download(self, sermon_id: str) -> SermonRecord:
        """Mark a queued sermon as actively downloading."""

        with self.transaction() as connection:
            row = self._transition_row(
                connection,
                sermon_id,
                STATUS_DOWNLOADING,
                updates={"last_error": None, "next_retry_at": None},
            )
        result = self._row_to_record(row)
        assert result is not None
        return result

    def mark_failed(
        self,
        sermon_id: str,
        error: str,
        *,
        retry_at: datetime | str | None = None,
    ) -> SermonRecord:
        """Record a failed attempt and increment ``download_attempts`` once."""

        if not str(error).strip():
            raise ValueError("error must not be empty")
        retry_timestamp = None
        if isinstance(retry_at, datetime):
            retry_timestamp = utc_timestamp(retry_at)
        elif retry_at is not None:
            retry_timestamp = str(retry_at)
        with self.transaction() as connection:
            row = self._transition_row(
                connection,
                sermon_id,
                STATUS_FAILED,
                error=str(error),
                details={"retry_at": retry_timestamp} if retry_timestamp else None,
                increment_attempt=True,
                updates={"next_retry_at": retry_timestamp},
            )
        result = self._row_to_record(row)
        assert result is not None
        return result

    def can_retry(self, sermon_id: str, *, max_attempts: int | None = None) -> bool:
        """Return whether a failed sermon remains below its retry limit."""

        record = self.require_sermon(sermon_id)
        limit = record.max_retries if max_attempts is None else max(0, int(max_attempts))
        return record.status == STATUS_FAILED and record.download_attempts < limit

    def queue_retry(
        self,
        sermon_id: str,
        *,
        max_attempts: int | None = None,
        strict: bool = False,
    ) -> bool:
        """Requeue a failed sermon; return ``False`` when retries are exhausted.

        Set ``strict=True`` to raise :class:`RetryLimitExceeded` instead of
        returning ``False`` at the limit.
        """

        with self.transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM sermons WHERE sermon_id = ?", (sermon_id,)
            ).fetchone()
            if existing is None:
                raise SermonNotFound(f"unknown sermon_id: {sermon_id}")
            if existing["status"] != STATUS_FAILED:
                raise InvalidStatusTransition(
                    f"only failed sermons can be retried; current status is {existing['status']}"
                )
            limit = int(existing["max_retries"] if max_attempts is None else max_attempts)
            if int(existing["download_attempts"]) >= max(0, limit):
                if strict:
                    raise RetryLimitExceeded(
                        f"retry limit reached for {sermon_id}: "
                        f"{existing['download_attempts']}/{max(0, limit)}"
                    )
                return False
            self._transition_row(
                connection,
                sermon_id,
                STATUS_QUEUED,
                details={"reason": "retry", "attempts": existing["download_attempts"]},
                updates={"next_retry_at": None},
            )
        return True

    retry_sermon = queue_retry
    retry_failed = queue_retry

    def list_retryable(self, *, now: datetime | str | None = None, limit: int | None = None) -> list[SermonRecord]:
        """List failed rows below their limits and due for retry."""

        when = utc_timestamp(now) if isinstance(now, datetime) else str(now or utc_timestamp())
        sql = """
            SELECT * FROM sermons
            WHERE status = ?
              AND download_attempts < max_retries
              AND (next_retry_at IS NULL OR next_retry_at <= ?)
            ORDER BY next_retry_at IS NOT NULL, next_retry_at, sermon_date, sermon_id
        """
        parameters: list[Any] = [STATUS_FAILED, when]
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            sql += " LIMIT ?"
            parameters.append(limit)
        rows = self.connect().execute(sql, parameters).fetchall()
        return [record for row in rows if (record := self._row_to_record(row)) is not None]

    def mark_downloaded(
        self,
        sermon_id: str,
        local_path: str | os.PathLike[str],
        *,
        sha256: str | None = None,
        file_size_bytes: int | None = None,
        filename: str | None = None,
        audio_only: bool = False,
    ) -> SermonRecord:
        """Store completed download facts and move to downloaded/audio-only."""

        path = os.fspath(local_path)
        if not path:
            raise ValueError("local_path must not be empty")
        if file_size_bytes is None:
            try:
                file_size_bytes = Path(path).stat().st_size
            except OSError:
                pass
        updates: dict[str, Any] = {
            "local_path": path,
            "local_media_path": path,
            "filename": filename or Path(path).name,
            "file_size_bytes": file_size_bytes,
            "filesize": file_size_bytes,
            "media_format": Path(path).suffix.lstrip(".").lower() or None,
            "sha256": sha256.casefold() if sha256 else None,
            "downloaded_at": utc_timestamp(),
            "last_error": None,
            "error": None,
            "next_retry_at": None,
        }
        if audio_only:
            updates["audio_path"] = path
        else:
            updates["video_path"] = path
        target = STATUS_AUDIO_ONLY if audio_only else STATUS_DOWNLOADED
        with self.transaction() as connection:
            row = self._transition_row(
                connection,
                sermon_id,
                target,
                details={"local_path": path},
                updates=updates,
            )
        result = self._row_to_record(row)
        assert result is not None
        return result

    def update_verification(
        self,
        sermon_id: str,
        *,
        valid: bool,
        sha256: str | None = None,
        file_size_bytes: int | None = None,
        local_path: str | os.PathLike[str] | None = None,
        error: str | None = None,
    ) -> SermonRecord:
        """Store verification facts and update lifecycle state atomically."""

        with self.transaction() as connection:
            current = connection.execute(
                "SELECT * FROM sermons WHERE sermon_id = ?", (sermon_id,)
            ).fetchone()
            if current is None:
                raise SermonNotFound(f"unknown sermon_id: {sermon_id}")
            verified_size = (
                file_size_bytes if file_size_bytes is not None else current["file_size_bytes"]
            )
            updates: dict[str, Any] = {
                "sha256": sha256.casefold() if sha256 else current["sha256"],
                "file_size_bytes": verified_size,
                "filesize": verified_size,
            }
            if local_path is not None:
                updates["local_path"] = os.fspath(local_path)
                updates["local_media_path"] = os.fspath(local_path)
            if valid:
                updates["verified_at"] = utc_timestamp()
                updates["last_error"] = None
                updates["error"] = None
                # Keep audio_only visible: it describes the archive limitation,
                # while verified_at records integrity independently.
                target = STATUS_AUDIO_ONLY if current["status"] == STATUS_AUDIO_ONLY else STATUS_VERIFIED
                if current["status"] not in {STATUS_DOWNLOADED, STATUS_AUDIO_ONLY, STATUS_VERIFIED}:
                    raise InvalidStatusTransition(
                        f"cannot verify a sermon in status {current['status']}"
                    )
            else:
                target = STATUS_NEEDS_REVIEW
                error = error or "file verification failed"
            row = self._transition_row(
                connection,
                sermon_id,
                target,
                error=error,
                details={"verification_valid": valid},
                updates=updates,
            )
        result = self._row_to_record(row)
        assert result is not None
        return result

    def verify_file(
        self,
        sermon_id: str,
        path: str | os.PathLike[str] | None = None,
        *,
        expected_sha256: str | None = None,
    ) -> bool:
        """Hash a local file, persist verification, and return whether it matched."""

        record = self.require_sermon(sermon_id)
        selected_path = path if path is not None else record.local_path
        if selected_path is None or not os.fspath(selected_path).strip():
            raise ValueError("no local path is available for verification")
        file_path = Path(selected_path)
        try:
            actual_sha256 = sha256_file(file_path)
            file_size = file_path.stat().st_size
        except OSError as exc:
            self.update_verification(
                sermon_id,
                valid=False,
                local_path=file_path,
                error=f"verification could not read file: {exc}",
            )
            return False

        expected = (expected_sha256 or record.sha256 or "").casefold()
        valid = not expected or actual_sha256 == expected
        self.update_verification(
            sermon_id,
            valid=valid,
            sha256=actual_sha256 if valid or not record.sha256 else record.sha256,
            file_size_bytes=file_size,
            local_path=file_path,
            error=None if valid else f"SHA-256 mismatch: expected {expected}, got {actual_sha256}",
        )
        return valid

    def list_status_events(self, sermon_id: str) -> list[dict[str, Any]]:
        """Return status history in event order with decoded details."""

        rows = self.connect().execute(
            "SELECT * FROM status_events WHERE sermon_id = ? ORDER BY event_id", (sermon_id,)
        ).fetchall()
        events = []
        for row in rows:
            event = dict(row)
            event["details"] = self._json_object(event["details"])
            events.append(event)
        return events

    def upsert_series(
        self,
        series_id: str,
        *,
        title: str | None = None,
        platform: str | None = None,
        platform_series_id: str | None = None,
        short_code: str | None = None,
        canonical_url: str | None = None,
        description: str | None = None,
        item_count: int | None = None,
        advertised_count: int | None = None,
        raw_metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Insert or refresh a normalized series row."""

        if not str(series_id).strip():
            raise ValueError("series_id must not be empty")
        now = utc_timestamp()
        with self.transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM series WHERE series_id = ?", (series_id,)
            ).fetchone()
            old_raw = self._json_object(existing["raw_metadata"]) if existing else {}
            old_raw.update(dict(raw_metadata or {}))
            connection.execute(
                """
                INSERT INTO series (
                    series_id, platform, platform_series_id, short_code, title, canonical_url,
                    description, advertised_count, raw_metadata, discovered_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(series_id) DO UPDATE SET
                    platform = COALESCE(series.platform, excluded.platform),
                    platform_series_id = COALESCE(series.platform_series_id, excluded.platform_series_id),
                    short_code = COALESCE(excluded.short_code, series.short_code),
                    title = COALESCE(excluded.title, series.title),
                    canonical_url = COALESCE(excluded.canonical_url, series.canonical_url),
                    description = COALESCE(excluded.description, series.description),
                    advertised_count = COALESCE(excluded.advertised_count, series.advertised_count),
                    raw_metadata = excluded.raw_metadata,
                    updated_at = excluded.updated_at
                """,
                (
                    str(series_id).strip(),
                    platform,
                    platform_series_id,
                    short_code,
                    title,
                    canonicalize_url(canonical_url),
                    description,
                    advertised_count if advertised_count is not None else item_count,
                    self._json_dump(old_raw, {}),
                    existing["discovered_at"] if existing else now,
                    now,
                ),
            )
            row = connection.execute(
                "SELECT * FROM series WHERE series_id = ?", (series_id,)
            ).fetchone()
        result = dict(row)
        result["raw_metadata"] = self._json_object(result["raw_metadata"])
        return result

    def list_series(self) -> list[dict[str, Any]]:
        """Return all series ordered by title and ID."""

        rows = self.connect().execute(
            "SELECT * FROM series ORDER BY title IS NULL, title COLLATE NOCASE, series_id"
        ).fetchall()
        result = []
        for row in rows:
            values = dict(row)
            values["raw_metadata"] = self._json_object(values["raw_metadata"])
            result.append(values)
        return result

    def start_crawl(
        self, source_url: str | None = None, *, metadata: Mapping[str, Any] | None = None
    ) -> int:
        """Create a running crawl audit row and return its integer ID."""

        with self.transaction() as connection:
            cursor = connection.execute(
                """INSERT INTO crawl_runs (source_url, status, started_at, metadata)
                   VALUES (?, 'running', ?, ?)""",
                (canonicalize_url(source_url), utc_timestamp(), self._json_dump(metadata, {})),
            )
            if cursor.lastrowid is None:
                raise ArchiveDBError("SQLite did not return a crawl run ID")
            return cursor.lastrowid

    def finish_crawl(
        self,
        run_id: int,
        *,
        status: str = "completed",
        pages_seen: int | None = None,
        items_seen: int | None = None,
        items_added: int | None = None,
        items_updated: int | None = None,
        series_found: int | None = None,
        item_pages: int | None = None,
        api_records: int | None = None,
        target_records: int | None = None,
        missing_date_records: int | None = None,
        out_of_range_records: int | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Finish a crawl and update supplied counters."""

        if status not in {"completed", "partial", "failed", "cancelled"}:
            raise ValueError("crawl status must be completed, partial, failed, or cancelled")
        with self.transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM crawl_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if existing is None:
                raise ArchiveDBError(f"unknown crawl run: {run_id}")
            counters = {
                "pages_seen": pages_seen,
                "items_seen": items_seen,
                "items_added": items_added,
                "items_updated": items_updated,
                "series_found": series_found,
                "item_pages": item_pages,
                "api_records": api_records,
                "target_records": target_records,
                "missing_date_records": missing_date_records,
                "out_of_range_records": out_of_range_records,
            }
            updates: dict[str, Any] = {
                "status": status,
                "completed_at": utc_timestamp(),
                "error": error,
            }
            updates.update({key: max(0, int(value)) for key, value in counters.items() if value is not None})
            assignments = ", ".join(f"{column} = ?" for column in updates)
            connection.execute(
                f"UPDATE crawl_runs SET {assignments} WHERE run_id = ?",
                (*updates.values(), run_id),
            )
            row = connection.execute(
                "SELECT * FROM crawl_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        result = dict(row)
        result["metadata"] = self._json_object(result["metadata"])
        return result

    def record_listing_audit(
        self,
        listing_url: str,
        observed_count: int,
        *,
        run_id: int | None = None,
        page_number: int | None = None,
        expected_count: int | None = None,
        item_ids: Iterable[str] = (),
        notes: str | None = None,
    ) -> int:
        """Record exactly what one listing page exposed during a crawl."""

        canonical = canonicalize_url(listing_url)
        if not canonical:
            raise ValueError("listing_url must not be empty")
        with self.transaction() as connection:
            cursor = connection.execute(
                """INSERT INTO listing_audit (
                       run_id, listing_url, page_number, expected_count,
                       observed_count, item_ids, observed_at, notes
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    canonical,
                    page_number,
                    expected_count,
                    max(0, int(observed_count)),
                    self._json_dump(list(item_ids), []),
                    utc_timestamp(),
                    notes,
                ),
            )
            if cursor.lastrowid is None:
                raise ArchiveDBError("SQLite did not return a listing audit ID")
            return cursor.lastrowid
