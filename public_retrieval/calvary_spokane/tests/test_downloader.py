from __future__ import annotations

import hashlib
import io
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from calvary_archive.database import ArchiveDB  # noqa: E402
from calvary_archive.downloader import (  # noqa: E402
    ArchiveDownloader,
    DownloadBackend,
    DownloadConfig,
    DownloadError,
    download_direct_http,
    select_backend,
    verify_file,
)
from calvary_archive.models import SermonRecord  # noqa: E402


class FakeResponse(io.BytesIO):
    def __init__(self, body: bytes, status: int, headers: dict[str, str] | None = None):
        super().__init__(body)
        self.status = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
        return False


class FakeDB:
    def __init__(self, records):
        self.records = {str(record["item_id"]): record for record in records}
        self.events: list[tuple[str, str, str | None, dict | None]] = []

    def list(self):
        return list(self.records.values())

    def get(self, item_id):
        return self.records[str(item_id)]

    def update(self, item_id, **fields):
        self.records[str(item_id)].update(fields)

    def transition(self, item_id, status, error=None, details=None):
        record = self.records[str(item_id)]
        record["status"] = status
        record["error"] = error
        self.events.append((str(item_id), status, error, details))


def test_backend_selection_uses_hls_direct_media_and_ytdlp_for_pages():
    assert select_backend("https://cdn.example.org/live/master.m3u8?token=x") is DownloadBackend.FFMPEG_HLS
    assert select_backend("https://cdn.example.org/sermons/message.mp4?download=1") is DownloadBackend.DIRECT_HTTP
    assert select_backend("https://www.youtube.com/watch?v=abc") is DownloadBackend.YT_DLP
    assert select_backend("https://church.example.org/sermons/hope") is DownloadBackend.YT_DLP


@pytest.mark.parametrize("server_honors_range", [True, False])
def test_direct_http_resume_and_safe_restart_when_range_is_ignored(
    tmp_path: Path, server_honors_range: bool
):
    destination = tmp_path / "message.mp4"
    partial = tmp_path / "message.mp4.part"
    partial.write_bytes(b"abc")
    requests: list[urllib.request.Request] = []

    def opener(request, timeout):
        requests.append(request)
        assert timeout == 12
        requested_range = request.get_header("Range")
        if requested_range:
            assert requested_range == "bytes=3-"
            if server_honors_range:
                return FakeResponse(b"def", 206, {"Content-Range": "bytes 3-5/6"})
            return FakeResponse(b"abcdef", 200)
        return FakeResponse(b"abcdef", 200)

    download_direct_http(
        "https://cdn.example.org/message.mp4",
        destination,
        opener=opener,
        timeout=12,
        chunk_size=2,
    )

    assert destination.read_bytes() == b"abcdef"
    assert not partial.exists()
    assert len(requests) == 1


def test_audio_only_and_no_media_status_outcomes_without_downloads(tmp_path: Path):
    audio = {
        "item_id": "audio-1",
        "date": "2024-01-01",
        "title": "Audio only",
        "speaker": "Pastor",
        "series": "Series",
        "audio_url": "https://cdn.example.org/audio.mp3",
        "status": "metadata_complete",
    }
    missing = {
        "item_id": "none-1",
        "date": "2024-01-02",
        "title": "No media",
        "speaker": "Pastor",
        "series": "Series",
        "status": "metadata_complete",
    }
    db = FakeDB([audio, missing])
    downloader = ArchiveDownloader(
        db,
        config=DownloadConfig(
                    root=tmp_path,
                    start_date=date(2020, 1, 1),
                    end_date=date(2025, 12, 31),
                    download_audio=False,
                    use_ffprobe=False,
                ),
        opener=lambda *_args, **_kwargs: pytest.fail("network should not be used"),
    )

    results = downloader.run()

    assert [result.status for result in results] == ["audio_only", "no_media"]
    assert audio["status"] == "audio_only"
    assert missing["status"] == "no_media"
    assert [event[1] for event in db.events] == ["audio_only", "no_media"]
    assert not (tmp_path / "downloads").exists()


