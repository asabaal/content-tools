from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from calvary_archive.database import (  # noqa: E402
    ArchiveDB,
    InvalidStatusTransition,
    RetryLimitExceeded,
)
from calvary_archive.models import SermonRecord  # noqa: E402


def metadata_record(sermon_id: str = "sermon-1", **changes: object) -> SermonRecord:
    values: dict[str, object] = {
        "sermon_id": sermon_id,
        "platform": "subsplash",
        "platform_item_id": sermon_id,
        "title": "Grace and Truth",
        "speaker": "Ken Ortiz",
        "sermon_date": "2024-03-10",
        "canonical_url": f"https://example.test/sermons/{sermon_id}/",
        "media_url": f"https://cdn.example.test/{sermon_id}.mp4",
        "status": "metadata_complete",
        "raw_metadata": {"source": "listing"},
    }
    values.update(changes)
    return SermonRecord.from_mapping(values)


def test_schema_initializes_and_context_closes(tmp_path: Path) -> None:
    db_path = tmp_path / "archive" / "data" / "sermons.sqlite"
    with ArchiveDB(db_path) as db:
        tables = {
            row[0]
            for row in db.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {
            "sermons",
            "sermon_sources",
            "series",
            "crawl_runs",
            "listing_audit",
            "status_events",
        } <= tables
        db.initialize()  # idempotent

    assert db_path.exists()
    assert db._connection is None


def test_duplicate_detection_uses_strong_fallbacks_conservatively(tmp_path: Path) -> None:
    with ArchiveDB(tmp_path / "sermons.sqlite") as db:
        original = db.upsert_sermon(metadata_record())
        assert (
            db.find_duplicate(canonical_url="https://example.test/sermons/sermon-1#player").sermon_id
            == original.sermon_id
        )

        canonical_duplicate = metadata_record(
            "different-id",
            platform="other-platform",
            platform_item_id="different-item",
            canonical_url="https://EXAMPLE.test/sermons/sermon-1?utm_source=email#player",
            media_url="https://cdn.example.test/different.mp4",
            description="updated description",
        )
        merged = db.upsert_sermon(canonical_duplicate)
        assert merged.sermon_id == original.sermon_id
        assert merged.description == "updated description"
        assert db.count_sermons() == 1

        # Two explicit IDs from the same provider remain distinct source records,
        # even when the provider duplicated all descriptive/media metadata.
        same_provider_copy = metadata_record(
            "provider-copy",
            canonical_url="https://example.test/provider-copy",
            media_url="https://cdn.example.test/sermon-1.mp4",
        )
        inserted_copy = db.upsert_sermon(same_provider_copy)
        assert inserted_copy.sermon_id == "provider-copy"
        assert db.count_sermons() == 2

        exact_metadata_duplicate = metadata_record(
            "third-id",
            platform="other-platform",
            canonical_url="https://example.test/other",
            media_url="https://cdn.example.test/other.mp4",
        )
        assert db.find_duplicate(exact_metadata_duplicate).sermon_id in {
            "sermon-1",
            "provider-copy",
        }

        # Missing speaker is not enough for a date/title fallback match.
        uncertain = metadata_record(
            "uncertain",
            platform="other-platform",
            title="Grace and Truth",
            speaker=None,
            canonical_url="https://example.test/uncertain",
            media_url="https://cdn.example.test/uncertain.mp4",
        )
        db.upsert_sermon(uncertain)
        assert db.count_sermons() == 3

        media_duplicate = metadata_record(
            "media-copy",
            platform="third-platform",
            title="Unrelated title",
            speaker="Another Speaker",
            sermon_date="2020-01-01",
            canonical_url="https://example.test/media-copy",
            media_url="https://cdn.example.test/uncertain.mp4",
        )
        assert db.find_duplicate(media_duplicate).sermon_id == "uncertain"


def test_source_evidence_upsert_preserves_multiple_source_provenance(tmp_path: Path) -> None:
    with ArchiveDB(tmp_path / "sermons.sqlite") as db:
        db.upsert_sermon(metadata_record())
        first = db.upsert_source_evidence(
            source_id="wayback:one",
            sermon_id="sermon-1",
            source_platform="calvary_legacy",
            platform_item_id="grace-and-truth",
            source_url="http://legacy.example.test/sermon/grace-and-truth",
            audio_url="http://media.example.test/grace.mp3?sig=preserve",
            audio_available=True,
            audio_status_code=200,
            raw_metadata={"capture": "20111006"},
        )
        assert first["audio_available"] == 1

        refreshed = db.upsert_source_evidence(
            source_id="wayback:one",
            sermon_id="sermon-1",
            source_platform="calvary_legacy",
            video_url="http://media.example.test/grace.m4v",
            video_available=False,
            video_status_code=404,
            raw_metadata={"video_checked": True},
        )
        assert refreshed["audio_url"] == "http://media.example.test/grace.mp3?sig=preserve"
        assert refreshed["video_available"] == 0
        assert refreshed["raw_metadata"] == {
            "capture": "20111006",
            "video_checked": True,
        }
        assert db.get_sermon("sermon-1").source_platform == "subsplash"


def test_authoritative_refresh_recovers_review_and_clears_stale_media(tmp_path: Path) -> None:
    with ArchiveDB(tmp_path / "sermons.sqlite") as db:
        db.upsert_sermon(
            metadata_record(
                sermon_date=None,
                status="needs_review",
                video_url="https://cdn.example.test/obsolete.mp4?token=keep-order",
                audio_url=None,
                media_url="https://cdn.example.test/obsolete.mp4?token=keep-order",
            )
        )
        refreshed = db.upsert_sermon(
            metadata_record(
                sermon_date="2008-05-04",
                status="audio_only",
                video_url=None,
                audio_url="https://cdn.example.test/current.mp3?sig=z&part=1",
                media_url="https://cdn.example.test/current.mp3?sig=z&part=1",
            )
        )

        assert refreshed.status == "audio_only"
        assert refreshed.sermon_date.isoformat() == "2008-05-04"
        assert refreshed.video_url is None
        assert not refreshed.has_video
        assert refreshed.audio_url == "https://cdn.example.test/current.mp3?sig=z&part=1"
        assert refreshed.has_audio
        assert refreshed.downloaded_at is None


def test_transfer_url_query_is_preserved_exactly(tmp_path: Path) -> None:
    signed = "https://cdn.example.test/media.mp3?source=archive&sig=b%2Ba&part=2"
    with ArchiveDB(tmp_path / "sermons.sqlite") as db:
        record = db.upsert_sermon(
            metadata_record(audio_url=signed, media_url=signed, video_url=None)
        )
        assert record.audio_url == signed
        assert record.media_url == signed


def test_metadata_upsert_preserves_download_facts(tmp_path: Path) -> None:
    downloaded = metadata_record(
        status="downloaded",
        local_path="media/sermon-1.mp4",
        video_path="media/sermon-1.mp4",
        filename="sermon-1.mp4",
        file_size_bytes=12345,
        sha256="a" * 64,
        download_attempts=2,
        downloaded_at="2024-03-11T01:02:03Z",
        last_error="an earlier transient error",
    )
    with ArchiveDB(tmp_path / "sermons.sqlite") as db:
        db.upsert_sermon(downloaded)
        refreshed = db.upsert_sermon(
            metadata_record(
                title="Grace and Truth (Corrected)",
                description="fresh metadata",
                local_path=None,
                file_size_bytes=None,
                sha256=None,
                download_attempts=0,
                last_error=None,
            )
        )

        assert refreshed.title == "Grace and Truth (Corrected)"
        assert refreshed.description == "fresh metadata"
        assert refreshed.status == "downloaded"
        assert refreshed.local_path == "media/sermon-1.mp4"
        assert refreshed.file_size_bytes == 12345
        assert refreshed.sha256 == "a" * 64
        assert refreshed.download_attempts == 2
        assert refreshed.downloaded_at == "2024-03-11T01:02:03Z"
        assert refreshed.last_error == "an earlier transient error"
        assert refreshed.raw_metadata == {"source": "listing"}


def test_attach_public_media_can_replace_proven_bad_remote_assignment(tmp_path: Path) -> None:
    old_url = "https://media.example.test/K983.mp3"
    corrected_url = "https://media.example.test/K984.mp3"
    with ArchiveDB(tmp_path / "sermons.sqlite") as db:
        db.upsert_sermon(
            metadata_record(
                video_url=None,
                audio_url=old_url,
                audio_source_url=old_url,
                media_url=old_url,
                original_media_filename="K983.mp3",
                status="audio_only",
            )
        )
        corrected = db.attach_public_media(
            "sermon-1",
            media_kind="audio",
            media_url=corrected_url,
            media_format="mp3",
            replace_existing=True,
            evidence={"reason": "exact source match"},
        )

        assert corrected.audio_url == corrected_url
        assert corrected.audio_source_url == corrected_url
        assert corrected.media_url == corrected_url
        assert corrected.original_media_filename == "K984.mp3"
        assert corrected.raw_metadata["legacy_media_recoveries"][-1]["reason"] == "exact source match"


def test_retry_transitions_are_legal_and_bounded(tmp_path: Path) -> None:
    with ArchiveDB(tmp_path / "sermons.sqlite") as db:
        db.upsert_sermon(metadata_record(max_retries=2))
        db.queue_sermon("sermon-1")
        db.start_download("sermon-1")
        failed = db.mark_failed("sermon-1", "timeout")
        assert failed.status == "failed"
        assert failed.download_attempts == 1
        assert db.can_retry("sermon-1")

        assert db.queue_retry("sermon-1")
        assert db.get_sermon("sermon-1").status == "queued"
        db.start_download("sermon-1")
        second_failure = db.mark_failed("sermon-1", "connection reset")
        assert second_failure.download_attempts == 2
        assert not db.queue_retry("sermon-1")
        with pytest.raises(RetryLimitExceeded):
            db.queue_retry("sermon-1", strict=True)

        events = db.list_status_events("sermon-1")
        assert [event["to_status"] for event in events] == [
            "metadata_complete",
            "queued",
            "downloading",
            "failed",
            "queued",
            "downloading",
            "failed",
        ]


def test_illegal_transition_is_rejected(tmp_path: Path) -> None:
    with ArchiveDB(tmp_path / "sermons.sqlite") as db:
        db.upsert_sermon(metadata_record(status="discovered"))
        with pytest.raises(InvalidStatusTransition):
            db.transition_status("sermon-1", "downloaded")
        assert db.get_sermon("sermon-1").status == "discovered"


def test_filtering_and_counts_use_inclusive_dates(tmp_path: Path) -> None:
    with ArchiveDB(tmp_path / "sermons.sqlite") as db:
        db.upsert_sermon(metadata_record("one", sermon_date="2024-01-01"))
        db.upsert_sermon(metadata_record("two", sermon_date="2024-01-31"))
        db.upsert_sermon(metadata_record("three", sermon_date="2024-02-01"))

        january = db.list_sermons(start_date="2024-01-01", end_date="2024-01-31")
        assert [record.sermon_id for record in january] == ["one", "two"]
        assert db.count_sermons(status="metadata_complete") == 3
        assert db.counts_by_status()["verified"] == 0


def test_download_checksum_and_verification_update(tmp_path: Path) -> None:
    content = b"verified sermon content\n" * 4096
    media_path = tmp_path / "sermon.mp4"
    media_path.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()

    with ArchiveDB(tmp_path / "sermons.sqlite") as db:
        db.upsert_sermon(metadata_record())
        db.queue_sermon("sermon-1")
        db.start_download("sermon-1")
        downloaded = db.mark_downloaded("sermon-1", media_path, sha256=expected)
        assert downloaded.status == "downloaded"
        assert downloaded.file_size_bytes == len(content)

        assert db.verify_file("sermon-1")
        verified = db.get_sermon("sermon-1")
        assert verified.status == "verified"
        assert verified.sha256 == expected
        assert verified.verified_at is not None


def test_checksum_mismatch_moves_download_to_review(tmp_path: Path) -> None:
    media_path = tmp_path / "sermon.mp3"
    media_path.write_bytes(b"actual")

    with ArchiveDB(tmp_path / "sermons.sqlite") as db:
        db.upsert_sermon(metadata_record())
        db.queue_sermon("sermon-1")
        db.start_download("sermon-1")
        db.mark_downloaded("sermon-1", media_path, sha256="0" * 64, audio_only=True)
        assert not db.verify_file("sermon-1")
        review = db.get_sermon("sermon-1")
        assert review.status == "needs_review"
        assert "SHA-256 mismatch" in review.last_error
