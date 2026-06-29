#!/usr/bin/env python3
"""Mass-apply a transform recipe across the Prophetic Preprint catalog.

Derives each song's project slug and intro title from ``batch_videos.SONGS``
(tracklist names), excludes the already-shipped slate and any locked songs, and
applies the recipe idempotently to each remaining project's ``script.json``.

Usage:
    python scripts/apply_recipe_all.py                          # all catalog songs except slate + locked
    python scripts/apply_recipe_all.py --recipe reality_signal_slate_v2
    python scripts/apply_recipe_all.py --only ai-psalm-9,here-goes
    python scripts/apply_recipe_all.py --exclude nathan-s-song
    python scripts/apply_recipe_all.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
_PROJECTS = Path(__file__).resolve().parent.parent.parent / "projects" / "prophetic-preprint"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_PROJECTS) not in sys.path:
    sys.path.insert(0, str(_PROJECTS))

import transform  # noqa: E402  (registers transforms)
from transform import REGISTRY, ScriptContext  # noqa: E402
from transform.recipes import load_recipe  # noqa: E402
from batch_videos import SONGS, slugify  # noqa: E402

PROJECTS_DIR = _PROJECTS / "projects"
RECIPE_DEFAULT = "reality_signal_slate_v2"

# Already shipped with v2 (do not re-apply here) + locked baseline.
SLATE_SHIPPED = {
    "asabaal", "blessed-the-name", "misclassified", "the-first-scroll",
    "culture-creator", "the-devil-s-playbook", "covenant-keeping-god",
}
LOCKED = {"ai-psalm-9"}  # design bible: preserve, do not redesign


def _catalog() -> list[tuple[str, str]]:
    """Return [(slug, title)] for every song in batch_videos.SONGS."""
    return [(slugify(s["tracklist"]), s["tracklist"]) for s in SONGS]


def apply_one(slug: str, title: str, recipe_name: str, dry_run: bool) -> dict:
    proj = PROJECTS_DIR / slug
    script_path = proj / "data" / "script.json"
    if not script_path.exists():
        return {"slug": slug, "ok": False, "reason": "no script.json"}
    ctx = ScriptContext(
        script=json.loads(script_path.read_text(encoding="utf-8")),
        lyrics_synced=json.loads((proj / "data" / "lyrics_synced.json").read_text(encoding="utf-8")),
        project_dir=proj,
    )
    recipe = load_recipe(recipe_name)
    for step in recipe.steps:
        if step.transform == "add_branded_scenes":
            step.params["title"] = title
    recipe.apply(ctx, REGISTRY)

    if not dry_run:
        bak = script_path.with_suffix(".json.bak")
        bak.write_text(script_path.read_text(encoding="utf-8"), encoding="utf-8")
        script_path.write_text(json.dumps(ctx.script, indent=2, ensure_ascii=False), encoding="utf-8")

    intro = ctx.script.get("intro", {})
    return {
        "slug": slug, "ok": True, "title": title,
        "intro_duration": intro.get("duration"),
        "outro": "outro" in ctx.script,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Mass-apply a recipe across the catalog")
    ap.add_argument("--recipe", default=RECIPE_DEFAULT)
    ap.add_argument("--only", default="", help="comma-separated slugs to target (default: all minus slate/locked)")
    ap.add_argument("--exclude", default="", help="comma-separated slugs to skip")
    ap.add_argument("--dry-run", action="store_true", help="don't write scripts")
    args = ap.parse_args(argv)

    catalog = _catalog()
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        targets = [(slug, title) for slug, title in catalog if slug in wanted]
    else:
        skip = set(SLATE_SHIPPED) | set(LOCKED)
        skip |= {s.strip() for s in args.exclude.split(",") if s.strip()}
        targets = [(slug, title) for slug, title in catalog if slug not in skip]

    print(f"Applying {args.recipe} to {len(targets)} song(s)...")
    intro_on = intro_off = 0
    for slug, title in targets:
        r = apply_one(slug, title, args.recipe, args.dry_run)
        if not r["ok"]:
            print(f"  SKIP {slug}: {r['reason']}")
            continue
        dur = r["intro_duration"]
        if dur and dur > 0:
            intro_on += 1
            tag = f"intro={dur}s"
        else:
            intro_off += 1
            tag = "intro=skipped(no pre-roll)"
        verb = "would apply" if args.dry_run else "applied"
        print(f"  {verb} {slug:30s} title={title!r:34s} {tag} outro={r['outro']}")

    print(f"\nDone: {len(targets)} songs | intro enabled: {intro_on} | intro skipped: {intro_off}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
