"""Configuration defaults and constants."""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
IMAGES_DIR = OUTPUTS_DIR / "images"
PLANS_DIR = OUTPUTS_DIR / "plans"

# Create directories
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
PLANS_DIR.mkdir(parents=True, exist_ok=True)

# AI Model Configuration
DEFAULT_AI_PROVIDER = "ollama"
DEFAULT_AI_MODEL = "gpt-oss:20b"
DEFAULT_AI_BASE_URL = "http://localhost:11434"

# AI Request Settings
AI_TIMEOUT = 300.0  # 5 minutes
AI_MAX_RETRIES = 2

# Calendar Settings
WEEK_RULE = "monday_determines_month"
VIDEO_WEEK_RULE = "last_week"

# Image Dimensions (default 1:1 square)
DEFAULT_IMAGE_WIDTH = 1080
DEFAULT_IMAGE_HEIGHT = 1080

# Alternative 4:5 portrait dimensions
PORTRAIT_WIDTH = 1080
PORTRAIT_HEIGHT = 1350

# Output Settings
IMAGE_FORMAT = "png"
IMAGE_QUALITY = 100

# Max words per slot type
MAX_WORDS_PER_SLOT = {
    "declarative_statement": 25,
    "excerpt": 60,
    "process_note": 90,
    "unanswered_question": 20,
    "reframing": 25,
    "quiet_observation": 30,
}

# Colorful Background Presets
COLORFUL_PRESETS = {
    "default": {
        "background": "#4A90E2",  # Vibrant blue
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
    },
    "warm": {
        "background": "#E67E22",  # Warm orange
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
    },
    "cool": {
        "background": "#27AE60",  # Rich teal
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
    },
    "purple": {
        "background": "#8E44AD",  # Vibrant purple
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
    },
    "red": {
        "background": "#C0392B",  # Deep red
        "text_color": "#FFFFFF",
        "font_size": 48,
        "padding": 80,
    },
}
