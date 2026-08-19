"""Discovery adapter for Calvary Spokane's public legacy archive.

The current Subsplash library omits some records that remain documented by the
church's 2011 sermon catalog and legacy media host.  This module treats those
sources as supplemental evidence: it preserves historical media links even when
they now return 404, but only marks media as available after a public check.
"""

from __future__ import annotations

import hashlib
import html as html_module
import json
import random
import re
import shutil
import subprocess
import time
from collections.abc import Iterable, Mapping
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx

from .discovery import RawResponseStore, extract_bible_book
from .models import SermonRecord
from .utils import parse_sermon_date

WAYBACK_CDX_URL = "https://web.archive.org/cdx/search/cdx"
# Primary catalog pattern plus the alternate domains checked in the 2026-08-19
# domain sweep (see reports/public-source-audit-domain-sweep-2026-08-19.md).
# The alternates hold no sermon content, but keeping them here means future
# re-crawls verify that remains true instead of assuming it.
LEGACY_ARCHIVE_PATTERN = "calvaryspokane.com/sermon/archive/*"
LEGACY_ARCHIVE_PATTERNS = [
    LEGACY_ARCHIVE_PATTERN,
    "calvarychapelspokane.com/*",
    "ccspokane.com/*",
]
LEGACY_PROPHECY_INDEX = "https://media.calvaryspokane.com/C.Mp3/prophecy/"
LEGACY_PLATFORM = "calvary_legacy"
USER_AGENT = (
    "CalvarySpokaneArchiver/1.0 "
    "(public legacy metadata discovery; personal historical research)"
)
_AUDIO_EXTENSIONS = {".aac", ".m4a", ".mp3", ".wav", ".wma"}
_VIDEO_EXTENSIONS = {".flv", ".m3u8", ".m4v", ".mov", ".mp4", ".webm", ".wmv"}
_PROPHECY_FILENAME_RE = re.compile(
    r"^KSE(?P<event_id>\d+)_(?P<year>\d{2})NYE(?P<part>[A-Za-z])\.mp3$",
    re.IGNORECASE,
)


def _plain_text(fragment: str) -> str:
    return " ".join(
        html_module.unescape(re.sub(r"<[^>]+>", " ", fragment)).replace("\xa0", " ").split()
    )


def _attributes(fragment: str) -> dict[str, str]:
    return {
        key.casefold(): html_module.unescape(double_quoted or single_quoted)
        for key, double_quoted, single_quoted in re.findall(
            r"([:\w-]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')", fragment, re.DOTALL
        )
    }


def _extension(url: str | None) -> str:
    if not url:
        return ""
    return Path(unquote(urlparse(url).path)).suffix.casefold()


def _absolute_legacy_url(path_or_url: str | None) -> str | None:
    if not path_or_url:
        return None
    return urljoin("http://calvaryspokane.com/", path_or_url)


def _wayback_url(timestamp: str, original_url: str | None) -> str | None:
    if not timestamp or not original_url:
        return None
    return f"https://web.archive.org/web/{timestamp}id_/{original_url}"


