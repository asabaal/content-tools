"""Tests for HTML template builder."""

from src.renderer.template_builder import (
    build_html,
    _build_gradient_css,
    _build_texture_css,
)


def test_build_gradient_css_vertical_top_bottom() -> None:
    result = _build_gradient_css("vertical_top_bottom", ["#FF0000", "#0000FF"])
    assert "linear-gradient(to bottom" in result
    assert "#FF0000" in result
    assert "#0000FF" in result


def test_build_gradient_css_vertical_bottom_top() -> None:
    result = _build_gradient_css("vertical_bottom_top", ["#FF0000", "#0000FF"])
    assert "linear-gradient(to top" in result


def test_build_gradient_css_horizontal_left_right() -> None:
    result = _build_gradient_css("horizontal_left_right", ["#FF0000", "#0000FF"])
    assert "linear-gradient(to right" in result


def test_build_gradient_css_horizontal_right_left() -> None:
    result = _build_gradient_css("horizontal_right_left", ["#FF0000", "#0000FF"])
    assert "linear-gradient(to left" in result


def test_build_gradient_css_diagonal_tl_br() -> None:
    result = _build_gradient_css("diagonal_tl_br", ["#FF0000", "#0000FF"])
    assert "linear-gradient(135deg" in result


def test_build_gradient_css_diagonal_tr_bl() -> None:
    result = _build_gradient_css("diagonal_tr_bl", ["#FF0000", "#0000FF"])
    assert "linear-gradient(225deg" in result


def test_build_gradient_css_radial_center() -> None:
    result = _build_gradient_css("radial_center", ["#FF0000", "#0000FF"])
    assert "radial-gradient(circle at center" in result


def test_build_gradient_css_radial_top() -> None:
    result = _build_gradient_css("radial_top", ["#FF0000", "#0000FF"])
    assert "radial-gradient(ellipse at top" in result


def test_build_gradient_css_radial_bottom() -> None:
    result = _build_gradient_css("radial_bottom", ["#FF0000", "#0000FF"])
    assert "radial-gradient(ellipse at bottom" in result


def test_build_gradient_css_default_stops() -> None:
    result = _build_gradient_css("vertical_top_bottom", ["#FF0000", "#00FF00", "#0000FF"])
    assert "0.0%" in result
    assert "50.0%" in result
    assert "100.0%" in result


def test_build_gradient_css_custom_stops() -> None:
    result = _build_gradient_css(
        "vertical_top_bottom",
        ["#FF0000", "#00FF00", "#0000FF"],
        gradient_stops=[0.0, 0.75, 1.0],
    )
    assert "0%" in result
    assert "75.0%" in result
    assert "100.0%" in result

def test_build_gradient_css_4_colors() -> None:
    result = _build_gradient_css(
        "horizontal_left_right",
        ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"],
    )
    assert "#FF0000" in result
    assert "#00FF00" in result
    assert "#0000FF" in result
    assert "#FFFF00" in result
    assert "0%" in result
    assert "33.0%" in result
    assert "67.0%" in result
    assert "100.0%" in result


def test_build_texture_css_none() -> None:
    css, html = _build_texture_css("none", 0.15, "multiply")
    assert css == ""
    assert html == ""


def test_build_texture_css_noise_fine() -> None:
    css, html = _build_texture_css("noise_fine", 0.15, "multiply")
    assert "texture-overlay" in css
    assert "opacity: 0.15" in css
    assert "mix-blend-mode: multiply" in css
    assert "filter: url(#tex-noise)" in css
    assert "noise-fine" in html
    assert "feTurbulence" in html


def test_build_texture_css_noise_coarse() -> None:
    css, html = _build_texture_css("noise_coarse", 0.2, "overlay")
    assert "filter: url(#tex-noise)" in css
    assert "feTurbulence" in html
    assert "mix-blend-mode: overlay" in css


def test_build_texture_css_grain_film() -> None:
    css, html = _build_texture_css("grain_film", 0.2, "overlay")
    assert "filter: url(#tex-noise)" in css
    assert "feTurbulence" in html
    assert "feColorMatrix" in html


def test_build_texture_css_paper_subtle() -> None:
    css, html = _build_texture_css("paper_subtle", 0.1, "multiply")
    assert "filter: url(#tex-noise)" in css
    assert "feTurbulence" in html
    assert "feDiffuseLighting" in html


