"""Tests for music generation module."""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.renderer.music_gen import (
    calculate_music_duration,
    calculate_slot_video_duration,
    generate_music_prompt_from_theme,
    generate_background_music,
)
from src.errors.exceptions import RendererError


def test_calculate_music_duration_short() -> None:
    assert calculate_music_duration(6.0) == 0.5 + 6.0 + 1.5


def test_calculate_music_duration_long() -> None:
    assert calculate_music_duration(20.0) == 0.5 + 20.0 + 3.0


def test_calculate_music_duration_very_long() -> None:
    assert calculate_music_duration(100.0) == 0.5 + 100.0 + 3.0


def test_calculate_music_duration_tail_capped() -> None:
    tail = min(3.0, 20.0 * 0.25)
    assert tail == 3.0


def test_calculate_music_duration_tail_uncapped() -> None:
    tail = min(3.0, 6.0 * 0.25)
    assert tail == 1.5


def test_calculate_slot_video_duration_short() -> None:
    assert calculate_slot_video_duration(6.0) == 0.5 + 6.0 + 1.5


def test_calculate_slot_video_duration_long() -> None:
    assert calculate_slot_video_duration(20.0) == 0.5 + 20.0 + 3.0


@pytest.mark.asyncio
async def test_generate_music_prompt_from_theme() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "gentle ambient piano, slow tempo"}
    mock_response.raise_for_status = MagicMock()

    mock_post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await generate_music_prompt_from_theme("Stability in Christ")
        assert result == "gentle ambient piano, slow tempo"


@pytest.mark.asyncio
async def test_generate_music_prompt_from_theme_empty_response() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": ""}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(RendererError, match="Empty response"):
            await generate_music_prompt_from_theme("Test")


@pytest.mark.asyncio
async def test_generate_music_prompt_from_theme_http_error() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("Server error")

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(Exception, match="Server error"):
            await generate_music_prompt_from_theme("Test")


def test_generate_background_music_success() -> None:
    json_output = json.dumps({"status": "ok", "path": "/tmp/music.wav", "duration": 23.5})

    with patch("src.renderer.music_gen.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=json_output, stderr="")
        result = generate_background_music("piano music", 30.0, "/tmp/music.wav")
        assert result == "/tmp/music.wav"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "--prompt" in cmd
        assert "piano music" in cmd
        assert "--duration" in cmd
        assert "30.0" in cmd
        assert "--outfile" in cmd
        assert "/tmp/music.wav" in cmd


def test_generate_background_music_with_seed() -> None:
    json_output = json.dumps({"status": "ok", "path": "/tmp/music.wav", "duration": 10.0})

    with patch("src.renderer.music_gen.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=json_output, stderr="")
        generate_background_music("piano", 10.0, "/tmp/out.wav", seed=42)
        cmd = mock_run.call_args[0][0]
        assert "--seed" in cmd
        assert "42" in cmd


def test_generate_background_music_nonzero_exit() -> None:
    with patch("src.renderer.music_gen.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="model load failed")
        with pytest.raises(RendererError, match="ACE-Step failed"):
            generate_background_music("piano", 10.0, "/tmp/out.wav")


def test_generate_background_music_timeout() -> None:
    import subprocess

    with patch("src.renderer.music_gen.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="python", timeout=600)
        with pytest.raises(RendererError, match="timed out"):
            generate_background_music("piano", 10.0, "/tmp/out.wav")


def test_generate_background_music_bad_json() -> None:
    with patch("src.renderer.music_gen.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="not json", stderr="")
        with pytest.raises(RendererError, match="non-JSON"):
            generate_background_music("piano", 10.0, "/tmp/out.wav")


def test_generate_background_music_error_status() -> None:
    json_output = json.dumps({"status": "error", "message": "out of memory"})

    with patch("src.renderer.music_gen.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=json_output, stderr="")
        with pytest.raises(RendererError, match="out of memory"):
            generate_background_music("piano", 10.0, "/tmp/out.wav")


def test_generate_background_music_custom_params() -> None:
    json_output = json.dumps({"status": "ok", "path": "/tmp/out.wav", "duration": 30.0})

    with patch("src.renderer.music_gen.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=json_output, stderr="")
        generate_background_music("jazz", 30.0, "/tmp/out.wav", steps=40, guidance=10.0)
        cmd = mock_run.call_args[0][0]
        assert "--steps" in cmd
        assert "40" in cmd
        assert "--guidance" in cmd
        assert "10.0" in cmd
