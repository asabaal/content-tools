"""Sermon audio transcription.

Transcribes locally archived sermon audio into derivative transcript artifacts
(JSON + readable text) stored alongside the rest of the archive, with full
provenance back to the source audio. Source files are only ever opened
read-only; transcripts are additive artifacts.

Configuration used for the canonical run is recorded per transcript and in the
processing report so results stay auditable.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from .database import ArchiveDB
from .models import SermonRecord

TRANSCRIPT_STATUS_VALUES = (
    "pending",
    "transcribing",
    "transcribed",
    "failed",
    "skipped",
)

DEFAULT_MODEL = "large-v3"
DEFAULT_DEVICE = "cuda"
DEFAULT_COMPUTE_TYPE = "float16"
DEFAULT_BATCH_SIZE = 16
DEFAULT_BEAM_SIZE = 5


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class TranscriptionConfig:
    """Settings for a transcription run (recorded with every transcript)."""

    model: str = DEFAULT_MODEL
    device: str = DEFAULT_DEVICE
    compute_type: str = DEFAULT_COMPUTE_TYPE
    batch_size: int = DEFAULT_BATCH_SIZE
    beam_size: int = DEFAULT_BEAM_SIZE
    word_timestamps: bool = True
    vad_filter: bool = True
    language: str = "en"
    use_batched_pipeline: bool = True

    def settings_summary(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "device": self.device,
            "compute_type": self.compute_type,
            "batch_size": self.batch_size,
            "beam_size": self.beam_size,
            "word_timestamps": self.word_timestamps,
            "vad_filter": self.vad_filter,
            "language": self.language,
            "batched_pipeline": self.use_batched_pipeline,
        }


@dataclass
class TranscriptResult:
    """Outcome of transcribing one file."""

    sermon_id: str
    status: str
    json_path: Path | None = None
    txt_path: Path | None = None
    duration_seconds: float | None = None
    processing_seconds: float | None = None
    segments: int = 0
    words: int = 0
    skipped_reason: str | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
    quality: dict[str, Any] = field(default_factory=dict)


def transcripts_root(root: Path) -> Path:
    return root / "transcripts"


def transcript_paths_for(record: Mapping[str, Any] | SermonRecord, root: Path) -> tuple[Path, Path]:
    """Map a sermon with local media to its (json, txt) transcript paths.

    Mirrors the downloads/ layout: transcripts/<year>/<audio-stem>.{json,txt}.
    """

    def value(key: str, default: Any = None) -> Any:
        if isinstance(record, SermonRecord):
            return getattr(record, key, default)
        return record.get(key, default)

    local = value("local_media_path") or value("local_path")
    if not local:
        raise ValueError(f"sermon {value('sermon_id')} has no local media path")
    local_path = Path(str(local))
    year_dir = str(value("year") or local_path.parent.name or "unknown")
    stem = local_path.stem
    base = transcripts_root(root) / year_dir
    return base / f"{stem}.json", base / f"{stem}.txt"


def _format_ts(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:d}:{secs:02d}"


def _json_scalar(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def build_payload(
    *,
    record: Mapping[str, Any] | SermonRecord,
    source_path: Path,
    source_sha256: str | None,
    segments: Sequence[Mapping[str, Any]],
    info: Mapping[str, Any],
    config: TranscriptionConfig,
    engine_version: str,
    started_at: str,
    completed_at: str,
    duration_seconds: float,
    processing_seconds: float,
    warnings: Sequence[str],
) -> dict[str, Any]:
    """Assemble the machine-readable transcript payload."""

    def value(key: str, default: Any = None) -> Any:
        if isinstance(record, SermonRecord):
            return getattr(record, key, default)
        return record.get(key, default)

    probs = [s.get("avg_logprob") for s in segments if s.get("avg_logprob") is not None]
    no_speech = [s for s in segments if s.get("no_speech_prob", 0.0) > 0.5]
    quality = {
        "language": info.get("language"),
        "language_probability": info.get("language_probability"),
        "duration_seconds": duration_seconds,
        "segment_count": len(segments),
        "word_count": sum(len(s.get("words") or []) for s in segments),
        "mean_segment_avg_logprob": (
            round(sum(probs) / len(probs), 4) if probs else None
        ),
        "segments_high_no_speech_prob": len(no_speech),
        "min_segment_avg_logprob": round(min(probs), 4) if probs else None,
    }
    return {
        "sermon_id": value("sermon_id"),
        "source": {
            "filename": source_path.name,
            "path": str(source_path),
            "sha256": source_sha256,
            "title": value("title"),
            "speaker": value("speaker"),
            "sermon_date": _json_scalar(value("sermon_date")),
            "series": value("series"),
            "source_platform": value("source_platform"),
        },
        "transcription": {
            "engine": "faster-whisper",
            "engine_version": engine_version,
            **config.settings_summary(),
            "started_at": started_at,
            "completed_at": completed_at,
            "processing_seconds": round(processing_seconds, 2),
            "realtime_factor": (
                round(processing_seconds / duration_seconds, 4)
                if duration_seconds
                else None
            ),
            "warnings": list(warnings),
        },
        "quality": quality,
        "segments": [dict(s) for s in segments],
    }


def render_txt(payload: Mapping[str, Any]) -> str:
    """Render the readable plain-text transcript with [mm:ss] markers."""

    source = payload.get("source", {})
    lines = [
        f"# {source.get('title') or 'Untitled sermon'}",
        "",
        f"Speaker: {source.get('speaker') or 'unknown'}"
        + (f"  |  Date: {source.get('sermon_date')}" if source.get("sermon_date") else ""),
        f"Series: {source.get('series') or '-'}  |  Source: {source.get('filename')}",
    ]
    tr = payload.get("transcription", {})
    lines += [
        f"Transcribed by faster-whisper {tr.get('model')} "
        f"({tr.get('engine_version')}) on {tr.get('completed_at')}",
        "",
    ]
    for segment in payload.get("segments", []):
        marker = _format_ts(segment.get("start", 0.0))
        lines.append(f"[{marker}] {str(segment.get('text', '')).strip()}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(path.suffix + ".part")
    part.write_text(text, encoding="utf-8")
    part.replace(path)


class TranscriptionEngine:
    """Lazy wrapper around faster-whisper.

    The heavy model is loaded on first use so the module can be imported (and
    unit-tested) without the transcription stack installed.
    """

    def __init__(self, config: TranscriptionConfig) -> None:
        self.config = config
        self._model: Any = None
        self._pipeline: Any = None

    @property
    def version(self) -> str:
        try:
            import faster_whisper

            return str(getattr(faster_whisper, "__version__", "unknown"))
        except Exception:
            return "unavailable"

    def _load(self) -> Any:
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.config.model,
                device=self.config.device,
                compute_type=self.config.compute_type,
            )
        return self._model

    def _load_pipeline(self) -> Any:
        if self._pipeline is None:
            model = self._load()
            if self.config.use_batched_pipeline and self.config.device == "cuda":
                from faster_whisper import BatchedInferencePipeline

                self._pipeline = BatchedInferencePipeline(model=model)
            else:
                self._pipeline = model
        return self._pipeline

    def probe_duration(self, path: Path) -> float:
        import subprocess

        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())

    def iter_segments(self, path: Path) -> tuple[Iterator[Any], Mapping[str, Any]]:
        pipeline = self._load_pipeline()
        kwargs: dict[str, Any] = {
            "language": self.config.language,
            "beam_size": self.config.beam_size,
            "word_timestamps": self.config.word_timestamps,
            "vad_filter": self.config.vad_filter,
        }
        if self._pipeline_is_batched:
            kwargs["batch_size"] = self.config.batch_size
        segments, info = pipeline.transcribe(str(path), **kwargs)
        return segments, {
            "language": getattr(info, "language", None),
            "language_probability": getattr(info, "language_probability", None),
            "duration": getattr(info, "duration", None),
        }

    @property
    def _pipeline_is_batched(self) -> bool:
        return self._pipeline is not None and self._pipeline.__class__.__name__ == "BatchedInferencePipeline"

    def segments_to_dicts(self, segments: Iterable[Any]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for seg in segments:
            words = [
                {
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "word": w.word,
                    "probability": round(w.probability, 4),
                }
                for w in (getattr(seg, "words", None) or [])
            ]
            out.append(
                {
                    "id": seg.id,
                    "start": round(seg.start, 3),
                    "end": round(seg.end, 3),
                    "text": seg.text,
                    "avg_logprob": round(seg.avg_logprob, 4) if seg.avg_logprob is not None else None,
                    "no_speech_prob": round(seg.no_speech_prob, 4) if seg.no_speech_prob is not None else None,
                    "compression_ratio": getattr(seg, "compression_ratio", None),
                    "words": words,
                }
            )
        return out


def run_transcription(
    root: Path,
    db: ArchiveDB,
    engine: TranscriptionEngine,
    *,
    records: Sequence[SermonRecord],
    dry_run: bool = False,
    force: bool = False,
    retry_failed: bool = False,
) -> list[TranscriptResult]:
    """Transcribe a selection of sermons with resume/skip semantics.

    Skip rules (in order):
    - no local media file on disk            -> skipped ("no local media")
    - transcript already transcribed + files exist, and not force -> skipped ("already transcribed")
    - previous failure and not retry_failed  -> skipped ("failed previously")
    """

    results: list[TranscriptResult] = []
    existing = db.transcript_status_map()

    for record in records:
        result = TranscriptResult(sermon_id=record.sermon_id, status="skipped")
        local = record.local_media_path or record.local_path
        if not local:
            result.skipped_reason = "no local media path"
            db.upsert_transcript(
                {
                    "sermon_id": record.sermon_id,
                    "status": "skipped",
                    "error": None,
                    "notes": "no local media path",
                }
            )
            results.append(result)
            continue
        source_path = Path(str(local))
        if not source_path.exists():
            result.skipped_reason = "local media file missing"
            db.upsert_transcript(
                {
                    "sermon_id": record.sermon_id,
                    "status": "skipped",
                    "error": f"local media file missing: {source_path}",
                }
            )
            results.append(result)
            continue

        try:
            json_path, txt_path = transcript_paths_for(record, root)
        except ValueError as exc:
            result.skipped_reason = str(exc)
            results.append(result)
            continue

        prior = existing.get(record.sermon_id)
        if (
            not force
            and prior is not None
            and prior.get("status") == "transcribed"
            and json_path.exists()
            and txt_path.exists()
        ):
            result.skipped_reason = "already transcribed"
            result.json_path = json_path
            result.txt_path = txt_path
            results.append(result)
            continue
        if (
            not retry_failed
            and not force
            and prior is not None
            and prior.get("status") == "failed"
        ):
            result.skipped_reason = "failed previously (use --retry-failed)"
            results.append(result)
            continue

        if dry_run:
            result.status = "pending"
            result.skipped_reason = None
            result.json_path = json_path
            result.txt_path = txt_path
            results.append(result)
            continue

        started_at = _utc_now()
        t0 = time.monotonic()
        db.upsert_transcript(
            {"sermon_id": record.sermon_id, "status": "transcribing", "started_at": started_at}
        )
        try:
            duration = engine.probe_duration(source_path)
            segment_iter, info = engine.iter_segments(source_path)
            segments = engine.segments_to_dicts(segment_iter)
            processing = time.monotonic() - t0
            completed_at = _utc_now()
            warnings: list[str] = []
            probs = [s["avg_logprob"] for s in segments if s["avg_logprob"] is not None]
            if probs and (sum(probs) / len(probs)) < -0.9:
                warnings.append(
                    "mean segment avg_logprob below -0.9; audio quality may be poor"
                )
            payload = build_payload(
                record=record,
                source_path=source_path,
                source_sha256=record.sha256,
                segments=segments,
                info=info,
                config=engine.config,
                engine_version=engine.version,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                processing_seconds=processing,
                warnings=warnings,
            )
            _atomic_write(json_path, json.dumps(payload, ensure_ascii=False, indent=1))
            _atomic_write(txt_path, render_txt(payload))
            db.upsert_transcript(
                {
                    "sermon_id": record.sermon_id,
                    "status": "transcribed",
                    "source_path": str(source_path),
                    "source_sha256": record.sha256,
                    "json_path": str(json_path),
                    "txt_path": str(txt_path),
                    "model": engine.config.model,
                    "device": engine.config.device,
                    "compute_type": engine.config.compute_type,
                    "settings_json": json.dumps(engine.config.settings_summary()),
                    "engine_version": engine.version,
                    "duration_seconds": duration,
                    "processing_seconds": processing,
                    "segments_count": len(segments),
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "error": None,
                }
            )
            result.status = "transcribed"
            result.json_path = json_path
            result.txt_path = txt_path
            result.duration_seconds = duration
            result.processing_seconds = processing
            result.segments = len(segments)
            result.words = payload["quality"]["word_count"]
            result.warnings = warnings
            result.quality = payload["quality"]
        except Exception as exc:  # noqa: BLE001 - record and continue the batch
            db.upsert_transcript(
                {
                    "sermon_id": record.sermon_id,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            result.status = "failed"
            result.error = f"{type(exc).__name__}: {exc}"
        results.append(result)
    return results


def summarize(results: Sequence[TranscriptResult]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    total_duration = sum(r.duration_seconds or 0.0 for r in results if r.status == "transcribed")
    total_processing = sum(r.processing_seconds or 0.0 for r in results if r.status == "transcribed")
    return {
        "selected": len(results),
        "status_counts": counts,
        "audio_seconds_transcribed": round(total_duration, 1),
        "processing_seconds": round(total_processing, 1),
        "failures": [
            {"sermon_id": r.sermon_id, "error": r.error}
            for r in results
            if r.status == "failed"
        ],
    }
