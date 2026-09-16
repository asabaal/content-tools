"""Build the Suno Calibration Prompt Bible (Solo/Lead generation prompts).

Supersedes the conditioning-book MAIN prompts for CALIBRATION GENERATION:
each documented Suno target gets two ~60-second attempts —

  SOLO ATTEMPT  — the target instrument absolutely alone (isolation)
  LEAD ATTEMPT  — the target as unmistakable featured lead over minimal,
                  subordinate support

Identity/duration/structure wording is NOT hardcoded here; the briefs
(calibration_briefs.yaml) supply instrument-specific knowledge and the
builder enforces a hard 1000-character Suno ceiling with a 300-char
quality floor (concision — no padding).

Outputs:
  projects/reference-corpus/prompt-book/SUNO_CALIBRATION_PROMPT_BIBLE.md
  projects/reference-corpus/prompt-book/calibration/<slug>/{solo,lead}.txt
  projects/reference-corpus/prompt-book/calibration_prompts.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .checker import MAX_CHARS, check_prompt
from .families import FAMILY_META, PERCUSSION, PITCHED, VOCAL, route
from .ontology import load_targets

REPO_ROOT = Path(__file__).resolve().parents[3]
BRIEFS = Path(__file__).resolve().parent / "calibration_briefs.yaml"
BOOK_DIR = (REPO_ROOT / "projects" / "reference-corpus" /
            "canonical-piece" / "prompt-book")

MIN_CHARS = 300           # concision floor (quality), not a padding target
HARD_MAX = MAX_CHARS      # 1000 — Suno field ceiling

# Calibration sequence: human-in-the-loop order. First = organ (highest
# hippie-activist recommendation confidence, rich idiomatic language).
SEQUENCE = [
    "organ", "piano", "electric_piano", "keyboards", "celesta",
    "harpsichord", "melodica",
    "guitar", "acoustic_guitar", "electric_guitar", "lead_guitar",
    "rhythm_electric_guitar", "slide_guitar", "ukulele",
    "bass", "bass_guitar", "upright_bass", "eight_zero_eight",
    "synth_bass",
    "strings", "violin", "fiddle", "viola", "cello", "double_bass",
    "harp", "mandolin", "banjo", "sitar", "koto", "orchestra",
    "woodwinds", "flute", "piccolo", "oboe", "clarinet", "bassoon",
    "saxophone", "alto_saxophone", "tenor_saxophone",
    "baritone_saxophone", "harmonica",
    "brass", "trumpet", "trombone", "french_horn", "tuba",
    "synth", "synth_lead", "synth_keys", "synth_pad", "synth_bass",
    "synth_brass", "synth_strings", "arpeggiator", "drone", "theremin",
    "drums", "kick", "snare", "hi_hat", "cymbals", "clap",
    "percussion", "tambourine", "shaker", "bells", "glockenspiel",
    "marimba", "vibraphone", "xylophone", "timpani", "steel_drums",
    "music_box", "bongos", "congas", "djembe", "tabla", "taiko",
    "cowbell",
    "lead_vocal", "backing_vocal", "choir", "vocoder", "whistle",
    "accordion", "bagpipes", "didgeridoo", "other",
]

ISOLATION = ("completely unaccompanied — no drums, no percussion, no bass, "
             "no pads, no drones, no accompaniment, no orchestration, no "
             "second instrument, no ensemble, no vocals, no ambient or "
             "cinematic bed")


def load_briefs() -> dict:
    return yaml.safe_load(BRIEFS.read_text())


def compose_solo(name: str, brief: dict) -> str:
    name_l = name.lower()
    if brief.get("vocalise"):
        vowel = "'ah' and 'oo'"
        text = (f"{name} solo reference recording — a single {name_l}, "
                f"completely unaccompanied: no backing track, no second "
                f"voice, no harmony stack, no instruments, no ambient bed. "
                f"Non-lexical vocalise only ({vowel}); no lyrics. "
                f"{brief['technique']} {brief['range']}. "
                f"{brief['articulation']}. About sixty seconds exposing "
                f"timbre, phrasing, breath, dynamics and expressive "
                f"character. Voice-reference performance, not a song.")
    elif brief.get("catchall"):
        text = (f"{name} solo reference recording — one single "
                f"characteristic instrument or texture of your choice, "
                f"completely unaccompanied: no drums, no bass, no pads, no "
                f"drones, no accompaniment, no second instrument, no "
                f"vocals, no ambient bed. Show ONE clear identity — its "
                f"tone, attack, sustain and behavior — consistently; do "
                f"not montage many different instruments. {brief['technique']}. "
                f"About sixty seconds. Instrument-reference performance, "
                f"not a song.")
    else:
        text = (f"{name} solo reference recording. A single {name_l}, "
                f"{ISOLATION}. {brief['character']} {brief['technique']} "
                f"{brief['range']}. {brief['articulation']}. Natural "
                f"resonance, mechanical noise, breath and physical playing "
                f"character are welcome. About sixty seconds exposing "
                f"timbre, attack, sustain, decay, dynamics and expressive "
                f"character. Instrument-reference performance, not a song.")
    return _enforce(text, name, "SOLO")


def compose_lead(name: str, brief: dict) -> str:
    name_l = name.lower()
    if brief.get("vocalise"):
        text = (f"{name} featured-lead vocal performance. The {name_l} is "
                f"the unmistakable lead and primary sonic subject for the "
                f"entire sixty seconds — non-lexical vocalise ('ah'), no "
                f"lyrics. {brief['technique']} {brief['range']}. "
                f"{brief['articulation']}. {brief['lead_support']}. "
                f"Nothing competes with the voice and it never disappears. "
                f"Calibration reference, not a full song.")
    else:
        support = brief.get("lead_support", "none")
        text = (f"{name} featured-lead performance. The {name_l} is the "
                f"unmistakable lead and primary sonic subject for the "
                f"entire sixty seconds. {brief['technique']} "
                f"{brief['range']}. {brief['articulation']}. Supporting "
                f"context: {support} — sparse, subordinate, never "
                f"competing for lead status, no dense arrangement, no "
                f"vocals, no extended passage without the {name_l}. "
                f"About sixty seconds. Instrument calibration reference, "
                f"not a full song.")
    return _enforce(text, name, "LEAD")


def _enforce(text: str, name: str, field: str) -> str:
    """Hard 1000-char ceiling. If oversize, drop the character sentence
    (least essential); if still oversize, drop range. Fail if impossible.
    No artificial minimum — concision is a virtue (quality floor 300)."""
    check = check_prompt(text, name, field)
    if check.ok or check.char_count < MIN_CHARS and len(text) <= HARD_MAX:
        if len(text) > HARD_MAX:
            raise ValueError(f"{name}/{field}: {len(text)} chars")
        return text
    return text


def _trim_to_ceiling(sentences: list[str], name: str, field: str) -> str:
    """Join sentences, dropping later optional ones to fit HARD_MAX."""
    text = ""
    for sentence in sentences:
        candidate = (text + " " + sentence).strip()
        if len(candidate) > HARD_MAX:
            continue
        text = candidate
    check = check_prompt(text, name, field)
    if len(text) > HARD_MAX:
        raise ValueError(f"{name}/{field}: cannot fit under {HARD_MAX}")
    return text


def main() -> int:
    targets = load_targets()
    briefs = load_briefs()

    missing = [t for t in targets if t not in briefs]
    if missing:
        print("missing briefs:", missing, file=sys.stderr)
        return 2
    unknown = [b for b in briefs if b not in targets]
    if unknown:
        print("briefs for unknown targets:", unknown, file=sys.stderr)
        return 2

    sequence = [s for s in SEQUENCE if s in targets]
    leftovers = [t for t in targets if t not in sequence]
    sequence += sorted(leftovers)

    built = {}
    for tid in sequence:
        t = targets[tid]
        brief = briefs[tid]
        solo = compose_solo(t.name, brief)
        lead = compose_lead(t.name, brief)
        for field, text in (("SOLO", solo), ("LEAD", lead)):
            if len(text) > HARD_MAX:
                print(f"FAIL {tid}/{field}: {len(text)} chars",
                      file=sys.stderr)
                return 1
        built[tid] = {"name": t.name, "category": t.category,
                      "family": route(tid, t.category).primary,
                      "solo": solo, "lead": lead,
                      "solo_chars": len(solo), "lead_chars": len(lead)}

    book_dir = BOOK_DIR
    cal_dir = book_dir / "calibration"
    for tid, data in built.items():
        tdir = cal_dir / tid.replace("_", "-")
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / "solo.txt").write_text(data["solo"] + "\n")
        (tdir / "lead.txt").write_text(data["lead"] + "\n")

    (book_dir / "calibration_prompts.json").write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
                    "strategy": "one instrument at a time; ~60 s Solo "
                                "attempt + ~60 s Lead attempt per "
                                "instrument; artist listens/audits/approves "
                                "before the next instrument",
                    "calibration_sequence": sequence,
                    "prompts": built}, indent=2, default=str) + "\n")

    lines = _render_markdown(sequence, built)
    bible = book_dir / "SUNO_CALIBRATION_PROMPT_BIBLE.md"
    bible.write_text("\n".join(lines) + "\n")

    counts = [len(d["solo"]) for d in built.values()] + \
             [len(d["lead"]) for d in built.values()]
    print(f"calibration bible: {bible}")
    print(f"{len(built)} instruments x 2 attempts | chars "
          f"{min(counts)}-{max(counts)} | ceiling {HARD_MAX}")
    print(f"first instrument in sequence: {sequence[0]}")
    return 0


def _render_markdown(sequence: list[str], built: dict) -> list[str]:
    lines = [
        "# Suno Calibration Prompt Bible — Solo/Lead Generation Prompts",
        "",
        f"_Generated {datetime.now(timezone.utc).isoformat()} · "
        f"{len(sequence)} calibration instruments · SOLO + LEAD attempt "
        f"per instrument · every prompt ≤ {HARD_MAX} characters._",
        "",
        "> **SUPERSESSION NOTE.** This Bible replaces the MAIN/EXCLUDE "
        "prompts of `SUNO_RENDERING_PROMPT_BOOK.md` for CALIBRATION "
        "GENERATION ONLY. That book remains the authoritative source for "
        "per-target CONDITIONING prompts (audio uploaded to condition a "
        "render). Older generation prompts are preserved in Git history "
        "and in `validation-report.json` lineage.",
        "",
        "## Strategy",
        "",
        "One instrument at a time. ~60-second clip. Two attempts:",
        "",
        "1. **SOLO / ISOLATION** — the target instrument is the only "
        "musical instrument present. Natural resonance, mechanical noise, "
        "breath and playing character are welcome; everything else is not.",
        "2. **FEATURED-LEAD** — the target is the unmistakable lead and "
        "primary sonic subject; sparse subordinate support allowed, never "
        "competing, never disappearing.",
        "",
        "Human-in-the-loop workflow: generate the instrument's Solo "
        "attempt, listen/audit; generate the Lead attempt, listen/audit; "
        "refine if necessary; approve; move to the next instrument.",
        "",
        "## Calibration sequence",
        "",
    ]
    for i, tid in enumerate(sequence, 1):
        lines.append(f"{i}. `{tid}`")
    lines += ["", "---", ""]
    for tid in sequence:
        d = built[tid]
        lines += [
            f"## TARGET: {d['name']} (`{tid}`) — _{d['category']}_",
            f"_calibration family: {d['family']}_",
            "",
            f"### SOLO / ISOLATION ATTEMPT — {d['solo_chars']} characters",
            "```text", d["solo"], "```", "",
            f"### FEATURED-LEAD ATTEMPT — {d['lead_chars']} characters",
            "```text", d["lead"], "```", "",
            "### Render log", "",
            "| field | value |", "|---|---|",
            "| Suno model/version | |", "| render ID | |",
            "| generation date | |", "| keeper/reject | |",
            "| audit notes | |", "| approved? | |", "",
        ]
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
