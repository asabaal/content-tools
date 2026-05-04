"""Tests for TTS module."""

import json
import sys
import types
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.renderer.tts import generate_tts, get_audio_duration, mux_audio_video
from src.errors.exceptions import RendererError


def _make_mock_edge_tts():
    mock_mod = types.ModuleType("edge_tts")
    mock_mod.Communicate = MagicMock()
    return mock_mod


@pytest.mark.asyncio
async def test_generate_tts_success() -> None:
    mock_communicate = AsyncMock()
    mock_communicate.save = AsyncMock()
    mock_mod = _make_mock_edge_tts()
    mock_mod.Communicate.return_value = mock_communicate

    with patch.dict(sys.modules, {"edge_tts": mock_mod}):
        result = await generate_tts("Hello world", "/tmp/out.mp3")
        assert result == "/tmp/out.mp3"
        mock_mod.Communicate.assert_called_once_with("Hello world", voice="en-US-AriaNeural")
        mock_communicate.save.assert_called_once_with("/tmp/out.mp3")


@pytest.mark.asyncio
async def test_generate_tts_custom_voice() -> None:
    mock_communicate = AsyncMock()
    mock_communicate.save = AsyncMock()
    mock_mod = _make_mock_edge_tts()
    mock_mod.Communicate.return_value = mock_communicate

    with patch.dict(sys.modules, {"edge_tts": mock_mod}):
        await generate_tts("Hello", "/tmp/out.mp3", voice="en-GB-SoniaNeural")
        mock_mod.Communicate.assert_called_once_with("Hello", voice="en-GB-SoniaNeural")


@pytest.mark.asyncio
async def test_generate_tts_not_installed() -> None:
    real_mod = sys.modules.get("edge_tts")
    try:
        sys.modules["edge_tts"] = None
        with pytest.raises(RendererError, match="edge-tts not installed"):
            await generate_tts("Hello", "/tmp/out.mp3")
    finally:
        if real_mod is not None:
            sys.modules["edge_tts"] = real_mod
        else:
            sys.modules.pop("edge_tts", None)


@pytest.mark.asyncio
async def test_generate_tts_generation_failure() -> None:
    mock_communicate = AsyncMock()
    mock_communicate.save = AsyncMock(side_effect=RuntimeError("network error"))
    mock_mod = _make_mock_edge_tts()
    mock_mod.Communicate.return_value = mock_communicate

    with patch.dict(sys.modules, {"edge_tts": mock_mod}):
        with pytest.raises(RendererError, match="TTS generation failed"):
            await generate_tts("Hello", "/tmp/out.mp3")


def test_get_audio_duration_success() -> None:
    ffprobe_output = json.dumps({"format": {"duration": "7.456"}})

    with patch("src.renderer.tts.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=ffprobe_output, returncode=0)
        result = get_audio_duration("/tmp/audio.mp3")
        assert result == 7.456
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffprobe"
        assert "-show_format" in cmd
        assert "/tmp/audio.mp3" in cmd


def test_get_audio_duration_zero() -> None:
    ffprobe_output = json.dumps({"format": {"duration": "0"}})

    with patch("src.renderer.tts.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=ffprobe_output, returncode=0)
        assert get_audio_duration("/tmp/silent.mp3") == 0.0


def test_get_audio_duration_missing_format() -> None:
    ffprobe_output = json.dumps({})

    with patch("src.renderer.tts.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=ffprobe_output, returncode=0)
        with pytest.raises(RendererError, match="ffprobe returned no duration"):
            get_audio_duration("/tmp/bad.mp3")


def test_get_audio_duration_ffprobe_not_found() -> None:
    with patch("src.renderer.tts.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(RendererError, match="ffprobe not found"):
            get_audio_duration("/tmp/audio.mp3")


def test_get_audio_duration_ffprobe_fail() -> None:
    import subprocess

    with patch("src.renderer.tts.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "ffprobe", stderr="error")
        with pytest.raises(RendererError, match="ffprobe failed"):
            get_audio_duration("/tmp/audio.mp3")


def test_mux_audio_video_success() -> None:
    with patch("src.renderer.tts.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = mux_audio_video("/tmp/video.mp4", "/tmp/audio.mp3", "/tmp/out.mp4")
        assert result == "/tmp/out.mp4"
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "-y" in cmd
        assert "-c:v" in cmd
        assert "copy" in cmd
        assert "-c:a" in cmd
        assert "aac" in cmd
        assert "-shortest" in cmd
        assert "+faststart" in cmd


def test_mux_audio_video_ffmpeg_not_found() -> None:
    with patch("src.renderer.tts.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(RendererError, match="ffmpeg not found"):
            mux_audio_video("/tmp/video.mp4", "/tmp/audio.mp3", "/tmp/out.mp4")


def test_mux_audio_video_ffmpeg_fail() -> None:
    with patch("src.renderer.tts.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="encode error")
        with pytest.raises(RendererError, match="ffmpeg mux failed"):
            mux_audio_video("/tmp/video.mp4", "/tmp/audio.mp3", "/tmp/out.mp4")


def test_get_audio_duration_timeout() -> None:
    import subprocess

    with patch("src.renderer.tts.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired("ffprobe", 30)
        with pytest.raises(RendererError, match="ffprobe timed out"):
            get_audio_duration("/tmp/audio.mp3")


def test_get_audio_duration_non_numeric_duration() -> None:
    ffprobe_output = json.dumps({"format": {"duration": "not_a_number"}})

    with patch("src.renderer.tts.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=ffprobe_output, returncode=0)
        with pytest.raises(RendererError, match="non-numeric duration"):
            get_audio_duration("/tmp/audio.mp3")


def test_mux_audio_video_timeout() -> None:
    import subprocess

    with patch("src.renderer.tts.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 120)
        with pytest.raises(RendererError, match="ffmpeg mux timed out"):
            mux_audio_video("/tmp/video.mp4", "/tmp/audio.mp3", "/tmp/out.mp4")
