#!/usr/bin/env python3
"""Apply the reality_signal_slate_v2 recipe to the 7-song slate.

Injects each song's display title into the add_branded_scenes step, applies the
recipe (idempotent + invertible), and writes the script back (with .json.bak).

Usage:
    python scripts/apply_slate_v2.py                # apply to all 7
    python scripts/apply_slate_v2.py asabaal        # apply to one
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import transform  # noqa: E402  (registers transforms)
from transform import REGISTRY, ScriptContext  # noqa: E402
from transform.recipes import load_recipe  # noqa: E402

BASE = Path("/mnt/storage/repos/content-tools/projects/prophetic-preprint/projects")
RECIPE = "reality_signal_slate_v2"

TITLES = {
    "asabaal": "ASABAAL",
    "blessed-the-name": "BLESSED (THE NAME)",
    "misclassified": "MISCLASSIFIED",
    "the-first-scroll": "THE FIRST SCROLL",
    "culture-creator": "CULTURE CREATOR",
    "the-devil-s-playbook": "THE DEVIL'S PLAYBOOK",
    "covenant-keeping-god": "COVENANT KEEPING GOD",
}


def apply_one(slug: str) -> None:
    proj = BASE / slug
    script_path = proj / "data" / "script.json"
    ctx = ScriptContext(
        script=json.loads(script_path.read_text(encoding="utf-8")),
        lyrics_synced=json.loads((proj / "data" / "lyrics_synced.json").read_text(encoding="utf-8")),
        project_dir=proj,
    )
    recipe = load_recipe(RECIPE)
    for step in recipe.steps:
        if step.transform == "add_branded_scenes":
            step.params["title"] = TITLES[slug]
    recipe.apply(ctx, REGISTRY)

    bak = script_path.with_suffix(".json.bak")
    bak.write_text(script_path.read_text(encoding="utf-8"), encoding="utf-8")
    script_path.write_text(json.dumps(ctx.script, indent=2, ensure_ascii=False), encoding="utf-8")
    intro = ctx.script.get("intro", {})
    print(f"  {slug:24s} intro_dur={intro.get('duration'):>6}  outro={'outro' in ctx.script}")


def main(argv: list[str]) -> int:
    slugs = argv[1:] or list(TITLES)
    print(f"Applying {RECIPE} to {len(slugs)} song(s):")
    for slug in slugs:
        if slug not in TITLES:
            print(f"  UNKNOWN slug: {slug}", file=sys.stderr)
            continue
        apply_one(slug)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
