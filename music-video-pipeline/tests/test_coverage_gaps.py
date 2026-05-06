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

        pm_mod = sys.modules.get("pretty_midi")
        sys.modules["pretty_midi"] = None

        try:
            importlib.reload(midi_mod)
            result = midi_mod.analyze_midi(tmp_path / "fake.mid")
            assert result.tempo is None
        finally:
            if pm_mod is not None:
                sys.modules["pretty_midi"] = pm_mod
            else:
                del sys.modules["pretty_midi"]
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

        try:
            import pretty_midi
            pm = pretty_midi.PrettyMIDI(initial_tempo=103.8)
            inst = pretty_midi.Instrument(program=0)
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=60, start=0.0, end=1.0))
            pm.instruments.append(inst)
            midi_path = tmp_path / "test.mid"
            pm.write(str(midi_path))
        except ImportError:
            pytest.skip("pretty_midi not installed")

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
