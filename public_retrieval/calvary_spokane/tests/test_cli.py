from __future__ import annotations

from calvary_archive.cli import build_parser, normalize_legacy_args


def test_cli_exposes_required_commands() -> None:
    parser = build_parser()
    for command in (
        "discover",
        "reconcile-media-candidates",
        "report",
        "download",
        "retry-failed",
        "verify",
    ):
        args = parser.parse_args([command])
        assert args.command == command


def test_legacy_metadata_only_form_becomes_discover() -> None:
    args = normalize_legacy_args(
        ["--start-date", "2004-06-01", "--end-date", "2010-08-31", "--metadata-only"]
    )
    assert args == [
        "discover",
        "--start-date",
        "2004-06-01",
        "--end-date",
        "2010-08-31",
        "--metadata-only",
    ]
