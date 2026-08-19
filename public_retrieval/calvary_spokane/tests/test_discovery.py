from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from calvary_archive.discovery import (  # noqa: E402
    date_in_range,
    extract_bible_book,
    extract_subsplash_identifiers,
    filter_items_by_date,
    hal_next_link,
    normalize_item,
    normalize_series,
    parse_collection,
    parse_shoebox_token,
    redact_shoebox_token,
)

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def value(record, name: str):
    if isinstance(record, dict):
        return record.get(name)
    return getattr(record, name, None)


def raw_metadata(record):
    return value(record, "raw_metadata") or value(record, "raw_json")


def test_identifier_and_token_parsing_from_links_iframes_and_scripts():
    html = """
    <a href="https://subsplash.com/+qq9m/lb/li/+ff8gwrs?embed">Archive</a>
    <iframe src="https://subsplash.com/+qq9m/embed/mi/*recent?audio"></iframe>
    <script>
      subsplashEmbed("+qq9m/lb/li/+w2yb2yp?embed&amp;branding", "https://subsplash.com/");
    </script>
    <script type="fastboot/shoebox" id="shoebox-tokens">
      {"apiToken":"public.header.signature","other":"preserved"}
    </script>
    """

    apps, lists = extract_subsplash_identifiers(html)

    assert apps == {"qq9m"}
    assert lists == {"ff8gwrs", "w2yb2yp"}
    assert parse_shoebox_token(html) == "public.header.signature"
    redacted = redact_shoebox_token(html)
    assert "public.header.signature" not in redacted
    assert '"apiToken":"[REDACTED]"' in redacted
    assert '"other":"preserved"' in redacted


def test_date_filtering_is_local_inclusive_and_keeps_missing_for_review():
    items = [
        {"id": "before", "date": "1996-12-31T23:59:59-08:00"},
        {"id": "start", "date": "1997-01-01T23:59:59-08:00"},
        {"id": "end", "date": "1997-12-31T00:00:00Z"},
        {"id": "after", "date": "1998-01-01T00:00:00Z"},
        {"id": "missing"},
    ]

    assert date_in_range(items[1], "1997-01-01", "1997-12-31")
    assert date_in_range(items[2], "1997-01-01", "1997-12-31")
    assert not date_in_range(items[0], "1997-01-01", "1997-12-31")
    assert not date_in_range(items[4], "1997-01-01", "1997-12-31")
    assert [item["id"] for item in filter_items_by_date(
        items, "1997-01-01", "1997-12-31"
    )] == ["start", "end", "missing"]
    assert [item["id"] for item in filter_items_by_date(
        items, "1997-01-01", "1997-12-31", include_missing=False
    )] == ["start", "end"]


def test_normalize_item_preserves_metadata_and_all_media_variants():
    item = load_fixture("subsplash_item.json")

    record = normalize_item(item)

    assert value(record, "platform_item_id") == item["id"]
    normalized_date = value(record, "date")
    if hasattr(normalized_date, "isoformat"):
        normalized_date = normalized_date.isoformat()
    assert normalized_date == "1997-04-06"
    assert value(record, "speaker") == "Ken Ortize"
    assert value(record, "title") == "A Promise Preserved"
    assert value(record, "description") == "An archived verse-by-verse study."
    assert value(record, "scripture") == "Gen.12.1-Gen.12.9"
    assert value(record, "source_url").endswith(item["id"])
    assert value(record, "canonical_url") == "https://subspla.sh/abc1234"
    assert value(record, "series") == "Genesis | Verse by Verse"
    assert extract_bible_book(value(record, "series"), [value(record, "scripture")]) == "Genesis"
    assert value(record, "thumbnail_url") == (
        "https://cdn.subsplash.com/images/APP123/_source/image-wide-1/image.png"
    )
    assert value(record, "audio_url").endswith("audio-source-1/audio.mp3")
    assert value(record, "video_url").endswith("video-output-1/video.mp4")
    assert value(record, "duration_seconds") == 3723
    assert value(record, "filename") == "04.06.97_KO.mp3"
    assert value(record, "status") == "metadata_complete"

    # Feed fields that have no first-class SermonRecord column remain untouched
    # in raw_metadata, including both native/external variants and HLS.
    raw = raw_metadata(record)
    assert raw == item
    assert raw["subtitle"] == "Genesis 12:1-9"
    assert raw["tags"] == ["speaker:Ken Ortize", "archive"]
    assert raw["scriptures"] == ["Gen.12.1-Gen.12.9"]
    assert raw["topic"] == "Faith"
    assert raw["service_type"] == "Sunday Morning"
    assert raw["external_audio_url"].endswith("external/audio.mp3")
    assert raw["external_video_url"].endswith("videos/12345")
    assert raw["external_m3u8_url"].endswith("videos/12345/master.m3u8")
    assert raw["_embedded"]["video"]["_embedded"]["playlists"][0]["_links"]["related"]["href"].endswith(
        "video-playlist-1/master.m3u8"
    )


