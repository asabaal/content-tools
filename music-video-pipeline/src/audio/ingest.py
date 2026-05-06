from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path
from typing import Optional

from pipeline.models import (
    IngestResult,
    InputTier,
    StemInfo,
    MidiFileInfo,
    SUPPORTED_AUDIO,
    SUPPORTED_LYRICS,
    SUPPORTED_MIDI,
)

logger = logging.getLogger(__name__)

STEM_NAME_PATTERN = re.compile(r"^(\d+)\s+(.+)\.(wav|mp3)$", re.IGNORECASE)
MIDI_NAME_PATTERN = re.compile(r"^(.+)\((.+)\)\.(mid|midi)$", re.IGNORECASE)
TEMPO_LOCKED_PATTERN = re.compile(r"\(\d+\s*BPM\)", re.IGNORECASE)
ZIP_PATTERN = re.compile(r"\.zip$", re.IGNORECASE)


def _find_audio(directory: Path) -> Optional[Path]:
    candidates = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() in SUPPORTED_AUDIO:
            candidates.append(f)
    if not candidates:
        return None
    for pref in [".wav", ".flac"]:
        for c in candidates:
            if c.suffix.lower() == pref:
                return c
    return candidates[0]


def _find_lyrics(directory: Path) -> Optional[Path]:
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() in SUPPORTED_LYRICS:
            return f
    return None


def _find_stem_zips(directory: Path) -> list[Path]:
    results = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() == ".zip" and "stem" in f.name.lower():
            results.append(f)
    return results


def _find_midi_zips(directory: Path) -> list[Path]:
    results = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() == ".zip" and "midi" in f.name.lower():
            results.append(f)
    return results


def _is_tempo_locked(name: str) -> bool:
    return bool(TEMPO_LOCKED_PATTERN.search(name))


def _extract_zip(zip_path: Path, dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    extracted = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            if Path(info.filename).suffix.lower() not in SUPPORTED_AUDIO | SUPPORTED_MIDI:
                continue
            zf.extract(info, dest_dir)
            extracted.append(dest_dir / info.filename)
    return extracted


def _parse_stem_name(filename: str) -> tuple[Optional[int], str]:
    m = STEM_NAME_PATTERN.match(filename)
    if m:
        return int(m.group(1)), m.group(2)
    return None, Path(filename).stem


def _parse_midi_instrument(filename: str) -> str:
    m = MIDI_NAME_PATTERN.match(filename)
    if m:
        return m.group(2).strip()
    return Path(filename).stem


def discover_inputs(data_dir: Path, cache_dir: Optional[Path] = None) -> IngestResult:
    if not data_dir.exists():
        return IngestResult(tier=InputTier.BASIC.value)

    if cache_dir is None:
        cache_dir = data_dir / "cache"

    audio = _find_audio(data_dir)
    lyrics = _find_lyrics(data_dir)

    stems = []
    midi_files = []
    has_tempo_locked = False

    stem_zips = _find_stem_zips(data_dir)
    preferred_zip = None
    for z in stem_zips:
        if _is_tempo_locked(z.name):
            has_tempo_locked = True
            if preferred_zip is None:
                preferred_zip = z
    if preferred_zip is None and stem_zips:
        preferred_zip = stem_zips[0]

    if preferred_zip is not None:
        stem_cache = cache_dir / "stems"
        extracted = _extract_zip(preferred_zip, stem_cache)
        for f in extracted:
            idx, name = _parse_stem_name(f.name)
            stem_type = name.lower().replace(" ", "_")
            stems.append(
                StemInfo(
                    name=name,
                    stem_type=stem_type,
                    path=str(f),
                    format=f.suffix.lower().lstrip("."),
                )
            )

    midi_zips = _find_midi_zips(data_dir)
    if midi_zips:
        midi_cache = cache_dir / "midi"
        extracted = _extract_zip(midi_zips[0], midi_cache)
        for f in extracted:
            instrument = _parse_midi_instrument(f.name)
            midi_files.append(
                MidiFileInfo(
                    name=f.name,
                    path=str(f),
                    instrument=instrument,
                )
            )

    if audio is not None and lyrics is not None and stems and midi_files:
        tier = InputTier.FULL.value
    elif audio is not None and lyrics is not None and stems:
        tier = InputTier.ENHANCED.value
    elif audio is not None and lyrics is not None:
        tier = InputTier.STANDARD.value
    else:
        tier = InputTier.BASIC.value

    return IngestResult(
        tier=tier,
        audio_path=str(audio) if audio else None,
        lyrics_path=str(lyrics) if lyrics else None,
        stems=stems,
        midi_files=midi_files,
        has_tempo_locked_stems=has_tempo_locked,
    )


def ingest_project(data_dir: Path, project_cache_dir: Optional[Path] = None) -> IngestResult:
    result = discover_inputs(data_dir, project_cache_dir)

    logger.info("Ingest complete: tier=%s", result.tier)
    logger.info("  Audio: %s", result.audio_path or "none")
    logger.info("  Lyrics: %s", result.lyrics_path or "none")
    logger.info("  Stems: %d", len(result.stems))
    logger.info("  MIDI: %d", len(result.midi_files))
    logger.info("  Tempo-locked: %s", result.has_tempo_locked_stems)

    return result
