"""HTML renderer using headless browser."""

import asyncio
from pathlib import Path
from typing import Literal

from playwright.async_api import async_playwright

from src.config.defaults import (
    COLORFUL_PRESETS,
    DEFAULT_IMAGE_HEIGHT,
    DEFAULT_IMAGE_WIDTH,
    IMAGES_DIR,
    IMAGE_FORMAT,
)
from src.errors.exceptions import RendererError
from src.renderer.template_builder import build_html


async def render_text_to_image(
    text: str,
    output_path: str,
    style_preset: str = "default",
    metadata: dict[str, str] | None = None,
    aspect_ratio: Literal["1:1", "4:5"] = "1:1",
) -> str:
    """Render text content to a PNG image.

    Args:
        text: The text content to render
        output_path: Path where image should be saved (or None for temp)
        style_preset: Name of colorful style preset
        metadata: Optional metadata dict (e.g., theme, date)
        aspect_ratio: Image aspect ratio ("1:1" or "4:5")

    Returns:
        Path to rendered image file

    Raises:
        RendererError: If rendering fails
    """
    # Get preset configuration
    if style_preset not in COLORFUL_PRESETS:
        raise RendererError(
            f"Invalid style preset '{style_preset}'. "
            f"Available: {list(COLORFUL_PRESETS.keys())}"
        )

    preset = COLORFUL_PRESETS[style_preset]

    # Set dimensions based on aspect ratio
    if aspect_ratio == "4:5":
        width = 1080
        height = 1350
    else:
        width = DEFAULT_IMAGE_WIDTH
        height = DEFAULT_IMAGE_HEIGHT

    # Generate HTML
    html_content = build_html(text, preset, metadata, width, height)

    # Render to image
    return await _render_html_to_image(html_content, output_path, width, height)


def _generate_html_v2(
    text: str,
    preset: dict[str, str | int],
    metadata: dict[str, str] | None,
    max_width: int,
    max_height: int,
) -> str:
    """Generate HTML from template and content.

    Args:
        text: Text content
        preset: Style preset configuration
        metadata: Optional metadata
        max_width: Max image width
        max_height: Max image height

    Returns:
        Complete HTML string
    """
    # Read template
    template_path = Path(__file__).parent / "templates" / "template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Build metadata HTML if provided
    metadata_html = ""
    if metadata:
        metadata_lines = []
        if "theme" in metadata:
            metadata_lines.append(f'<div class="metadata-line">{metadata["theme"]}</div>')
        if "subtheme" in metadata:
            metadata_lines.append(f'<div class="metadata-line">{metadata["subtheme"]}</div>')
        if "date" in metadata:
            metadata_lines.append(f'<div class="metadata-line">{metadata["date"]}</div>')

        if metadata_lines:
            metadata_html = '<div class="metadata">\n' + "\n".join(metadata_lines) + "\n</div>"

    # Calculate sizes
    font_size = int(preset.get("font_size", 48))
    padding = int(preset.get("padding", 80))
    metadata_font_size = font_size // 2
    metadata_margin = font_size // 2
    metadata_padding = font_size // 4
    preset_width = int(preset.get("max_width", max_width))

    # Fill template
    return template.format(
        background_color=preset.get("background", "#4A90E2"),
        text_color=preset.get("text_color", "#FFFFFF"),
        font_size=font_size,
        padding=padding,
        max_width=preset_width - (2 * padding),
        metadata_html=metadata_html,
        metadata_font_size=metadata_font_size,
        metadata_margin=metadata_margin,
        metadata_padding=metadata_padding,
        text_content=text,
    )


async def _render_html_to_image(
    html: str,
    output_path: str,
    width: int,
    height: int,
) -> str:
    """Render HTML to PNG image using Playwright.

    Args:
        html: HTML content to render
        output_path: Where to save the image
        width: Viewport width
        height: Viewport height

    Returns:
        Path to saved image

    Raises:
        RendererError: If rendering fails
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                viewport={"width": width, "height": height},
            )

            # Set HTML content
            await page.set_content(html)

            # Take screenshot
            screenshot_path = Path(output_path)
            await page.screenshot(
                path=str(screenshot_path),
                full_page=False,
                type="png",
            )

            await browser.close()

            return str(screenshot_path)

    except Exception as e:
        raise RendererError(f"Failed to render HTML to image: {e}")


def get_output_path(
    year: int,
    month: int,
    day: int,
    slot_type: str,
) -> str:
    """Generate output path for a daily post image.

    Args:
        year: Year
        month: Month (1-12)
        day: Day (1-31)
        slot_type: Slot type identifier

    Returns:
        Full path for image file
    """
    filename = f"{year:04d}-{month:02d}-{day:02d}_{slot_type}.{IMAGE_FORMAT}"
    return str(IMAGES_DIR / filename)
