"""Tests for AI background image generation."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.renderer.image_gen import (
    generate_background_image,
    generate_image_prompt_from_theme,
)
from src.errors.exceptions import RendererError


@pytest.mark.asyncio
async def test_generate_image_prompt_from_theme() -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "ethereal watercolor sunrise soft pastels"}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await generate_image_prompt_from_theme("faith, hope, and love")
        assert result == "ethereal watercolor sunrise soft pastels"


@pytest.mark.asyncio
async def test_generate_image_prompt_empty_response() -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": ""}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(RendererError, match="Empty response"):
            await generate_image_prompt_from_theme("test")


@pytest.mark.asyncio
async def test_generate_background_image_success() -> None:
    with patch("src.renderer.image_gen.asyncio.create_subprocess_exec") as mock_proc:
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            json.dumps({"status": "ok", "path": "/tmp/bg.png"}).encode(),
            b"",
        )
        mock_proc.return_value = mock_process

        result = await generate_background_image(
            prompt="abstract sunrise",
            output_path="/tmp/bg.png",
        )
        assert result == "/tmp/bg.png"
        mock_proc.assert_called_once()


@pytest.mark.asyncio
async def test_generate_background_image_timeout() -> None:
    import asyncio

    with patch("src.renderer.image_gen.asyncio.create_subprocess_exec") as mock_proc:
        mock_process = AsyncMock()
        mock_process.communicate.side_effect = asyncio.TimeoutError()
        mock_proc.return_value = mock_process

        with pytest.raises(RendererError, match="timed out"):
            await generate_background_image(
                prompt="test",
                output_path="/tmp/bg.png",
            )


@pytest.mark.asyncio
async def test_generate_background_image_nonzero_exit() -> None:
    with patch("src.renderer.image_gen.asyncio.create_subprocess_exec") as mock_proc:
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (
            json.dumps({"status": "error", "message": "OOM"}).encode(),
            b"stderr output",
        )
        mock_proc.return_value = mock_process

        with pytest.raises(RendererError, match="SD3 failed"):
            await generate_background_image(
                prompt="test",
                output_path="/tmp/bg.png",
            )


@pytest.mark.asyncio
async def test_generate_background_image_non_json_output() -> None:
    with patch("src.renderer.image_gen.asyncio.create_subprocess_exec") as mock_proc:
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"not json at all", b"")
        mock_proc.return_value = mock_process

        with pytest.raises(RendererError, match="non-JSON"):
            await generate_background_image(
                prompt="test",
                output_path="/tmp/bg.png",
            )


@pytest.mark.asyncio
async def test_generate_background_image_error_status() -> None:
    with patch("src.renderer.image_gen.asyncio.create_subprocess_exec") as mock_proc:
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            json.dumps({"status": "error", "message": "model load failed"}).encode(),
            b"",
        )
        mock_proc.return_value = mock_process

        with pytest.raises(RendererError, match="model load failed"):
            await generate_background_image(
                prompt="test",
                output_path="/tmp/bg.png",
            )


@pytest.mark.asyncio
async def test_generate_background_image_with_seed() -> None:
    with patch("src.renderer.image_gen.asyncio.create_subprocess_exec") as mock_proc:
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            json.dumps({"status": "ok", "path": "/tmp/bg.png"}).encode(),
            b"",
        )
        mock_proc.return_value = mock_process

        await generate_background_image(
            prompt="test",
            output_path="/tmp/bg.png",
            seed=42,
        )
        call_args = mock_proc.call_args[0]
        assert "--seed" in call_args
        assert "42" in call_args
