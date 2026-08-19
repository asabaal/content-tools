"""Live discovery and normalization for the Calvary Spokane archive.

The Subsplash media-items feed is the authoritative inventory.  Builder lists are
also crawled because they preserve what a visitor can navigate to, but they are
not used to decide which media items exist.
"""

from __future__ import annotations

import copy
import hashlib
import html as html_module
import inspect
import json
import random
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence
from urllib.parse import unquote, urlparse

import httpx

try:  # The project skeleton may be populated in stages.
    from .models import SermonRecord
except ImportError:  # pragma: no cover - exercised until the sibling arrives.
    SermonRecord = None  # type: ignore[assignment,misc]


START_URLS = (
    "https://www.calvaryspokane.com/sermon-archive",
    "https://www.calvaryspokane.com/sermons",
    "https://www.calvaryspokane.com/old-testament",
    "https://www.calvaryspokane.com/new-testament",
)
CORE_URL = "https://core.subsplash.com"
MEDIA_ITEMS_URL = f"{CORE_URL}/media/v1/media-items"
MEDIA_SERIES_URL = f"{CORE_URL}/media/v1/media-series"
APPS_URL = f"{CORE_URL}/accounts/v1/apps"
BUILDER_LISTS_URL = f"{CORE_URL}/builder/v1/lists"
BUILDER_ROWS_URL = f"{CORE_URL}/builder/v1/list-rows"
MEDIA_INCLUDES = (
    "images,audio.audio-outputs,audio.video,video.video-outputs,"
    "video.playlists,document,broadcast"
)
USER_AGENT = (
    "CalvarySpokaneArchiver/1.0 "
    "(public archival discovery; https://www.calvaryspokane.com/sermon-archive)"
)

_TOKEN_RE = re.compile(r'("apiToken"\s*:\s*)"(?:\\.|[^"\\])*"', re.IGNORECASE)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9_.-]+")


class _ShoeboxParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_tokens = False
        self._parts: list[str] = []
        self.payloads: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag.lower() == "script" and attributes.get("id") == "shoebox-tokens":
            self._in_tokens = True
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._in_tokens:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_tokens:
            self.payloads.append("".join(self._parts))
            self._in_tokens = False
            self._parts = []


def parse_shoebox_token(page_html: str) -> str:
    """Extract the public API bearer token from a Subsplash shoebox script."""

    parser = _ShoeboxParser()
    parser.feed(page_html)
    for payload in parser.payloads:
        try:
            value = json.loads(html_module.unescape(payload)).get("apiToken")
        except (json.JSONDecodeError, AttributeError):
            continue
        if isinstance(value, str) and value:
            return value

    # A fallback is useful for mildly malformed/minified HTML that HTMLParser
    # cannot balance. json.loads correctly unescapes the captured JSON string.
    match = re.search(r'"apiToken"\s*:\s*("(?:\\.|[^"\\])*")', page_html)
    if match:
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError:
            value = None
        if isinstance(value, str) and value:
            return value
    raise ValueError("Subsplash page did not contain a usable shoebox apiToken")


def redact_shoebox_token(page_html: str) -> str:
    """Return HTML safe to persist while leaving the shoebox structure intact."""

    return _TOKEN_RE.sub(lambda match: f'{match.group(1)}"[REDACTED]"', page_html)


def extract_subsplash_identifiers(page_html: str) -> tuple[set[str], set[str]]:
    """Find app and Builder-list shortcodes in links, iframes, and scripts."""

    searchable = html_module.unescape(page_html).replace("\\/", "/")
    apps: set[str] = set()
    lists: set[str] = set()

    for match in re.finditer(
        r"\+([A-Za-z0-9]{3,})/lb/li/\+([A-Za-z0-9]{3,})",
        searchable,
        re.IGNORECASE,
    ):
        apps.add(match.group(1))
        lists.add(match.group(2))

    # Recent-media iframes identify an app but do not point to a Builder list.
    for match in re.finditer(
        r"\+([A-Za-z0-9]{3,})/(?:embed(?:/|\b)|lb(?:/|\b))",
        searchable,
        re.IGNORECASE,
    ):
        apps.add(match.group(1))

    return apps, lists


