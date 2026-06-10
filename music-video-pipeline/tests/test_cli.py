import json
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
from click.testing import CliRunner

from cli.commands import cli


@pytest.fixture
def runner():
    return CliRunner()


def _write_wav(path, duration=1.0, sr=22050, freq=440.0):
    import soundfile as sf
    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
    sig = (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    sf.write(str(path), sig, sr)


@pytest.fixture
def sample_wav_for_cli(tmp_path):
    p = tmp_path / "song.wav"
    _write_wav(p)
    return p


@pytest.fixture
def sample_srt_for_cli(tmp_path):
    p = tmp_path / "lyrics.srt"
    p.write_text(
        "1\n00:00:00,000 --> 00:00:00,500\nHello world\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def sample_txt_sections_for_cli(tmp_path):
    p = tmp_path / "lyrics.txt"
    p.write_text("[Intro]\nHello world\n[Verse]\nSecond line\n")
    return p


class TestInit:
    def test_init_basic(self, runner, tmp_path):
        result = runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "Test" in result.output
        assert (tmp_path / "data" / "mvp_project.json").exists()

    def test_init_with_artist(self, runner, tmp_path):
        result = runner.invoke(cli, ["init", "--name", "Song", "--artist", "Artist", "--dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "Artist" in result.output

    def test_init_with_audio(self, runner, tmp_path, sample_wav_for_cli):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Analyzing audio" in result.output
        assert (tmp_path / "data" / "analysis.json").exists()
        assert (tmp_path / "data" / "waveforms.json").exists()

    def test_init_with_lyrics(self, runner, tmp_path, sample_wav_for_cli, sample_srt_for_cli):
        result = runner.invoke(
            cli,
            [
                "init",
                "--name",
                "Test",
                "--audio",
                str(sample_wav_for_cli),
                "--lyrics",
                str(sample_srt_for_cli),
                "--dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert "Importing lyrics" in result.output
        assert (tmp_path / "data" / "lyrics_raw.json").exists()

    def test_init_no_analyze(self, runner, tmp_path, sample_wav_for_cli):
        result = runner.invoke(
            cli,
            ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path), "--no-analyze"],
        )
        assert result.exit_code == 0
        assert "Analyzing" not in result.output

    def test_init_existing_project_fails(self, runner, tmp_path):
        runner.invoke(cli, ["init", "--name", "First", "--dir", str(tmp_path)])
        result = runner.invoke(cli, ["init", "--name", "Second", "--dir", str(tmp_path)])
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_init_audio_not_found(self, runner, tmp_path):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", "/nonexistent/file.mp3", "--dir", str(tmp_path)]
        )
        assert result.exit_code != 0

    def test_init_unsupported_audio(self, runner, tmp_path):
        fake = tmp_path / "song.xyz"
        fake.write_bytes(b"data")
        result = runner.invoke(cli, ["init", "--name", "Test", "--audio", str(fake), "--dir", str(tmp_path)])
        assert result.exit_code != 0
        assert "Unsupported" in result.output

    def test_init_unsupported_lyrics(self, runner, tmp_path):
        fake = tmp_path / "lyrics.xml"
        fake.write_text("<x/>")
        result = runner.invoke(cli, ["init", "--name", "Test", "--lyrics", str(fake), "--dir", str(tmp_path)])
        assert result.exit_code != 0

    def test_init_lyrics_not_found(self, runner, tmp_path):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--lyrics", "/nonexistent/file.srt", "--dir", str(tmp_path)]
        )
        assert result.exit_code != 0

    def test_init_instrumental(self, runner, tmp_path, sample_wav_for_cli):
        result = runner.invoke(
            cli, ["init", "--name", "Instrumental", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Importing lyrics" not in result.output

    def test_init_next_step_message(self, runner, tmp_path):
        result = runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        assert "mvp serve" in result.output

    def test_init_with_data_dir(self, runner, tmp_path, suno_data_dir):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--data-dir", str(suno_data_dir), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Input tier" in result.output

    def test_init_with_data_dir_auto_discovers(self, runner, tmp_path, suno_data_dir):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--data-dir", str(suno_data_dir), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert (tmp_path / "data" / "ingest.json").exists()

    def test_init_auto_syncs(self, runner, tmp_path, sample_wav_for_cli, sample_srt_for_cli):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--lyrics", str(sample_srt_for_cli), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Syncing lyrics" in result.output
        assert (tmp_path / "data" / "lyrics_synced.json").exists()

    def test_init_no_sync_flag(self, runner, tmp_path, sample_wav_for_cli, sample_srt_for_cli):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--lyrics", str(sample_srt_for_cli), "--dir", str(tmp_path), "--no-sync"]
        )
        assert result.exit_code == 0
        assert not (tmp_path / "data" / "lyrics_synced.json").exists()

    def test_init_no_analyze_skips_sync_too(self, runner, tmp_path, sample_wav_for_cli, sample_srt_for_cli):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--lyrics", str(sample_srt_for_cli), "--dir", str(tmp_path), "--no-analyze"]
        )
        assert result.exit_code == 0
        assert not (tmp_path / "data" / "lyrics_synced.json").exists()
        assert not (tmp_path / "data" / "analysis.json").exists()

    def test_init_sync_without_analysis_returns_early(self, runner, tmp_path, sample_srt_for_cli):
        runner.invoke(
            cli, ["init", "--name", "Test", "--lyrics", str(sample_srt_for_cli), "--dir", str(tmp_path), "--no-analyze"]
        )
        (tmp_path / "data" / "lyrics_raw.json").write_text('{"lines":[{"index":0,"text":"hi","start":0,"end":1,"words":[]}]}', encoding="utf-8")
        result = runner.invoke(
            cli, ["init", "--name", "Test2", "--dir", str(tmp_path / "sub")]
        )
        assert result.exit_code == 0

    def test_run_sync_returns_when_no_analysis(self, tmp_path, sample_wav_for_cli, sample_srt_for_cli, runner):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--lyrics", str(sample_srt_for_cli), "--dir", str(tmp_path), "--no-sync"]
        )
        assert result.exit_code == 0
        (tmp_path / "data" / "analysis.json").unlink()
        from cli.commands import _run_sync
        from pipeline.models import MusicVideoProject
        proj = MusicVideoProject.load(tmp_path)
        _run_sync(proj)
        assert not (tmp_path / "data" / "lyrics_synced.json").exists()


class TestAnalyze:
    def test_analyze_existing_project(self, runner, tmp_path, sample_wav_for_cli):
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "Analyzing audio" in result.output

    def test_analyze_with_lyrics_override(self, runner, tmp_path, sample_wav_for_cli, sample_srt_for_cli):
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        result = runner.invoke(
            cli, ["analyze", "--project", str(tmp_path), "--lyrics", str(sample_srt_for_cli)]
        )
        assert result.exit_code == 0
        assert "Importing lyrics" in result.output

    def test_analyze_with_audio_override(self, runner, tmp_path, sample_wav_for_cli):
        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        result = runner.invoke(
            cli, ["analyze", "--project", str(tmp_path), "--audio", str(sample_wav_for_cli)]
        )
        assert result.exit_code == 0
        assert "Analyzing audio" in result.output

    def test_analyze_verbose(self, runner, tmp_path, sample_wav_for_cli):
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path), "--verbose"])
        assert result.exit_code == 0
        assert "Sample rate" in result.output

    def test_analyze_no_project_fails(self, runner, tmp_path):
        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code != 0
        assert "No project found" in result.output

    def test_analyze_no_audio_fails(self, runner, tmp_path):
        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code != 0
        assert "No audio file" in result.output

    def test_analyze_audio_override_copies_file(self, runner, tmp_path, sample_wav_for_cli):
        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        runner.invoke(
            cli, ["analyze", "--project", str(tmp_path), "--audio", str(sample_wav_for_cli)]
        )
        assert (tmp_path / "data" / "raw" / sample_wav_for_cli.name).exists()

    def test_analyze_lyrics_override_copies_file(self, runner, tmp_path, sample_wav_for_cli, sample_srt_for_cli):
        runner.invoke(
            cli,
            [
                "init",
                "--name",
                "Test",
                "--audio",
                str(sample_wav_for_cli),
                "--dir",
                str(tmp_path),
            ],
        )
        runner.invoke(
            cli, ["analyze", "--project", str(tmp_path), "--lyrics", str(sample_srt_for_cli)]
        )
        assert (tmp_path / "data" / "raw" / sample_srt_for_cli.name).exists()

    def test_analyze_with_vocal_stem(self, runner, tmp_path, sample_wav_for_cli):
        stem_dir = tmp_path / "data" / "cache" / "stems"
        stem_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(stem_dir / "0 Lead Vocals.wav")
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        stem_path = str(stem_dir / "0 Lead Vocals.wav")
        ingest_data = {
            "tier": "enhanced",
            "stems": [
                {"name": "Lead Vocals", "stem_type": "lead_vocals", "path": stem_path, "format": "wav"},
            ],
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest_data), encoding="utf-8")
        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "Vocal onsets" in result.output

    def test_analyze_vocal_stem_saves_files(self, runner, tmp_path, sample_wav_for_cli):
        stem_dir = tmp_path / "data" / "cache" / "stems"
        stem_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(stem_dir / "0 Lead Vocals.wav")
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        stem_path = str(stem_dir / "0 Lead Vocals.wav")
        ingest_data = {
            "tier": "enhanced",
            "stems": [
                {"name": "Lead Vocals", "stem_type": "lead_vocals", "path": stem_path, "format": "wav"},
            ],
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest_data), encoding="utf-8")
        runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert (tmp_path / "data" / "vocal_onsets.json").exists()
        assert (tmp_path / "data" / "vocal_transcription.json").exists()

    def test_analyze_vocal_stem_transcription_failure(self, runner, tmp_path, sample_wav_for_cli):
        stem_dir = tmp_path / "data" / "cache" / "stems"
        stem_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(stem_dir / "0 Lead Vocals.wav")
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        stem_path = str(stem_dir / "0 Lead Vocals.wav")
        ingest_data = {
            "tier": "enhanced",
            "stems": [
                {"name": "Lead Vocals", "stem_type": "lead_vocals", "path": stem_path, "format": "wav"},
            ],
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest_data), encoding="utf-8")
        from unittest.mock import patch
        with patch("cli.commands.AudioAnalyzer.transcribe_vocal_stem", side_effect=RuntimeError("model not found")):
            result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code != 0
        assert "lead_vocals" in result.output

    def test_analyze_vocal_stem_transcription_failure_force(self, runner, tmp_path, sample_wav_for_cli):
        stem_dir = tmp_path / "data" / "cache" / "stems"
        stem_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(stem_dir / "0 Lead Vocals.wav")
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        stem_path = str(stem_dir / "0 Lead Vocals.wav")
        ingest_data = {
            "tier": "enhanced",
            "stems": [
                {"name": "Lead Vocals", "stem_type": "lead_vocals", "path": stem_path, "format": "wav"},
            ],
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest_data), encoding="utf-8")
        from unittest.mock import patch
        with patch("cli.commands.AudioAnalyzer.transcribe_vocal_stem", side_effect=RuntimeError("model not found")):
            result = runner.invoke(cli, ["analyze", "--force", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "WARNING" in result.output


class TestInfo:
    def test_info_shows_project(self, runner, tmp_path):
        runner.invoke(cli, ["init", "--name", "MySong", "--artist", "Art", "--dir", str(tmp_path)])
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "MySong" in result.output
        assert "Art" in result.output

    def test_info_shows_audio(self, runner, tmp_path, sample_wav_for_cli):
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "BPM" in result.output
        assert "Beats" in result.output

    def test_info_shows_lyrics(self, runner, tmp_path, sample_wav_for_cli, sample_srt_for_cli):
        runner.invoke(
            cli,
            [
                "init",
                "--name",
                "Test",
                "--audio",
                str(sample_wav_for_cli),
                "--lyrics",
                str(sample_srt_for_cli),
                "--dir",
                str(tmp_path),
            ],
        )
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "SRT" in result.output
        assert "Lines" in result.output

    def test_info_instrumental(self, runner, tmp_path, sample_wav_for_cli):
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "instrumental mode" in result.output

    def test_info_pipeline_stages(self, runner, tmp_path):
        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "ingest" in result.output
        assert "sync" in result.output

    def test_info_files_section(self, runner, tmp_path):
        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "mvp_project.json" in result.output

    def test_info_no_project_fails(self, runner, tmp_path):
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert result.exit_code != 0

    def test_info_next_step_analyze(self, runner, tmp_path):
        from pipeline.models import MusicVideoProject

        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path), "--no-analyze"])
        proj = MusicVideoProject.load(tmp_path)
        proj.stages.mark_complete("ingest")
        proj.save()
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert "mvp analyze" in result.output

    def test_info_next_step_sync(self, runner, tmp_path, sample_wav_for_cli):
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert "mvp sync" in result.output

    def test_info_next_step_serve(self, runner, tmp_path):
        from pipeline.models import MusicVideoProject

        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        proj = MusicVideoProject.load(tmp_path)
        for s in ["ingest", "analyze", "sync"]:
            proj.stages.mark_complete(s)
        proj.save()
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert "mvp serve" in result.output

    def test_info_next_step_render(self, runner, tmp_path):
        from pipeline.models import MusicVideoProject

        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        proj = MusicVideoProject.load(tmp_path)
        for s in ["ingest", "analyze", "sync", "structure", "design"]:
            proj.stages.mark_complete(s)
        proj.save()
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert "mvp render" in result.output

    def test_info_all_complete(self, runner, tmp_path):
        from pipeline.models import MusicVideoProject

        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        proj = MusicVideoProject.load(tmp_path)
        for s in ["ingest", "analyze", "sync", "structure", "design", "render"]:
            proj.stages.mark_complete(s)
        proj.save()
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert "All stages complete" in result.output

    def test_info_missing_files_shown_as_dash(self, runner, tmp_path):
        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        (tmp_path / "data" / "analysis.json").unlink(missing_ok=True)
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert result.exit_code == 0

    def test_info_no_audio_not_analyzed(self, runner, tmp_path):
        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path), "--no-analyze"])
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert "not analyzed" in result.output

    def test_info_input_tier(self, runner, tmp_path):
        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert "Input tier" in result.output

    def test_info_lyrics_with_sections(self, runner, tmp_path, sample_wav_for_cli, sample_txt_sections_for_cli):
        runner.invoke(
            cli,
            [
                "init",
                "--name",
                "Test",
                "--audio",
                str(sample_wav_for_cli),
                "--lyrics",
                str(sample_txt_sections_for_cli),
                "--dir",
                str(tmp_path),
            ],
        )
        result = runner.invoke(cli, ["info", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "Sections" in result.output


class TestCLIEdgeCases:
    def test_analyze_no_lyrics_path(self, runner, tmp_path):
        from pipeline.models import MusicVideoProject

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])
        proj = MusicVideoProject.load(tmp_path)
        proj.paths.lyrics = None
        proj.save()
        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code == 0

    def test_lyrics_import_empty_lines_warning(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "empty.srt"
        srt.write_text("")
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0

    def test_lyrics_txt_format_note_no_sections(self, runner, tmp_path):
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        txt = tmp_path / "lyrics.txt"
        txt.write_text("Hello world\nSecond line")
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(txt), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Plain text detected" in result.output

    def test_cli_main_entry(self):
        from cli.commands import cli
        assert cli is not None


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


class TestSyncCommand:
    def test_sync_no_project(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli, ["sync"])
        assert result.exit_code != 0
        assert "No project found" in result.output

    def test_sync_no_analysis(self, runner, tmp_path, sample_wav_for_cli):
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path), "--no-analyze"])
        (tmp_path / "data" / "lyrics_raw.json").write_text('{"lines": []}', encoding="utf-8")
        result = runner.invoke(cli, ["sync", "--project", str(tmp_path)])
        assert result.exit_code != 0
        assert "analysis.json" in result.output

    def test_sync_no_raw(self, runner, tmp_path, sample_wav_for_cli):
        result = runner.invoke(cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)])
        (tmp_path / "data" / "analysis.json").unlink()
        result = runner.invoke(cli, ["sync", "--project", str(tmp_path)])
        assert result.exit_code != 0
        assert "lyrics_raw.json" in result.output

    def test_sync_success(self, runner, tmp_path, sample_wav_for_cli, sample_srt_for_cli):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--lyrics", str(sample_srt_for_cli), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0

        result = runner.invoke(cli, ["sync", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "Syncing lyrics" in result.output
        assert "Lines synced" in result.output
        assert "lyrics_synced.json" in result.output

        synced = json.loads((tmp_path / "data" / "lyrics_synced.json").read_text(encoding="utf-8"))
        assert "lines" in synced

    def test_sync_with_transcription(self, runner, tmp_path, sample_wav_for_cli, sample_srt_for_cli):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--lyrics", str(sample_srt_for_cli), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0

        trans_data = {
            "segments": [
                {"start": 0.0, "end": 0.5, "text": "Hello world"},
            ],
            "words": [{"word": "Hello", "start": 0.0, "end": 0.3, "probability": 0.9}],
        }
        (tmp_path / "data" / "vocal_transcription.json").write_text(
            json.dumps(trans_data), encoding="utf-8"
        )

        result = runner.invoke(cli, ["sync", "--project", str(tmp_path)])
        assert result.exit_code == 0
        assert "Syncing lyrics" in result.output

    def test_sync_with_drift(self, runner, tmp_path, sample_wav_for_cli):
        srt_content = (
            "1\n00:00:00,000 --> 00:00:00,500\nHello world\n\n"
            "2\n00:00:01,000 --> 00:00:01,500\nSecond line here\n\n"
            "3\n00:00:02,000 --> 00:00:02,500\nThird line here\n\n"
            "4\n00:00:03,000 --> 00:00:03,500\nFourth line here\n"
        )
        lyrics_file = tmp_path / "lyrics.srt"
        lyrics_file.write_text(srt_content, encoding="utf-8")

        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--lyrics", str(lyrics_file), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0

        trans_data = {
            "segments": [
                {"start": 0.0, "end": 0.5, "text": "Hello world"},
                {"start": 1.0, "end": 1.5, "text": "Second line here"},
                {"start": 2.0, "end": 2.5, "text": "Completely different text"},
                {"start": 3.0, "end": 3.5, "text": "Also very wrong words"},
            ],
            "words": [],
        }
        (tmp_path / "data" / "vocal_transcription.json").write_text(
            json.dumps(trans_data), encoding="utf-8"
        )

        result = runner.invoke(cli, ["sync", "--project", str(tmp_path)])
        assert result.exit_code == 0

    def test_sync_verbose(self, runner, tmp_path, sample_wav_for_cli, sample_srt_for_cli):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--lyrics", str(sample_srt_for_cli), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0

        result = runner.invoke(cli, ["sync", "--project", str(tmp_path), "--verbose"])
        assert result.exit_code == 0
        assert "0:" in result.output

    def test_sync_marks_stage_complete(self, runner, tmp_path, sample_wav_for_cli, sample_srt_for_cli):
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--lyrics", str(sample_srt_for_cli), "--dir", str(tmp_path)]
        )
        runner.invoke(cli, ["sync", "--project", str(tmp_path)])

        proj = json.loads((tmp_path / "data" / "mvp_project.json").read_text(encoding="utf-8"))
        assert proj["stages"]["sync"] == "complete"

    def test_sync_with_sections(self, runner, tmp_path, sample_wav_for_cli, sample_txt_sections_for_cli):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--lyrics", str(sample_txt_sections_for_cli), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0

        result = runner.invoke(cli, ["sync", "--project", str(tmp_path)])
        assert result.exit_code == 0
        synced = json.loads((tmp_path / "data" / "lyrics_synced.json").read_text(encoding="utf-8"))
        section_lines = [l for l in synced["lines"] if l.get("section")]
        assert len(section_lines) > 0


class TestServeCommand:
    def test_serve_command_exists(self, runner):
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "port" in result.output.lower()

    def test_serve_launches_subprocess(self, runner, sample_wav_for_cli, tmp_path, monkeypatch):
        import subprocess

        captured_cmd = []

        def mock_run(cmd, **kwargs):
            captured_cmd.append(cmd)
            return MagicMock(returncode=0)

        monkeypatch.setattr(subprocess, "run", mock_run)
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0

        result = runner.invoke(cli, ["serve", "--project", str(tmp_path), "--port", "9999"])
        assert result.exit_code == 0
        assert len(captured_cmd) == 1
        assert "9999" in captured_cmd[0]
        assert str(tmp_path) in captured_cmd[0]

    def test_serve_no_project(self, runner, tmp_path, monkeypatch):
        import subprocess

        monkeypatch.setattr(subprocess, "run", lambda cmd, **kwargs: MagicMock(returncode=0))
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli, ["serve", "--port", "9999"])
        assert result.exit_code == 0

    def test_serve_script_not_found(self, runner, tmp_path, monkeypatch):
        import subprocess
        from unittest.mock import patch
        from pathlib import Path as RealPath

        monkeypatch.setattr(subprocess, "run", lambda cmd, **kwargs: MagicMock(returncode=0))
        serve_path = RealPath(__file__).resolve().parent.parent / "serve.py"

        with patch.object(RealPath, "exists", return_value=False):
            result = runner.invoke(cli, ["serve", "--project", str(tmp_path)])
            assert result.exit_code != 0

    def test_serve_finds_project_in_cwd(self, runner, sample_wav_for_cli, tmp_path, monkeypatch):
        import subprocess

        captured_cmd = []
        monkeypatch.setattr(subprocess, "run", lambda cmd, **kwargs: captured_cmd.append(cmd) or MagicMock(returncode=0))
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli, ["serve", "--port", "9999"])
        assert result.exit_code == 0
        assert any(str(tmp_path) in str(a) for a in captured_cmd[0])