def parse_legacy_listing_page(
    page_html: str,
    *,
    capture_timestamp: str,
    listing_url: str,
    archived_listing_url: str | None = None,
) -> list[dict[str, Any]]:
    """Parse sermon cards from one archived 2011 listing page.

    Media classification is intentionally scoped to ``ul.media`` and based on
    file extensions.  A sermon titled "Watch and Pray" must not become a video
    merely because the word "Watch" appears in its title.
    """

    records: list[dict[str, Any]] = []
    card_pattern = re.compile(
        r"<div\s+class=[\"']sermonListItem[\"']>(.*?</ul>)\s*</div>",
        re.IGNORECASE | re.DOTALL,
    )
    for card in card_pattern.findall(page_html):
        title_match = re.search(
            r"<h3>\s*<a\s+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
            card,
            re.IGNORECASE | re.DOTALL,
        )
        date_match = re.search(r"Date:\s*(\d{1,2}/\d{1,2}/\d{4})", card, re.IGNORECASE)
        if title_match is None or date_match is None:
            continue

        item_path = html_module.unescape(title_match.group(1))
        source_url = _absolute_legacy_url(item_path)
        series_match = re.search(
            r"Series:\s*<a\s+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
            card,
            re.IGNORECASE | re.DOTALL,
        )
        speaker_match = re.search(
            r"Speaker:\s*<a\s+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
            card,
            re.IGNORECASE | re.DOTALL,
        )
        passage_match = re.search(
            r"Passage:\s*(.*?)<br\s*/?>", card, re.IGNORECASE | re.DOTALL
        )
        media_match = re.search(
            r"<ul\s+class=[\"']media[\"']>(.*?)</ul>",
            card,
            re.IGNORECASE | re.DOTALL,
        )
        media: list[dict[str, Any]] = []
        for attribute_text, label_html in re.findall(
            r"<a\b([^>]*)>(.*?)</a>",
            media_match.group(1) if media_match else "",
            re.IGNORECASE | re.DOTALL,
        ):
            attributes = _attributes(attribute_text)
            media_url = attributes.get("href")
            suffix = _extension(media_url)
            kind = (
                "audio"
                if suffix in _AUDIO_EXTENSIONS
                else "video"
                if suffix in _VIDEO_EXTENSIONS
                else "notes"
                if suffix == ".pdf"
                else None
            )
            if kind and media_url:
                media.append(
                    {
                        "kind": kind,
                        "url": media_url,
                        "class": attributes.get("class"),
                        "label": _plain_text(label_html) or None,
                    }
                )

        sermon_date = datetime.strptime(date_match.group(1), "%m/%d/%Y").date().isoformat()
        series_path = html_module.unescape(series_match.group(1)) if series_match else None
        series_url = _absolute_legacy_url(series_path)
        records.append(
            {
                "legacy_id": item_path.rstrip("/").rsplit("/", 1)[-1],
                "title": _plain_text(title_match.group(2)),
                "speaker": _plain_text(speaker_match.group(2)) if speaker_match else None,
                "speaker_path": (
                    html_module.unescape(speaker_match.group(1)) if speaker_match else None
                ),
                "sermon_date": sermon_date,
                "series": _plain_text(series_match.group(2)) if series_match else None,
                "series_path": series_path,
                "series_url": series_url,
                "archived_series_url": _wayback_url(capture_timestamp, series_url),
                "scripture_reference": (
                    _plain_text(passage_match.group(1)) or None if passage_match else None
                ),
                "source_url": source_url,
                "archived_source_url": _wayback_url(capture_timestamp, source_url),
                "listing_url": listing_url,
                "archived_listing_url": archived_listing_url
                or _wayback_url(capture_timestamp, listing_url),
                "wayback_capture_timestamp": capture_timestamp,
                "media": media,
                "audio_urls": [entry["url"] for entry in media if entry["kind"] == "audio"],
                "video_urls": [entry["url"] for entry in media if entry["kind"] == "video"],
                "notes_urls": [entry["url"] for entry in media if entry["kind"] == "notes"],
                "source_kind": "wayback_2011_listing",
            }
        )
    return records


class _DirectoryIndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        href = attributes.get("href")
        if tag.casefold() == "a" and isinstance(href, str):
            self.links.append(href)


def parse_directory_links(page_html: str, base_url: str) -> list[str]:
    """Return public, non-navigation links from an Apache directory index."""

    parser = _DirectoryIndexParser()
    parser.feed(page_html)
    links: list[str] = []
    for href in parser.links:
        if href.startswith(("?", "/")):
            continue
        absolute = urljoin(base_url, href)
        if absolute not in links:
            links.append(absolute)
    return links


