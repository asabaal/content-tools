"""Normalized data models for the Calvary Spokane sermon archive."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any

from .utils import parse_sermon_date


class ArchiveStatus(StrEnum):
    """Lifecycle states used by the catalog and downloader."""

    DISCOVERED = "discovered"
    METADATA_COMPLETE = "metadata_complete"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    VERIFIED = "verified"
    AUDIO_ONLY = "audio_only"
    NO_MEDIA = "no_media"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


ARCHIVE_STATUSES = frozenset(status.value for status in ArchiveStatus)
STATUSES = ARCHIVE_STATUSES

# Individual constants are convenient in SQL-facing and command-line code.
STATUS_DISCOVERED = ArchiveStatus.DISCOVERED.value
STATUS_METADATA_COMPLETE = ArchiveStatus.METADATA_COMPLETE.value
STATUS_QUEUED = ArchiveStatus.QUEUED.value
STATUS_DOWNLOADING = ArchiveStatus.DOWNLOADING.value
STATUS_DOWNLOADED = ArchiveStatus.DOWNLOADED.value
STATUS_VERIFIED = ArchiveStatus.VERIFIED.value
STATUS_AUDIO_ONLY = ArchiveStatus.AUDIO_ONLY.value
STATUS_NO_MEDIA = ArchiveStatus.NO_MEDIA.value
STATUS_FAILED = ArchiveStatus.FAILED.value
STATUS_NEEDS_REVIEW = ArchiveStatus.NEEDS_REVIEW.value


REQUIRED_INVENTORY_FIELDS = (
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


NORMALIZED_INVENTORY_FIELDS = REQUIRED_INVENTORY_FIELDS + (
    "source_id",
    "source_id",
    "external_id",
    "platform",
    "item_id",
    "platform_item_id",
    "series_id",
    "platform_series_id",
    "app_key",
    "short_code",
    "slug",
    "title",
    "subtitle",
    "speaker",
    "sermon_date",
    "date",
    "series",
    "series_title",
    "scripture",
    "scriptures",
    "bible_book",
    "topic",
    "service_type",
    "description",
    "summary",
    "tags",
    "duration_seconds",
    "duration_ms",
    "published_at",
    "canonical_url",
    "source_url",
    "share_url",
    "embed_url",
    "series_url",
    "series_items_url",
    "media_url",
    "audio_url",
    "video_url",
    "hls_url",
    "thumbnail_url",
    "media_type",
    "mime_type",
    "status",
    "needs_review",
    "review_reason",
    "local_path",
    "audio_path",
    "video_path",
    "filename",
    "file_size_bytes",
    "sha256",
    "download_attempts",
    "max_retries",
    "last_error",
    "next_retry_at",
    "discovered_at",
    "metadata_updated_at",
    "queued_at",
    "download_started_at",
    "downloaded_at",
    "verified_at",
    "updated_at",
    "notes",
)


FIELD_ALIASES = {
    "date": "sermon_date",
    "sermonDate": "sermon_date",
    "series_title": "series",
    "page_url": "source_url",
    "webpage_url": "source_url",
    "source_page_url": "source_url",
    "local_file": "local_path",
    "local_file_path": "local_path",
    "file_size": "file_size_bytes",
    "checksum": "sha256",
    "checksum_sha256": "sha256",
    "attempts": "download_attempts",
    "retry_count": "download_attempts",
    "error_message": "last_error",
    "source_item_id": "item_id",
}


@dataclass(slots=True)
class SermonRecord:
    """A normalized sermon inventory row.

    Metadata fields describe the remote item.  Fields from ``local_path``
    through ``verified_at`` are local archive facts and must only be changed
    by download/verification operations once the row exists.
    """

    sermon_id: str
    id: str | None = None
    source_id: str | None = None
    external_id: str | None = None
    source: str | None = None
    platform: str | None = None
    source_platform: str | None = None
    item_id: str | None = None
    platform_item_id: str | None = None
    series_id: str | None = None
    platform_series_id: str | None = None
    app_key: str | None = None
    short_code: str | None = None
    slug: str | None = None
    title: str = ""
    subtitle: str | None = None
    speaker: str | None = None
    sermon_date: date | None = None
    date: str | None = None
    year: int | None = None
    series: str | None = None
    series_title: str | None = None
    series_url: str | None = None
    series_items_url: str | None = None
    scripture: str | None = None
    scripture_reference: str | None = None
    scriptures: list[Any] = field(default_factory=list)
    bible_book: str | None = None
    book_of_bible: str | None = None
    topic: str | None = None
    service_type: str | None = None
    description: str | None = None
    summary: str | None = None
    summary_text: str | None = None
    summary_html: str | None = None
    tags: list[Any] = field(default_factory=list)
    duration_seconds: int | None = None
    duration: int | float | None = None
    duration_ms: int | None = None
    published_at: str | None = None
    canonical_url: str | None = None
    source_url: str | None = None
    share_url: str | None = None
    embed_url: str | None = None
    media_url: str | None = None
    has_video: bool = False
    has_audio: bool = False
    audio_url: str | None = None
    audio_source_url: str | None = None
    native_audio_url: str | None = None
    external_audio_url: str | None = None
    video_url: str | None = None
    video_source_url: str | None = None
    native_video_url: str | None = None
    external_video_url: str | None = None
    hls_url: str | None = None
    native_hls_url: str | None = None
    external_hls_url: str | None = None
    thumbnail_url: str | None = None
    original_filename: str | None = None
    original_media_filename: str | None = None
    audio_original_filename: str | None = None
    video_original_filename: str | None = None
    media_type: str | None = None
    media_format: str | None = None
    mime_type: str | None = None
    status: str | None = STATUS_DISCOVERED
    download_status: str | None = None
    in_scope: bool = True
    needs_review: bool = False
    review_reason: str | None = None
    local_path: str | None = None
    local_media_path: str | None = None
    audio_path: str | None = None
    video_path: str | None = None
    filename: str | None = None
    file_size_bytes: int | None = None
    filesize: int | None = None
    sha256: str | None = None
    download_attempts: int = 0
    max_retries: int = 3
    last_error: str | None = None
    error: str | None = None
    next_retry_at: str | None = None
    discovered_at: str | None = None
    metadata_updated_at: str | None = None
    queued_at: str | None = None
    download_started_at: str | None = None
    downloaded_at: str | None = None
    verified_at: str | None = None
    updated_at: str | None = None
    notes: str | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    raw_json: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None
    raw_json_text: str | None = None

    def __post_init__(self) -> None:
        self.sermon_id = str(self.sermon_id).strip()
        if not self.sermon_id:
            raise ValueError("sermon_id must not be empty")
        self.title = str(self.title or "").strip()

        parsed_date = parse_sermon_date(self.sermon_date if self.sermon_date is not None else self.date)
        if (self.sermon_date is not None or self.date is not None) and parsed_date is None:
            raise ValueError(f"invalid sermon_date: {self.sermon_date or self.date!r}")
        self.sermon_date = parsed_date
        self.date = parsed_date.isoformat() if parsed_date is not None else None
        self.year = parsed_date.year if parsed_date is not None else None

        if not isinstance(self.raw_metadata, dict):
            if isinstance(self.raw_metadata, Mapping):
                self.raw_metadata = dict(self.raw_metadata)
            elif isinstance(self.raw_metadata, str):
                try:
                    decoded = json.loads(self.raw_metadata)
                except json.JSONDecodeError:
                    decoded = {"value": self.raw_metadata}
                self.raw_metadata = decoded if isinstance(decoded, dict) else {"value": decoded}
            else:
                self.raw_metadata = {"value": self.raw_metadata}
        if not self.raw_metadata:
            source_raw = self.raw_json if isinstance(self.raw_json, Mapping) else self.raw
            if isinstance(source_raw, Mapping):
                self.raw_metadata = dict(source_raw)
        if self.raw_json is None:
            self.raw_json = dict(self.raw_metadata)
        if self.raw is None:
            self.raw = dict(self.raw_metadata)
        if self.raw_json_text is None and self.raw_json:
            self.raw_json_text = json.dumps(self.raw_json, ensure_ascii=False, sort_keys=True)

        provider_status = str(self.status or "").strip().lower()
        if provider_status in ARCHIVE_STATUSES:
            self.status = provider_status
        else:
            if provider_status:
                self.raw_metadata.setdefault("source_status", provider_status)
            self.status = STATUS_METADATA_COMPLETE if provider_status == "published" else STATUS_DISCOVERED

        self.download_attempts = max(0, int(self.download_attempts or 0))
        self.max_retries = max(0, int(self.max_retries))
        if self.duration_ms is None and self.duration is not None:
            self.duration_ms = max(0, int(self.duration))
        if self.duration_seconds is not None:
            self.duration_seconds = max(0, int(self.duration_seconds))
        elif self.duration_ms is not None:
            self.duration_seconds = max(0, self.duration_ms // 1000)
        if self.file_size_bytes is None and self.filesize is not None:
            self.file_size_bytes = self.filesize
        if self.file_size_bytes is not None:
            self.file_size_bytes = max(0, int(self.file_size_bytes))
        self.filesize = self.file_size_bytes

        # Feed-specific code uses generic, source, and platform-scoped names.
        # Keep them synchronized without discarding the provider's identifiers.
        self.id = self.id or self.sermon_id
        self.item_id = self.item_id or self.platform_item_id or self.source_id or self.sermon_id
        self.platform_item_id = self.platform_item_id or self.item_id
        self.source_id = self.source_id or self.item_id
        self.external_id = self.external_id or self.item_id
        self.platform = self.platform or self.source_platform or self.source
        self.source_platform = self.source_platform or self.platform
        self.source = self.source or self.platform
        self.platform_series_id = self.platform_series_id or self.series_id
        self.series = self.series or self.series_title
        self.series_title = self.series_title or self.series

        self.description = self.description or self.summary_text or self.summary
        self.summary = self.summary or self.summary_text or self.description
        self.scriptures = list(self.scriptures or [])
        self.tags = list(self.tags or [])
        if self.scripture is None and self.scriptures:
            self.scripture = "; ".join(str(value) for value in self.scriptures)
        self.scripture = self.scripture or self.scripture_reference
        self.scripture_reference = self.scripture_reference or self.scripture
        self.bible_book = self.bible_book or self.book_of_bible
        self.book_of_bible = self.book_of_bible or self.bible_book
        self.audio_url = self.audio_url or self.audio_source_url
        self.audio_source_url = self.audio_source_url or self.audio_url
        self.video_url = self.video_url or self.video_source_url or self.hls_url
        self.video_source_url = self.video_source_url or self.video_url or self.hls_url
        self.has_audio = bool(self.has_audio or self.audio_source_url)
        self.has_video = bool(self.has_video or self.video_source_url or self.hls_url)
        self.original_filename = self.original_filename or self.original_media_filename
        self.original_media_filename = self.original_media_filename or self.original_filename
        self.local_path = self.local_path or self.local_media_path
        self.local_media_path = self.local_media_path or self.local_path
        self.error = self.error or self.last_error
        self.last_error = self.last_error or self.error
        self.download_status = self.status
        self.media_format = self.media_format or self.mime_type
        self.canonical_url = self.canonical_url or self.share_url or self.source_url
        self.media_url = self.media_url or self.video_source_url or self.audio_source_url

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "SermonRecord":
        """Build a record from scraper/SQLite data, accepting common aliases."""

        normalized: dict[str, Any] = {}
        valid_fields = cls.__dataclass_fields__
        for key, value in values.items():
            target = FIELD_ALIASES.get(key, key)
            if target in valid_fields:
                normalized[target] = value

        if "raw_metadata" not in normalized:
            normalized["raw_metadata"] = {}
        return cls(**normalized)

    def to_dict(self, *, dates_as_iso: bool = True) -> dict[str, Any]:
        """Return a mutable representation suitable for persistence."""

        values = asdict(self)
        if dates_as_iso and isinstance(values["sermon_date"], date):
            values["sermon_date"] = values["sermon_date"].isoformat()
        return values

    @property
    def checksum(self) -> str | None:
        """Compatibility alias for the SHA-256 digest."""

        return self.sha256


def normalize_status(status: str | ArchiveStatus) -> str:
    """Return a validated string status."""

    value = status.value if isinstance(status, ArchiveStatus) else str(status).strip().lower()
    if value not in ARCHIVE_STATUSES:
        allowed = ", ".join(sorted(ARCHIVE_STATUSES))
        raise ValueError(f"unknown archive status {status!r}; expected one of: {allowed}")
    return value
