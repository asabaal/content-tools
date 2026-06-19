#!/usr/bin/env python3
"""Apply a visual design profile to a project's script.json.

Reads a simple per-song profile spec and patches the section visual blocks
to match the visual design bible. Supports per-section overrides by type
with ordinal indexing (e.g., "verse:1" for the second verse section).

Usage:
    python scripts/apply_profile.py -p <project_dir> --profile <profile.json>
    python scripts/apply_profile.py -p .../misclassified --profile .../misclassified_profile.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _resolve_type_key(sections: list, key: str) -> list[int]:
    """Resolve a profile key like 'verse' or 'verse:1' to section indices.

    Ordinal is 1-based: 'verse:1' = first verse, 'verse:2' = second.
    Without ordinal: matches all sections of that type.
    """
    if ":" in key:
        base_type, ordinal_str = key.split(":", 1)
        ordinal = int(ordinal_str)
    else:
        base_type, ordinal = key, 0

    indices = []
    type_seen = 0
    for i, s in enumerate(sections):
        stype = s.get("type", "")
        if stype == base_type:
            type_seen += 1
            if ordinal == 0 or type_seen == ordinal:
                indices.append(i)
    return indices


def apply_profile(script_path: Path, profile: dict) -> dict:
    """Apply profile overrides to a script.json dict."""
    script = json.loads(script_path.read_text(encoding="utf-8"))
    sections = script.get("sections", [])

    defaults = profile.get("defaults", {})
    if defaults:
        merged = dict(script.get("defaults", {}))
        merged.update(defaults)
        script["defaults"] = merged

    caption = profile.get("caption_style", {})
    if caption:
        merged_cap = dict(script.get("caption_style", {}))
        merged_cap.update(caption)
        script["caption_style"] = merged_cap

    section_profiles = profile.get("sections", {})

    for key, visual_overrides in section_profiles.items():
        indices = _resolve_type_key(sections, key)
        if not indices:
            print(f"  WARNING: no sections matched '{key}'", file=sys.stderr)
            continue

        for idx in indices:
            section = sections[idx]
            visual = dict(section.get("visual", {}))
            visual.update(visual_overrides)
            section["visual"] = visual
            sections[idx] = section

            line_overrides = {}
            for lo_key, lo_val in visual_overrides.items():
                if lo_key.startswith("line_"):
                    line_overrides[lo_key[5:]] = lo_val
            if line_overrides:
                existing_lo = dict(section.get("lines_overrides", {}))
                for li in section.get("lines", []):
                    li_str = str(li)
                    if li_str not in existing_lo:
                        existing_lo[li_str] = {}
                    existing_lo[li_str].update(line_overrides)
                section["lines_overrides"] = existing_lo

    script["sections"] = sections
    return script


def main():
    parser = argparse.ArgumentParser(description="Apply visual profile to script.json")
    parser.add_argument("--project", "-p", required=True, help="Project directory")
    parser.add_argument("--profile", required=True, help="Profile JSON file")
    args = parser.parse_args()

    project_dir = Path(args.project)
    script_path = project_dir / "data" / "script.json"
    profile_path = Path(args.profile)

    if not script_path.exists():
        print(f"Error: {script_path} not found", file=sys.stderr)
        sys.exit(1)
    if not profile_path.exists():
        print(f"Error: {profile_path} not found", file=sys.stderr)
        sys.exit(1)

    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    print(f"  Applying profile from {profile_path.name}...")

    sections = json.loads(script_path.read_text(encoding="utf-8")).get("sections", [])
    print(f"  Script has {len(sections)} sections")

    for key in profile.get("sections", {}):
        indices = _resolve_type_key(sections, key)
        if indices:
            print(f"    '{key}' -> sections {indices}")

    script = apply_profile(script_path, profile)

    backup_path = script_path.with_suffix(".json.bak")
    backup_path.write_text(script_path.read_text(encoding="utf-8"), encoding="utf-8")

    script_path.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Updated {script_path.name} (backup at {backup_path.name})")


if __name__ == "__main__":
    main()