class TestIngestCommand:
    def test_ingest_with_midi_files(self, runner, tmp_path, sample_wav_for_cli, monkeypatch):
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        midi_dir = tmp_path / "data" / "cache" / "midi"
        midi_dir.mkdir(parents=True, exist_ok=True)
        midi_file = midi_dir / "song.mid"
        midi_file.write_bytes(b"dummy midi")

        ingest_data = {
            "tier": "enhanced",
            "stems": [],
            "midi_files": [{"path": str(midi_file), "format": "mid"}],
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest_data), encoding="utf-8")

        from unittest.mock import patch
        with patch("audio.midi.extract_tempo", return_value=120.0):
            result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code == 0

    def test_ingest_no_audio_no_data_dir(self, runner, tmp_path):
        from cli.commands import _run_ingest
        from pipeline.models import MusicVideoProject

        proj = MusicVideoProject.create(project_dir=tmp_path, name="Test")
        result = _run_ingest(proj)
        assert result is None

    def test_ingest_scan_dir_missing(self, runner, tmp_path):
        from cli.commands import _run_ingest
        from pipeline.models import MusicVideoProject

        proj = MusicVideoProject.create(project_dir=tmp_path, name="Test")
        proj.paths.data_dir = str(tmp_path / "nonexistent_data")
        result = _run_ingest(proj)
        assert result is None

    def test_ingest_with_data_dir_discovers_files(self, runner, tmp_path, suno_data_dir):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--data-dir", str(suno_data_dir), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        ingest = json.loads((tmp_path / "data" / "ingest.json").read_text(encoding="utf-8"))
        assert ingest["audio_path"] is not None or ingest["lyrics_path"] is not None


