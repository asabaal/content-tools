"""Tests for HTML renderer."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.renderer.html_renderer import (
    render_text_to_image,
    get_output_path,
    render_animated_video,
)


@pytest.mark.asyncio
async def test_get_output_path_basic() -> None:
    """Test basic output path generation."""
    path = get_output_path(
        year=2026,
        month=2,
        day=15,
        monthly_theme="Test Theme",
        week_number=2,
        subtheme="Test Subtheme",
        slot_type="declarative_statement",
    )
    
    assert "20260215" in path
    assert "Test-Theme" in path
    assert "Test-Subtheme" in path
    assert "declarative_statement" in path
    assert path.endswith(".png")


@pytest.mark.asyncio
async def test_get_output_path_sanitization() -> None:
    """Test that special characters are sanitized in filename."""
    path = get_output_path(
        year=2026,
        month=2,
        day=15,
        monthly_theme="Test Theme!@#$",
        week_number=2,
        subtheme="Test/Subtheme",
        slot_type="declarative statement",
    )
    
    assert "20260215" in path
    assert "@" not in path
    assert "#" not in path
    assert "$" not in path
    # Check that subtheme is sanitized (space replaced with dash)
    assert "TestSubtheme" in path


@pytest.mark.asyncio
async def test_get_output_path_empty_subtheme() -> None:
    """Test output path with empty subtheme."""
    path = get_output_path(
        year=2026,
        month=2,
        day=15,
        monthly_theme="Test Theme",
        week_number=2,
        subtheme="",
        slot_type="post",
    )
    
    assert "week02" in path


@pytest.mark.asyncio
async def test_render_text_to_image_invalid_preset() -> None:
    """Test error when invalid style preset is provided."""
    with pytest.raises(Exception) as exc_info:
        await render_text_to_image(
            text="Test",
            slot_info={"type": "post"},
            style_preset="invalid_preset",
        )
    
    assert "Invalid style preset" in str(exc_info.value)


@pytest.mark.asyncio
async def test_render_text_to_image_with_background_override() -> None:
    """Test rendering with background color override."""
    with patch("src.renderer.html_renderer.async_playwright") as mock_playwright:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        await render_text_to_image(
            text="Test content",
            slot_info={
                "type": "post",
                "year": "2026",
                "month": "2",
                "day": "15",
                "week_number": "1",
                "subtheme": "Sub",
                "monthly_theme": "Theme",
            },
            background_color="#FF0000",
        )
        
        # Verify browser operations were called
        mock_browser.new_page.assert_called_once()
        mock_page.set_content.assert_called_once()
        mock_page.screenshot.assert_called_once()


@pytest.mark.asyncio
async def test_render_text_to_image_4_5_aspect_ratio() -> None:
    """Test rendering with 4:5 aspect ratio."""
    with patch("src.renderer.html_renderer.async_playwright") as mock_playwright:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        result = await render_text_to_image(
            text="Test",
            slot_info={
                "type": "post",
                "year": "2026",
                "month": "2",
                "day": "15",
                "week_number": "1",
                "subtheme": "Sub",
                "monthly_theme": "Theme",
            },
            aspect_ratio="4:5",
        )
        
        # Verify correct dimensions for 4:5
        call_kwargs = mock_browser.new_page.call_args[1]
        assert call_kwargs["viewport"]["width"] == 1080
        assert call_kwargs["viewport"]["height"] == 1350


@pytest.mark.asyncio
async def test_render_text_to_image_generates_output_path() -> None:
    """Test that output path is generated when not provided."""
    with patch("src.renderer.html_renderer.async_playwright") as mock_playwright:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.screenshot.return_value = None
        
        result = await render_text_to_image(
            text="Test",
            slot_info={
                "type": "post",
                "year": "2026",
                "month": "2",
                "day": "15",
                "week_number": "1",
                "subtheme": "Sub",
                "monthly_theme": "Theme",
            },
            output_path="",
        )
        
        assert result is not None
        assert ".png" in result


@pytest.mark.asyncio
async def test_render_text_to_image_with_provided_path() -> None:
    """Test rendering with provided output path."""
    with patch("src.renderer.html_renderer.async_playwright") as mock_playwright:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.screenshot.return_value = None
        
        custom_path = "/tmp/custom.png"
        result = await render_text_to_image(
            text="Test",
            slot_info={
                "type": "post",
                "year": "2026",
                "month": "2",
                "day": "15",
                "week_number": "1",
                "subtheme": "Sub",
                "monthly_theme": "Theme",
            },
            output_path=custom_path,
        )
        
        assert result == custom_path


@pytest.mark.asyncio
async def test_render_text_to_image_playwright_error() -> None:
    """Test error handling when Playwright fails."""
    with patch("src.renderer.html_renderer.async_playwright") as mock_playwright:
        mock_playwright.return_value.__aenter__.side_effect = Exception("Playwright failed")
        
        from src.errors.exceptions import RendererError
        
        with pytest.raises(RendererError) as exc_info:
            await render_text_to_image(
                text="Test",
                slot_info={
                    "type": "post",
                    "year": "2026",
                    "month": "2",
                    "day": "15",
                    "week_number": "1",
                    "subtheme": "Sub",
                    "monthly_theme": "Theme",
                },
            )
        
        assert "Failed to render HTML to image" in str(exc_info.value)


@pytest.mark.asyncio
async def test_render_text_to_image_with_gradient_params() -> None:
    """Test rendering with gradient parameters passes through to template."""
    with patch("src.renderer.html_renderer.async_playwright") as mock_playwright:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.screenshot.return_value = None

        result = await render_text_to_image(
            text="Test content",
            slot_info={
                "type": "post",
                "year": "2026",
                "month": "4",
                "day": "6",
                "week_number": "1",
                "subtheme": "Sub",
                "monthly_theme": "Theme",
            },
            output_path="/tmp/test_gradient.png",
            gradient_direction="vertical_top_bottom",
            gradient_colors=["#FF0000", "#0000FF"],
        )

        html_content = mock_page.set_content.call_args[0][0]
        assert "linear-gradient(to bottom" in html_content
        assert result == "/tmp/test_gradient.png"


@pytest.mark.asyncio
async def test_render_text_to_image_with_texture_params() -> None:
    """Test rendering with texture parameters passes through to template."""
    with patch("src.renderer.html_renderer.async_playwright") as mock_playwright:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.screenshot.return_value = None

        result = await render_text_to_image(
            text="Test content",
            slot_info={
                "type": "post",
                "year": "2026",
                "month": "4",
                "day": "6",
                "week_number": "1",
                "subtheme": "Sub",
                "monthly_theme": "Theme",
            },
            output_path="/tmp/test_texture.png",
            texture_type="noise_fine",
            texture_opacity=0.2,
            texture_blend_mode="overlay",
        )

        html_content = mock_page.set_content.call_args[0][0]
        assert "texture-overlay" in html_content
        assert "filter: url(#tex-noise)" in html_content
        assert result == "/tmp/test_texture.png"


@pytest.mark.asyncio
async def test_render_text_to_image_with_gradient_and_texture() -> None:
    """Test rendering with both gradient and texture parameters."""
    with patch("src.renderer.html_renderer.async_playwright") as mock_playwright:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.screenshot.return_value = None

        await render_text_to_image(
            text="Test content",
            slot_info={
                "type": "post",
                "year": "2026",
                "month": "4",
                "day": "6",
                "week_number": "1",
                "subtheme": "Sub",
                "monthly_theme": "Theme",
            },
            output_path="/tmp/test_both.png",
            gradient_direction="radial_center",
            gradient_colors=["#FF0000", "#0000FF"],
            texture_type="vignette_soft",
            texture_opacity=0.25,
        )

        html_content = mock_page.set_content.call_args[0][0]
        assert "radial-gradient(circle at center" in html_content
        assert "texture-overlay" in html_content


@pytest.mark.asyncio
async def test_render_text_to_image_backward_compat() -> None:
    """Test rendering without new params still works (backward compatibility)."""
    with patch("src.renderer.html_renderer.async_playwright") as mock_playwright:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.screenshot.return_value = None

        await render_text_to_image(
            text="Test content",
            slot_info={
                "type": "post",
                "year": "2026",
                "month": "4",
                "day": "6",
                "week_number": "1",
                "subtheme": "Sub",
                "monthly_theme": "Theme",
            },
            output_path="/tmp/test_compat.png",
        )

        html_content = mock_page.set_content.call_args[0][0]
        assert "background-color: #4A90E2" in html_content
        assert "linear-gradient" not in html_content
        assert "texture-overlay" not in html_content


@pytest.mark.asyncio
async def test_render_text_to_image_text_color_override() -> None:
    """Test text_color is passed through to template builder."""
    with patch("src.renderer.html_renderer.async_playwright") as mock_playwright:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.screenshot.return_value = None

        await render_text_to_image(
            text="Test content",
            slot_info={"type": "post", "year": "2026", "month": "4", "day": "6", "week_number": "1", "subtheme": "S", "monthly_theme": "T"},
            output_path="/tmp/test_color.png",
            text_color="#FF0000",
        )

        html_content = mock_page.set_content.call_args[0][0]
        assert "#FF0000" in html_content


@pytest.mark.asyncio
async def test_render_animated_video_video_duration_overrides_loop() -> None:
    """Test video_duration param overrides anim_loop."""
    from PIL import Image

    frame = Image.new("RGB", (1080, 1080), (0, 128, 255))

    with patch("src.renderer.html_renderer._render_text_layer_to_pil", return_value=Image.new("RGBA", (1080, 1080))), \
         patch("src.renderer.html_renderer.AnimationFrameGenerator") as mock_anim_cls, \
         patch("src.renderer.html_renderer.VideoEncoder") as mock_encoder_cls:
        mock_anim = MagicMock()
        mock_anim.generate_background_frame.return_value = frame
        mock_anim_cls.return_value = mock_anim
        mock_encoder = MagicMock()
        mock_encoder.__enter__ = MagicMock(return_value=mock_encoder)
        mock_encoder.__exit__ = MagicMock(return_value=False)
        mock_encoder_cls.return_value = mock_encoder

        result = await render_animated_video(
            text="Test",
            slot_info={"type": "post", "year": "2026", "month": "4", "day": "6", "week_number": "1", "subtheme": "S", "monthly_theme": "T"},
            output_path="/tmp/test.mp4",
            anim_loop=60,
            video_duration=5.0,
        )

        assert result == "/tmp/test.mp4"
        assert mock_encoder.write_frame.call_count == 150


@pytest.mark.asyncio
async def test_render_animated_video_video_duration_overrides_audio() -> None:
    """Test video_duration takes precedence over audio-derived duration."""
    from PIL import Image

    frame = Image.new("RGB", (1080, 1080), (0, 128, 255))

    with patch("src.renderer.html_renderer._render_text_layer_to_pil", return_value=Image.new("RGBA", (1080, 1080))), \
         patch("src.renderer.html_renderer.AnimationFrameGenerator") as mock_anim_cls, \
         patch("src.renderer.html_renderer.VideoEncoder") as mock_encoder_cls, \
         patch("src.renderer.html_renderer.get_audio_duration", return_value=10.0), \
         patch("src.renderer.html_renderer.mux_audio_video", return_value="/tmp/out.mp4"), \
         patch("pathlib.Path.rename"):
        mock_anim = MagicMock()
        mock_anim.generate_background_frame.return_value = frame
        mock_anim_cls.return_value = mock_anim
        mock_encoder = MagicMock()
        mock_encoder.__enter__ = MagicMock(return_value=mock_encoder)
        mock_encoder.__exit__ = MagicMock(return_value=False)
        mock_encoder_cls.return_value = mock_encoder

        await render_animated_video(
            text="Test",
            slot_info={"type": "post", "year": "2026", "month": "4", "day": "6", "week_number": "1", "subtheme": "S", "monthly_theme": "T"},
            output_path="/tmp/test.mp4",
            audio_path="/tmp/audio.mp3",
            video_duration=3.0,
        )

        assert mock_encoder.write_frame.call_count == 90


@pytest.mark.asyncio
async def test_render_text_layer_to_pil_invalid_preset() -> None:
    """Test _render_text_layer_to_pil raises error for invalid preset."""
    from src.renderer.html_renderer import _render_text_layer_to_pil
    from src.errors.exceptions import RendererError

    with pytest.raises(RendererError, match="Invalid style preset"):
        await _render_text_layer_to_pil(
            text="Test",
            slot_info={"type": "post"},
            width=1080,
            height=1080,
            style_preset="nonexistent",
        )


@pytest.mark.asyncio
async def test_render_text_layer_to_pil_render_error() -> None:
    """Test _render_text_layer_to_pil wraps playwright errors."""
    from src.renderer.html_renderer import _render_text_layer_to_pil
    from src.errors.exceptions import RendererError

    with patch("src.renderer.html_renderer.async_playwright") as mock_pw:
        mock_pw.return_value.__aenter__.side_effect = Exception("browser crash")
        with pytest.raises(RendererError, match="Failed to render text layer"):
            await _render_text_layer_to_pil(
                text="Test",
                slot_info={"type": "post"},
                width=1080,
                height=1080,
                style_preset="default",
            )


@pytest.mark.asyncio
async def test_render_animated_video_4_5_aspect_ratio() -> None:
    """Test render_animated_video with 4:5 aspect ratio uses correct dimensions."""
    from PIL import Image

    frame = Image.new("RGB", (1080, 1350), (0, 128, 255))

    with patch("src.renderer.html_renderer._render_text_layer_to_pil", return_value=Image.new("RGBA", (1080, 1350))), \
         patch("src.renderer.html_renderer.AnimationFrameGenerator") as mock_anim_cls, \
         patch("src.renderer.html_renderer.VideoEncoder") as mock_encoder_cls:
        mock_anim = MagicMock()
        mock_anim.generate_background_frame.return_value = frame
        mock_anim_cls.return_value = mock_anim
        mock_encoder = MagicMock()
        mock_encoder.__enter__ = MagicMock(return_value=mock_encoder)
        mock_encoder.__exit__ = MagicMock(return_value=False)
        mock_encoder_cls.return_value = mock_encoder

        await render_animated_video(
            text="Test",
            slot_info={"type": "post", "year": "2026", "month": "4", "day": "6", "week_number": "1", "subtheme": "S", "monthly_theme": "T"},
            output_path="/tmp/test_45.mp4",
            aspect_ratio="4:5",
        )

        mock_anim_cls.assert_called_once()
        assert mock_anim_cls.call_args[1]["width"] == 1080
        assert mock_anim_cls.call_args[1]["height"] == 1350


@pytest.mark.asyncio
async def test_render_animated_video_generates_output_path() -> None:
    """Test render_animated_video generates path when output_path is empty."""
    from PIL import Image

    frame = Image.new("RGB", (1080, 1080), (0, 128, 255))

    with patch("src.renderer.html_renderer._render_text_layer_to_pil", return_value=Image.new("RGBA", (1080, 1080))), \
         patch("src.renderer.html_renderer.AnimationFrameGenerator") as mock_anim_cls, \
         patch("src.renderer.html_renderer.VideoEncoder") as mock_encoder_cls:
        mock_anim = MagicMock()
        mock_anim.generate_background_frame.return_value = frame
        mock_anim_cls.return_value = mock_anim
        mock_encoder = MagicMock()
        mock_encoder.__enter__ = MagicMock(return_value=mock_encoder)
        mock_encoder.__exit__ = MagicMock(return_value=False)
        mock_encoder_cls.return_value = mock_encoder

        result = await render_animated_video(
            text="Test",
            slot_info={"type": "post", "year": "2026", "month": "4", "day": "6", "week_number": "1", "subtheme": "S", "monthly_theme": "T"},
            output_path="",
        )

        assert result.endswith(".mp4")


@pytest.mark.asyncio
async def test_render_text_to_image_with_background_image() -> None:
    from PIL import Image

    with patch("src.renderer.html_renderer._render_text_layer_to_pil", return_value=Image.new("RGBA", (1080, 1080))) as mock_render:
        result = await render_text_to_image(
            text="Test",
            slot_info={"type": "post", "year": "2026", "month": "4", "day": "6", "week_number": "1", "subtheme": "S", "monthly_theme": "T"},
            background_image_path="/tmp/bg_test.png",
        )

        assert result is not None


@pytest.mark.asyncio
async def test_render_animated_video_with_background_image() -> None:
    import tempfile
    from PIL import Image

    frame = Image.new("RGB", (1080, 1080), (0, 128, 255))
    bg_img = Image.new("RGB", (1024, 1024), (50, 100, 150))

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        bg_img.save(f.name)
        bg_path = f.name

    try:
        with patch("src.renderer.html_renderer._render_text_layer_to_pil", return_value=Image.new("RGBA", (1080, 1080))), \
             patch("src.renderer.html_renderer.AnimationFrameGenerator") as mock_anim_cls, \
             patch("src.renderer.html_renderer.VideoEncoder") as mock_encoder_cls:
            mock_anim = MagicMock()
            mock_anim.generate_background_frame.return_value = frame
            mock_anim_cls.return_value = mock_anim
            mock_encoder = MagicMock()
            mock_encoder.__enter__ = MagicMock(return_value=mock_encoder)
            mock_encoder.__exit__ = MagicMock(return_value=False)
            mock_encoder_cls.return_value = mock_encoder

            await render_animated_video(
                text="Test",
                slot_info={"type": "post", "year": "2026", "month": "4", "day": "6", "week_number": "1", "subtheme": "S", "monthly_theme": "T"},
                background_image_path=bg_path,
            )

            call_kwargs = mock_anim_cls.call_args[1]
            assert call_kwargs.get("background_image") is not None
    finally:
        import os
        os.unlink(bg_path)
