"""Small, dependency-free helpers shared by the archiver."""

from __future__ import annotations

import hashlib
import os
import re
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y.%m.%d",
    "%Y%m%d",
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%m.%d.%Y",
    "%m/%d/%y",
    "%m-%d-%y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%B %d %Y",
    "%b %d %Y",
    "%d %B %Y",
    "%d %b %Y",
)
_ORDINAL_DAY = re.compile(r"(?<=\d)(?:st|nd|rd|th)\b", re.IGNORECASE)
_WEEKDAY_PREFIX = re.compile(
    r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+",
    re.IGNORECASE,
)
_UNSAFE_FILENAME = re.compile(r"[^a-z0-9]+")
_WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}
_TRACKING_QUERY_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source"}


def parse_sermon_date(value: date | datetime | str | None) -> date | None:
    """Parse a feed date into ``datetime.date``.

    ISO dates/timestamps and common US church-listing formats are accepted.
    ``None``, blank strings, and unrecognized values return ``None`` so a
    missing date stays missing rather than being replaced with today's date.
    """

    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    iso_text = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
    try:
        return datetime.fromisoformat(iso_text).date()
    except ValueError:
        pass
    try:
        return date.fromisoformat(text)
    except ValueError:
        pass

    text = _WEEKDAY_PREFIX.sub("", text)
    text = _ORDINAL_DAY.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    for date_format in _DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None


def is_date_in_range(
    value: date | datetime | str | None,
    start: date | datetime | str | None = None,
    end: date | datetime | str | None = None,
) -> bool:
    """Return whether ``value`` falls within the inclusive optional bounds."""

    parsed = parse_sermon_date(value)
    parsed_start = parse_sermon_date(start)
    parsed_end = parse_sermon_date(end)
    if parsed is None:
        return False
    if start is not None and parsed_start is None:
        return False
    if end is not None and parsed_end is None:
        return False
    if parsed_start is not None and parsed_end is not None and parsed_start > parsed_end:
        return False
    return (parsed_start is None or parsed >= parsed_start) and (
        parsed_end is None or parsed <= parsed_end
    )


def date_in_range(
    value: date | datetime | str | None,
    start: date | datetime | str | None = None,
    end: date | datetime | str | None = None,
) -> bool:
    """Alias for :func:`is_date_in_range`."""

    return is_date_in_range(value, start, end)


