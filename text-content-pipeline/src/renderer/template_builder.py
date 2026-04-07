"""HTML template builder for rendering."""

from datetime import datetime
from typing import Literal

from src.config.defaults import (
    GradientDirection,
    TextureBlendMode,
    TextureType,
)


def _build_gradient_css(
    gradient_direction: GradientDirection,
    gradient_colors: list[str],
    gradient_stops: list[float] | None = None,
) -> str:
    """Build CSS background property for a gradient.

    Args:
        gradient_direction: Direction of the gradient
        gradient_colors: List of 2-4 hex color strings
        gradient_stops: Optional normalized stop positions (0.0-1.0)

    Returns:
        CSS background property value string
    """
    num_colors = len(gradient_colors)
    if gradient_stops is None:
        gradient_stops = [round(i / (num_colors - 1), 2) for i in range(num_colors)]

    color_stops = ", ".join(
        f"{color} {stop * 100}%"
        for color, stop in zip(gradient_colors, gradient_stops)
    )

    direction_map: dict[str, str] = {
        "vertical_top_bottom": f"linear-gradient(to bottom, {color_stops})",
        "vertical_bottom_top": f"linear-gradient(to top, {color_stops})",
        "horizontal_left_right": f"linear-gradient(to right, {color_stops})",
        "horizontal_right_left": f"linear-gradient(to left, {color_stops})",
        "diagonal_tl_br": f"linear-gradient(135deg, {color_stops})",
        "diagonal_tr_bl": f"linear-gradient(225deg, {color_stops})",
        "radial_center": f"radial-gradient(circle at center, {color_stops})",
        "radial_top": f"radial-gradient(ellipse at top, {color_stops})",
        "radial_bottom": f"radial-gradient(ellipse at bottom, {color_stops})",
    }

    return direction_map[gradient_direction]


def _build_texture_css(
    texture_type: TextureType,
    texture_opacity: float,
    texture_blend_mode: TextureBlendMode,
) -> tuple[str, str]:
    """Build CSS, SVG defs, and HTML for a texture overlay.

    Args:
        texture_type: Type of texture overlay
        texture_opacity: Opacity from 0.0 to 1.0
        texture_blend_mode: CSS mix-blend-mode value

    Returns:
        Tuple of (css_string, html_string) for the texture overlay
    """
    if texture_type == "none":
        return "", ""

    base_css = f"""
        .texture-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: white;
            pointer-events: none;
            opacity: {texture_opacity};
            mix-blend-mode: {texture_blend_mode};
            z-index: 1;
        }}"""

    overlay_html = '        <div class="texture-overlay'

    if texture_type == "noise_fine":
        svg_defs = """        <svg class="svg-defs">
            <defs>
                <filter id="tex-noise" x="0%" y="0%" width="100%" height="100%">
                    <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/>
                </filter>
            </defs>
        </svg>"""
        css = base_css + """
        .svg-defs { position: absolute; width: 0; height: 0; }
        .texture-overlay.noise-fine { filter: url(#tex-noise); }"""
        return css, svg_defs + "\n" + overlay_html + ' noise-fine"></div>'

    elif texture_type == "noise_coarse":
        svg_defs = """        <svg class="svg-defs">
            <defs>
                <filter id="tex-noise" x="0%" y="0%" width="100%" height="100%">
                    <feTurbulence type="fractalNoise" baseFrequency="0.15" numOctaves="4" stitchTiles="stitch"/>
                </filter>
            </defs>
        </svg>"""
        css = base_css + """
        .svg-defs { position: absolute; width: 0; height: 0; }
        .texture-overlay.noise-coarse { filter: url(#tex-noise); }"""
        return css, svg_defs + "\n" + overlay_html + ' noise-coarse"></div>'

    elif texture_type == "grain_film":
        svg_defs = """        <svg class="svg-defs">
            <defs>
                <filter id="tex-noise" x="0%" y="0%" width="100%" height="100%">
                    <feTurbulence type="fractalNoise" baseFrequency="0.5" numOctaves="5" stitchTiles="stitch"/>
                    <feColorMatrix type="saturate" values="0"/>
                </filter>
            </defs>
        </svg>"""
        css = base_css + """
        .svg-defs { position: absolute; width: 0; height: 0; }
        .texture-overlay.grain-film { filter: url(#tex-noise); }"""
        return css, svg_defs + "\n" + overlay_html + ' grain-film"></div>'

    elif texture_type == "paper_subtle":
        svg_defs = """        <svg class="svg-defs">
            <defs>
                <filter id="tex-noise" x="0%" y="0%" width="100%" height="100%">
                    <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="5" stitchTiles="stitch"/>
                    <feDiffuseLighting in="turbulence" lighting-color="white" surfaceScale="2">
                        <feDistantLight azimuth="45" elevation="55"/>
                    </feDiffuseLighting>
                </filter>
            </defs>
        </svg>"""
        css = base_css + """
        .svg-defs { position: absolute; width: 0; height: 0; }
        .texture-overlay.paper-subtle { filter: url(#tex-noise); }"""
        return css, svg_defs + "\n" + overlay_html + ' paper-subtle"></div>'

    elif texture_type == "vignette_soft":
        css = base_css + """
        .texture-overlay.vignette-soft {
            background: radial-gradient(ellipse at center, transparent 40%, rgba(0, 0, 0, 0.7) 100%);
        }"""
        return css, overlay_html + ' vignette-soft"></div>'

    elif texture_type == "vignette_heavy":
        css = base_css + """
        .texture-overlay.vignette-heavy {
            background: radial-gradient(ellipse at center, transparent 20%, rgba(0, 0, 0, 0.9) 100%);
        }"""
        return css, overlay_html + ' vignette-heavy"></div>'

    return "", ""


