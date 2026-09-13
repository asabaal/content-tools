"""Vocal/lyric transcription.

Reuses the existing content-tools vocal transcription path:
`music-video-pipeline/src/audio/analyzer.py::AudioAnalyzer.transcribe_vocal_stem`
(faster-whisper with word timestamps and hallucination filtering).
Raw model output is preserved verbatim; reconciliation with known lyrics is
a separate, later artifact.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MVP_SRC = _REPO_ROOT / "music-video-pipeline" / "src"


def _analyzer():
    if str(_MVP_SRC) not in sys.path:
        sys.path.insert(0, str(_MVP_SRC))
    from audio.analyzer import AudioAnalyzer
    return AudioAnalyzer()


def mix_wavs(paths: list[Path], out_path: Path) -> Path:
    """Sum several vocal stems into one 'combined vocals' wav (normalized)."""
    import numpy as np
    import soundfile as sf

    arrays, sr = [], None
    for p in paths:
        y, sr = sf.read(p, dtype="float32", always_2d=True)
        arrays.append(y)
    n = min(len(a) for a in arrays)
    mix = sum(a[:n] for a in arrays) / len(arrays)
    peak = np.max(np.abs(mix)) or 1.0
    if peak > 1.0:
        mix = mix / peak
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out_path, mix, sr)
    return out_path


def transcribe_vocals(stem_paths: dict[str, Path], out_dir: Path, *,
                      model_size: str = "small") -> dict[str, Any]:
    """Transcribe each named vocal stem. `stem_paths` values may be real
    stems or the combined-vocals wav produced by `mix_wavs`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    analyzer = _analyzer()
    results: dict[str, Any] = {}
    for name, path in stem_paths.items():
        logger.info("transcribing vocals: %s (%s)", name, path)
        raw = analyzer.transcribe_vocal_stem(str(path), model_size=model_size)
        out_file = out_dir / f"{name}.json"
        out_file.write_text(json_str({
            "source_stem": str(path),
            "model": {"type": "faster-whisper", "size": model_size},
            "raw_segments": raw.get("segments", []),
            "language": raw.get("language"),
            "note": "raw model output, preserved verbatim; lyric "
                    "reconciliation (if known lyrics exist) is a separate "
                    "downstream artifact",
        }))
        results[name] = {
            "segments": len(raw.get("segments", [])),
            "words": sum(len(s.get("words", []))
                         for s in raw.get("segments", [])),
            "output": str(out_file),
        }
    return results


def json_str(obj) -> str:
    import json
    return json.dumps(obj, indent=2, default=str)
