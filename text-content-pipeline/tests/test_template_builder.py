"""Tests for HTML template builder."""

from src.renderer.template_builder import build_html


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
    """Test that text color is applied correctly."""
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
        "text_color": "#123456",
        "font_size": 48,
        "padding": 80,
        "max_width": 1080,
    }
    
    html = build_html(text, slot_info, preset, 1080, 1080)
    
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
