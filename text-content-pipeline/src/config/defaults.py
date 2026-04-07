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

ACE_STEP_PYTHON = "/mnt/storage/python_env/ace_step_env/bin/python"
ACE_STEP_SCRIPT = str(PROJECT_ROOT / "scripts" / "run_ace_step_pipe.py")
ACE_STEP_DEFAULT_STEPS = 20
ACE_STEP_DEFAULT_GUIDANCE = 7.0
ACE_STEP_MUSIC_VOLUME = 0.3
ACE_STEP_TTS_DELAY = 0.5
ACE_STEP_TAIL_MAX = 3.0
ACE_STEP_TAIL_RATIO = 0.25
ACE_STEP_TIMEOUT = 600

BACKGROUND_TEST_DIR = OUTPUTS_DIR / "background_tests"


def auto_contrast_color(hex_color: str) -> str:
    """Return black or white text color for best contrast against a background.

    Uses WCAG relative luminance formula on the background color.
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "#FFFFFF"
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#000000" if luminance > 0.6 else "#FFFFFF"


def companion_color(hex_color: str, hue_shift: float = 40.0) -> str:
    """Generate an interesting companion color by rotating hue.

    Converts to HSL, shifts the hue, and slightly adjusts saturation/lightness
    to produce a harmonious but visually distinct gradient pair.
    """
    import colorsys

    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "#FFFFFF"
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    h, s, l = colorsys.rgb_to_hls(r, g, b)
    h = (h + hue_shift / 360.0) % 1.0
    s = min(1.0, s * 1.1)
    l = max(0.2, min(0.8, l * 0.9))
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(r2*255):02X}{int(g2*255):02X}{int(b2*255):02X}"
