#!/usr/bin/env python3
"""Reality Signal groupoid -- script transformation CLI.

Operates directly on a project's ``data/script.json`` (never the generator).
Recipes are declarative JSON specs of a desired version, composed of registered
transformations; every application is journaled and fully invertible.

Usage:
    python scripts/transform.py apply -p <project> --recipe reality_signal_slate
    python scripts/transform.py apply -p <project> --recipe reality_signal_slate --dry-run
    python scripts/transform.py invert -p <project>
    python scripts/transform.py list
    python scripts/transform.py diff  -p <project> --recipe reality_signal_slate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import transform  # noqa: E402  (imports trigger registration)
from transform import REGISTRY, Recipe, ScriptContext  # noqa: E402
from transform.recipes import DEFAULT_RECIPES_DIR, load_recipe  # noqa: E402


def _load_context(project_dir: Path) -> ScriptContext:
    data_dir = project_dir / "data"
    script_path = data_dir / "script.json"
    if not script_path.exists():
        raise SystemExit(f"script.json not found at {script_path}")
    script = json.loads(script_path.read_text(encoding="utf-8"))
    synced = None
    synced_path = data_dir / "lyrics_synced.json"
    if synced_path.exists():
        synced = json.loads(synced_path.read_text(encoding="utf-8"))
    return ScriptContext(script=script, lyrics_synced=synced, project_dir=project_dir)


def _journal_summary(journal) -> dict:
    roots: dict[str, int] = {}
    for entry in journal.entries:
        root = "/".join(str(p) for p in entry.address[:2]) or "<root>"
        roots[root] = roots.get(root, 0) + 1
    return {"total_changes": len(journal.entries), "by_area": roots}


def cmd_apply(args: argparse.Namespace) -> int:
    project_dir = Path(args.project)
    ctx = _load_context(project_dir)
    recipe = load_recipe(args.recipe) if not args.recipe_dict else Recipe.from_dict(json.loads(args.recipe_dict))

    print(f"  Recipe: {recipe.name} ({len(recipe.steps)} steps)")
    journal = recipe.apply(ctx, REGISTRY)
    summary = _journal_summary(journal)
    print(f"  Applied: {summary['total_changes']} key changes")
    for area, count in sorted(summary["by_area"].items()):
        print(f"    {area}: {count}")

    if args.dry_run:
        print("  (dry-run; script not written)")
        return 0

    _write_script(project_dir, ctx.script, backup=not args.no_backup)
    print(f"  Wrote data/script.json")
    return 0


def cmd_invert(args: argparse.Namespace) -> int:
    project_dir = Path(args.project)
    ctx = _load_context(project_dir)
    existing = ctx.script.get("_transforms")
    if not isinstance(existing, dict) or not existing.get("journal"):
        print("  No transform journal found in script; nothing to invert.")
        return 1
    recipe_name = existing.get("recipe", "<unknown>")
    journal = Recipe(name=recipe_name).invert(ctx)
    print(f"  Inverted recipe {recipe_name!r} ({len(journal.entries)} entries replayed)")
    _write_script(project_dir, ctx.script, backup=not args.no_backup)
    print(f"  Restored data/script.json")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    print("Transformations:")
    for name in REGISTRY.names():
        t = REGISTRY.get(name)
        print(f"  {name:24s} {t.description}")
    print(f"\nRecipes ({DEFAULT_RECIPES_DIR}):")
    if DEFAULT_RECIPES_DIR.is_dir():
        for p in sorted(DEFAULT_RECIPES_DIR.glob("*.json")):
            try:
                r = Recipe.from_dict(json.loads(p.read_text(encoding="utf-8")))
                print(f"  {r.name:24s} ({len(r.steps)} steps)  [{p.name}]")
            except Exception as e:  # pragma: no cover
                print(f"  {p.name}: <invalid: {e}>")
    else:
        print("  (none)")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    project_dir = Path(args.project)
    ctx = _load_context(project_dir)
    recipe = load_recipe(args.recipe)
    before = json.loads(json.dumps(ctx.script))  # cheap deepcopy
    journal = recipe.apply(ctx, REGISTRY)
    summary = _journal_summary(journal)
    print(f"  Recipe: {recipe.name}")
    print(f"  Changes: {summary['total_changes']}")
    for area, count in sorted(summary["by_area"].items()):
        print(f"    {area}: {count}")
    # show a few representative concrete diffs
    print("  Sample changes (first 12):")
    for entry in journal.entries[:12]:
        addr = "/".join(str(p) for p in entry.address)
        b = entry.before if entry.before is not None else "<absent>"
        a = entry.after if entry.after is not None else "<removed>"
        print(f"    {addr}: {_short(b)} -> {_short(a)}")
    # restore (discard the in-memory application)
    ctx.script.clear()
    ctx.script.update(before)
    return 0


def _short(v) -> str:
    s = str(v)
    return s if len(s) <= 48 else s[:45] + "..."


def _write_script(project_dir: Path, script: dict, backup: bool) -> None:
    script_path = project_dir / "data" / "script.json"
    if backup and script_path.exists():
        bak = script_path.with_suffix(".json.bak")
        bak.write_text(script_path.read_text(encoding="utf-8"), encoding="utf-8")
    script_path.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reality Signal groupoid -- script transforms")
    sub = parser.add_subparsers(dest="command", required=True)

    p_apply = sub.add_parser("apply", help="Apply a recipe to a project's script.json")
    p_apply.add_argument("-p", "--project", required=True, help="Project directory")
    p_apply.add_argument("--recipe", default=None, help="Recipe name or path")
    p_apply.add_argument("--recipe-dict", default=None, help="Inline JSON recipe string")
    p_apply.add_argument("--dry-run", action="store_true", help="Do not write the script")
    p_apply.add_argument("--no-backup", action="store_true", help="Skip .json.bak backup")
    p_apply.set_defaults(func=cmd_apply)

    p_inv = sub.add_parser("invert", help="Invert the recorded transform journal")
    p_inv.add_argument("-p", "--project", required=True, help="Project directory")
    p_inv.add_argument("--no-backup", action="store_true", help="Skip .json.bak backup")
    p_inv.set_defaults(func=cmd_invert)

    p_list = sub.add_parser("list", help="List registered transforms and recipes")
    p_list.set_defaults(func=cmd_list)

    p_diff = sub.add_parser("diff", help="Show what a recipe would change (dry-run)")
    p_diff.add_argument("-p", "--project", required=True, help="Project directory")
    p_diff.add_argument("--recipe", required=True, help="Recipe name or path")
    p_diff.set_defaults(func=cmd_diff)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