class TestLyricsImport:
    def test_lyrics_import_no_path_returns(self, tmp_path):
        from cli.commands import _run_lyrics_import
        from pipeline.models import MusicVideoProject

        proj = MusicVideoProject.create(project_dir=tmp_path, name="Test")
        _run_lyrics_import(proj)
        assert not (tmp_path / "data" / "lyrics_raw.json").exists()

    def test_lyrics_import_with_sections(self, runner, tmp_path, sample_wav_for_cli, sample_txt_sections_for_cli):
        result = runner.invoke(
            cli,
            [
                "init", "--name", "Test",
                "--audio", str(sample_wav_for_cli),
                "--lyrics", str(sample_txt_sections_for_cli),
                "--dir", str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert "Sections:" in result.output
        assert "intro" in result.output or "verse" in result.output

    def test_lyrics_import_empty_file_warning(self, runner, tmp_path, sample_wav_for_cli):
        empty_srt = tmp_path / "empty.srt"
        empty_srt.write_text("", encoding="utf-8")
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli),
                  "--lyrics", str(empty_srt), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0

    def test_lyrics_import_lrc_format(self, runner, tmp_path, sample_wav_for_cli):
        lrc = tmp_path / "lyrics.lrc"
        lrc.write_text("[00:01.00]Hello world\n[00:03.50]Second line\n")
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli),
                  "--lyrics", str(lrc), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "LRC" in result.output


