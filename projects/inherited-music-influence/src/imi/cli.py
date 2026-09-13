"""CLI for the Inherited Music Influence Archive pipeline.

Usage: python3 src/imi/cli.py <command> [options]
Commands: parse, enrich, rank, export, note, note-get, unresolved, summary
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_DEFAULT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _root(args) -> Path:
    return Path(args.root).resolve() if args.root else PROJECT_DEFAULT


def cmd_parse(args) -> int:
    from .parse_workbook import parse_project
    counts = parse_project(_root(args))
    print(json.dumps({"stage": "parse", "counts": counts}, indent=2))
    return 0


def cmd_enrich(args) -> int:
    from .resolve import run_enrichment
    root = _root(args)
    counts = run_enrichment(root, limit=args.limit, only=args.ids, force=args.force)
    print(json.dumps({"stage": "enrich", "counts": counts}, indent=2))
    return 0


def cmd_rank(args) -> int:
    from .rank import rank
    rows = rank(_root(args))
    for r in rows[: args.n]:
        print(f"{r['queue_rank']:4d}  {r['canonical_artist'][:28]:28}  "
              f"{r['canonical_title'][:38]:38}  dad={r['dad_source_count']} "
              f"fav={r['dad_favorite_source_count']}")
    return 0


def cmd_export(args) -> int:
    from .rank import export_views
    summary = export_views(_root(args), top_n=300)
    print(json.dumps({"stage": "export", "summary": summary}, indent=2))
    return 0


def cmd_note(args) -> int:
    from .annotations import set_note
    updates = {
        "recognition_status": args.recognize,
        "childhood_association": args.childhood,
        "listened": args.listened,
        "listening_note": args.listening_note,
        "memory_note": args.memory_note,
        "musical_features": args.musical_features,
        "possible_influence_note": args.influence_note,
        "influence_confidence": args.influence_confidence,
    }
    row = set_note(_root(args), args.song_id, updates)
    print(json.dumps({"stage": "note", "annotation": row}, indent=2))
    return 0


def cmd_note_get(args) -> int:
    from .annotations import get_note
    print(json.dumps(get_note(_root(args), args.song_id), indent=2))
    return 0


def cmd_unresolved(args) -> int:
    from .db import connect
    root = _root(args)
    conn = connect(root / "data" / "imi.sqlite")
    rows = conn.execute(
        "SELECT dad_source_id, sheet_row, artist_raw, title_raw, year_raw,"
        " resolution_status, resolution_notes FROM dad_sources"
        " WHERE resolution_status IN ('unresolved','ambiguous')"
        " ORDER BY favorite_raw DESC, sheet_row").fetchall()
    out = {"unresolved": len(rows),
           "rows": [dict(r) for r in rows]}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                  encoding="utf-8")
    return 0


def cmd_summary(args) -> int:
    from .rank import export_views
    summary = export_views(_root(args))
    print(json.dumps(summary, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help=f"project root (default {PROJECT_DEFAULT})")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("parse", help="parse preserved workbook -> dad_sources")
    p = sub.add_parser("enrich", help="resolve releases via MusicBrainz (cached, resumable)")
    p.add_argument("--limit", type=int)
    p.add_argument("--ids", help="comma-separated dad_source_ids")
    p.add_argument("--force", action="store_true",
                   help="include already-resolved rows")

    p = sub.add_parser("rank", help="print head of ranked queue")
    p.add_argument("--n", type=int, default=25)
    sub.add_parser("export", help="regenerate queues + top-300 + summary")
    sub.add_parser("summary", help="print archive summary")

    p = sub.add_parser("note", help="write an annotation for a song")
    p.add_argument("song_id")
    p.add_argument("--recognize", choices=(
        "unreviewed", "definitely_recognize", "not_sure", "definitely_do_not_recognize"))
    p.add_argument("--childhood", choices=("yes", "maybe", "no", "unknown"))
    p.add_argument("--listened", choices=("yes", "no"))
    p.add_argument("--listening-note")
    p.add_argument("--memory-note")
    p.add_argument("--musical-features")
    p.add_argument("--influence-note")
    p.add_argument("--influence-confidence")

    p = sub.add_parser("note-get", help="read annotations for a song")
    p.add_argument("song_id")

    p = sub.add_parser("unresolved", help="list unresolved/ambiguous sources")
    p.add_argument("--out", help="also write JSON to this path")

    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return {"parse": cmd_parse, "enrich": cmd_enrich, "rank": cmd_rank,
            "export": cmd_export, "note": cmd_note, "note-get": cmd_note_get,
            "unresolved": cmd_unresolved, "summary": cmd_summary}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
