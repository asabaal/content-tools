"""HTML template builder for rendering."""

from datetime import datetime
from typing import Literal


def build_html(
    text: str,
    slot_info: dict[str, str],  # Contains: type, date, week_number, subtheme, monthly_theme, year, month, day
    preset: dict[str, str | int],
    max_width: int,
    max_height: int,
) -> str:
    """Build HTML from content and style.

    Args:
        text: Text content
        slot_info: Dictionary with slot information
        preset: Style preset configuration
        max_width: Max image width
        max_height: Max image height

    Returns:
        Complete HTML string
    """
    # Get preset values
    background = preset.get("background", "#4A90E2")
    text_color = preset.get("text_color", "#FFFFFF")
    font_size = int(preset.get("font_size", 48))
    padding = int(preset.get("padding", 80))
    preset_width = int(preset.get("max_width", max_width))

    # Extract slot info with defaults
    year = int(slot_info.get("year", datetime.now().year))
    month = int(slot_info.get("month", datetime.now().month))
    day = int(slot_info.get("day", datetime.now().day))
    week_number = int(slot_info.get("week_number", 1))
    subtheme = slot_info.get("subtheme", "")
    monthly_theme = slot_info.get("monthly_theme", "Theme")

    # Metadata settings
    metadata_font_size = font_size // 2
    metadata_margin = font_size // 2
    metadata_padding = font_size // 4

    # Build prominent monthly theme header
    theme_header_html = f"""        <div class="theme-header">
            <div class="theme-value">{monthly_theme}</div>
        </div>"""

    # Build week/subtheme metadata (stylized)
    week_metadata_html = ""
    if subtheme:
        week_metadata_html = f"""        <div class="week-metadata">
            <div class="subtheme-pill">{subtheme}</div>
        </div>"""

    # Build complete HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Content Post</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: {background};
            color: {text_color};
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: {padding}px;
        }}

        .card {{
            width: 100%;
            max-width: {preset_width}px;
        }}

        .theme-header {{
            text-align: center;
            font-size: {metadata_font_size}px;
            font-weight: 700;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: {metadata_margin}px;
            padding-bottom: {metadata_padding}px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.4);
        }}

        .theme-label {{
            opacity: 0.7;
            font-size: {metadata_font_size}px;
            margin-bottom: {metadata_font_size // 2}px;
        }}

        .theme-value {{
            font-size: {font_size}px;
        }}

        .week-metadata {{
            display: flex;
            gap: 10px;
            margin-bottom: {metadata_margin}px;
            justify-content: center;
        }}

        .week-pill {{
            background: rgba(255, 255,  255, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: {metadata_font_size}px;
            font-weight: 600;
            letter-spacing: 1px;
        }}

        .subtheme-pill {{
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: {metadata_font_size}px;
            font-size: {metadata_font_size}px;
            font-weight: 600;
            letter-spacing: 1px;
        }}

        .text-content {{
            font-size: {font_size}px;
            font-weight: 400;
            line-height: 1.4;
            text-align: center;
            margin-top: {font_size}px;
        }}
    </style>
</head>
<body>
    <div class="card">
{theme_header_html}
{week_metadata_html}
        <div class="text-content">
            {text}
        </div>
    </div>
</body>
</html>
"""
    return html
