"""Deterministic exports and completeness reports for the Calvary archive.

SQLite is the source of truth for every value emitted here.  The reporting code
intentionally discovers table columns at runtime: the crawler schema has gained
new normalized inventory fields over time, and those fields should appear in
exports without requiring a second, easy-to-forget report schema update.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import tempfile
from collections import Counter
from collections.abc import Callable, Generator, Iterable, Mapping, Sequence
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, TextIO


_UNKNOWN = "(unknown)"
_RAW_METADATA_COLUMNS = ("raw_metadata_json", "raw_metadata")
_REQUIRED_INVENTORY_FIELDS = (
    "sermon_id",
    "source_platform",
    "source_url",
    "series_url",
    "sermon_date",
    "year",
    "title",
    "speaker",
    "series",
    "book_of_bible",
    "scripture_reference",
    "topic",
    "description",
    "service_type",
    "duration_seconds",
    "has_video",
    "has_audio",
    "video_source_url",
    "audio_source_url",
    "thumbnail_url",
    "original_media_filename",
    "local_media_path",
    "download_status",
    "media_format",
    "filesize",
    "sha256",
    "discovered_at",
    "downloaded_at",
    "error",
    "notes",
)

_DATE_COLUMNS = (
    "sermon_date",
    "date",
    "published_date",
    "date_published",
    "publication_date",
    "event_date",
    "date_iso",
    "sermon_date_iso",
    "normalized_date",
    "date_normalized",
    "preached_at",
    "published_at",
)
_TITLE_COLUMNS = ("title", "sermon_title", "name")
_SPEAKER_COLUMNS = ("speaker", "speaker_name", "preacher", "teacher", "pastor", "author")
_SERIES_VALUE_COLUMNS = ("series_title", "series_name", "series")
_SERIES_KEY_COLUMNS = ("series_id", "source_series_id", "series_slug")
_BOOK_COLUMNS = ("bible_book", "bible_books", "scripture_book", "book", "book_name")
_STATUS_COLUMNS = ("status", "record_status", "inventory_status", "archive_status", "download_status", "state")
_ID_COLUMNS = (
    "id",
    "sermon_id",
    "source_id",
    "external_id",
    "run_id",
    "audit_id",
    "event_id",
    "slug",
    "url",
)

_VIDEO_VALUE_COLUMNS = (
    "video_url",
    "video_download_url",
    "video_source_url",
    "youtube_url",
    "vimeo_url",
    "mp4_url",
    "video_path",
    "video_file_path",
    "video_download_path",
    "video_file",
    "video_filename",
    "local_video_path",
    "archived_video_path",
    "video_archive_path",
    "video_relpath",
    "video_id",
)
_AUDIO_VALUE_COLUMNS = (
    "audio_url",
    "audio_download_url",
    "audio_source_url",
    "mp3_url",
    "audio_path",
    "audio_file_path",
    "audio_download_path",
    "audio_file",
    "audio_filename",
    "local_audio_path",
    "archived_audio_path",
    "audio_archive_path",
    "audio_relpath",
    "audio_id",
)
_VIDEO_FLAG_COLUMNS = ("has_video", "video_available", "video_downloaded")
_AUDIO_FLAG_COLUMNS = ("has_audio", "audio_available", "audio_downloaded")
_LOCAL_MEDIA_COLUMNS = (
    "video_path",
    "video_file_path",
    "video_download_path",
    "video_file",
    "video_filename",
    "local_video_path",
    "archived_video_path",
    "video_archive_path",
    "video_relpath",
    "audio_path",
    "audio_file_path",
    "audio_download_path",
    "audio_file",
    "audio_filename",
    "local_audio_path",
    "archived_audio_path",
    "audio_archive_path",
    "audio_relpath",
    "media_path",
    "download_path",
)
_DOWNLOAD_FLAG_COLUMNS = (
    "downloaded",
    "is_downloaded",
    "download_succeeded",
    "media_downloaded",
    "video_downloaded",
    "audio_downloaded",
    "archived",
)
_REVIEW_FLAG_COLUMNS = (
    "needs_review",
    "review_required",
    "manual_review",
    "needs_manual_review",
    "needs_date_review",
    "date_needs_review",
    "date_review_required",
)
_DATE_REVIEW_FLAG_COLUMNS = (
    "needs_date_review",
    "date_needs_review",
    "date_review_required",
)

_DISCOVERED_SERIES_METRICS = (
    "discovered_series",
    "series_discovered",
    "series_count",
    "series_found",
)
_ADVERTISED_METRICS = (
    "advertised_items",
    "advertised_count",
    "item_count_advertised",
    "expected_items",
    "expected_count",
    "source_item_count",
    "reported_count",
    "advertised_total",
    "advertised_sermon_count",
    "listing_advertised_count",
)
_DISCOVERED_ITEM_METRICS = (
    "discovered_items",
    "discovered_count",
    "items_discovered",
    "found_items",
    "found_count",
    "sermons_discovered",
    "records_discovered",
    "discovered_total",
    "discovered_sermon_count",
    "listing_discovered_count",
    "unique_item_urls",
    "observed_count",
    "items_seen",
)
_ITEM_PAGE_METRICS = (
    "item_pages",
    "item_page_count",
    "item_pages_count",
    "item_pages_fetched",
    "pages_fetched",
    "detail_pages",
    "detail_page_count",
    "detail_pages_fetched",
    "item_pages_ok",
    "pages_seen",
)
_API_RECORD_METRICS = (
    "api_records",
    "api_record_count",
    "api_records_count",
    "records_from_api",
    "api_items",
    "api_items_count",
    "api_records_found",
)
_INVENTORY_METRICS = (
    "inventory_target_records",
    "inventory_records",
    "target_records",
    "sermon_records",
    "normalized_records",
    "records_inserted",
    "inventory_rows",
    "target_count",
    "items_seen",
)
_DOWNLOAD_METRICS = (
    "downloads",
    "downloaded_records",
    "download_count",
    "downloads_succeeded",
    "successful_downloads",
    "media_downloaded",
    "download_success_count",
    "download_ok",
)
_FAILURE_METRICS = (
    "failures",
    "failure_count",
    "failed",
    "failed_count",
    "downloads_failed",
    "error_count",
    "errors",
    "download_failure_count",
    "download_fail",
)
_REVIEW_METRICS = (
    "review",
    "review_count",
    "needs_review",
    "needs_review_count",
    "review_records",
    "manual_review_count",
    "needs_review_count",
)
_VIDEO_METRICS = ("video", "video_count", "video_records", "records_with_video", "video_items")
_VIDEO_ONLY_METRICS = ("video_only", "video_only_count", "video_only_records")
_BOTH_METRICS = ("both", "both_count", "both_records", "video_and_audio_count")
_AUDIO_ONLY_METRICS = ("audio_only", "audio_only_count", "audio_only_records")
_NO_MEDIA_METRICS = ("no_media", "no_media_count", "no_media_records")

_BIBLE_BOOKS = (
    "Genesis",
    "Exodus",
    "Leviticus",
    "Numbers",
    "Deuteronomy",
    "Joshua",
    "Judges",
    "Ruth",
    "1 Samuel",
    "2 Samuel",
    "1 Kings",
    "2 Kings",
    "1 Chronicles",
    "2 Chronicles",
    "Ezra",
    "Nehemiah",
    "Esther",
    "Job",
    "Psalms",
    "Proverbs",
    "Ecclesiastes",
    "Song of Solomon",
    "Isaiah",
    "Jeremiah",
    "Lamentations",
    "Ezekiel",
    "Daniel",
    "Hosea",
    "Joel",
    "Amos",
    "Obadiah",
    "Jonah",
    "Micah",
    "Nahum",
    "Habakkuk",
    "Zephaniah",
    "Haggai",
    "Zechariah",
    "Malachi",
    "Matthew",
    "Mark",
    "Luke",
    "John",
    "Acts",
    "Romans",
    "1 Corinthians",
    "2 Corinthians",
    "Galatians",
    "Ephesians",
    "Philippians",
    "Colossians",
    "1 Thessalonians",
    "2 Thessalonians",
    "1 Timothy",
    "2 Timothy",
    "Titus",
    "Philemon",
    "Hebrews",
    "James",
    "1 Peter",
    "2 Peter",
    "1 John",
    "2 John",
    "3 John",
    "Jude",
    "Revelation",
)
_BIBLE_BOOK_ALIASES = {book.casefold(): book for book in _BIBLE_BOOKS}
_BIBLE_BOOK_ALIASES.update(
    {
        "psalm": "Psalms",
        "song of songs": "Song of Solomon",
        "songs": "Song of Solomon",
        "canticles": "Song of Solomon",
        "revelations": "Revelation",
    }
)
_BIBLE_BOOK_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(" 
    + "|".join(
        re.escape(alias).replace(r"\ ", r"\s+")
        for alias in sorted(_BIBLE_BOOK_ALIASES, key=len, reverse=True)
    )
    + r")\s+\d",
    re.IGNORECASE,
)

_COMPLETENESS_FIELDS = (
    "row_type",
    "identifier",
    "label",
    "discovered_series",
    "advertised_items",
    "discovered_items",
    "item_pages",
    "api_records",
    "inventory_target_records",
    "video",
    "video_only",
    "both",
    "audio_only",
    "no_media",
    "downloads",
    "failures",
    "review",
)


@contextmanager
def _connection_for(db_or_path: Any) -> Generator[Any, None, None]:
    """Yield a DB-API connection, closing only connections opened here."""

    if isinstance(db_or_path, (str, bytes, os.PathLike)):
        db_path = os.fsdecode(os.fspath(db_or_path))
        if db_path != ":memory:" and not db_path.startswith("file:"):
            path = Path(db_path)
            if not path.exists():
                raise FileNotFoundError(f"SQLite database does not exist: {path}")
        connection = sqlite3.connect(db_path, uri=db_path.startswith("file:"))
        try:
            yield connection
        finally:
            connection.close()
        return

    if isinstance(db_or_path, sqlite3.Connection) or hasattr(db_or_path, "execute"):
        yield db_or_path
        return

    for attribute in ("connection", "conn", "connect"):
        connection = getattr(db_or_path, attribute, None)
        if connection is not None and hasattr(connection, "execute"):
            yield connection
            return
        if callable(connection):
            connection = connection()
        if connection is not None and hasattr(connection, "execute"):
            yield connection
            return

    for attribute in ("db_path", "database_path", "path"):
        candidate_path = getattr(db_or_path, attribute, None)
        if isinstance(candidate_path, (str, bytes, os.PathLike)):
            with _connection_for(candidate_path) as connection:
                yield connection
            return

    raise TypeError("db_or_path must be a SQLite path or DB-API connection")


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _fetch_rows(connection: Any, table_name: str) -> tuple[list[str], list[dict[str, Any]]]:
    cursor = connection.execute(f"SELECT * FROM {_quote_identifier(table_name)}")
    columns = [description[0] for description in cursor.description or ()]
    rows: list[dict[str, Any]] = []
    for raw_row in cursor.fetchall():
        if isinstance(raw_row, sqlite3.Row):
            rows.append({column: raw_row[column] for column in columns})
        elif isinstance(raw_row, Mapping):
            rows.append({column: raw_row.get(column) for column in columns})
        else:
            rows.append(dict(zip(columns, raw_row)))
    return columns, rows


def _load_database(connection: Any) -> tuple[dict[str, list[str]], dict[str, list[dict[str, Any]]]]:
    cursor = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    table_names = [str(row[0]) for row in cursor.fetchall()]
    canonical_names = {name.casefold(): name for name in table_names}
    if "sermons" not in canonical_names:
        raise ValueError("SQLite database is missing the required sermons table")

    columns_by_table: dict[str, list[str]] = {}
    rows_by_table: dict[str, list[dict[str, Any]]] = {}
    for requested in (
        "sermons",
        "sermon_sources",
        "series",
        "crawl_runs",
        "listing_audit",
        "status_events",
        "legacy_media_assets",
        "legacy_media_observations",
        "legacy_media_matches",
    ):
        actual = canonical_names.get(requested)
        if actual is None:
            columns_by_table[requested] = []
            rows_by_table[requested] = []
            continue
        columns, rows = _fetch_rows(connection, actual)
        columns_by_table[requested] = columns
        rows_by_table[requested] = rows
    return columns_by_table, rows_by_table


def _column_map(row: Mapping[str, Any]) -> dict[str, str]:
    return {str(key).casefold(): str(key) for key in row}


def _value(row: Mapping[str, Any], aliases: Sequence[str]) -> Any:
    columns = _column_map(row)
    for alias in aliases:
        actual = columns.get(alias.casefold())
        if actual is not None:
            return row.get(actual)
    return None


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bool(bytes(value))
    if isinstance(value, str):
        return value.strip().casefold() not in {
            "",
            "0",
            "false",
            "no",
            "none",
            "null",
            "n/a",
            "unknown",
            "missing",
            "not available",
        }
    return bool(value)


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "yes", "y", "1", "on", "required", "review"}:
            return True
        if normalized in {"false", "no", "n", "0", "off", "", "none", "null"}:
            return False
    return bool(value)


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    return str(value).strip()


def _number(value: Any) -> int | None:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "yes", "y", "on"}:
            return 1
        if normalized in {"false", "no", "n", "off"}:
            return 0
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def _metric(row: Mapping[str, Any], aliases: Sequence[str]) -> int | None:
    columns = _column_map(row)
    for alias in aliases:
        actual = columns.get(alias.casefold())
        if actual is not None:
            return _number(row.get(actual))

    for metadata_column in ("metadata", "details", "raw_metadata", "raw_metadata_json"):
        actual = columns.get(metadata_column)
        if actual is None:
            continue
        parsed = _parse_raw_metadata(row.get(actual))
        if isinstance(parsed, Mapping):
            nested_columns = _column_map(parsed)
            for alias in aliases:
                nested = nested_columns.get(alias.casefold())
                if nested is not None:
                    return _number(parsed.get(nested))
    return None


def _metric_sum(rows: Iterable[Mapping[str, Any]], aliases: Sequence[str]) -> int | None:
    values = [_metric(row, aliases) for row in rows]
    available = [value for value in values if value is not None]
    return sum(available) if available else None


def _parse_date(value: Any) -> date | None:
    text = _text(value)
    if not text:
        return None

    iso_candidate = text
    if iso_candidate.endswith("Z"):
        iso_candidate = iso_candidate[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(iso_candidate).date()
    except ValueError:
        pass
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass

    for pattern in (
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def _row_date(row: Mapping[str, Any]) -> date | None:
    return _parse_date(_value(row, _DATE_COLUMNS))


def _identity(row: Mapping[str, Any]) -> str:
    value = _value(row, _ID_COLUMNS)
    if _present(value):
        return _text(value)
    return json.dumps(
        {str(key): _json_safe(value) for key, value in row.items()},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _natural_key(value: Any) -> tuple[int, Any]:
    text = _text(value)
    try:
        return (0, int(text))
    except ValueError:
        return (1, text.casefold())


def _sermon_sort_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    parsed_date = _row_date(row)
    title = _text(_value(row, _TITLE_COLUMNS))
    return (
        parsed_date is None,
        parsed_date.isoformat() if parsed_date else "",
        title.casefold(),
        _natural_key(_identity(row)),
    )


def _generic_sort_key(row: Mapping[str, Any]) -> tuple[str, str]:
    label = _text(
        _value(
            row,
            (
                "started_at",
                "crawl_started_at",
                "title",
                "name",
                "series_title",
                "listing_url",
                "url",
                "id",
            ),
        )
    )
    return (label.casefold(), _identity(row).casefold())


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def _parse_raw_metadata(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (Mapping, list, tuple)):
        return _json_safe(value)
    text = _text(value)
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        # Invalid source JSON should remain inspectable rather than disappearing.
        return text


def _required_value(row: Mapping[str, Any], field: str) -> Any:
    aliases: dict[str, tuple[str, ...]] = {
        "source_platform": ("source_platform", "platform", "source"),
        "year": ("year",),
        "book_of_bible": ("book_of_bible", "bible_book"),
        "scripture_reference": ("scripture_reference", "scripture"),
        "has_video": ("has_video", "video_url", "video_source_url"),
        "has_audio": ("has_audio", "audio_url", "audio_source_url"),
        "video_source_url": ("video_source_url", "video_url"),
        "audio_source_url": ("audio_source_url", "audio_url"),
        "original_media_filename": ("original_media_filename", "filename"),
        "local_media_path": ("local_media_path", "local_path"),
        "download_status": ("download_status", "status"),
        "media_format": ("media_format", "mime_type"),
        "filesize": ("filesize", "file_size_bytes"),
        "error": ("error", "last_error"),
    }
    value = _value(row, aliases.get(field, (field,)))
    if field == "year" and not _present(value):
        parsed = _row_date(row)
        return parsed.year if parsed else None
    if field in {"has_video", "has_audio"}:
        if field == "has_video":
            return _media_type(row) in {"video", "both"}
        return _media_type(row) in {"audio-only", "both"}
    return value


def _export_row(row: Mapping[str, Any], extra_columns: Sequence[str]) -> dict[str, Any]:
    exported = {field: _required_value(row, field) for field in _REQUIRED_INVENTORY_FIELDS}
    for column in extra_columns:
        exported.setdefault(column, row.get(column))
    return exported


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    safe_value = _json_safe(value)
    if isinstance(safe_value, (dict, list)):
        return json.dumps(safe_value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return safe_value


def _media_type(row: Mapping[str, Any]) -> str:
    status = _text(_value(row, _STATUS_COLUMNS)).casefold()
    if status == "no_media":
        return "no media"

    explicit = _text(_value(row, ("media_type", "media_kind", "media"))).casefold()
    if explicit in {"both", "video+audio", "audio+video"}:
        return "both"
    if explicit in {"audio", "audio-only", "audio_only"}:
        return "audio-only"
    if explicit in {"video", "video-only", "video_only"}:
        return "video"
    if explicit in {"none", "no media", "no_media"}:
        return "no media"

    video = any(_truthy(_value(row, (column,))) for column in _VIDEO_FLAG_COLUMNS)
    audio = any(_truthy(_value(row, (column,))) for column in _AUDIO_FLAG_COLUMNS)
    video = video or any(_present(_value(row, (column,))) for column in _VIDEO_VALUE_COLUMNS)
    audio = audio or any(_present(_value(row, (column,))) for column in _AUDIO_VALUE_COLUMNS)

    generic_media = " ".join(
        _text(_value(row, (column,)))
        for column in ("media_url", "local_path", "filename", "mime_type")
    ).casefold()
    if any(marker in generic_media for marker in ("video/", ".mp4", ".m4v", ".mov", ".webm", ".m3u8")):
        video = True
    if any(marker in generic_media for marker in ("audio/", ".mp3", ".m4a", ".aac", ".wav", ".ogg", ".flac")):
        audio = True
    if status == "audio_only":
        audio = True

    if video and audio:
        return "both"
    if video:
        return "video"
    if audio:
        return "audio-only"
    return "no media"


def _is_downloaded(row: Mapping[str, Any]) -> bool:
    if any(_truthy(_value(row, (column,))) for column in _DOWNLOAD_FLAG_COLUMNS):
        return True
    if any(_present(_value(row, (column,))) for column in _LOCAL_MEDIA_COLUMNS):
        return True
    status = _text(_value(row, _STATUS_COLUMNS)).casefold()
    return status in {
        "downloaded",
        "verified",
        "archived",
        "complete",
        "completed",
        "success",
        "succeeded",
    }


def _is_failure(row: Mapping[str, Any]) -> bool:
    status = _text(_value(row, _STATUS_COLUMNS)).casefold()
    if any(token in status for token in ("fail", "error")):
        return True
    if status in {
        "discovered",
        "metadata_complete",
        "queued",
        "downloading",
        "downloaded",
        "verified",
        "audio_only",
        "no_media",
        "needs_review",
        "complete",
        "completed",
        "success",
        "succeeded",
    }:
        return False
    for column, value in row.items():
        name = str(column).casefold()
        if (name.endswith("_error") or name == "error" or name in _FAILURE_METRICS) and _present(value):
            numeric = _number(value)
            if numeric is None or numeric > 0:
                return True
    return False


def _is_review(row: Mapping[str, Any]) -> bool:
    if any(_truthy(_value(row, (column,))) for column in _REVIEW_FLAG_COLUMNS):
        return True
    status = _text(_value(row, _STATUS_COLUMNS)).casefold()
    return "review" in status or status in {"ambiguous", "uncertain"}


def _date_review_reasons(row: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    raw_date = _value(row, _DATE_COLUMNS)
    if not _present(raw_date):
        reasons.append("missing date")
    elif _parse_date(raw_date) is None:
        reasons.append("unparseable date")

    if any(_truthy(_value(row, (column,))) for column in _DATE_REVIEW_FLAG_COLUMNS):
        reasons.append("explicitly flagged for date review")

    precision = _text(_value(row, ("date_precision", "sermon_date_precision"))).casefold()
    if precision in {"unknown", "approximate", "year", "month", "partial", "ambiguous"}:
        reasons.append(f"date precision is {precision}")

    confidence = _text(_value(row, ("date_confidence", "sermon_date_confidence"))).casefold()
    if confidence in {"low", "unknown", "uncertain", "ambiguous"}:
        reasons.append(f"date confidence is {confidence}")

    review_text = " ".join(
        _text(_value(row, (column,)))
        for column in ("review_reason", "review_notes", "date_review_reason")
    ).casefold()
    if "date" in review_text and "date concern noted" not in reasons:
        reasons.append("date concern noted")

    # Preserve order while avoiding duplicate reasons from overlapping flags.
    return list(dict.fromkeys(reasons))


def _series_key(row: Mapping[str, Any]) -> str:
    return _text(_value(row, ("id", "series_id", "source_series_id", "slug", "series_slug")))


def _series_label(row: Mapping[str, Any]) -> str:
    return _text(_value(row, ("title", "name", "series_title", "series_name", "slug"))) or _series_key(row) or _UNKNOWN


def _series_lookup(series_rows: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for row in series_rows:
        label = _series_label(row)
        for column in ("id", "series_id", "source_series_id", "slug", "series_slug"):
            value = _text(_value(row, (column,)))
            if value:
                lookup[value] = label
    return lookup


def _sermon_series_label(row: Mapping[str, Any], lookup: Mapping[str, str]) -> str:
    direct = _text(_value(row, _SERIES_VALUE_COLUMNS))
    if direct:
        return direct
    key = _text(_value(row, _SERIES_KEY_COLUMNS))
    return lookup.get(key, key or _UNKNOWN)


def _related_sermons(
    source_row: Mapping[str, Any], sermons: Sequence[Mapping[str, Any]], series_lookup: Mapping[str, str]
) -> list[Mapping[str, Any]]:
    source_keys = {
        _text(_value(source_row, (column,)))
        for column in ("id", "series_id", "source_series_id", "slug", "series_slug")
        if _text(_value(source_row, (column,)))
    }
    source_label = _series_label(source_row)
    source_url = _text(_value(source_row, ("listing_url", "series_url", "url")))
    raw_item_ids = _parse_raw_metadata(_value(source_row, ("item_ids", "items")))
    item_ids = {
        _text(item)
        for item in (raw_item_ids if isinstance(raw_item_ids, list) else ())
        if _text(item)
    }

    related: list[Mapping[str, Any]] = []
    for sermon in sermons:
        sermon_key = _text(_value(sermon, _SERIES_KEY_COLUMNS))
        sermon_label = _sermon_series_label(sermon, series_lookup)
        sermon_url = _text(_value(sermon, ("listing_url", "series_url")))
        sermon_item_ids = {
            _text(_value(sermon, (column,)))
            for column in ("sermon_id", "item_id", "platform_item_id", "source_id", "external_id")
            if _text(_value(sermon, (column,)))
        }
        if (
            bool(item_ids.intersection(sermon_item_ids))
            or (sermon_key and sermon_key in item_ids)
            or (sermon_key and sermon_key in source_keys)
            or (source_label != _UNKNOWN and sermon_label.casefold() == source_label.casefold())
            or (source_url and sermon_url == source_url)
        ):
            related.append(sermon)
    return related


def _inventory_counts(sermons: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    media = Counter(_media_type(row) for row in sermons)
    return {
        "inventory_target_records": len(sermons),
        "video": media["video"] + media["both"],
        "video_only": media["video"],
        "both": media["both"],
        "audio_only": media["audio-only"],
        "no_media": media["no media"],
        "downloads": sum(_is_downloaded(row) for row in sermons),
        "failures": sum(_is_failure(row) for row in sermons),
        "review": sum(_is_review(row) or bool(_date_review_reasons(row)) for row in sermons),
    }


def _preferred_metric(
    listing_rows: Sequence[Mapping[str, Any]],
    series_rows: Sequence[Mapping[str, Any]],
    latest_crawl: Mapping[str, Any] | None,
    aliases: Sequence[str],
    fallback: int | None,
) -> int | None:
    for value in (
        _metric_sum(listing_rows, aliases),
        _metric_sum(series_rows, aliases),
        _metric(latest_crawl, aliases) if latest_crawl else None,
    ):
        if value is not None:
            return value
    return fallback


def _coverage_row(
    row_type: str,
    identifier: str,
    label: str,
    source: Mapping[str, Any] | None,
    related_sermons: Sequence[Mapping[str, Any]],
    *,
    discovered_series: int | None = None,
) -> dict[str, Any]:
    source = source or {}
    inventory = _inventory_counts(related_sermons)
    target = _metric(source, _INVENTORY_METRICS)
    result: dict[str, Any] = {
        "row_type": row_type,
        "identifier": identifier,
        "label": label,
        "discovered_series": discovered_series,
        "advertised_items": _metric(source, _ADVERTISED_METRICS),
        "discovered_items": _metric(source, _DISCOVERED_ITEM_METRICS),
        "item_pages": _metric(source, _ITEM_PAGE_METRICS),
        "api_records": _metric(source, _API_RECORD_METRICS),
        **inventory,
    }
    if target is not None:
        result["inventory_target_records"] = target
    for field, aliases in (
        ("video", _VIDEO_METRICS),
        ("video_only", _VIDEO_ONLY_METRICS),
        ("both", _BOTH_METRICS),
        ("audio_only", _AUDIO_ONLY_METRICS),
        ("no_media", _NO_MEDIA_METRICS),
    ):
        direct_value = _metric(source, aliases)
        if direct_value is not None:
            result[field] = direct_value

    direct_downloads = _metric(source, _DOWNLOAD_METRICS)
    direct_failures = _metric(source, _FAILURE_METRICS)
    direct_review = _metric(source, _REVIEW_METRICS)
    if direct_downloads is not None:
        result["downloads"] = direct_downloads
    if direct_failures is not None:
        result["failures"] = direct_failures
    elif _is_failure(source):
        result["failures"] = 1
    if direct_review is not None:
        result["review"] = direct_review
    elif _is_review(source):
        result["review"] = 1
    return result


def _build_completeness_rows(
    sermons: Sequence[Mapping[str, Any]],
    series_rows: Sequence[Mapping[str, Any]],
    crawl_rows: Sequence[Mapping[str, Any]],
    listing_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    series_lookup = _series_lookup(series_rows)
    ordered_crawls = sorted(crawl_rows, key=_generic_sort_key)
    completed_crawls = [
        row
        for row in ordered_crawls
        if _text(_value(row, ("status",))).casefold() in {"completed", "complete", "succeeded"}
    ]
    latest_crawl = (
        completed_crawls[-1]
        if completed_crawls
        else ordered_crawls[-1]
        if ordered_crawls
        else None
    )
    inventory = _inventory_counts(sermons)
    distinct_sermon_series = {
        _sermon_series_label(row, series_lookup)
        for row in sermons
        if _sermon_series_label(row, series_lookup) != _UNKNOWN
    }
    discovered_series = len(series_rows) if series_rows else len(distinct_sermon_series)

    overall: dict[str, Any] = {
        "row_type": "archive",
        "identifier": "overall",
        "label": "Archive total",
        "discovered_series": discovered_series,
        "advertised_items": (
            _metric_sum(series_rows, _ADVERTISED_METRICS)
            or _metric_sum(listing_rows, _ADVERTISED_METRICS)
        ),
        "discovered_items": (
            _metric(latest_crawl, _DISCOVERED_ITEM_METRICS)
            if latest_crawl
            else len(sermons)
        ),
        "item_pages": (
            _metric(latest_crawl, _ITEM_PAGE_METRICS) if latest_crawl else None
        ),
        "api_records": (
            _metric(latest_crawl, _API_RECORD_METRICS) if latest_crawl else None
        ),
        **inventory,
    }

    result = [overall]
    auditable_crawls = [
        row
        for row in ordered_crawls
        if (_metric(row, _API_RECORD_METRICS) or 0) > 0
        and (_metric(row, _ITEM_PAGE_METRICS) or 0) > 0
    ]
    for row in auditable_crawls:
        identifier = _text(_value(row, ("id", "crawl_run_id", "run_id", "started_at"))) or _identity(row)
        label = _text(_value(row, ("started_at", "crawl_started_at", "label"))) or f"Crawl {identifier}"
        run_listing_rows = [
            listing
            for listing in listing_rows
            if _text(_value(listing, ("run_id", "crawl_run_id"))) == identifier
        ]
        coverage = _coverage_row(
            "crawl",
            identifier,
            label,
            row,
            (),
            discovered_series=_metric(row, _DISCOVERED_SERIES_METRICS),
        )
        for field, aliases in (
            ("advertised_items", _ADVERTISED_METRICS),
            ("discovered_items", _DISCOVERED_ITEM_METRICS),
            ("item_pages", _ITEM_PAGE_METRICS),
            ("api_records", _API_RECORD_METRICS),
        ):
            if coverage[field] is None:
                coverage[field] = _metric_sum(run_listing_rows, aliases)
        if coverage["item_pages"] is None and run_listing_rows:
            coverage["item_pages"] = len(run_listing_rows)
        result.append(coverage)

    for row in sorted(series_rows, key=lambda item: (_series_label(item).casefold(), _series_key(item))):
        identifier = _series_key(row) or _identity(row)
        related = _related_sermons(row, sermons, series_lookup)
        coverage = _coverage_row("series", identifier, _series_label(row), row, related, discovered_series=1)
        if coverage["discovered_items"] is None:
            coverage["discovered_items"] = len(related)
        result.append(coverage)

    for row in sorted(listing_rows, key=_generic_sort_key):
        identifier = _text(
            _value(row, ("id", "audit_id", "listing_audit_id", "listing_url", "url"))
        ) or _identity(row)
        label = (
            _text(_value(row, ("listing_url", "url", "title", "name")))
            or _series_label(row)
            or f"Listing {identifier}"
        )
        related = _related_sermons(row, sermons, series_lookup)
        coverage = _coverage_row("listing", identifier, label, row, related)
        if coverage["discovered_items"] is None:
            coverage["discovered_items"] = len(related)
        if coverage["item_pages"] is None:
            coverage["item_pages"] = 1
        result.append(coverage)
    return result


def _counter_for(
    sermons: Sequence[Mapping[str, Any]], aliases: Sequence[str], *, split_values: bool = False
) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in sermons:
        text = _text(_value(row, aliases))
        if not text:
            counter[_UNKNOWN] += 1
            continue
        values = [text]
        if split_values:
            try:
                parsed = json.loads(text)
            except (json.JSONDecodeError, TypeError):
                parsed = None
            if isinstance(parsed, list):
                values = [_text(value) for value in parsed if _text(value)]
            elif ";" in text or "|" in text:
                values = [piece.strip() for piece in text.replace("|", ";").split(";") if piece.strip()]
        if not values:
            counter[_UNKNOWN] += 1
        else:
            counter.update(values)
    return counter


def _bible_book_counter(sermons: Sequence[Mapping[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in sermons:
        direct = _text(_value(row, _BOOK_COLUMNS))
        if direct:
            try:
                parsed = json.loads(direct)
            except (json.JSONDecodeError, TypeError):
                parsed = None
            if isinstance(parsed, list):
                labels = [_text(value) for value in parsed if _text(value)]
            else:
                labels = [
                    value.strip()
                    for value in direct.replace("|", ";").split(";")
                    if value.strip()
                ]
        else:
            scripture = _text(_value(row, ("scripture", "scripture_reference", "passage")))
            labels = []
            for match in _BIBLE_BOOK_PATTERN.finditer(scripture):
                canonical = _BIBLE_BOOK_ALIASES[re.sub(r"\s+", " ", match.group(1)).casefold()]
                if canonical not in labels:
                    labels.append(canonical)

        counter.update(labels or (_UNKNOWN,))
    return counter


def _markdown_cell(value: Any) -> str:
    text = _text(value) or _UNKNOWN
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _count_table(counter: Counter[str], *, chronological: bool = False) -> list[str]:
    lines = ["| Value | Count |", "|---|---:|"]
    if chronological:
        items = sorted(counter.items(), key=lambda item: (item[0] == _UNKNOWN, item[0]))
    else:
        items = sorted(counter.items(), key=lambda item: (-item[1], item[0].casefold(), item[0]))
    if not items:
        lines.append("| (none) | 0 |")
    else:
        lines.extend(f"| {_markdown_cell(label)} | {count} |" for label, count in items)
    return lines


def _event_kind(row: Mapping[str, Any]) -> str:
    return " ".join(
        _text(_value(row, (column,)))
        for column in (
            "event_type",
            "event",
            "status",
            "from_status",
            "to_status",
            "new_status",
            "category",
            "outcome",
            "error",
        )
    ).casefold()


def _build_summary(
    sermons: Sequence[Mapping[str, Any]],
    series_rows: Sequence[Mapping[str, Any]],
    crawl_rows: Sequence[Mapping[str, Any]],
    listing_rows: Sequence[Mapping[str, Any]],
    status_events: Sequence[Mapping[str, Any]],
    completeness_rows: Sequence[Mapping[str, Any]],
) -> str:
    dated_sermons = [row for row in sermons if _row_date(row) is not None]
    parsed_dates = [parsed for row in dated_sermons if (parsed := _row_date(row)) is not None]
    dated_media = Counter(_media_type(row) for row in dated_sermons)
    years: Counter[str] = Counter()
    months: Counter[str] = Counter()
    for row in sermons:
        parsed = _row_date(row)
        years[str(parsed.year) if parsed else _UNKNOWN] += 1
        months[parsed.strftime("%Y-%m") if parsed else _UNKNOWN] += 1

    series_lookup = _series_lookup(series_rows)
    series_counts = Counter(_sermon_series_label(row, series_lookup) for row in sermons)
    speaker_counts = _counter_for(sermons, _SPEAKER_COLUMNS)
    book_counts = _bible_book_counter(sermons)
    status_counts = _counter_for(sermons, _STATUS_COLUMNS)
    media_counts = Counter(_media_type(row) for row in sermons)
    media_counts = Counter({kind: media_counts.get(kind, 0) for kind in ("video", "both", "audio-only", "no media")})

    date_review_count = sum(bool(_date_review_reasons(row)) for row in sermons)
    failed_crawls = sum(_is_failure(row) for row in crawl_rows)
    failed_events = sum(any(token in _event_kind(row) for token in ("fail", "error")) for row in status_events)
    review_events = sum("review" in _event_kind(row) for row in status_events)
    overall = completeness_rows[0]

    lines = [
        "# Calvary Spokane Archive Summary",
        "",
        f"- Total sermons: **{len(sermons)}**",
        f"- Dated sermons in inventory scope: **{len(parsed_dates)}**",
        f"- Dated sermons with video: **{dated_media['video'] + dated_media['both']}**",
        f"- Dated audio-only sermons: **{dated_media['audio-only']}**",
        f"- Dated sermons with no accessible media: **{dated_media['no media']}**",
        f"- Needs date review: **{date_review_count}**",
        "- Completeness CSV media totals include undated review candidates as well as dated sermons.",
    ]
    if parsed_dates:
        lines.append(f"- Date window: **{min(parsed_dates).isoformat()} to {max(parsed_dates).isoformat()}**")
    else:
        lines.append("- Date window: **unavailable**")

    sections = (
        ("By year", _count_table(years, chronological=True)),
        ("By month", _count_table(months, chronological=True)),
        ("By speaker", _count_table(speaker_counts)),
        ("By series", _count_table(series_counts)),
        ("By Bible book", _count_table(book_counts)),
        ("By media type", _count_table(media_counts)),
        ("By status", _count_table(status_counts)),
    )
    for heading, table_lines in sections:
        lines.extend(("", f"## {heading}", "", *table_lines))

    lines.extend(
        (
            "",
            "## Completeness overview",
            "",
            "| Metric | Count |",
            "|---|---:|",
            f"| Discovered series | {_csv_value(overall['discovered_series'])} |",
            f"| Advertised items | {_csv_value(overall['advertised_items'])} |",
            f"| Discovered items | {_csv_value(overall['discovered_items'])} |",
            f"| Item pages | {_csv_value(overall['item_pages'])} |",
            f"| API records | {_csv_value(overall['api_records'])} |",
            f"| Inventory target records | {_csv_value(overall['inventory_target_records'])} |",
            f"| Records with video | {_csv_value(overall['video'])} |",
            f"| Audio-only records | {_csv_value(overall['audio_only'])} |",
            f"| Records with no media | {_csv_value(overall['no_media'])} |",
            f"| Downloaded records | {_csv_value(overall['downloads'])} |",
            f"| Failed inventory records | {_csv_value(overall['failures'])} |",
            f"| Inventory records needing review | {_csv_value(overall['review'])} |",
            "",
            "## Crawl, series, and listing coverage",
            "",
            "| Scope | Label | Advertised | Discovered | Item pages | API records | Inventory | Failures | Review |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        )
    )
    for row in completeness_rows[1:]:
        lines.append(
            "| {scope} | {label} | {advertised} | {discovered} | {pages} | {api} | {inventory} | {failures} | {review} |".format(
                scope=_markdown_cell(row["row_type"]),
                label=_markdown_cell(row["label"]),
                advertised=_csv_value(row["advertised_items"]),
                discovered=_csv_value(row["discovered_items"]),
                pages=_csv_value(row["item_pages"]),
                api=_csv_value(row["api_records"]),
                inventory=_csv_value(row["inventory_target_records"]),
                failures=_csv_value(row["failures"]),
                review=_csv_value(row["review"]),
            )
        )
    if len(completeness_rows) == 1:
        lines.append("| (none) | (no crawl, series, or listing rows) |  |  |  |  |  |  |  |")

    lines.extend(
        (
            "",
            "## Failures and review",
            "",
            f"- Crawl runs: **{len(crawl_rows)}** (failed: **{failed_crawls}**)",
            f"- Discovered series rows: **{len(series_rows)}**",
            f"- Listing audit rows: **{len(listing_rows)}**",
            f"- Status events: **{len(status_events)}** (failure events: **{failed_events}**, review events: **{review_events}**)",
            f"- Inventory failures: **{overall['failures']}**",
            f"- Inventory review records: **{overall['review']}**",
            "",
        )
    )
    return "\n".join(lines)


def _write_csv(file_object: TextIO, fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    writer = csv.DictWriter(file_object, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def _stage_outputs(renderers: Sequence[tuple[Path, Callable[[TextIO], None]]]) -> None:
    staged: list[tuple[Path, Path]] = []
    try:
        for destination, renderer in renderers:
            destination.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
            )
            temporary_path = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as file_object:
                    renderer(file_object)
                    file_object.flush()
                    os.fsync(file_object.fileno())
            except BaseException:
                temporary_path.unlink(missing_ok=True)
                raise
            staged.append((temporary_path, destination))

        for temporary_path, destination in staged:
            os.replace(temporary_path, destination)

        for directory in {destination.parent for _, destination in staged}:
            try:
                directory_descriptor = os.open(directory, os.O_RDONLY)
                try:
                    os.fsync(directory_descriptor)
                finally:
                    os.close(directory_descriptor)
            except OSError:
                # Some filesystems do not support fsync on a directory.  The
                # file-level atomic replacements have still completed.
                pass
    finally:
        for temporary_path, _ in staged:
            temporary_path.unlink(missing_ok=True)


_CALENDAR_GAP_FIELDS = (
    "date",
    "weekday",
    "expected_service_type",
    "records_on_date",
    "known_holiday",
    "previous_date",
    "previous_title",
    "previous_series",
    "previous_media_id",
    "next_date",
    "next_title",
    "next_series",
    "next_media_id",
    "series_active_before_after",
    "confidence",
    "notes",
)


def _easter_sunday(year: int) -> date:
    """Return Gregorian Easter Sunday using the Anonymous Gregorian algorithm."""

    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _holiday_name(value: date) -> str | None:
    if value == _easter_sunday(value.year):
        return "Easter Sunday"
    if value.weekday() == 3 and value.month == 11 and 22 <= value.day <= 28:
        return "Thanksgiving"
    exact = {
        (12, 24): "Christmas Eve",
        (12, 25): "Christmas Day",
        (12, 31): "New Year's Eve",
        (1, 1): "New Year's Day",
    }
    if (value.month, value.day) in exact:
        return exact[(value.month, value.day)]
    if (value.month == 12 and value.day >= 26) or (value.month == 1 and value.day <= 7):
        return "Christmas/New Year period"
    return None


def _joined_record_value(records: Sequence[Mapping[str, Any]], field: str) -> str:
    values = [str(record.get(field) or "").strip() for record in records]
    return "; ".join(dict.fromkeys(value for value in values if value))


def _build_calendar_gap_report(
    sermons: Sequence[Mapping[str, Any]],
    start: date,
    end: date,
) -> tuple[list[dict[str, Any]], str]:
    records_by_date: dict[date, list[Mapping[str, Any]]] = {}
    for sermon in sermons:
        sermon_date = _row_date(sermon)
        if sermon_date is not None and start <= sermon_date <= end:
            records_by_date.setdefault(sermon_date, []).append(sermon)

    expected: list[date] = []
    cursor = start
    while cursor <= end:
        if cursor.weekday() in {3, 6}:
            expected.append(cursor)
        cursor += timedelta(days=1)
    represented = sorted(value for value in records_by_date if value.weekday() in {3, 6})
    represented_by_weekday = {
        weekday: [value for value in represented if value.weekday() == weekday]
        for weekday in (3, 6)
    }

    gap_rows: list[dict[str, Any]] = []
    for gap_date in expected:
        if gap_date in records_by_date:
            continue
        same_weekday_dates = represented_by_weekday[gap_date.weekday()]
        preceding_dates = [value for value in same_weekday_dates if value < gap_date]
        following_dates = [value for value in same_weekday_dates if value > gap_date]
        previous_date = preceding_dates[-1] if preceding_dates else None
        next_date = following_dates[0] if following_dates else None
        previous_records = records_by_date.get(previous_date, []) if previous_date else []
        next_records = records_by_date.get(next_date, []) if next_date else []
        previous_series = _joined_record_value(previous_records, "series")
        next_series = _joined_record_value(next_records, "series")
        same_series = bool(previous_series and previous_series == next_series)
        holiday = _holiday_name(gap_date)
        previous_distance = (gap_date - previous_date).days if previous_date else None
        next_distance = (next_date - gap_date).days if next_date else None
        if holiday:
            confidence = "holiday"
            notes = "Calendar gap coincides with a holiday or year-end service period."
        elif (
            previous_distance == 7
            and next_distance == 7
            and same_series
        ) or (
            same_series
            and previous_distance is not None
            and next_distance is not None
            and previous_distance <= 42
            and next_distance <= 42
        ):
            confidence = "likely_scheduled_gap"
            notes = (
                "Non-holiday calendar gap bracketed by the same series; this is not proof "
                "that a service occurred or that a recording was published."
            )
        elif (
            previous_distance is not None
            and next_distance is not None
            and previous_distance <= 42
            and next_distance <= 42
        ):
            confidence = "possible_cancelled_service"
            notes = (
                "Calendar gap lies between nearby services, but source evidence does not "
                "confirm a missing sermon."
            )
        else:
            confidence = "unknown"
            notes = "No catalog record; schedule and recording status remain unknown."
        gap_rows.append(
            {
                "date": gap_date.isoformat(),
                "weekday": gap_date.strftime("%A"),
                "expected_service_type": (
                    "Sunday service" if gap_date.weekday() == 6 else "Thursday service"
                ),
                "records_on_date": 0,
                "known_holiday": holiday,
                "previous_date": previous_date.isoformat() if previous_date else None,
                "previous_title": _joined_record_value(previous_records, "title"),
                "previous_series": previous_series,
                "previous_media_id": _joined_record_value(
                    previous_records, "original_media_filename"
                ),
                "next_date": next_date.isoformat() if next_date else None,
                "next_title": _joined_record_value(next_records, "title"),
                "next_series": next_series,
                "next_media_id": _joined_record_value(next_records, "original_media_filename"),
                "series_active_before_after": previous_series if same_series else None,
                "confidence": confidence,
                "notes": notes,
            }
        )

    expected_counts = Counter(value.strftime("%A") for value in expected)
    present_counts = Counter(value.strftime("%A") for value in represented)
    confidence_counts = Counter(str(row["confidence"]) for row in gap_rows)
    no_media = [
        sermon
        for sermon in sermons
        if (sermon_date := _row_date(sermon)) is not None
        and start <= sermon_date <= end
        and _media_type(sermon) == "no media"
    ]
    lines = [
        "# Sunday/Thursday Calendar Coverage",
        "",
        f"Inclusive audit window: **{start.isoformat()} through {end.isoformat()}**.",
        "",
        (
            "A calendar gap means only that no inventory record currently occupies an expected "
            "Sunday or Thursday date. It is **not** a confirmed missing sermon: holidays, cancelled "
            "services, schedule breaks, combined services, and unrecorded services are all possible."
        ),
        "",
        "| Service day | Calendar dates | Represented dates | Gap dates | Coverage |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in ("Sunday", "Thursday"):
        expected_count = expected_counts[label]
        present_count = present_counts[label]
        coverage = (100.0 * present_count / expected_count) if expected_count else 0.0
        lines.append(
            f"| {label} | {expected_count} | {present_count} | "
            f"{expected_count - present_count} | {coverage:.1f}% |"
        )
    total_expected = len(expected)
    total_present = len(represented)
    lines.extend(
        (
            f"| **Total** | **{total_expected}** | **{total_present}** | "
            f"**{total_expected - total_present}** | **{100.0 * total_present / total_expected:.1f}%** |",
            "",
            "## Gap classifications",
            "",
            "| Classification | Dates | Meaning |",
            "|---|---:|---|",
            f"| Holiday/year-end | {confidence_counts['holiday']} | Plausible schedule exception |",
            f"| Likely scheduled gap | {confidence_counts['likely_scheduled_gap']} | Bracketed by the same series; still unconfirmed |",
            f"| Possible cancelled service | {confidence_counts['possible_cancelled_service']} | Nearby services exist, but no source record |",
            f"| Unknown | {confidence_counts['unknown']} | Insufficient evidence |",
            "",
            "## Confirmed records with unavailable media",
            "",
            (
                f"There are **{len(no_media)}** known historical records in the date window whose "
                "currently checked public audio/video is unavailable. These are inventory records, "
                "not calendar gaps."
            ),
            "",
        )
    )
    for sermon in sorted(no_media, key=_sermon_sort_key):
        sermon_date = _row_date(sermon)
        lines.append(
            f"- `{sermon_date.isoformat() if sermon_date else ''}` — "
            f"{_text(sermon.get('title')) or '(untitled)'}"
        )
    lines.append("")
    return gap_rows, "\n".join(lines)


def generate_reports(db_or_path: Any, archive_root: str | os.PathLike[str]) -> None:
    """Generate canonical archive exports and completeness reports.

    ``db_or_path`` may be a SQLite path or an existing DB-API connection.  An
    existing connection is never committed or closed.  Each destination is
    fully staged, flushed, and atomically replaced; no temporary report remains
    after either success or failure.
    """

    with _connection_for(db_or_path) as connection:
        columns_by_table, rows_by_table = _load_database(connection)

    series_rows = rows_by_table["series"]
    crawl_rows = rows_by_table["crawl_runs"]
    completed_crawls = sorted(
        (
            row
            for row in crawl_rows
            if _text(_value(row, ("status",))).casefold()
            in {"completed", "complete", "succeeded"}
        ),
        key=_generic_sort_key,
    )
    scope_start: date | None = None
    scope_end: date | None = None
    if completed_crawls:
        metadata = _parse_raw_metadata(completed_crawls[-1].get("metadata"))
        if isinstance(metadata, Mapping):
            scope_start = _parse_date(metadata.get("start_date"))
            scope_end = _parse_date(metadata.get("end_date"))

    def in_completed_scope(row: Mapping[str, Any]) -> bool:
        sermon_date = _row_date(row)
        if sermon_date is None:
            return True
        return (scope_start is None or sermon_date >= scope_start) and (
            scope_end is None or sermon_date <= scope_end
        )

    sermons = sorted(
        (row for row in rows_by_table["sermons"] if in_completed_scope(row)),
        key=_sermon_sort_key,
    )
    listing_rows = rows_by_table["listing_audit"]
    status_events = rows_by_table["status_events"]
    selected_sermon_ids = {
        str(_value(row, ("sermon_id", "id", "source_id")) or "") for row in sermons
    }
    source_rows = sorted(
        (
            row
            for row in rows_by_table["sermon_sources"]
            if str(row.get("sermon_id") or "") in selected_sermon_ids
        ),
        key=_generic_sort_key,
    )
    media_crawls = []
    for row in completed_crawls:
        metadata = _parse_raw_metadata(row.get("metadata"))
        if isinstance(metadata, Mapping) and metadata.get("source") == "legacy_media_index":
            media_crawls.append(row)
    latest_media_run_id = (
        max((_number(row.get("run_id")) or 0 for row in media_crawls), default=0) or None
    )
    media_observations = [
        row
        for row in rows_by_table["legacy_media_observations"]
        if latest_media_run_id is not None
        and _number(row.get("run_id")) == latest_media_run_id
    ]
    observed_media_ids = {str(row.get("media_id") or "") for row in media_observations}
    media_assets = sorted(
        (
            row
            for row in rows_by_table["legacy_media_assets"]
            if str(row.get("media_id") or "") in observed_media_ids
        ),
        key=lambda row: (_text(row.get("media_url")).casefold(), _text(row.get("media_id"))),
    )
    media_matches = sorted(
        (
            row
            for row in rows_by_table["legacy_media_matches"]
            if latest_media_run_id is not None
            and _number(row.get("run_id")) == latest_media_run_id
        ),
        key=lambda row: (
            _text(row.get("classification")),
            _text(row.get("media_id")),
            _text(row.get("sermon_id")),
        ),
    )

    database_columns = [
        column
        for column in columns_by_table["sermons"]
        if column.casefold() not in _RAW_METADATA_COLUMNS
    ]
    normalized_columns = list(_REQUIRED_INVENTORY_FIELDS) + [
        column for column in database_columns if column not in _REQUIRED_INVENTORY_FIELDS
    ]
    raw_column = next(
        (
            column
            for preferred in _RAW_METADATA_COLUMNS
            for column in columns_by_table["sermons"]
            if column.casefold() == preferred
        ),
        None,
    )

    json_rows: list[dict[str, Any]] = []
    for row in sermons:
        exported = {
            column: _json_safe(value)
            for column, value in _export_row(row, database_columns).items()
        }
        exported["raw_metadata"] = _parse_raw_metadata(row.get(raw_column)) if raw_column else None
        json_rows.append(exported)

    date_review_rows: list[dict[str, Any]] = []
    for row in sermons:
        reasons = _date_review_reasons(row)
        if reasons:
            exported = _export_row(row, database_columns)
            exported["date_review_reason"] = "; ".join(reasons)
            date_review_rows.append(exported)

    completeness_rows = _build_completeness_rows(sermons, series_rows, crawl_rows, listing_rows)
    calendar_start = scope_start or date(2004, 6, 1)
    calendar_end = scope_end or date(2010, 8, 31)
    calendar_gap_rows, calendar_coverage = _build_calendar_gap_report(
        sermons, calendar_start, calendar_end
    )
    summary = _build_summary(
        sermons,
        series_rows,
        crawl_rows,
        listing_rows,
        status_events,
        completeness_rows,
    )
    if source_rows:
        historical_video_links = sum(bool(row.get("video_url")) for row in source_rows)
        reachable_historical_videos = sum(
            bool(row.get("video_url")) and _truthy(row.get("video_available"))
            for row in source_rows
        )
        summary += (
            "\n## Supplemental provenance\n\n"
            f"- Source evidence records: **{len(source_rows)}**\n"
            f"- Historical video links documented: **{historical_video_links}**\n"
            f"- Historical video links currently reachable: **{reachable_historical_videos}**\n"
        )
    if latest_media_run_id is not None:
        classifications = Counter(_text(row.get("classification")) for row in media_matches)
        unique_candidate_ids = {
            str(row.get("media_id") or "")
            for row in media_matches
            if _text(row.get("classification"))
            in {"candidate_unprobed", "target_candidate", "needs_date_review"}
        }
        summary += (
            "\n## Legacy media index audit\n\n"
            f"- Latest completed media-index run: **{latest_media_run_id}**\n"
            f"- Public media files listed in that run: **{len(media_assets)}**\n"
            f"- Files matched to inventory: **{classifications['matched_inventory']}**\n"
            f"- Ambiguous matches: **{classifications['ambiguous_inventory_match']}**\n"
            f"- Unresolved target/review candidates: **{len(unique_candidate_ids)}**\n"
            "- A listed file is not counted as a sermon unless its identity and historical date are supported.\n"
        )

    root = Path(archive_root)
    sermons_csv = root / "data" / "sermons.csv"
    sermons_json = root / "data" / "sermons.json"
    summary_md = root / "reports" / "summary.md"
    completeness_csv = root / "reports" / "completeness.csv"
    date_review_csv = root / "reports" / "needs_date_review.csv"
    sources_json = root / "data" / "sermon_sources.json"
    provenance_csv = root / "reports" / "provenance.csv"
    calendar_gaps_csv = root / "reports" / "calendar-gaps.csv"
    calendar_coverage_md = root / "reports" / "calendar-coverage.md"
    media_assets_json = root / "data" / "legacy_media_assets.json"
    media_matches_csv = root / "reports" / "legacy-media-matches.csv"
    media_candidates_csv = root / "reports" / "legacy-media-candidates.csv"

    def render_sermons_csv(file_object: TextIO) -> None:
        _write_csv(
            file_object,
            normalized_columns,
            (_export_row(row, database_columns) for row in sermons),
        )

    def render_sermons_json(file_object: TextIO) -> None:
        json.dump(json_rows, file_object, ensure_ascii=False, indent=2, sort_keys=True)
        file_object.write("\n")

    def render_summary(file_object: TextIO) -> None:
        file_object.write(summary)

    def render_completeness(file_object: TextIO) -> None:
        _write_csv(file_object, _COMPLETENESS_FIELDS, completeness_rows)

    def render_date_review(file_object: TextIO) -> None:
        _write_csv(file_object, (*normalized_columns, "date_review_reason"), date_review_rows)

    def render_calendar_gaps(file_object: TextIO) -> None:
        _write_csv(file_object, _CALENDAR_GAP_FIELDS, calendar_gap_rows)

    def render_calendar_coverage(file_object: TextIO) -> None:
        file_object.write(calendar_coverage)

    outputs: list[tuple[Path, Callable[[TextIO], None]]] = [
        (sermons_csv, render_sermons_csv),
        (sermons_json, render_sermons_json),
        (summary_md, render_summary),
        (completeness_csv, render_completeness),
        (date_review_csv, render_date_review),
        (calendar_gaps_csv, render_calendar_gaps),
        (calendar_coverage_md, render_calendar_coverage),
    ]
    if source_rows:
        source_columns = [
            column
            for column in columns_by_table["sermon_sources"]
            if column.casefold() != "raw_metadata"
        ]
        source_json_rows: list[dict[str, Any]] = []
        for row in source_rows:
            exported = {column: _json_safe(row.get(column)) for column in source_columns}
            exported["raw_metadata"] = _parse_raw_metadata(row.get("raw_metadata"))
            source_json_rows.append(exported)

        def render_sources_json(file_object: TextIO) -> None:
            json.dump(source_json_rows, file_object, ensure_ascii=False, indent=2, sort_keys=True)
            file_object.write("\n")

        def render_provenance_csv(file_object: TextIO) -> None:
            _write_csv(
                file_object,
                (*source_columns, "raw_metadata"),
                source_json_rows,
            )

        outputs.extend(
            ((sources_json, render_sources_json), (provenance_csv, render_provenance_csv))
        )

    if columns_by_table["legacy_media_assets"]:
        media_asset_columns = list(columns_by_table["legacy_media_assets"])
        media_match_columns = list(columns_by_table["legacy_media_matches"])
        asset_by_id = {str(row.get("media_id") or ""): row for row in media_assets}
        sermon_by_id = {str(row.get("sermon_id") or ""): row for row in sermons}
        media_json_rows: list[dict[str, Any]] = []
        for row in media_assets:
            exported = {column: _json_safe(row.get(column)) for column in media_asset_columns}
            exported["ffprobe_metadata"] = _parse_raw_metadata(row.get("ffprobe_metadata"))
            media_json_rows.append(exported)

        media_report_fields = (
            *media_match_columns,
            "media_url",
            "source_root",
            "parent_index_url",
            "relative_path",
            "filename",
            "media_kind",
            "extension",
            "listed_last_modified",
            "listed_size",
            "probed_at",
            "probe_error",
            "ffprobe_metadata",
            "sermon_date",
            "sermon_title",
            "sermon_speaker",
            "sermon_series",
        )
        media_report_rows: list[dict[str, Any]] = []
        for match in media_matches:
            asset = asset_by_id.get(str(match.get("media_id") or ""), {})
            sermon = sermon_by_id.get(str(match.get("sermon_id") or ""), {})
            exported = {column: match.get(column) for column in media_match_columns}
            exported["evidence"] = _parse_raw_metadata(match.get("evidence"))
            for field in (
                "media_url",
                "source_root",
                "parent_index_url",
                "relative_path",
                "filename",
                "media_kind",
                "extension",
                "listed_last_modified",
                "listed_size",
                "probed_at",
                "probe_error",
            ):
                exported[field] = asset.get(field)
            exported["ffprobe_metadata"] = _parse_raw_metadata(asset.get("ffprobe_metadata"))
            exported["sermon_date"] = sermon.get("sermon_date")
            exported["sermon_title"] = sermon.get("title")
            exported["sermon_speaker"] = sermon.get("speaker")
            exported["sermon_series"] = sermon.get("series")
            media_report_rows.append(exported)
        candidate_rows = [
            row
            for row in media_report_rows
            if _text(row.get("classification")) != "matched_inventory"
        ]

        def render_media_assets_json(file_object: TextIO) -> None:
            json.dump(media_json_rows, file_object, ensure_ascii=False, indent=2, sort_keys=True)
            file_object.write("\n")

        def render_media_matches(file_object: TextIO) -> None:
            _write_csv(file_object, media_report_fields, media_report_rows)

        def render_media_candidates(file_object: TextIO) -> None:
            _write_csv(file_object, media_report_fields, candidate_rows)

        outputs.extend(
            (
                (media_assets_json, render_media_assets_json),
                (media_matches_csv, render_media_matches),
                (media_candidates_csv, render_media_candidates),
            )
        )

    _stage_outputs(outputs)
