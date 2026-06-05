import json
import zipfile
from pathlib import Path

import numpy as np
import pytest
from click.testing import CliRunner

from cli.commands import cli
from pipeline.models import MusicVideoProject


@pytest.fixture
def runner():
    return CliRunner()


def _write_wav(path, duration=1.0, sr=22050, freq=440.0):
    import soundfile as sf
    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
    sig = (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    sf.write(str(path), sig, sr)


class TestAnalyzerEdgeCases:
    def test_confidence_zero_with_beats(self, tmp_path):
        import soundfile as sf
        sr = 22050
        dur = 2.0
        t = np.linspace(0, dur, int(sr * dur), endpoint=False, dtype=np.float32)
        sig = np.zeros_like(t)
        sig[0:100] = 0.3 * np.sin(2 * np.pi * 440 * np.arange(100) / sr).astype(np.float32)
        sig[int(sr):int(sr) + 100] = 0.3 * np.sin(2 * np.pi * 440 * np.arange(100) / sr).astype(np.float32)
        p = tmp_path / "beats.wav"
        sf.write(str(p), sig, sr)
        from audio.analyzer import AudioAnalyzer
        a = AudioAnalyzer()
        features = a.analyze(p)
        assert features.duration > 0

    def test_waveform_empty_chunk(self, tmp_path):
        import soundfile as sf
        sr = 22050
        sig = np.array([0.1], dtype=np.float32)
        p = tmp_path / "tiny.wav"
        sf.write(str(p), sig, sr)
        from audio.analyzer import AudioAnalyzer
        a = AudioAnalyzer()
        a.load_audio(p)
        peaks, dur = a.generate_waveforms()
        assert dur > 0
        assert isinstance(peaks, list)


class TestIngestEdgeCases:
    def test_extract_zip_skips_non_audio(self, tmp_path):
        from audio.ingest import _extract_zip
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("readme.txt", "text")
            zf.writestr("0 Vocals.wav", b"fake")
        dest = tmp_path / "out"
        files = _extract_zip(zip_path, dest)
        assert len(files) == 1
        assert files[0].name == "0 Vocals.wav"

    def test_extract_zip_skips_dirs(self, tmp_path):
        from audio.ingest import _extract_zip
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("subdir/", "")
            zf.writestr("subdir/file.wav", b"fake")
        dest = tmp_path / "out"
        files = _extract_zip(zip_path, dest)
        assert len(files) == 1


class TestMidiEdgeCases:
    def test_analyze_without_pretty_midi(self, tmp_path, monkeypatch):
        import audio.midi as midi_mod
        import importlib
        import sys

        import pretty_midi as _pm
        pm_mod = sys.modules["pretty_midi"]
        sys.modules["pretty_midi"] = None

        try:
            importlib.reload(midi_mod)
            result = midi_mod.analyze_midi(tmp_path / "fake.mid")
            assert result.tempo is None
        finally:
            sys.modules["pretty_midi"] = pm_mod
            importlib.reload(midi_mod)


class TestParserEdgeCases:
    def test_parse_plain_text_continue_on_section(self, tmp_path):
        from lyrics.parser import LyricParser
        p = tmp_path / "test.txt"
        p.write_text("[Section]\nline one\nline two\n[Another Section]\nline three")
        parser = LyricParser()
        lines, sections = parser._parse_plain_text(p.read_text())
        assert len(lines) == 3
        assert len(sections) == 2


class TestCLIWithIngest:
    def test_analyze_with_stems_in_ingest(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])

        stem_wav = tmp_path / "stem.wav"
        _write_wav(stem_wav)
        stem_zip = tmp_path / "stems.zip"
        with zipfile.ZipFile(stem_zip, "w") as zf:
            zf.write(str(stem_wav), "0 Drums.wav")

        ingest = {
            "tier": "enhanced",
            "audio_path": str(wav),
            "lyrics_path": None,
            "stems": [{"name": "Drums", "stem_type": "drums", "path": str(stem_wav), "format": "wav"}],
            "midi_files": [],
            "has_tempo_locked_stems": False,
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest))

        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "Stems analyzed" in result.output

    def test_analyze_with_midi_in_ingest(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])

        import pretty_midi
        pm = pretty_midi.PrettyMIDI(initial_tempo=103.8)
        inst = pretty_midi.Instrument(program=0)
        inst.notes.append(pretty_midi.Note(velocity=100, pitch=60, start=0.0, end=1.0))
        pm.instruments.append(inst)
        midi_path = tmp_path / "test.mid"
        pm.write(str(midi_path))

        ingest = {
            "tier": "full",
            "audio_path": str(wav),
            "lyrics_path": None,
            "stems": [],
            "midi_files": [{"name": "test.mid", "path": str(midi_path), "instrument": "Vocals", "note_count": 1, "duration": 1.0}],
            "has_tempo_locked_stems": False,
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest))

        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "from MIDI" in result.output

    def test_init_with_data_dir_and_ingest(self, runner, tmp_path, suno_data_dir):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--data-dir", str(suno_data_dir), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert (tmp_path / "data" / "ingest.json").exists()

    def test_info_midi_bpm_display(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])

        proj = MusicVideoProject.load(tmp_path)
        proj.audio_info = type(proj.audio_info)(
            duration=10.0, bpm=103.8, midi_bpm=103.8, sample_rate=22050, beat_count=20, onset_count=40
        )
        proj.stages.mark_complete("analyze")
        proj.save()

        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "from MIDI" in result.output

    def test_info_bpm_no_midi(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])

        proj = MusicVideoProject.load(tmp_path)
        proj.audio_info = type(proj.audio_info)(duration=10.0, bpm=120.0, sample_rate=22050, beat_count=20, onset_count=40)
        proj.stages.mark_complete("analyze")
        proj.save()

        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "BPM: 120" in result.output

    def test_cli_main_entry_point(self, tmp_path):
        from cli.commands import cli
        assert cli is not None

    def test_ingest_no_audio_no_data_dir(self, runner, tmp_path):
        result = runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        assert result.exit_code == 0

    def test_ingest_scan_dir_does_not_exist(self, runner, tmp_path):
        result = runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        assert result.exit_code == 0

    def test_ingest_data_dir_deleted_after_init(self, runner, tmp_path):
        d = tmp_path / "external_data"
        d.mkdir()
        _write_wav(d / "song.wav")
        (d / "lyrics.txt").write_text("hello")
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--data-dir", str(d), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        import shutil
        shutil.rmtree(d)
        proj = MusicVideoProject.load(tmp_path)
        from cli.commands import _run_ingest
        result = _run_ingest(proj)
        assert result is None

    def test_ingest_with_tempo_locked(self, runner, tmp_path):
        d = tmp_path / "suno"
        d.mkdir()
        _write_wav(d / "song.wav")
        (d / "lyrics.txt").write_text("[Intro]\nHello\n")
        stem_zip = d / "Song Stems (103BPM).zip"
        with zipfile.ZipFile(stem_zip, "w") as zf:
            zf.writestr("readme.txt", "ignore")

        result = runner.invoke(
            cli, ["init", "--name", "Test", "--data-dir", str(d), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        ingest_data = json.loads((tmp_path / "data" / "ingest.json").read_text())
        assert ingest_data["has_tempo_locked_stems"] is True

    def test_analyze_no_ingest_file(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])
        (tmp_path / "data" / "ingest.json").unlink(missing_ok=True)
        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code == 0

    def test_lyrics_import_returns_early(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])
        proj = MusicVideoProject.load(tmp_path)
        proj.paths.lyrics = None
        proj.save()
        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code == 0

    def test_lyrics_import_none_direct(self, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        proj = MusicVideoProject.create(project_dir=tmp_path / "proj", name="Test", audio_path=wav)
        proj.paths.lyrics = None
        from cli.commands import _run_lyrics_import
        _run_lyrics_import(proj)

    def test_info_bpm_no_audio_info(self, runner, tmp_path):
        result = runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        proj = MusicVideoProject.load(tmp_path)
        proj.stages.mark_complete("analyze")
        proj.save()
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "not analyzed" in result.output

    def test_cwd_project_discovery(self, runner, tmp_path):
        import os
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])
        old_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            result = runner.invoke(cli, ["info"])
            assert result.exit_code == 0
            assert "Test" in result.output
        finally:
            os.chdir(old_cwd)

    def test_cwd_no_project_raises(self, runner, tmp_path):
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            result = runner.invoke(cli, ["info"])
            assert result.exit_code != 0
        finally:
            os.chdir(old_cwd)

    def test_cli_main_block(self):
        import subprocess
        import sys
        r = subprocess.run(
            [sys.executable, "src/cli/commands.py"],
            capture_output=True, text=True,
            cwd="/mnt/storage/repos/content-tools/music-video-pipeline",
        )
        assert "Usage" in r.stdout or "Usage" in r.stderr


