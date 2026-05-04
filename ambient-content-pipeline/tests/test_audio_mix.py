"""Tests for audio mixing module."""

import pytest
from unittest.mock import patch, MagicMock
from src.renderer.audio_mix import prepare_slot_audio
from src.errors.exceptions import RendererError


def test_prepare_slot_audio_success() -> None:
    with patch("src.renderer.audio_mix.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        path, dur = prepare_slot_audio(
            tts_path="/tmp/tts.mp3",
            music_path="/tmp/music.wav",
            output_path="/tmp/mixed.mp3",
            tts_duration=7.0,
            slot_video_duration=8.75,
        )
        assert path == "/tmp/mixed.mp3"
        assert dur == 8.75
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "-y" in cmd
        assert "-i" in cmd
        assert "/tmp/tts.mp3" in cmd
        assert "/tmp/music.wav" in cmd


def test_prepare_slot_audio_filter_chain() -> None:
    with patch("src.renderer.audio_mix.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        prepare_slot_audio(
            tts_path="/tmp/tts.mp3",
            music_path="/tmp/music.wav",
            output_path="/tmp/out.mp3",
            tts_duration=7.0,
            slot_video_duration=8.75,
        )
        cmd = mock_run.call_args[0][0]
        filter_idx = cmd.index("-filter_complex")
        filter_str = cmd[filter_idx + 1]
        assert "adelay=500|500" in filter_str
        assert "atrim=0:8.75" in filter_str
        assert "volume=0.3" in filter_str
        assert "amix=inputs=2" in filter_str
        assert "dropout_transition=2" in filter_str


def test_prepare_slot_audio_custom_volume() -> None:
    with patch("src.renderer.audio_mix.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        prepare_slot_audio(
            tts_path="/tmp/tts.mp3",
            music_path="/tmp/music.wav",
            output_path="/tmp/out.mp3",
            tts_duration=7.0,
            slot_video_duration=8.75,
            music_volume=0.5,
        )
        cmd = mock_run.call_args[0][0]
        filter_idx = cmd.index("-filter_complex")
        filter_str = cmd[filter_idx + 1]
        assert "volume=0.5" in filter_str


def test_prepare_slot_audio_ffmpeg_fail() -> None:
    with patch("src.renderer.audio_mix.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="codec not found")
        with pytest.raises(RendererError, match="ffmpeg audio mixing failed"):
            prepare_slot_audio(
                tts_path="/tmp/tts.mp3",
                music_path="/tmp/music.wav",
                output_path="/tmp/out.mp3",
                tts_duration=7.0,
                slot_video_duration=8.75,
            )


def test_prepare_slot_audio_timeout() -> None:
    import subprocess

    with patch("src.renderer.audio_mix.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffmpeg", timeout=60)
        with pytest.raises(RendererError, match="timed out"):
            prepare_slot_audio(
                tts_path="/tmp/tts.mp3",
                music_path="/tmp/music.wav",
                output_path="/tmp/out.mp3",
                tts_duration=7.0,
                slot_video_duration=8.75,
            )


def test_prepare_slot_audio_invalid_duration() -> None:
    with pytest.raises(RendererError, match="must be positive"):
        prepare_slot_audio(
            tts_path="/tmp/tts.mp3",
            music_path="/tmp/music.wav",
            output_path="/tmp/out.mp3",
            tts_duration=5.0,
            slot_video_duration=0,
        )


def test_prepare_slot_audio_negative_volume() -> None:
    with pytest.raises(RendererError, match="must be a non-negative number"):
        prepare_slot_audio(
            tts_path="/tmp/tts.mp3",
            music_path="/tmp/music.wav",
            output_path="/tmp/out.mp3",
            tts_duration=5.0,
            slot_video_duration=10.0,
            music_volume=-0.5,
        )


def test_prepare_slot_audio_output_params() -> None:
    with patch("src.renderer.audio_mix.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        prepare_slot_audio(
            tts_path="/tmp/tts.mp3",
            music_path="/tmp/music.wav",
            output_path="/tmp/out.mp3",
            tts_duration=7.0,
            slot_video_duration=8.75,
        )
        cmd = mock_run.call_args[0][0]
        assert "-ar" in cmd
        assert "44100" in cmd
        assert "-ac" in cmd
        assert "1" in cmd
        assert "/tmp/out.mp3" in cmd