def test_mismatched_range_failure_preserves_existing_partial(tmp_path: Path):
    destination = tmp_path / "message.mp4"
    partial = tmp_path / "message.mp4.part"
    partial.write_bytes(b"abc")
    calls = 0

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            return FakeResponse(b"wrong", 206, {"Content-Range": "bytes 1-5/6"})
        raise urllib.error.URLError("clean restart failed")

    with pytest.raises(urllib.error.URLError):
        download_direct_http(
            "https://cdn.example.org/message.mp4",
            destination,
            opener=opener,
        )

    assert partial.read_bytes() == b"abc"
    assert not destination.exists()
    assert not (tmp_path / "message.mp4.part.restart").exists()


def test_clean_restart_rejects_partial_response_and_keeps_old_partial(tmp_path: Path):
    destination = tmp_path / "message.mp4"
    partial = tmp_path / "message.mp4.part"
    partial.write_bytes(b"abc")
    calls = 0

    def opener(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            return FakeResponse(b"wrong", 206, {"Content-Range": "bytes 1-5/6"})
        return FakeResponse(b"abcdef", 206, {"Content-Range": "bytes 0-5/6"})

    with pytest.raises(DownloadError, match="Clean HTTP restart must return 200"):
        download_direct_http(
            "https://cdn.example.org/message.mp4",
            destination,
            opener=opener,
        )

    assert partial.read_bytes() == b"abc"
    assert not destination.exists()


def test_audio_availability_can_be_downloaded_later(tmp_path: Path):
    audio = {
        "item_id": "audio-later",
        "date": "2008-01-01",
        "title": "Audio later",
        "speaker": "Pastor",
        "series": "Series",
        "audio_url": "https://cdn.example.org/audio.mp3",
        "status": "metadata_complete",
    }
    db = FakeDB([audio])
    metadata_pass = ArchiveDownloader(
        db,
        config=DownloadConfig(root=tmp_path, download_audio=False, use_ffprobe=False),
        opener=lambda *_args, **_kwargs: pytest.fail("metadata pass must not download"),
    )
    assert metadata_pass.run()[0].status == "audio_only"
    assert "download_path" not in audio

    payload = b"public audio bytes"

    def opener(request, timeout):
        return FakeResponse(payload, 200, {"Content-Length": str(len(payload))})

    audio_pass = ArchiveDownloader(
        db,
        config=DownloadConfig(root=tmp_path, download_audio=True, use_ffprobe=False),
        opener=opener,
    )
    result = audio_pass.run()[0]
    assert result.status == "audio_only"
    assert result.path is not None and result.path.read_bytes() == payload
    assert audio["download_path"] == str(result.path)


def test_downloaded_audio_can_upgrade_to_newly_available_video(tmp_path: Path):
    audio_payload = b"archived audio"
    video_payload = b"new public video"

    def opener(request, timeout):
        payload = video_payload if request.full_url.endswith("video.mp4") else audio_payload
        return FakeResponse(payload, 200, {"Content-Length": str(len(payload))})

    with ArchiveDB(tmp_path / "archive.sqlite") as db:
        db.upsert_sermon(
            SermonRecord(
                sermon_id="upgrade-1",
                item_id="upgrade-1",
                platform="subsplash",
                title="Upgrade",
                speaker="Pastor",
                series="Series",
                sermon_date=date(2008, 1, 1),
                audio_url="https://cdn.example.org/audio.mp3",
                status="audio_only",
            )
        )
        audio_downloader = ArchiveDownloader(
            db,
            config=DownloadConfig(root=tmp_path, download_audio=True, use_ffprobe=False),
            opener=opener,
        )
        audio_result = audio_downloader.run()[0]
        assert audio_result.path is not None

        refreshed = SermonRecord(
            sermon_id="upgrade-1",
            item_id="upgrade-1",
            platform="subsplash",
            title="Upgrade",
            speaker="Pastor",
            series="Series",
            sermon_date=date(2008, 1, 1),
            audio_url="https://cdn.example.org/audio.mp3",
            video_url="https://cdn.example.org/video.mp4",
            status="metadata_complete",
        )
        db.upsert_sermon(refreshed)
        video_result = ArchiveDownloader(
            db,
            config=DownloadConfig(root=tmp_path, use_ffprobe=False),
            opener=opener,
        ).run()[0]
        persisted = db.require_sermon("upgrade-1")

    assert video_result.status == "verified"
    assert video_result.path is not None and video_result.path.suffix == ".mp4"
    assert video_result.path.read_bytes() == video_payload
    assert persisted.audio_path == str(audio_result.path)
    assert persisted.video_path == str(video_result.path)


def test_required_ffprobe_missing_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    media = tmp_path / "message.mp3"
    media.write_bytes(b"not independently validated")
    monkeypatch.setattr("calvary_archive.downloader.shutil.which", lambda _binary: None)

    result = verify_file(media, use_ffprobe=True)

    assert not result.valid
    assert "ffprobe executable not found" in (result.error or "")


def test_checksum_and_filesize_verification(tmp_path: Path):
    media = tmp_path / "message.mp4"
    payload = b"locally generated test media bytes"
    media.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    good = verify_file(
        media,
        expected_sha256=digest,
        expected_filesize=len(payload),
        use_ffprobe=False,
    )
    assert good.valid
    assert good.sha256 == digest
    assert good.filesize == len(payload)
    assert not good.ffprobe_checked

    bad = verify_file(media, expected_sha256="0" * 64, use_ffprobe=False)
    assert not bad.valid
    assert "SHA-256 mismatch" in (bad.error or "")


def test_verify_existing_updates_verified_and_needs_review(tmp_path: Path):
    good_path = tmp_path / "good.mp4"
    bad_path = tmp_path / "bad.mp4"
    good_path.write_bytes(b"good")
    bad_path.write_bytes(b"changed")
    good_digest = hashlib.sha256(b"good").hexdigest()
    expected_bad_digest = hashlib.sha256(b"original").hexdigest()
    records = [
        {
            "item_id": "1",
            "date": "2023-01-01",
            "download_path": str(good_path),
            "sha256": good_digest,
            "filesize": 4,
            "status": "downloaded",
        },
        {
            "item_id": "2",
            "date": "2023-01-02",
            "download_path": str(bad_path),
            "sha256": expected_bad_digest,
            "status": "downloaded",
        },
    ]
    db = FakeDB(records)
    downloader = ArchiveDownloader(
        db,
                config=DownloadConfig(
                    root=tmp_path,
                    start_date=date(2020, 1, 1),
                    end_date=date(2025, 12, 31),
                    use_ffprobe=False,
                )
    )

    results = downloader.verify_existing()

    assert [result.valid for result in results] == [True, False]
    assert db.records["1"]["status"] == "verified"
    assert db.records["1"]["sha256"] == good_digest
    assert db.records["2"]["status"] == "needs_review"
    assert "SHA-256 mismatch" in (db.records["2"]["error"] or "")


def test_archive_db_integration_uses_canonical_id_and_persists_download_facts(
    tmp_path: Path,
):
    payload = b"fake local video content"

    def opener(request, timeout):
        assert request.full_url == "https://cdn.example.org/provider-42.mp4"
        return FakeResponse(payload, 200, {"Content-Length": str(len(payload))})

    with ArchiveDB(tmp_path / "archive.sqlite") as db:
        db.upsert_sermon(
            SermonRecord(
                sermon_id="catalog-1",
                item_id="provider-42",
                title="A Title",
                speaker="Pastor Name",
                series="Series Name",
                sermon_date=date(2024, 3, 4),
                video_url="https://cdn.example.org/provider-42.mp4",
                status="metadata_complete",
            )
        )
        downloader = ArchiveDownloader(
            db,
            config=DownloadConfig(
                root=tmp_path,
                start_date=date(2020, 1, 1),
                end_date=date(2025, 12, 31),
                retries=1,
                backoff=0,
                use_ffprobe=False,
            ),
            opener=opener,
        )

        result = downloader.run()[0]
        persisted = db.require_sermon("catalog-1")
        event_statuses = [
            event["to_status"] for event in db.list_status_events("catalog-1")
        ]

    assert result.status == "verified"
    assert result.path is not None
    assert result.path.name == (
        "2024-03-04__pastor-name__series-name__a-title__provider-42.mp4"
    )
    assert result.path.read_bytes() == payload
    assert persisted.status == "verified"
    assert persisted.local_path == str(result.path)
    assert persisted.video_path == str(result.path)
    assert persisted.file_size_bytes == len(payload)
    assert persisted.sha256 == hashlib.sha256(payload).hexdigest()
    assert event_statuses[-4:] == ["queued", "downloading", "downloaded", "verified"]
