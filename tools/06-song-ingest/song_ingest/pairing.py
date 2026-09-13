"""Deterministic WAV-stem <-> reference-MIDI pairing.

The reference MIDIs (e.g. manually extracted Suno MIDI) were exported in the
same order as the WAV stems of the source package. Their filenames carry
that ordinal position: the unnumbered/base MIDI is the first stem,
`(1)` the second, ... `(n)` the (n+1)-th.

Canonical stem order comes from the original export package (the stems
zip's member order) and is cross-checked against the numbered stem
filenames (`N Name.wav`). The resulting mapping is recorded in the
manifest as fact; structural similarity is NEVER used to establish it
(similarity remains useful for comparing our local transcription of a
stem against the reference transcription of the SAME stem).
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any


def ordered_stems_from_zip(zip_path: Path, *, mix_filename: str | None) -> list[Path] | None:
    """Ordered stem paths from the original export package's member order.

    The mix (if present in the package) is excluded — MIDI exports exist
    per stem, not for the full mix. Returns None if the zip is missing.
    Paths returned point at the extracted files in the project directory
    (zip members are flat names; we resolve them next to the zip).
    """
    if not zip_path.is_file():
        return None
    with zipfile.ZipFile(zip_path) as z:
        members = [Path(n).name for n in z.namelist() if not n.endswith("/")]
    stems = []
    for name in members:
        if not re.match(r"^\d+\s+.+\.(wav|mp3|flac)$", name, re.IGNORECASE):
            continue
        if mix_filename and name == mix_filename:
            continue
        candidate = zip_path.parent / name
        if candidate.is_file():
            stems.append(candidate)
    return stems or None


def ordered_stems_from_filenames(stems: dict[str, Path]) -> list[Path]:
    """Fallback: numbered stem filenames `N Name.ext` sorted by N."""
    def sort_key(path: Path) -> int:
        m = re.match(r"^(\d+)\s", path.name)
        return int(m.group(1)) if m else 999
    return sorted(stems.values(), key=sort_key)


def ordered_reference_midis(project_dir: Path) -> list[Path]:
    """Reference MIDIs in export order: unnumbered/base first, then (1)..(n)."""
    def sort_key(path: Path) -> tuple[int, str]:
        m = re.search(r"\((\d+)\)", path.name)
        return (int(m.group(1)) if m else -1, path.name)
    return sorted(project_dir.glob("*.mid"), key=sort_key)


def build_pairing(project_dir: Path, *, stems: dict[str, Path],
                  mix_filename: str | None) -> dict[str, Any]:
    """Produce the canonical, manifest-ready pairing.

    Returns:
      {
        "method": "ordinal export order (base MIDI = first stem)",
        "stem_order_source": "export zip member order" | "numbered filenames",
        "pairs": [ {ordinal, stem_name, stem_path, stem_sha256?,
                    reference_midi, reference_sha256?}, ... ],
        "unpaired": {"stems": [...], "references": [...]},
      }
    """
    from .detectors import sha256_file

    zip_candidates = sorted(project_dir.glob("*.zip"))
    stem_order: list[Path] | None = None
    order_source = "numbered filenames"
    for z in zip_candidates:
        stem_order = ordered_stems_from_zip(z, mix_filename=mix_filename)
        if stem_order and len(stem_order) >= 2:
            order_source = f"export package member order ({z.name})"
            break
    if not stem_order:
        stem_order = ordered_stems_from_filenames(stems)

    refs = ordered_reference_midis(project_dir)

    pairs: list[dict[str, Any]] = []
    used_stems: set[str] = set()
    used_refs: set[str] = set()
    for ordinal, (stem_path, ref_path) in enumerate(
            zip(stem_order, refs)):
        stem_name = next((n for n, p in stems.items() if p == stem_path),
                         stem_path.stem)
        pairs.append({
            "ordinal": ordinal,
            "stem_name": stem_name,
            "stem_path": str(stem_path),
            "reference_midi": ref_path.name,
            "reference_path": str(ref_path),
        })
        used_stems.add(stem_name)
        used_refs.add(ref_path.name)

    result: dict[str, Any] = {
        "method": "ordinal export order (base MIDI = first stem, "
                  "(1) = second, ...)",
        "stem_order_source": order_source,
        "canonical": True,
        "pairs": pairs,
        "unpaired": {
            "stems": sorted(set(stems) - used_stems),
            "references": sorted(r.name for r in refs
                                 if r.name not in used_refs),
        },
    }
    # sha256 the small reference MIDIs (not the huge WAVs) for the manifest
    for pair in pairs:
        ref = project_dir / pair["reference_midi"]
        if ref.is_file():
            pair["reference_sha256"] = sha256_file(ref)
    return result
