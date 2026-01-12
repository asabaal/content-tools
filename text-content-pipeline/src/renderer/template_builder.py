"""HTML template builder for rendering."""

from typing import Literal


def build_html(
    text: str,
    preset: dict[str, str | int],
    metadata: dict[str, str] | None,
    max_width: int,
    max_height: int,
) -> str:
    """Build HTML from content and style.

    Args:
        text: Text content
        preset: Style preset configuration
        metadata: Optional metadata
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

    # Metadata settings
    metadata_font_size = font_size // 2
    metadata_margin = font_size // 2
    metadata_padding = font_size // 4

    # Build metadata HTML
    metadata_html = ""
    if metadata:
        lines = []
        if "theme" in metadata:
            lines.append(f'            <div class="metadata-line">{metadata["theme"]}</div>')
        if "subtheme" in metadata:
            lines.append(f'            <div class="metadata-line">{metadata["subtheme"]}</div>')
        if "date" in metadata:
            lines.append(f'            <div class="metadata-line">{metadata["date"]}</div>')
        if lines:
            metadata_html = f'        <div class="metadata">\n' + "\n".join(lines) + f'\n        </div>'

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

        .metadata {{
            font-size: {metadata_font_size}px;
            opacity: 0.7;
            margin-bottom: {metadata_margin}px;
            padding-bottom: {metadata_padding}px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.3);
        }}

        .metadata-line {{
            margin: 2px 0;
        }}

        .text-content {{
            font-size: {font_size}px;
            font-weight: 400;
            line-height: 1.4;
        }}
    </style>
</head>
<body>
    <div class="card">
{metadata_html}
        <div class="text-content">
            {text}
        </div>
    </div>
</body>
</html>
"""
    return html