def normalize_speaker(value: str | None) -> str | None:
    """Normalize the known one-letter legacy tag typo while preserving it raw."""

    if value and value.strip().casefold() in {"ken orize", "ken ortize"}:
        return "Ken Ortize"
    return value.strip() if value and value.strip() else None


def parse_prophecy_index(
    page_html: str,
    *,
    index_url: str = LEGACY_PROPHECY_INDEX,
) -> list[dict[str, Any]]:
    """Discover explicitly named New Year's Eve files from the public index."""

    records: list[dict[str, Any]] = []
    for media_url in parse_directory_links(page_html, index_url):
        filename = Path(unquote(urlparse(media_url).path)).name
        match = _PROPHECY_FILENAME_RE.match(filename)
        if match is None:
            continue
        year = 2000 + int(match.group("year"))
        part = match.group("part").upper()
        records.append(
            {
                "legacy_id": Path(filename).stem,
                "title": f"{year} New Year's Eve Prophecy Update, Part {part}",
                "speaker": None,
                "sermon_date": f"{year:04d}-12-31",
                "series": "Prophecy Update",
                "scripture_reference": None,
                "source_url": media_url,
                "archived_source_url": None,
                "listing_url": index_url,
                "archived_listing_url": None,
                "series_url": index_url,
                "audio_urls": [media_url],
                "video_urls": [],
                "notes_urls": [],
                "media": [{"kind": "audio", "url": media_url}],
                "source_kind": "legacy_media_directory",
                "filename_evidence": {
                    "event_id": match.group("event_id"),
                    "year": year,
                    "part": part,
                    "filename": filename,
                },
            }
        )
    return records


