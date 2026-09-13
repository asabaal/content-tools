"""WAV -> MIDI transcription backends.

Interface: a backend's `transcribe(audio_path, out_midi, **params)` writes a
MIDI file and returns a provenance record. Basic Pitch is the V0 default;
the interface exists so backends can be benchmarked and swapped
(e.g. future: MT3x, spotify's newer models, custom CQT from music_creation
research — see /mnt/storage/repos/music_creation/study_outputs FINDINGS).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Protocol

from .detectors import sha256_file

logger = logging.getLogger(__name__)


class TranscriptionBackend(Protocol):
    name: str

    def transcribe(self, audio_path: Path, out_midi: Path,
                   **params) -> dict[str, Any]: ...


class BasicPitchBackend:
    """Spotify basic-pitch (ICASSP 2022 model), polyphonic, per-stem friendly."""

    name = "basic_pitch"

    def transcribe(self, audio_path: Path, out_midi: Path, *,
                   onset_threshold: float = 0.5,
                   frame_threshold: float = 0.3,
                   minimum_note_length: float = 100.0,
                   midi_tempo: float = 120.0) -> dict[str, Any]:
        import basic_pitch
        from basic_pitch.inference import predict

        out_midi = Path(out_midi)
        out_midi.parent.mkdir(parents=True, exist_ok=True)
        output, midi_data, note_events = predict(
            str(audio_path),
            onset_threshold=onset_threshold,
            frame_threshold=frame_threshold,
            minimum_note_length=minimum_note_length,
            midi_tempo=midi_tempo,
        )
        midi_data.write(out_midi)

        pitches = [n[2] for n in note_events]
        return {
            "audio": str(audio_path),
            "midi": str(out_midi),
            "note_count": len(note_events),
            "pitch_min": min(pitches) if pitches else None,
            "pitch_max": max(pitches) if pitches else None,
            "provenance": {
                "backend": self.name,
                "model": "basic-pitch ICASSP 2022 (nmp)",
                "basic_pitch_version": getattr(basic_pitch, "__version__", "0.4.0"),
                "params": {"onset_threshold": onset_threshold,
                           "frame_threshold": frame_threshold,
                           "minimum_note_length_ms": minimum_note_length,
                           "midi_tempo": midi_tempo},
                "audio_sha256": sha256_file(Path(audio_path)),
                "outputs": {"onset_matrix": list(output["onset"].shape),
                            "frame_matrix": list(output["frame"].shape) if "frame" in output
                            else list(output["contour"].shape) if "contour" in output
                            else None},
            },
        }


def get_backend(name: str = "basic_pitch") -> TranscriptionBackend:
    if name == "basic_pitch":
        return BasicPitchBackend()
    raise ValueError(f"unknown transcription backend {name!r}; "
                     f"available: basic_pitch")
