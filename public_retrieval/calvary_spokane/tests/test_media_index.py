from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from calvary_archive.database import ArchiveDB  # noqa: E402
from calvary_archive.media_index import (  # noqa: E402
    LegacyMediaIndexAudit,
    normalize_guest_media_candidate,
    normalized_media_url,
    parse_media_index,
    probe_date_evidence,
)


def test_parse_media_index_contains_links_and_preserves_listing_metadata() -> None:
    page = """
    <a href="?C=N;O=D">Name</a>
    <a href="/">Parent Directory</a>
    <a href="Series%20One/">Series One/</a> 2014-05-08 16:46 -
    <a href="K800.mp3">K800.mp3</a> 2014-05-08 16:47 12M
    <a href="notes.pdf">notes.pdf</a> 2014-05-08 16:48 1M
    <a href="https://external.example/K801.mp3">external</a>
    """

    entries = parse_media_index(
        page,
        index_url="https://media.example.test/root/",
        source_root="https://media.example.test/root/",
    )

    assert [entry["url"] for entry in entries] == [
        "https://media.example.test/root/K800.mp3",
        "https://media.example.test/root/Series%20One/",
    ]
    media = entries[0]
    assert media["listed_last_modified"] == "2014-05-08 16:47"
    assert media["listed_size"] == "12M"
    assert normalized_media_url(media["url"]) == "media.example.test/root/K800.mp3"


def test_probe_date_evidence_requires_explicit_dates() -> None:
    evidence = probe_date_evidence(
        {
            "filename": "https://media.example.test/K900.mp3",
            "tags": {
                "date": "2009-12-31",
                "title": "2009 Prophecy Update",
                "artist": "Ken Ortize",
            },
        }
    )

    assert evidence["full_dates"] == ["2009-12-31"]
    assert evidence["years"] == [2009]
    assert evidence["tags"]["artist"] == "Ken Ortize"


def test_probe_date_evidence_ignores_xmp_and_accepts_legacy_two_digit_title_date() -> None:
    evidence = probe_date_evidence(
        {
            "filename": "https://media.example.test/guest/GS1105.mp3",
            "tags": {
                "title": "GS1105-Judges-15-09-27-09",
                "date": "2009",
                "id3v2_priv.XMP": '<xmp:CreateDate="2006-03-27"/>',
            },
        }
    )

    assert evidence["full_dates"] == ["2009-09-27"]
    assert evidence["years"] == [2009]
    assert "id3v2_priv.xmp" not in evidence["trusted_date_tags"]


def _guest_asset(filename: str, title: str, *, artist: str | None = None) -> dict[str, object]:
    tags = {"title": title}
    if artist:
        tags["artist"] = artist
    return {
        "media_id": f"legacy-media:{filename.casefold()}",
        "media_url": f"https://media.example.test/C.Mp3/guest/{filename}",
        "parent_index_url": "https://media.example.test/C.Mp3/guest/",
        "relative_path": f"guest/{filename}",
        "filename": filename,
        "media_kind": "audio",
        "extension": "mp3",
        "ffprobe_metadata": {"duration": "2550.648", "tags": tags},
        "probe_error": None,
        "probed_at": "2026-08-19T00:00:00Z",
    }


def test_guest_candidate_promotes_service_date_but_preserves_conflict_for_review() -> None:
    exact = normalize_guest_media_candidate(
        _guest_asset("GS1105.mp3", "GS1105-Judges-15-09-27-09", artist="Bob Davis"),
        start_date=date(2004, 6, 1),
        end_date=date(2010, 8, 31),
    )
    assert exact is not None
    assert exact["tier"] == "confirmed_exact_date"
    assert exact["record"]["sermon_date"] == "2009-09-27"
    assert exact["record"]["speaker"] == "Bob Davis"
    assert exact["record"]["status"] == "audio_only"

    conflict = normalize_guest_media_candidate(
        _guest_asset("GS1123.mp3", "GS1123 9am-John4:1-26_2009-01-10"),
        start_date=date(2004, 6, 1),
        end_date=date(2010, 8, 31),
    )
    assert conflict is not None
    assert conflict["tier"] == "conflicting_exact_date"
    assert conflict["record"]["sermon_date"] is None
    assert conflict["record"]["status"] == "needs_review"


def test_guest_candidate_excludes_partial_month_after_cutoff() -> None:
    candidate = normalize_guest_media_candidate(
        _guest_asset("GS1149.mp3", "GS1149CoryKirkhamJohn18_12-27_2010-11"),
        start_date=date(2004, 6, 1),
        end_date=date(2010, 8, 31),
    )
    assert candidate is None


def test_recursive_audit_matches_inventory_without_probing_known_audio(tmp_path: Path) -> None:
    media_root = "https://media.example.test/root/"
    pages = {
        "/root/": """
            <a href="Series/">Series/</a> 2014-05-08 16:46 -
            <a href="https://external.example/nope/">external</a>
        """,
        "/root/Series/": """
            <a href="K800.mp3">K800.mp3</a> 2014-05-08 16:47 12M
            <a href="KSE999_09special.mp3">KSE999_09special.mp3</a> 2014-05-08 16:48 13M
        """,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        page = pages.get(request.url.path)
        if page is None:
            raise AssertionError(f"unexpected request: {request.url}")
        return httpx.Response(200, text=page, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    archive_root = tmp_path / "archive"
    with ArchiveDB(archive_root / "data" / "sermons.sqlite") as db:
        db.upsert_sermon(
            {
                "sermon_id": "known-k800",
                "platform": "test",
                "platform_item_id": "known-k800",
                "title": "Known sermon",
                "speaker": "Ken Ortize",
                "sermon_date": "2005-01-02",
                "audio_url": f"{media_root}Series/K800.mp3",
                "audio_source_url": f"{media_root}Series/K800.mp3",
                "has_audio": True,
                "status": "audio_only",
            }
        )
        with LegacyMediaIndexAudit(
            archive_root,
            db,
            media_roots=(media_root,),
            client=client,
            delay_range=(0, 0),
            sleep=lambda _: None,
        ) as audit:
            result = audit.run(no_ffprobe=True)

        assert result["tree_complete"] is True
        assert result["directories_seen"] == 2
        assert result["assets_seen"] == 2
        assert result["matched_inventory"] == 1
        assert result["probes_attempted"] == 0
        matches = [
            dict(row)
            for row in db.connect().execute(
                "SELECT classification, sermon_id FROM legacy_media_matches ORDER BY classification"
            )
        ]
        assert matches == [
            {"classification": "matched_inventory", "sermon_id": "known-k800"},
            {"classification": "unmatched_unprobed", "sermon_id": None},
        ]

        def no_network(request: httpx.Request) -> httpx.Response:
            raise AssertionError(f"reuse unexpectedly fetched {request.url}")

        reuse_client = httpx.Client(
            transport=httpx.MockTransport(no_network), follow_redirects=True
        )
        with LegacyMediaIndexAudit(
            archive_root,
            db,
            media_roots=(media_root,),
            client=reuse_client,
            delay_range=(0, 0),
            sleep=lambda _: None,
        ) as audit:
            reused = audit.run(no_ffprobe=True, reuse_run_id=result["run_id"])
        assert reused["reused_run"] == result["run_id"]
        assert reused["assets_seen"] == 2
