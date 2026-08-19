"""Download, resume, and verify media for the Calvary Spokane archive.

The module deliberately keeps orchestration serial by default.  Downloads are I/O
heavy and the public providers involved are better served by a conservative
request rate; ``workers`` is nevertheless part of the configuration so a future
bounded executor can be introduced without changing the command-line contract.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

# Import the archive's filename safety helper without pinning this downloader to
# a single historical helper name.
_project_safe_filename: Callable[..., object] | None = None
try:
    _utils = importlib.import_module(f"{__package__ or 'calvary_archive'}.utils")
    _project_safe_filename = getattr(
        _utils, "sanitize_filename_component", None
    ) or getattr(_utils, "safe_filename", None)
except ImportError:  # Keep this module usable in isolation and focused tests.
    pass


DOWNLOADABLE_STATUSES = {
    "discovered",
    "metadata_complete",
    "queued",
    "downloading",
    "downloaded",
}
DEFAULT_START_DATE = date(2004, 6, 1)
DEFAULT_END_DATE = date(2010, 8, 31)
RETRYABLE_STATUSES = {"failed", "needs_review"}
FINAL_STATUSES = {"verified", "audio_only", "no_media"}

_VIDEO_EXTENSIONS = {
    ".mp4",
    ".m4v",
    ".mov",
    ".webm",
    ".mkv",
    ".avi",
    ".mpeg",
    ".mpg",
}
_AUDIO_EXTENSIONS = {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".opus", ".flac"}
_MEDIA_EXTENSIONS = _VIDEO_EXTENSIONS | _AUDIO_EXTENSIONS
_HLS_RE = re.compile(r"(?:\.m3u8)(?:$|[?#])", re.IGNORECASE)
_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


class DownloadBackend(str, Enum):
    """A mature transfer backend selected from the source URL."""

    DIRECT_HTTP = "direct"
    DIRECT = "direct"  # Friendly alias.
    YT_DLP = "yt-dlp"
    FFMPEG_HLS = "ffmpeg"
    HLS = "ffmpeg"  # Friendly alias.


@dataclass(frozen=True)
class DownloadConfig:
    root: Path
    start_date: date = DEFAULT_START_DATE
    end_date: date = DEFAULT_END_DATE
    workers: int = 1
    retries: int = 3
    backoff: float = 1.0
    timeout: float = 60.0
    process_timeout: float = 21600.0
    chunk_size: int = 1024 * 1024
    download_audio: bool = False
    use_ffprobe: bool = True
    yt_dlp_binary: str = "yt-dlp"
    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root))
        start = self.start_date if isinstance(self.start_date, date) else date.fromisoformat(str(self.start_date))
        end = self.end_date if isinstance(self.end_date, date) else date.fromisoformat(str(self.end_date))
        if start > end:
            raise ValueError("start_date must not be after end_date")
        object.__setattr__(self, "start_date", start)
        object.__setattr__(self, "end_date", end)
        if self.workers < 1:
            raise ValueError("workers must be at least 1")
        if self.retries < 1:
            raise ValueError("retries must be at least 1")
        if self.backoff < 0:
            raise ValueError("backoff cannot be negative")
        if self.timeout <= 0 or self.process_timeout <= 0:
            raise ValueError("timeouts must be positive")
        if self.chunk_size < 1:
            raise ValueError("chunk_size must be at least 1")


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    path: Path
    sha256: str | None
    filesize: int
    ffprobe_checked: bool
    error: str | None = None


@dataclass(frozen=True)
class DownloadResult:
    item_id: str
    status: str
    path: Path | None = None
    backend: DownloadBackend | None = None
    sha256: str | None = None
    filesize: int | None = None
    error: str | None = None
    dry_run: bool = False


class DownloadError(RuntimeError):
    """A transfer failed after choosing a valid source/backend."""


class VerificationError(RuntimeError):
    """A downloaded file did not pass integrity/media verification."""


def select_backend(url: str) -> DownloadBackend:
    """Choose ffmpeg for HLS, direct HTTP for media URLs, otherwise yt-dlp.

    Provider URLs and ordinary web pages intentionally go to yt-dlp rather than
    relying on brittle provider-specific URL parsing here.
    """

    if not url or not str(url).strip():
        raise ValueError("A non-empty media URL is required")
    value = str(url).strip()
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError(f"Unsupported media URL scheme: {parsed.scheme or '(none)'}")
    if _HLS_RE.search(value):
        return DownloadBackend.FFMPEG_HLS
    if Path(urllib.parse.unquote(parsed.path)).suffix.lower() in _MEDIA_EXTENSIONS:
        return DownloadBackend.DIRECT_HTTP
    return DownloadBackend.YT_DLP


# Alternate descriptive name retained for callers that prefer it.
select_download_backend = select_backend


def _fallback_safe_filename(value: str) -> str:
    value = value.strip().replace(os.sep, "-")
    if os.altsep:
        value = value.replace(os.altsep, "-")
    value = _SAFE_RE.sub("-", value).strip(" .-_")
    return value[:120] or "unknown"


def _safe_component(value: Any, *, max_length: int = 80) -> str:
    text = "unknown" if value is None else str(value)
    if _project_safe_filename is not None:
        try:
            safe = str(
                _project_safe_filename(text, max_length=max_length)
            ).strip(" .")
            if safe and safe not in {".", ".."}:
                # Components must remain components even if the project helper is
                # designed to sanitize complete filenames.
                safe = safe.replace("/", "-").replace("\\", "-")
                return safe[:max_length]
        except (TypeError, ValueError):
            pass
    return _fallback_safe_filename(text)[:max_length]


def _record_dict(record: Any) -> dict[str, Any]:
    if isinstance(record, Mapping):
        return dict(record)
    if is_dataclass(record) and not isinstance(record, type):
        return asdict(record)
    try:
        return dict(vars(record))
    except TypeError:
        return {}


def _value(record: Any, *names: str, default: Any = None) -> Any:
    if isinstance(record, Mapping):
        for name in names:
            if name in record and record[name] is not None:
                return record[name]
    for name in names:
        try:
            value = getattr(record, name)
        except (AttributeError, KeyError):
            continue
        if value is not None:
            return value
    return default


def _item_id(record: Any) -> str:
    """Return the provider item ID used in the deterministic filename."""

    value = _value(record, "item_id", "platform_item_id", "id", "sermon_id", "external_id")
    if value is None:
        raise ValueError("Sermon record has no item id")
    return str(value)


def _database_id(record: Any) -> str:
    """Return the catalog's canonical key used by ArchiveDB methods."""

    value = _value(record, "sermon_id", "id", "item_id", "platform_item_id")
    if value is None:
        raise ValueError("Sermon record has no database id")
    return str(value)


