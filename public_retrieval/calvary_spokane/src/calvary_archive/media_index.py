"""Auditable recursive inventory of Calvary Spokane's public legacy media trees.

Directory listings are evidence that a file was publicly exposed, not proof of a
sermon date or even proof that the file can still be read.  This module keeps
those facts separate: it records listings first, reconciles strong URL/filename
identifiers against the canonical inventory, then performs bounded ``ffprobe``
metadata checks only for unresolved target candidates or known no-media records.
"""

from __future__ import annotations

import csv
import hashlib
import html as html_module
import json
import posixpath
import random
import re
import shutil
import subprocess
import time
from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urljoin, urlparse

import httpx

from .discovery import RawResponseStore, extract_bible_book
from .utils import parse_sermon_date

MEDIA_INDEX_ROOTS = (
    "https://media.calvaryspokane.com/C.Mp3/",
    "https://media.calvaryspokane.com/mp3/",
    "https://media.calvaryspokane.com/C.Video/",
)
USER_AGENT = (
    "CalvarySpokaneArchiver/1.0 "
    "(public legacy-media index audit; personal historical research)"
)
_AUDIO_EXTENSIONS = {".aac", ".m4a", ".mp3", ".wav", ".wma"}
_VIDEO_EXTENSIONS = {".flv", ".m3u8", ".m4v", ".mov", ".mp4", ".webm", ".wmv"}
_MEDIA_EXTENSIONS = _AUDIO_EXTENSIONS | _VIDEO_EXTENSIONS
_LEGACY_ID_RE = re.compile(r"^(KSE|KT|K)(\d+)", re.IGNORECASE)
_GUEST_ID_RE = re.compile(r"^GS(\d+)", re.IGNORECASE)
_FULL_DATE_PATTERNS = (
    re.compile(r"(?<!\d)(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)"),
    re.compile(r"(?<!\d)(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})(?!\d)"),
)
_SHORT_DATE_PATTERN = re.compile(
    r"(?<!\d)(?=(\d{1,2})[-/.](\d{1,2})[-/.](\d{2})(?!\d))"
)
_YEAR_MONTH_PATTERN = re.compile(r"(?<!\d)(20\d{2})[-/.](\d{1,2})(?![-/.]\d)")
_YEAR_RE = re.compile(r"(?<!\d)(20\d{2})(?!\d)")
_TRUSTED_DATE_TAGS = {
    "album",
    "comment",
    "date",
    "description",
    "title",
    "year",
}
_GUEST_SPEAKER_PATTERNS = (
    (re.compile(r"Scott\s*Douglass", re.IGNORECASE), "Scott Douglass"),
    (re.compile(r"Bob\s*Davis", re.IGNORECASE), "Bob Davis"),
    (re.compile(r"Steve\s*Whinery", re.IGNORECASE), "Steve Whinery"),
    (re.compile(r"Josh\s*O['’]?\s*Donnell", re.IGNORECASE), "Josh O'Donnell"),
    (re.compile(r"Cory\s*Kirkham", re.IGNORECASE), "Cory Kirkham"),
    (re.compile(r"J\.?\s*D\.?\s*Farag", re.IGNORECASE), "J. D. Farag"),
    (re.compile(r"John\s*Michaels", re.IGNORECASE), "John Michaels"),
    (re.compile(r"Josh\s*Nerren", re.IGNORECASE), "Josh Nerren"),
    (re.compile(r"Don\s*McClure", re.IGNORECASE), "Don McClure"),
    (re.compile(r"\bWalid\b", re.IGNORECASE), "Walid"),
)
_TARGET_REVIEW_SEGMENTS = {
    "01-gen-old",
    "1stjohn series 2009-10",
    "2nd john series 2010",
    "44-act-old",
    "66-rev-old",
    "events",
    "guest",
    "jd farag",
    "kse",
    "other",
    "ortize-ben",
    "ortize-ken",
    "prophecy",
    "special",
    "spiritual_leadership_series-09-10",
}


class _IndexLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str | None]] = []
        self._current: dict[str, str | None] | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "a":
            return
        href = dict(attrs).get("href")
        if isinstance(href, str):
            self._current = {"href": href, "label": None}
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._current is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "a" and self._current is not None:
            self._current["label"] = "".join(self._text).strip() or None
            self.links.append(self._current)
            self._current = None
            self._text = []


def normalized_media_url(url: str) -> str:
    """Return a scheme-insensitive, path-case-preserving comparison key."""

    parsed = urlparse(url)
    host = (parsed.hostname or "").casefold()
    port = f":{parsed.port}" if parsed.port else ""
    decoded_path = unquote(parsed.path)
    normalized_path = posixpath.normpath(decoded_path)
    if decoded_path.endswith("/") and not normalized_path.endswith("/"):
        normalized_path += "/"
    if not normalized_path.startswith("/"):
        normalized_path = "/" + normalized_path
    return f"{host}{port}{normalized_path}"


