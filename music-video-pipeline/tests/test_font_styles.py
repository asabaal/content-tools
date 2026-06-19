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
    _load_registry,
    _find_font,
)


class TestFontStyle:
    def test_all_11_styles(self):
        assert len(FontStyle) == 11

    def test_style_values(self):
        names = {s.value for s in FontStyle}
        assert names == {"neon", "graffiti", "chrome", "fire", "ice", "gold", "hologram", "matrix", "basic", "clean_white", "dramatic_red"}


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


class TestFontRegistry:
    def test_load_registry_returns_dict(self):
        from render.font_styles import _load_registry
        reg = _load_registry()
        assert isinstance(reg, dict)

    def test_load_registry_caches(self):
        from render.font_styles import _load_registry
        reg1 = _load_registry()
        reg2 = _load_registry()
        assert reg1 is reg2

    def test_load_registry_contains_legacy_entries(self):
        from render.font_styles import _load_registry
        reg = _load_registry()
        assert 1 in reg
        assert len(reg[1]) == 2


class TestFindFont:
    def test_default_font(self):
        from render.font_styles import _find_font
        font = _find_font(48)
        assert font is not None

    def test_non_bold_font(self):
        from render.font_styles import _find_font
        font = _find_font(48, bold=False)
        assert font is not None

    def test_font_family_zero(self):
        from render.font_styles import _find_font
        font = _find_font(36, bold=True, family=0)
        assert font is not None

    def test_font_family_nonexistent(self):
        from render.font_styles import _find_font
        font = _find_font(36, bold=True, family=999)
        assert font is not None


class TestEdgeCasesText:
    def test_empty_string(self):
        arr = _create_base_text("", 48)
        assert arr.ndim == 3
        assert arr.shape[2] == 4

    def test_single_char(self):
        arr = _create_base_text("A", 48)
        assert arr[:, :, 3].sum() > 0

    def test_very_long_text(self):
        text = "Hello world " * 100
        arr = _create_base_text(text, 24)
        assert arr.ndim == 3
        assert arr.shape[2] == 4
        assert arr.shape[1] > 100

    def test_special_characters(self):
        text = "Hello! @#$%^&*(){}[]"
        arr = _create_base_text(text, 48)
        assert arr[:, :, 3].sum() > 0

    def test_unicode_text(self):
        text = "Hello \u00e9\u00e8\u00ea\u00eb \u00f1"
        arr = _create_base_text(text, 48)
        assert arr.ndim == 3

    def test_cjk_characters(self):
        text = "\u4f60\u597d\u4e16\u754c"
        arr = _create_base_text(text, 48)
        assert arr.ndim == 3

    def test_newline_text(self):
        text = "Line1\nLine2"
        arr = _create_base_text(text, 48)
        assert arr.ndim == 3


class TestStyleGeneratorsWithFamily:
    @pytest.mark.parametrize("style_func", [
        _generate_neon, _generate_graffiti, _generate_chrome, _generate_basic,
    ])
    def test_with_family_zero(self, style_func):
        result = style_func("Hi", 48, family=0)
        assert result.ndim == 3
        assert result.shape[2] == 4

    @pytest.mark.parametrize("style_func", [
        _generate_neon, _generate_basic,
    ])
    def test_with_nonexistent_family(self, style_func):
        result = style_func("Hi", 48, family=999)
        assert result.ndim == 3
        assert result.shape[2] == 4


class TestGenerateStyledTextAdvanced:
    def test_with_family_parameter(self):
        img = generate_styled_text("Hi", FontStyle.NEON, size=36, family=0)
        assert isinstance(img, Image.Image)

    def test_with_nonexistent_family(self):
        img = generate_styled_text("Hi", FontStyle.NEON, size=36, family=999)
        assert isinstance(img, Image.Image)

    def test_empty_text(self):
        img = generate_styled_text("", FontStyle.NEON, size=36)
        assert isinstance(img, Image.Image)

    def test_target_dimensions_centers(self):
        img = generate_styled_text("Hi", FontStyle.BASIC, size=24, target_width=800, target_height=600)
        assert img.size == (800, 600)
        arr = np.array(img)
        assert arr[:, :, 3].sum() > 0


class TestCompositeEdgeCases:
    def test_composite_at_zero_offset(self):
        base = np.zeros((100, 100, 4), dtype=np.uint8)
        overlay = np.full((50, 50, 4), [255, 0, 0, 255], dtype=np.uint8)
        result = _composite(base, overlay, 0, 0)
        assert result[0, 0, 0] == 255

    def test_composite_partial_overlap(self):
        base = np.zeros((100, 100, 4), dtype=np.uint8)
        overlay = np.full((50, 50, 4), [255, 0, 0, 255], dtype=np.uint8)
        result = _composite(base, overlay, 80, 80)
        assert result[80, 80, 0] == 255
        assert result[0, 0, 0] == 0


class TestOutlineThickness:
    def test_thickness_zero(self):
        base = _create_base_text("Hi", 48)
        outline = _create_outline(base, 0)
        assert outline.shape == base.shape

    def test_large_thickness(self):
        base = _create_base_text("Hi", 48)
        outline = _create_outline(base, 10)
        assert outline.shape == base.shape
        assert outline[:, :, 3].sum() >= base[:, :, 3].sum()


class TestLoadRegistryCorrupt:
    def test_corrupt_registry_json(self, tmp_path, monkeypatch):
        import render.font_styles as fs
        corrupt = tmp_path / "font_registry.json"
        corrupt.write_text("NOT VALID JSON{{{")
        monkeypatch.setattr(fs, "_REGISTRY_PATH", corrupt)
        monkeypatch.setattr(fs, "_font_registry", None)
        result = _load_registry()
        assert isinstance(result, dict)


class TestFindFontFallback:
    def test_no_system_fonts_fallback(self, monkeypatch):
        monkeypatch.setattr(Path, "exists", lambda self: False)
        font = _find_font(36)
        assert font is not None