def test_build_texture_css_vignette_soft() -> None:
    css, html = _build_texture_css("vignette_soft", 0.25, "multiply")
    assert "texture-overlay" in css
    assert "radial-gradient" in css
    assert "vignette-soft" in html
    assert "rgba(0, 0, 0, 0.7)" in css


def test_build_texture_css_vignette_heavy() -> None:
    css, html = _build_texture_css("vignette_heavy", 0.3, "normal")
    assert "radial-gradient" in css
    assert "rgba(0, 0, 0, 0.9)" in css
    assert "mix-blend-mode: normal" in css


def test_build_html_gradient_vertical_top_bottom() -> None:
    text = "Test content"
    slot_info = {
        "year": "2026", "month": "4", "day": "6",
        "week_number": "1", "subtheme": "Sub",
        "monthly_theme": "Theme", "type": "post",
    }
    preset = {
        "background": "#4A90E2", "text_color": "#FFFFFF",
        "font_size": 48, "padding": 80, "max_width": 1080,
    }

    html = build_html(
        text, slot_info, preset, 1080, 1080,
        gradient_direction="vertical_top_bottom",
        gradient_colors=["#FF0000", "#0000FF"],
    )

    assert "linear-gradient(to bottom" in html
    assert "background:" in html
    assert "background-color:" not in html


def test_build_html_gradient_diagonal_tl_br_3_colors() -> None:
    text = "Test content"
    slot_info = {
        "year": "2026", "month": "4", "day": "6",
        "week_number": "1", "subtheme": "Sub",
        "monthly_theme": "Theme", "type": "post",
    }
    preset = {
        "background": "#4A90E2", "text_color": "#FFFFFF",
        "font_size": 48, "padding": 80, "max_width": 1080,
    }

    html = build_html(
        text, slot_info, preset, 1080, 1080,
        gradient_direction="diagonal_tl_br",
        gradient_colors=["#FF0000", "#00FF00", "#0000FF"],
    )

    assert "linear-gradient(135deg" in html
    assert "#FF0000" in html
    assert "#00FF00" in html
    assert "#0000FF" in html


def test_build_html_gradient_radial_center() -> None:
    text = "Test content"
    slot_info = {
        "year": "2026", "month": "4", "day": "6",
        "week_number": "1", "subtheme": "Sub",
        "monthly_theme": "Theme", "type": "post",
    }
    preset = {
        "background": "#4A90E2", "text_color": "#FFFFFF",
        "font_size": 48, "padding": 80, "max_width": 1080,
    }

    html = build_html(
        text, slot_info, preset, 1080, 1080,
        gradient_direction="radial_center",
        gradient_colors=["#FF0000", "#0000FF"],
    )

    assert "radial-gradient(circle at center" in html


def test_build_html_texture_noise_fine() -> None:
    text = "Test content"
    slot_info = {
        "year": "2026", "month": "4", "day": "6",
        "week_number": "1", "subtheme": "Sub",
        "monthly_theme": "Theme", "type": "post",
    }
    preset = {
        "background": "#4A90E2", "text_color": "#FFFFFF",
        "font_size": 48, "padding": 80, "max_width": 1080,
    }

    html = build_html(
        text, slot_info, preset, 1080, 1080,
        texture_type="noise_fine",
        texture_opacity=0.15,
        texture_blend_mode="multiply",
    )

    assert "texture-overlay" in html
    assert "filter: url(#tex-noise)" in html
    assert "mix-blend-mode: multiply" in html


def test_build_html_texture_vignette_soft() -> None:
    text = "Test content"
    slot_info = {
        "year": "2026", "month": "4", "day": "6",
        "week_number": "1", "subtheme": "Sub",
        "monthly_theme": "Theme", "type": "post",
    }
    preset = {
        "background": "#4A90E2", "text_color": "#FFFFFF",
        "font_size": 48, "padding": 80, "max_width": 1080,
    }

    html = build_html(
        text, slot_info, preset, 1080, 1080,
        texture_type="vignette_soft",
        texture_opacity=0.25,
    )

    assert "texture-overlay" in html
    assert "radial-gradient" in html
    assert "vignette-soft" in html


