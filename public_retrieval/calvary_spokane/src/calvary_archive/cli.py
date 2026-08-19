"""Command-line orchestration for the Calvary Spokane archive."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

from .database import ArchiveDB
from .discovery import discover
from .downloader import ArchiveDownloader, DownloadConfig
from .legacy import discover_legacy
from .media_index import audit_media_indexes, reconcile_media_index_candidates
from .reports import generate_reports
from .transcribe import (
    TranscriptionConfig,
    TranscriptionEngine,
    run_transcription,
    summarize,
)

DEFAULT_ARCHIVE_ROOT = Path(
    os.environ.get("CALVARY_ARCHIVE_ROOT", "/mnt/storage/data/calvary-spokane")
)
DEFAULT_START_DATE = "2004-06-01"
DEFAULT_END_DATE = "2010-08-31"
COMMANDS = {
    "discover",
    "discover-legacy",
    "audit-media-indexes",
    "reconcile-media-candidates",
    "report",
    "download",
    "retry-failed",
    "verify",
    "transcribe",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def ensure_layout(root: Path) -> None:
    for path in (
        root / "data",
        root / "data" / "raw",
        root / "logs",
        root / "downloads",
        root / "reports",
    ):
        path.mkdir(parents=True, exist_ok=True)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def log_event(root: Path, command: str, event: str, **details: Any) -> None:
    entry = {
        "timestamp": utc_now(),
        "command": command,
        "event": event,
        **_json_safe(details),
    }
    with (root / "logs" / "archive.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def _add_selection_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--speaker", help="Select one exact speaker name")
    parser.add_argument("--series", help="Select one exact series title")
    parser.add_argument("--year", type=int, help="Select one sermon year")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE, help="Inclusive download/verify start date")
    parser.add_argument("--end-date", default=DEFAULT_END_DATE, help="Inclusive download/verify end date")
    parser.add_argument("--limit", type=int, help="Limit selected records for testing")
    parser.add_argument("--dry-run", action="store_true", help="Show work without changing media state")


def _add_download_options(parser: argparse.ArgumentParser) -> None:
    _add_selection_options(parser)
    parser.add_argument(
        "--video",
        action="store_true",
        help="Download video when available (this is already the default)",
    )
    parser.add_argument(
        "--audio-if-no-video",
        action="store_true",
        help="Download audio when an item has no public video",
    )
    parser.add_argument("--workers", type=int, default=1, help="Bounded media concurrency (currently serial)")
    parser.add_argument("--retries", type=int, default=3, help="Attempts per selected media item")
    parser.add_argument("--backoff", type=float, default=1.0, help="Initial retry backoff in seconds")
    parser.add_argument("--timeout", type=float, default=60.0, help="Direct HTTP timeout in seconds")
    parser.add_argument(
        "--process-timeout",
        type=float,
        default=21600.0,
        help="Maximum seconds for one yt-dlp/ffmpeg process",
    )
    parser.add_argument("--no-ffprobe", action="store_true", help="Skip ffprobe media validation")


def _add_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ARCHIVE_ROOT,
        help=f"Archive workspace (default: {DEFAULT_ARCHIVE_ROOT})",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="archive_sermons.py",
        description=(
            "Inventory, download, resume, verify, and report the public Calvary Spokane "
            "sermon archive across Subsplash and supplemental legacy sources."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser(
        "discover", help="Crawl all public metadata before downloading media"
    )
    _add_root(discover_parser)
    discover_parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    discover_parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    discover_parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Compatibility flag; discover never downloads media",
    )
    discover_parser.add_argument("--limit", type=int, help="Stop after selecting N target records")
    discover_parser.add_argument("--dry-run", action="store_true", help="Crawl without inventory upserts")

    legacy_parser = subparsers.add_parser(
        "discover-legacy",
        help="Crawl the public Wayback catalog and legacy media indexes",
    )
    _add_root(legacy_parser)
    legacy_parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    legacy_parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    legacy_parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Import preserved legacy listing JSON instead of refetching Wayback pages",
    )
    legacy_parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Compatibility flag; legacy discovery never downloads full media",
    )
    legacy_parser.add_argument("--limit", type=int, help="Stop after N legacy records")
    legacy_parser.add_argument("--dry-run", action="store_true", help="Crawl without inventory upserts")

    media_index_parser = subparsers.add_parser(
        "audit-media-indexes",
        help="Recursively inventory public legacy MP3/video directory indexes",
    )
    _add_root(media_index_parser)
    media_index_parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    media_index_parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    media_index_parser.add_argument(
        "--max-directories",
        "--limit",
        dest="max_directories",
        type=int,
        help="Stop after N directory pages (a partial test crawl)",
    )
    media_index_parser.add_argument(
        "--max-probes",
        type=int,
        default=200,
        help="Maximum bounded ffprobe checks for unresolved target candidates",
    )
    media_index_parser.add_argument(
        "--no-ffprobe", action="store_true", help="Inventory listings without probing media"
    )
    media_index_parser.add_argument(
        "--reuse-run",
        dest="reuse_run_id",
        type=int,
        help="Reclassify/probe a completed media-index run without refetching directory pages",
    )
    media_index_parser.add_argument(
        "--dry-run", action="store_true", help="Crawl without media-index database upserts"
    )

    reconcile_parser = subparsers.add_parser(
        "reconcile-media-candidates",
        help="Promote exact-dated legacy guest media and retain ambiguous sessions for review",
    )
    _add_root(reconcile_parser)
    reconcile_parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    reconcile_parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    reconcile_parser.add_argument(
        "--run-id", type=int, help="Reconcile a specific completed media-index run"
    )
    reconcile_parser.add_argument(
        "--dry-run", action="store_true", help="Preview candidate decisions without database writes"
    )

    report_parser = subparsers.add_parser("report", help="Regenerate CSV, JSON, and completeness reports")
    _add_root(report_parser)

    download_parser = subparsers.add_parser("download", help="Download video and optionally audio-only items")
    _add_root(download_parser)
    _add_download_options(download_parser)

    retry_parser = subparsers.add_parser("retry-failed", help="Retry only failed media records")
    _add_root(retry_parser)
    _add_download_options(retry_parser)

    verify_parser = subparsers.add_parser("verify", help="Re-hash and ffprobe existing local media")
    _add_root(verify_parser)
    _add_selection_options(verify_parser)
    verify_parser.add_argument("--no-ffprobe", action="store_true", help="Skip ffprobe media validation")

    transcribe_parser = subparsers.add_parser(
        "transcribe", help="Transcribe locally archived audio with faster-whisper"
    )
    _add_root(transcribe_parser)
    _add_selection_options(transcribe_parser)
    transcribe_parser.add_argument("--model", default="large-v3", help="faster-whisper model size")
    transcribe_parser.add_argument("--device", default="cuda", help="cuda or cpu")
    transcribe_parser.add_argument("--compute-type", default="float16", dest="compute_type")
    transcribe_parser.add_argument("--batch-size", type=int, default=16, dest="batch_size")
    transcribe_parser.add_argument("--beam-size", type=int, default=5, dest="beam_size")
    transcribe_parser.add_argument("--force", action="store_true", help="Re-transcribe even if complete")
    transcribe_parser.add_argument(
        "--retry-failed", action="store_true", dest="retry_failed", help="Re-queue failed transcripts"
    )

    return parser


def normalize_legacy_args(argv: Sequence[str]) -> list[str]:
    """Support the original metadata-only command concept without a subcommand."""

    normalized = list(argv)
    if not any(argument in COMMANDS for argument in normalized) and "--metadata-only" in normalized:
        normalized.insert(0, "discover")
    return normalized


def _result_counts(results: Sequence[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        status = str(getattr(result, "status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def _open_database(root: Path, *, must_exist: bool = False) -> ArchiveDB:
    database_path = root / "data" / "sermons.sqlite"
    if must_exist and not database_path.exists():
        raise FileNotFoundError(
            f"Inventory does not exist at {database_path}; run the discover command first"
        )
    return ArchiveDB(database_path)


def _download_config(args: argparse.Namespace, root: Path) -> DownloadConfig:
    return DownloadConfig(
        root=root,
        start_date=args.start_date,
        end_date=args.end_date,
        workers=args.workers,
        retries=args.retries,
        backoff=args.backoff,
        timeout=args.timeout,
        process_timeout=args.process_timeout,
        download_audio=args.audio_if_no_video,
        use_ffprobe=not args.no_ffprobe,
    )


def _print_json(value: Any) -> None:
    print(json.dumps(_json_safe(value), ensure_ascii=False, indent=2, sort_keys=True))


def run_command(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    ensure_layout(root)
    command = args.command
    log_event(root, command, "started", arguments=vars(args))

    if command == "discover":
        with _open_database(root) as db:
            result = discover(
                root,
                db,
                start_date=args.start_date,
                end_date=args.end_date,
                limit=args.limit,
                dry_run=args.dry_run,
            )
            if not args.dry_run:
                generate_reports(db, root)
        log_event(root, command, "completed", result=result)
        _print_json(result)
        return 0

    if command == "discover-legacy":
        with _open_database(root) as db:
            result = discover_legacy(
                root,
                db,
                start_date=args.start_date,
                end_date=args.end_date,
                cache_dir=args.cache_dir,
                limit=args.limit,
                dry_run=args.dry_run,
            )
            if not args.dry_run:
                generate_reports(db, root)
        log_event(root, command, "completed", result=result)
        _print_json(result)
        return 0

    if command == "audit-media-indexes":
        with _open_database(root) as db:
            result = audit_media_indexes(
                root,
                db,
                start_date=args.start_date,
                end_date=args.end_date,
                max_directories=args.max_directories,
                max_probes=args.max_probes,
                no_ffprobe=args.no_ffprobe,
                dry_run=args.dry_run,
                reuse_run_id=args.reuse_run_id,
            )
            if not args.dry_run:
                generate_reports(db, root)
        log_event(root, command, "completed", result=result)
        _print_json(result)
        return 0

    if command == "reconcile-media-candidates":
        with _open_database(root, must_exist=True) as db:
            result = reconcile_media_index_candidates(
                root,
                db,
                start_date=args.start_date,
                end_date=args.end_date,
                run_id=args.run_id,
                dry_run=args.dry_run,
            )
            if not args.dry_run:
                generate_reports(db, root)
        log_event(root, command, "completed", result=result)
        _print_json(result)
        return 0

    if command == "report":
        with _open_database(root, must_exist=True) as db:
            generate_reports(db, root)
            result = {
                "inventory_records": db.count_sermons(),
                "status_counts": db.counts_by_status(),
                "summary": str(root / "reports" / "summary.md"),
            }
        log_event(root, command, "completed", result=result)
        _print_json(result)
        return 0

    if command in {"download", "retry-failed"}:
        with _open_database(root, must_exist=True) as db:
            downloader = ArchiveDownloader(db, config=_download_config(args, root))
            results = downloader.run(
                dry_run=args.dry_run,
                limit=args.limit,
                speaker=args.speaker,
                series=args.series,
                year=args.year,
                retry_failed=command == "retry-failed",
                only_failed=command == "retry-failed",
            )
            if not args.dry_run:
                generate_reports(db, root)
        summary = {"selected": len(results), "status_counts": _result_counts(results)}
        log_event(root, command, "completed", result=summary, items=results)
        _print_json(summary)
        return 3 if any(result.status in {"failed", "needs_review"} for result in results) else 0

    if command == "verify":
        config = DownloadConfig(
            root=root,
            start_date=args.start_date,
            end_date=args.end_date,
            use_ffprobe=not args.no_ffprobe,
        )
        with _open_database(root, must_exist=True) as db:
            downloader = ArchiveDownloader(db, config=config)
            results = downloader.verify_existing(
                dry_run=args.dry_run,
                limit=args.limit,
                speaker=args.speaker,
                series=args.series,
                year=args.year,
            )
            if not args.dry_run:
                generate_reports(db, root)
        valid = sum(result.valid for result in results)
        summary = {"checked": len(results), "valid": valid, "invalid": len(results) - valid}
        log_event(root, command, "completed", result=summary, files=results)
        _print_json(summary)
        return 3 if valid != len(results) else 0

    if command == "transcribe":
        config = TranscriptionConfig(
            model=args.model,
            device=args.device,
            compute_type=args.compute_type,
            batch_size=args.batch_size,
            beam_size=args.beam_size,
        )
        with _open_database(root, must_exist=True) as db:
            records = db.list_transcribe_candidates(
                speaker=args.speaker,
                series=args.series,
                year=args.year,
                limit=args.limit,
            )
            engine = TranscriptionEngine(config)
            results = run_transcription(
                root,
                db,
                engine,
                records=records,
                dry_run=args.dry_run,
                force=args.force,
                retry_failed=args.retry_failed,
            )
        summary = summarize(results)
        summary["configuration"] = config.settings_summary()
        summary["engine_version"] = engine.version
        log_event(root, command, "completed", result=summary, items=results)
        _print_json(summary)
        return 3 if summary["status_counts"].get("failed") else 0

    raise RuntimeError(f"unsupported command: {command}")


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(normalize_legacy_args(raw_args))
    try:
        return run_command(args)
    except KeyboardInterrupt:
        root = getattr(args, "root", DEFAULT_ARCHIVE_ROOT).expanduser().resolve()
        ensure_layout(root)
        log_event(root, args.command, "interrupted")
        print("Interrupted; existing database rows and .part files remain resumable.", file=sys.stderr)
        return 130
    except Exception as exc:
        root = getattr(args, "root", DEFAULT_ARCHIVE_ROOT).expanduser().resolve()
        ensure_layout(root)
        log_event(root, args.command, "failed", error=f"{type(exc).__name__}: {exc}")
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