# Canonical Protestant Bible-book names. Abbreviations are accepted only when
# they occur in an explicit scripture value; arbitrary sermon titles are never
# mined for a book name.
_BIBLE_BOOKS = (
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua",
    "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
    "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
    "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah",
    "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel",
    "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah",
    "Haggai", "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John",
    "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians",
    "Ephesians", "Philippians", "Colossians", "1 Thessalonians",
    "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon",
    "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
    "Jude", "Revelation",
)
_SCRIPTURE_ALIASES: dict[str, str] = {
    "gen": "Genesis", "ge": "Genesis", "exod": "Exodus", "ex": "Exodus",
    "lev": "Leviticus", "lv": "Leviticus", "num": "Numbers", "nu": "Numbers",
    "deut": "Deuteronomy", "dt": "Deuteronomy", "josh": "Joshua",
    "judg": "Judges", "jdg": "Judges", "1 sam": "1 Samuel", "1sam": "1 Samuel",
    "2 sam": "2 Samuel", "2sam": "2 Samuel", "1 kgs": "1 Kings",
    "1kgs": "1 Kings", "2 kgs": "2 Kings", "2kgs": "2 Kings",
    "1 chr": "1 Chronicles", "1chr": "1 Chronicles", "2 chr": "2 Chronicles",
    "2chr": "2 Chronicles", "neh": "Nehemiah", "esth": "Esther",
    "ps": "Psalms", "psa": "Psalms", "prov": "Proverbs", "pr": "Proverbs",
    "eccl": "Ecclesiastes", "ecc": "Ecclesiastes", "song": "Song of Solomon",
    "song of songs": "Song of Solomon", "sos": "Song of Solomon", "isa": "Isaiah",
    "jer": "Jeremiah", "lam": "Lamentations", "ezek": "Ezekiel", "ezk": "Ezekiel",
    "dan": "Daniel", "dn": "Daniel", "hos": "Hosea", "obad": "Obadiah",
    "mic": "Micah", "nah": "Nahum", "hab": "Habakkuk", "zeph": "Zephaniah",
    "hag": "Haggai", "zech": "Zechariah", "zec": "Zechariah", "mal": "Malachi",
    "matt": "Matthew", "mt": "Matthew", "mk": "Mark", "lk": "Luke",
    "jn": "John", "rom": "Romans", "ro": "Romans", "1 cor": "1 Corinthians",
    "1cor": "1 Corinthians", "2 cor": "2 Corinthians", "2cor": "2 Corinthians",
    "gal": "Galatians", "eph": "Ephesians", "phil": "Philippians",
    "col": "Colossians", "1 thess": "1 Thessalonians", "1thess": "1 Thessalonians",
    "2 thess": "2 Thessalonians", "2thess": "2 Thessalonians",
    "1 tim": "1 Timothy", "1tim": "1 Timothy", "2 tim": "2 Timothy",
    "2tim": "2 Timothy", "phlm": "Philemon", "heb": "Hebrews", "jas": "James",
    "1 pet": "1 Peter", "1pet": "1 Peter", "2 pet": "2 Peter",
    "2pet": "2 Peter", "1 jn": "1 John", "1jn": "1 John", "2 jn": "2 John",
    "2jn": "2 John", "3 jn": "3 John", "3jn": "3 John", "rev": "Revelation",
}
for _book in _BIBLE_BOOKS:
    _SCRIPTURE_ALIASES[_book.lower()] = _book


def extract_bible_book(
    series_title: str | None,
    scriptures: Sequence[str] | None,
) -> str | None:
    """Extract a book only from an explicit series/book or scripture value."""

    if isinstance(series_title, str):
        normalized = re.sub(r"\s+", " ", series_title.strip())
        normalized = re.sub(r"^the book of\s+", "", normalized, flags=re.IGNORECASE)
        for book in sorted(_BIBLE_BOOKS, key=len, reverse=True):
            if re.match(
                rf"^{re.escape(book)}(?:$|\s*(?:[|:–—-]|\())",
                normalized,
                re.IGNORECASE,
            ):
                return book

    for scripture in scriptures or ():
        if not isinstance(scripture, str):
            continue
        normalized = re.sub(r"\s+", " ", scripture.strip().lower())
        for alias in sorted(_SCRIPTURE_ALIASES, key=len, reverse=True):
            if re.match(rf"^{re.escape(alias)}(?=$|[\s.:\d])", normalized):
                return _SCRIPTURE_ALIASES[alias]
    return None