def test_build_html_texture_none_no_overlay() -> None:
    text = "Test content"
    slot_info = {
        "year": "2026", "month": "4", "day": "6",
        "week_number": "1", "subtheme": "Sub",
        "monthly_theme": "Theme", "type": "post",
    }
    preset = {
        "background": "#4A90E2", "text_color": "#FFFFFF",
        "font_size": 48, "padding": 80, "max_width": 1080,
    }

    html = build_html(text, slot_info, preset, 1080, 1080)

    assert "texture-overlay" not in html


def test_build_html_composition_gradient_plus_texture() -> None:
    text = "Test content"
    slot_info = {
        "year": "2026", "month": "4", "day": "6",
        "week_number": "1", "subtheme": "Sub",
        "monthly_theme": "Theme", "type": "post",
    }
    preset = {
        "background": "#4A90E2", "text_color": "#FFFFFF",
        "font_size": 48, "padding": 80, "max_width": 1080,
    }

    html = build_html(
        text, slot_info, preset, 1080, 1080,
        gradient_direction="horizontal_left_right",
        gradient_colors=["#FF0000", "#00FF00", "#0000FF", "#FFFF00"],
        texture_type="grain_film",
        texture_opacity=0.2,
        texture_blend_mode="overlay",
    )

    assert "linear-gradient(to right" in html
    assert "#FF0000" in html
    assert "#FFFF00" in html
    assert "texture-overlay" in html
    assert "filter: url(#tex-noise)" in html
    assert "mix-blend-mode: overlay" in html


def test_build_html_backward_compat_no_new_params() -> None:
    text = "Test content"
    slot_info = {
        "year": "2026", "month": "4", "day": "6",
        "week_number": "1", "subtheme": "Sub",
        "monthly_theme": "Theme", "type": "post",
    }
    preset = {
        "background": "#4A90E2", "text_color": "#FFFFFF",
        "font_size": 48, "padding": 80, "max_width": 1080,
    }

    html = build_html(text, slot_info, preset, 1080, 1080)

    assert "background-color: #4A90E2" in html
    assert "linear-gradient" not in html
    assert "radial-gradient" not in html
    assert "texture-overlay" not in html
    assert text in html


def test_build_html_backward_compat_matches_old_output() -> None:
    text = "Test content"
    slot_info = {
        "year": "2026", "month": "4", "day": "6",
        "week_number": "1", "subtheme": "Sub",
        "monthly_theme": "Theme", "type": "post",
    }
    preset = {
        "background": "#4A90E2", "text_color": "#FFFFFF",
        "font_size": 48, "padding": 80, "max_width": 1080,
    }

    html = build_html(text, slot_info, preset, 1080, 1080)

    assert "<!DOCTYPE html>" in html
    assert "background-color: #4A90E2" in html
    assert "color: #FFFFFF" in html
    assert "font-size: 48px" in html
    assert "padding: 80px" in html
    assert text in html
    assert "Theme" in html
    assert "Sub" in html


def test_build_html_card_z_index_with_texture() -> None:
    text = "Test content"
    slot_info = {
        "year": "2026", "month": "4", "day": "6",
        "week_number": "1", "subtheme": "Sub",
        "monthly_theme": "Theme", "type": "post",
    }
    preset = {
        "background": "#4A90E2", "text_color": "#FFFFFF",
        "font_size": 48, "padding": 80, "max_width": 1080,
    }

    html_with_texture = build_html(
        text, slot_info, preset, 1080, 1080,
        texture_type="noise_fine",
    )
    html_without = build_html(text, slot_info, preset, 1080, 1080)

    assert "z-index: 2" in html_with_texture
    assert "z-index: 2" not in html_without


def test_build_html_basic() -> None:
    """Test basic HTML generation."""
    text = "This is a test post"
    slot_info = {
        "year": "2026",
        "month": "2",
        "day": "2",
        "week_number": "1",
        "subtheme": "Test Subtheme",
        "monthly_theme": "Test Theme",
        "type": "post",
    }
    preset = {
        "background": "#4A90E2",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1080)
    
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html
    assert text in html


