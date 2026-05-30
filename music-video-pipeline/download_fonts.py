#!/usr/bin/env python3
"""
Download and register Google Fonts for the music video pipeline.
"""

import json
import shutil
from pathlib import Path

FONTS_DIR = Path(__file__).parent / "fonts"
REPO_DIR = Path("/mnt/storage/tmp/opencode/google-fonts")
REGISTRY_PATH = Path(__file__).parent / "src" / "render" / "font_registry.json"

EXISTING_FONTS = {"Exo2", "Bangers", "BebasNeue", "JetBrainsMono", "Lora", "Oswald"}

CATEGORY_MAP = {
    "SANS_SERIF": "sans",
    "SERIF": "serif",
    "DISPLAY": "display",
    "HANDWRITING": "handwriting",
    "MONOSPACE": "mono",
}

SKIP_FONT_NAMES = {
    "Noto Sans", "Noto Serif",  # These are massive CJK font families
}


def parse_metadata(meta_path: Path) -> dict | None:
    if not meta_path.exists():
        return None

    text = meta_path.read_text(encoding="utf-8", errors="ignore")
    info = {"category": "SANS_SERIF", "has_latin": False, "fonts": []}

    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("category:"):
            val = line.split('"')
            if len(val) >= 2:
                info["category"] = val[1]
        elif line.startswith("name:"):
            if "name" not in info or info.get("name") is None:
                val = line.split('"')
                if len(val) >= 2:
                    info["name"] = val[1]
        elif line.startswith("subsets:"):
            if '"latin"' in line:
                info["has_latin"] = True
        elif line.startswith("filename:"):
            val = line.split('"')
            if len(val) >= 2:
                info["fonts"].append(val[1])

    return info


def find_bold_regular(font_files: list[str]) -> tuple[str, str]:
    bold = None
    regular = None

    for f in font_files:
        lower = f.lower()
        if any(w in lower for w in ["bold", "black", "extrabold", "semibold", "heavy"]):
            if bold is None:
                bold = f
        elif "medium" not in lower:
            if regular is None:
                regular = f

    if regular is None:
        regular = font_files[0] if font_files else None
    if bold is None:
        bold = regular

    return bold, regular


def process_fonts():
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    ofl_dir = REPO_DIR / "ofl"

    registry = {}
    font_id = 1

    # Register existing fonts
    for name in sorted(EXISTING_FONTS):
        existing_files = list(FONTS_DIR.glob(f"{name}*.ttf"))
        bold = regular = None
        for f in existing_files:
            if "Bold" in f.name:
                bold = f.name
            elif regular is None:
                regular = f.name
        if not bold:
            bold = regular
        if not regular:
            continue
        registry[name] = {
            "id": font_id,
            "bold": bold,
            "regular": regular,
            "category": "sans",
        }
        font_id += 1

    font_dirs = sorted([d for d in ofl_dir.iterdir() if d.is_dir()])
    total = len(font_dirs)
    copied = 0
    skipped_no_latin = 0
    skipped_no_ttf = 0

    for i, font_dir in enumerate(font_dirs):
        dirname = font_dir.name
        if dirname.lower() in {e.lower() for e in EXISTING_FONTS}:
            continue

        meta = parse_metadata(font_dir / "METADATA.pb")

        if meta and not meta.get("has_latin"):
            skipped_no_latin += 1
            continue

        category = meta.get("category", "SANS_SERIF") if meta else "SANS_SERIF"
        font_name = meta.get("name", dirname) if meta else dirname

        if font_name in SKIP_FONT_NAMES:
            continue

        # Find all TTF files in the directory
        ttfs = sorted(font_dir.glob("*.ttf"))
        if not ttfs:
            skipped_no_ttf += 1
            continue

        font_files = [t.name for t in ttfs]
        bold, regular = find_bold_regular(font_files)

        if not regular:
            skipped_no_ttf += 1
            continue

        # Copy TTF files
        for ttf in ttfs:
            dst = FONTS_DIR / ttf.name
            if not dst.exists():
                shutil.copy2(ttf, dst)

        registry[font_name] = {
            "id": font_id,
            "bold": bold,
            "regular": regular,
            "category": CATEGORY_MAP.get(category, "sans"),
        }
        font_id += 1
        copied += 1

        if (i + 1) % 200 == 0:
            print(f"  Processed {i + 1}/{total} (copied {copied}, skipped {skipped_no_latin + skipped_no_ttf})")

    print(f"\nDone: {copied} fonts copied")
    print(f"  Skipped (no Latin): {skipped_no_latin}")
    print(f"  Skipped (no TTF): {skipped_no_ttf}")
    print(f"Total registry: {len(registry)} fonts")

    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)
    print(f"Registry saved to {REGISTRY_PATH}")

    cats = {}
    for info in registry.values():
        cat = info["category"]
        cats[cat] = cats.get(cat, 0) + 1
    print("\nCategory counts:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    return registry


if __name__ == "__main__":
    process_fonts()
