"""Tests for configuration defaults."""

from pathlib import Path
from src.config.defaults import (
    PROJECT_ROOT,
    OUTPUTS_DIR,
    IMAGES_DIR,
    PLANS_DIR,
    DEFAULT_AI_PROVIDER,
    DEFAULT_AI_MODEL,
    DEFAULT_AI_BASE_URL,
    AI_TIMEOUT,
    AI_MAX_RETRIES,
    WEEK_RULE,
    VIDEO_WEEK_RULE,
    DEFAULT_IMAGE_WIDTH,
    DEFAULT_IMAGE_HEIGHT,
    PORTRAIT_WIDTH,
    PORTRAIT_HEIGHT,
    IMAGE_FORMAT,
    IMAGE_QUALITY,
    COLORFUL_PRESETS,
    MAX_WORDS_PER_SLOT,
)


def test_project_paths_exist() -> None:
    """Test that all path constants are Path objects and exist."""
    assert isinstance(PROJECT_ROOT, Path)
    assert PROJECT_ROOT.exists()
    
    assert isinstance(OUTPUTS_DIR, Path)
    assert OUTPUTS_DIR.exists()
    
    assert isinstance(IMAGES_DIR, Path)
    assert IMAGES_DIR.exists()
    
    assert isinstance(PLANS_DIR, Path)
    assert PLANS_DIR.exists()


def test_paths_are_relative_to_project_root() -> None:
    """Test that output paths are relative to project root."""
    assert OUTPUTS_DIR.is_relative_to(PROJECT_ROOT)
    assert IMAGES_DIR.is_relative_to(PROJECT_ROOT)
    assert PLANS_DIR.is_relative_to(PROJECT_ROOT)


def test_ai_config_constants() -> None:
    """Test AI configuration constants."""
    assert DEFAULT_AI_PROVIDER == "ollama"
    assert DEFAULT_AI_MODEL == "gpt-oss:20b"
    assert DEFAULT_AI_BASE_URL == "http://localhost:11434"
    assert AI_TIMEOUT == 300.0
    assert AI_MAX_RETRIES == 2


def test_calendar_settings() -> None:
    """Test calendar configuration constants."""
    assert WEEK_RULE == "monday_determines_month"
    assert VIDEO_WEEK_RULE == "last_week"


def test_image_dimensions() -> None:
    """Test default image dimensions."""
    assert DEFAULT_IMAGE_WIDTH == 1080
    assert DEFAULT_IMAGE_HEIGHT == 1080
    assert PORTRAIT_WIDTH == 1080
    assert PORTRAIT_HEIGHT == 1350


def test_output_format_settings() -> None:
    """Test output format constants."""
    assert IMAGE_FORMAT == "png"
    assert IMAGE_QUALITY == 100


def test_colorful_presets_exist() -> None:
    """Test that colorful presets dict exists and has required keys."""
    assert isinstance(COLORFUL_PRESETS, dict)
    assert len(COLORFUL_PRESETS) > 0
    
    required_keys = ["default", "warm", "cool", "purple", "red"]
    for key in required_keys:
        assert key in COLORFUL_PRESETS


def test_colorful_preset_structure() -> None:
    """Test that each preset has required keys."""
    for preset_name, preset in COLORFUL_PRESETS.items():
        assert isinstance(preset, dict)
        assert "background" in preset
        assert "text_color" in preset
        assert "font_size" in preset
        assert "padding" in preset


def test_default_preset() -> None:
    """Test default preset values."""
    default_preset = COLORFUL_PRESETS["default"]
    
    assert default_preset["background"] == "#4A90E2"
    assert default_preset["text_color"] == "#FFFFFF"
    assert default_preset["font_size"] == 48
    assert default_preset["padding"] == 80


def test_warm_preset() -> None:
    """Test warm preset values."""
    warm_preset = COLORFUL_PRESETS["warm"]
    
    assert warm_preset["background"] == "#E67E22"
    assert warm_preset["text_color"] == "#FFFFFF"


def test_cool_preset() -> None:
    """Test cool preset values."""
    cool_preset = COLORFUL_PRESETS["cool"]
    
    assert cool_preset["background"] == "#27AE60"
    assert cool_preset["text_color"] == "#FFFFFF"


def test_purple_preset() -> None:
    """Test purple preset values."""
    purple_preset = COLORFUL_PRESETS["purple"]
    
    assert purple_preset["background"] == "#8E44AD"
    assert purple_preset["text_color"] == "#FFFFFF"


def test_red_preset() -> None:
    """Test red preset values."""
    red_preset = COLORFUL_PRESETS["red"]
    
    assert red_preset["background"] == "#C0392B"
    assert red_preset["text_color"] == "#FFFFFF"


def test_preset_color_format() -> None:
    """Test that preset colors are hex codes."""
    for preset_name, preset in COLORFUL_PRESETS.items():
        background = preset["background"]
        text_color = preset["text_color"]
        
        assert isinstance(background, str)
        assert background.startswith("#")
        assert len(background) == 7
        
        assert isinstance(text_color, str)
        assert text_color.startswith("#")
        assert len(text_color) == 7


def test_preset_numeric_values() -> None:
    """Test that preset numeric values are integers."""
    for preset_name, preset in COLORFUL_PRESETS.items():
        assert isinstance(preset["font_size"], int)
        assert isinstance(preset["padding"], int)
        assert preset["font_size"] > 0
        assert preset["padding"] > 0


def test_max_words_per_slot_exists() -> None:
    """Test that MAX_WORDS_PER_SLOT config exists."""
    assert isinstance(MAX_WORDS_PER_SLOT, dict)
    assert len(MAX_WORDS_PER_SLOT) > 0


def test_max_words_per_slot_has_all_slot_types() -> None:
    """Test that all slot types have max word limits."""
    required_slots = [
        "declarative_statement",
        "excerpt",
        "process_note",
        "unanswered_question",
        "reframing",
        "quiet_observation",
    ]
    for slot in required_slots:
        assert slot in MAX_WORDS_PER_SLOT


def test_max_words_per_slot_values_are_integers() -> None:
    """Test that all max words values are positive integers."""
    for slot_type, max_words in MAX_WORDS_PER_SLOT.items():
        assert isinstance(max_words, int), f"{slot_type} max_words is not int"
        assert max_words > 0, f"{slot_type} max_words must be positive"


def test_max_words_per_slot_reasonable_values() -> None:
    """Test that max words values are reasonable for each slot type."""
    # Declarative statements should be short
    assert MAX_WORDS_PER_SLOT["declarative_statement"] <= 30
    # Process notes can be longer
    assert MAX_WORDS_PER_SLOT["process_note"] >= 50
    # Questions should be short
    assert MAX_WORDS_PER_SLOT["unanswered_question"] <= 30