def _date_text(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and len(value) >= 10:
        candidate = value[:10]
        if _DATE_RE.match(candidate):
            try:
                return date.fromisoformat(candidate).isoformat()
            except ValueError:
                return None
    return None


def date_in_range(
    value: Mapping[str, Any] | str | date | datetime | None,
    start_date: str | date | datetime | None = None,
    end_date: str | date | datetime | None = None,
) -> bool:
    """Apply an inclusive local ISO-date range without timezone conversion."""

    raw_value = value.get("date") if isinstance(value, Mapping) else value
    item_date = _date_text(raw_value)
    if item_date is None:
        return False
    start = _date_text(start_date)
    end = _date_text(end_date)
    if start_date is not None and start is None:
        raise ValueError(f"invalid start_date: {start_date!r}")
    if end_date is not None and end is None:
        raise ValueError(f"invalid end_date: {end_date!r}")
    return (start is None or item_date >= start) and (end is None or item_date <= end)


def filter_items_by_date(
    items: Iterable[Mapping[str, Any]],
    start_date: str | date | datetime | None = None,
    end_date: str | date | datetime | None = None,
    *,
    include_missing: bool = True,
) -> list[Mapping[str, Any]]:
    """Locally filter dated items, optionally retaining missing-date inventory."""

    selected: list[Mapping[str, Any]] = []
    for item in items:
        if _date_text(item.get("date")) is None:
            if include_missing:
                selected.append(item)
        elif date_in_range(item, start_date, end_date):
            selected.append(item)
    return selected


def _link(resource: Mapping[str, Any] | None, relation: str) -> str | None:
    if not isinstance(resource, Mapping):
        return None
    links = resource.get("_links")
    if not isinstance(links, Mapping):
        return None
    link = links.get(relation)
    if isinstance(link, Mapping):
        href = link.get("href")
        if isinstance(href, str):
            return href
    if isinstance(link, str):
        return link
    return None


def _embedded(resource: Mapping[str, Any] | None, relation: str) -> Any:
    if not isinstance(resource, Mapping):
        return None
    embedded = resource.get("_embedded")
    return embedded.get(relation) if isinstance(embedded, Mapping) else None


def _as_resources(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, list):
        return [entry for entry in value if isinstance(entry, Mapping)]
    return []


def _related_url(resource: Mapping[str, Any] | None) -> str | None:
    return _link(resource, "related") or _link(resource, "download")


def _thumbnail_url(item: Mapping[str, Any]) -> str | None:
    images = _as_resources(_embedded(item, "images"))
    order = {"wide": 0, "square": 1, "banner": 2}
    images.sort(key=lambda image: order.get(str(image.get("type", "")), 99))
    for image in images:
        url = _related_url(image)
        if url:
            return url
        source = _embedded(image, "source")
        url = _related_url(source if isinstance(source, Mapping) else None)
        if url:
            return url
    return None


def _first_string(resource: Mapping[str, Any], names: Sequence[str]) -> str | None:
    for name in names:
        value = resource.get(name)
        if isinstance(value, str) and value:
            return value
    return None


def _url_basename(url: str | None) -> str | None:
    if not url:
        return None
    name = Path(unquote(urlparse(url).path)).name
    return name or None


def _url_format(url: str | None) -> str | None:
    name = _url_basename(url)
    suffix = Path(name).suffix.lstrip(".").lower() if name else ""
    return suffix or None


def _first_duration(*resources: Mapping[str, Any] | None) -> int | float | None:
    for resource in resources:
        if not isinstance(resource, Mapping):
            continue
        value = resource.get("duration")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
    return None


def _media_values(item: Mapping[str, Any]) -> dict[str, Any]:
    audio = _embedded(item, "audio")
    audio = audio if isinstance(audio, Mapping) else None
    audio_outputs = _as_resources(_embedded(audio, "audio-outputs"))
    audio_outputs.sort(
        key=lambda output: int(output.get("bitrate") or output.get("file_size") or 0),
        reverse=True,
    )
    audio_output = audio_outputs[0] if audio_outputs else None
    native_audio_url = _related_url(audio) or _related_url(audio_output)
    external_audio_url = _first_string(
        item, ("external_audio_url", "externalAudioUrl", "audio_url")
    )

    video = _embedded(item, "video")
    video = video if isinstance(video, Mapping) else None
    video_outputs = _as_resources(_embedded(video, "video-outputs"))
    video_outputs.sort(
        key=lambda output: (
            int(output.get("height") or 0),
            int(output.get("width") or 0),
            int(output.get("bitrate") or output.get("file_size") or 0),
        ),
        reverse=True,
    )
    video_output = video_outputs[0] if video_outputs else None
    native_video_url = _related_url(video_output) or _related_url(video)
    external_video_url = _first_string(
        item, ("external_video_url", "externalVideoUrl", "video_url")
    )

    playlists = _as_resources(_embedded(video, "playlists"))
    native_hls_url = None
    for playlist in playlists:
        content_type = str(playlist.get("content_type", "")).lower()
        playlist_type = str(playlist.get("type", "")).lower()
        if "mpegurl" in content_type or "m3u8" in content_type or playlist_type == "hls":
            native_hls_url = _related_url(playlist)
            if native_hls_url:
                break
    external_hls_url = _first_string(
        item, ("external_m3u8_url", "external_hls_url", "externalM3u8Url")
    )

    duration = _first_duration(audio_output, audio, video_output, video, item)
    selected_audio_url = native_audio_url or external_audio_url
    selected_video_url = native_video_url or external_video_url or external_hls_url or native_hls_url
    audio_filename = _first_string(
        audio or {}, ("original_filename", "filename", "title")
    ) or _url_basename(selected_audio_url)
    video_filename = _first_string(
        video or {}, ("original_filename", "filename", "title")
    ) or _url_basename(selected_video_url)

    return {
        "audio_url": selected_audio_url,
        "native_audio_url": native_audio_url,
        "external_audio_url": external_audio_url,
        "video_url": selected_video_url,
        "native_video_url": native_video_url,
        "external_video_url": external_video_url,
        "hls_url": external_hls_url or native_hls_url,
        "native_hls_url": native_hls_url,
        "external_hls_url": external_hls_url,
        "duration": duration,
        "duration_ms": duration,
        "duration_seconds": int(duration / 1000) if duration is not None else None,
        "original_filename": audio_filename or video_filename,
        "audio_original_filename": audio_filename,
        "video_original_filename": video_filename,
        "media_format": _url_format(selected_video_url or selected_audio_url),
    }


def _series_for_item(
    item: Mapping[str, Any],
    series_by_id: Mapping[str, Mapping[str, Any]] | None,
) -> Mapping[str, Any] | None:
    series = _embedded(item, "media-series")
    if isinstance(series, Mapping):
        return series
    series_id = item.get("media_series_id") or item.get("media-series_id")
    if isinstance(series_id, str) and series_by_id:
        return series_by_id.get(series_id)
    return None


def _model_field_names(model: Any) -> set[str] | None:
    fields = getattr(model, "model_fields", None) or getattr(model, "__fields__", None)
    if isinstance(fields, Mapping):
        return set(fields)
    try:
        signature = inspect.signature(model)
    except (TypeError, ValueError):
        return None
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in signature.parameters.values()):
        return None
    return {
        name
        for name, parameter in signature.parameters.items()
        if name != "self"
        and parameter.kind
        in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }


def _make_sermon_record(values: dict[str, Any]) -> Any:
    if SermonRecord is None:
        return values
    fields = _model_field_names(SermonRecord)
    kwargs = values if fields is None else {key: value for key, value in values.items() if key in fields}
    return SermonRecord(**kwargs)


