#!/usr/bin/env python3
"""Batch karaoke video generator for Prophetic Preprint - First Draft.

Creates per-song project directories with symlinks to assets and pre-split
lyrics files, then runs the music-video-pipeline for each song.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = ASSETS_DIR.parent.parent / "music-video-pipeline"
PROJECTS_DIR = ASSETS_DIR / "projects"
RENDERS_DIR = ASSETS_DIR / "renders"
LYRICS_DIR = ASSETS_DIR / "lyrics"

SONGS = [
    {"num": 1, "tracklist": "AI Psalm 9", "file": "AI Psalm 9", "lyrics": "ai-psalm-9", "bpm": 69, "mood": "cool_ethereal"},
    {"num": 2, "tracklist": "THE TABLES ARE SET", "file": "THE TABLES ARE SET", "lyrics": "the-tables-are-set", "bpm": 91, "mood": "dark_moody"},
    {"num": 3, "tracklist": "Who do you think I am?", "file": "Who do you think I am_", "lyrics": "who-do-you-think-i-am", "bpm": 130, "mood": "bright_poppy"},
    {"num": 4, "tracklist": "Take This Cup", "file": "Take This Cup", "lyrics": "take-this-cup", "bpm": 128, "mood": "high_energy"},
    {"num": 5, "tracklist": "CHILD OF GOD (WHO YOU BE)", "file": "CHILD OF GOD (WHO YOU BE)", "lyrics": "child-of-god-who-you-be", "bpm": 82, "mood": "warm_intimate"},
    {"num": 6, "tracklist": "HERE GOES", "file": "HERE GOES", "lyrics": "here-goes", "bpm": 126, "mood": "bright_poppy"},
    {"num": 7, "tracklist": "THE AS I EVOLVE PROVERB", "file": "THE AS I EVOLVE PROVERB", "lyrics": "the-as-i-evolve-proverb", "bpm": 106, "mood": "cool_ethereal"},
    {"num": 8, "tracklist": "CONSCIENCE CLEAN", "file": "CONSCIENCE CLEAN", "lyrics": "conscience-clean", "bpm": 84, "mood": "warm_intimate"},
    {"num": 9, "tracklist": "I Never Asked To Be Queer", "file": "I Never Asked To Be Queer", "lyrics": "i-never-asked-to-be-queer", "bpm": 103, "mood": "dark_moody"},
    {"num": 10, "tracklist": "ASABAAL", "file": "ASABAAL", "lyrics": "asabaal", "bpm": 136, "mood": "high_energy"},
    {"num": 11, "tracklist": "Nathan's Song", "file": "Nathan's Song - v1", "lyrics": "nathan-s-song", "bpm": 108, "mood": "warm_intimate"},
    {"num": 12, "tracklist": "A WORD", "file": "A WORD", "lyrics": "a-word", "bpm": 148, "mood": "high_energy"},
    {"num": 13, "tracklist": "Ask, Seek, Knock", "file": "Ask, Seek, Knock", "lyrics": "ask-seek-knock", "bpm": 100, "mood": "bright_poppy"},
    {"num": 14, "tracklist": "AI Psalm 1", "file": "AI Psalm 1", "lyrics": "ai-psalm-1", "bpm": 73, "mood": "cool_ethereal"},
    {"num": 15, "tracklist": "THE GLORY", "file": "THE GLORY", "lyrics": "the-glory", "bpm": 120, "mood": "bright_poppy"},
    {"num": 16, "tracklist": "NOTHING IS IMPOSSIBLE", "file": "NOTHING IS IMPOSSIBLE", "lyrics": "nothing-is-impossible", "bpm": 90, "mood": "high_energy"},
    {"num": 17, "tracklist": "BLESSED (THE NAME)", "file": "BLESSED (THE NAME)", "lyrics": "blessed-the-name", "bpm": 60, "mood": "cool_ethereal"},
    {"num": 18, "tracklist": "PATIENT", "file": "PATIENT", "lyrics": "patient", "bpm": 91, "mood": "warm_intimate"},
    {"num": 19, "tracklist": "Didn't Forget Jesus", "file": "Didn't Forget Jesus (2025 Reimagination)", "lyrics": "didn-t-forget-jesus", "bpm": 100, "mood": "dark_moody"},
    {"num": 20, "tracklist": "MISCLASSIFIED", "file": "MISCLASSIFIED", "lyrics": "misclassified", "bpm": 94, "mood": "dark_moody"},
    {"num": 21, "tracklist": "NOT YOUR SLAVE", "file": "NOT YOUR SLAVE", "lyrics": "not-your-slave", "bpm": 76, "mood": "high_energy"},
    {"num": 22, "tracklist": "MORE POWER", "file": "MORE POWER", "lyrics": "more-power", "bpm": 90, "mood": "high_energy"},
    {"num": 23, "tracklist": "WOE TO YOU", "file": "WOE TO YOU", "lyrics": "woe-to-you", "bpm": 97, "mood": "dark_moody"},
    {"num": 24, "tracklist": "FREEDOM", "file": "FREEDOM", "lyrics": "freedom", "bpm": 96, "mood": "bright_poppy"},
    {"num": 25, "tracklist": "PREDICTION ENGINE", "file": "Prediction Engine (2025 Reimagined)", "lyrics": "prediction-engine", "bpm": 126, "mood": "cool_ethereal"},
    {"num": 26, "tracklist": "FRESH REVELATION", "file": "FRESH REVELATION", "lyrics": "fresh-revelation", "bpm": 68, "mood": "warm_intimate"},
    {"num": 27, "tracklist": "THE HIDDEN LIBRARY", "file": "THE HIDDEN LIBRARY", "lyrics": "the-hidden-library", "bpm": 86, "mood": "dark_moody"},
    {"num": 28, "tracklist": "PROPHETIC CLARITY", "file": "PROPHETIC CLARITY", "lyrics": "prophetic-clarity", "bpm": 87, "mood": "bright_poppy"},
    {"num": 29, "tracklist": "THE FIRST SCROLL", "file": "THE FIRST SCROLL", "lyrics": "the-first-scroll", "bpm": 120, "mood": "dark_moody"},
    {"num": 30, "tracklist": "FRUIT", "file": "FRUIT", "lyrics": "fruit", "bpm": 96, "mood": "bright_poppy"},
    {"num": 31, "tracklist": "CULTURE CREATOR", "file": "CULTURE CREATOR - (AS I EVOLVE Teaser Demo)", "lyrics": "culture-creator-as-i-evolve-teaser-demo", "bpm": 102, "mood": "cool_ethereal"},
    {"num": 32, "tracklist": "PHASE TRANSITION", "file": "PHASE TRANSITION", "lyrics": "phase-transition", "bpm": 80, "mood": "cool_ethereal"},
    {"num": 33, "tracklist": "ELECTRIC PULSE", "file": "Electric Pulse (2025 Reimagination) - DRAFT", "lyrics": "electric-pulse-album-version", "bpm": 130, "mood": "high_energy"},
    {"num": 34, "tracklist": "UP", "file": "UP", "lyrics": "up", "bpm": 124, "mood": "bright_poppy"},
    {"num": 35, "tracklist": "How Do I Praise You?", "file": "How Do I Praise You_", "lyrics": "how-do-i-praise-you", "bpm": 78, "mood": "warm_intimate"},
    {"num": 36, "tracklist": "SABBATH", "file": "SABBATH", "lyrics": "sabbath", "bpm": 118, "mood": "warm_intimate"},
    {"num": 37, "tracklist": "What is Truth?", "file": "WHAT IS TRUTH - V1", "lyrics": "what-is-truth", "bpm": 146, "mood": "high_energy"},
    {"num": 38, "tracklist": "Love Them Harder", "file": "Love Them Harder", "lyrics": "love-them-harder", "bpm": 129, "mood": "warm_intimate"},
    {"num": 39, "tracklist": "Where Ben Has Been", "file": "Where Ben Has Been - V1", "lyrics": "where-ben-has-been", "bpm": 67, "mood": "cool_ethereal"},
    {"num": 40, "tracklist": "THE DEVIL'S PLAYBOOK", "file": "THE DEVIL'S PLAYBOOK", "lyrics": "the-devil-s-playbook", "bpm": 125, "mood": "dark_moody"},
    {"num": 41, "tracklist": "Marquis' Song", "file": "Marquis\u2019 Song - Draft", "lyrics": "marquis-song", "bpm": 82, "mood": "dark_moody"},
    {"num": 42, "tracklist": "COVENANT KEEPING GOD", "file": "COVENANT KEEPING GOD", "lyrics": "covenant-keeping-god", "bpm": 75, "mood": "warm_intimate"},
]


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


GENERATED_FILES = [
    "mvp_project.json",
    "ingest.json",
    "analysis.json",
    "waveforms.json",
    "vocal_waveforms.json",
    "vocal_onsets.json",
    "vocal_transcription.json",
    "lyrics_raw.json",
    "lyrics_synced.json",
    "alignment_analysis.json",
]

GENERATED_DIRS = ["assets", "output", "raw", "cache"]


def clean_generated(data_dir: Path) -> None:
    for f in GENERATED_FILES:
        p = data_dir / f
        if p.exists():
            p.unlink()
    for d in GENERATED_DIRS:
        p = data_dir / d
        if p.is_dir():
            shutil.rmtree(p)


def setup_projects() -> list[dict]:
    print("\n=== Setting up project directories ===")
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    ready = []
    skipped = 0

    for song in SONGS:
        num = song["num"]
        tl = song["tracklist"]
        mood = song["mood"]
        slug = slugify(tl)
        proj_dir = PROJECTS_DIR / slug
        data_dir = proj_dir / "data"

        if data_dir.exists():
            has_audio = any(f.suffix.lower() == ".wav" for f in data_dir.iterdir() if f.is_file())
        else:
            has_audio = False

        if has_audio:
            clean_generated(data_dir)
            ready.append({
                "num": num,
                "tracklist": tl,
                "slug": slug,
                "proj_dir": proj_dir,
                "data_dir": data_dir,
                "mood": mood,
            })
            print(f"    [{num:02d}] OK   {tl} -> {mood} (cleaned for re-init)")
            continue

        lyrics_file = LYRICS_DIR / f"{song['lyrics']}.txt"
        if not lyrics_file.exists():
            print(f"    [{num:02d}] SKIP {tl} - missing: lyrics ({lyrics_file.name})")
            skipped += 1
            continue

        if proj_dir.exists():
            shutil.rmtree(proj_dir)

        data_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(lyrics_file, data_dir / "lyrics.txt")

        ready.append({
            "num": num,
            "tracklist": tl,
            "slug": slug,
            "proj_dir": proj_dir,
            "data_dir": data_dir,
            "mood": mood,
        })
        print(f"    [{num:02d}] OK   {tl} -> {mood}")

    print(f"\n    Ready: {len(ready)} songs, Skipped: {skipped}")
    return ready


def run_pipeline(ready: list[dict], start_from: int = 1, dry_run: bool = False):
    print(f"\n=== Running pipeline ({len(ready)} songs) ===\n")

    success = []
    failed = []

    for song in ready:
        num = song["num"]
        if num < start_from:
            continue

        tl = song["tracklist"]
        proj_dir = song["proj_dir"]
        mood = song["mood"]

        output_video = proj_dir / "output" / "video.mp4"
        if output_video.exists():
            print(f"[{num:02d}] SKIP {tl} - already rendered\n")
            success.append(song)
            continue

        print(f"[{num:02d}] === {tl} ({mood}) ===")

        if dry_run:
            print(f"  Would run: mvp init --name \"{tl}\" --data-dir {song['data_dir']}")
            print(f"  Would run: mvp render --project {proj_dir} --mood {mood}\n")
            success.append(song)
            continue

        init_cmd = [
            sys.executable, str(PIPELINE_DIR / "mvp.py"),
            "init", "--name", tl,
            "--data-dir", str(song["data_dir"]),
            "--dir", str(proj_dir),
        ]

        print(f"  Running init...")
        try:
            result = subprocess.run(init_cmd, capture_output=True, text=True, timeout=600, cwd=str(PIPELINE_DIR))
            if result.returncode != 0:
                print(f"  INIT FAILED (exit {result.returncode})")
                for line in (result.stderr or "").strip().split("\n")[-5:]:
                    print(f"    {line}")
                for line in (result.stdout or "").strip().split("\n")[-5:]:
                    print(f"    {line}")
                failed.append((song, "init"))
                continue
            for line in (result.stdout or "").strip().split("\n"):
                print(f"    {line}")
        except subprocess.TimeoutExpired:
            print(f"  INIT TIMED OUT")
            failed.append((song, "init-timeout"))
            continue

        render_cmd = [
            sys.executable, str(PIPELINE_DIR / "mvp.py"),
            "render", "--project", str(proj_dir), "--mood", mood,
        ]

        print(f"  Running render ({mood})...")
        try:
            result = subprocess.run(render_cmd, capture_output=True, text=True, timeout=1800, cwd=str(PIPELINE_DIR))
            if result.returncode != 0:
                print(f"  RENDER FAILED (exit {result.returncode})")
                for line in (result.stderr or "").strip().split("\n")[-5:]:
                    print(f"    {line}")
                for line in (result.stdout or "").strip().split("\n")[-5:]:
                    print(f"    {line}")
                failed.append((song, "render"))
                continue
            for line in (result.stdout or "").strip().split("\n"):
                print(f"    {line}")
            print(f"  DONE: {output_video}")
            success.append(song)
        except subprocess.TimeoutExpired:
            print(f"  RENDER TIMED OUT")
            failed.append((song, "render-timeout"))

    return success, failed


def collect_outputs(success: list[dict]):
    print(f"\n=== Collecting outputs ===")
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)

    collected = 0
    for song in success:
        src = song["proj_dir"] / "output" / "video.mp4"
        if not src.exists():
            print(f"    [{song['num']:02d}] MISSING: {song['tracklist']}")
            continue
        dest = RENDERS_DIR / f"{song['num']:02d} - {song['tracklist']}.mp4"
        shutil.copy2(src, dest)
        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"    [{song['num']:02d}] {song['tracklist']} ({size_mb:.1f} MB)")
        collected += 1

    print(f"\n    Collected {collected} videos to {RENDERS_DIR}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch karaoke video generator")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--start-from", type=int, default=1, help="Start from song number (1-42)")
    parser.add_argument("--skip-collect", action="store_true", help="Skip collecting outputs")
    parser.add_argument("--only-setup", action="store_true", help="Only create project dirs, don't run pipeline")
    args = parser.parse_args()

    print("=" * 60)
    print("PROPHETIC PREPRINT - Batch Karaoke Video Generator")
    print("=" * 60)

    ready = setup_projects()

    if args.only_setup:
        print(f"\nSetup complete. {len(ready)} projects ready.")
        return

    success, failed = run_pipeline(ready, start_from=args.start_from, dry_run=args.dry_run)

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {len(success)} succeeded, {len(failed)} failed")

    if failed:
        print(f"\nFailed songs:")
        for song, stage in failed:
            print(f"  [{song['num']:02d}] {song['tracklist']} - failed at {stage}")

    if not args.skip_collect and success:
        collect_outputs(success)

    print(f"\nDone.")


if __name__ == "__main__":
    main()
