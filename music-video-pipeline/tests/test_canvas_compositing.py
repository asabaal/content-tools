import numpy as np
import pytest

from canvas.compositing import composite_layer, apply_glow, apply_blur, fill_canvas


class TestCompositeLayerNormal:
    def test_opaque_layer(self):
        base = np.zeros((4, 4, 3), dtype=np.uint8)
        layer = np.zeros((4, 4, 4), dtype=np.uint8)
        layer[:, :, 0] = 255
        layer[:, :, 3] = 255
        result = composite_layer(base, layer, "normal")
        assert result.shape == (4, 4, 3)
        assert np.all(result[:, :, 0] == 255)

    def test_semi_transparent(self):
        base = np.full((4, 4, 3), 100, dtype=np.uint8)
        layer = np.zeros((4, 4, 4), dtype=np.uint8)
        layer[:, :, 1] = 200
        layer[:, :, 3] = 128
        result = composite_layer(base, layer, "normal")
        assert result.shape == (4, 4, 3)
        g = result[0, 0, 1]
        assert g > 100

    def test_4channel_base(self):
        base = np.zeros((4, 4, 4), dtype=np.uint8)
        base[:, :, 3] = 200
        layer = np.zeros((4, 4, 4), dtype=np.uint8)
        layer[:, :, 0] = 255
        layer[:, :, 3] = 100
        result = composite_layer(base, layer, "normal")
        assert result.shape == (4, 4, 4)

    def test_3channel_layer(self):
        base = np.zeros((4, 4, 3), dtype=np.uint8)
        layer = np.full((4, 4, 3), 200, dtype=np.uint8)
        result = composite_layer(base, layer, "normal")
        assert result.shape == (4, 4, 3)
        assert np.all(result[:, :, :] > 0)


class TestCompositeLayerBlendModes:
    def test_screen_brightens(self):
        base = np.full((4, 4, 3), 50, dtype=np.uint8)
        layer = np.zeros((4, 4, 4), dtype=np.uint8)
        layer[:, :, 0] = 200
        layer[:, :, 3] = 255
        result = composite_layer(base, layer, "screen")
        assert result[0, 0, 0] > 50

    def test_multiply_darkens(self):
        base = np.full((4, 4, 3), 200, dtype=np.uint8)
        layer = np.zeros((4, 4, 4), dtype=np.uint8)
        layer[:, :, 0] = 100
        layer[:, :, 3] = 255
        result = composite_layer(base, layer, "multiply")
        assert result[0, 0, 0] < 200

    def test_add(self):
        base = np.full((4, 4, 3), 100, dtype=np.uint8)
        layer = np.zeros((4, 4, 4), dtype=np.uint8)
        layer[:, :, 0] = 200
        layer[:, :, 3] = 255
        result = composite_layer(base, layer, "add")
        assert result[0, 0, 0] > 100

    def test_lighten(self):
        base = np.full((4, 4, 3), 50, dtype=np.uint8)
        layer = np.zeros((4, 4, 4), dtype=np.uint8)
        layer[:, :, 0] = 200
        layer[:, :, 3] = 255
        result = composite_layer(base, layer, "lighten")
        assert result[0, 0, 0] >= 200

    def test_darken(self):
        base = np.full((4, 4, 3), 200, dtype=np.uint8)
        layer = np.zeros((4, 4, 4), dtype=np.uint8)
        layer[:, :, 0] = 50
        layer[:, :, 3] = 255
        result = composite_layer(base, layer, "darken")
        assert result[0, 0, 0] <= 50

    def test_overlay(self):
        base = np.full((4, 4, 3), 100, dtype=np.uint8)
        layer = np.zeros((4, 4, 4), dtype=np.uint8)
        layer[:, :, 0] = 200
        layer[:, :, 3] = 255
        result = composite_layer(base, layer, "overlay")
        assert result.shape == (4, 4, 3)

    def test_soft_light(self):
        base = np.full((4, 4, 3), 100, dtype=np.uint8)
        layer = np.zeros((4, 4, 4), dtype=np.uint8)
        layer[:, :, 0] = 200
        layer[:, :, 3] = 255
        result = composite_layer(base, layer, "soft_light")
        assert result.shape == (4, 4, 3)

    def test_unknown_mode_falls_to_normal(self):
        base = np.full((4, 4, 3), 100, dtype=np.uint8)
        layer = np.zeros((4, 4, 4), dtype=np.uint8)
        layer[:, :, 0] = 200
        layer[:, :, 3] = 255
        result = composite_layer(base, layer, "nonexistent")
        assert result.shape == (4, 4, 3)