class TestRenderCommand:
    def test_render_help(self, runner):
        result = runner.invoke(cli, ["render", "--help"])
        assert result.exit_code == 0
        assert "fps" in result.output.lower()
        assert "bare" in result.output.lower()

    def test_render_no_project_fails(self, runner, tmp_path):
        result = runner.invoke(cli, ["render", "--project", str(tmp_path)])
        assert result.exit_code != 0

    @pytest.fixture
    def _synced_project(self, tmp_path, sample_wav_for_cli, sample_srt_for_cli):
        runner = CliRunner()
        runner.invoke(
            cli,
            ["init", "--name", "Test", "--audio", str(sample_wav_for_cli),
             "--lyrics", str(sample_srt_for_cli), "--dir", str(tmp_path)],
        )
        return tmp_path

    def test_render_bare_flag(self, runner, _synced_project, monkeypatch):
        from unittest.mock import MagicMock, patch

        mock_renderer = MagicMock()
        mock_renderer.duration = 1.0
        mock_renderer.audio_path = _synced_project / "data" / "raw" / "song.wav"
        mock_renderer.load.return_value = None
        mock_renderer.render.return_value = None

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            out = _synced_project / "output" / "video.mp4"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"fake")
            result = runner.invoke(
                cli, ["render", "--project", str(_synced_project), "--bare"]
            )
        assert result.exit_code == 0
        assert "Bare timing render" in result.output

    def test_render_with_mood(self, runner, _synced_project, monkeypatch):
        from unittest.mock import MagicMock, patch

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
            out = _synced_project / "output" / "video.mp4"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"fake")
            result = runner.invoke(
                cli, ["render", "--project", str(_synced_project), "--mood", "dark_moody"]
            )
        assert result.exit_code == 0
        assert "dark_moody" in result.output

    def test_render_with_time_range(self, runner, _synced_project, monkeypatch):
        from unittest.mock import MagicMock, patch

        mock_result = MagicMock()
        mock_result.script = {"sections": []}
        mock_result.sections_profiled = 1
        mock_result.variance_detected = "low"
        mock_result.mood_used = "dark_moody"

        mock_renderer = MagicMock()
        mock_renderer.duration = 2.0
        mock_renderer.audio_path = None
        mock_renderer.load.return_value = None
        mock_renderer.render.return_value = None

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            import scriptgen
            monkeypatch.setattr(scriptgen, "generate_script", lambda *a, **kw: mock_result)
            out = _synced_project / "output" / "preview_0.5-1.5.mp4"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"fake")
            result = runner.invoke(
                cli, ["render", "--project", str(_synced_project),
                      "--start", "0.5", "--end", "1.5"]
            )
        assert result.exit_code == 0
        assert "preview_" in result.output

    def test_render_custom_output(self, runner, _synced_project, tmp_path, monkeypatch):
        from unittest.mock import MagicMock, patch

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

        out_path = tmp_path / "custom_output.mp4"
        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            import scriptgen
            monkeypatch.setattr(scriptgen, "generate_script", lambda *a, **kw: mock_result)
            out_path.write_bytes(b"fake")
            result = runner.invoke(
                cli, ["render", "--project", str(_synced_project),
                      "--output", str(out_path)]
            )
        assert result.exit_code == 0
        assert "custom_output" in result.output

    def test_render_no_synced_fails(self, runner, tmp_path, sample_wav_for_cli):
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli),
                  "--dir", str(tmp_path)]
        )
        result = runner.invoke(cli, ["render", "--project", str(tmp_path)])
        assert result.exit_code != 0
        assert "lyrics_synced.json" in result.output


