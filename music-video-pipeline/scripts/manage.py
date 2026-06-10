#!/usr/bin/env python3
"""Job manager for multi-song music video pipeline projects.

Discovers song projects under a collection directory, checks which pipeline
stages have completed output, and runs only the stages that are needed.

Usage:
    python scripts/manage.py -d projects/prophetic-preprint status
    python scripts/manage.py -d projects/prophetic-preprint run analyze --redo --force
    python scripts/manage.py -d projects/prophetic-preprint run sync --redo
    python scripts/manage.py -d projects/prophetic-preprint run audit --mood dark_moody
    python scripts/manage.py -d projects/prophetic-preprint run all --mood dark_moody --force
    python scripts/manage.py -d projects/prophetic-preprint dashboard
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

PIPELINE_DIR = Path(__file__).resolve().parent.parent
MVP_SCRIPT = PIPELINE_DIR / "mvp.py"
DASHBOARD_SCRIPT = PIPELINE_DIR / "scripts" / "timing_dashboard.py"

STAGE_ORDER = ["analyze", "sync", "audit", "render"]

STAGE_OUTPUTS = {
    "analyze": ["analysis.json"],
    "sync": ["lyrics_synced.json"],
    "audit": ["script.json"],
    "render": ["output/video.mp4"],
}

STAGE_CLEAN = {
    "analyze": [
        "analysis.json",
        "vocal_transcription.json",
        "vocal_transcription_lead_vocals.json",
        "vocal_transcription_backing_vocals.json",
        "vocal_onsets.json",
        "vocal_waveforms.json",
        "waveforms.json",
    ],
    "sync": [
        "lyrics_synced.json",
        "alignment_analysis.json",
    ],
    "audit": [
        "script.json",
    ],
    "render": [],
}


def discover_projects(projects_dir: Path) -> list[dict]:
    found = []
    for d in sorted(projects_dir.iterdir()):
        if not d.is_dir():
            continue
        proj_json = d / "data" / "mvp_project.json"
        if not proj_json.exists():
            continue
        try:
            meta = json.loads(proj_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        found.append({
            "name": meta.get("name", d.name),
            "slug": d.name,
            "dir": d,
            "data_dir": d / "data",
            "meta": meta,
        })
    return found


def stage_complete(proj: dict, stage: str) -> bool:
    proj_dir = proj["dir"]
    data_dir = proj["data_dir"]
    for rel in STAGE_OUTPUTS.get(stage, []):
        if stage == "render":
            p = proj_dir / rel
        else:
            p = data_dir / rel
        if not p.exists() or p.stat().st_size == 0:
            return False
    return True


def clean_stage(proj: dict, stage: str) -> None:
    data_dir = proj["data_dir"]
    for fname in STAGE_CLEAN.get(stage, []):
        p = data_dir / fname
        if p.exists():
            p.unlink()
    if stage == "audit":
        audit_dir = proj["dir"] / "output" / "audit"
        if audit_dir.is_dir():
            shutil.rmtree(audit_dir)
    if stage == "render":
        video = proj["dir"] / "output" / "video.mp4"
        if video.exists():
            video.unlink()


def run_stage_for_song(
    proj: dict,
    stage: str,
    mood: Optional[str] = None,
    force: bool = False,
    verbose: bool = False,
) -> dict:
    proj_dir = proj["dir"]
    slug = proj["slug"]
    name = proj["name"]

    if stage == "analyze":
        cmd = [sys.executable, str(MVP_SCRIPT), "analyze", "-p", str(proj_dir)]
        if force:
            cmd.append("--force")
        if verbose:
            cmd.append("-v")
    elif stage == "sync":
        cmd = [sys.executable, str(MVP_SCRIPT), "sync", "-p", str(proj_dir)]
        if verbose:
            cmd.append("-v")
    elif stage == "audit":
        cmd = [sys.executable, str(MVP_SCRIPT), "audit", "-p", str(proj_dir), "--json-only"]
        if mood:
            cmd.extend(["--mood", mood])
    elif stage == "render":
        cmd = [sys.executable, str(MVP_SCRIPT), "render", "-p", str(proj_dir)]
        if mood:
            cmd.extend(["--mood", mood])
    else:
        return {"slug": slug, "stage": stage, "status": "error", "message": f"Unknown stage: {stage}"}

    t0 = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,
            cwd=str(PIPELINE_DIR),
        )
        elapsed = time.time() - t0
        if result.returncode == 0:
            return {"slug": slug, "name": name, "stage": stage, "status": "ok", "elapsed": elapsed}
        else:
            stderr_tail = (result.stderr or "").strip().split("\n")[-5:]
            stdout_tail = (result.stdout or "").strip().split("\n")[-5:]
            return {
                "slug": slug,
                "name": name,
                "stage": stage,
                "status": "failed",
                "elapsed": elapsed,
                "exit_code": result.returncode,
                "stderr": "\n".join(stderr_tail),
                "stdout": "\n".join(stdout_tail),
            }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        return {"slug": slug, "name": name, "stage": stage, "status": "timeout", "elapsed": elapsed}


def run_stage(
    projects: list[dict],
    stage: str,
    mood: Optional[str] = None,
    force: bool = False,
    redo: bool = False,
    jobs: int = 1,
    dry_run: bool = False,
    verbose: bool = False,
) -> list[dict]:
    to_run = []
    skipped = []

    for proj in projects:
        if redo:
            if not dry_run:
                clean_stage(proj, stage)
            to_run.append(proj)
        elif stage_complete(proj, stage):
            skipped.append(proj)
        else:
            to_run.append(proj)

    if skipped:
        for proj in skipped:
            print(f"  [{proj['slug']}] {stage:8s} SKIP (output exists)")
        print()

    if not to_run:
        print(f"  All {len(projects)} songs already have {stage} output. Use --redo to force.")
        return []

    print(f"  Running {stage} for {len(to_run)} song(s)...\n")

    if dry_run:
        for proj in to_run:
            cmd_parts = [f"{stage}"]
            if stage == "analyze" and force:
                cmd_parts.append("--force")
            if stage in ("audit", "render") and mood:
                cmd_parts.append(f"--mood {mood}")
            print(f"  [{proj['slug']}] WOULD RUN: mvp {' '.join(cmd_parts)}")
        return []

    results = []
    if jobs <= 1:
        for proj in to_run:
            print(f"  [{proj['slug']}] {stage:8s} RUNNING...", end="", flush=True)
            result = run_stage_for_song(proj, stage, mood=mood, force=force, verbose=verbose)
            elapsed = result.get("elapsed", 0)
            status = result["status"]
            if status == "ok":
                print(f" OK ({elapsed:.1f}s)")
            elif status == "timeout":
                print(f" TIMEOUT ({elapsed:.1f}s)")
            else:
                print(f" FAILED ({elapsed:.1f}s)")
                if result.get("stderr"):
                    for line in result["stderr"].split("\n"):
                        print(f"    {line}")
                if result.get("stdout"):
                    for line in result["stdout"].split("\n"):
                        print(f"    {line}")
            results.append(result)
    else:
        with ProcessPoolExecutor(max_workers=jobs) as executor:
            futures = {
                executor.submit(
                    run_stage_for_song, proj, stage, mood=mood, force=force, verbose=verbose
                ): proj
                for proj in to_run
            }
            for future in as_completed(futures):
                proj = futures[future]
                result = future.result()
                elapsed = result.get("elapsed", 0)
                status = result["status"]
                if status == "ok":
                    print(f"  [{proj['slug']}] {stage:8s} OK ({elapsed:.1f}s)")
                elif status == "timeout":
                    print(f"  [{proj['slug']}] {stage:8s} TIMEOUT ({elapsed:.1f}s)")
                else:
                    print(f"  [{proj['slug']}] {stage:8s} FAILED ({elapsed:.1f}s)")
                    if result.get("stderr"):
                        for line in result["stderr"].split("\n"):
                            print(f"    {line}")
                results.append(result)

    return results


def cmd_status(projects: list[dict]) -> None:
    header = f"  {'Song':<35s} {'Analyze':>8s} {'Sync':>8s} {'Audit':>8s} {'Render':>8s}"
    print(header)
    print("  " + "-" * len(header))

    counts = {"analyze": 0, "sync": 0, "audit": 0, "render": 0}
    for proj in projects:
        row = f"  {proj['name']:<35s}"
        for stage in STAGE_ORDER:
            done = stage_complete(proj, stage)
            tag = "done" if done else "---"
            row += f" {tag:>8s}"
            if done:
                counts[stage] += 1
        print(row)

    total = len(projects)
    print()
    print(f"  Total: {total} songs")
    for stage in STAGE_ORDER:
        pct = counts[stage] / total * 100 if total else 0
        print(f"    {stage:8s}: {counts[stage]:>3d}/{total} ({pct:.0f}%)")


def cmd_run(
    projects: list[dict],
    stages: list[str],
    mood: Optional[str] = None,
    force: bool = False,
    redo: bool = False,
    jobs: int = 1,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    all_results = []
    failed_stages = {}

    for stage in stages:
        print(f"\n{'=' * 60}")
        print(f"  Stage: {stage}")
        print(f"{'=' * 60}")
        results = run_stage(
            projects,
            stage,
            mood=mood,
            force=force,
            redo=redo,
            jobs=jobs,
            dry_run=dry_run,
            verbose=verbose,
        )
        all_results.extend(results)

        failed = [r for r in results if r["status"] not in ("ok",)]
        if failed:
            failed_stages[stage] = failed
            if stage != stages[-1]:
                failed_slugs = {r["slug"] for r in failed}
                print(f"\n  WARNING: {len(failed)} song(s) failed at {stage}.")
                print(f"  Continuing to next stage, but these songs may also fail.")

    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"{'=' * 60}")

    ok = [r for r in all_results if r["status"] == "ok"]
    failed = [r for r in all_results if r["status"] == "failed"]
    timeouts = [r for r in all_results if r["status"] == "timeout"]

    print(f"  Succeeded: {len(ok)}")
    print(f"  Failed:    {len(failed)}")
    print(f"  Timeout:   {len(timeouts)}")

    if failed:
        print(f"\n  Failed songs:")
        for r in failed:
            print(f"    [{r['slug']}] {r['stage']} (exit {r.get('exit_code', '?')})")
    if timeouts:
        print(f"\n  Timed out:")
        for r in timeouts:
            print(f"    [{r['slug']}] {r['stage']}")


def cmd_dashboard(projects_dir: Path, dry_run: bool = False) -> None:
    if not DASHBOARD_SCRIPT.exists():
        print(f"  Error: dashboard script not found at {DASHBOARD_SCRIPT}")
        sys.exit(1)

    cmd = [sys.executable, str(DASHBOARD_SCRIPT), str(projects_dir)]
    if dry_run:
        print(f"  Would run: {' '.join(cmd)}")
        return

    print(f"  Generating dashboard...")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PIPELINE_DIR))
    if result.returncode == 0:
        for line in (result.stdout or "").strip().split("\n"):
            print(f"    {line}")
    else:
        print(f"  Dashboard generation failed (exit {result.returncode})")
        for line in (result.stderr or "").strip().split("\n")[-5:]:
            print(f"    {line}")


def main():
    parser = argparse.ArgumentParser(
        description="Job manager for multi-song music video pipeline projects"
    )
    parser.add_argument(
        "--project-dir", "-d",
        required=True,
        help="Path to collection root (e.g., projects/prophetic-preprint)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show pipeline status for all songs")

    run_parser = sub.add_parser("run", help="Run pipeline stage(s)")
    run_parser.add_argument(
        "stages",
        nargs="+",
        choices=["analyze", "sync", "audit", "render", "all"],
        help="Stage(s) to run. 'all' runs analyze -> sync -> audit",
    )
    run_parser.add_argument("--redo", action="store_true", help="Force re-run even if output exists")
    run_parser.add_argument("--force", action="store_true", help="Pass --force to analyze (skip vocal stem errors)")
    run_parser.add_argument("--mood", default=None, help="Mood for audit/render")
    run_parser.add_argument("--jobs", "-j", type=int, default=1, help="Parallel workers (default: 1)")
    run_parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    run_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    dash_parser = sub.add_parser("dashboard", help="Generate timing dashboard")
    dash_parser.add_argument("--dry-run", action="store_true", help="Show what would run")

    args = parser.parse_args()
    collection_dir = Path(args.project_dir).resolve()

    if not collection_dir.is_dir():
        print(f"Error: {collection_dir} is not a directory")
        sys.exit(1)

    projects_dir = collection_dir
    projects = discover_projects(projects_dir)
    if not projects:
        sub = collection_dir / "projects"
        if sub.is_dir():
            projects = discover_projects(sub)
            projects_dir = sub
    if not projects:
        print(f"No projects found under {collection_dir}")
        print(f"  (Looked for subdirectories containing data/mvp_project.json)")
        sys.exit(1)

    print(f"\n  Collection: {collection_dir.name}")
    print(f"  Songs: {len(projects)}")

    if args.command == "status":
        cmd_status(projects)

    elif args.command == "run":
        stages = args.stages
        if "all" in stages:
            stages = ["analyze", "sync", "audit"]
        cmd_run(
            projects,
            stages=stages,
            mood=args.mood,
            force=args.force,
            redo=args.redo,
            jobs=args.jobs,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )

    elif args.command == "dashboard":
        cmd_dashboard(collection_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