def normalize_item(
    item: Mapping[str, Any],
    series_by_id: Mapping[str, Mapping[str, Any]] | None = None,
    *,
    app_shortcode: str | None = None,
) -> Any:
    """Normalize one media item without inferring editorial metadata."""

    raw = copy.deepcopy(dict(item))
    item_id = item.get("id")
    item_date = _date_text(item.get("date"))
    series = _series_for_item(item, series_by_id)
    series_id = series.get("id") if isinstance(series, Mapping) else None
    series_title = series.get("title") if isinstance(series, Mapping) else None
    scriptures = copy.deepcopy(item.get("scriptures"))
    if not isinstance(scriptures, list):
        scriptures = [] if scriptures is None else [scriptures]
    tags = copy.deepcopy(item.get("tags"))
    if not isinstance(tags, list):
        tags = [] if tags is None else [tags]

    summary_html = item.get("summary")
    summary = item.get("summary_text") if item.get("summary_text") is not None else summary_html
    service_type = item.get("service_type")
    if service_type is None:
        service_type = item.get("service-type")
    explicit_topics: list[str] = []
    for tag in tags:
        if isinstance(tag, Mapping) and str(tag.get("type", "")).casefold() == "topic":
            value = tag.get("value") or tag.get("name")
            if isinstance(value, str) and value.strip():
                explicit_topics.append(value.strip())
        elif isinstance(tag, str) and tag.casefold().startswith("topic:"):
            value = tag.partition(":")[2].strip()
            if value:
                explicit_topics.append(value)

    media = _media_values(item)
    has_audio = bool(media["audio_url"])
    has_video = bool(media["video_url"] or media["hls_url"])
    if item_date is None:
        archive_status = "needs_review"
    elif not has_audio and not has_video:
        archive_status = "no_media"
    elif has_audio and not has_video:
        archive_status = "audio_only"
    else:
        archive_status = "metadata_complete"
    media_type = (
        "audio_video" if has_audio and has_video else "video" if has_video else "audio" if has_audio else None
    )
    scripture_text = "; ".join(str(value) for value in scriptures) or None
    api_source_url = _link(item, "self")
    share_url = _link(item, "share")
    embed_url = _link(item, "embed")
    source_url = api_source_url or share_url or embed_url
    series_shortcode = series.get("short_code") if isinstance(series, Mapping) else None
    public_series_url = (
        f"https://subsplash.com/+{app_shortcode}/lb/ms/+{series_shortcode}"
        if app_shortcode and isinstance(series_shortcode, str)
        else _link(series, "self")
    )
    bible_book = extract_bible_book(
        series_title if isinstance(series_title, str) else None,
        [str(value) for value in scriptures],
    )

    values: dict[str, Any] = {
        "id": item_id,
        "sermon_id": item_id,
        "item_id": item_id,
        "platform_item_id": item_id,
        "source_id": item_id,
        "external_id": item_id,
        "source": "subsplash",
        "platform": "subsplash",
        "source_platform": "subsplash",
        "app_key": item.get("app_key"),
        "short_code": item.get("short_code"),
        "slug": item.get("slug"),
        "canonical_url": share_url or source_url,
        "source_url": source_url,
        "share_url": share_url,
        "embed_url": embed_url,
        "date": item_date,
        "sermon_date": item_date,
        "year": int(item_date[:4]) if item_date else None,
        "title": item.get("title") or "",
        "subtitle": item.get("subtitle"),
        "summary": summary,
        "summary_text": item.get("summary_text"),
        "summary_html": summary_html,
        "description": summary,
        "speaker": item.get("speaker"),
        "tags": tags,
        "scriptures": scriptures,
        "scripture": scripture_text,
        "scripture_reference": scripture_text,
        "topic": item.get("topic") or "; ".join(explicit_topics) or None,
        "service_type": service_type,
        "series_id": series_id,
        "platform_series_id": series_id,
        "series": series_title,
        "series_title": series_title,
        "series_url": public_series_url,
        "series_items_url": _link(series, "media-items"),
        "bible_book": bible_book,
        "book_of_bible": bible_book,
        "thumbnail_url": _thumbnail_url(item),
        "published_at": item.get("published_at"),
        "status": archive_status,
        "source_status": item.get("status"),
        "needs_review": item_date is None,
        "review_reason": "missing_date" if item_date is None else None,
        "media_type": media_type,
        "media_format": media["media_format"],
        "has_video": has_video,
        "has_audio": has_audio,
        "media_url": media["video_url"] or media["audio_url"],
        "video_source_url": media["video_url"] or media["hls_url"],
        "audio_source_url": media["audio_url"],
        "filename": media["original_filename"],
        "original_media_filename": media["original_filename"],
        "download_status": archive_status,
        "in_scope": True,
        "raw_json": raw,
        "raw": raw,
        "raw_metadata": raw,
        "raw_json_text": json.dumps(raw, ensure_ascii=False, sort_keys=True),
    }
    values.update(media)
    return _make_sermon_record(values)