def _record_date(record: Any) -> date:
    raw = _value(
        record,
        "date",
        "sermon_date",
        "published_date",
        "published_at",
        "publication_date",
    )
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    if raw is None:
        raise ValueError(f"Sermon {_item_id(record)} has no publication date")
    text = str(raw).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid publication date for {_item_id(record)}: {raw!r}")


def _iter_sources(record: Any) -> Iterable[tuple[str, str, bool]]:
    """Yield ``(kind, url, public)`` from optional structured source fields."""

    sources = _value(record, "media_sources", "sources", default=())
    if isinstance(sources, str):
        try:
            sources = json.loads(sources)
        except json.JSONDecodeError:
            sources = ()
    if isinstance(sources, Mapping):
        sources = [sources]
    if not isinstance(sources, Iterable):
        return
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        url = source.get("url") or source.get("src")
        if not url:
            continue
        kind = str(source.get("kind") or source.get("type") or "video").lower()
        public = bool(source.get("public", source.get("is_public", True)))
        yield kind, str(url), public


def _video_source(record: Any) -> str | None:
    public = _value(record, "video_public", "is_video_public", "public_video", default=True)
    if public is False or str(public).lower() in {"false", "0", "private"}:
        return None
    direct = _value(
        record,
        "video_url",
        "video_source_url",
        "video_source",
        "watch_url",
    )
    if direct:
        return str(direct)
    for kind, url, is_public in _iter_sources(record):
        if is_public and ("video" in kind or kind in {"hls", "youtube", "vimeo"}):
            return url
    media_url = _value(record, "media_url")
    media_kind = str(_value(record, "media_type", "media_kind", default="")).lower()
    media_suffix = Path(
        urllib.parse.unquote(urllib.parse.urlparse(str(media_url or "")).path)
    ).suffix.lower()
    if media_url and "audio" not in media_kind and media_suffix not in _AUDIO_EXTENSIONS:
        return str(media_url)
    return None


def _audio_source(record: Any) -> str | None:
    direct = _value(record, "audio_url", "audio_source_url", "audio_source", "mp3_url")
    if direct:
        return str(direct)
    for kind, url, is_public in _iter_sources(record):
        if is_public and "audio" in kind:
            return url
    media_url = _value(record, "media_url")
    media_kind = str(_value(record, "media_type", "media_kind", default="")).lower()
    media_suffix = Path(
        urllib.parse.unquote(urllib.parse.urlparse(str(media_url or "")).path)
    ).suffix.lower()
    if media_url and ("audio" in media_kind or media_suffix in _AUDIO_EXTENSIONS):
        return str(media_url)
    return None


def _extension_for(url: str, backend: DownloadBackend, *, audio: bool) -> str:
    suffix = Path(urllib.parse.unquote(urllib.parse.urlparse(url).path)).suffix.lower()
    if suffix in _MEDIA_EXTENSIONS and backend is DownloadBackend.DIRECT_HTTP:
        return suffix
    if audio:
        return ".m4a"
    return ".mp4"


def destination_for(
    record: Any,
    root: str | Path,
    source_url: str,
    backend: DownloadBackend | None = None,
    *,
    audio: bool = False,
) -> Path:
    """Build the required chronological archive destination for a record."""

    backend = backend or select_backend(source_url)
    sermon_date = _record_date(record)
    speaker = _safe_component(
        _value(record, "speaker", "speaker_name", default="unknown"), max_length=40
    )
    series = _safe_component(
        _value(record, "series", "series_name", default="unknown"), max_length=45
    )
    title = _safe_component(
        _value(record, "title", "sermon_title", default="untitled"), max_length=75
    )
    item = _safe_component(_item_id(record), max_length=60)
    extension = _extension_for(source_url, backend, audio=audio)
    filename = f"{sermon_date.isoformat()}__{speaker}__{series}__{title}__{item}{extension}"
    return Path(root) / "downloads" / str(sermon_date.year) / filename


def part_path_for(destination: str | Path) -> Path:
    destination = Path(destination)
    return destination.with_name(destination.name + ".part")


def _response_status(response: Any) -> int:
    status = getattr(response, "status", None)
    if status is None and hasattr(response, "getcode"):
        status = response.getcode()
    return int(status or 200)


