import pretty_midi
import pytest
from pathlib import Path

from audio.midi import MidiNote, MidiInstrument, MidiAnalysis, analyze_midi, extract_tempo


class TestMidiNote:
    def test_duration(self):
        n = MidiNote(pitch=60, start=1.0, end=2.0, velocity=100)
        assert n.duration == 1.0

    def test_to_dict(self):
        n = MidiNote(pitch=60, start=1.0, end=2.0, velocity=100)
        d = n.to_dict()
        assert d["pitch"] == 60
        assert d["start"] == 1.0
        assert d["end"] == 2.0
        assert d["velocity"] == 100


class TestMidiInstrument:
    def test_to_dict(self):
        notes = [MidiNote(pitch=60, start=0.0, end=1.0, velocity=80)]
        inst = MidiInstrument(name="Piano", program=0, notes=notes)
        d = inst.to_dict()
        assert d["name"] == "Piano"
        assert d["program"] == 0
        assert d["note_count"] == 1
        assert len(d["notes"]) == 1


class TestMidiAnalysis:
    def test_to_dict(self):
        a = MidiAnalysis(source_file="test.mid", tempo=120.0, duration=30.0)
        d = a.to_dict()
        assert d["source_file"] == "test.mid"
        assert d["tempo"] == 120.0
        assert d["duration"] == 30.0

    def test_to_dict_with_instruments(self):
        inst = MidiInstrument(name="Piano", program=0)
        a = MidiAnalysis(source_file="test.mid", instruments=[inst])
        d = a.to_dict()
        assert len(d["instruments"]) == 1


class TestAnalyzeMidi:
    def test_analyze_real_midi(self, tmp_path):
        pm = pretty_midi.PrettyMIDI(initial_tempo=120.0)
        inst = pretty_midi.Instrument(program=0)
        inst.notes.append(pretty_midi.Note(velocity=100, pitch=60, start=0.0, end=1.0))
        inst.notes.append(pretty_midi.Note(velocity=80, pitch=64, start=1.0, end=2.0))
        pm.instruments.append(inst)

        midi_path = tmp_path / "test.mid"
        pm.write(str(midi_path))

        result = analyze_midi(midi_path)
        assert result.tempo is not None
        assert result.duration > 0
        assert len(result.instruments) == 1
        assert result.instruments[0].note_count == 2
        assert result.source_file == "test.mid"

    def test_analyze_midi_drums(self, tmp_path):
        pm = pretty_midi.PrettyMIDI(initial_tempo=100.0)
        inst = pretty_midi.Instrument(program=0, is_drum=True)
        inst.notes.append(pretty_midi.Note(velocity=100, pitch=36, start=0.0, end=0.5))
        pm.instruments.append(inst)

        midi_path = tmp_path / "drums.mid"
        pm.write(str(midi_path))

        result = analyze_midi(midi_path)
        assert result.instruments[0].name == "Drums"


class TestExtractTempo:
    def test_extract_tempo(self, tmp_path):
        pm = pretty_midi.PrettyMIDI(initial_tempo=103.8)
        midi_path = tmp_path / "test.mid"
        pm.write(str(midi_path))

        tempo = extract_tempo(midi_path)
        assert tempo is not None
        assert abs(tempo - 103.8) < 1.0

    def test_extract_tempo_missing_file(self):
        tempo = extract_tempo("/nonexistent/file.mid")
        assert tempo is None
