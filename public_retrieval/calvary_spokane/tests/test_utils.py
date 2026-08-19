from __future__ import annotations

import hashlib
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from calvary_archive.utils import (  # noqa: E402
    build_media_filename,
    canonicalize_url,
    final_path_from_part,
    is_date_in_range,
    parse_sermon_date,
    partial_path,
    safe_filename,
    sha256_file,
    slugify,
    utc_timestamp,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2024-02-03", date(2024, 2, 3)),
        ("2024-02-03T18:30:00Z", date(2024, 2, 3)),
        ("February 3, 2024", date(2024, 2, 3)),
        ("Feb 3rd, 2024", date(2024, 2, 3)),
        ("Saturday, February 3, 2024", date(2024, 2, 3)),
        ("02/03/2024", date(2024, 2, 3)),
        (date(2024, 2, 3), date(2024, 2, 3)),
        (None, None),
        ("", None),
        ("not a date", None),
    ],
)
def test_parse_sermon_date(raw: object, expected: date | None) -> None:
    assert parse_sermon_date(raw) == expected


def test_date_range_is_inclusive_and_open_ended() -> None:
    assert is_date_in_range("2024-05-01", "2024-05-01", "2024-05-31")
    assert is_date_in_range("2024-05-31", "2024-05-01", "2024-05-31")
    assert is_date_in_range("2024-05-15", start="2024-05-01")
    assert is_date_in_range("2024-05-15", end="2024-05-31")
    assert not is_date_in_range(None, "2024-05-01", "2024-05-31")
    assert not is_date_in_range("2024-05-15", "2024-06-01", "2024-05-01")


def test_slug_and_filename_are_safe_and_deterministic() -> None:
    assert slugify('  Faith / Hope: A "Test"?  ') == "faith-hope-a-test"
    first = build_media_filename(
        "video/42",
        'Faith / Hope: A "Test"?',
        "March 10, 2024",
        ".MP4.part",
        speaker="Ken Ortiz",
    )
    second = build_media_filename(
        "video/42",
        'Faith / Hope: A "Test"?',
        "March 10, 2024",
        ".mp4",
        speaker="Ken Ortiz",
    )
    assert first == second
    assert first.startswith("2024-03-10-faith-hope-a-test-ken-ortiz-")
    assert first.endswith(".mp4")
    assert re.fullmatch(r"[a-z0-9._-]+", first)
    assert "/" not in first and "\\" not in first


def test_part_filename_and_path_handling() -> None:
    filename = build_media_filename("abc123", "A Sermon", extension="mp3", partial=True)
    assert filename == "a-sermon-abc123.mp3.part"
    assert partial_path("archive/a.mp3") == Path("archive/a.mp3.part")
    assert partial_path("archive/a.mp3.part") == Path("archive/a.mp3.part")
    assert final_path_from_part("archive/a.mp3.part") == Path("archive/a.mp3")
    assert safe_filename("../../Bad: Name?.MP3.part") == "bad-name.mp3.part"


def test_utc_timestamp_is_utc_and_stable() -> None:
    moment = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert utc_timestamp(moment) == "2024-01-02T03:04:05Z"


def test_sha256_file_streams_content(tmp_path: Path) -> None:
    content = (b"calvary-spokane\x00" * 100_000) + b"end"
    path = tmp_path / "sermon.bin"
    path.write_bytes(content)
    assert sha256_file(path, chunk_size=97) == hashlib.sha256(content).hexdigest()


def test_canonical_url_removes_tracking_and_normalizes() -> None:
    assert canonicalize_url(
        "/sermons/faith/?b=2&utm_source=email&a=1#player",
        "HTTPS://Example.COM:443/archive/",
    ) == "https://example.com/sermons/faith?a=1&b=2"
    assert canonicalize_url(None) is None
