import numpy as np
import pytest

from canvas.geometry import render_shape, render_path
from canvas.models import CanvasObject


def _make_obj(**overrides):
    defaults = {
        "type": "shape",
        "geometry": {"shape": "rectangle"},
        "position": [0.5, 0.5],
        "size": [0.5, 0.5],
        "opacity": 1.0,
        "style": {"fill": "#FF8C00"},
    }
    defaults.update(overrides)
    return CanvasObject.from_dict(defaults)


class TestRenderShapeRectangle:
    def test_basic(self):
        obj = _make_obj(geometry={"shape": "rectangle"})
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert layer.dtype == np.uint8
        assert np.count_nonzero(layer[:, :, 3]) > 0

    def test_full_size(self):
        obj = _make_obj(size=[1.0, 1.0])
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.all(layer[:, :, 3] > 0)

    def test_rect_alias(self):
        obj = _make_obj(geometry={"shape": "rect"})
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)


class TestRenderShapeCircle:
    def test_basic(self):
        obj = _make_obj(geometry={"shape": "circle"})
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) > 0

    def test_ellipse_alias(self):
        obj = _make_obj(geometry={"shape": "ellipse"})
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)


class TestRenderShapeDiamond:
    def test_basic(self):
        obj = _make_obj(geometry={"shape": "diamond"})
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) > 0


class TestRenderShapePolygon:
    @pytest.mark.parametrize("shape", ["polygon", "hexagon", "octagon", "pentagon", "triangle"])
    def test_polygon_types(self, shape):
        obj = _make_obj(geometry={"shape": shape, "sides": 6})
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) > 0


class TestRenderShapeLine:
    def test_basic(self):
        obj = _make_obj(geometry={"shape": "line"}, style={"stroke": "#FFFFFF", "stroke_width": 2, "fill": "none"})
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) > 0


class TestRenderShapeRing:
    def test_basic(self):
        obj = _make_obj(
            geometry={"shape": "ring", "inner": 0.3},
            size=[0.5, 0.5],
            style={"stroke": "#FF8C00", "stroke_width": 3, "fill": "none"},
        )
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) > 0


class TestRenderShapeArc:
    def test_basic(self):
        obj = _make_obj(
            geometry={"shape": "arc", "start_angle": 0, "end_angle": 180},
            style={"stroke": "#FF8C00", "stroke_width": 3, "fill": "none"},
        )
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) > 0


class TestRenderShapeGrid:
    def test_basic(self):
        obj = _make_obj(
            geometry={"shape": "grid", "rows": 4, "cols": 4, "gap": 2},
            style={"stroke": "#FF8C00", "stroke_width": 1, "fill": "none"},
        )
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) > 0


class TestRenderShapeUnknown:
    def test_unknown_shape_returns_blank(self):
        obj = _make_obj(geometry={"shape": "nonexistent"})
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer) == 0


class TestRenderShapeFillStroke:
    def test_fill_only(self):
        obj = _make_obj(style={"fill": "#FF0000"})
        layer = render_shape(obj, 64, 64, {})
        assert np.count_nonzero(layer[:, :, 3]) > 0

    def test_stroke_only(self):
        obj = _make_obj(style={"stroke": "#00FF00", "stroke_width": 3, "fill": "none"})
        layer = render_shape(obj, 64, 64, {})
        assert np.count_nonzero(layer[:, :, 3]) > 0

    def test_no_fill_no_stroke(self):
        obj = _make_obj(style={"fill": "none"})
        layer = render_shape(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)

    def test_palette_color(self):
        obj = _make_obj(style={"fill": "$primary"})
        layer = render_shape(obj, 64, 64, {"primary": "#2E86C1"})
        assert np.count_nonzero(layer[:, :, 3]) > 0

    def test_rounded_rectangle(self):
        obj = _make_obj(geometry={"shape": "rectangle"}, style={"fill": "#FF8C00", "corner_radius": 5})
        layer = render_shape(obj, 64, 64, {})
        assert np.count_nonzero(layer[:, :, 3]) > 0

    def test_3char_hex_color(self):
        obj = _make_obj(style={"fill": "#F80"})
        layer = render_shape(obj, 64, 64, {})
        assert np.count_nonzero(layer[:, :, 3]) > 0


class TestRenderPath:
    def test_open_path(self):
        obj = _make_obj(
            type="shape",
            geometry={
                "shape": "line",
                "points": [[0.2, 0.2], [0.8, 0.8]],
                "closed": False,
            },
            style={"stroke": "#FF8C00", "stroke_width": 2, "fill": "none"},
        )
        layer = render_path(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) > 0

    def test_closed_path(self):
        obj = _make_obj(
            type="shape",
            geometry={
                "shape": "line",
                "points": [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]],
                "closed": True,
            },
            style={"stroke": "#FF8C00", "stroke_width": 2, "fill": "#FF0000"},
        )
        layer = render_path(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) > 0

    def test_single_point_returns_blank(self):
        obj = _make_obj(
            type="shape",
            geometry={"shape": "line", "points": [[0.5, 0.5]]},
            style={"stroke": "#FF8C00", "stroke_width": 2, "fill": "none"},
        )
        layer = render_path(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) == 0

    def test_empty_points_returns_blank(self):
        obj = _make_obj(
            type="shape",
            geometry={"shape": "line", "points": []},
            style={"stroke": "#FF8C00", "stroke_width": 2, "fill": "none"},
        )
        layer = render_path(obj, 64, 64, {})
        assert layer.shape == (64, 64, 4)
        assert np.count_nonzero(layer[:, :, 3]) == 0

    def test_absolute_points(self):
        obj = _make_obj(
            type="shape",
            geometry={"shape": "line", "points": [[10, 10], [50, 50]]},
            style={"stroke": "#FF8C00", "stroke_width": 2, "fill": "none"},
        )
        layer = render_path(obj, 64, 64, {})
        assert np.count_nonzero(layer[:, :, 3]) > 0
