import json
import zipfile
from pathlib import Path

import numpy as np
import pytest

from audio.ingest import (
    discover_inputs,
    ingest_project,
    _find_audio,
    _find_lyrics,
    _find_stem_zips,
    _find_midi_zips,
    _is_tempo_locked,
    _parse_stem_name,
    _parse_midi_instrument,
    _extract_zip,
)
from pipeline.models import IngestResult


def _write_wav(path, duration=1.0, sr=22050, freq=440.0):
    import soundfile as sf
    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
    sig = (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    sf.write(str(path), sig, sr)


def _make_stem_zip(dest, stem_files=None):
    if stem_files is None:
        stem_files = [
            ("0 Lead Vocals.wav", b"fake0"),
            ("1 Drums.wav", b"fake1"),
            ("2 Bass.wav", b"fake2"),
        ]
    with zipfile.ZipFile(dest, "w") as zf:
        for name, data in stem_files:
            zf.writestr(name, data)
    return dest


def _make_midi_zip(dest, midi_files=None):
    if midi_files is None:
        midi_files = [
            ("Song (Vocals).mid", b"MThdfake"),
            ("Song (Drums).mid", b"MThdfake"),
        ]
    with zipfile.ZipFile(dest, "w") as zf:
        for name, data in midi_files:
            zf.writestr(name, data)
    return dest


class TestFindAudio:
    def test_finds_wav(self, tmp_path):
        _write_wav(tmp_path / "song.wav")
        assert _find_audio(tmp_path) == tmp_path / "song.wav"

    def test_prefers_wav_over_mp3(self, tmp_path):
        _write_wav(tmp_path / "song.wav")
        (tmp_path / "song.mp3").write_bytes(b"fake")
        assert _find_audio(tmp_path) == tmp_path / "song.wav"

    def test_finds_mp3(self, tmp_path):
        (tmp_path / "song.mp3").write_bytes(b"fake")
        assert _find_audio(tmp_path) == tmp_path / "song.mp3"

    def test_empty_dir(self, tmp_path):
        assert _find_audio(tmp_path) is None

    def test_ignores_non_audio(self, tmp_path):
        (tmp_path / "readme.txt").write_text("hi")
        assert _find_audio(tmp_path) is None


class TestFindLyrics:
    def test_finds_txt(self, tmp_path):
        (tmp_path / "lyrics.txt").write_text("hello")
        assert _find_lyrics(tmp_path) == tmp_path / "lyrics.txt"

    def test_finds_srt(self, tmp_path):
        (tmp_path / "lyrics.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nHello")
        assert _find_lyrics(tmp_path) == tmp_path / "lyrics.srt"

    def test_empty_dir(self, tmp_path):
        assert _find_lyrics(tmp_path) is None


class TestFindStemZips:
    def test_finds_stem_zip(self, tmp_path):
        _make_stem_zip(tmp_path / "Song Stems.zip")
        zips = _find_stem_zips(tmp_path)
        assert len(zips) == 1
        assert "Stems" in zips[0].name

    def test_ignores_non_stem_zip(self, tmp_path):
        _make_stem_zip(tmp_path / "other.zip")
        assert _find_stem_zips(tmp_path) == []

    def test_multiple_stem_zips(self, tmp_path):
        _make_stem_zip(tmp_path / "Song Stems.zip")
        _make_stem_zip(tmp_path / "Song Stems (103BPM).zip")
        zips = _find_stem_zips(tmp_path)
        assert len(zips) == 2


class TestFindMidiZips:
    def test_finds_midi_zip(self, tmp_path):
        _make_midi_zip(tmp_path / "Song MIDI.zip")
        zips = _find_midi_zips(tmp_path)
        assert len(zips) == 1

    def test_ignores_non_midi_zip(self, tmp_path):
        _make_stem_zip(tmp_path / "Song Stems.zip")
        assert _find_midi_zips(tmp_path) == []


class TestIsTempoLocked:
    def test_locked(self):
        assert _is_tempo_locked("Song Stems (103BPM).zip") is True

    def test_not_locked(self):
        assert _is_tempo_locked("Song Stems.zip") is False


class TestParseStemName:
    def test_numbered_stem(self):
        idx, name = _parse_stem_name("0 Lead Vocals.wav")
        assert idx == 0
        assert name == "Lead Vocals"

    def test_no_number(self):
        idx, name = _parse_stem_name("vocals.wav")
        assert idx is None
        assert name == "vocals"


class TestParseMidiInstrument:
    def test_parenthetical(self):
        assert _parse_midi_instrument("Song (Vocals).mid") == "Vocals"

    def test_no_parens(self):
        assert _parse_midi_instrument("vocals.mid") == "vocals"


class TestExtractZip:
    def test_extracts_audio_files(self, tmp_path):
        zip_path = tmp_path / "stems.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("0 Vocals.wav", b"fake")
            zf.writestr("readme.txt", b"text")
        dest = tmp_path / "extracted"
        files = _extract_zip(zip_path, dest)
        assert len(files) == 1
        assert files[0].name == "0 Vocals.wav"

    def test_extracts_midi_files(self, tmp_path):
        zip_path = tmp_path / "midi.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("Song (Vocals).mid", b"MThd")
        dest = tmp_path / "extracted"
        files = _extract_zip(zip_path, dest)
        assert len(files) == 1


class TestDiscoverInputs:
    def test_empty_dir(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        result = discover_inputs(empty)
        assert result.tier == "basic"
        assert result.audio_path is None

    def test_nonexistent_dir(self, tmp_path):
        result = discover_inputs(tmp_path / "nonexistent")
        assert result.tier == "basic"

    def test_audio_only(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        _write_wav(d / "song.wav")
        result = discover_inputs(d)
        assert result.audio_path is not None
        assert result.tier == "basic"

    def test_audio_plus_lyrics(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        _write_wav(d / "song.wav")
        (d / "lyrics.txt").write_text("hello")
        result = discover_inputs(d)
        assert result.tier == "standard"
        assert result.audio_path is not None
        assert result.lyrics_path is not None

    def test_audio_lyrics_stems(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        _write_wav(d / "song.wav")
        (d / "lyrics.txt").write_text("hello")
        _make_stem_zip(d / "Song Stems.zip")
        cache = tmp_path / "cache"
        result = discover_inputs(d, cache)
        assert result.tier == "enhanced"
        assert len(result.stems) == 3

    def test_full_tier(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        _write_wav(d / "song.wav")
        (d / "lyrics.txt").write_text("hello")
        _make_stem_zip(d / "Song Stems.zip")
        _make_midi_zip(d / "Song MIDI.zip")
        cache = tmp_path / "cache"
        result = discover_inputs(d, cache)
        assert result.tier == "full"
        assert len(result.stems) == 3
        assert len(result.midi_files) == 2

    def test_tempo_locked_detection(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        _write_wav(d / "song.wav")
        _make_stem_zip(d / "Song Stems.zip")
        _make_stem_zip(d / "Song Stems (103BPM).zip")
        cache = tmp_path / "cache"
        result = discover_inputs(d, cache)
        assert result.has_tempo_locked_stems is True

    def test_prefers_tempo_locked_stems(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        _write_wav(d / "song.wav")
        _make_stem_zip(d / "Song Stems.zip")
        _make_stem_zip(d / "Song Stems (103BPM).zip")
        cache = tmp_path / "cache"
        result = discover_inputs(d, cache)
        assert result.has_tempo_locked_stems is True
        assert len(result.stems) > 0


class TestIngestProject:
    def test_logging(self, tmp_path, caplog):
        import logging
        d = tmp_path / "data"
        d.mkdir()
        _write_wav(d / "song.wav")
        with caplog.at_level(logging.INFO, logger="audio.ingest"):
            result = ingest_project(d)
        assert result.audio_path is not None

    def test_empty(self, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        result = ingest_project(d)
        assert result.tier == "basic"
