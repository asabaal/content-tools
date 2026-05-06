from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MidiNote:
    pitch: int
    start: float
    end: float
    velocity: int

    @property
    def duration(self) -> float:
        return self.end - self.start

    def to_dict(self) -> dict:
        return {"pitch": self.pitch, "start": round(self.start, 3), "end": round(self.end, 3), "velocity": self.velocity}


@dataclass
class MidiInstrument:
    name: str
    program: int
    notes: list = field(default_factory=list)

    @property
    def note_count(self) -> int:
        return len(self.notes)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "program": self.program,
            "note_count": self.note_count,
            "notes": [n.to_dict() for n in self.notes],
        }


@dataclass
class MidiAnalysis:
    source_file: str
    tempo: Optional[float] = None
    duration: float = 0.0
    instruments: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "tempo": self.tempo,
            "duration": self.duration,
            "instruments": [i.to_dict() for i in self.instruments],
        }


def analyze_midi(midi_path: str | Path) -> MidiAnalysis:
    try:
        import pretty_midi
    except ImportError:
        logger.warning("pretty_midi not installed, skipping MIDI analysis")
        return MidiAnalysis(source_file=str(midi_path))

    midi_path = Path(midi_path)
    logger.info("Analyzing MIDI: %s", midi_path)

    pm = pretty_midi.PrettyMIDI(str(midi_path))

    tempo_changes, tempos = pm.get_tempo_changes()
    tempo = float(tempos[0]) if len(tempos) > 0 else None

    instruments = []
    for inst in pm.instruments:
        notes = [
            MidiNote(pitch=n.pitch, start=n.start, end=n.end, velocity=n.velocity)
            for n in inst.notes
        ]
        instruments.append(
            MidiInstrument(
                name=pretty_midi.program_to_instrument_name(inst.program) if not inst.is_drum else "Drums",
                program=inst.program,
                notes=notes,
            )
        )

    return MidiAnalysis(
        source_file=midi_path.name,
        tempo=tempo,
        duration=pm.get_end_time(),
        instruments=instruments,
    )


def extract_tempo(midi_path: str | Path) -> Optional[float]:
    try:
        result = analyze_midi(midi_path)
        return result.tempo
    except Exception:
        return None
