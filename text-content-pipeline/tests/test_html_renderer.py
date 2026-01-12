"""Tests for HTML renderer."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.renderer.html_renderer import render_text_to_image, get_output_path


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