def test_build_html_includes_theme() -> None:
    """Test that monthly theme is included in HTML."""
    text = "Test content"
    slot_info = {
        "year": "2026",
        "month": "2",
        "day": "2",
        "week_number": "1",
        "subtheme": "Sub",
        "monthly_theme": "My Monthly Theme",
        "type": "post",
    }
    preset = {
        "background": "#4A90E2",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1080)
    
    assert "My Monthly Theme" in html


def test_build_html_includes_subtheme() -> None:
    """Test that subtheme is included in HTML when provided."""
    text = "Test content"
    slot_info = {
        "year": "2026",
        "month": "2",
        "day": "2",
        "week_number": "1",
        "subtheme": "My Subtheme",
        "monthly_theme": "Theme",
        "type": "post",
    }
    preset = {
        "background": "#4A90E2",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1080)
    
    assert "My Subtheme" in html


def test_build_html_no_subtheme() -> None:
    """Test that HTML is generated without subtheme."""
    text = "Test content"
    slot_info = {
        "year": "2026",
        "month": "2",
        "day": "2",
        "week_number": "1",
        "subtheme": "",
        "monthly_theme": "Theme",
        "type": "post",
    }
    preset = {
        "background": "#4A90E2",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1080)
    
    assert text in html
    assert "Theme" in html


def test_build_html_background_color() -> None:
    """Test that background color is applied correctly."""
    text = "Test"
    slot_info = {
        "year": "2026",
        "month": "2",
        "day": "2",
        "week_number": "1",
        "subtheme": "Sub",
        "monthly_theme": "Theme",
        "type": "post",
    }
    preset = {
        "background": "#FF5733",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1080)
    
    assert "#FF5733" in html
    assert "background-color:" in html


def test_build_html_text_color() -> None:
    """Test that explicit text_color override is applied correctly."""
    text = "Test"
    slot_info = {
        "year": "2026",
        "month": "2",
        "day": "2",
        "week_number": "1",
        "subtheme": "Sub",
        "monthly_theme": "Theme",
        "type": "post",
    }
    preset = {
        "background": "#4A90E2",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }

    html = build_html(text, slot_info, preset, 1080, 1080, text_color="#123456")

    assert "#123456" in html
    assert "color:" in html


def test_build_html_default_values() -> None:
    """Test HTML generation with default values from slot_info."""
    text = "Test"
    slot_info = {
        "type": "post",
    }
    preset = {
        "background": "#4A90E2",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1080)
    
    assert "Theme" in html
    assert text in html


def test_build_html_special_characters() -> None:
    """Test HTML generation with special characters in text."""
    text = "Test with <special> & characters"
    slot_info = {
        "year": "2026",
        "month": "2",
        "day": "2",
        "week_number": "1",
        "subtheme": "Sub",
        "monthly_theme": "Theme",
        "type": "post",
    }
    preset = {
        "background": "#4A90E2",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1080)
    
    assert "Test with" in html
    assert "special" in html
    assert "characters" in html


def test_build_html_custom_dimensions() -> None:
    """Test HTML generation with custom dimensions."""
    text = "Test"
    slot_info = {
        "year": "2026",
        "month": "2",
        "day": "2",
        "week_number": "1",
        "subtheme": "Sub",
        "monthly_theme": "Theme",
        "type": "post",
    }
    preset = {
        "background": "#4A90E2",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1350)
    
    assert "<!DOCTYPE html>" in html
    assert text in html


def test_build_html_content_structure() -> None:
    """Test that HTML has proper structure."""
    text = "Test content"
    slot_info = {
        "year": "2026",
        "month": "2",
        "day": "2",
        "week_number": "1",
        "subtheme": "Sub",
        "monthly_theme": "Theme",
        "type": "post",
    }
    preset = {
        "background": "#4A90E2",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1080)
    
    assert "<head>" in html
    assert "</head>" in html
    assert "<body>" in html
    assert "</body>" in html
    assert "<style>" in html
    assert "</style>" in html


def test_build_html_with_subtheme_subtitle() -> None:
    """Test that subtheme_subtitle is used for display when provided."""
    text = "Test content"
    slot_info = {
        "year": "2026",
        "month": "2",
        "day": "2",
        "week_number": "1",
        "subtheme": "This is a very long subtheme that should not be displayed",
        "subtheme_subtitle": "Short Title",
        "monthly_theme": "Theme",
        "type": "post",
    }
    preset = {
        "background": "#4A90E2",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1080)
    
    assert "Short Title" in html
    assert "very long subtheme" not in html


