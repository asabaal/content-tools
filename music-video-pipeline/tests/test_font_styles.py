import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from render.font_styles import (
    FontStyle,
    _apply_glow,
    _composite,
    _create_base_text,
    _create_outline,
    _generate_basic,
    _generate_chrome,
    _generate_fire,
    _generate_gold,
    _generate_graffiti,
    _generate_hologram,
    _generate_ice,
    _generate_matrix,
    _generate_neon,
    _STYLE_GENERATORS,
    generate_styled_text,
)


class TestFontStyle:
    def test_all_9_styles(self):
        assert len(FontStyle) == 9

    def test_style_values(self):
        names = {s.value for s in FontStyle}
        assert names == {"neon", "graffiti", "chrome", "fire", "ice", "gold", "hologram", "matrix", "basic"}


class TestCreateBaseText:
    def test_produces_rgba(self):
        arr = _create_base_text("Hello", 48)
        assert arr.ndim == 3
        assert arr.shape[2] == 4
        assert arr.dtype == np.uint8

    def test_has_visible_pixels(self):
        arr = _create_base_text("Test", 48)
        assert arr[:, :, 3].sum() > 0


class TestCreateOutline:
    def test_produces_larger_alpha(self):
        base = _create_base_text("Hi", 48)
        outline = _create_outline(base, 3)
        assert outline.shape == base.shape
        assert outline[:, :, 3].sum() >= base[:, :, 3].sum()

    def test_thickness_1(self):
        base = _create_base_text("Hi", 48)
        outline = _create_outline(base, 1)
        assert outline.shape == base.shape


class TestApplyGlow:
    def test_produces_glow(self):
        base = _create_base_text("Hi", 48)
        glow = _apply_glow(base, (255, 0, 255), 10, 100)
        assert glow.shape == base.shape
        assert glow[:, :, 3].sum() > 0


class TestComposite:
    def test_overlay_on_empty(self):
        base = np.zeros((100, 100, 4), dtype=np.uint8)
        overlay = np.full((50, 50, 4), [255, 0, 0, 200], dtype=np.uint8)
        result = _composite(base, overlay, 10, 10)
        assert result[10, 10, 0] > 0

    def test_out_of_bounds_ignored(self):
        base = np.zeros((10, 10, 4), dtype=np.uint8)
        overlay = np.full((5, 5, 4), [255, 0, 0, 255], dtype=np.uint8)
        result = _composite(base, overlay, 100, 100)
        assert result.sum() == 0


class TestStyleGenerators:
    @pytest.mark.parametrize("style_func", [
        _generate_neon, _generate_graffiti, _generate_chrome, _generate_fire,
        _generate_ice, _generate_gold, _generate_hologram, _generate_matrix,
        _generate_basic,
    ])
    def test_produces_rgba(self, style_func):
        result = style_func("Hi", 48)
        assert result.ndim == 3
        assert result.shape[2] == 4
        assert result.dtype == np.uint8

    @pytest.mark.parametrize("style_func", [
        _generate_neon, _generate_graffiti, _generate_chrome, _generate_fire,
        _generate_ice, _generate_gold, _generate_hologram, _generate_matrix,
        _generate_basic,
    ])
    def test_has_visible_pixels(self, style_func):
        result = style_func("Test", 36)
        assert result[:, :, 3].sum() > 0

    @pytest.mark.parametrize("style_func", [
        _generate_neon, _generate_graffiti, _generate_chrome, _generate_fire,
        _generate_ice, _generate_gold, _generate_hologram, _generate_matrix,
        _generate_basic,
    ])
    def test_padded_output(self, style_func):
        result = style_func("Hi", 36)
        h, w = result.shape[:2]
        base = _create_base_text("Hi", 36)
        assert h > base.shape[0] or w > base.shape[1]


class TestGenerateStyledText:
    @pytest.mark.parametrize("style", FontStyle)
    def test_all_styles_enum(self, style):
        img = generate_styled_text("Test", style, size=36)
        assert isinstance(img, Image.Image)
        assert img.mode == "RGBA"

    def test_string_style(self):
        img = generate_styled_text("Hi", "neon", size=36)
        assert isinstance(img, Image.Image)

    def test_unknown_string_falls_back(self):
        img = generate_styled_text("Hi", "nonexistent", size=36)
        assert isinstance(img, Image.Image)

    def test_with_target_dimensions(self):
        img = generate_styled_text("Hi", FontStyle.NEON, size=36, target_width=640, target_height=480)
        assert img.size == (640, 480)

    def test_all_generators_registered(self):
        for style in FontStyle:
            assert style in _STYLE_GENERATORS
