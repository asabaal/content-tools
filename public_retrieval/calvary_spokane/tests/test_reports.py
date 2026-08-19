from __future__ import annotations

import csv
import importlib.util
import json
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_PATH = PROJECT_ROOT / "src" / "calvary_archive" / "reports.py"
REPORTS_SPEC = importlib.util.spec_from_file_location("calvary_archive_reports", REPORTS_PATH)
assert REPORTS_SPEC is not None and REPORTS_SPEC.loader is not None
REPORTS_MODULE = importlib.util.module_from_spec(REPORTS_SPEC)
REPORTS_SPEC.loader.exec_module(REPORTS_MODULE)
generate_reports = REPORTS_MODULE.generate_reports


EXPECTED_OUTPUTS = {
    Path("data/sermons.csv"),
    Path("data/sermons.json"),
    Path("reports/summary.md"),
    Path("reports/completeness.csv"),
    Path("reports/needs_date_review.csv"),
    Path("reports/calendar-gaps.csv"),
    Path("reports/calendar-coverage.md"),
}


def _create_fixture(database_path: Path) -> None:
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE series (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            listing_url TEXT,
            advertised_count INTEGER,
            discovered_count INTEGER
        );

        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            source_id TEXT NOT NULL,
            title TEXT NOT NULL,
            sermon_date TEXT,
            speaker TEXT,
            series_id INTEGER,
            bible_book TEXT,
            scripture_reference TEXT,
            page_url TEXT,
            video_url TEXT,
            audio_url TEXT,
            video_path TEXT,
            audio_path TEXT,
            status TEXT,
            needs_date_review INTEGER NOT NULL DEFAULT 0,
            raw_metadata_json TEXT,
            FOREIGN KEY (series_id) REFERENCES series(id)
        );

        CREATE TABLE crawl_runs (
            id INTEGER PRIMARY KEY,
            started_at TEXT,
            status TEXT,
            series_discovered INTEGER,
            advertised_items INTEGER,
            discovered_items INTEGER,
            item_pages_fetched INTEGER,
            api_records INTEGER,
            inventory_records INTEGER,
            downloads_succeeded INTEGER,
            downloads_failed INTEGER,
            review_count INTEGER
        );

        CREATE TABLE listing_audit (
            id INTEGER PRIMARY KEY,
            series_id INTEGER,
            listing_url TEXT,
            advertised_count INTEGER,
            discovered_count INTEGER,
            item_page_count INTEGER,
            api_record_count INTEGER,
            inventory_records INTEGER,
            failure_count INTEGER,
            review_count INTEGER
        );

        CREATE TABLE status_events (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER,
            event_type TEXT,
            status TEXT
        );
        """
    )
    connection.executemany(
        "INSERT INTO series(id, title, listing_url, advertised_count, discovered_count) VALUES (?, ?, ?, ?, ?)",
        [
            (1, "Genesis", "https://example.test/series/genesis", 2, 2),
            (2, "Romans", "https://example.test/series/romans", 2, 1),
        ],
    )
    connection.executemany(
        """
        INSERT INTO sermons(
            id, source_id, title, sermon_date, speaker, series_id, bible_book,
            scripture_reference, page_url, video_url, audio_url, video_path,
            audio_path, status, needs_date_review, raw_metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1,
                "sermon-1",
                "Creation",
                "2020-01-05",
                "Ken Ortiz",
                1,
                "Genesis",
                "Genesis 1:1-5",
                "https://example.test/sermons/creation",
                "https://cdn.example.test/creation.mp4",
                "https://cdn.example.test/creation.mp3",
                "media/creation.mp4",
                None,
                "downloaded",
                0,
                json.dumps(
                    {
                        "api": {"tags": ["creation", "light"], "duration": 2700},
                        "source": ["listing", "api"],
                    }
                ),
            ),
            (
                2,
                "sermon-2",
                "Faith Comes by Hearing",
                None,
                "Guest Speaker",
                2,
                "Romans",
                "Romans 10:17",
                "https://example.test/sermons/hearing",
                None,
                "https://cdn.example.test/hearing.mp3",
                None,
                "media/hearing.mp3",
                "failed",
                1,
                json.dumps({"api": {"formats": [{"kind": "audio", "bitrate": 128}]}}),
            ),
            (
                3,
                "sermon-3",
                "The Fall",
                "2020-02-09",
                None,
                1,
                "Genesis",
                "Genesis 3",
                "https://example.test/sermons/fall",
                None,
                None,
                None,
                None,
                "needs_review",
                0,
                json.dumps({"advertisedTitle": "The Fall — Genesis 3", "flags": [None, True]}),
            ),
        ],
    )
    connection.execute(
        """
        INSERT INTO crawl_runs(
            id, started_at, status, series_discovered, advertised_items,
            discovered_items, item_pages_fetched, api_records, inventory_records,
            downloads_succeeded, downloads_failed, review_count
        ) VALUES (1, '2024-04-01T12:00:00Z', 'completed', 2, 4, 3, 3, 2, 3, 2, 1, 2)
        """
    )
    connection.executemany(
        """
        INSERT INTO listing_audit(
            id, series_id, listing_url, advertised_count, discovered_count,
            item_page_count, api_record_count, inventory_records, failure_count,
            review_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, 1, "https://example.test/series/genesis", 2, 2, 2, 1, 2, 0, 1),
            (2, 2, "https://example.test/series/romans", 2, 1, 1, 1, 1, 1, 1),
        ],
    )
    connection.executemany(
        "INSERT INTO status_events(id, sermon_id, event_type, status) VALUES (?, ?, ?, ?)",
        [
            (1, 1, "download", "completed"),
            (2, 2, "download", "failed"),
            (3, 3, "manual_review", "needs_review"),
        ],
    )
    connection.commit()
    connection.close()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file_object:
        return list(csv.DictReader(file_object))


def test_generate_reports_exports_inventory_and_raw_metadata(tmp_path: Path) -> None:
    database_path = tmp_path / "archive.sqlite3"
    archive_root = tmp_path / "archive"
    _create_fixture(database_path)

    generate_reports(database_path, archive_root)

    actual_outputs = {
        path.relative_to(archive_root)
        for path in archive_root.rglob("*")
        if path.is_file()
    }
    assert actual_outputs == EXPECTED_OUTPUTS

    csv_path = archive_root / "data" / "sermons.csv"
    sermon_rows = _read_csv(csv_path)
    with csv_path.open(newline="", encoding="utf-8") as file_object:
        fieldnames = csv.DictReader(file_object).fieldnames
    assert fieldnames is not None
    required_fields = [
        "sermon_id",
        "source_platform",
        "source_url",
        "series_url",
        "sermon_date",
        "year",
        "title",
        "speaker",
        "series",
        "book_of_bible",
        "scripture_reference",
        "topic",
        "description",
        "service_type",
        "duration_seconds",
        "has_video",
        "has_audio",
        "video_source_url",
        "audio_source_url",
        "thumbnail_url",
        "original_media_filename",
        "local_media_path",
        "download_status",
        "media_format",
        "filesize",
        "sha256",
        "discovered_at",
        "downloaded_at",
        "error",
        "notes",
    ]
    assert fieldnames[: len(required_fields)] == required_fields
    assert "raw_metadata_json" not in fieldnames
    assert [row["source_id"] for row in sermon_rows] == ["sermon-1", "sermon-3", "sermon-2"]
    assert sermon_rows[1]["speaker"] == ""
    assert sermon_rows[2]["sermon_date"] == ""

    json_rows = json.loads((archive_root / "data" / "sermons.json").read_text(encoding="utf-8"))
    assert [row["source_id"] for row in json_rows] == ["sermon-1", "sermon-3", "sermon-2"]
    assert json_rows[0]["raw_metadata"]["api"]["tags"] == ["creation", "light"]
    assert json_rows[0]["raw_metadata"]["api"]["duration"] == 2700
    assert json_rows[1]["raw_metadata"]["flags"] == [None, True]
    assert json_rows[2]["raw_metadata"]["api"]["formats"][0] == {
        "bitrate": 128,
        "kind": "audio",
    }
    gap_rows = _read_csv(archive_root / "reports" / "calendar-gaps.csv")
    assert gap_rows
    assert {row["weekday"] for row in gap_rows} == {"Sunday", "Thursday"}
    coverage = (archive_root / "reports" / "calendar-coverage.md").read_text(encoding="utf-8")
    assert "not** a confirmed missing sermon" in coverage


def test_generate_reports_counts_coverage_and_date_review(tmp_path: Path) -> None:
    database_path = tmp_path / "archive.sqlite3"
    archive_root = tmp_path / "archive"
    _create_fixture(database_path)

    connection = sqlite3.connect(database_path)
    try:
        generate_reports(connection, archive_root)
        # A caller-owned connection remains usable and open.
        assert connection.execute("SELECT COUNT(*) FROM sermons").fetchone()[0] == 3
    finally:
        connection.close()

    completeness_rows = _read_csv(archive_root / "reports" / "completeness.csv")
    overall = completeness_rows[0]
    assert overall == {
        "row_type": "archive",
        "identifier": "overall",
        "label": "Archive total",
        "discovered_series": "2",
        "advertised_items": "4",
        "discovered_items": "3",
        "item_pages": "3",
        "api_records": "2",
        "inventory_target_records": "3",
        "video": "1",
        "video_only": "0",
        "both": "1",
        "audio_only": "1",
        "no_media": "1",
        "downloads": "2",
        "failures": "1",
        "review": "2",
    }
    assert [row["row_type"] for row in completeness_rows] == [
        "archive",
        "crawl",
        "series",
        "series",
        "listing",
        "listing",
    ]
    listing_rows = [row for row in completeness_rows if row["row_type"] == "listing"]
    assert [(row["advertised_items"], row["discovered_items"]) for row in listing_rows] == [
        ("2", "2"),
        ("2", "1"),
    ]

    review_rows = _read_csv(archive_root / "reports" / "needs_date_review.csv")
    assert [row["source_id"] for row in review_rows] == ["sermon-2"]
    assert "missing date" in review_rows[0]["date_review_reason"]
    assert "explicitly flagged for date review" in review_rows[0]["date_review_reason"]

    summary = (archive_root / "reports" / "summary.md").read_text(encoding="utf-8")
    assert "Total sermons: **3**" in summary
    assert "Date window: **2020-01-05 to 2020-02-09**" in summary
    assert "| 2020 | 2 |" in summary
    assert "| 2020-01 | 1 |" in summary
    assert "| Ken Ortiz | 1 |" in summary
    assert "| Genesis | 2 |" in summary
    assert "| both | 1 |" in summary
    assert "| audio-only | 1 |" in summary
    assert "| no media | 1 |" in summary
    assert "| Advertised items | 4 |" in summary
    assert "| Discovered items | 3 |" in summary
    assert "Listing audit rows: **2**" in summary
    assert "failure events: **1**, review events: **1**" in summary


def test_replaces_existing_outputs_without_leaving_temporary_files(tmp_path: Path) -> None:
    database_path = tmp_path / "archive.sqlite3"
    archive_root = tmp_path / "archive"
    _create_fixture(database_path)

    for relative_path in EXPECTED_OUTPUTS:
        destination = archive_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("stale", encoding="utf-8")

    generate_reports(database_path, archive_root)

    assert all((archive_root / path).read_text(encoding="utf-8") != "stale" for path in EXPECTED_OUTPUTS)
    assert not list(archive_root.rglob("*.tmp"))


def test_canonical_archive_schema_and_connection_wrapper(tmp_path: Path) -> None:
    database_path = tmp_path / "canonical.sqlite"
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE series (
            series_id TEXT PRIMARY KEY,
            title TEXT,
            raw_metadata TEXT,
            discovered_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE sermons (
            sermon_id TEXT PRIMARY KEY,
            item_id TEXT,
            series_id TEXT,
            title TEXT,
            speaker TEXT,
            sermon_date TEXT,
            series TEXT,
            scripture TEXT,
            canonical_url TEXT,
            media_url TEXT,
            audio_url TEXT,
            video_url TEXT,
            media_type TEXT,
            status TEXT,
            local_path TEXT,
            last_error TEXT,
            discovered_at TEXT,
            updated_at TEXT,
            raw_metadata TEXT
        );
        CREATE TABLE crawl_runs (
            run_id INTEGER PRIMARY KEY,
            status TEXT,
            started_at TEXT,
            completed_at TEXT,
            pages_seen INTEGER,
            items_seen INTEGER,
            error TEXT,
            metadata TEXT
        );
        CREATE TABLE listing_audit (
            audit_id INTEGER PRIMARY KEY,
            run_id INTEGER,
            listing_url TEXT,
            page_number INTEGER,
            expected_count INTEGER,
            observed_count INTEGER,
            item_ids TEXT,
            observed_at TEXT,
            notes TEXT
        );
        CREATE TABLE status_events (
            event_id INTEGER PRIMARY KEY,
            sermon_id TEXT,
            from_status TEXT,
            to_status TEXT,
            event_at TEXT,
            error TEXT,
            details TEXT
        );
        """
    )
    connection.execute(
        "INSERT INTO series VALUES (?, ?, ?, ?, ?)",
        ("series-1", "Letters and Beginnings", "{}", "2024-01-01", "2024-01-01"),
    )
    connection.executemany(
        "INSERT INTO sermons VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                "sermon-1",
                "item-1",
                "series-1",
                "The Word of Life",
                "Ken Ortiz",
                "2024-01-07",
                "Letters and Beginnings",
                "1 John 1:1-4; Genesis 1:1",
                "https://example.test/one",
                "https://cdn.example.test/one.mp4",
                None,
                None,
                None,
                "verified",
                "media/one.mp4",
                "old transient error",
                "2024-01-01",
                "2024-01-08",
                json.dumps({"provider": {"chapters": [{"title": "Introduction"}]}}),
            ),
            (
                "sermon-2",
                "item-2",
                "series-1",
                "Undated Sermon",
                None,
                None,
                "Letters and Beginnings",
                None,
                "https://example.test/two",
                None,
                None,
                None,
                None,
                "no_media",
                None,
                None,
                "2024-01-01",
                "2024-01-08",
                json.dumps({"provider": {"advertised": True}}),
            ),
        ],
    )
    connection.execute(
        "INSERT INTO crawl_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            1,
            "completed",
            "2024-01-08T00:00:00Z",
            "2024-01-08T00:01:00Z",
            1,
            2,
            None,
            json.dumps({"series_discovered": 1}),
        ),
    )
    connection.execute(
        "INSERT INTO listing_audit VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            1,
            1,
            "https://example.test/listing",
            1,
            3,
            2,
            json.dumps(["item-1", "item-2"]),
            "2024-01-08T00:00:30Z",
            "one advertised item was not discovered",
        ),
    )
    connection.executemany(
        "INSERT INTO status_events VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "sermon-1", "downloading", "failed", "2024-01-08", "timeout", "{}"),
            (2, "sermon-2", "discovered", "needs_review", "2024-01-08", None, "{}"),
        ],
    )
    connection.commit()

    class DatabaseWrapper:
        def __init__(self, wrapped_connection: sqlite3.Connection) -> None:
            self.connection = wrapped_connection

    archive_root = tmp_path / "archive"
    try:
        generate_reports(DatabaseWrapper(connection), archive_root)
        assert connection.execute("SELECT COUNT(*) FROM sermons").fetchone()[0] == 2
    finally:
        connection.close()

    csv_rows = _read_csv(archive_root / "data" / "sermons.csv")
    assert "raw_metadata" not in csv_rows[0]
    json_rows = json.loads((archive_root / "data" / "sermons.json").read_text(encoding="utf-8"))
    assert json_rows[0]["raw_metadata"]["provider"]["chapters"] == [
        {"title": "Introduction"}
    ]

    overall = _read_csv(archive_root / "reports" / "completeness.csv")[0]
    assert overall["advertised_items"] == "3"
    assert overall["discovered_items"] == "2"
    assert overall["item_pages"] == "1"
    assert overall["inventory_target_records"] == "2"
    assert overall["video"] == "1"
    assert overall["no_media"] == "1"
    assert overall["downloads"] == "1"
    assert overall["failures"] == "0"
    assert overall["review"] == "1"

    summary = (archive_root / "reports" / "summary.md").read_text(encoding="utf-8")
    assert "| 1 John | 1 |" in summary
    assert "| Genesis | 1 |" in summary
    assert "failure events: **1**, review events: **1**" in summary
    date_review = _read_csv(archive_root / "reports" / "needs_date_review.csv")
    assert [(row["sermon_id"], row["date_review_reason"]) for row in date_review] == [
        ("sermon-2", "missing date")
    ]
