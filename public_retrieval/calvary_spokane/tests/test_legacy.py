from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from calvary_archive.database import ArchiveDB  # noqa: E402
from calvary_archive.legacy import (  # noqa: E402
    LEGACY_PROPHECY_INDEX,
    LegacyArchiveDiscovery,
    normalize_speaker,
    parse_legacy_listing_page,
    parse_prophecy_index,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_legacy_listing_preserves_metadata_and_scopes_media() -> None:
    records = parse_legacy_listing_page(
        (FIXTURES / "legacy_listing.html").read_text(encoding="utf-8"),
        capture_timestamp="20111006040511",
        listing_url="http://calvaryspokane.com/sermon/archive/?start=280",
    )

    assert len(records) == 2
    watch, wedding = records
    assert watch["title"] == "Watch and Pray"
    assert watch["sermon_date"] == "2008-05-29"
    assert watch["scripture_reference"] == "Matthew 26:36–46"
    assert watch["video_urls"] == []
    assert watch["audio_urls"] == [
        "http://media.calvaryspokane.com/C.Mp3/TeachUsToPray/KT1749.mp3"
    ]

    assert wedding["speaker"] == "Ken Ortize"
    assert wedding["series"] == "Profiles from the Gospel of Grace"
    assert wedding["video_urls"] == [
        "http://media.calvaryspokane.com/C.Video/ProfilesfromGospelofGrace/KT1815.m4v"
    ]
    assert wedding["notes_urls"] == [
        "http://media.calvaryspokane.com/C.Notes/Profiles/KT1815.pdf"
    ]
    assert wedding["archived_source_url"].startswith(
        "https://web.archive.org/web/20111006040511id_/"
    )


def test_prophecy_index_discovers_explicit_nye_files_only() -> None:
    page = """
    <a href="KSE281_09NYEa.mp3">part a</a>
    <a href="KSE282_09NYEb.mp3">part b</a>
    <a href="KSE283_09NYEc.mp3">part c</a>
    <a href="KSE296.mp3">not explicitly dated</a>
    <a href="Prophecy%202015/">directory</a>
    """

    records = parse_prophecy_index(page)
    assert [record["sermon_date"] for record in records] == ["2009-12-31"] * 3
    assert [record["legacy_id"] for record in records] == [
        "KSE281_09NYEa",
        "KSE282_09NYEb",
        "KSE283_09NYEc",
    ]
    assert all(record["listing_url"] == LEGACY_PROPHECY_INDEX for record in records)
    assert normalize_speaker("Ken Orize") == "Ken Ortize"


def test_cached_legacy_import_keeps_unavailable_video_as_provenance(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    record = {
        "legacy_id": "wedding-in-cana",
        "title": "Wedding in Cana",
        "speaker": "Ken Ortize",
        "sermon_date": "2010-08-26",
        "series": "Profiles from the Gospel of Grace",
        "scripture_reference": "John 2:1–11",
        "source_url": "http://calvaryspokane.com/sermon/view/wedding-in-cana",
        "archived_source_url": "https://web.archive.org/web/201110/id_/http://calvaryspokane.com/sermon/view/wedding-in-cana",
        "listing_url": "http://calvaryspokane.com/sermon/archive/?start=120",
        "archived_listing_url": "https://web.archive.org/web/201110/id_/http://calvaryspokane.com/sermon/archive/?start=120",
        "series_url": "http://calvaryspokane.com/sermon/series/profiles",
        "audio_urls": ["https://media.example.test/KT1815.mp3"],
        "video_urls": ["https://media.example.test/KT1815.m4v"],
        "notes_urls": [],
        "source_kind": "wayback_2011_listing",
    }
    (cache / "legacy-records-target.json").write_text(json.dumps([record]), encoding="utf-8")
    (cache / "legacy-audio-availability.json").write_text(
        json.dumps(
            {
                "results": [
                    {
                        "url": "https://media.example.test/KT1815.mp3",
                        "available": True,
                        "status_code": 200,
                        "checked_at": "2026-08-18T00:00:00Z",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL(LEGACY_PROPHECY_INDEX):
            return httpx.Response(200, text="<html><body></body></html>", request=request)
        if request.method == "HEAD" and request.url.path.endswith(".m4v"):
            return httpx.Response(404, request=request)
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    root = tmp_path / "archive"
    with ArchiveDB(root / "data" / "sermons.sqlite") as db:
        with LegacyArchiveDiscovery(
            root,
            db,
            cache_dir=cache,
            client=client,
            delay_range=(0, 0),
            sleep=lambda _: None,
        ) as discovery:
            result = discovery.run(start_date="2010-08-26", end_date="2010-08-26")

        assert result["records_added"] == 1
        sermon = db.list_sermons()[0]
        assert sermon.has_audio
        assert not sermon.has_video
        assert sermon.status == "audio_only"
        assert sermon.audio_source_url == "https://media.example.test/KT1815.mp3"
        assert sermon.video_source_url is None

        sources = db.list_source_evidence(sermon.sermon_id)
        assert len(sources) == 1
        assert sources[0]["video_url"] == "https://media.example.test/KT1815.m4v"
        assert sources[0]["video_available"] == 0
        assert sources[0]["video_status_code"] == 404