def normalize_series(series: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a Subsplash media-series object for ``ArchiveDB.upsert_series``."""

    raw = copy.deepcopy(dict(series))
    images_holder = {"_embedded": {"images": _embedded(series, "images")}}
    series_id = series.get("id")
    description = (
        series.get("summary_text")
        if series.get("summary_text") is not None
        else series.get("summary")
    )
    source_url = _link(series, "self")
    return {
        "id": series_id,
        "series_id": series_id,
        "source_id": series_id,
        "platform": "subsplash",
        "platform_series_id": series_id,
        "app_key": series.get("app_key"),
        "short_code": series.get("short_code"),
        "slug": series.get("slug"),
        "title": series.get("title"),
        "subtitle": series.get("subtitle"),
        "summary": description,
        "description": description,
        "summary_text": series.get("summary_text"),
        "summary_html": series.get("summary"),
        "canonical_url": source_url,
        "source_url": source_url,
        "media_items_url": _link(series, "media-items"),
        "thumbnail_url": _thumbnail_url(images_holder),
        "item_count": series.get("published_media_items_count")
        if series.get("published_media_items_count") is not None
        else series.get("media_items_count"),
        "status": series.get("status"),
        "published_at": series.get("published_at"),
        "raw_json": raw,
        "raw_metadata": raw,
    }


def parse_collection(payload: Mapping[str, Any], relation: str) -> list[Mapping[str, Any]]:
    """Extract resources from a HAL collection using hyphen/underscore aliases."""

    embedded = payload.get("_embedded")
    if not isinstance(embedded, Mapping):
        return []
    aliases = (relation, relation.replace("_", "-"), relation.replace("-", "_"))
    for alias in aliases:
        resources = embedded.get(alias)
        if isinstance(resources, list):
            return [resource for resource in resources if isinstance(resource, Mapping)]
        if isinstance(resources, Mapping):
            return [resources]
    return []


def hal_next_link(payload: Mapping[str, Any]) -> str | None:
    return _link(payload, "next")


class RawResponseStore:
    """Write every fetched HTML/JSON response beneath one run directory."""

    def __init__(self, root: str | Path, run_id: str | int) -> None:
        safe_run_id = _SAFE_NAME_RE.sub("_", str(run_id)).strip("._") or "run"
        self.directory = Path(root) / "data" / "raw" / safe_run_id
        self.directory.mkdir(parents=True, exist_ok=True)
        self._sequence = 0

    @property
    def responses_saved(self) -> int:
        return self._sequence

    def save(self, response: httpx.Response, label: str) -> Path:
        self._sequence += 1
        content_type = response.headers.get("content-type", "").lower()
        text = response.text
        is_json = "json" in content_type or text.lstrip().startswith(("{", "["))
        is_html = "html" in content_type or "<html" in text[:1000].lower()
        if is_html or "apiToken" in text:
            text = redact_shoebox_token(text)
        extension = "json" if is_json else "html" if is_html else "txt"
        safe_label = _SAFE_NAME_RE.sub("_", label).strip("._") or "response"
        path = self.directory / f"{self._sequence:04d}_{safe_label}.{extension}"
        encoding = response.encoding or "utf-8"
        path.write_text(text, encoding=encoding)
        saved_bytes = text.encode(encoding, errors="replace")
        manifest_entry = {
            "sequence": self._sequence,
            "label": label,
            "filename": path.name,
            "requested_url": str(response.request.url),
            "final_url": str(response.url),
            "status_code": response.status_code,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "content_type": response.headers.get("content-type"),
            "etag": response.headers.get("etag"),
            "last_modified": response.headers.get("last-modified"),
            "byte_count": len(saved_bytes),
            "sha256": hashlib.sha256(saved_bytes).hexdigest(),
            "redacted": is_html or "apiToken" in response.text,
        }
        with (self.directory / "manifest.jsonl").open("a", encoding="utf-8") as manifest:
            manifest.write(json.dumps(manifest_entry, ensure_ascii=False, sort_keys=True) + "\n")
        return path


@dataclass
class CrawlStats:
    start_pages: int = 0
    builder_lists: int = 0
    builder_rows: int = 0
    series_fetched: int = 0
    series_upserted: int = 0
    item_pages: int = 0
    items_fetched: int = 0
    items_upserted: int = 0
    items_added: int = 0
    items_updated: int = 0
    items_out_of_range: int = 0
    items_missing_date: int = 0
    items_broadcast_filtered: int = 0

    def as_dict(self) -> dict[str, int]:
        return dict(vars(self))


def _call_supported(method: Callable[..., Any], values: Mapping[str, Any]) -> Any:
    """Call a DB method with the keyword subset its current signature accepts."""

    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return method(**dict(values))
    parameters = signature.parameters
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in parameters.values()):
        return method(**dict(values))
    kwargs = {
        key: value
        for key, value in values.items()
        if key in parameters
        and parameters[key].kind
        in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }
    return method(**kwargs)


def _run_id_from(value: Any) -> str | int | None:
    if isinstance(value, (str, int)):
        return value
    if isinstance(value, Mapping):
        candidate = value.get("run_id") if value.get("run_id") is not None else value.get("id")
        return candidate if isinstance(candidate, (str, int)) else None
    for name in ("run_id", "id"):
        candidate = getattr(value, name, None)
        if isinstance(candidate, (str, int)):
            return candidate
    return None


class CalvarySpokaneDiscovery:
    """Synchronous, polite crawler for the public Calvary Spokane archive."""

    def __init__(
        self,
        root: str | Path,
        db: Any,
        *,
        start_urls: Sequence[str] = START_URLS,
        client: httpx.Client | None = None,
        delay_range: tuple[float, float] = (0.25, 0.7),
        retries: int = 4,
        timeout: float = 30.0,
        sleep: Callable[[float], None] = time.sleep,
        random_source: random.Random | None = None,
    ) -> None:
        self.root = Path(root)
        self.db = db
        self.start_urls = tuple(start_urls)
        self.delay_range = delay_range
        self.retries = retries
        self.sleep = sleep
        self.random = random_source or random.Random()
        self._owns_client = client is None
        self.client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT, "Accept": "application/hal+json, application/json, text/html"},
            follow_redirects=True,
            timeout=timeout,
        )
        if client is not None:
            self.client.headers.setdefault("User-Agent", USER_AGENT)
        self.raw_store: RawResponseStore | None = None
        self.token: str | None = None
        self.app_shortcode: str | None = None
        self.list_shortcodes: set[str] = set()
        self._token_page_url: str | None = None
        self.run_id: str | int | None = None

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> "CalvarySpokaneDiscovery":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _delay(self, attempt: int = 0) -> None:
        low, high = self.delay_range
        jitter = self.random.uniform(max(0.0, low), max(low, high))
        backoff = 0.75 * (2**attempt) if attempt else 0.0
        self.sleep(jitter + backoff)

    def _request(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        auth: bool = False,
        label: str = "response",
    ) -> httpx.Response:
        attempt = 0
        refreshed = False
        while True:
            self._delay(attempt)
            headers = {"Authorization": f"Bearer {self.token}"} if auth and self.token else {}
            try:
                response = self.client.get(url, params=params, headers=headers)
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt >= self.retries:
                    raise
                attempt += 1
                continue

            if self.raw_store is not None:
                self.raw_store.save(response, label)

            if response.status_code == 401 and auth and not refreshed:
                refreshed = True
                self.refresh_token()
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < self.retries:
                    retry_after = response.headers.get("retry-after")
                    if retry_after:
                        try:
                            self.sleep(min(float(retry_after), 60.0))
                        except ValueError:
                            pass
                    attempt += 1
                    continue
            response.raise_for_status()
            return response

    def _json_request(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        label: str,
    ) -> Mapping[str, Any]:
        response = self._request(url, params=params, auth=True, label=label)
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise ValueError(f"expected a JSON object from {response.url}")
        return payload

    def _hal_pages(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None,
        label: str,
    ) -> Iterator[Mapping[str, Any]]:
        next_url: str | None = url
        next_params = params
        seen: set[str] = set()
        page = 0
        observed = 0
        expected_total: int | None = None
        while next_url:
            page += 1
            payload = self._json_request(next_url, params=next_params, label=f"{label}_{page:04d}")
            count = payload.get("count")
            total = payload.get("total")
            if isinstance(count, int):
                observed += count
            if expected_total is None and isinstance(total, int):
                expected_total = total
            elif isinstance(total, int) and expected_total != total:
                raise RuntimeError(
                    f"HAL total changed during {label} pagination: {expected_total} -> {total}"
                )
            yield payload
            candidate = hal_next_link(payload)
            if candidate is None:
                if expected_total is not None and observed != expected_total:
                    raise RuntimeError(
                        f"Incomplete HAL pagination for {label}: observed {observed}, "
                        f"expected {expected_total}"
                    )
                break
            if candidate in seen:
                raise RuntimeError(f"HAL pagination loop detected at {candidate}")
            seen.add(candidate)
            next_url = candidate
            next_params = None

    def refresh_token(self) -> str:
        if not self._token_page_url:
            if not self.app_shortcode or not self.list_shortcodes:
                raise RuntimeError("cannot refresh token before discovering app and list shortcodes")
            list_shortcode = sorted(self.list_shortcodes)[0]
            self._token_page_url = (
                f"https://subsplash.com/+{self.app_shortcode}/lb/li/+{list_shortcode}"
            )
        response = self._request(self._token_page_url, auth=False, label="subsplash_token_page")
        self.token = parse_shoebox_token(response.text)
        return self.token

    def _start_run(
        self,
        start_date: str | date | datetime | None,
        end_date: str | date | datetime | None,
        *,
        limit: int | None,
        dry_run: bool,
    ) -> str | int:
        now = datetime.now(timezone.utc).isoformat()
        result = None
        method = getattr(self.db, "start_run", None) or getattr(self.db, "start_crawl", None)
        if callable(method):
            metadata = {
                "source": "calvary_spokane",
                "start_date": _date_text(start_date),
                "end_date": _date_text(end_date),
                "limit": limit,
                "dry_run": dry_run,
            }
            result = _call_supported(
                method,
                {
                    "source": "calvary_spokane",
                    "archive": "calvary_spokane",
                    "source_url": self.start_urls[0] if self.start_urls else None,
                    "metadata": metadata,
                    "started_at": now,
                    "start_date": _date_text(start_date),
                    "end_date": _date_text(end_date),
                },
            )
        discovered = _run_id_from(result)
        return discovered or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

    def _finish_run(self, status: str, stats: CrawlStats, error: str | None = None) -> None:
        method = getattr(self.db, "finish_run", None) or getattr(self.db, "finish_crawl", None)
        if not callable(method):
            return
        pages_seen = self.raw_store.responses_saved if self.raw_store is not None else 0
        _call_supported(
            method,
            {
                "run_id": self.run_id,
                "id": self.run_id,
                "status": status,
                "stats": stats.as_dict(),
                "counts": stats.as_dict(),
                "pages_seen": pages_seen,
                "items_seen": stats.items_fetched,
                "items_added": stats.items_added,
                "items_updated": stats.items_updated,
                "series_found": stats.series_fetched,
                "item_pages": stats.item_pages,
                "api_records": stats.items_fetched,
                "target_records": stats.items_upserted,
                "missing_date_records": stats.items_missing_date,
                "out_of_range_records": stats.items_out_of_range,
                "error": error,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def _record_listing(self, **values: Any) -> None:
        method = getattr(self.db, "record_listing", None)
        if not callable(method):
            return
        common = {
            "run_id": self.run_id,
            "source": "subsplash",
            **values,
        }
        try:
            _call_supported(method, common)
        except TypeError:
            # A few early ArchiveDB versions accepted one listing dictionary.
            method(common)

    def _record_listing_audit(
        self,
        payload: Mapping[str, Any],
        relation: str,
        page_number: int,
        notes: str,
    ) -> None:
        method = getattr(self.db, "record_listing_audit", None)
        if not callable(method):
            return
        resources = parse_collection(payload, relation)
        item_ids: list[str] = []
        for resource in resources:
            resource_id = resource.get("id")
            embedded = resource.get("_embedded")
            if relation == "list-rows" and isinstance(embedded, Mapping):
                target = next(
                    (
                        value
                        for key, value in embedded.items()
                        if key != "source-list" and isinstance(value, Mapping)
                    ),
                    None,
                )
                target_id = target.get("id") if isinstance(target, Mapping) else None
                if isinstance(target_id, str):
                    resource_id = target_id
            elif not isinstance(resource_id, str) and isinstance(embedded, Mapping):
                target = next(
                    (
                        value
                        for key, value in embedded.items()
                        if key != "source-list" and isinstance(value, Mapping)
                    ),
                    None,
                )
                resource_id = target.get("id") if isinstance(target, Mapping) else None
            if isinstance(resource_id, str):
                item_ids.append(resource_id)
        listing_url = _link(payload, "self")
        if not listing_url:
            return
        _call_supported(
            method,
            {
                "listing_url": listing_url,
                "observed_count": len(resources),
                "run_id": self.run_id,
                "page_number": page_number,
                "expected_count": payload.get("total"),
                "item_ids": item_ids,
                "notes": notes,
            },
        )

    def _upsert_series(self, series: Mapping[str, Any]) -> None:
        method = getattr(self.db, "upsert_series", None)
        if callable(method):
            normalized = normalize_series(series)
            try:
                _call_supported(method, normalized)
            except TypeError:
                # The interface originally accepted one normalized dictionary.
                method(normalized)

    def _upsert_sermon(
        self,
        item: Mapping[str, Any],
        series_by_id: Mapping[str, Mapping[str, Any]],
        *,
        in_scope: bool = True,
    ) -> bool:
        method = getattr(self.db, "upsert_sermon", None)
        if not callable(method):
            return False
        item_id = item.get("id")
        getter = getattr(self.db, "get_sermon", None) or getattr(self.db, "get", None)
        existed = bool(callable(getter) and isinstance(item_id, str) and getter(item_id) is not None)
        record = normalize_item(item, series_by_id, app_shortcode=self.app_shortcode)
        if isinstance(record, Mapping):
            record = {**record, "in_scope": in_scope}
        else:
            record.in_scope = in_scope
        method(record)
        return not existed

    def _discover_start_pages(self, stats: CrawlStats) -> None:
        apps: set[str] = set()
        lists: set[str] = set()
        for index, url in enumerate(self.start_urls, 1):
            response = self._request(url, label=f"start_page_{index:02d}")
            found_apps, found_lists = extract_subsplash_identifiers(response.text)
            apps.update(found_apps)
            lists.update(found_lists)
            stats.start_pages += 1
        if not apps:
            raise RuntimeError("no Subsplash app shortcode found on Calvary Spokane start pages")
        if len(apps) != 1:
            raise RuntimeError(f"ambiguous Subsplash app shortcodes: {sorted(apps)}")
        if not lists:
            raise RuntimeError("no Subsplash Builder-list shortcode found on start pages")
        self.app_shortcode = next(iter(apps))
        self.list_shortcodes = lists
        self._token_page_url = (
            f"https://subsplash.com/+{self.app_shortcode}/lb/li/+{sorted(lists)[0]}"
        )

    def _resolve_app_key(self) -> str:
        payload = self._json_request(
            APPS_URL,
            params={"filter[short_code]": self.app_shortcode, "page[size]": 100},
            label="accounts_apps",
        )
        apps = parse_collection(payload, "apps")
        exact = [app for app in apps if app.get("short_code") == self.app_shortcode]
        if len(exact) != 1 or not isinstance(exact[0].get("id"), str):
            raise RuntimeError(
                f"could not uniquely resolve Subsplash app shortcode {self.app_shortcode!r}"
            )
        return str(exact[0]["id"])

    def _crawl_builder_lists(self, app_key: str, stats: CrawlStats) -> None:
        pending = list(sorted(self.list_shortcodes))
        seen_shortcodes: set[str] = set()
        while pending:
            shortcode = pending.pop(0)
            if shortcode in seen_shortcodes:
                continue
            seen_shortcodes.add(shortcode)
            list_pages = self._hal_pages(
                BUILDER_LISTS_URL,
                params={
                    "filter[app_key]": app_key,
                    "filter[short_code]": shortcode,
                    "page[size]": 100,
                },
                label=f"builder_list_{shortcode}",
            )
            for list_page_number, payload in enumerate(list_pages, 1):
                self._record_listing_audit(
                    payload, "lists", list_page_number, f"Builder list {shortcode}"
                )
                for builder_list in parse_collection(payload, "lists"):
                    stats.builder_lists += 1
                    list_id = builder_list.get("id")
                    self._record_listing(
                        listing_type="builder_list",
                        list_id=list_id,
                        list_shortcode=shortcode,
                        item_id=list_id,
                        item_type="list",
                        position=None,
                        source_url=_link(builder_list, "self"),
                        raw_json=copy.deepcopy(dict(builder_list)),
                        listing=copy.deepcopy(dict(builder_list)),
                    )
                    if not isinstance(list_id, str):
                        continue
                    row_pages = self._hal_pages(
                        BUILDER_ROWS_URL,
                        params={
                            "filter[source_list]": list_id,
                            "include": "list-features",
                            "page[size]": 100,
                        },
                        label=f"builder_rows_{shortcode}",
                    )
                    for row_page_number, rows_payload in enumerate(row_pages, 1):
                        self._record_listing_audit(
                            rows_payload,
                            "list-rows",
                            row_page_number,
                            f"Builder rows for {shortcode}",
                        )
                        for row in parse_collection(rows_payload, "list-rows"):
                            stats.builder_rows += 1
                            row_embedded = row.get("_embedded")
                            targets = row_embedded if isinstance(row_embedded, Mapping) else {}
                            target = next(
                                (
                                    value
                                    for key, value in targets.items()
                                    if key != "source-list" and isinstance(value, Mapping)
                                ),
                                None,
                            )
                            target_id = target.get("id") if isinstance(target, Mapping) else None
                            target_type = row.get("type")
                            self._record_listing(
                                listing_type="builder_row",
                                list_id=list_id,
                                list_shortcode=shortcode,
                                item_id=target_id,
                                target_id=target_id,
                                item_type=target_type,
                                position=row.get("position"),
                                raw_json=copy.deepcopy(dict(row)),
                                listing=copy.deepcopy(dict(row)),
                            )
                            if target_type == "list" and isinstance(target, Mapping):
                                nested = target.get("short_code")
                                if isinstance(nested, str) and nested not in seen_shortcodes:
                                    pending.append(nested)

    @staticmethod
    def _broadcast_is_archivable(item: Mapping[str, Any]) -> bool:
        status = item.get("broadcast_status")
        broadcast = _embedded(item, "broadcast")
        if isinstance(broadcast, Mapping):
            status = broadcast.get("status")
        return status is None or status == "on-demand"

    def run(
        self,
        *,
        start_date: str | date | datetime | None = None,
        end_date: str | date | datetime | None = None,
        limit: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Run discovery, returning run metadata and crawl counts."""

        # Validate the caller's range before creating a database run.
        if start_date is not None and _date_text(start_date) is None:
            raise ValueError(f"invalid start_date: {start_date!r}")
        if end_date is not None and _date_text(end_date) is None:
            raise ValueError(f"invalid end_date: {end_date!r}")
        normalized_start = _date_text(start_date)
        normalized_end = _date_text(end_date)
        if normalized_start is not None and normalized_end is not None and normalized_start > normalized_end:
            raise ValueError("start_date must not be after end_date")
        if limit is not None and limit < 0:
            raise ValueError("limit must not be negative")

        stats = CrawlStats()
        self.run_id = self._start_run(
            start_date,
            end_date,
            limit=limit,
            dry_run=dry_run,
        )
        self.raw_store = RawResponseStore(self.root, self.run_id)
        try:
            self._discover_start_pages(stats)
            self.refresh_token()
            app_key = self._resolve_app_key()
            self._crawl_builder_lists(app_key, stats)

            series_by_id: dict[str, Mapping[str, Any]] = {}
            for payload in self._hal_pages(
                MEDIA_SERIES_URL,
                params={
                    "filter[app_key]": app_key,
                    "filter[status]": "published",
                    "include": "images",
                    "page[size]": 100,
                },
                label="media_series",
            ):
                for series in parse_collection(payload, "media-series"):
                    stats.series_fetched += 1
                    series_id = series.get("id")
                    if isinstance(series_id, str):
                        series_by_id[series_id] = series
                    if not dry_run:
                        self._upsert_series(series)
                        stats.series_upserted += 1

            # Date bounds deliberately do not appear in these API params. Every
            # authoritative page is persisted and counted before local filtering.
            seen_item_ids: set[str] = set()
            for payload in self._hal_pages(
                MEDIA_ITEMS_URL,
                params={
                    "filter[app_key]": app_key,
                    "filter[status]": "published",
                    "filter[broadcast.status|broadcast.status]": "null|on-demand",
                    "include": MEDIA_INCLUDES,
                    "page[size]": 100,
                    "sort": "date,created_at",
                },
                label="media_items",
            ):
                stats.item_pages += 1
                for item in parse_collection(payload, "media-items"):
                    item_id = item.get("id")
                    if isinstance(item_id, str):
                        if item_id in seen_item_ids:
                            raise RuntimeError(f"duplicate media item across API pages: {item_id}")
                        seen_item_ids.add(item_id)
                    stats.items_fetched += 1
                    if not self._broadcast_is_archivable(item):
                        stats.items_broadcast_filtered += 1
                        continue
                    item_date = _date_text(item.get("date"))
                    if item_date is None:
                        stats.items_missing_date += 1
                        self._record_listing(
                            listing_type="needs_review",
                            list_id=None,
                            item_id=item.get("id"),
                            item_type="media-item",
                            position=item.get("position"),
                            reason="missing_date",
                            raw_json=copy.deepcopy(dict(item)),
                            listing=copy.deepcopy(dict(item)),
                        )
                    elif not date_in_range(item_date, start_date, end_date):
                        stats.items_out_of_range += 1
                        if not dry_run and isinstance(item_id, str):
                            getter = getattr(self.db, "get_sermon", None) or getattr(self.db, "get", None)
                            if callable(getter) and getter(item_id) is not None:
                                self._upsert_sermon(item, series_by_id, in_scope=False)
                                stats.items_updated += 1
                        continue
                    if limit is not None and stats.items_upserted >= limit:
                        break
                    if not dry_run:
                        if self._upsert_sermon(item, series_by_id):
                            stats.items_added += 1
                        else:
                            stats.items_updated += 1
                    stats.items_upserted += 1
                if limit is not None and stats.items_upserted >= limit:
                    break

            self._finish_run("partial" if limit is not None else "completed", stats)
            return {
                "run_id": self.run_id,
                "app_shortcode": self.app_shortcode,
                "app_key": app_key,
                "list_shortcodes": sorted(self.list_shortcodes),
                "dry_run": dry_run,
                "limit": limit,
                **stats.as_dict(),
            }
        except Exception as exc:
            self._finish_run("failed", stats, f"{type(exc).__name__}: {exc}")
            raise


# A short alias is convenient for callers and older integration drafts.
Discovery = CalvarySpokaneDiscovery


def discover(
    root: str | Path,
    db: Any,
    *,
    start_date: str | date | datetime | None = None,
    end_date: str | date | datetime | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """One-shot wrapper around :class:`CalvarySpokaneDiscovery`."""

    run_options = {
        key: kwargs.pop(key)
        for key in tuple(kwargs)
        if key in {"limit", "dry_run"}
    }
    with CalvarySpokaneDiscovery(root, db, **kwargs) as crawler:
        return crawler.run(start_date=start_date, end_date=end_date, **run_options)


run_discovery = discover