def _deduplicate(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    deduplicated: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for source in records:
        record = dict(source)
        key = (
            str(record.get("sermon_date") or ""),
            str(record.get("title") or "").casefold(),
            str(record.get("speaker") or "").casefold(),
            str(record.get("source_url") or ""),
        )
        if key not in deduplicated:
            deduplicated[key] = record
            continue
        existing = deduplicated[key]
        for field in ("audio_urls", "video_urls", "notes_urls"):
            existing[field] = list(
                dict.fromkeys([*(existing.get(field) or []), *(record.get(field) or [])])
            )
    return sorted(
        deduplicated.values(),
        key=lambda item: (str(item.get("sermon_date") or ""), str(item.get("title") or "")),
    )


def _source_evidence_id(record: Mapping[str, Any]) -> str:
    identity = "\0".join(
        str(record.get(key) or "")
        for key in ("source_kind", "legacy_id", "sermon_date", "source_url")
    )
    return "legacy:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def _sermon_id(record: Mapping[str, Any]) -> str:
    identity = "\0".join(
        str(record.get(key) or "") for key in ("legacy_id", "sermon_date", "title")
    )
    return "legacy:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def _clean_media_urls(record: Mapping[str, Any], field: str, extensions: set[str]) -> list[str]:
    return [
        str(url)
        for url in record.get(field) or []
        if isinstance(url, str) and _extension(url) in extensions
    ]


def _date_in_range(value: str, start_date: date, end_date: date) -> bool:
    parsed = parse_sermon_date(value)
    return parsed is not None and start_date <= parsed <= end_date


class LegacyArchiveDiscovery:
    """Polite supplemental crawler/importer for public legacy sources."""

    def __init__(
        self,
        root: str | Path,
        db: Any,
        *,
        cache_dir: str | Path | None = None,
        client: httpx.Client | None = None,
        delay_range: tuple[float, float] = (0.45, 0.9),
        retries: int = 4,
        sleep: Callable[[float], None] = time.sleep,
        random_source: random.Random | None = None,
    ) -> None:
        self.root = Path(root)
        self.db = db
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.delay_range = delay_range
        self.retries = retries
        self.sleep = sleep
        self.random = random_source or random.Random()
        self._owns_client = client is None
        self.client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=90.0
        )
        if client is not None:
            self.client.headers.setdefault("User-Agent", USER_AGENT)
        self.raw_store: RawResponseStore | None = None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> "LegacyArchiveDiscovery":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _delay(self, attempt: int = 0) -> None:
        low, high = self.delay_range
        self.sleep(self.random.uniform(low, high) + (1.25 * (2**attempt) if attempt else 0))

    def _request(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        label: str,
        method: str = "GET",
    ) -> httpx.Response:
        for attempt in range(self.retries + 1):
            self._delay(attempt)
            try:
                response = self.client.request(method, url, params=params)
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt >= self.retries:
                    raise
                continue
            if self.raw_store is not None and method == "GET":
                self.raw_store.save(response, label)
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < self.retries:
                    continue
            if method == "GET":
                response.raise_for_status()
            return response
        raise RuntimeError(f"request retry loop exhausted for {url}")

    def _load_cached_records(self) -> list[dict[str, Any]]:
        if self.cache_dir is None:
            return []
        path = self.cache_dir / "legacy-records-target.json"
        if not path.exists():
            raise FileNotFoundError(f"legacy cache is missing {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"legacy cache must contain a JSON array: {path}")
        return [dict(item) for item in payload if isinstance(item, Mapping)]

    def _cached_availability(self) -> dict[str, dict[str, Any]]:
        if self.cache_dir is None:
            return {}
        path = self.cache_dir / "legacy-audio-availability.json"
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_results = payload.get("results") if isinstance(payload, Mapping) else None
        results = raw_results if isinstance(raw_results, list) else []
        return {
            str(item["url"]): dict(item)
            for item in results
            if isinstance(item, Mapping) and isinstance(item.get("url"), str)
        }

    def _crawl_wayback(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        captures: dict[int, tuple[str, str]] = {}
        for pattern in LEGACY_ARCHIVE_PATTERNS:
            response = self._request(
                WAYBACK_CDX_URL,
                params={
                    "url": pattern,
                    "from": "2011",
                    "to": "2012",
                    "output": "json",
                    "fl": "timestamp,original,statuscode,mimetype",
                    "filter": "statuscode:200",
                    "collapse": "urlkey",
                    "limit": "50000",
                },
                label="wayback_cdx_legacy_archive",
            )
            payload = response.json()
            for row in payload[1:] if isinstance(payload, list) else []:
                if not isinstance(row, list) or len(row) < 2:
                    continue
                timestamp, original_url = str(row[0]), str(row[1])
                values = parse_qs(urlparse(original_url).query).get("start", ["0"])
                offset_text = values[0] if values else "0"
                if not offset_text.isdigit():
                    continue
                offset = int(offset_text)
                if offset not in captures or timestamp > captures[offset][0]:
                    captures[offset] = (timestamp, original_url)

        records: list[dict[str, Any]] = []
        for offset, (timestamp, original_url) in sorted(captures.items()):
            replay_url = _wayback_url(timestamp, original_url)
            assert replay_url is not None
            page = self._request(replay_url, label=f"legacy_listing_{offset:04d}")
            parsed = parse_legacy_listing_page(
                page.text,
                capture_timestamp=timestamp,
                listing_url=original_url,
                archived_listing_url=replay_url,
            )
            records.extend(parsed)
            dates = [parse_sermon_date(item.get("sermon_date")) for item in parsed]
            valid_dates = [value for value in dates if value is not None]
            if valid_dates and max(valid_dates) < start_date:
                break
        return [
            item
            for item in _deduplicate(records)
            if _date_in_range(str(item.get("sermon_date") or ""), start_date, end_date)
        ]

    @staticmethod
    def _ffprobe(url: str) -> dict[str, Any]:
        executable = shutil.which("ffprobe")
        if executable is None:
            return {"error": "ffprobe_not_found"}
        command = [
            executable,
            "-v",
            "error",
            "-show_entries",
            "format=filename,format_name,duration,size,bit_rate:format_tags",
            "-of",
            "json",
            url,
        ]
        try:
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=180, check=True
            )
            payload = json.loads(completed.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}
        if not isinstance(payload, Mapping):
            return {}
        format_metadata = payload.get("format")
        return dict(format_metadata) if isinstance(format_metadata, Mapping) else {}

    def _prophecy_records(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        response = self._request(LEGACY_PROPHECY_INDEX, label="legacy_prophecy_index")
        records = parse_prophecy_index(response.text)
        selected = [
            item
            for item in records
            if _date_in_range(str(item.get("sermon_date") or ""), start_date, end_date)
        ]
        for item in selected:
            media_url = str(item["audio_urls"][0])
            probe = self._ffprobe(media_url)
            raw_tags = probe.get("tags")
            tags: Mapping[str, Any] = raw_tags if isinstance(raw_tags, Mapping) else {}
            raw_title_value = tags.get("title")
            raw_artist_value = tags.get("artist")
            raw_album_value = tags.get("album")
            raw_title = raw_title_value if isinstance(raw_title_value, str) else None
            raw_artist = raw_artist_value if isinstance(raw_artist_value, str) else None
            raw_album = raw_album_value if isinstance(raw_album_value, str) else None
            if raw_title:
                item["title"] = raw_title
            item["speaker"] = normalize_speaker(raw_artist)
            if raw_album:
                item["series"] = raw_album
            try:
                item["duration_seconds"] = int(float(probe["duration"]))
            except (KeyError, TypeError, ValueError):
                item["duration_seconds"] = None
            item["ffprobe_metadata"] = probe
        return selected

    def _availability(self, url: str, cached: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
        if url in cached:
            return dict(cached[url])
        response = self._request(url, label="media_head", method="HEAD")
        return {
            "url": url,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "status_code": response.status_code,
            "final_url": str(response.url),
            "content_type": response.headers.get("content-type"),
            "content_length": (
                int(response.headers["content-length"])
                if response.headers.get("content-length", "").isdigit()
                else None
            ),
            "available": 200 <= response.status_code < 400,
        }

    def run(
        self,
        *,
        start_date: str | date = "2004-06-01",
        end_date: str | date = "2010-08-31",
        limit: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        start = parse_sermon_date(start_date)
        end = parse_sermon_date(end_date)
        if start is None or end is None:
            raise ValueError("start_date and end_date must be valid dates")
        if start > end:
            raise ValueError("start_date must not be after end_date")
        if limit is not None and limit < 0:
            raise ValueError("limit must not be negative")

        run_id = self.db.start_crawl(
            source_url=WAYBACK_CDX_URL,
            metadata={
                "source": LEGACY_PLATFORM,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "cache_dir": str(self.cache_dir) if self.cache_dir else None,
                "dry_run": dry_run,
            },
        )
        self.raw_store = RawResponseStore(self.root, f"legacy-{run_id}")
        stats = {
            "records_discovered": 0,
            "records_matched": 0,
            "records_added": 0,
            "records_enriched": 0,
            "sources_upserted": 0,
            "audio_available": 0,
            "audio_unavailable": 0,
            "historical_video_links": 0,
            "video_available": 0,
        }
        try:
            listing_records = (
                self._load_cached_records()
                if self.cache_dir is not None
                else self._crawl_wayback(start, end)
            )
            listing_records = [
                item
                for item in listing_records
                if _date_in_range(str(item.get("sermon_date") or ""), start, end)
            ]
            records = _deduplicate([*listing_records, *self._prophecy_records(start, end)])
            if limit is not None:
                records = records[:limit]
            stats["records_discovered"] = len(records)
            cached_availability = self._cached_availability()

            for raw_record in records:
                audio_urls = _clean_media_urls(raw_record, "audio_urls", _AUDIO_EXTENSIONS)
                video_urls = _clean_media_urls(raw_record, "video_urls", _VIDEO_EXTENSIONS)
                stats["historical_video_links"] += int(bool(video_urls))

                lookup = SermonRecord.from_mapping(
                    {
                        "sermon_id": _sermon_id(raw_record),
                        "platform": LEGACY_PLATFORM,
                        "platform_item_id": str(raw_record.get("legacy_id") or ""),
                        "title": str(raw_record.get("title") or ""),
                        "speaker": normalize_speaker(raw_record.get("speaker")),
                        "sermon_date": str(raw_record.get("sermon_date") or ""),
                        "canonical_url": raw_record.get("archived_source_url")
                        or raw_record.get("source_url"),
                        "media_url": audio_urls[0] if audio_urls else None,
                        "audio_url": audio_urls[0] if audio_urls else None,
                    }
                )
                duplicate = self.db.find_duplicate(lookup)
                if duplicate is not None:
                    stats["records_matched"] += 1

                should_check_audio = bool(audio_urls) and (
                    duplicate is None or not bool(duplicate.has_audio)
                )
                audio_check = (
                    self._availability(audio_urls[0], cached_availability)
                    if should_check_audio
                    else {
                        "url": audio_urls[0] if audio_urls else None,
                        "available": bool(duplicate and duplicate.has_audio),
                        "status_code": None,
                        "checked_at": None,
                    }
                )
                audio_available = bool(audio_check.get("available"))
                stats["audio_available" if audio_available else "audio_unavailable"] += int(
                    bool(audio_urls)
                )

                video_check: dict[str, Any] = {}
                if video_urls:
                    video_check = self._availability(video_urls[0], {})
                    if video_check.get("available"):
                        stats["video_available"] += 1
                video_available = bool(video_check.get("available"))
                source_page = raw_record.get("archived_source_url") or raw_record.get("source_url")
                bible_book = extract_bible_book(
                    raw_record.get("series"),
                    [str(raw_record.get("scripture_reference") or "")],
                )
                status = (
                    "metadata_complete"
                    if video_available
                    else "audio_only"
                    if audio_available
                    else "no_media"
                )
                normalized = SermonRecord.from_mapping(
                    {
                        "sermon_id": _sermon_id(raw_record),
                        "platform": LEGACY_PLATFORM,
                        "source_platform": LEGACY_PLATFORM,
                        "item_id": str(raw_record.get("legacy_id") or ""),
                        "platform_item_id": str(raw_record.get("legacy_id") or ""),
                        "title": str(raw_record.get("title") or ""),
                        "speaker": normalize_speaker(raw_record.get("speaker")),
                        "sermon_date": str(raw_record.get("sermon_date") or ""),
                        "series": raw_record.get("series"),
                        "scripture": raw_record.get("scripture_reference"),
                        "scripture_reference": raw_record.get("scripture_reference"),
                        "bible_book": bible_book,
                        "book_of_bible": bible_book,
                        "service_type": (
                            "New Year's Eve"
                            if raw_record.get("source_kind") == "legacy_media_directory"
                            else None
                        ),
                        "duration_seconds": raw_record.get("duration_seconds"),
                        "canonical_url": source_page,
                        "source_url": source_page,
                        "series_url": raw_record.get("archived_series_url")
                        or raw_record.get("series_url"),
                        "media_url": (
                            video_urls[0]
                            if video_available
                            else audio_urls[0]
                            if audio_available
                            else None
                        ),
                        "audio_url": audio_urls[0] if audio_available else None,
                        "audio_source_url": audio_urls[0] if audio_available else None,
                        "video_url": video_urls[0] if video_available else None,
                        "video_source_url": video_urls[0] if video_available else None,
                        "has_audio": audio_available,
                        "has_video": video_available,
                        "original_media_filename": (
                            Path(unquote(urlparse(audio_urls[0]).path)).name
                            if audio_urls
                            else None
                        ),
                        "media_type": (
                            "audio_video"
                            if audio_available and video_available
                            else "video"
                            if video_available
                            else "audio"
                            if audio_available
                            else None
                        ),
                        "media_format": (
                            _extension(video_urls[0] if video_available else audio_urls[0])
                            .lstrip(".")
                            if video_available or audio_available
                            else None
                        ),
                        "status": status,
                        "notes": (
                            "Supplemental public legacy archive record. Historical media URLs "
                            "that are no longer reachable are retained in sermon_sources."
                        ),
                        "raw_metadata": {
                            "legacy_source": raw_record,
                            "audio_availability": audio_check,
                            "video_availability": video_check or None,
                        },
                    }
                )

                canonical = duplicate
                if not dry_run:
                    if duplicate is None:
                        canonical = self.db.upsert_sermon(normalized)
                        stats["records_added"] += 1
                    elif audio_available and not duplicate.has_audio:
                        values = duplicate.to_dict(dates_as_iso=False)
                        values.update(
                            {
                                "audio_url": audio_urls[0],
                                "audio_source_url": audio_urls[0],
                                "media_url": audio_urls[0],
                                "has_audio": True,
                                "media_type": "audio",
                                "media_format": _extension(audio_urls[0]).lstrip("."),
                                "status": "audio_only",
                                "raw_metadata": {
                                    **duplicate.raw_metadata,
                                    "legacy_media_recovery": {
                                        "source_id": _source_evidence_id(raw_record),
                                        "audio_url": audio_urls[0],
                                        "availability": audio_check,
                                    },
                                },
                            }
                        )
                        canonical = self.db.upsert_sermon(SermonRecord.from_mapping(values))
                        stats["records_enriched"] += 1

                    assert canonical is not None
                    self.db.upsert_source_evidence(
                        source_id=_source_evidence_id(raw_record),
                        sermon_id=canonical.sermon_id,
                        source_platform=LEGACY_PLATFORM,
                        platform_item_id=str(raw_record.get("legacy_id") or ""),
                        source_url=raw_record.get("source_url"),
                        archived_source_url=raw_record.get("archived_source_url"),
                        listing_url=raw_record.get("listing_url"),
                        archived_listing_url=raw_record.get("archived_listing_url"),
                        series_url=raw_record.get("archived_series_url")
                        or raw_record.get("series_url"),
                        audio_url=audio_urls[0] if audio_urls else None,
                        audio_available=audio_available if audio_urls else None,
                        audio_status_code=audio_check.get("status_code"),
                        video_url=video_urls[0] if video_urls else None,
                        video_available=video_available if video_urls else None,
                        video_status_code=video_check.get("status_code"),
                        checked_at=audio_check.get("checked_at")
                        or video_check.get("checked_at"),
                        notes=(
                            "Historical video availability is not promoted to the canonical "
                            "record unless the URL is currently reachable."
                        ),
                        raw_metadata=raw_record,
                    )
                    stats["sources_upserted"] += 1

            self.db.finish_crawl(
                run_id,
                status="partial" if limit is not None else "completed",
                pages_seen=self.raw_store.responses_saved,
                items_seen=stats["records_discovered"],
                items_added=stats["records_added"],
                items_updated=stats["records_enriched"],
                target_records=stats["records_discovered"],
            )
            return {"run_id": run_id, "dry_run": dry_run, "limit": limit, **stats}
        except Exception as exc:
            self.db.finish_crawl(run_id, status="failed", error=f"{type(exc).__name__}: {exc}")
            raise


def discover_legacy(
    root: str | Path,
    db: Any,
    *,
    start_date: str | date = "2004-06-01",
    end_date: str | date = "2010-08-31",
    **kwargs: Any,
) -> dict[str, Any]:
    """One-shot wrapper around :class:`LegacyArchiveDiscovery`."""

    run_options = {
        key: kwargs.pop(key) for key in tuple(kwargs) if key in {"limit", "dry_run"}
    }
    with LegacyArchiveDiscovery(root, db, **kwargs) as crawler:
        return crawler.run(start_date=start_date, end_date=end_date, **run_options)