def test_normalize_audio_only_video_only_no_media_and_missing_date():
    fixture = load_fixture("subsplash_item.json")

    audio_only = copy.deepcopy(fixture)
    audio_only["_embedded"].pop("video")
    audio_only.pop("external_video_url")
    audio_only.pop("external_m3u8_url")
    audio_record = normalize_item(audio_only)
    assert value(audio_record, "audio_url") is not None
    assert value(audio_record, "video_url") is None
    assert value(audio_record, "status") == "audio_only"
    assert raw_metadata(audio_record) == audio_only

    external_audio_only = copy.deepcopy(audio_only)
    external_audio_only["_embedded"].pop("audio")
    external_audio_only["external_audio_url"] = (
        "https://media.example.test/archive/K771.mp3?signature=keep"
    )
    external_record = normalize_item(external_audio_only)
    assert value(external_record, "original_media_filename") == "K771.mp3"
    assert value(external_record, "media_format") == "mp3"

    video_only = copy.deepcopy(fixture)
    video_only["_embedded"].pop("audio")
    video_only.pop("external_audio_url")
    video_record = normalize_item(video_only)
    assert value(video_record, "audio_url") is None
    assert value(video_record, "video_url").endswith("video-output-1/video.mp4")
    assert value(video_record, "filename") == "04.06.97_KO.mp4"

    no_media = copy.deepcopy(fixture)
    no_media["_embedded"].pop("audio")
    no_media["_embedded"].pop("video")
    for field in ("external_audio_url", "external_video_url", "external_m3u8_url"):
        no_media.pop(field)
    dated_no_media_record = normalize_item(no_media)
    assert value(dated_no_media_record, "audio_url") is None
    assert value(dated_no_media_record, "video_url") is None
    assert value(dated_no_media_record, "status") == "no_media"

    no_media.pop("date")
    no_media.pop("topic")
    no_media.pop("service_type")
    no_media["tags"].extend(["topic:Not Metadata", "service:Not Metadata"])
    missing_date_record = normalize_item(no_media)
    assert value(missing_date_record, "date") is None
    assert value(missing_date_record, "status") == "needs_review"
    assert raw_metadata(missing_date_record) == no_media
    assert "topic" not in raw_metadata(missing_date_record)
    assert "service_type" not in raw_metadata(missing_date_record)


def test_representative_hal_collection_and_series_normalization():
    payload = load_fixture("subsplash_collection.json")

    series = parse_collection(payload, "media_series")

    assert len(series) == 2
    assert payload["count"] == 2
    assert payload["total"] == 86
    assert series[0]["title"] == "Genesis | Verse by Verse"
    assert hal_next_link(payload) == (
        "https://core.subsplash.com/media/v1/media-series?"
        "filter[app_key]=APP123&page[number]=2&page[size]=2"
    )

    normalized = normalize_series(series[0])
    assert normalized["source_id"] == "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
    assert normalized["item_count"] == 31
    assert normalized["summary"] == "A historical study through Genesis."
    assert normalized["thumbnail_url"].endswith("series-image-1/image.png")
    assert normalized["raw_json"] == series[0]
