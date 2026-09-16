"""Build the Suno Rendering Prompt Book — calibration-family aware (§5 of
the TIMING_PROBES_ADDENDUM).

Three canonical references; targets route by ontology family:
  pitched_harmonic  → 4:00 'The Steward's Calibration' (piano/synth
                      conditioning candidates)
  percussion_timing → 2:00 'Percussion Timing Reference' (neutral click)
  vocal_timing      → 2:00 'Vocal Timing Reference' (neutral ah/vox)

Every MAIN and EXCLUDE prompt is validated at 900–1000 exact characters,
and stale duration wording (4:48 / 288 s / 120 bars) fails the build.
Each prompt entry identifies its canonical conditioning artifact + hash.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .checker import check_book
from .families import FAMILY_META, PITCHED, PERCUSSION, VOCAL, route
from .ontology import DEFAULT_REPO, load_targets
from .prompts import build_exclude, build_main, pitched_identity

FORBIDDEN_STALE_REFERENCES = ["4:48", "288 seconds", "288-second",
                              "120 bars"]
MC_ROOT = Path(DEFAULT_REPO) / "reference_composition"

FAMILY_PIECE_DIR = {
    PITCHED: MC_ROOT / "output",
    PERCUSSION: MC_ROOT / "timing" / "output",
    VOCAL: MC_ROOT / "timing" / "output",
}
FAMILY_MID = {
    PITCHED: "canonical_reference_piece.mid",
    PERCUSSION: "percussion_timing_reference.mid",
    VOCAL: "vocal_timing_reference.mid",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def title_of(family: str) -> str:
    return {PITCHED: "The Steward's Calibration",
            PERCUSSION: "Percussion Timing Reference",
            VOCAL: "Vocal Timing Reference"}[family]


def assert_no_stale_references(texts: dict[str, str]) -> None:
    """Fail if superseded duration wording (4:48 / 288 s / 120 bars)
    survives in generated prompts or the book. (The guard module's own
    documentation is never scanned.)"""
    hits = []
    for name, text in texts.items():
        for bad in FORBIDDEN_STALE_REFERENCES:
            if bad.lower() in text.lower():
                hits.append(f"{name}: contains {bad!r}")
    if hits:
        raise SystemExit("STALE DURATION REFERENCES FOUND:\n" +
                         "\n".join(hits))


def _piece_map(family: str) -> dict:
    prefix = family.replace("_timing", "")   # percussion_timing -> percussion
    path = FAMILY_PIECE_DIR[family] / (
        "movement_map.json" if family == PITCHED
        else f"{prefix}_timing_map.json")
    return json.loads(path.read_text())


def family_intro(family: str) -> tuple[list[str], list[str]]:
    """(intro_lines, conditioning_lines) for a family section."""
    meta = FAMILY_META[family]
    mmap = _piece_map(family)
    dur = mmap.get("duration_seconds", meta["duration_seconds"])
    n_sections = len(mmap.get("sections") or mmap.get("regions") or [])
    lines = [
        f"Reference piece: **{title_of(family)}** — {dur:.0f} s, "
        f"{mmap.get('tempo_bpm', 100 if family == PITCHED else 120)} BPM, "
        f"{n_sections} "
        f"{'movements' if family == PITCHED else 'timing regions'}.",
    ]
    cond_lines = []
    for c in meta["conditioning"]:
        path = FAMILY_PIECE_DIR[family] / c["path"]
        cond_lines.append(
            f"- conditioning candidate `{c['candidate']}`: "
            f"`{c['path']}` (sha256 {sha256_file(path)[:16]}…)"
            if path.is_file() else
            f"- conditioning candidate `{c['candidate']}`: MISSING "
            f"({c['path']})")
    return lines, cond_lines


def identity_for(family: str) -> str:
    """Compose the MAIN identity line from the family's generated movement
    map — the score artifacts are the single source of truth for duration,
    bars, and movement/region names."""
    mmap = _piece_map(family)
    if family == PITCHED:
        return pitched_identity(mmap)
    label = title_of(family)
    dur = mmap["duration_seconds"]
    dur_str = f"{int(dur // 60)}:{int(dur % 60):02d}"
    n = len(mmap["regions"])
    word = {9: "nine", 10: "ten", 11: "eleven"}.get(n, str(n))
    kind = ("timing probe on a neutral click transient (no drum-kit "
            "styling)" if family == PERCUSSION else
            "non-lexical vocal timing probe ('ah' vowel only, no words)")
    return (f"Perform '{label}': {dur_str} {kind}, {mmap['tempo_bpm']} BPM, "
            f"{word} regions: "
            + "; ".join(r["region"].replace("_", " ") for r in mmap["regions"])
            + ". Lanes/voices may differ by pitch only; onsets stay exactly "
            "on the written grid.")


def build_all(repo_root: Path) -> dict:
    targets = load_targets()

    routed = {}
    for target_id, t in targets.items():
        routed[target_id] = route(target_id, t.category)

    identities = {f: identity_for(f) for f in (PITCHED, PERCUSSION, VOCAL)}
    prompts: dict[str, dict[str, str]] = {}
    for target_id, target in sorted(targets.items()):
        family = routed[target_id].primary
        prompts[target_id] = {
            "main": build_main(target, identities[family], family=family),
            "exclude": build_exclude(target, targets, family=family),
        }

    texts = {f"{tid}/{field}": text
             for tid, pair in prompts.items()
             for field, text in pair.items()}
    assert_no_stale_references(texts)
    report = check_book(prompts)
    return {"targets": targets, "routed": routed, "prompts": prompts,
            "report": report, "identities": identities}


def write_book(repo_root: Path, built: dict) -> Path:
    repo_root = Path(repo_root)
    piece_dir = repo_root / "projects" / "reference-corpus" / "canonical-piece"
    book_dir = piece_dir / "prompt-book"
    book_dir.mkdir(parents=True, exist_ok=True)

    report = built["report"]
    if not report["all_ok"]:
        failures = [c for c in report["checks"] if not c["ok"]]
        for f in failures:
            print(f"FAIL {f['target_id']}/{f['field']}: "
                  f"{f['char_count']} chars — {f['problems']}", file=sys.stderr)
        raise SystemExit(f"{len(failures)} prompt(s) failed validation; "
                         f"book NOT written")

    supersession = ("CALIBRATION GENERATION SUPERSEDED: the Solo/Lead "
                    "generation prompts now live in "
                    "`SUNO_CALIBRATION_PROMPT_BIBLE.md` (one instrument at "
                    "a time, ~60 s Solo + Lead attempts). This book remains "
                    "the authoritative source for per-target CONDITIONING "
                    "prompts only. Old generation prompts preserved in Git "
                    "history.")
    lines = [
        "# Suno Rendering Prompt Book — Calibration Suite",
        "",
        f"> {supersession}",
        "",
        f"_Generated {datetime.now(timezone.utc).isoformat()} · "
        f"{report['targets']} targets · {report['prompt_count']} prompts · "
        f"all validated at {report['rules']}._",
        "",
        "## The calibration suite (three canonical references)",
        "",
        "One piece per measurement problem; every Suno Advanced Split "
        "target renders its family's reference. Never per-target etudes.",
        "",
        "1. **Pitched / Harmonic Reference — 4:00** — 'The Steward's "
        "Calibration': nine movements, all 24 keys, progressions, scales, "
        "intervals 2nds–octaves, chord types, textures, articulations, "
        "registers, two solos, dense finale. Conditioning candidates: "
        "neutral piano and neutral plain synth.",
        "2. **Percussion Timing Reference — 2:00** — onset/timing stress "
        "test on a neutral click: subdivisions through quintuplets, dotted "
        "figures, accents, rests, syncopation, 3+3+2 groupings, "
        "simultaneous/staggered events, call-and-response, 3/4, 6/8, 5/8 "
        "(3+2, 2+3), 7/8 (2+2+3, 3+2+2). Conditioning: neutral click, NOT a "
        "drum kit.",
        "3. **Vocal Timing Reference — 2:00** — non-lexical 'ah' timing "
        "probe: note lengths, sustains, staccato, legato, melisma, dotted "
        "and tied rhythms, pickups, contours (ascending/descending/arch/"
        "repeated), registers, 1–4 part stacks, staggered backing entries, "
        "call-and-response, 3/4, 6/8, 5/8, 7/8. Conditioning: neutral "
        "ah/vox patch (GM 52 Voice Aahs via FluidR3_GM).",
        "",
        "Invariants for every render: movement/region order, tempo, "
        "calibration-passage content and timing, target timbre dominant.",
        "",
    ]

    by_family: dict[str, list[str]] = {PITCHED: [], PERCUSSION: [],
                                       VOCAL: []}
    for target_id in sorted(built["prompts"]):
        by_family[built["routed"][target_id].primary].append(target_id)

    for family in (PITCHED, PERCUSSION, VOCAL):
        meta = FAMILY_META[family]
        intro, cond = family_intro(family)
        lines += ["---", f"# FAMILY: {meta['label']} ({family})",
                  f"Duration: {meta['duration_seconds']:.0f} s · "
                  f"{len(by_family[family])} target(s)"]
        lines += intro
        lines += ["", "**Canonical conditioning artifact(s)**"] + cond + [""]

        for target_id in by_family[family]:
            target = built["targets"][target_id]
            main_p = built["prompts"][target_id]["main"]
            excl_p = built["prompts"][target_id]["exclude"]
            cm = check_book({target_id: {"main": main_p,
                                         "exclude": excl_p}})
            checks = {c["field"]: c for c in cm["checks"]}

            def _line(c, icon):
                mark = "✓" if c["ok"] else "✗ FAIL"
                return (f"{icon} {c['field']} — {c['char_count']} "
                        f"characters {mark}")

            multi = ""
            if built["routed"][target_id].multi:
                multi = ("  _multi-family: "
                         + ", ".join(built["routed"][target_id].all_families)
                         + "_")
            lines += [
                f"## TARGET: {target.name} (`{target_id}`)"
                f"{'  [beta]' if target.is_beta else ''}{multi}",
                f"_category: {target.category}"
                + (f" · {target.description}" if target.description else "")
                + "_",
                "",
                _line(checks["MAIN"], "🟣"),
                "```text", main_p, "```", "",
                _line(checks["EXCLUDE"], "🛑"),
                "```text", excl_p, "```", "",
                "### Render log (fill after rendering)", "",
                "| field | value |", "|---|---|",
                "| Suno model/version | |",
                "| render ID | |",
                "| generation date | |",
                "| conditioning source + sha256 | |",
                "| keeper/reject | |",
                "| deviations from canonical structure | |",
                "| extraction performed? | |",
                "| extracted target path/hash | |",
                "| MIDI extracted? | |",
                "| notes | |", "",
            ]

    book_text = "\n".join(lines) + "\n"
    assert_no_stale_references({"__book__": book_text})
    book_path = book_dir / "SUNO_RENDERING_PROMPT_BOOK.md"
    book_path.write_text(book_text)

    (book_dir / "validation-report.json").write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
                    **report}, indent=2) + "\n")

    for target_id, pair in built["prompts"].items():
        tdir = piece_dir / "targets" / target_id.replace("_", "-")
        tdir.mkdir(exist_ok=True)
        (tdir / "prompt.txt").write_text(pair["main"])
        (tdir / "exclude.txt").write_text(pair["exclude"])
    return book_path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="build-book")
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
