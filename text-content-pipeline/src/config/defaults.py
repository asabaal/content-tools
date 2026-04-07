"""Configuration defaults and constants."""

from pathlib import Path
from typing import Literal

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
DEFAULT_AI_MODEL = "qwen3.5:35b-a3b"
DEFAULT_AI_BASE_URL = "http://localhost:11434"

# AI Request Settings
AI_TIMEOUT = 600.0  # 10 minutes
AI_MAX_RETRIES = 2
AI_TEMPERATURE = 0.2  # Low for precise instruction following

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

# Gradient directions
GradientDirection = Literal[
    "vertical_top_bottom",
    "vertical_bottom_top",
    "horizontal_left_right",
    "horizontal_right_left",
    "diagonal_tl_br",
    "diagonal_tr_bl",
    "radial_center",
    "radial_top",
    "radial_bottom",
]

# Texture types
TextureType = Literal[
    "none",
    "noise_fine",
    "noise_coarse",
    "grain_film",
    "paper_subtle",
    "vignette_soft",
    "vignette_heavy",
]

# Texture blend modes
TextureBlendMode = Literal[
    "normal",
    "multiply",
    "overlay",
]

# Texture defaults
DEFAULT_TEXTURE_OPACITY = 0.15
DEFAULT_TEXTURE_BLEND_MODE: TextureBlendMode = "multiply"

# Animation types
AnimType = Literal[
    "drift",
    "flow",
    "pulse",
    "distortion",
    "parallax",
    "reactive",
]

ANIM_FPS = 30
DEFAULT_ANIM_TYPE: AnimType = "drift"
DEFAULT_ANIM_INTENSITY = 0.2
DEFAULT_ANIM_SPEED = 1.0
DEFAULT_ANIM_LOOP = 60

DEFAULT_TTS_VOICE = "en-US-AriaNeural"
AUDIO_PAD_SECONDS = 0.5

BACKGROUND_TEST_DIR = OUTPUTS_DIR / "background_tests"
