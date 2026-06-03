import numpy as np
import pytest

from canvas.lights import render_light, render_gradient
from canvas.models import CanvasObject


class TestRenderLightRadial:
    def test_basic(self):
        obj = CanvasObject.from_dict({
            "type": "light",
            "geometry": {"shape": "radial"},
            "position": [0.5, 0.5],
            "size": [0.5, 0.5],
            "opacity": 1.0,
            "style": {"color": "#FF8C00", "intensity": 1.0, "softness": 1.0},
        })
        layer = render_light(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert layer.dtype == np.uint8
        assert np.count_nonzero(layer[:, :, 3]) > 0
        assert np.max(layer[:, :, :3]) > 0

    def test_3char_hex_color(self):
        obj = CanvasObject.from_dict({
            "type": "light", "geometry": {"shape": "radial"},
            "position": [0.5, 0.5], "size": [0.5, 0.5], "opacity": 1.0,
            "style": {"color": "#F80", "intensity": 1.0, "softness": 1.0},
        })
        layer = render_light(obj, 64, 64, {})
        assert np.count_nonzero(layer[:, :, 3]) > 0

    def test_center_is_brightest(self):
        obj = CanvasObject.from_dict({
            "type": "light",
            "geometry": {"shape": "radial"},
            "position": [0.5, 0.5],
            "size": [0.5, 0.5],
            "opacity": 1.0,
            "style": {"color": "#FFFFFF", "intensity": 1.0, "softness": 1.0},
        })
        layer = render_light(obj, 64, 64, {})
        center_alpha = layer[32, 32, 3]
        corner_alpha = layer[0, 0, 3]
        assert center_alpha > corner_alpha

    def test_opacity_modulates(self):
        obj1 = CanvasObject.from_dict({
            "type": "light", "geometry": {"shape": "radial"},
            "position": [0.5, 0.5], "size": [0.5, 0.5], "opacity": 1.0,
            "style": {"color": "#FFFFFF", "intensity": 1.0, "softness": 1.0},
        })
        obj2 = CanvasObject.from_dict({
            "type": "light", "geometry": {"shape": "radial"},
            "position": [0.5, 0.5], "size": [0.5, 0.5], "opacity": 0.3,
            "style": {"color": "#FFFFFF", "intensity": 1.0, "softness": 1.0},
        })
        l1 = render_light(obj1, 64, 64, {})
        l2 = render_light(obj2, 64, 64, {})
        assert np.max(l1[:, :, 3]) > np.max(l2[:, :, 3])

    def test_palette_color(self):
        obj = CanvasObject.from_dict({
            "type": "light", "geometry": {"shape": "radial"},
            "position": [0.5, 0.5], "size": [0.5, 0.5], "opacity": 1.0,
            "style": {"color": "$primary", "intensity": 1.0, "softness": 1.0},
        })
        layer = render_light(obj, 64, 64, {"primary": "#2E86C1"})
        assert np.count_nonzero(layer[:, :, 3]) > 0


class TestRenderLightConic:
    def test_basic(self):
        obj = CanvasObject.from_dict({
            "type": "light", "geometry": {"shape": "conic"},
            "position": [0.5, 0.5], "size": [1.0, 1.0], "opacity": 0.8,
            "style": {"color": "#FF8C00", "intensity": 1.0, "softness": 0.8},
        })
        layer = render_light(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) > 0

    def test_with_offset(self):
        obj = CanvasObject.from_dict({
            "type": "light", "geometry": {"shape": "conic", "offset": 1.0},
            "position": [0.5, 0.5], "size": [1.0, 1.0], "opacity": 0.8,
            "style": {"color": "#FF8C00", "intensity": 1.0, "softness": 0.8},
        })
        layer = render_light(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)


class TestRenderLightSpot:
    def test_basic(self):
        obj = CanvasObject.from_dict({
            "type": "light", "geometry": {"shape": "spot", "angle": 45, "spread": 0.5},
            "position": [0.5, 0.5], "size": [0.5, 0.5], "opacity": 1.0,
            "style": {"color": "#FF8C00", "intensity": 1.0, "softness": 1.0},
        })
        layer = render_light(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) > 0


class TestRenderLightUnknown:
    def test_unknown_type_returns_zeros(self):
        obj = CanvasObject.from_dict({
            "type": "light", "geometry": {"shape": "nonexistent"},
            "position": [0.5, 0.5], "size": [0.5, 0.5], "opacity": 1.0,
            "style": {"color": "#FFFFFF", "intensity": 1.0, "softness": 1.0},
        })
        layer = render_light(obj, 64, 64, {})
        assert np.count_nonzero(layer) == 0


class TestRenderGradient:
    def test_horizontal(self):
        obj = CanvasObject.from_dict({
            "type": "gradient",
            "geometry": {"direction": "horizontal"},
            "position": [0.5, 0.5], "size": [1.0, 1.0], "opacity": 1.0,
            "style": {"colors": ["#FF0000", "#0000FF"]},
        })
        layer = render_gradient(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, :3]) > 0

    def test_vertical(self):
        obj = CanvasObject.from_dict({
            "type": "gradient",
            "geometry": {"direction": "vertical"},
            "position": [0.5, 0.5], "size": [1.0, 1.0], "opacity": 1.0,
            "style": {"colors": ["#FF0000", "#0000FF"]},
        })
        layer = render_gradient(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        left = layer[0, 0, :3]
        right = layer[63, 63, :3]
        assert not np.array_equal(left, right)

    def test_radial(self):
        obj = CanvasObject.from_dict({
            "type": "gradient",
            "geometry": {"direction": "radial"},
            "position": [0.5, 0.5], "size": [1.0, 1.0], "opacity": 1.0,
            "style": {"colors": ["#FF0000", "#0000FF"]},
        })
        layer = render_gradient(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)

    def test_conic(self):
        obj = CanvasObject.from_dict({
            "type": "gradient",
            "geometry": {"direction": "conic"},
            "position": [0.5, 0.5], "size": [1.0, 1.0], "opacity": 1.0,
            "style": {"colors": ["#FF0000", "#00FF00", "#0000FF"]},
        })
        layer = render_gradient(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)

    def test_angle_gradient(self):
        obj = CanvasObject.from_dict({
            "type": "gradient",
            "geometry": {"direction": "angle_45"},
            "position": [0.5, 0.5], "size": [1.0, 1.0], "opacity": 1.0,
            "style": {"colors": ["#FF0000", "#0000FF"]},
        })
        layer = render_gradient(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)

    def test_angle_no_suffix(self):
        obj = CanvasObject.from_dict({
            "type": "gradient",
            "geometry": {"direction": "angle_"},
            "position": [0.5, 0.5], "size": [1.0, 1.0], "opacity": 1.0,
            "style": {"colors": ["#FF0000", "#0000FF"]},
        })
        with pytest.raises(ValueError):
            render_gradient(obj, 64, 64, {})

    def test_empty_colors_defaults(self):
        obj = CanvasObject.from_dict({
            "type": "gradient",
            "geometry": {"direction": "horizontal"},
            "position": [0.5, 0.5], "size": [1.0, 1.0], "opacity": 1.0,
            "style": {"colors": []},
        })
        layer = render_gradient(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, :3]) > 0

    def test_multi_color_gradient(self):
        obj = CanvasObject.from_dict({
            "type": "gradient",
            "geometry": {"direction": "horizontal"},
            "position": [0.5, 0.5], "size": [1.0, 1.0], "opacity": 1.0,
            "style": {"colors": ["#FF0000", "#00FF00", "#0000FF"]},
        })
        layer = render_gradient(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)

    def test_unknown_direction_falls_to_vertical(self):
        obj = CanvasObject.from_dict({
            "type": "gradient",
            "geometry": {"direction": "unknown"},
            "position": [0.5, 0.5], "size": [1.0, 1.0], "opacity": 1.0,
            "style": {"colors": ["#FF0000", "#0000FF"]},
        })
        layer = render_gradient(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
