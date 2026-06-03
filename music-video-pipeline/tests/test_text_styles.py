import numpy as np
import pytest
from pathlib import Path
from PIL import Image

from render.text_styles import (
    StyleConfig,
    TextStyle,
    _alpha_blend,
    _cv2_to_pil,
    _find_font,
    _pil_to_cv2_alpha,
    _render_fill,
    _render_glow,
    _render_outline,
    _render_shadow,
    _render_text_base,
    get_style_config,
    render_styled_text,
)


class TestTextStyle:
    def test_all_styles_exist(self):
        assert len(TextStyle) == 6

    def test_style_values(self):
        assert TextStyle.MODERN_BOLD.value == "modern_bold"
        assert TextStyle.NEON_GLOW.value == "neon_glow"
        assert TextStyle.ELEGANT_GOLD.value == "elegant_gold"
        assert TextStyle.HIP_HOP.value == "hip_hop"
        assert TextStyle.CLEAN_WHITE.value == "clean_white"
        assert TextStyle.DRAMATIC_RED.value == "dramatic_red"


class TestGetStyleConfig:
    def test_returns_config_for_known_style(self):
        config = get_style_config(TextStyle.MODERN_BOLD)
        assert isinstance(config, StyleConfig)
        assert config.fill_color == (255, 255, 255, 255)

    def test_neon_glow_has_glow(self):
        config = get_style_config(TextStyle.NEON_GLOW)
        assert config.glow_color is not None
        assert config.glow_radius > 0

    def test_clean_white_has_shadow(self):
        config = get_style_config(TextStyle.CLEAN_WHITE)
        assert config.shadow_color is not None

    def test_default_fallback(self):
        config = get_style_config(TextStyle.HIP_HOP)
        assert config.outline_width == 3


class TestFindFont:
    def test_returns_font(self):
        font = _find_font(48)
        assert font is not None

    def test_different_sizes(self):
        f1 = _find_font(24)
        f2 = _find_font(72)
        assert f1 is not None
        assert f2 is not None


class TestPilToCv2Alpha:
    def test_converts_rgba(self):
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        arr = _pil_to_cv2_alpha(img)
        assert arr.shape == (100, 100, 4)
        assert arr.dtype == np.uint8


class TestCv2ToPil:
    def test_roundtrip(self):
        original = Image.new("RGBA", (50, 50), (100, 200, 50, 255))
        bgra = _pil_to_cv2_alpha(original)
        result = _cv2_to_pil(bgra)
        assert result.mode == "RGBA"
        assert result.size == (50, 50)


class TestAlphaBlend:
    def test_blend_transparent_src(self):
        dest = np.full((10, 10, 4), 255, dtype=np.uint8)
        src = np.zeros((10, 10, 4), dtype=np.uint8)
        _alpha_blend(dest, src)
        assert np.all(dest[:, :, 3] == 255)

    def test_blend_opaque_src(self):
        dest = np.zeros((10, 10, 4), dtype=np.uint8)
        src = np.full((10, 10, 4), 255, dtype=np.uint8)
        _alpha_blend(dest, src)
        assert np.all(dest[:, :, :3] == 255)


class TestRenderTextBase:
    def test_produces_non_empty_output(self):
        result = _render_text_base("Hello", 48, 640, 480, (255, 255, 255, 255))
        assert result.shape == (480, 640, 4)
        assert result[:, :, 3].sum() > 0

    def test_centered(self):
        result = _render_text_base("Hi", 48, 200, 200, (255, 255, 255, 255))
        assert result.shape == (200, 200, 4)


class TestRenderShadow:
    def test_with_shadow(self):
        config = get_style_config(TextStyle.MODERN_BOLD)
        frame = np.zeros((200, 400, 4), dtype=np.uint8)
        _render_shadow(frame, "Shadow", 36, 400, 200, config)
        assert frame[:, :, 3].sum() > 0

    def test_without_shadow(self):
        config = StyleConfig(
            fill_color=(255, 255, 255, 255),
            outline_color=(0, 0, 0, 255),
            outline_width=0,
            shadow_color=None,
            shadow_offset=(0, 0),
            shadow_blur=0,
            glow_color=None,
            glow_radius=0,
        )
        frame = np.zeros((200, 400, 4), dtype=np.uint8)
        _render_shadow(frame, "NoShadow", 36, 400, 200, config)
        assert frame[:, :, 3].sum() == 0


class TestRenderGlow:
    def test_with_glow(self):
        config = get_style_config(TextStyle.NEON_GLOW)
        frame = np.zeros((200, 400, 4), dtype=np.uint8)
        _render_glow(frame, "Glow", 36, 400, 200, config)
        assert frame[:, :, 3].sum() > 0

    def test_without_glow(self):
        config = StyleConfig(
            fill_color=(255, 255, 255, 255),
            outline_color=(0, 0, 0, 255),
            outline_width=0,
            shadow_color=None,
            shadow_offset=(0, 0),
            shadow_blur=0,
            glow_color=None,
            glow_radius=0,
        )
        frame = np.zeros((200, 400, 4), dtype=np.uint8)
        _render_glow(frame, "NoGlow", 36, 400, 200, config)
        assert frame[:, :, 3].sum() == 0


class TestRenderOutline:
    def test_with_outline(self):
        config = get_style_config(TextStyle.MODERN_BOLD)
        frame = np.zeros((200, 400, 4), dtype=np.uint8)
        _render_outline(frame, "Outline", 36, 400, 200, config)
        assert frame[:, :, 3].sum() > 0

    def test_without_outline(self):
        config = StyleConfig(
            fill_color=(255, 255, 255, 255),
            outline_color=(0, 0, 0, 255),
            outline_width=0,
            shadow_color=None,
            shadow_offset=(0, 0),
            shadow_blur=0,
            glow_color=None,
            glow_radius=0,
        )
        frame = np.zeros((200, 400, 4), dtype=np.uint8)
        _render_outline(frame, "NoOutline", 36, 400, 200, config)
        assert frame[:, :, 3].sum() == 0


class TestRenderFill:
    def test_produces_pixels(self):
        config = get_style_config(TextStyle.CLEAN_WHITE)
        frame = np.zeros((200, 400, 4), dtype=np.uint8)
        _render_fill(frame, "Fill", 36, 400, 200, config)
        assert frame[:, :, 3].sum() > 0


class TestRenderStyledText:
    @pytest.mark.parametrize("style", TextStyle)
    def test_all_styles_produce_image(self, style):
        img = render_styled_text("Test", 48, style, width=640, height=480)
        assert isinstance(img, Image.Image)
        assert img.mode == "RGBA"
        assert img.size == (640, 480)

    def test_output_has_pixels(self):
        img = render_styled_text("Hello World", 48, TextStyle.MODERN_BOLD, width=640, height=480)
        arr = np.array(img)
        assert arr[:, :, 3].sum() > 0

    def test_different_font_sizes(self):
        small = render_styled_text("Hi", 24, TextStyle.NEON_GLOW, width=640, height=480)
        large = render_styled_text("Hi", 96, TextStyle.NEON_GLOW, width=640, height=480)
        small_px = np.array(small)[:, :, 3].sum()
        large_px = np.array(large)[:, :, 3].sum()
        assert large_px > small_px


class TestFindFontFallback:
    def test_no_system_fonts_fallback(self, monkeypatch):
        monkeypatch.setattr(Path, "exists", lambda self: False)
        font = _find_font(36)
        assert font is not None