def _listed_details(page_html: str) -> dict[str, tuple[str | None, str | None]]:
    details: dict[str, tuple[str | None, str | None]] = {}
    pattern = re.compile(
        r"<a\b[^>]*href=[\"'](?P<href>[^\"']+)[\"'][^>]*>.*?</a>"
        r"(?P<tail>[^\r\n<]*)",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(page_html):
        href = html_module.unescape(match.group("href"))
        tail = " ".join(html_module.unescape(match.group("tail")).split())
        metadata = re.search(
            r"(?P<modified>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s+(?P<size>\S+)",
            tail,
        )
        details[href] = (
            metadata.group("modified") if metadata else None,
            metadata.group("size") if metadata else None,
        )
    return details


def parse_media_index(
    page_html: str,
    *,
    index_url: str,
    source_root: str,
) -> list[dict[str, Any]]:
    """Parse and contain links from one Apache-style public directory index."""

    index = urlparse(index_url)
    root = urlparse(source_root)
    root_path = root.path if root.path.endswith("/") else root.path + "/"
    if index.hostname != root.hostname or not index.path.startswith(root_path):
        raise ValueError("index_url must be contained beneath source_root")

    parser = _IndexLinkParser()
    parser.feed(page_html)
    details = _listed_details(page_html)
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for link in parser.links:
        href = str(link["href"] or "").strip()
        if not href or href.startswith(("?", "#")):
            continue
        candidate = urlparse(urljoin(index_url, href))
        if candidate.scheme not in {"http", "https"} or candidate.hostname != root.hostname:
            continue
        decoded_path = unquote(candidate.path)
        decoded_root = unquote(root_path)
        normalized_path = posixpath.normpath(decoded_path)
        if decoded_path.endswith("/") and not normalized_path.endswith("/"):
            normalized_path += "/"
        if not normalized_path.startswith(decoded_root) or normalized_path == decoded_root.rstrip("/"):
            continue
        clean_url = candidate._replace(query="", fragment="").geturl()
        if clean_url in seen:
            continue
        seen.add(clean_url)
        is_directory = decoded_path.endswith("/")
        extension = Path(decoded_path).suffix.casefold()
        if not is_directory and extension not in _MEDIA_EXTENSIONS:
            continue
        listed_modified, listed_size = details.get(href, (None, None))
        entries.append(
            {
                "url": clean_url,
                "label": link.get("label"),
                "is_directory": is_directory,
                "extension": extension,
                "listed_last_modified": listed_modified,
                "listed_size": listed_size,
            }
        )
    return sorted(entries, key=lambda entry: str(entry["url"]))


def legacy_identifier(value: str) -> tuple[str, int] | None:
    stem = Path(unquote(urlparse(value).path)).stem if "/" in value else Path(value).stem
    match = _LEGACY_ID_RE.match(stem)
    if match is None:
        return None
    return match.group(1).upper(), int(match.group(2))


def _probe_tags(probe: Mapping[str, Any]) -> dict[str, str]:
    raw_tags = probe.get("tags")
    if not isinstance(raw_tags, Mapping):
        return {}
    return {
        str(key).casefold(): str(value).strip()
        for key, value in raw_tags.items()
        if value is not None and str(value).strip()
    }


def probe_date_evidence(probe: Mapping[str, Any]) -> dict[str, Any]:
    """Extract explicit dates from trusted descriptive tags.

    Arbitrary private metadata can contain production-tool timestamps unrelated
    to the sermon.  In particular, embedded XMP source-ingredient dates must not
    turn a modern file into a historical candidate.  Two-digit title dates are
    accepted because the legacy guest archive uses that format, but the expanded
    year is still retained as source evidence rather than silently inferred.
    """

    tags = _probe_tags(probe)
    trusted_values = [
        value for key, value in tags.items() if key in _TRUSTED_DATE_TAGS
    ]
    text_values = [*trusted_values, str(probe.get("filename") or "")]
    full_dates: set[str] = set()
    years: set[int] = set()
    year_months: set[str] = set()
    for text in text_values:
        for pattern_index, pattern in enumerate(_FULL_DATE_PATTERNS):
            for match in pattern.finditer(text):
                if pattern_index == 0:
                    year, month, day = (int(value) for value in match.groups())
                else:
                    month, day, year = (int(value) for value in match.groups())
                try:
                    full_dates.add(date(year, month, day).isoformat())
                except ValueError:
                    continue
        for match in _SHORT_DATE_PATTERN.finditer(text):
            month, day, short_year = (int(value) for value in match.groups())
            year = 2000 + short_year if short_year < 70 else 1900 + short_year
            try:
                full_dates.add(date(year, month, day).isoformat())
            except ValueError:
                continue
        for match in _YEAR_MONTH_PATTERN.finditer(text):
            year, month = (int(value) for value in match.groups())
            if 1 <= month <= 12:
                year_months.add(f"{year:04d}-{month:02d}")
        years.update(int(match.group(1)) for match in _YEAR_RE.finditer(text))
    return {
        "full_dates": sorted(full_dates),
        "year_months": sorted(year_months),
        "years": sorted(years),
        "tags": tags,
        "trusted_date_tags": sorted(
            key for key in tags if key in _TRUSTED_DATE_TAGS
        ),
    }


def _media_id(url: str) -> str:
    digest = hashlib.sha256(normalized_media_url(url).encode("utf-8")).hexdigest()[:24]
    return f"legacy-media:{digest}"


def _candidate_sermon_id(media_id: str) -> str:
    suffix = media_id.split(":", 1)[-1]
    return f"legacy-guest:{suffix}"


def _duration_seconds(probe: Mapping[str, Any]) -> int | None:
    try:
        return max(0, int(float(probe["duration"])))
    except (KeyError, TypeError, ValueError):
        return None


def _guest_speaker(tags: Mapping[str, str], raw_title: str) -> str | None:
    for field in ("artist", "album_artist"):
        value = str(tags.get(field) or "").strip()
        if value:
            return value
    for pattern, normalized in _GUEST_SPEAKER_PATTERNS:
        if pattern.search(raw_title):
            return normalized
    return None


def _candidate_path_kind(asset: Mapping[str, Any]) -> str | None:
    path = unquote(str(asset.get("relative_path") or "")).casefold()
    if path.startswith("guest/"):
        return "guest"
    if path.startswith("inwplc/inwplc2009/"):
        return "conference"
    return None


def normalize_guest_media_candidate(
    asset: Mapping[str, Any],
    *,
    start_date: date,
    end_date: date,
) -> dict[str, Any] | None:
    """Normalize a strongly bounded legacy guest/session candidate.

    Exact dates are promoted only for ordinary Sunday or Thursday services.
    Conflicting dates, year-only conference records, and chronologically bounded
    guest files remain undated review records.  This deliberately favors an
    auditable candidate over a guessed sermon date.
    """

    path_kind = _candidate_path_kind(asset)
    if path_kind is None or str(asset.get("media_kind") or "") != "audio":
        return None
    raw_probe = asset.get("ffprobe_metadata")
    if isinstance(raw_probe, str):
        try:
            raw_probe = json.loads(raw_probe)
        except json.JSONDecodeError:
            raw_probe = {}
    probe = dict(raw_probe) if isinstance(raw_probe, Mapping) else {}
    if asset.get("probe_error") or not probe:
        return None
    duration = _duration_seconds(probe)
    if duration is None or duration < 20 * 60:
        return None

    date_evidence = probe_date_evidence(probe)
    explicit_dates = [date.fromisoformat(value) for value in date_evidence["full_dates"]]
    in_range_dates = [value for value in explicit_dates if start_date <= value <= end_date]
    if explicit_dates and not in_range_dates:
        return None

    target_years = [
        year
        for year in date_evidence["years"]
        if start_date.year <= year <= end_date.year
    ]
    target_path_year = any(
        start_date.year <= int(value) <= end_date.year
        for value in _YEAR_RE.findall(str(asset.get("relative_path") or ""))
    )
    guest_id_match = _GUEST_ID_RE.match(Path(str(asset.get("filename") or "")).stem)
    guest_id = int(guest_id_match.group(1)) if guest_id_match else None
    bounded_guest_id = bool(
        path_kind == "guest" and guest_id is not None and 1060 <= guest_id <= 1142
    )

    # A year-month after the inclusive cutoff is stronger than a generic year
    # tag.  GS1149, for example, explicitly says 2010-11 and is out of scope.
    year_months = [str(value) for value in date_evidence.get("year_months") or []]
    if year_months and not in_range_dates:
        first_scope_month = f"{start_date.year:04d}-{start_date.month:02d}"
        last_scope_month = f"{end_date.year:04d}-{end_date.month:02d}"
        if all(value < first_scope_month or value > last_scope_month for value in year_months):
            return None

    if not (in_range_dates or target_years or target_path_year or bounded_guest_id):
        return None

    trusted_service_date = (
        in_range_dates[0]
        if len(in_range_dates) == 1 and in_range_dates[0].weekday() in {3, 6}
        else None
    )
    tier = (
        "confirmed_exact_date"
        if trusted_service_date is not None
        else "conflicting_exact_date"
        if in_range_dates
        else "confirmed_target_year"
        if target_years or target_path_year
        else "identifier_bounded_review"
    )
    tags = date_evidence["tags"]
    raw_title = str(tags.get("title") or asset.get("filename") or "").strip()
    album = str(tags.get("album") or "").strip()
    series = (
        "INWPLC 2009"
        if path_kind == "conference"
        else album
        if album.casefold() == "the israel of the bible"
        else None
    )
    scripture_reference = album if re.search(r"\d", album) else None
    bible_book = extract_bible_book(series, [raw_title, album])
    media_url = str(asset.get("media_url") or "")
    media_id = str(asset.get("media_id") or _media_id(media_url))
    status = "audio_only" if trusted_service_date is not None else "needs_review"
    record = {
        "sermon_id": _candidate_sermon_id(media_id),
        "platform": "calvary_legacy_media_index",
        "source_platform": "calvary_legacy_media_index",
        "item_id": Path(str(asset.get("filename") or "")).stem,
        "platform_item_id": Path(str(asset.get("filename") or "")).stem,
        "title": raw_title,
        "speaker": _guest_speaker(tags, raw_title),
        "sermon_date": trusted_service_date.isoformat() if trusted_service_date else None,
        "series": series,
        "scripture": scripture_reference,
        "scripture_reference": scripture_reference,
        "bible_book": bible_book,
        "book_of_bible": bible_book,
        "topic": raw_title,
        "service_type": "Conference session" if path_kind == "conference" else "Guest message",
        "duration_seconds": duration,
        "canonical_url": media_url,
        "source_url": media_url,
        "series_url": asset.get("parent_index_url"),
        "media_url": media_url,
        "audio_url": media_url,
        "audio_source_url": media_url,
        "has_audio": True,
        "has_video": False,
        "original_media_filename": asset.get("filename"),
        "media_type": "audio",
        "media_format": str(asset.get("extension") or "mp3").lstrip("."),
        "status": status,
        "notes": (
            "Recovered from a public legacy guest-media index using an embedded source-title "
            "date."
            if trusted_service_date
            else "Public legacy guest/session recording retained without guessing an exact date."
        ),
        "raw_metadata": {
            "legacy_media_candidate_reconciliation": {
                "tier": tier,
                "asset": dict(asset),
                "ffprobe": probe,
                "date_evidence": date_evidence,
            }
        },
    }
    return {
        "tier": tier,
        "record": record,
        "asset": dict(asset),
        "date_evidence": date_evidence,
    }


def _match_id(
    run_id: int,
    media_id: str,
    sermon_id: str | None,
    classification: str,
) -> str:
    identity = "\0".join((str(run_id), media_id, sermon_id or "", classification))
    return "legacy-match:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def _target_path_hint(asset: Mapping[str, Any]) -> bool:
    segments = {
        segment.casefold()
        for segment in unquote(str(asset.get("relative_path") or "")).split("/")[:-1]
        if segment
    }
    return bool(segments & _TARGET_REVIEW_SEGMENTS)


class LegacyMediaIndexAudit:
    """Polite, resumable metadata inventory of the public legacy media roots."""

    def __init__(
        self,
        root: str | Path,
        db: Any,
        *,
        media_roots: Sequence[str] = MEDIA_INDEX_ROOTS,
        client: httpx.Client | None = None,
        delay_range: tuple[float, float] = (0.3, 0.7),
        retries: int = 3,
        sleep: Callable[[float], None] = time.sleep,
        random_source: random.Random | None = None,
    ) -> None:
        self.root = Path(root)
        self.db = db
        self.media_roots = tuple(media_roots)
        self.delay_range = delay_range
        self.retries = retries
        self.sleep = sleep
        self.random = random_source or random.Random()
        self._owns_client = client is None
        self.client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=60.0
        )
        if client is not None:
            self.client.headers.setdefault("User-Agent", USER_AGENT)
        self.raw_store: RawResponseStore | None = None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> "LegacyMediaIndexAudit":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _delay(self, attempt: int = 0) -> None:
        low, high = self.delay_range
        self.sleep(self.random.uniform(low, high) + (1.0 * (2**attempt) if attempt else 0))

    def _request(self, url: str, *, label: str) -> httpx.Response:
        for attempt in range(self.retries + 1):
            self._delay(attempt)
            try:
                response = self.client.get(url)
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt >= self.retries:
                    raise
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < self.retries:
                    continue
            response.raise_for_status()
            if self.raw_store is not None:
                self.raw_store.save(response, label)
            return response
        raise RuntimeError(f"request retry loop exhausted for {url}")

    @staticmethod
    def _ffprobe(url: str) -> dict[str, Any]:
        executable = shutil.which("ffprobe")
        if executable is None:
            return {"error": "ffprobe_not_found"}
        command = [
            executable,
            "-v",
            "error",
            "-probesize",
            "2097152",
            "-analyzeduration",
            "3000000",
            "-show_entries",
            "format=filename,format_name,duration,size,bit_rate:format_tags",
            "-of",
            "json",
            url,
        ]
        try:
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=90, check=True
            )
            payload = json.loads(completed.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}
        format_metadata = payload.get("format") if isinstance(payload, Mapping) else None
        return dict(format_metadata) if isinstance(format_metadata, Mapping) else {}

    def _enumerate(
        self,
        *,
        run_id: int,
        max_directories: int | None,
        dry_run: bool,
    ) -> tuple[list[dict[str, Any]], int, bool, int, int]:
        assets: dict[str, dict[str, Any]] = {}
        directories_seen = 0
        inserted = 0
        updated = 0
        complete = True
        for source_root in self.media_roots:
            queue: deque[str] = deque([source_root])
            visited: set[str] = set()
            while queue:
                if max_directories is not None and directories_seen >= max_directories:
                    complete = False
                    break
                index_url = queue.popleft()
                if index_url in visited:
                    continue
                visited.add(index_url)
                response = self._request(
                    index_url,
                    label=f"media_index_{hashlib.sha256(index_url.encode()).hexdigest()[:12]}",
                )
                directories_seen += 1
                entries = parse_media_index(
                    response.text, index_url=index_url, source_root=source_root
                )
                child_directories = [entry for entry in entries if entry["is_directory"]]
                queue.extend(str(entry["url"]) for entry in child_directories)
                media_entries = [entry for entry in entries if not entry["is_directory"]]
                if not dry_run:
                    self.db.record_listing_audit(
                        index_url,
                        len(media_entries),
                        run_id=run_id,
                        item_ids=(str(entry["url"]) for entry in media_entries),
                        notes=(
                            f"Public legacy media index; child directories={len(child_directories)}"
                        ),
                    )
                root_path = unquote(urlparse(source_root).path)
                for entry in media_entries:
                    media_url = str(entry["url"])
                    path = unquote(urlparse(media_url).path)
                    extension = str(entry["extension"])
                    asset = {
                        "media_id": _media_id(media_url),
                        "media_url": media_url,
                        "normalized_url": normalized_media_url(media_url),
                        "source_root": source_root,
                        "parent_index_url": index_url,
                        "relative_path": path[len(root_path) :],
                        "filename": Path(path).name,
                        "media_kind": "audio" if extension in _AUDIO_EXTENSIONS else "video",
                        "extension": extension.lstrip("."),
                        "listed_last_modified": entry.get("listed_last_modified"),
                        "listed_size": entry.get("listed_size"),
                    }
                    if dry_run:
                        persisted = {**asset, "ffprobe_metadata": {}, "probed_at": None}
                        is_new = True
                    else:
                        persisted, is_new = self.db.upsert_legacy_media_asset(
                            asset, run_id=run_id
                        )
                    inserted += int(is_new)
                    updated += int(not is_new)
                    assets[str(asset["media_id"])] = persisted
            if not complete:
                break
        return list(assets.values()), directories_seen, complete, inserted, updated

    def _inventory_lookups(self, start: date, end: date) -> dict[str, Any]:
        connection = self.db.connect()
        sermon_rows = [dict(row) for row in connection.execute("SELECT * FROM sermons")]
        source_rows = [dict(row) for row in connection.execute("SELECT * FROM sermon_sources")]
        url_map: dict[str, set[str]] = defaultdict(set)
        basename_map: dict[str, set[str]] = defaultdict(set)
        identifier_map: dict[tuple[str, int], set[str]] = defaultdict(set)
        evidence_by_url: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        sermon_by_id = {str(row["sermon_id"]): row for row in sermon_rows}
        target_identifier_numbers: dict[str, set[int]] = defaultdict(set)

        def remember_target_identifier(sermon_id: str, identifier: tuple[str, int] | None) -> None:
            if identifier is None:
                return
            sermon_date = parse_sermon_date(sermon_by_id[sermon_id].get("sermon_date"))
            if sermon_date is not None and start <= sermon_date <= end:
                target_identifier_numbers[identifier[0]].add(identifier[1])

        for row in sermon_rows:
            sermon_id = str(row["sermon_id"])
            for field in (
                "canonical_url",
                "source_url",
                "media_url",
                "audio_url",
                "audio_source_url",
                "video_url",
                "video_source_url",
            ):
                url = row.get(field)
                if not isinstance(url, str) or not url:
                    continue
                key = normalized_media_url(url)
                url_map[key].add(sermon_id)
                basename = Path(unquote(urlparse(url).path)).name.casefold()
                if basename:
                    basename_map[basename].add(sermon_id)
                identifier = (
                    legacy_identifier(url)
                    if Path(unquote(urlparse(url).path)).suffix.casefold()
                    in _MEDIA_EXTENSIONS
                    else None
                )
                if identifier:
                    identifier_map[identifier].add(sermon_id)
                remember_target_identifier(sermon_id, identifier)
                evidence_by_url[(key, sermon_id)].append(
                    {"table": "sermons", "field": field, "url": url}
                )
        for row in source_rows:
            sermon_id = str(row["sermon_id"])
            for field in ("audio_url", "video_url"):
                url = row.get(field)
                if not isinstance(url, str) or not url:
                    continue
                key = normalized_media_url(url)
                url_map[key].add(sermon_id)
                basename = Path(unquote(urlparse(url).path)).name.casefold()
                if basename:
                    basename_map[basename].add(sermon_id)
                identifier = (
                    legacy_identifier(url)
                    if Path(unquote(urlparse(url).path)).suffix.casefold()
                    in _MEDIA_EXTENSIONS
                    else None
                )
                if identifier:
                    identifier_map[identifier].add(sermon_id)
                remember_target_identifier(sermon_id, identifier)
                evidence_by_url[(key, sermon_id)].append(
                    {
                        "table": "sermon_sources",
                        "source_id": row.get("source_id"),
                        "field": field,
                        "url": url,
                    }
                )
        ranges = {
            prefix: (min(numbers), max(numbers))
            for prefix, numbers in target_identifier_numbers.items()
            if numbers
        }
        return {
            "sermon_by_id": sermon_by_id,
            "url_map": url_map,
            "basename_map": basename_map,
            "identifier_map": identifier_map,
            "evidence_by_url": evidence_by_url,
            "ranges": ranges,
        }

    @staticmethod
    def _initial_match(asset: Mapping[str, Any], lookups: Mapping[str, Any]) -> dict[str, Any]:
        normalized_url = str(asset["normalized_url"])
        basename = str(asset["filename"]).casefold()
        identifier = legacy_identifier(str(asset["filename"]))
        if lookups["url_map"].get(normalized_url):
            sermon_ids = set(lookups["url_map"][normalized_url])
            rule = "exact_normalized_url"
        elif lookups["basename_map"].get(basename):
            sermon_ids = set(lookups["basename_map"][basename])
            rule = "exact_unique_basename"
        elif identifier and lookups["identifier_map"].get(identifier):
            sermon_ids = set(lookups["identifier_map"][identifier])
            rule = "exact_unique_legacy_identifier"
        else:
            sermon_ids = set()
            rule = "none"

        if len(sermon_ids) == 1:
            return {
                "classification": "matched_inventory",
                "match_rule": rule,
                "confidence": "high" if rule == "exact_normalized_url" else "medium",
                "sermon_ids": sorted(sermon_ids),
            }
        if len(sermon_ids) > 1:
            return {
                "classification": "ambiguous_inventory_match",
                "match_rule": rule,
                "confidence": "low",
                "sermon_ids": sorted(sermon_ids),
            }

        candidate_reasons: list[str] = []
        if identifier:
            bounds = lookups["ranges"].get(identifier[0])
            if bounds and bounds[0] <= identifier[1] <= bounds[1]:
                candidate_reasons.append(
                    f"legacy identifier {identifier[0]}{identifier[1]} is inside target inventory bounds"
                )
        if _target_path_hint(asset):
            candidate_reasons.append("path is a guest/event/special/old target-era review directory")
        years = {int(value) for value in _YEAR_RE.findall(str(asset["relative_path"]))}
        if any(2004 <= year <= 2010 for year in years):
            candidate_reasons.append("path contains a target-period year")
        return {
            "classification": "candidate_unprobed" if candidate_reasons else "unmatched_unprobed",
            "match_rule": "candidate_path_or_identifier" if candidate_reasons else "none",
            "confidence": "low",
            "sermon_ids": [],
            "candidate_reasons": candidate_reasons,
        }

    @staticmethod
    def _duration(probe: Mapping[str, Any]) -> int | None:
        try:
            return max(0, int(float(probe["duration"])))
        except (KeyError, TypeError, ValueError):
            return None

    def _load_existing_run_assets(
        self, run_id: int
    ) -> tuple[list[dict[str, Any]], int, bool]:
        connection = self.db.connect()
        crawl = connection.execute(
            "SELECT * FROM crawl_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if crawl is None:
            raise ValueError(f"unknown media-index run: {run_id}")
        metadata = json.loads(str(crawl["metadata"] or "{}"))
        if not isinstance(metadata, Mapping) or metadata.get("source") != "legacy_media_index":
            raise ValueError(f"crawl run {run_id} is not a legacy media-index run")
        rows = connection.execute(
            """
            SELECT a.*
            FROM legacy_media_observations o
            JOIN legacy_media_assets a USING(media_id)
            WHERE o.run_id = ?
            ORDER BY a.media_url
            """,
            (run_id,),
        ).fetchall()
        assets: list[dict[str, Any]] = []
        for row in rows:
            asset = dict(row)
            raw_probe = asset.get("ffprobe_metadata")
            try:
                parsed_probe = json.loads(str(raw_probe or "{}"))
            except json.JSONDecodeError:
                parsed_probe = {}
            asset["ffprobe_metadata"] = (
                dict(parsed_probe) if isinstance(parsed_probe, Mapping) else {}
            )
            assets.append(asset)
        return assets, int(crawl["pages_seen"] or 0), str(crawl["status"]) == "completed"

    def run(
        self,
        *,
        start_date: str | date = "2004-06-01",
        end_date: str | date = "2010-08-31",
        max_directories: int | None = None,
        max_probes: int = 200,
        no_ffprobe: bool = False,
        dry_run: bool = False,
        reuse_run_id: int | None = None,
    ) -> dict[str, Any]:
        start = parse_sermon_date(start_date)
        end = parse_sermon_date(end_date)
        if start is None or end is None:
            raise ValueError("start_date and end_date must be valid dates")
        if start > end:
            raise ValueError("start_date must not be after end_date")
        if max_directories is not None and max_directories < 1:
            raise ValueError("max_directories must be positive")
        if max_probes < 0:
            raise ValueError("max_probes must not be negative")
        if reuse_run_id is not None and max_directories is not None:
            raise ValueError("max_directories cannot be used with reuse_run_id")

        new_run = reuse_run_id is None
        run_id = (
            self.db.start_crawl(
                source_url=self.media_roots[0],
                metadata={
                    "source": "legacy_media_index",
                    "media_roots": list(self.media_roots),
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "max_directories": max_directories,
                    "max_probes": max_probes,
                    "no_ffprobe": no_ffprobe,
                    "dry_run": dry_run,
                },
            )
            if new_run
            else int(reuse_run_id)
        )
        self.raw_store = RawResponseStore(self.root, f"media-index-{run_id}")
        stats: dict[str, Any] = {
            "run_id": run_id,
            "reused_run": None if new_run else run_id,
            "dry_run": dry_run,
            "directories_seen": 0,
            "assets_seen": 0,
            "assets_added": 0,
            "assets_updated": 0,
            "matched_inventory": 0,
            "ambiguous_inventory_match": 0,
            "candidate_unprobed": 0,
            "target_candidates": 0,
            "needs_date_review": 0,
            "unmatched_unprobed": 0,
            "probes_attempted": 0,
            "probes_reused": 0,
            "probes_succeeded": 0,
            "probes_failed": 0,
            "canonical_media_recovered": 0,
        }
        try:
            if new_run:
                assets, directories_seen, complete, inserted, updated = self._enumerate(
                    run_id=run_id,
                    max_directories=max_directories,
                    dry_run=dry_run,
                )
            else:
                assets, directories_seen, complete = self._load_existing_run_assets(run_id)
                inserted = 0
                updated = 0
            stats.update(
                {
                    "directories_seen": directories_seen,
                    "assets_seen": len(assets),
                    "assets_added": inserted,
                    "assets_updated": updated,
                    "tree_complete": complete,
                }
            )
            lookups = self._inventory_lookups(start, end)
            states = {
                str(asset["media_id"]): self._initial_match(asset, lookups) for asset in assets
            }

            probe_queue: list[tuple[int, dict[str, Any]]] = []
            for asset in assets:
                media_id = str(asset["media_id"])
                state = states[media_id]
                priority = 0
                if state["classification"] == "matched_inventory" and len(state["sermon_ids"]) == 1:
                    sermon = lookups["sermon_by_id"][state["sermon_ids"][0]]
                    if not bool(sermon.get(f"has_{asset['media_kind']}")):
                        priority = 100
                elif state["classification"] == "candidate_unprobed":
                    identifier = legacy_identifier(str(asset["filename"]))
                    priority = 90 if identifier else 80
                if priority:
                    probe_queue.append((priority, asset))
            probe_queue.sort(
                key=lambda item: (-item[0], str(item[1]["relative_path"]).casefold())
            )
            network_probes = 0
            for _, asset in probe_queue:
                media_id = str(asset["media_id"])
                state = states[media_id]
                cached_probe = asset.get("ffprobe_metadata")
                if (
                    asset.get("probed_at")
                    and isinstance(cached_probe, Mapping)
                    and cached_probe
                    and not asset.get("probe_error")
                ):
                    probe = dict(cached_probe)
                    stats["probes_reused"] += 1
                else:
                    if no_ffprobe or network_probes >= max_probes:
                        continue
                    probe = self._ffprobe(str(asset["media_url"]))
                    network_probes += 1
                    stats["probes_attempted"] += 1
                    error = str(probe.get("error")) if probe.get("error") else None
                    if error:
                        stats["probes_failed"] += 1
                    else:
                        stats["probes_succeeded"] += 1
                    if not dry_run:
                        self.db.set_legacy_media_probe(media_id, metadata=probe, error=error)
                error = str(probe.get("error")) if probe.get("error") else None
                evidence = probe_date_evidence(probe)
                state["probe"] = probe
                state["probe_date_evidence"] = evidence
                if state["classification"] == "matched_inventory":
                    if not error and len(state["sermon_ids"]) == 1:
                        sermon_id = state["sermon_ids"][0]
                        sermon = lookups["sermon_by_id"][sermon_id]
                        if not bool(sermon.get(f"has_{asset['media_kind']}")):
                            if not dry_run:
                                self.db.attach_public_media(
                                    sermon_id,
                                    media_kind=str(asset["media_kind"]),
                                    media_url=str(asset["media_url"]),
                                    media_format=str(asset["extension"]),
                                    duration_seconds=self._duration(probe),
                                    evidence={
                                        "media_id": media_id,
                                        "listing_url": asset["parent_index_url"],
                                        "media_url": asset["media_url"],
                                        "match_rule": state["match_rule"],
                                        "ffprobe": probe,
                                    },
                                )
                                source_id = f"media-index:{media_id}"
                                source_kwargs = {
                                    "audio_url": asset["media_url"]
                                    if asset["media_kind"] == "audio"
                                    else None,
                                    "audio_available": True
                                    if asset["media_kind"] == "audio"
                                    else None,
                                    "video_url": asset["media_url"]
                                    if asset["media_kind"] == "video"
                                    else None,
                                    "video_available": True
                                    if asset["media_kind"] == "video"
                                    else None,
                                }
                                self.db.upsert_source_evidence(
                                    source_id=source_id,
                                    sermon_id=sermon_id,
                                    source_platform="calvary_legacy_media_index",
                                    platform_item_id=Path(str(asset["filename"])).stem,
                                    source_url=str(asset["media_url"]),
                                    listing_url=str(asset["parent_index_url"]),
                                    checked_at=datetime.now(timezone.utc).isoformat(),
                                    notes="Recovered from a currently public legacy directory index.",
                                    raw_metadata={"asset": asset, "ffprobe": probe},
                                    **source_kwargs,
                                )
                            stats["canonical_media_recovered"] += 1
                elif not error:
                    explicit_dates = [
                        value
                        for value in evidence["full_dates"]
                        if start <= date.fromisoformat(value) <= end
                    ]
                    target_years = [
                        year for year in evidence["years"] if start.year <= year <= end.year
                    ]
                    if explicit_dates:
                        state["classification"] = "target_candidate"
                        state["match_rule"] = "explicit_probe_date"
                        state["confidence"] = "medium"
                    elif evidence["full_dates"]:
                        state["classification"] = "out_of_scope"
                        state["match_rule"] = "explicit_probe_date_outside_window"
                        state["confidence"] = "high"
                    elif target_years or state.get("candidate_reasons"):
                        state["classification"] = "needs_date_review"
                        state["match_rule"] = "probe_tags_or_target_path_without_full_date"
                        state["confidence"] = "low"

            for asset in assets:
                media_id = str(asset["media_id"])
                state = states[media_id]
                classification = str(state["classification"])
                stats[classification] = stats.get(classification, 0) + 1
                match_rows: list[dict[str, Any]] = []
                sermon_ids = state.get("sermon_ids") or [None]
                for sermon_id in sermon_ids:
                    evidence: dict[str, Any] = {
                        "media_url": asset["media_url"],
                        "relative_path": asset["relative_path"],
                        "candidate_reasons": state.get("candidate_reasons", []),
                        "probe_date_evidence": state.get("probe_date_evidence"),
                    }
                    if sermon_id:
                        evidence["sermon"] = {
                            key: lookups["sermon_by_id"][sermon_id].get(key)
                            for key in ("sermon_date", "title", "speaker", "series")
                        }
                        evidence["url_evidence"] = lookups["evidence_by_url"].get(
                            (str(asset["normalized_url"]), sermon_id), []
                        )
                    match_rows.append(
                        {
                            "match_id": _match_id(
                                run_id, media_id, sermon_id, classification
                            ),
                            "sermon_id": sermon_id,
                            "classification": classification,
                            "match_rule": state["match_rule"],
                            "confidence": state["confidence"],
                            "evidence": evidence,
                        }
                    )
                if not dry_run:
                    self.db.replace_legacy_media_matches(
                        run_id=run_id, media_id=media_id, matches=match_rows
                    )

            raw_assets = sorted(assets, key=lambda asset: str(asset["media_url"]))
            (self.raw_store.directory / "legacy-media-assets.json").write_text(
                json.dumps(raw_assets, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            (self.raw_store.directory / "legacy-media-audit-summary.json").write_text(
                json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            finish_status = "completed" if complete else "partial"
            self.db.finish_crawl(
                run_id,
                status=finish_status,
                pages_seen=directories_seen,
                items_seen=len(assets),
                items_added=inserted if new_run else None,
                items_updated=updated if new_run else None,
                api_records=stats["matched_inventory"],
                target_records=stats.get("target_candidate", 0),
                missing_date_records=stats.get("needs_date_review", 0),
            )
            return stats
        except Exception as exc:
            if new_run:
                self.db.finish_crawl(
                    run_id, status="failed", error=f"{type(exc).__name__}: {exc}"
                )
            raise


def _write_candidate_reconciliation_report(
    root: Path,
    *,
    db: Any,
    start: date,
    end: date,
    candidates: Sequence[Mapping[str, Any]],
    corrections: Sequence[Mapping[str, Any]],
) -> None:
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    csv_path = reports_dir / "missing-sermons.csv"
    markdown_path = reports_dir / "missing-sermons.md"
    fields = (
        "tier",
        "sermon_id",
        "sermon_date",
        "title",
        "speaker",
        "series",
        "service_type",
        "duration_seconds",
        "media_filename",
        "media_url",
        "full_date_evidence",
        "year_evidence",
        "notes",
    )
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        record = candidate["record"]
        evidence = candidate["date_evidence"]
        rows.append(
            {
                "tier": candidate["tier"],
                "sermon_id": record["sermon_id"],
                "sermon_date": record.get("sermon_date"),
                "title": record.get("title"),
                "speaker": record.get("speaker"),
                "series": record.get("series"),
                "service_type": record.get("service_type"),
                "duration_seconds": record.get("duration_seconds"),
                "media_filename": record.get("original_media_filename"),
                "media_url": record.get("audio_url"),
                "full_date_evidence": "; ".join(evidence.get("full_dates") or []),
                "year_evidence": "; ".join(str(value) for value in evidence.get("years") or []),
                "notes": record.get("notes"),
            }
        )
    rows.sort(key=lambda row: (str(row["tier"]), str(row["sermon_date"] or ""), str(row["media_filename"])))
    csv_tmp = csv_path.with_suffix(".csv.tmp")
    with csv_tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})
    csv_tmp.replace(csv_path)

    by_tier: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_tier[str(row["tier"])].append(row)
    connection = db.connect()
    historical_corrections = [dict(value) for value in corrections]
    known_correction_ids = {str(value.get("sermon_id") or "") for value in historical_corrections}
    for correction_row in connection.execute(
        "SELECT sermon_id, sermon_date, title, raw_metadata FROM sermons"
    ):
        if str(correction_row["sermon_id"]) in known_correction_ids:
            continue
        try:
            raw_metadata = json.loads(str(correction_row["raw_metadata"] or "{}"))
        except json.JSONDecodeError:
            continue
        recoveries = raw_metadata.get("legacy_media_recoveries")
        if not isinstance(recoveries, list):
            continue
        for recovery in recoveries:
            if not isinstance(recovery, Mapping) or recovery.get("reason") != "canonical_filename_conflict":
                continue
            historical_corrections.append(
                {
                    "sermon_id": correction_row["sermon_id"],
                    "sermon_date": correction_row["sermon_date"],
                    "title": correction_row["title"],
                    "previous_filename": recovery.get("previous_filename"),
                    "filename": recovery.get("filename"),
                }
            )
            break
    dated_count = connection.execute(
        "SELECT COUNT(*) FROM sermons WHERE sermon_date BETWEEN ? AND ?",
        (start.isoformat(), end.isoformat()),
    ).fetchone()[0]
    older_john_count = connection.execute(
        """SELECT COUNT(*) FROM sermons
           WHERE sermon_date IS NULL AND series = 'The Gospel of John'
             AND original_media_filename LIKE 'KT%'"""
    ).fetchone()[0]
    lines = [
        "# Calvary Spokane Missing-Sermon Reconciliation",
        "",
        f"Inclusive target window: **{start.isoformat()} through {end.isoformat()}**.",
        "",
        "This report distinguishes confirmed omissions from records that merely need date review. "
        "A Sunday/Thursday calendar hole by itself is not evidence that a sermon existed.",
        "",
        "## Reconciled result",
        "",
        f"- Canonical dated records in range after reconciliation: **{dated_count}**",
        f"- Exact-dated public guest recordings recovered: **{len(by_tier['confirmed_exact_date'])}**",
        f"- Public recordings retained for exact-date review: **{sum(len(value) for key, value in by_tier.items() if key != 'confirmed_exact_date')}**",
        f"- Canonical media assignments corrected: **{len(historical_corrections)}**",
        "- No target-period public video was found; these recovered records are audio-only.",
        "",
        "## Confirmed omissions recovered into the dated inventory",
        "",
        "| Date | File | Speaker | Embedded source title | Duration |",
        "|---|---|---|---|---:|",
    ]
    for row in by_tier["confirmed_exact_date"]:
        lines.append(
            f"| {row['sermon_date']} | `{row['media_filename']}` | {row['speaker'] or '(unknown)'} "
            f"| {str(row['title']).replace('|', '\\|')} | {row['duration_seconds']}s |"
        )
    lines.extend(
        [
            "",
            "## Public target-window candidates still lacking a safe exact date",
            "",
            "These records are now preserved in the canonical inventory with `needs_review`; no date was invented.",
            "",
        ]
    )
    tier_labels = {
        "confirmed_target_year": "Year confirmed, exact date absent",
        "identifier_bounded_review": "Target-era guest-ID sequence, exact date absent",
        "conflicting_exact_date": "Conflicting exact-date evidence",
    }
    for tier in ("confirmed_target_year", "identifier_bounded_review", "conflicting_exact_date"):
        tier_rows = by_tier[tier]
        if not tier_rows:
            continue
        lines.extend(
            [
                f"### {tier_labels[tier]} ({len(tier_rows)})",
                "",
                "| File | Speaker | Source title | Date/year evidence | Duration |",
                "|---|---|---|---|---:|",
            ]
        )
        for row in tier_rows:
            evidence = row["full_date_evidence"] or row["year_evidence"] or "identifier/path only"
            lines.append(
                f"| `{row['media_filename']}` | {row['speaker'] or '(unknown)'} "
                f"| {str(row['title']).replace('|', '\\|')} | {evidence} | {row['duration_seconds']}s |"
            )
        lines.append("")
        if tier == "conflicting_exact_date":
            lines.extend(
                [
                    "`GS1123.mp3` is sequence-adjacent to early-2010 guest files and `2010-01-10` is a Sunday calendar gap, so its embedded `2009-01-10` may contain a one-digit year typo. That is strong circumstantial evidence, not independent confirmation; the canonical date remains blank.",
                    "",
                ]
            )
    lines.extend(
        [
            "## Canonical media correction",
            "",
        ]
    )
    if historical_corrections:
        lines.extend(
            [
                "| Date | Sermon | Previous file | Correct public file |",
                "|---|---|---|---|",
            ]
        )
        for correction in historical_corrections:
            lines.append(
                f"| {correction['sermon_date']} | {str(correction['title']).replace('|', '\\|')} "
                f"| `{correction['previous_filename']}` | `{correction['filename']}` |"
            )
    else:
        lines.append("No canonical media correction was required in this run.")
    lines.extend(
        [
            "",
            "## Undated Subsplash records",
            "",
            f"- **{older_john_count}** undated `The Gospel of John` items use `KT1167`–`KT1261`. "
            "The target window begins around `KT1616`, so this is an older sequence, not an uncounted "
            "2004–2010 series.",
            "- The undated `K646` Proverbs item is likewise far earlier in the numeric sequence than the "
            "June 2004 starting point (`K771`).",
            "- The remaining undated Subsplash video is explicitly a 2025 family conference.",
            "",
            "## Remaining calendar gaps",
            "",
            "After the confirmed dated imports, remaining Sunday/Thursday holes are schedule hypotheses only. "
            "They may represent holidays, cancellations, combined services, unrecorded services, or unpublished "
            "guest messages. See `calendar-gaps.csv`; do not treat that file as a list of confirmed missing sermons.",
            "",
            "Full normalized evidence is in `missing-sermons.csv`, `legacy-media-candidates.csv`, and SQLite.",
            "",
        ]
    )
    markdown_tmp = markdown_path.with_suffix(".md.tmp")
    markdown_tmp.write_text("\n".join(lines), encoding="utf-8")
    markdown_tmp.replace(markdown_path)


def reconcile_media_index_candidates(
    root: str | Path,
    db: Any,
    *,
    start_date: str | date = "2004-06-01",
    end_date: str | date = "2010-08-31",
    run_id: int | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Promote strongly evidenced guest assets and retain ambiguous ones for review."""

    start = parse_sermon_date(start_date)
    end = parse_sermon_date(end_date)
    if start is None or end is None:
        raise ValueError("start_date and end_date must be valid dates")
    if start > end:
        raise ValueError("start_date must not be after end_date")
    connection = db.connect()
    selected_run = run_id
    if selected_run is None:
        row = connection.execute(
            "SELECT MAX(run_id) FROM legacy_media_observations"
        ).fetchone()
        selected_run = int(row[0]) if row and row[0] is not None else None
    if selected_run is None:
        raise ValueError("no legacy media-index run is available")
    assets = []
    for row in connection.execute(
        """SELECT a.* FROM legacy_media_observations o
           JOIN legacy_media_assets a USING(media_id)
           WHERE o.run_id = ? ORDER BY a.media_url""",
        (selected_run,),
    ):
        asset = dict(row)
        try:
            decoded = json.loads(str(asset.get("ffprobe_metadata") or "{}"))
        except json.JSONDecodeError:
            decoded = {}
        asset["ffprobe_metadata"] = decoded if isinstance(decoded, Mapping) else {}
        assets.append(asset)

    candidates = [
        candidate
        for asset in assets
        if (candidate := normalize_guest_media_candidate(asset, start_date=start, end_date=end))
        is not None
    ]
    stats: dict[str, Any] = {
        "run_id": selected_run,
        "dry_run": dry_run,
        "candidates_reconciled": len(candidates),
        "confirmed_exact_date": 0,
        "confirmed_target_year": 0,
        "identifier_bounded_review": 0,
        "conflicting_exact_date": 0,
        "records_added": 0,
        "records_updated": 0,
        "canonical_media_corrected": 0,
    }
    for candidate in candidates:
        tier = str(candidate["tier"])
        stats[tier] += 1
        record = candidate["record"]
        duplicate = db.find_duplicate(record)
        stats["records_added" if duplicate is None else "records_updated"] += 1
        if dry_run:
            continue
        canonical = db.upsert_sermon(record)
        asset = candidate["asset"]
        db.upsert_source_evidence(
            source_id=f"media-index-candidate:{asset['media_id']}",
            sermon_id=canonical.sermon_id,
            source_platform="calvary_legacy_media_index",
            platform_item_id=Path(str(asset["filename"])).stem,
            source_url=str(asset["media_url"]),
            listing_url=str(asset["parent_index_url"]),
            audio_url=str(asset["media_url"]),
            audio_available=True,
            checked_at=asset.get("probed_at"),
            notes="Public legacy guest/session media candidate reconciled from embedded metadata.",
            raw_metadata={
                "asset": asset,
                "date_evidence": candidate["date_evidence"],
                "reconciliation_tier": tier,
            },
        )
        db.replace_legacy_media_matches(
            run_id=selected_run,
            media_id=str(asset["media_id"]),
            matches=[
                {
                    "match_id": _match_id(
                        selected_run, str(asset["media_id"]), canonical.sermon_id, "matched_inventory"
                    ),
                    "sermon_id": canonical.sermon_id,
                    "classification": "matched_inventory",
                    "match_rule": f"reconciled_{tier}",
                    "confidence": "high" if tier == "confirmed_exact_date" else "medium",
                    "evidence": {
                        "media_url": asset["media_url"],
                        "date_evidence": candidate["date_evidence"],
                        "reconciliation_tier": tier,
                    },
                }
            ],
        )

    corrections: list[dict[str, Any]] = []
    correction_rows = connection.execute(
        """SELECT a.*, s.sermon_id, s.sermon_date, s.title,
                  s.original_media_filename AS canonical_filename,
                  s.audio_url AS canonical_audio_url
           FROM legacy_media_matches m
           JOIN legacy_media_assets a ON a.media_id = m.media_id
           JOIN sermons s ON s.sermon_id = m.sermon_id
           WHERE m.run_id = ?
             AND m.classification = 'matched_inventory'
             AND m.match_rule = 'exact_normalized_url'
             AND a.media_kind = 'audio'
             AND s.original_media_filename IS NOT NULL
             AND lower(a.filename) <> lower(s.original_media_filename)""",
        (selected_run,),
    ).fetchall()
    for raw_row in correction_rows:
        row = dict(raw_row)
        asset_identifier = legacy_identifier(str(row["filename"]))
        canonical_identifier = legacy_identifier(str(row["canonical_filename"]))
        if not asset_identifier or not canonical_identifier or asset_identifier == canonical_identifier:
            continue
        correction = {
            "sermon_id": row["sermon_id"],
            "sermon_date": row["sermon_date"],
            "title": row["title"],
            "previous_filename": row["canonical_filename"],
            "previous_audio_url": row["canonical_audio_url"],
            "filename": row["filename"],
            "media_url": row["media_url"],
        }
        corrections.append(correction)
        if not dry_run:
            db.attach_public_media(
                str(row["sermon_id"]),
                media_kind="audio",
                media_url=str(row["media_url"]),
                media_format=str(row["extension"]),
                duration_seconds=_duration_seconds(
                    json.loads(str(row.get("ffprobe_metadata") or "{}"))
                ),
                evidence={"reason": "canonical_filename_conflict", **correction},
                replace_existing=True,
            )
    stats["canonical_media_corrected"] = len(corrections)
    if not dry_run:
        _write_candidate_reconciliation_report(
            Path(root), db=db, start=start, end=end, candidates=candidates, corrections=corrections
        )
    stats["report"] = str(Path(root) / "reports" / "missing-sermons.md")
    return stats


def audit_media_indexes(
    root: str | Path,
    db: Any,
    *,
    start_date: str | date = "2004-06-01",
    end_date: str | date = "2010-08-31",
    **kwargs: Any,
) -> dict[str, Any]:
    """One-shot wrapper around :class:`LegacyMediaIndexAudit`."""

    run_keys = {
        "max_directories",
        "max_probes",
        "no_ffprobe",
        "dry_run",
        "reuse_run_id",
    }
    run_options = {key: kwargs.pop(key) for key in tuple(kwargs) if key in run_keys}
    with LegacyMediaIndexAudit(root, db, **kwargs) as audit:
        return audit.run(start_date=start_date, end_date=end_date, **run_options)