class TestAuditCommand:
    def test_audit_help(self, runner):
        result = runner.invoke(cli, ["audit", "--help"])
        assert result.exit_code == 0
        assert "json-only" in result.output.lower() or "json" in result.output.lower()

    def test_audit_no_project_fails(self, runner, tmp_path):
        result = runner.invoke(cli, ["audit", "--project", str(tmp_path)])
        assert result.exit_code != 0

    def test_audit_no_synced_fails(self, runner, tmp_path, sample_wav_for_cli):
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli),
                  "--dir", str(tmp_path)]
        )
        result = runner.invoke(cli, ["audit", "--project", str(tmp_path)])
        assert result.exit_code != 0
        assert "lyrics_synced.json" in result.output


class TestFindProject:
    def test_find_project_with_explicit_path(self, runner, tmp_path):
        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        from cli.commands import _find_project
        result = _find_project(str(tmp_path))
        assert result == tmp_path.resolve()

    def test_find_project_invalid_path_raises(self):
        from cli.commands import _find_project
        with pytest.raises(Exception):
            _find_project("/nonexistent/path")

    def test_find_project_cwd(self, runner, tmp_path, monkeypatch):
        runner.invoke(cli, ["init", "--name", "Test", "--dir", str(tmp_path)])
        monkeypatch.chdir(tmp_path)
        from cli.commands import _find_project
        result = _find_project(None)
        assert result == tmp_path.resolve()

    def test_find_project_no_project_cwd_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from cli.commands import _find_project
        with pytest.raises(Exception, match="No project found"):
            _find_project(None)