def _ascii_slug(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = text.casefold().replace("&", " and ")
    return _UNSAFE_FILENAME.sub("-", text).strip("-._ ")


def slugify(value: Any, *, max_length: int = 80, fallback: str = "untitled") -> str:
    """Create a filesystem-safe, deterministic ASCII slug."""

    if max_length < 1:
        raise ValueError("max_length must be positive")
    slug = _ascii_slug(value) or _ascii_slug(fallback) or "untitled"
    if slug in _WINDOWS_RESERVED:
        slug = f"_{slug}"
    slug = slug[:max_length].rstrip("-._ ") or "untitled"
    return slug


def sanitize_filename_component(
    value: Any, *, max_length: int = 80, fallback: str = "untitled"
) -> str:
    """Alias spelling that emphasizes use as one filename component."""

    return slugify(value, max_length=max_length, fallback=fallback)


def _normalize_extension(extension: str | None) -> str:
    if not extension:
        return ""
    cleaned = str(extension).strip().lower()
    while cleaned.endswith(".part"):
        cleaned = cleaned[:-5]
    cleaned = cleaned.lstrip(".")
    cleaned = re.sub(r"[^a-z0-9]+", "", cleaned)
    return f".{cleaned}" if cleaned else ""


def build_media_filename(
    item_id: str,
    title: str,
    sermon_date: date | datetime | str | None = None,
    extension: str = ".mp4",
    *,
    speaker: str | None = None,
    partial: bool = False,
    max_length: int = 180,
) -> str:
    """Build a stable archive filename containing the source item ID.

    The final extension is normalized and ``.part`` is appended only for a
    temporary download.  A digest is added when sanitizing/truncating the item
    ID could otherwise make two distinct source identifiers collide.
    """

    if max_length < 32:
        raise ValueError("max_length must be at least 32")
    raw_item_id = str(item_id).strip()
    if not raw_item_id:
        raise ValueError("item_id must not be empty")

    item_component = slugify(raw_item_id, max_length=64, fallback="item")
    simple_item = raw_item_id.casefold().strip()
    if item_component != simple_item or len(raw_item_id) > 64:
        digest = hashlib.sha256(raw_item_id.encode("utf-8")).hexdigest()[:10]
        item_component = f"{item_component[:52].rstrip('-')}-{digest}"

    components: list[str] = []
    parsed_date = parse_sermon_date(sermon_date)
    if parsed_date is not None:
        components.append(parsed_date.isoformat())
    components.append(slugify(title, max_length=90))
    if speaker:
        components.append(slugify(speaker, max_length=40, fallback="speaker"))
    components.append(item_component)

    suffix = _normalize_extension(extension)
    part_suffix = ".part" if partial else ""
    fixed_length = len(suffix) + len(part_suffix)
    stem_limit = max_length - fixed_length
    stem = "-".join(components)
    if len(stem) > stem_limit:
        # Keep the item ID intact; trim the descriptive prefix first.
        reserved = len(item_component) + 1
        prefix = "-".join(components[:-1])[: max(1, stem_limit - reserved)].rstrip("-._ ")
        stem = f"{prefix}-{item_component}" if prefix else item_component
    return f"{stem}{suffix}{part_suffix}"


def build_filename(
    sermon_date: date | datetime | str | None,
    title: str,
    item_id: str,
    extension: str = ".mp4",
    *,
    speaker: str | None = None,
    partial: bool = False,
    max_length: int = 180,
) -> str:
    """Date-first compatibility wrapper around :func:`build_media_filename`."""

    return build_media_filename(
        item_id,
        title,
        sermon_date,
        extension,
        speaker=speaker,
        partial=partial,
        max_length=max_length,
    )


def safe_filename(name: str, *, max_length: int = 180) -> str:
    """Sanitize an arbitrary filename while preserving its extension/``.part``."""

    raw_name = Path(str(name)).name
    partial = raw_name.casefold().endswith(".part")
    if partial:
        raw_name = raw_name[:-5]
    suffix = Path(raw_name).suffix
    stem = raw_name[: -len(suffix)] if suffix else raw_name
    normalized_suffix = _normalize_extension(suffix)
    fixed_length = len(normalized_suffix) + (5 if partial else 0)
    safe_stem = slugify(stem, max_length=max(1, max_length - fixed_length))
    return f"{safe_stem}{normalized_suffix}{'.part' if partial else ''}"


def partial_path(path: str | os.PathLike[str]) -> Path:
    """Return the temporary ``.part`` path for a final media path."""

    result = Path(path)
    return result if result.name.endswith(".part") else result.with_name(f"{result.name}.part")


def final_path_from_part(path: str | os.PathLike[str]) -> Path:
    """Remove one trailing ``.part`` suffix, leaving ordinary paths unchanged."""

    result = Path(path)
    return result.with_name(result.name[:-5]) if result.name.endswith(".part") else result


def utc_now() -> datetime:
    """Return an aware current UTC datetime."""

    return datetime.now(timezone.utc)


def utc_timestamp(moment: datetime | None = None) -> str:
    """Return a stable ISO-8601 UTC timestamp with a ``Z`` suffix."""

    current = moment or utc_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)
    return current.isoformat(timespec="seconds").replace("+00:00", "Z")


def utc_now_iso() -> str:
    """Alias for callers that prefer an explicit string-oriented name."""

    return utc_timestamp()


def sha256_file(path: str | os.PathLike[str], *, chunk_size: int = 1024 * 1024) -> str:
    """Stream a file and return its lowercase SHA-256 digest."""

    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_sha256(path: str | os.PathLike[str], *, chunk_size: int = 1024 * 1024) -> str:
    """Alias for :func:`sha256_file`."""

    return sha256_file(path, chunk_size=chunk_size)


def canonicalize_url(url: str | None, base_url: str | None = None) -> str | None:
    """Return a conservative canonical form suitable for duplicate checks."""

    if url is None or not str(url).strip():
        return None
    resolved = urljoin(base_url, str(url).strip()) if base_url else str(url).strip()
    parsed = urlsplit(resolved)
    scheme = parsed.scheme.casefold()
    hostname = (parsed.hostname or "").casefold()
    if not hostname:
        return resolved.split("#", 1)[0]

    try:
        port = parsed.port
    except ValueError:
        return resolved.split("#", 1)[0]
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        hostname = f"{hostname}:{port}"
    if parsed.username:
        credentials = parsed.username
        if parsed.password:
            credentials += f":{parsed.password}"
        hostname = f"{credentials}@{hostname}"

    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_") and key.casefold() not in _TRACKING_QUERY_KEYS
    ]
    query = urlencode(sorted(query_items), doseq=True)
    return urlunsplit((scheme, hostname, path, query, ""))


def canonical_url(url: str | None, base_url: str | None = None) -> str | None:
    """Alias for :func:`canonicalize_url`."""

    return canonicalize_url(url, base_url)