class TestSrtEmptyText:
    def test_srt_valid_timing_empty_text_after_strip(self, tmp_path):
        content = "1\n00:00:01,000 --> 00:00:02,000\n   \n\n2\n00:00:03,000 --> 00:00:04,000\nHello"
        p = tmp_path / "test.srt"
        p.write_text(content)
        from lyrics.parser import LyricParser
        result = LyricParser().parse_file(p)
        assert result.total_lines == 1
        assert result.lines[0].text == "Hello"


class TestFormatDurationEdgeCases:
    def test_format_duration_over_60_minutes(self):
        from cli.commands import _format_duration
        assert _format_duration(3661) == "1:01:01"

    def test_format_duration_minutes(self):
        from cli.commands import _format_duration
        assert _format_duration(125) == "2:05"


class TestCommandCoverageGaps:
    def test_stem_truncation_and_empty_path(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav, duration=2.0)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])

        stem_dir = tmp_path / "data" / "cache" / "stems"
        stem_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(stem_dir / "short_vocal.wav", duration=0.1, sr=22050)
        corrupt = stem_dir / "corrupt.wav"
        corrupt.write_bytes(b"not_a_wav")

        ingest_data = {
            "tier": "enhanced",
            "stems": [
                {"name": "Missing", "stem_type": "vocals", "path": "", "format": "wav"},
                {"name": "Gone", "stem_type": "vocals", "path": "/nonexistent/stem.wav", "format": "wav"},
                {"name": "Corrupt", "stem_type": "other", "path": str(corrupt), "format": "wav"},
                {"name": "ShortVocal", "stem_type": "vocals", "path": str(stem_dir / "short_vocal.wav"), "format": "wav"},
            ],
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest_data))

        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code == 0

    def test_full_mix_fallback_truncated_vocals(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav, duration=2.0)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])

        stem_dir = tmp_path / "data" / "cache" / "stems"
        stem_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(stem_dir / "drums.wav", duration=2.0, sr=22050)
        _write_wav(stem_dir / "vocals.wav", duration=0.1, sr=22050)

        ingest_data = {
            "tier": "enhanced",
            "stems": [
                {"name": "Drums", "stem_type": "drums", "path": str(stem_dir / "drums.wav"), "format": "wav"},
                {"name": "Vocals", "stem_type": "vocals", "path": str(stem_dir / "vocals.wav"), "format": "wav"},
            ],
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest_data))

        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "WARNING" in result.output
        assert (tmp_path / "data" / "vocal_onsets.json").exists()

        vo = json.loads((tmp_path / "data" / "vocal_onsets.json").read_text(encoding="utf-8"))
        assert vo["source"] == "combined_mix (fallback)"

    def test_combined_vocal_transcription(self, runner, tmp_path):
        from unittest.mock import patch

        wav = tmp_path / "song.wav"
        _write_wav(wav, duration=2.0)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])

        stem_dir = tmp_path / "data" / "cache" / "stems"
        stem_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(stem_dir / "lead.wav", duration=2.0)
        _write_wav(stem_dir / "backing.wav", duration=2.0)

        ingest_data = {
            "tier": "enhanced",
            "stems": [
                {"name": "Lead", "stem_type": "lead_vocals", "path": str(stem_dir / "lead.wav"), "format": "wav"},
                {"name": "Backing", "stem_type": "backing_vocals", "path": str(stem_dir / "backing.wav"), "format": "wav"},
            ],
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest_data))

        lyrics_raw = {
            "lines": [
                {"index": 0, "text": "Hello world", "start": 0.0, "end": 1.0, "words": []},
                {"index": 1, "text": "Second line here", "start": 1.0, "end": 2.0, "words": []},
            ]
        }
        (tmp_path / "data" / "lyrics_raw.json").write_text(json.dumps(lyrics_raw))

        def mock_transcribe(path):
            if "lead" in path:
                return {
                    "language": "en", "language_probability": 0.9, "duration": 2.0,
                    "segments": [{"start": 0.0, "end": 1.0, "text": "Hello world"}],
                    "words": [{"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.9}],
                }
            return {
                "language": "en", "language_probability": 0.8, "duration": 2.0,
                "segments": [{"start": 1.0, "end": 2.0, "text": "Second line here"}],
                "words": [{"word": "Second", "start": 1.0, "end": 1.5, "probability": 0.8}],
            }

        mock_onsets = np.array([0.1, 0.5, 1.1, 1.5])

        with patch("cli.commands.AudioAnalyzer.transcribe_vocal_stem", side_effect=mock_transcribe), \
             patch("cli.commands.AudioAnalyzer.extract_vocal_onsets", return_value=mock_onsets), \
             patch("cli.commands.AudioAnalyzer.generate_waveforms_for_file", return_value=([0.1, 0.2, 0.3], 2.0)):
            result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])

        assert result.exit_code == 0
        assert "No single stem" in result.output or "merging" in result.output.lower()
        assert (tmp_path / "data" / "vocal_onsets.json").exists()
        assert (tmp_path / "data" / "vocal_waveforms.json").exists()
        assert (tmp_path / "data" / "cache" / "stems" / "combined_vocals.wav").exists()

    def test_combined_waveform_failure(self, runner, tmp_path):
        from unittest.mock import patch

        wav = tmp_path / "song.wav"
        _write_wav(wav, duration=2.0)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])

        stem_dir = tmp_path / "data" / "cache" / "stems"
        stem_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(stem_dir / "lead.wav", duration=2.0)
        _write_wav(stem_dir / "backing.wav", duration=2.0)

        ingest_data = {
            "tier": "enhanced",
            "stems": [
                {"name": "Lead", "stem_type": "lead_vocals", "path": str(stem_dir / "lead.wav"), "format": "wav"},
                {"name": "Backing", "stem_type": "backing_vocals", "path": str(stem_dir / "backing.wav"), "format": "wav"},
            ],
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest_data))

        lyrics_raw = {
            "lines": [
                {"index": 0, "text": "Hello world", "start": 0.0, "end": 1.0, "words": []},
                {"index": 1, "text": "Second line here", "start": 1.0, "end": 2.0, "words": []},
            ]
        }
        (tmp_path / "data" / "lyrics_raw.json").write_text(json.dumps(lyrics_raw))

        def mock_transcribe(path):
            if "lead" in path:
                return {
                    "language": "en", "language_probability": 0.9, "duration": 2.0,
                    "segments": [{"start": 0.0, "end": 1.0, "text": "Hello world"}],
                    "words": [{"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.9}],
                }
            return {
                "language": "en", "language_probability": 0.8, "duration": 2.0,
                "segments": [{"start": 1.0, "end": 2.0, "text": "Second line here"}],
                "words": [{"word": "Second", "start": 1.0, "end": 1.5, "probability": 0.8}],
            }

        mock_onsets = np.array([0.1, 0.5, 1.1, 1.5])

        with patch("cli.commands.AudioAnalyzer.transcribe_vocal_stem", side_effect=mock_transcribe), \
             patch("cli.commands.AudioAnalyzer.extract_vocal_onsets", return_value=mock_onsets), \
             patch("cli.commands.AudioAnalyzer.generate_waveforms_for_file", side_effect=RuntimeError("boom")):
            result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])

        assert result.exit_code == 0

    def test_lyrics_raw_invalid_json(self, runner, tmp_path):
        from unittest.mock import patch

        wav = tmp_path / "song.wav"
        _write_wav(wav, duration=2.0)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])

        stem_dir = tmp_path / "data" / "cache" / "stems"
        stem_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(stem_dir / "vocals.wav", duration=2.0)

        ingest_data = {
            "tier": "enhanced",
            "stems": [
                {"name": "Vocals", "stem_type": "lead_vocals", "path": str(stem_dir / "vocals.wav"), "format": "wav"},
            ],
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest_data))
        (tmp_path / "data" / "lyrics_raw.json").write_text("not valid json{{{", encoding="utf-8")

        with patch("cli.commands.AudioAnalyzer.transcribe_vocal_stem", return_value={
            "language": "en", "language_probability": 0.9, "duration": 2.0,
            "segments": [{"start": 0.0, "end": 1.0, "text": "Hello"}],
            "words": [{"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.9}],
        }), patch("cli.commands.AudioAnalyzer.extract_vocal_onsets", return_value=np.array([0.1, 0.5])), \
             patch("cli.commands.AudioAnalyzer.generate_waveforms_for_file", return_value=([0.1, 0.2], 2.0)):
            result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])

        assert result.exit_code == 0

    def test_vocal_waveform_failure_single_stem(self, runner, tmp_path):
        from unittest.mock import patch

        wav = tmp_path / "song.wav"
        _write_wav(wav, duration=2.0)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])

        stem_dir = tmp_path / "data" / "cache" / "stems"
        stem_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(stem_dir / "vocals.wav", duration=2.0)

        ingest_data = {
            "tier": "enhanced",
            "stems": [
                {"name": "Vocals", "stem_type": "lead_vocals", "path": str(stem_dir / "vocals.wav"), "format": "wav"},
            ],
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest_data))

        with patch("cli.commands.AudioAnalyzer.transcribe_vocal_stem", return_value={
            "language": "en", "language_probability": 0.9, "duration": 2.0,
            "segments": [{"start": 0.0, "end": 1.0, "text": "Hello world"}],
            "words": [{"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.9}],
        }), patch("cli.commands.AudioAnalyzer.extract_vocal_onsets", return_value=np.array([0.1, 0.5])), \
             patch("cli.commands.AudioAnalyzer.generate_waveforms_for_file", side_effect=RuntimeError("waveform failed")):
            result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])

        assert result.exit_code == 0
        assert "WARNING" in result.output

    def test_sync_loads_vocal_waveforms(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        vw_data = {"peaks": [0.1, 0.2, 0.3], "peaks_per_second": 100}
        (tmp_path / "data" / "vocal_waveforms.json").write_text(json.dumps(vw_data), encoding="utf-8")

        result = runner.invoke(cli, ["sync", "--project", str(tmp_path)])
        assert result.exit_code == 0

    def test_sync_invalid_vocal_waveforms(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        (tmp_path / "data" / "vocal_waveforms.json").write_text("invalid json{{", encoding="utf-8")

        result = runner.invoke(cli, ["sync", "--project", str(tmp_path)])
        assert result.exit_code == 0

    def test_sync_with_onset_refiner(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        analysis = json.loads((tmp_path / "data" / "analysis.json").read_text(encoding="utf-8"))
        analysis["vocal_onset_times"] = [0.05, 0.15, 0.3, 0.45]
        (tmp_path / "data" / "analysis.json").write_text(json.dumps(analysis), encoding="utf-8")

        result = runner.invoke(cli, ["sync", "--project", str(tmp_path)])
        assert result.exit_code == 0

    def test_render_base_color(self, runner, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        mock_result = MagicMock()
        mock_result.script = {"sections": []}
        mock_result.sections_profiled = 1
        mock_result.variance_detected = "low"
        mock_result.mood_used = "dark_moody"

        mock_renderer = MagicMock()
        mock_renderer.duration = 1.0
        mock_renderer.audio_path = tmp_path / "data" / "raw" / "song.wav"
        mock_renderer.load.return_value = None
        mock_renderer.render.return_value = None

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            import scriptgen
            monkeypatch.setattr(scriptgen, "generate_script", lambda *a, **kw: mock_result)
            out = tmp_path / "output" / "video.mp4"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"fake")
            result = runner.invoke(
                cli, ["render", "--project", str(tmp_path), "--mood", "dark_moody", "--base-color", "#ff0000"]
            )
        assert result.exit_code == 0
        assert "Base color" in result.output

    def test_render_intro_image_relative(self, runner, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        (tmp_path / "intro.png").write_bytes(b"fake png")

        mock_result = MagicMock()
        mock_result.script = {"sections": []}
        mock_result.sections_profiled = 1
        mock_result.variance_detected = "low"
        mock_result.mood_used = "dark_moody"

        mock_renderer = MagicMock()
        mock_renderer.duration = 1.0
        mock_renderer.audio_path = tmp_path / "data" / "raw" / "song.wav"
        mock_renderer.load.return_value = None
        mock_renderer.render.return_value = None

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            import scriptgen
            monkeypatch.setattr(scriptgen, "generate_script", lambda *a, **kw: mock_result)
            out = tmp_path / "output" / "video.mp4"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"fake")
            result = runner.invoke(
                cli, ["render", "--project", str(tmp_path), "--mood", "dark_moody",
                      "--intro-image", "intro.png", "--intro-title", "Test Song",
                      "--intro-subtitle", "Subtitle"]
            )
        assert result.exit_code == 0
        assert "Intro" in result.output

    def test_render_audio_path_from_project(self, runner, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        proj = MusicVideoProject.load(tmp_path)
        proj.paths.audio = "data/raw/song.wav"
        proj.save()

        mock_result = MagicMock()
        mock_result.script = {"sections": []}
        mock_result.sections_profiled = 1
        mock_result.variance_detected = "low"
        mock_result.mood_used = "dark_moody"

        mock_renderer = MagicMock()
        mock_renderer.duration = 1.0
        mock_renderer.audio_path = None
        mock_renderer.load.return_value = None
        mock_renderer.render.return_value = None

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            import scriptgen
            monkeypatch.setattr(scriptgen, "generate_script", lambda *a, **kw: mock_result)
            out = tmp_path / "output" / "video.mp4"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"fake")
            result = runner.invoke(
                cli, ["render", "--project", str(tmp_path), "--mood", "dark_moody"]
            )
        assert result.exit_code == 0

    def test_audit_with_issues(self, runner, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from PIL import Image as PILImage

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        (tmp_path / "intro.png").write_bytes(b"fake")

        synced = {
            "lines": [
                {
                    "words": [
                        {"text": "Hi", "start": 0.0, "end": 0.01},
                        {"text": "there", "start": 0.6, "end": 0.8},
                        {"text": "long", "start": 0.8, "end": 2.5},
                        {"text": "bad", "start": 3.0, "end": 2.5},
                        {"text": "ok", "start": 3.0, "end": 3.5},
                    ]
                },
            ]
        }

        mock_renderer = MagicMock()
        mock_renderer.synced = synced
        mock_renderer.load.return_value = None

        call_count = [0]
        def mock_render_frame(t):
            call_count[0] += 1
            if call_count[0] == 4:
                raise RuntimeError("frame error")
            return PILImage.new("RGB", (960, 540), (0, 0, 0))

        mock_renderer.render_frame = mock_render_frame

        mock_gen_result = MagicMock()
        mock_gen_result.script = {"sections": []}
        mock_gen_result.sections_profiled = 1
        mock_gen_result.variance_detected = "low"
        mock_gen_result.mood_used = "dark_moody"

        import scriptgen
        monkeypatch.setattr(scriptgen, "generate_script", lambda *a, **kw: mock_gen_result)

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(
                cli, ["audit", "--project", str(tmp_path), "--mood", "dark_moody",
                      "--intro-image", "intro.png", "--intro-title", "Song",
                      "--intro-subtitle", "Sub"]
            )

        assert result.exit_code == 0
        assert "Auditing" in result.output
        assert "Issues found" in result.output
        assert (tmp_path / "output" / "audit" / "summary.json").exists()
        assert (tmp_path / "output" / "audit" / "contact_sheet.png").exists()

    def test_audit_many_issues(self, runner, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from PIL import Image as PILImage

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        lines = []
        for i in range(25):
            lines.append({"words": [{"text": f"w{i}", "start": float(i) + 0.1, "end": float(i)}]})
        synced = {"lines": lines}

        mock_renderer = MagicMock()
        mock_renderer.synced = synced
        mock_renderer.load.return_value = None
        mock_renderer.render_frame = lambda t: PILImage.new("RGB", (960, 540), (0, 0, 0))

        mock_gen_result = MagicMock()
        mock_gen_result.script = {"sections": []}
        mock_gen_result.sections_profiled = 1
        mock_gen_result.variance_detected = "low"
        mock_gen_result.mood_used = "dark_moody"

        import scriptgen
        monkeypatch.setattr(scriptgen, "generate_script", lambda *a, **kw: mock_gen_result)

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(
                cli, ["audit", "--project", str(tmp_path), "--mood", "dark_moody"]
            )

        assert result.exit_code == 0
        assert "... and" in result.output

    def test_audit_no_issues(self, runner, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from PIL import Image as PILImage

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        synced = {
            "lines": [
                {
                    "words": [
                        {"text": "Hello", "start": 0.0, "end": 0.3},
                        {"text": "world", "start": 0.3, "end": 0.5},
                    ]
                },
            ]
        }

        mock_renderer = MagicMock()
        mock_renderer.synced = synced
        mock_renderer.load.return_value = None
        mock_renderer.render_frame = lambda t: PILImage.new("RGB", (960, 540), (0, 0, 0))

        mock_gen_result = MagicMock()
        mock_gen_result.script = {"sections": []}
        mock_gen_result.sections_profiled = 1
        mock_gen_result.variance_detected = "low"
        mock_gen_result.mood_used = "dark_moody"

        import scriptgen
        monkeypatch.setattr(scriptgen, "generate_script", lambda *a, **kw: mock_gen_result)

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(
                cli, ["audit", "--project", str(tmp_path), "--mood", "dark_moody"]
            )

        assert result.exit_code == 0
        assert "Issues found: 0" in result.output

    def test_audit_custom_output(self, runner, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        synced = {
            "lines": [
                {"words": [{"text": "Hi", "start": 0.0, "end": 0.3}]},
            ]
        }

        mock_renderer = MagicMock()
        mock_renderer.synced = synced
        mock_renderer.load.return_value = None

        mock_gen_result = MagicMock()
        mock_gen_result.script = {"sections": []}
        mock_gen_result.sections_profiled = 1
        mock_gen_result.variance_detected = "low"
        mock_gen_result.mood_used = "dark_moody"

        import scriptgen
        monkeypatch.setattr(scriptgen, "generate_script", lambda *a, **kw: mock_gen_result)

        custom_out = tmp_path / "my_audit"
        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(
                cli, ["audit", "--project", str(tmp_path), "--mood", "dark_moody",
                      "--json-only", "--output", str(custom_out)]
            )

        assert result.exit_code == 0
        assert (custom_out / "summary.json").exists()

    def test_audit_no_synced_lines(self, runner, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        mock_renderer = MagicMock()
        mock_renderer.synced = {"lines": []}
        mock_renderer.load.return_value = None

        mock_gen_result = MagicMock()
        mock_gen_result.script = {"sections": []}
        mock_gen_result.sections_profiled = 1
        mock_gen_result.variance_detected = "low"
        mock_gen_result.mood_used = "dark_moody"

        import scriptgen
        monkeypatch.setattr(scriptgen, "generate_script", lambda *a, **kw: mock_gen_result)

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(
                cli, ["audit", "--project", str(tmp_path), "--mood", "dark_moody"]
            )

        assert result.exit_code != 0
        assert "No synced lines" in result.output

    def test_audit_detects_text_overflow_9x16(self, runner, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch
        from cli.commands import _detect_text_overflow

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        synced = {
            "lines": [
                {
                    "words": [
                        {"text": "Hello", "start": 0.0, "end": 0.3},
                        {"text": "world", "start": 0.3, "end": 0.5},
                    ]
                },
            ]
        }

        mock_renderer = MagicMock()
        mock_renderer.synced = synced
        mock_renderer.load.return_value = None
        mock_renderer.caption_style = {"font_size": 112}
        mock_renderer.get_visual.return_value = {"font_size": 112, "font_family": 0}
        mock_renderer._layout_line.return_value = [
            {"px_x": -20, "px_y": 480, "wW": 100, "word_size": 47, "x": None},
            {"px_x": 560, "px_y": 480, "wW": 80, "word_size": 47, "x": None},
        ]

        overflow = _detect_text_overflow(mock_renderer, synced["lines"], 540, 960)
        assert len(overflow) >= 2
        assert any(o["edge"] == "left" for o in overflow)
        assert any(o["edge"] == "right" for o in overflow)
        assert all(o["check"] == "text_overflow" for o in overflow)

    def test_audit_no_text_overflow_when_fits(self, runner, tmp_path, monkeypatch):
        from unittest.mock import MagicMock
        from cli.commands import _detect_text_overflow

        synced = {
            "lines": [
                {
                    "words": [
                        {"text": "Hi", "start": 0.0, "end": 0.3},
                    ]
                },
            ]
        }

        mock_renderer = MagicMock()
        mock_renderer.caption_style = {"font_size": 112}
        mock_renderer.get_visual.return_value = {"font_size": 112, "font_family": 0}
        mock_renderer._layout_line.return_value = [
            {"px_x": 270, "px_y": 480, "wW": 40, "word_size": 47, "x": None},
        ]

        overflow = _detect_text_overflow(mock_renderer, synced["lines"], 540, 960)
        assert len(overflow) == 0

    def test_audit_overflow_graceful_on_missing_layout(self, runner, tmp_path, monkeypatch):
        from unittest.mock import MagicMock
        from cli.commands import _detect_text_overflow

        synced = {
            "lines": [
                {"words": [{"text": "Test", "start": 0.0, "end": 0.3}]},
            ]
        }

        mock_renderer = MagicMock()
        mock_renderer.caption_style = {"font_size": 112}
        mock_renderer.get_visual.side_effect = RuntimeError("no visual")
        mock_renderer._layout_line.side_effect = RuntimeError("no layout")

        overflow = _detect_text_overflow(mock_renderer, synced["lines"], 540, 960)
        assert len(overflow) == 0

    def test_audit_with_overflow_in_summary(self, runner, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch

        from PIL import Image as PILImage

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        synced = {
            "lines": [
                {
                    "words": [
                        {"text": "Hello", "start": 0.0, "end": 0.3},
                        {"text": "world", "start": 0.3, "end": 0.5},
                    ]
                },
            ]
        }

        mock_renderer = MagicMock()
        mock_renderer.synced = synced
        mock_renderer.load.return_value = None
        mock_renderer.render_frame.return_value = PILImage.new("RGB", (540, 960), (0, 0, 0))
        mock_renderer.caption_style = {"font_size": 112}
        mock_renderer.get_visual.return_value = {"font_size": 112, "font_family": 0}
        mock_renderer._layout_line.return_value = [
            {"px_x": -20, "px_y": 480, "wW": 100, "word_size": 47, "x": None},
            {"px_x": 560, "px_y": 480, "wW": 80, "word_size": 47, "x": None},
        ]

        mock_gen_result = MagicMock()
        mock_gen_result.script = {"sections": []}
        mock_gen_result.sections_profiled = 1
        mock_gen_result.variance_detected = "low"
        mock_gen_result.mood_used = "dark_moody"

        import scriptgen
        monkeypatch.setattr(scriptgen, "generate_script", lambda *a, **kw: mock_gen_result)

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(
                cli, ["audit", "--project", str(tmp_path), "--aspect-ratio", "9:16", "--json-only"]
            )

        assert result.exit_code == 0
        assert "Text overflow" in result.output
        summary = json.loads((tmp_path / "output" / "audit_9x16" / "summary.json").read_text())
        assert "overflow_issues" in summary
        assert len(summary["overflow_issues"]) >= 2