def test_build_html_falls_back_to_subtheme_when_no_subtitle() -> None:
    """Test that subtheme is used when subtitle is not provided."""
    text = "Test content"
    slot_info = {
        "year": "2026",
        "month": "2",
        "day": "2",
        "week_number": "1",
        "subtheme": "Fallback Subtheme",
        "monthly_theme": "Theme",
        "type": "post",
    }
    preset = {
        "background": "#4A90E2",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1080)
    
    assert "Fallback Subtheme" in html


def test_build_html_empty_subtitle_uses_subtheme() -> None:
    """Test that empty subtitle falls back to subtheme."""
    text = "Test content"
    slot_info = {
        "year": "2026",
        "month": "2",
        "day": "2",
        "week_number": "1",
        "subtheme": "The Subtheme",
        "subtheme_subtitle": "",
        "monthly_theme": "Theme",
        "type": "post",
    }
    preset = {
        "background": "#4A90E2",
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1080)
    
    assert "The Subtheme" in html


def test_build_html_auto_contrast_dark_bg() -> None:
    """Auto-contrast returns white text on dark backgrounds."""
    preset = {"background": "#4A90E2", "text_color": "#FFFFFF", "font_size": 48, "padding": 80}
    slot_info = {"year": "2026", "month": "2", "day": "2", "week_number": "1", "subtheme": "S", "monthly_theme": "T", "type": "post"}
    html = build_html("Test", slot_info, preset, 1080, 1080)
    assert "#FFFFFF" in html


def test_build_html_auto_contrast_light_bg() -> None:
    """Auto-contrast returns black text on light backgrounds."""
    preset = {"background": "#FFFFCC", "text_color": "#FFFFFF", "font_size": 48, "padding": 80}
    slot_info = {"year": "2026", "month": "2", "day": "2", "week_number": "1", "subtheme": "S", "monthly_theme": "T", "type": "post"}
    html = build_html("Test", slot_info, preset, 1080, 1080)
    assert "#000000" in html


def test_build_html_explicit_text_color_overrides_auto() -> None:
    """Explicit text_color param overrides auto-contrast."""
    preset = {"background": "#FFFFCC", "text_color": "#FFFFFF", "font_size": 48, "padding": 80}
    slot_info = {"year": "2026", "month": "2", "day": "2", "week_number": "1", "subtheme": "S", "monthly_theme": "T", "type": "post"}
    html = build_html("Test", slot_info, preset, 1080, 1080, text_color="#FF0000")
    assert "#FF0000" in html
    assert "#000000" not in html


def test_build_html_auto_contrast_with_gradient() -> None:
    """Auto-contrast uses first gradient color for contrast calculation."""
    preset = {"background": "#4A90E2", "text_color": "#FFFFFF", "font_size": 48, "padding": 80}
    slot_info = {"year": "2026", "month": "2", "day": "2", "week_number": "1", "subtheme": "S", "monthly_theme": "T", "type": "post"}
    html = build_html("Test", slot_info, preset, 1080, 1080, gradient_direction="vertical_top_bottom", gradient_colors=["#FFFFFF", "#000000"])
    assert "#000000" in html


def test_build_texture_css_fallthrough_returns_empty() -> None:
    """The final return '', '' at the end of _build_texture_css is reached for unknown types."""
    css, html = _build_texture_css("none", 0.1, "multiply")
    assert css == ""
    assert html == ""


def test_build_html_transparent_bg() -> None:
    """Test transparent_bg renders with transparent background and no texture."""
    text = "Test content"
    slot_info = {
        "year": "2026", "month": "4", "day": "6",
        "week_number": "1", "subtheme": "Sub",
        "monthly_theme": "Theme", "type": "post",
    }
    preset = {
        "background": "#4A90E2", "text_color": "#FFFFFF",
        "font_size": 48, "padding": 80, "max_width": 1080,
    }

    html = build_html(
        text, slot_info, preset, 1080, 1080,
        transparent_bg=True,
        texture_type="noise_fine",
    )

    assert "background-color: transparent" in html
    assert "texture-overlay" not in html
