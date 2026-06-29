#!/usr/bin/env python3
"""Batch-render catalog songs whose scripts have been transformed.

Renders each project via `mvp.py render` (no --mood, so the edited script.json is
used), copies the result to renders/<TITLE>.mp4, and is robust per-song (one
failure does not stop the batch). Sorted shortest-first for quick feedback.

Usage:
    nohup python scripts/render_catalog.py > /tmp/render_catalog.log 2>&1 &
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

_PIPELINE = Path(__file__).resolve().parent.parent
_SRC = _PIPELINE / "src"
_PROJECTS = _PIPELINE.parent / "projects" / "prophetic-preprint"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_PROJECTS) not in sys.path:
    sys.path.insert(0, str(_PROJECTS))

from batch_videos import SONGS, slugify  # noqa: E402

PROJECTS_DIR = _PROJECTS / "projects"
RENDERS_DIR = _PROJECTS / "renders"
RECIPE_APPLIED_MARKER = "_transforms"  # scripts we transformed carry this

SLATE_SHIPPED = {
    "asabaal", "blessed-the-name", "misclassified", "the-first-scroll",
    "culture-creator", "the-devil-s-playbook", "covenant-keeping-god",
}
LOCKED = {"ai-psalm-9"}


def _duration(slug: str) -> float:
    p = PROJECTS_DIR / slug / "data" / "analysis.json"
    try:
        return float(json.loads(p.read_text()).get("duration", 0.0))
    except Exception:
        return 9999.0


def _targets() -> list[tuple[str, str]]:
    out = []
    for s in SONGS:
        slug = slugify(s["tracklist"])
        if slug in SLATE_SHIPPED or slug in LOCKED:
            continue
        out.append((slug, s["tracklist"]))
    return out


def main() -> int:
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)
    targets = _targets()
    # shortest first
    targets.sort(key=lambda st: _duration(st[0]))

    print(f"Rendering {len(targets)} songs (shortest first).", flush=True)
    ok = fail = 0
    for i, (slug, title) in enumerate(targets, 1):
        proj = PROJECTS_DIR / slug
        t0 = time.time()
        print(f"[{i}/{len(targets)}] {slug} ({title!r}) duration={_duration(slug):.0f}s ...", flush=True)
        try:
            r = subprocess.run(
                [sys.executable, "mvp.py", "render", "--project", str(proj)],
                cwd=str(_PIPELINE),
                capture_output=True, text=True, timeout=2400,
            )
            success = r.returncode == 0 and (proj / "output" / "video.mp4").exists()
        except subprocess.TimeoutExpired:
            success = False
            r = None
        if success:
            dest = RENDERS_DIR / f"{title}.mp4"
            shutil.copy2(proj / "output" / "video.mp4", dest)
            mb = dest.stat().st_size / 1e6
            print(f"  OK {dest.name} ({mb:.0f}MB) in {time.time()-t0:.0f}s", flush=True)
            ok += 1
        else:
            print(f"  FAIL {slug}", flush=True)
            if r is not None:
                tail = (r.stderr or r.stdout or "")
                for line in tail.strip().splitlines()[-6:]:
                    print(f"    {line}", flush=True)
            fail += 1

    print(f"\nDONE: {ok} ok, {fail} failed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