class TestToRelative:
    def test_relative_path(self):
        from cli.commands import _to_relative
        result = _to_relative("/foo/bar/baz.txt", Path("/foo/bar"))
        assert result == "baz.txt"

    def test_absolute_when_not_relative(self):
        from cli.commands import _to_relative
        result = _to_relative("/other/path/file.txt", Path("/foo/bar"))
        assert result == "/other/path/file.txt"


class TestInitForceFlag:
    def test_init_existing_project_error(self, runner, tmp_path):
        runner.invoke(cli, ["init", "--name", "First", "--dir", str(tmp_path)])
        result = runner.invoke(cli, ["init", "--name", "Second", "--dir", str(tmp_path)])
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_init_data_dir_auto_discovers_audio(self, runner, tmp_path, suno_data_dir):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--data-dir", str(suno_data_dir), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Audio:" in result.output or "found" in result.output

    def test_init_data_dir_auto_discovers_lyrics(self, runner, tmp_path, suno_data_dir):
        result = runner.invoke(
            cli, ["init", "--name", "Test", "--data-dir", str(suno_data_dir), "--dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Lyrics:" in result.output or "found" in result.output


class TestAnalyzeVariations:
    def test_analyze_with_no_ingest_file(self, runner, tmp_path, sample_wav_for_cli):
        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        (tmp_path / "data" / "ingest.json").unlink(missing_ok=True)
        result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code == 0

    def test_analyze_multiple_vocal_stems(self, runner, tmp_path, sample_wav_for_cli):
        from unittest.mock import patch

        stem_dir = tmp_path / "data" / "cache" / "stems"
        stem_dir.mkdir(parents=True, exist_ok=True)
        _write_wav(stem_dir / "0 Lead Vocals.wav")
        _write_wav(stem_dir / "1 Backing Vocals.wav")

        runner.invoke(
            cli, ["init", "--name", "Test", "--audio", str(sample_wav_for_cli), "--dir", str(tmp_path)]
        )
        stem_path0 = str(stem_dir / "0 Lead Vocals.wav")
        stem_path1 = str(stem_dir / "1 Backing Vocals.wav")
        ingest_data = {
            "tier": "enhanced",
            "stems": [
                {"name": "Lead Vocals", "stem_type": "lead_vocals", "path": stem_path0, "format": "wav"},
                {"name": "Backing Vocals", "stem_type": "backing_vocals", "path": stem_path1, "format": "wav"},
            ],
        }
        (tmp_path / "data" / "ingest.json").write_text(json.dumps(ingest_data), encoding="utf-8")

        with patch("cli.commands.AudioAnalyzer.transcribe_vocal_stem", return_value={
            "language": "en", "language_probability": 0.9, "duration": 1.0,
            "segments": [{"start": 0.0, "end": 0.5, "text": "Hello world"}],
            "words": [{"word": "Hello", "start": 0.0, "end": 0.3, "probability": 0.9}],
        }):
            result = runner.invoke(cli, ["analyze", "--project", str(tmp_path)])
        assert result.exit_code == 0
