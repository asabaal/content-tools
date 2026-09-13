"""Build the Suno Rendering Prompt Book (spec §10).

    python -m reference_corpus.build_book [--corpus-root projects/reference-corpus]

1. loads the documented Suno Advanced Split ontology (standard + beta)
2. builds 🟣 MAIN and 🛑 EXCLUDE prompts for every target from the canonical
   piece's movement map (one-piece principle)
3. validates every prompt with the exact character checker (900–1000)
4. writes per-target prompt.txt / exclude.txt and the human-readable
   SUNO_RENDERING_PROMPT_BOOK.md with character counts beside each prompt
5. exits non-zero if any prompt fails validation
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .checker import check_book
from .corpus import CANONICAL_DIR, CORPUS_ROOT
from .ontology import load_targets
from .prompts import build_exclude, build_main


def movement_summary_from_map(mmap_path: Path) -> str:
    """Short machine-derived movement summary so prompts describe the REAL
    composition (never hand-written drift)."""
    m = json.loads(mmap_path.read_text())
    parts = []
    for s in m["sections"]:
        parts.append(f"{s['title']} ({s['start_seconds']:.0f}s-"
                     f"{s['end_seconds']:.0f}s)")
    return ("Movement timing map: " + "; ".join(parts) + ". Total duration "
            f"{m['duration_seconds']:.0f} seconds.")


def build_all(repo_root: Path) -> dict:
    repo_root = Path(repo_root)
    piece = repo_root / CANONICAL_DIR
    mmap_path = piece / "movement_map.json"
    if not mmap_path.is_file():
        print("movement_map.json missing — ingest the canonical composition "
              "first (reference_corpus.corpus.init_corpus)", file=sys.stderr)
        return {}

    targets = load_targets()
    summary = movement_summary_from_map(mmap_path)

    prompts: dict[str, dict[str, str]] = {}
    for target_id, target in sorted(targets.items()):
        prompts[target_id] = {
            "main": build_main(target, summary),
            "exclude": build_exclude(target, targets),
        }

    report = check_book(prompts)
    return {"targets": targets, "prompts": prompts, "report": report,
            "summary": summary}


def write_book(repo_root: Path, built: dict) -> Path:
    repo_root = Path(repo_root)
    piece = repo_root / CANONICAL_DIR
    book_dir = piece / "prompt-book"
    book_dir.mkdir(parents=True, exist_ok=True)

    report = built["report"]
    if not report["all_ok"]:
        failures = [c for c in report["checks"] if not c["ok"]]
        for f in failures:
            print(f"FAIL {f['target_id']}/{f['field']}: "
                  f"{f['char_count']} chars — {f['problems']}",
                  file=sys.stderr)
        raise SystemExit(f"{len(failures)} prompt(s) failed validation; "
                         f"book NOT written")

    mmap = json.loads((piece / "movement_map.json").read_text())
    lines = [
        "# Suno Rendering Prompt Book — The Steward's Calibration",
        "",
        f"_Generated {datetime.now(timezone.utc).isoformat()} · "
        f"{report['targets']} targets · {report['prompt_count']} prompts · "
        f"all validated at {report['rules']} characters._",
        "",
        "## What this piece is and why it exists",
        "",
        "This is the ONE canonical reference composition of the Suno Target "
        "Reference Corpus. It is a 4:48 instrumental calibration suite: you "
        "will render the SAME piece repeatedly, once per Suno Advanced Split "
        "target, so the resulting audio differs (as much as Suno permits) "
        "only in the requested instrument/timbre. Those renders become the "
        "reference exemplars that let us decide which Suno extraction "
        "targets are actually present in unknown songs — including "
        "`projects/hippie-activist./`.",
        "",
        "## Composition structure (invariant across ALL renders)",
        "",
        f"- Tempo/meter: {mmap['tempo_bpm']} BPM, "
        f"{mmap['meter'][0]}/{mmap['meter'][1]}, "
        f"{mmap['duration_seconds']:.0f} seconds, "
        f"{mmap['total_bars']} bars, nine movements:",
        "",
    ]
    for s in mmap["sections"]:
        lines.append(f"  * **{s['title']}** — {s['start_seconds']:.0f}s–"
                     f"{s['end_seconds']:.0f}s "
                     f"(coverage: {', '.join(s['coverage_tags'])})")
    lines += [
        "",
        "### Key journey",
        "",
        "Majors Parade visits all 12 major keys (circle of fifths, C → Ab); "
        "Minors Parade visits all 12 minor keys with harmonic-minor "
        "dominants; the Progression Journey modulates C → F → G and runs an "
        "A blues; the Finale climbs C → D and closes with an E-minor "
        "cadence.",
        "",
        "### What each render must keep (invariants)",
        "",
        "Same movement order and boundaries; same 100 BPM; same harmonic "
        "and key journey; same melodic contours; same two solos; same "
        "dense-finale climax logic; calibration passages (scales, intervals, "
        "counterpoint, voicings, registers, articulations) must stay "
        "audible. Only the dominant instrument/timbre changes per target.",
        "",
        "## Prompts",
        "",
        "Paste MAIN into Suno's main/style field and EXCLUDE into the "
        "exclude/avoid field. Character counts (exact, spaces included) are "
        "printed beside each prompt — both must be 900–1000.",
        "",
    ]

    for target_id in sorted(built["prompts"]):
        target = built["targets"][target_id]
        main_p = built["prompts"][target_id]["main"]
        excl_p = built["prompts"][target_id]["exclude"]
        cm = check_book({target_id: {"main": main_p, "exclude": excl_p}})
        checks = {c["field"]: c for c in cm["checks"]}

        def _line(c, icon):
            mark = "✓" if c["ok"] else "✗ FAIL"
            return f"{icon} {c['field']} — {c['char_count']} characters {mark}"

        lines += [
            f"## TARGET: {target.name} (`{target_id}`)"
            f"{'  [beta]' if target.is_beta else ''}",
            f"_category: {target.category}"
            + (f" · {target.description}" if target.description else "") + "_",
            "",
            _line(checks["MAIN"], "🟣"),
            "```text",
            main_p,
            "```",
            "",
            _line(checks["EXCLUDE"], "🛑"),
            "```text",
            excl_p,
            "```",
            "",
            "### Render log (fill after rendering)",
            "",
            "| field | value |", "|---|---|",
            "| Suno model/version | |",
            "| render ID | |",
            "| generation date | |",
            "| keeper/reject | |",
            "| deviations from canonical structure | |",
            "| extraction performed? | |",
            "| extracted target path/hash | |",
            "| MIDI extracted? | |",
            "| notes | |",
            "",
        ]

    # per-target files
    from .ontology import TARGETS_DIR  # ensure import surface stays honest
    for target_id, pair in built["prompts"].items():
        tdir = piece / "targets" / target_id.replace("_", "-")
        tdir.mkdir(exist_ok=True)
        (tdir / "prompt.txt").write_text(pair["main"])
        (tdir / "exclude.txt").write_text(pair["exclude"])

    book_path = book_dir / "SUNO_RENDERING_PROMPT_BOOK.md"
    book_path.write_text("\n".join(lines) + "\n")

    (book_dir / "validation-report.json").write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
                    **report}, indent=2) + "\n")
    return book_path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="build-book")
    ap.add_argument("--corpus-root", type=Path, default=CORPUS_ROOT)
    args = ap.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[3]
    built = build_all(repo_root)
    if not built:
        return 2
    book = write_book(repo_root, built)
    r = built["report"]
    print(f"prompt book: {book}")
    print(f"{r['prompt_count']} prompts across {r['targets']} targets — "
          f"all_ok={r['all_ok']}")
    return 0 if r["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
