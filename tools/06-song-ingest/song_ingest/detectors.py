"""Instrument detection backends.

Interface: a Detector returns, for one audio file:

    {
      "clipwise": [{"label": str, "confidence": float}, ...],   # song-level
      "temporal": [{"label": str, "start": s, "end": s,
                    "confidence": float, "peak": float}, ...],  # time-localized
      "provenance": {"detector": str, "model": str, "device": str,
                     "params": {...}, "audio_sha256": str},
    }

V0 backend: PANNs Cnn14 (panns-inference, PyTorch/CUDA) — 527 AudioSet
classes, multi-label. panns-inference's AudioTagging exposes no framewise
output, so temporal evidence comes from sliding 10 s windows (hop 5 s)
through the same checkpoint — no second model needed.
Planned future backends behind the same interface: Essentia MTG-Jamendo
instrumentation (multi-label, instrument-focused; needs TensorFlow) and CLAP
(open-vocabulary validation; needs transformers). Neither is installed yet.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import numpy as np

logger = logging.getLogger(__name__)

TARGET_SR = 32000          # PANNs Cnn14 expects 32 kHz
WINDOW_SECONDS = 10
HOP_SECONDS = 5


def sha256_file(path: Path, *, buf: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(buf):
            h.update(chunk)
    return h.hexdigest()


def load_audio_mono(path: Path) -> tuple[np.ndarray, int]:
    """Load any supported audio file as mono float32 at TARGET_SR."""
    import soundfile as sf
    import librosa

    y, sr = sf.read(path, dtype="float32", always_2d=True)
    mono = y.mean(axis=1)
    if sr != TARGET_SR:
        mono = librosa.resample(mono, orig_sr=sr, target_sr=TARGET_SR)
    np.clip(mono, -1.0, 1.0, out=mono)
    return mono.astype(np.float32), TARGET_SR


@dataclass
class TemporalSegment:
    label: str
    start: float
    end: float
    confidence: float   # mean prob over the segment
    peak: float         # max prob within the segment

    def to_dict(self) -> dict:
        return {"label": self.label, "start": round(self.start, 2),
                "end": round(self.end, 2),
                "confidence": round(self.confidence, 4),
                "peak": round(self.peak, 4)}


class Detector(Protocol):
    name: str

    def detect(self, audio_path: Path, *, top_k: int = 15,
               temporal_threshold: float = 0.3,
               min_segment_seconds: float = 2.0) -> dict[str, Any]: ...


# ---- label mapping ------------------------------------------------------------

# Curated AudioSet/PANNs label fragments -> canonical instrument vocabulary
# used by reconciliation. Matching is lowercase substring on the raw label.
CANONICAL_FRAGMENTS: dict[str, str] = {
    "guitar": "guitar", "bass guitar": "bass", "bass (instrument)": "bass",
    "drum": "drums", "percussion": "percussion", "cymbal": "percussion",
    "snare": "drums", "bass drum": "drums",
    "piano": "piano", "organ": "organ", "harpsichord": "keys",
    "keyboard": "keys",
    "string section": "strings", "violin": "strings", "cello": "strings",
    "viola": "strings", "double bass": "bass", "harp": "strings",
    "brass": "brass", "trumpet": "brass", "trombone": "brass",
    "horn": "brass", "tuba": "brass", "french horn": "brass",
    "woodwind": "woodwinds", "flute": "woodwinds", "clarinet": "woodwinds",
    "saxophone": "woodwinds", "oboe": "woodwinds", "bassoon": "woodwinds",
    "singing": "vocals", "vocal": "vocals", "choir": "vocals", "voice": "vocals",
    "synthesizer": "synth", "synth": "synth", "sampler": "synth",
    "fx": "fx", "effect": "fx",
}


def canonicalize(label: str) -> str | None:
    low = label.lower()
    for fragment, canonical in CANONICAL_FRAGMENTS.items():
        if fragment in low:
            return canonical
    return None


def aggregate_canonical(clipwise: list[dict]) -> dict[str, float]:
    """Collapse raw AudioSet classes into the canonical vocabulary by taking
    the max confidence per canonical instrument."""
    best: dict[str, float] = {}
    for item in clipwise:
        canon = canonicalize(item["label"])
        if canon:
            best[canon] = max(best.get(canon, 0.0), item["confidence"])
    return dict(sorted(best.items(), key=lambda kv: -kv[1]))


# ---- PANNs backend --------------------------------------------------------------

@dataclass
class PannsDetector:
    """PANNs Cnn14 backend: whole-file clipwise + windowed temporal evidence."""
    device: str = "auto"           # "auto" | "cuda" | "cpu"
    name: str = "panns_cnn14"
    _tagger: Any = field(default=None, repr=False)

    def _get_tagger(self):
        if self._tagger is None:
            from panns_inference import AudioTagging
            device = self.device
            if device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("loading PANNs Cnn14 on %s", device)
            self._tagger = AudioTagging(checkpoint_path=None, device=device)
        return self._tagger

    def detect(self, audio_path: Path, *, top_k: int = 15,
               temporal_threshold: float = 0.3,
               min_segment_seconds: float = 2.0) -> dict[str, Any]:
        """Song-level (clipwise) + time-localized evidence.

        Temporal evidence comes from sliding 10 s windows (hop 5 s) through
        the same Cnn14 — panns-inference's AudioTagging exposes no framewise
        output, and this avoids a second checkpoint.
        """
        import torch

        waveform, sr = load_audio_mono(Path(audio_path))
        tagger = self._get_tagger()
        labels = list(tagger.labels)

        # --- song-level clipwise (whole file) ---
        with torch.no_grad():
            clip, _ = tagger.inference(waveform[None, :])
        clip = clip[0]

        order = np.argsort(-clip)[:top_k]
        clipwise_out = [{"label": labels[i],
                         "confidence": round(float(clip[i]), 4)}
                        for i in order]

        # --- temporal curves via sliding windows through the same model ---
        win = WINDOW_SECONDS * sr
        hop = HOP_SECONDS * sr
        starts = list(range(0, max(len(waveform) - win, 0) + 1, hop)) or [0]
        curves = np.zeros((len(starts), len(labels)), dtype=np.float32)
        batch = 8
        with torch.no_grad():
            for i in range(0, len(starts), batch):
                chunk = starts[i:i + batch]
                x = np.stack([
                    np.pad(waveform[s:s + win],
                           (0, max(0, win - len(waveform[s:s + win]))))
                    for s in chunk])
                out = tagger.model(torch.from_numpy(x).to(tagger.device), None)
                curves[i:i + len(chunk)] = \
                    out["clipwise_output"].cpu().numpy()

        duration = len(waveform) / sr
        temporal_out: list[dict] = []
        for i in order:
            probs = curves[:, i]          # probability per window center
            above = probs >= temporal_threshold
            if not above.any():
                continue
            runs = []
            in_run = False
            run_start = 0
            for idx, a in enumerate(above):
                if a and not in_run:
                    run_start, in_run = idx, True
                elif not a and in_run:
                    runs.append((run_start, idx))
                    in_run = False
            if in_run:
                runs.append((run_start, len(above)))
            for rs, re in runs:
                seg = probs[rs:re]
                seg_start = max(0.0, starts[rs] / sr)
                seg_end = min(duration, (starts[re - 1] + win) / sr)
                if seg_end - seg_start < min_segment_seconds:
                    continue
                temporal_out.append(TemporalSegment(
                    label=labels[i], start=seg_start, end=seg_end,
                    confidence=float(seg.mean()), peak=float(seg.max()),
                ).to_dict())
        temporal_out.sort(key=lambda d: -d["confidence"])

        return {
            "file": str(audio_path),
            "duration_seconds": round(duration, 2),
            "clipwise": clipwise_out,
            "canonical": aggregate_canonical(clipwise_out),
            "temporal": temporal_out[:40],
            "provenance": {
                "detector": self.name,
                "model": "PANNs Cnn14 (AudioSet-527), panns-inference",
                "device": str(tagger.device),
                "params": {"top_k": top_k,
                           "temporal_threshold": temporal_threshold,
                           "min_segment_seconds": min_segment_seconds,
                           "window_seconds": WINDOW_SECONDS,
                           "hop_seconds": HOP_SECONDS,
                           "target_sr": TARGET_SR, "mono": True},
                "audio_sha256": sha256_file(Path(audio_path)),
            },
        }


def get_detector(name: str = "panns_cnn14", **kwargs) -> Detector:
    if name == "panns_cnn14":
        return PannsDetector(**kwargs)
    raise ValueError(f"unknown detector backend {name!r}; available: "
                     f"panns_cnn14 (planned: essentia_mtg_jamendo, clap)")
