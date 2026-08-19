"""Tests for the transcription module (pure logic + stubbed engine)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from calvary_archive.database import ArchiveDB
from calvary_archive.models import SermonRecord
from calvary_archive.transcribe import (
    TranscriptionConfig,
    TranscriptionEngine,
    build_payload,
    render_txt,
    run_transcription,
    summarize,
    transcript_paths_for,
    transcripts_root,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _make_db(tmp_path: Path) -> ArchiveDB:
    db = ArchiveDB(tmp_path / "test.sqlite")
    db.initialize()
    return db


def _record(
    tmp_path: Path,
    db: ArchiveDB,
    *,
    sermon_id: str = "s1",
    year: int = 2006,
    date: str = "2006-05-14",
) -> SermonRecord:
    media = tmp_path / "downloads" / str(year) / f"{sermon_id}.mp3"
    media.parent.mkdir(parents=True, exist_ok=True)
    media.write_bytes(b"fake audio")
    record = SermonRecord(
        sermon_id=sermon_id,
        title=f"A Test Sermon {sermon_id}",
        speaker="Ken Ortize",
        sermon_date=date,
        series="Acts",
        local_media_path=str(media),
        sha256="abc123",
    )
    db.upsert_sermon(record)
    return db.require_sermon(sermon_id)


class StubEngine(TranscriptionEngine):
    """Engine stub: yields two fake segments without loading any model."""

    def __init__(self, config: TranscriptionConfig, fail_on: set[str] | None = None) -> None:
        super().__init__(config)
        self.fail_on = set(fail_on or ())
        self.calls: list[str] = []

    def probe_duration(self, path: Path) -> float:
        return 120.0

    @property
    def version(self) -> str:
        return "stub-1.0"

    def iter_segments(self, path: Path):
        self.calls.append(str(path))

        @dataclass
        class W:
            start: float
            end: float
            word: str
            probability: float

        @dataclass
        class S:
            id: int
            start: float
            end: float
            text: str
            avg_logprob: float
            no_speech_prob: float
            compression_ratio: float | None = None
            words: list = field(default_factory=list)

        segs = [
            S(0, 0.0, 5.0, " Grace and peace to you.", -0.2, 0.01, 1.4,
              [W(0.0, 0.5, " Grace", 0.99), W(0.5, 1.0, " and", 0.98)]),
            S(1, 5.0, 10.0, " Turn to Acts chapter two.", -0.3, 0.01, 1.3,
              [W(5.0, 5.6, " Turn", 0.97)]),
        ]
        if str(path) in self.fail_on:
            raise RuntimeError("stub failure")
        return iter(segs), {"language": "en", "language_probability": 1.0, "duration": 120.0}


# --------------------------------------------------------------------------- #
# Path mapping
# --------------------------------------------------------------------------- #
class TestTranscriptPaths:
    def test_paths_mirror_downloads_layout(self, tmp_path: Path):
        record = {
            "sermon_id": "x",
            "year": 2007,
            "local_media_path": "/archive/downloads/2007/2007-01-04__a__b__c.mp3",
        }
        j, t = transcript_paths_for(record, tmp_path)
        assert j == transcripts_root(tmp_path) / "2007" / "2007-01-04__a__b__c.json"
        assert t == transcripts_root(tmp_path) / "2007" / "2007-01-04__a__b__c.txt"

    def test_missing_media_raises(self, tmp_path: Path):
        with pytest.raises(ValueError):
            transcript_paths_for({"sermon_id": "x", "year": 2007}, tmp_path)


# --------------------------------------------------------------------------- #
# Payload + text rendering
# --------------------------------------------------------------------------- #
class TestPayloadAndText:
    def _payload(self, **overrides: Any) -> dict[str, Any]:
        base = dict(
            record={"sermon_id": "s1", "title": "T", "speaker": "Spk",
                    "sermon_date": "2006-05-14", "series": "Acts", "source_platform": "subsplash"},
            source_path=Path("/a/b/s1.mp3"),
            source_sha256="deadbeef",
            segments=[
                {"start": 0.0, "end": 5.0, "text": " Grace.", "avg_logprob": -0.2,
                 "no_speech_prob": 0.01, "words": [{"word": "Grace"}]},
                {"start": 5.0, "end": 10.0, "text": " Peace.", "avg_logprob": -0.4,
                 "no_speech_prob": 0.02, "words": [{"word": "Peace"}, {"word": "be"}]},
            ],
            info={"language": "en", "language_probability": 0.99},
            config=TranscriptionConfig(),
            engine_version="1.0.0",
            started_at="2026-08-19T00:00:00Z",
            completed_at="2026-08-19T00:01:00Z",
            duration_seconds=120.0,
            processing_seconds=12.0,
            warnings=[],
        )
        base.update(overrides)
        return build_payload(**base)

    def test_payload_provenance_fields(self):
        payload = self._payload()
        src = payload["source"]
        assert src["filename"] == "s1.mp3"
        assert src["sha256"] == "deadbeef"
        assert src["sermon_date"] == "2006-05-14"
        assert payload["transcription"]["model"] == "large-v3"
        assert payload["transcription"]["realtime_factor"] == 0.1
        assert payload["quality"]["word_count"] == 3
        assert payload["quality"]["mean_segment_avg_logprob"] == pytest.approx(-0.3)

    def test_txt_render_markers_and_header(self):
        text = render_txt(self._payload())
        assert "A Test Sermon" in text or "T" in text
        assert "[0:00] Grace." in text
        assert "[0:05] Peace." in text


# --------------------------------------------------------------------------- #
# Orchestration: resume/skip/fail semantics
# --------------------------------------------------------------------------- #
class TestRunTranscription:
    def test_transcribes_and_skips_on_rerun(self, tmp_path: Path):
        db = _make_db(tmp_path)
        record = _record(tmp_path, db)
        engine = StubEngine(TranscriptionConfig())
        results = run_transcription(tmp_path, db, engine, records=[record])
        assert results[0].status == "transcribed"
        j, t = transcript_paths_for(record, tmp_path)
        assert j.exists() and t.exists()
        payload = json.loads(j.read_text())
        assert payload["source"]["sha256"] == "abc123"
        assert db.get_transcript("s1")["status"] == "transcribed"

        results2 = run_transcription(tmp_path, db, engine, records=[record])
        assert results2[0].status == "skipped"
        assert results2[0].skipped_reason == "already transcribed"
        assert engine.calls.count(str(Path(record.local_media_path))) == 1  # not re-run

    def test_failure_recorded_and_retryable(self, tmp_path: Path):
        db = _make_db(tmp_path)
        record = _record(tmp_path, db, sermon_id="s2")
        engine = StubEngine(TranscriptionConfig(), fail_on={record.local_media_path})
        results = run_transcription(tmp_path, db, engine, records=[record])
        assert results[0].status == "failed"
        assert "stub failure" in results[0].error
        assert db.get_transcript("s2")["status"] == "failed"

        # without retry_failed: skipped
        engine2 = StubEngine(TranscriptionConfig())
        r2 = run_transcription(tmp_path, db, engine2, records=[record])
        assert r2[0].status == "skipped"
        assert "failed previously" in r2[0].skipped_reason

        # with retry_failed: succeeds
        r3 = run_transcription(tmp_path, db, engine2, records=[record], retry_failed=True)
        assert r3[0].status == "transcribed"

    def test_missing_media_skipped(self, tmp_path: Path):
        db = _make_db(tmp_path)
        record = _record(tmp_path, db, sermon_id="s3")
        Path(record.local_media_path).unlink()
        results = run_transcription(tmp_path, db, StubEngine(TranscriptionConfig()), records=[record])
        assert results[0].status == "skipped"
        assert "missing" in results[0].skipped_reason

    def test_dry_run_touches_nothing(self, tmp_path: Path):
        db = _make_db(tmp_path)
        record = _record(tmp_path, db, sermon_id="s4")
        engine = StubEngine(TranscriptionConfig())
        results = run_transcription(tmp_path, db, engine, records=[record], dry_run=True)
        assert results[0].status == "pending"
        assert engine.calls == []
        j, _ = transcript_paths_for(record, tmp_path)
        assert not j.exists()
        assert db.get_transcript("s4") is None

    def test_summarize_counts(self, tmp_path: Path):
        db = _make_db(tmp_path)
        r1 = _record(tmp_path, db, sermon_id="a")
        Path(_record(tmp_path, db, sermon_id="b", date="2006-05-21").local_media_path).unlink()
        engine = StubEngine(TranscriptionConfig())
        results = run_transcription(tmp_path, db, engine, records=[r1, db.require_sermon("b")])
        s = summarize(results)
        assert s["status_counts"] == {"transcribed": 1, "skipped": 1}
        assert s["audio_seconds_transcribed"] == 120.0


# --------------------------------------------------------------------------- #
# Database integration
# --------------------------------------------------------------------------- #
class TestTranscriptTable:
    def test_upsert_partial_then_complete(self, tmp_path: Path):
        db = _make_db(tmp_path)
        _record(tmp_path, db, sermon_id="z")
        db.upsert_transcript({"sermon_id": "z", "status": "pending"})
        assert db.get_transcript("z")["status"] == "pending"
        db.upsert_transcript({"sermon_id": "z", "status": "transcribed", "model": "large-v3"})
        row = db.get_transcript("z")
        assert row["status"] == "transcribed"
        assert row["model"] == "large-v3"
        assert db.transcript_status_counts() == {"transcribed": 1}

    def test_candidates_require_local_media(self, tmp_path: Path):
        db = _make_db(tmp_path)
        _record(tmp_path, db, sermon_id="with_media")
        no_media = SermonRecord(sermon_id="no_media", title="X", local_media_path=None)
        db.upsert_sermon(no_media)
        ids = [r.sermon_id for r in db.list_transcribe_candidates()]
        assert ids == ["with_media"]

    def test_invalid_status_rejected(self, tmp_path: Path):
        db = _make_db(tmp_path)
        _record(tmp_path, db, sermon_id="s")
        with pytest.raises(sqlite3.IntegrityError):
            db.upsert_transcript({"sermon_id": "s", "status": "bogus"})