def build_html(
    text: str,
    slot_info: dict[str, str],
    preset: dict[str, str | int],
    max_width: int,
    max_height: int,
    gradient_direction: GradientDirection | None = None,
    gradient_colors: list[str] | None = None,
    gradient_stops: list[float] | None = None,
    texture_type: TextureType | None = None,
    texture_opacity: float | None = None,
    texture_blend_mode: TextureBlendMode | None = None,
    transparent_bg: bool = False,
) -> str:
    """Build HTML from content and style.

    Args:
        text: Text content
        slot_info: Dictionary with slot information
        preset: Style preset configuration
        max_width: Max image width
        max_height: Max image height
        gradient_direction: Optional gradient direction
        gradient_colors: Optional list of 2-4 hex color strings
        gradient_stops: Optional normalized stop positions (0.0-1.0)
        texture_type: Optional texture overlay type
        texture_opacity: Optional texture opacity (0.0-1.0)
        texture_blend_mode: Optional texture blend mode
        transparent_bg: If True, render with transparent background

    Returns:
        Complete HTML string
    """
    from src.config.defaults import DEFAULT_TEXTURE_BLEND_MODE, DEFAULT_TEXTURE_OPACITY

    background = preset.get("background", "#4A90E2")
    text_color = preset.get("text_color", "#FFFFFF")
    font_size = int(preset.get("font_size", 48))
    padding = int(preset.get("padding", 80))
    preset_width = int(preset.get("max_width", max_width))

    # Determine background CSS
    use_gradient = (
        gradient_direction is not None
        and gradient_colors is not None
        and len(gradient_colors) >= 2
    )
    if transparent_bg:
        bg_css_property = "background-color"
        bg_css_value = "transparent"
    elif use_gradient:
        assert gradient_direction is not None
        assert gradient_colors is not None
        bg_css_property = "background"
        bg_css_value = _build_gradient_css(
            gradient_direction,
            gradient_colors,
            gradient_stops,
        )
    else:
        bg_css_property = "background-color"
        bg_css_value = background

    # Determine texture
    if transparent_bg:
        effective_texture_type: TextureType = "none"
        texture_css, texture_html = "", ""
    else:
        effective_texture_type = texture_type or "none"
        effective_texture_opacity = texture_opacity if texture_opacity is not None else DEFAULT_TEXTURE_OPACITY
        effective_texture_blend = texture_blend_mode or DEFAULT_TEXTURE_BLEND_MODE

        texture_css, texture_html = _build_texture_css(
            effective_texture_type,
            effective_texture_opacity,
            effective_texture_blend,
        )

    # Extract slot info with defaults
    year = int(slot_info.get("year", datetime.now().year))
    month = int(slot_info.get("month", datetime.now().month))
    day = int(slot_info.get("day", datetime.now().day))
    week_number = int(slot_info.get("week_number", 1))
    subtheme = slot_info.get("subtheme", "")
    subtheme_subtitle = slot_info.get("subtheme_subtitle", "")
    monthly_theme = slot_info.get("monthly_theme", "Theme")

    display_subtheme = subtheme_subtitle if subtheme_subtitle else subtheme

    metadata_font_size = font_size // 2
    metadata_margin = font_size // 2
    metadata_padding = font_size // 4

    theme_header_html = f"""        <div class="theme-header">
            <div class="theme-value">{monthly_theme}</div>
        </div>"""

    week_metadata_html = ""
    if display_subtheme:
        week_metadata_html = f"""        <div class="week-metadata">
            <div class="subtheme-pill">{display_subtheme}</div>
        </div>"""

    card_z_index = "z-index: 2; position: relative;" if texture_html else ""

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
            {bg_css_property}: {bg_css_value};
            color: {text_color};
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: {padding}px;
        }}
{texture_css}
        .card {{
            width: 100%;
            max-width: {preset_width}px;
            {card_z_index}
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
{texture_html}
</body>
</html>
"""
    return html