def _header(response: Any, name: str) -> str | None:
    headers = getattr(response, "headers", {})
    if hasattr(headers, "get"):
        value = headers.get(name)
        return str(value) if value is not None else None
    return None


def _open_response(opener: Any, request: urllib.request.Request, timeout: float) -> Any:
    if hasattr(opener, "open"):
        return opener.open(request, timeout=timeout)
    return opener(request, timeout=timeout)


def _copy_response(response: Any, output: Any, chunk_size: int) -> None:
    while True:
        chunk = response.read(chunk_size)
        if not chunk:
            break
        output.write(chunk)


def download_direct_http(
    url: str,
    destination: str | Path,
    *,
    opener: Any = urllib.request.urlopen,
    timeout: float = 60.0,
    chunk_size: int = 1024 * 1024,
) -> Path:
    """Download an ordinary media URL, safely resuming a valid partial file.

    If a server ignores ``Range`` and replies with 200, the partial is restarted
    using that complete response body.  A malformed/mismatched 206 is discarded
    and followed by a clean request so bytes can never be silently duplicated.
    """

    destination = Path(destination)
    partial = part_path_for(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {destination}")

    offset = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": "CalvaryArchive/1.0"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    request = urllib.request.Request(url, headers=headers)

    try:
        response = _open_response(opener, request, timeout)
    except urllib.error.HTTPError as exc:
        if exc.code == 416 and offset:
            content_range = exc.headers.get("Content-Range", "") if exc.headers else ""
            total = content_range.partition("/")[2]
            if total.isdigit() and int(total) == offset:
                os.replace(partial, destination)
                return destination
        raise DownloadError(f"HTTP download failed for {url}: {exc}") from exc

    with response:
        status = _response_status(response)
        content_range = _header(response, "Content-Range") or ""
        valid_resume = status == 206 and content_range.lower().startswith(f"bytes {offset}-")
        total_text = content_range.partition("/")[2]
        expected_total = int(total_text) if total_text.isdigit() else None
        content_length = _header(response, "Content-Length")
        if expected_total is None and status == 200 and content_length and content_length.isdigit():
            expected_total = int(content_length)
        if offset and valid_resume:
            mode = "ab"
        elif status in {200, 206}:
            # 200 means Range was ignored.  A 206 with an unexpected range is
            # unsafe too; consume neither as an append.
            if status == 206 and offset:
                response.close()
                # Preserve the valid old partial until a complete replacement has
                # been fetched and validated.
                restart = partial.with_name(partial.name + ".restart")
                restart.unlink(missing_ok=True)
                clean_request = urllib.request.Request(
                    url, headers={"User-Agent": "CalvaryArchive/1.0"}
                )
                try:
                    clean_response = _open_response(opener, clean_request, timeout)
                    with clean_response:
                        clean_status = _response_status(clean_response)
                        if clean_status != 200:
                            raise DownloadError(
                                f"Clean HTTP restart must return 200, got {clean_status} for {url}"
                            )
                        with restart.open("wb") as output:
                            _copy_response(clean_response, output, chunk_size)
                        clean_range = (
                            _header(clean_response, "Content-Range") or ""
                        ).partition("/")[2]
                        clean_length = _header(clean_response, "Content-Length")
                        expected_clean = (
                            int(clean_range)
                            if clean_range.isdigit()
                            else int(clean_length)
                            if clean_length and clean_length.isdigit()
                            else None
                        )
                    if expected_clean is not None and restart.stat().st_size != expected_clean:
                        raise DownloadError(
                            f"Incomplete HTTP response for {url}: expected {expected_clean} bytes, "
                            f"got {restart.stat().st_size}"
                        )
                    os.replace(restart, destination)
                    partial.unlink(missing_ok=True)
                    return destination
                except BaseException:
                    restart.unlink(missing_ok=True)
                    raise
            mode = "wb"
        else:
            raise DownloadError(f"Unexpected HTTP status {status} for {url}")

        with partial.open(mode) as output:
            _copy_response(response, output, chunk_size)

    actual_size = partial.stat().st_size
    if expected_total is not None and actual_size != expected_total:
        raise DownloadError(
            f"Incomplete HTTP response for {url}: expected {expected_total} bytes, "
            f"got {actual_size}"
        )
    os.replace(partial, destination)
    return destination


# Backward-friendly alias for direct callers.
direct_http_download = download_direct_http


def download_with_ytdlp(
    url: str,
    destination: str | Path,
    *,
    binary: str = "yt-dlp",
    audio: bool = False,
    runner: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
    timeout: float | None = None,
) -> Path:
    """Use yt-dlp's native ``.part`` continuation without overwriting output."""

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {destination}")
    command = [
        binary,
        "--continue",
        "--no-overwrites",
        "--no-playlist",
        "--output",
        str(destination),
    ]
    if audio:
        command.extend(["--format", "bestaudio/best"])
    else:
        command.extend(
            ["--format", "bestvideo*+bestaudio/best", "--merge-output-format", "mp4"]
        )
    command.append(url)
    completed = runner(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "unknown yt-dlp error").strip()
        raise DownloadError(f"yt-dlp failed: {detail}")
    if not destination.is_file():
        raise DownloadError(f"yt-dlp completed without creating {destination}")
    return destination


def _ffmpeg_muxer(destination: Path) -> str:
    return {
        ".mp4": "mp4",
        ".m4v": "mp4",
        ".mov": "mov",
        ".m4a": "ipod",
        ".mp3": "mp3",
        ".webm": "webm",
        ".mkv": "matroska",
    }.get(destination.suffix.lower(), "mp4")


def download_hls(
    url: str,
    destination: str | Path,
    *,
    binary: str = "ffmpeg",
    runner: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
    timeout: float | None = None,
) -> Path:
    """Download HLS to a fresh task-level partial file with ffmpeg."""

    destination = Path(destination)
    partial = part_path_for(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {destination}")
    # ffmpeg cannot reliably resume segmented HLS muxing; every attempt starts
    # this task's partial output from zero.
    partial.unlink(missing_ok=True)
    command = [
        binary,
        "-nostdin",
        "-v",
        "error",
        "-y",
        "-i",
        url,
        "-map",
        "0:v?",
        "-map",
        "0:a?",
        "-c",
        "copy",
        "-f",
        _ffmpeg_muxer(destination),
        str(partial),
    ]
    completed = runner(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "unknown ffmpeg error").strip()
        partial.unlink(missing_ok=True)
        raise DownloadError(f"ffmpeg HLS download failed: {detail}")
    if not partial.is_file() or partial.stat().st_size == 0:
        partial.unlink(missing_ok=True)
        raise DownloadError("ffmpeg completed without a non-empty media file")
    os.replace(partial, destination)
    return destination


ffmpeg_hls_download = download_hls


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        while True:
            chunk = source.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(
    path: str | Path,
    *,
    expected_sha256: str | None = None,
    expected_filesize: int | str | None = None,
    use_ffprobe: bool = True,
    ffprobe_binary: str = "ffprobe",
    runner: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
) -> VerificationResult:
    """Hash and validate a media file, invoking ffprobe when it is available."""

    media_path = Path(path)
    if not media_path.is_file():
        return VerificationResult(False, media_path, None, 0, False, "file is missing")
    size = media_path.stat().st_size
    if size <= 0:
        return VerificationResult(False, media_path, None, size, False, "file is empty")
    digest = sha256_file(media_path)
    if expected_filesize is not None and expected_filesize != "":
        try:
            wanted_size = int(expected_filesize)
        except (TypeError, ValueError):
            return VerificationResult(
                False, media_path, digest, size, False, "stored filesize is invalid"
            )
        if wanted_size != size:
            return VerificationResult(
                False,
                media_path,
                digest,
                size,
                False,
                f"filesize mismatch: expected {wanted_size}, got {size}",
            )
    if expected_sha256 and digest.lower() != str(expected_sha256).lower():
        return VerificationResult(
            False,
            media_path,
            digest,
            size,
            False,
            f"SHA-256 mismatch: expected {expected_sha256}, got {digest}",
        )

    probe = shutil.which(ffprobe_binary) if use_ffprobe else None
    if use_ffprobe and not probe:
        return VerificationResult(
            False,
            media_path,
            digest,
            size,
            False,
            f"required ffprobe executable not found: {ffprobe_binary}",
        )
    if probe:
        completed = runner(
            [
                probe,
                "-v",
                "error",
                "-show_entries",
                "format=duration,format_name:stream=codec_type",
                "-of",
                "json",
                str(media_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "ffprobe rejected file").strip()
            return VerificationResult(False, media_path, digest, size, True, detail)
        try:
            probe_data = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            return VerificationResult(
                False, media_path, digest, size, True, "ffprobe returned invalid JSON"
            )
        media_format = probe_data.get("format")
        if not isinstance(media_format, Mapping):
            return VerificationResult(
                False, media_path, digest, size, True, "ffprobe found no media format"
            )
        streams = probe_data.get("streams")
        stream_types = {
            str(stream.get("codec_type"))
            for stream in streams or []
            if isinstance(stream, Mapping)
        }
        if not stream_types.intersection({"audio", "video"}):
            return VerificationResult(
                False, media_path, digest, size, True, "ffprobe found no audio or video stream"
            )
        try:
            duration_value = media_format.get("duration")
            duration = float(str(duration_value)) if duration_value is not None else 0.0
        except (TypeError, ValueError):
            duration = 0.0
        if duration <= 0:
            return VerificationResult(
                False, media_path, digest, size, True, "ffprobe found no positive media duration"
            )
        return VerificationResult(True, media_path, digest, size, True)
    return VerificationResult(True, media_path, digest, size, False)


verify_media = verify_file


class _DatabaseAdapter:
    """Small compatibility layer around the ArchiveDB public methods."""

    def __init__(self, db: Any):
        self.db = db

    def list(self) -> list[Any]:
        method = getattr(self.db, "list", None) or getattr(self.db, "list_sermons", None)
        if method is None:
            raise TypeError("ArchiveDB must provide list()")
        try:
            return list(method())
        except TypeError:
            # A few DB wrappers make status explicit rather than optional.
            records: list[Any] = []
            seen: set[str] = set()
            for status in sorted(DOWNLOADABLE_STATUSES | RETRYABLE_STATUSES | FINAL_STATUSES):
                try:
                    batch = method(status=status)
                except TypeError:
                    batch = method(status)
                for record in batch:
                    item = _database_id(record)
                    if item not in seen:
                        records.append(record)
                        seen.add(item)
            return records

    def get(self, item_id: str) -> Any:
        method = getattr(self.db, "get", None) or getattr(self.db, "get_sermon", None)
        if method is None:
            raise TypeError("ArchiveDB must provide get()")
        return method(item_id)

    @staticmethod
    def _accepted_kwargs(method: Callable[..., Any], fields: Mapping[str, Any]) -> dict[str, Any]:
        try:
            signature = inspect.signature(method)
        except (TypeError, ValueError):
            return dict(fields)
        if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in signature.parameters.values()):
            return dict(fields)
        return {key: value for key, value in fields.items() if key in signature.parameters}

    def update(self, record: Any, **fields: Any) -> None:
        if not fields:
            return
        method = getattr(self.db, "update", None) or getattr(self.db, "update_sermon", None)
        if method is None:
            return
        item = _database_id(record)
        accepted = self._accepted_kwargs(method, fields)
        attempts: list[tuple[tuple[Any, ...], dict[str, Any]]] = [
            ((item,), accepted),
            ((item, dict(fields)), {}),
        ]
        # Mutable SermonRecord-style APIs commonly accept the record itself.
        mutable_record = record
        for key, value in fields.items():
            if not isinstance(mutable_record, Mapping) and hasattr(mutable_record, key):
                try:
                    setattr(mutable_record, key, value)
                except (AttributeError, TypeError):
                    pass
        attempts.append(((mutable_record,), {}))
        last_error: TypeError | None = None
        for args, kwargs in attempts:
            try:
                method(*args, **kwargs)
                return
            except TypeError as exc:
                last_error = exc
        if last_error:
            raise last_error

    def transition(
        self,
        record: Any,
        status: str,
        *,
        error: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        method = getattr(self.db, "transition", None) or getattr(
            self.db, "transition_status", None
        )
        if method is None:
            self.update(record, status=status, error=error, error_detail=error)
            return
        item = _database_id(record)
        payload = dict(details or {})
        if error:
            payload.setdefault("error", error)
        possible_kwargs = {
            "error": error,
            "error_detail": error,
            "details": payload or None,
            "event_details": payload or None,
        }
        accepted = self._accepted_kwargs(method, possible_kwargs)
        attempts = [
            ((item, status), accepted),
            ((item, status, error), {}),
            ((item, status), {}),
        ]
        last_error: TypeError | None = None
        for args, kwargs in attempts:
            try:
                method(*args, **kwargs)
                return
            except TypeError as exc:
                last_error = exc
        if last_error:
            raise last_error

    def mark_downloaded(
        self,
        record: Any,
        path: Path,
        verification: VerificationResult,
        *,
        audio: bool,
        backend: DownloadBackend | None,
    ) -> None:
        """Persist completed transfer facts and the downloaded/audio-only event."""

        method = getattr(self.db, "mark_downloaded", None)
        if method is not None:
            method(
                _database_id(record),
                path,
                sha256=verification.sha256,
                file_size_bytes=verification.filesize,
                filename=path.name,
                audio_only=audio,
            )
            return
        self.update(
            record,
            **_metadata_update_fields(
                record,
                path=path,
                verification=verification,
                backend=backend,
                audio=audio,
            ),
        )
        self.transition(
            record,
            "audio_only" if audio else "downloaded",
            details={"path": str(path), "media_kind": "audio" if audio else "video"},
        )

    def update_verification(
        self,
        record: Any,
        verification: VerificationResult,
        *,
        path: Path,
        audio: bool,
    ) -> None:
        """Persist integrity facts using ArchiveDB's atomic helper when present."""

        method = getattr(self.db, "update_verification", None)
        if method is not None:
            method(
                _database_id(record),
                valid=verification.valid,
                sha256=verification.sha256 if verification.valid else None,
                file_size_bytes=verification.filesize,
                local_path=path,
                error=verification.error,
            )
            return
        if verification.valid:
            self.update(
                record,
                **_metadata_update_fields(
                    record,
                    path=path,
                    verification=verification,
                    backend=None,
                    audio=audio,
                ),
            )
            if not audio:
                self.transition(
                    record,
                    "verified",
                    details={"path": str(path), "sha256": verification.sha256},
                )
        else:
            self.transition(
                record,
                "needs_review",
                error=f"Existing file failed verification: {verification.error}",
            )


def _metadata_update_fields(
    record: Any,
    *,
    path: Path,
    verification: VerificationResult,
    backend: DownloadBackend | None,
    audio: bool,
) -> dict[str, Any]:
    data = _record_dict(record)

    def name_for(candidates: Sequence[str], default: str) -> str:
        return next((name for name in candidates if name in data), default)

    fields: dict[str, Any] = {
        name_for(("download_path", "local_path", "media_path", "file_path"), "download_path"): str(path),
        name_for(("sha256", "checksum_sha256", "checksum"), "sha256"): verification.sha256,
        name_for(
            ("filesize", "file_size_bytes", "file_size", "size_bytes"), "filesize"
        ): verification.filesize,
        name_for(("media_kind", "downloaded_media_kind"), "media_kind"): "audio" if audio else "video",
    }
    if backend is not None:
        fields[name_for(("download_backend", "backend"), "download_backend")] = backend.value
    return fields


def _stored_path(record: Any, root: Path) -> Path | None:
    value = _value(
        record,
        "download_path",
        "local_path",
        "video_path",
        "audio_path",
        "media_path",
        "file_path",
    )
    if not value:
        return None
    path = Path(str(value))
    if not path.is_absolute():
        path = root / path
    return path


def _expected_checksum(record: Any) -> str | None:
    value = _value(record, "sha256", "checksum_sha256", "checksum")
    return str(value) if value else None


def _expected_filesize(record: Any) -> int | str | None:
    return _value(record, "filesize", "file_size_bytes", "file_size", "size_bytes")


class ArchiveDownloader:
    """Serial, resumable archive downloader with DB status/event transitions."""

    def __init__(
        self,
        db: Any,
        root: str | Path | None = None,
        *,
        config: DownloadConfig | None = None,
        opener: Any = urllib.request.urlopen,
        runner: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
        sleeper: Callable[[float], None] = time.sleep,
        **config_options: Any,
    ) -> None:
        if config is not None and config_options:
            raise ValueError("pass config or individual configuration options, not both")
        if config is None:
            if root is None:
                raise ValueError("root or config is required")
            config = DownloadConfig(root=Path(root), **config_options)
        self.config = config
        self.db = _DatabaseAdapter(db)
        self.opener = opener
        self.runner = runner
        self.sleeper = sleeper

    def _transition(
        self,
        record: Any,
        status: str,
        *,
        error: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self.db.transition(record, status, error=error, details=details)

    def _verify(self, path: Path, record: Any, *, compare_stored: bool) -> VerificationResult:
        return verify_file(
            path,
            expected_sha256=_expected_checksum(record) if compare_stored else None,
            expected_filesize=_expected_filesize(record) if compare_stored else None,
            use_ffprobe=self.config.use_ffprobe,
            ffprobe_binary=self.config.ffprobe_binary,
            runner=self.runner,
        )

    def _transfer(
        self,
        backend: DownloadBackend,
        source: str,
        destination: Path,
        *,
        audio: bool,
    ) -> None:
        if backend is DownloadBackend.DIRECT_HTTP:
            download_direct_http(
                source,
                destination,
                opener=self.opener,
                timeout=self.config.timeout,
                chunk_size=self.config.chunk_size,
            )
        elif backend is DownloadBackend.FFMPEG_HLS:
            download_hls(
                source,
                destination,
                binary=self.config.ffmpeg_binary,
                runner=self.runner,
                timeout=self.config.process_timeout,
            )
        else:
            download_with_ytdlp(
                source,
                destination,
                binary=self.config.yt_dlp_binary,
                audio=audio,
                runner=self.runner,
                timeout=self.config.process_timeout,
            )

    def _transfer_with_retries(
        self,
        record: Any,
        backend: DownloadBackend,
        source: str,
        destination: Path,
        *,
        audio: bool,
    ) -> None:
        last_error: Exception | None = None
        for attempt in range(1, self.config.retries + 1):
            self._transition(
                record,
                "downloading",
                details={"attempt": attempt, "backend": backend.value, "url": source},
            )
            try:
                self._transfer(backend, source, destination, audio=audio)
                return
            except (DownloadError, OSError, subprocess.SubprocessError) as exc:
                last_error = exc
                if backend is DownloadBackend.FFMPEG_HLS:
                    part_path_for(destination).unlink(missing_ok=True)
                if attempt < self.config.retries:
                    delay = self.config.backoff * (2 ** (attempt - 1))
                    if delay:
                        self.sleeper(delay)
        assert last_error is not None
        raise DownloadError(
            f"download failed after {self.config.retries} attempt(s): {last_error}"
        ) from last_error

    def _prepare_transfer_status(
        self,
        record: Any,
        status: str,
        *,
        backend: DownloadBackend | None,
        destination: Path,
    ) -> str:
        """Move a retryable record to queued without violating DB lifecycle edges."""

        if status == "discovered":
            self._transition(record, "metadata_complete", details={"reason": "media selected"})
            status = "metadata_complete"
        if status in {"metadata_complete", "audio_only", "failed", "needs_review"}:
            self._transition(
                record,
                "queued",
                details={
                    "backend": backend.value if backend else None,
                    "destination": str(destination),
                },
            )
            status = "queued"
        if status not in {"queued", "downloading"}:
            raise VerificationError(f"cannot start a download from status {status}")
        return status

    def _record_availability(
        self,
        record: Any,
        status: str,
        target: str,
        message: str,
    ) -> None:
        """Reach audio_only/no_media through legal ArchiveDB transitions."""

        if target == "audio_only":
            if status in {"discovered", "failed", "queued", "needs_review"}:
                self._transition(
                    record,
                    "metadata_complete",
                    details={"reason": "audio source without public video"},
                )
                status = "metadata_complete"
        else:
            if status == "queued":
                self._transition(record, "metadata_complete", details={"reason": "source removed"})
                status = "metadata_complete"
            elif status == "downloading":
                self._transition(record, "failed", error=message)
                status = "failed"
            elif status in {"downloaded", "audio_only"}:
                self._transition(record, "needs_review", error=message)
                status = "needs_review"
        self._transition(record, target, error=message)

    def download_record(self, record: Any, *, dry_run: bool = False) -> DownloadResult:
        item = _item_id(record)
        status = str(_value(record, "status", default="metadata_complete"))
        stored = _stored_path(record, self.config.root)

        if status == "verified":
            if stored and stored.is_file():
                return DownloadResult(item, "verified", path=stored)
            message = "record is verified but its media file is missing"
            if not dry_run:
                self._transition(record, "needs_review", error=message)
            return DownloadResult(item, "needs_review", path=stored, error=message, dry_run=dry_run)

        video = _video_source(record)
        audio_source = _audio_source(record)
        audio = False
        # A previously archived audio file must not satisfy a newly discovered
        # video source. Preserve audio_path, but download/verify the video target.
        if video and stored:
            stored_audio = _value(record, "audio_path")
            if stored_audio:
                audio_path = Path(str(stored_audio))
                if not audio_path.is_absolute():
                    audio_path = self.config.root / audio_path
                if audio_path == stored:
                    stored = None
        if not video:
            if not audio_source:
                message = "No public video or audio source is available"
                if not dry_run:
                    self._record_availability(record, status, "no_media", message)
                return DownloadResult(item, "no_media", error=message, dry_run=dry_run)
            if not self.config.download_audio:
                message = "No public video source; an audio source is available"
                if not dry_run:
                    self._record_availability(record, status, "audio_only", message)
                return DownloadResult(item, "audio_only", error=message, dry_run=dry_run)
            video = audio_source
            audio = True

        try:
            backend = select_backend(video)
            destination = destination_for(
                record, self.config.root, video, backend, audio=audio
            )
        except (TypeError, ValueError) as exc:
            message = str(exc)
            if not dry_run:
                self._transition(record, "needs_review", error=message)
            return DownloadResult(item, "needs_review", error=message, dry_run=dry_run)

        existing = stored if stored and stored.is_file() else destination
        if existing.is_file():
            verification = self._verify(existing, record, compare_stored=True)
            if verification.valid:
                if not dry_run:
                    if status not in {"downloaded", "audio_only", "verified"}:
                        prepared = self._prepare_transfer_status(
                            record,
                            status,
                            backend=backend,
                            destination=existing,
                        )
                        if prepared == "queued":
                            self._transition(
                                record,
                                "downloading",
                                details={"existing": True, "backend": backend.value},
                            )
                        self.db.mark_downloaded(
                            record,
                            existing,
                            verification,
                            audio=audio,
                            backend=backend,
                        )
                    self.db.update_verification(
                        record, verification, path=existing, audio=audio
                    )
                final_status = "audio_only" if audio or status == "audio_only" else "verified"
                return DownloadResult(
                    item,
                    final_status,
                    path=existing,
                    backend=backend,
                    sha256=verification.sha256,
                    filesize=verification.filesize,
                    dry_run=dry_run,
                )
            message = f"Existing file failed verification: {verification.error}"
            if not dry_run:
                self.db.update_verification(
                    record, verification, path=existing, audio=audio
                )
            return DownloadResult(
                item,
                "needs_review",
                path=existing,
                backend=backend,
                sha256=verification.sha256,
                filesize=verification.filesize,
                error=message,
                dry_run=dry_run,
            )

        if dry_run:
            return DownloadResult(
                item, "queued", path=destination, backend=backend, dry_run=True
            )

        if status == "downloaded":
            message = "record is downloaded but its media file is missing"
            self._transition(record, "needs_review", error=message)
            return DownloadResult(
                item,
                "needs_review",
                path=destination,
                backend=backend,
                error=message,
            )
        attempts = int(_value(record, "download_attempts", default=0) or 0)
        max_retries = int(_value(record, "max_retries", default=self.config.retries) or 0)
        if status == "failed" and attempts >= max_retries:
            message = f"retry limit reached ({attempts}/{max_retries})"
            return DownloadResult(
                item, "failed", path=destination, backend=backend, error=message
            )

        try:
            self._prepare_transfer_status(
                record, status, backend=backend, destination=destination
            )
            self._transfer_with_retries(
                record, backend, video, destination, audio=audio
            )
            verification = self._verify(destination, record, compare_stored=False)
            if not verification.valid:
                raise VerificationError(verification.error or "media verification failed")
            self.db.mark_downloaded(
                record,
                destination,
                verification,
                audio=audio,
                backend=backend,
            )
            self.db.update_verification(
                record, verification, path=destination, audio=audio
            )
            return DownloadResult(
                item,
                "audio_only" if audio else "verified",
                path=destination,
                backend=backend,
                sha256=verification.sha256,
                filesize=verification.filesize,
            )
        except (DownloadError, VerificationError, OSError) as exc:
            message = str(exc)
            self._transition(record, "failed", error=message)
            return DownloadResult(
                item, "failed", path=destination, backend=backend, error=message
            )

    def _matches_filters(
        self,
        record: Any,
        *,
        speaker: str | None,
        series: str | None,
        year: int | None,
        retry_failed: bool,
        only_failed: bool,
    ) -> bool:
        status = str(_value(record, "status", default="metadata_complete"))
        allowed = {"failed"} if only_failed else set(DOWNLOADABLE_STATUSES)
        if retry_failed and not only_failed:
            allowed |= RETRYABLE_STATUSES
        if status == "audio_only" and (
            _video_source(record) is not None
            or (
                self.config.download_audio
                and _stored_path(record, self.config.root) is None
            )
        ):
            allowed.add("audio_only")
        if status not in allowed:
            return False
        if status == "failed":
            attempts = int(_value(record, "download_attempts", default=0) or 0)
            retry_limit = int(_value(record, "max_retries", default=3) or 0)
            if attempts >= retry_limit:
                return False
        try:
            sermon_date = _record_date(record)
        except ValueError:
            return False
        if not (self.config.start_date <= sermon_date <= self.config.end_date):
            return False
        if speaker:
            actual = str(_value(record, "speaker", "speaker_name", default=""))
            if actual.casefold() != speaker.casefold():
                return False
        if series:
            actual = str(_value(record, "series", "series_name", default=""))
            if actual.casefold() != series.casefold():
                return False
        if year is not None and sermon_date.year != year:
            return False
        return True

    def run(
        self,
        *,
        dry_run: bool = False,
        limit: int | None = None,
        speaker: str | None = None,
        series: str | None = None,
        year: int | None = None,
        retry_failed: bool = False,
        only_failed: bool = False,
    ) -> list[DownloadResult]:
        if limit is not None and limit < 0:
            raise ValueError("limit cannot be negative")
        records = [
            record
            for record in self.db.list()
            if self._matches_filters(
                record,
                speaker=speaker,
                series=series,
                year=year,
                retry_failed=retry_failed,
                only_failed=only_failed,
            )
        ]

        def sort_key(record: Any) -> tuple[date, str]:
            try:
                item_date = _record_date(record)
            except ValueError:
                item_date = date.max
            return item_date, _item_id(record)

        records.sort(key=sort_key)
        if limit is not None:
            records = records[:limit]
        # Intentionally serial.  ``workers`` remains a low configurable contract,
        # and values above one can be honored by a bounded executor in the future.
        return [self.download_record(record, dry_run=dry_run) for record in records]

    def verify_existing(
        self,
        *,
        limit: int | None = None,
        speaker: str | None = None,
        series: str | None = None,
        year: int | None = None,
        dry_run: bool = False,
    ) -> list[VerificationResult]:
        records = self.db.list()
        selected: list[Any] = []
        for record in records:
            try:
                sermon_date = _record_date(record)
            except ValueError:
                continue
            if not (self.config.start_date <= sermon_date <= self.config.end_date):
                continue
            if speaker:
                actual = str(_value(record, "speaker", "speaker_name", default=""))
                if actual.casefold() != speaker.casefold():
                    continue
            if series:
                actual = str(_value(record, "series", "series_name", default=""))
                if actual.casefold() != series.casefold():
                    continue
            if year is not None and sermon_date.year != year:
                continue
            if _stored_path(record, self.config.root) is not None:
                selected.append(record)
        def existing_sort_key(record: Any) -> tuple[date, str]:
            try:
                item_date = _record_date(record)
            except ValueError:
                item_date = date.max
            return item_date, _item_id(record)

        selected.sort(key=existing_sort_key)
        if limit is not None:
            selected = selected[:limit]

        results: list[VerificationResult] = []
        for record in selected:
            path = _stored_path(record, self.config.root)
            assert path is not None
            verification = self._verify(path, record, compare_stored=True)
            results.append(verification)
            if dry_run:
                continue
            status = str(_value(record, "status", default="downloaded"))
            audio_path = _value(record, "audio_path")
            audio = status == "audio_only" or (
                audio_path is not None and Path(str(audio_path)).name == path.name
            )
            if verification.valid and status not in {"downloaded", "audio_only", "verified"}:
                if status == "no_media":
                    self._transition(record, "discovered", details={"reason": "local media found"})
                    status = "discovered"
                prepared = self._prepare_transfer_status(
                    record, status, backend=None, destination=path
                )
                if prepared == "queued":
                    self._transition(record, "downloading", details={"existing": True})
                self.db.mark_downloaded(
                    record,
                    path,
                    verification,
                    audio=audio,
                    backend=None,
                )
            self.db.update_verification(
                record, verification, path=path, audio=audio
            )
        return results


# Concise public aliases/function entry points.
Downloader = ArchiveDownloader


def download_archive(db: Any, root: str | Path, **kwargs: Any) -> list[DownloadResult]:
    run_keys = {
        "dry_run", "limit", "speaker", "series", "year", "retry_failed", "only_failed"
    }
    run_options = {key: kwargs.pop(key) for key in tuple(kwargs) if key in run_keys}
    config = DownloadConfig(root=Path(root), **kwargs)
    return ArchiveDownloader(db, config=config).run(**run_options)


def verify_existing_files(
    db: Any,
    root: str | Path,
    **kwargs: Any,
) -> list[VerificationResult]:
    verify_keys = {"dry_run", "limit", "speaker", "series", "year"}
    verify_options = {key: kwargs.pop(key) for key in tuple(kwargs) if key in verify_keys}
    config = DownloadConfig(root=Path(root), **kwargs)
    return ArchiveDownloader(db, config=config).verify_existing(**verify_options)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("download", "verify"), default="download")
    parser.add_argument("--db", required=True, help="Archive SQLite database path")
    parser.add_argument("--root", type=Path, required=True, help="Archive root directory")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--backoff", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--speaker")
    parser.add_argument("--series")
    parser.add_argument("--year", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--audio", action="store_true", help="Download audio when video is absent")
    parser.add_argument("--no-ffprobe", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        database_module = importlib.import_module(
            f"{__package__ or 'calvary_archive'}.database"
        )
        archive_db = getattr(database_module, "ArchiveDB")
    except (ImportError, AttributeError) as exc:  # pragma: no cover - install error.
        raise SystemExit(f"Unable to import ArchiveDB: {exc}") from exc

    db = archive_db(args.db)
    config = DownloadConfig(
        root=args.root,
        workers=args.workers,
        retries=args.retries,
        backoff=args.backoff,
        timeout=args.timeout,
        download_audio=args.audio,
        use_ffprobe=not args.no_ffprobe,
    )
    downloader = ArchiveDownloader(db, config=config)
    common = {
        "limit": args.limit,
        "speaker": args.speaker,
        "series": args.series,
        "year": args.year,
        "dry_run": args.dry_run,
    }
    if args.command == "verify":
        results: Sequence[Any] = downloader.verify_existing(**common)
        failed = sum(not result.valid for result in results)
    else:
        results = downloader.run(**common, retry_failed=args.retry_failed)
        failed = sum(result.status in {"failed", "needs_review"} for result in results)
    print(json.dumps([asdict(result) for result in results], default=str, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
