"""HTML renderer using headless browser."""

from datetime import datetime
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
from src.renderer.template_builder import build_html
from src.errors.exceptions import RendererError


async def render_text_to_image(
    text: str,
    slot_info: dict[str, str],
    output_path: str = "",
    style_preset: str = "default",
    background_color: str | None = None,
    aspect_ratio: Literal["1:1", "4:5"] = "1:1",
) -> str:
    """Render text content to a PNG image.

    Args:
        text: The text content to render
        slot_info: Dictionary with slot information (type, date, week_number, subtheme, monthly_theme)
        output_path: Path where image should be saved (or None to let function generate)
        style_preset: Name of colorful style preset
        background_color: Optional override color
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

    preset = COLORFUL_PRESETS[style_preset].copy()
    
    # Override background color if specified
    if background_color:
        preset["background"] = background_color

    # Set dimensions based on aspect ratio
    if aspect_ratio == "4:5":
        width = 1080
        height = 1350
    else:
        width = DEFAULT_IMAGE_WIDTH
        height = DEFAULT_IMAGE_HEIGHT

    # Generate HTML using template builder
    html_content = build_html(text, slot_info, preset, width, height)

    # Generate filename if not provided
    if not output_path:
        output_path = get_output_path(
            year=int(slot_info.get("year", datetime.now().year)),
            month=int(slot_info.get("month", datetime.now().month)),
            day=int(slot_info.get("day", datetime.now().day)),
            monthly_theme=slot_info.get("monthly_theme", ""),
            week_number=int(slot_info.get("week_number", 1)),
            subtheme=slot_info.get("subtheme", ""),
            slot_type=slot_info.get("type", "post"),
        )

    # Render to image
    return await _render_html_to_image(html_content, output_path, width, height)


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

            await page.set_content(html)

            screenshot_path = Path(output_path)
            await page.screenshot(
                path=str(screenshot_path),
                full_page=False,
                type="png",
            )

            await browser.close()

            return str(screenshot_path)

    except Exception as e:
        raise RendererError(f"Failed to render HTML to image: {e}") from e


def get_output_path(
    year: int,
    month: int,
    day: int,
    monthly_theme: str,
    week_number: int,
    subtheme: str,
    slot_type: str,
) -> str:
    """Generate output path for a daily post image.

    Args:
        year: Calendar year
        month: Calendar month (1-12)
        day: Calendar day (1-31)
        monthly_theme: Monthly theme text
        week_number: Week number
        subtheme: Subtheme text
        slot_type: Slot type identifier

    Returns:
        Full path for image file
    """
    import re
    
    def sanitize(s: str) -> str:
        s = re.sub(r'[^\w\s-]', '', s)
        s = re.sub(r'\s+', '-', s)
        return s[:80] if len(s) > 80 else s
    
    theme_part = sanitize(monthly_theme)
    subtheme_part = sanitize(subtheme) if subtheme else f"week{week_number:02d}"
    type_part = sanitize(slot_type)
    
    filename = f"{year:04d}{month:02d}{day:02d}_{theme_part}_week{week_number:02d}_{subtheme_part}_{type_part}.{IMAGE_FORMAT}"
    return str(IMAGES_DIR / filename)