class TestCompositeLayerMask:
    def test_2d_mask(self):
        base = np.zeros((4, 4, 3), dtype=np.uint8)
        layer = np.full((4, 4, 4), 255, dtype=np.uint8)
        mask = np.zeros((4, 4), dtype=np.uint8)
        mask[2, 2] = 255
        result = composite_layer(base, layer, "normal", mask)
        assert result.shape == (4, 4, 3)
        assert result[0, 0, 0] < result[2, 2, 0]

    def test_3channel_mask(self):
        base = np.zeros((4, 4, 3), dtype=np.uint8)
        layer = np.full((4, 4, 4), 255, dtype=np.uint8)
        mask = np.zeros((4, 4, 3), dtype=np.uint8)
        mask[2, 2, 0] = 255
        result = composite_layer(base, layer, "normal", mask)
        assert result.shape == (4, 4, 3)


class TestApplyGlow:
    def test_basic(self):
        layer = np.zeros((32, 32, 4), dtype=np.uint8)
        layer[14:18, 14:18, :] = 255
        glow = apply_glow(layer, (255, 200, 0), 5, 0.5)
        assert glow.shape == (32, 32, 4)
        assert np.count_nonzero(glow[:, :, 3]) > 0

    def test_3channel_input(self):
        layer = np.zeros((32, 32, 3), dtype=np.uint8)
        layer[14:18, 14:18, :] = 255
        glow = apply_glow(layer, (255, 0, 0), 5, 0.5)
        assert glow.shape[0] == 32
        assert glow.shape[1] == 32

    def test_zero_radius_returns_original(self):
        layer = np.zeros((16, 16, 4), dtype=np.uint8)
        layer[7, 7, :] = 255
        glow = apply_glow(layer, (255, 0, 0), 0, 0.5)
        assert np.array_equal(glow, layer)

    def test_low_intensity_returns_original(self):
        layer = np.zeros((16, 16, 4), dtype=np.uint8)
        layer[7, 7, :] = 255
        glow = apply_glow(layer, (255, 0, 0), 5, 0.005)
        assert np.array_equal(glow, layer)


class TestApplyBlur:
    def test_basic(self):
        layer = np.zeros((32, 32, 4), dtype=np.uint8)
        layer[14:18, 14:18, :] = 255
        blurred = apply_blur(layer, 3.0)
        assert blurred.shape == (32, 32, 4)

    def test_low_radius_no_change(self):
        layer = np.zeros((16, 16, 4), dtype=np.uint8)
        layer[7, 7, :] = 255
        blurred = apply_blur(layer, 0.3)
        assert np.array_equal(blurred, layer)


class TestFillCanvas:
    def test_basic(self):
        canvas = fill_canvas(64, 32, "#FF8C00")
        assert canvas.shape == (32, 64, 3)
        assert canvas.dtype == np.uint8
        assert np.all(canvas[0, 0] == [255, 140, 0])

    def test_black(self):
        canvas = fill_canvas(64, 32, "#000000")
        assert np.all(canvas == 0)

    def test_white(self):
        canvas = fill_canvas(64, 32, "#FFFFFF")
        assert np.all(canvas[0, 0] == [255, 255, 255])

    def test_3char_hex(self):
        canvas = fill_canvas(64, 32, "#F80")
        assert canvas.shape == (32, 64, 3)
        assert np.all(canvas[0, 0] == [255, 136, 0])
