import numpy as np
import pytest

from canvas.models import CanvasObject
from canvas.repetition import expand_repeats


class TestExpandRepeatsNone:
    def test_single_instance(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [0.5, 0.5],
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 1
        assert instances[0]["position"] == (320.0, 180.0)
        assert instances[0]["opacity"] == 1.0

    def test_preserves_rotation(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [0.5, 0.5],
            "rotation": 45.0,
        })
        instances = expand_repeats(obj, 640, 360)
        assert instances[0]["rotation"] == 45.0

    def test_explicit_none_mode(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.3, 0.7], "size": [0.5, 0.5],
            "repeat": {"mode": "none"},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 1
        x, y = instances[0]["position"]
        assert abs(x - 192.0) < 1.0
        assert abs(y - 252.0) < 1.0


class TestExpandRepeatsGrid:
    def test_2x2_grid(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [0.1, 0.1],
            "repeat": {"mode": "grid", "rows": 2, "cols": 2, "spacing": 0.2},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 4

    def test_single_row(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [0.1, 0.1],
            "repeat": {"mode": "grid", "rows": 1, "cols": 5, "spacing": 0.1},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 5

    def test_jitter(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [0.1, 0.1],
            "repeat": {"mode": "grid", "rows": 3, "cols": 3, "spacing": 0.1, "jitter_x": 0.02, "jitter_y": 0.02},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 9

    def test_default_spacing(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [0.1, 0.1],
            "repeat": {"mode": "grid", "rows": 2, "cols": 2},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 4

    def test_separate_spacing_x_y(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [0.1, 0.1],
            "repeat": {"mode": "grid", "rows": 2, "cols": 2, "spacing_x": 0.3, "spacing_y": 0.1},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 4
        xs = [inst["position"][0] for inst in instances]
        ys = [inst["position"][1] for inst in instances]
        assert len(set(xs)) >= 2
        assert len(set(ys)) >= 2


class TestExpandRepeatsRadial:
    def test_6_instances(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "circle"},
            "position": [0.5, 0.5], "size": [0.05, 0.05],
            "repeat": {"mode": "radial", "count": 6, "radius": 0.2},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 6

    def test_positions_around_center(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "circle"},
            "position": [0.5, 0.5], "size": [0.05, 0.05],
            "repeat": {"mode": "radial", "count": 4, "radius": 0.1},
        })
        instances = expand_repeats(obj, 640, 360)
        positions = [inst["position"] for inst in instances]
        assert len(set(positions)) >= 2


class TestExpandRepeatsRandom:
    def test_count(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "circle"},
            "position": [0.5, 0.5], "size": [0.05, 0.05],
            "repeat": {"mode": "random", "count": 10, "seed": 42},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 10

    def test_deterministic_with_seed(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "circle"},
            "position": [0.5, 0.5], "size": [0.05, 0.05],
            "repeat": {"mode": "random", "count": 5, "seed": 123},
        })
        i1 = expand_repeats(obj, 640, 360)
        i2 = expand_repeats(obj, 640, 360)
        for a, b in zip(i1, i2):
            assert a["position"] == b["position"]

    def test_area_bounds(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "circle"},
            "position": [0.5, 0.5], "size": [0.05, 0.05],
            "repeat": {"mode": "random", "count": 20, "seed": 1,
                       "area": {"x": 0.4, "y": 0.4, "w": 0.2, "h": 0.2}},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 20
        for inst in instances:
            x, y = inst["position"]
            assert 200 <= x <= 400, f"x={x} out of bounds"
            assert 120 <= y <= 240, f"y={y} out of bounds"


class TestExpandRepeatsMirror:
    def test_x_mirror(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.3, 0.5], "size": [0.1, 0.1],
            "repeat": {"mode": "mirror", "axes": "x"},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 2

    def test_y_mirror(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.3], "size": [0.1, 0.1],
            "repeat": {"mode": "mirror", "axes": "y"},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 2

    def test_xy_mirror(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.3, 0.3], "size": [0.1, 0.1],
            "repeat": {"mode": "mirror", "axes": "xy"},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 4


class TestExpandRepeatsUnknown:
    def test_unknown_mode_returns_empty(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [0.5, 0.5],
            "repeat": {"mode": "nonexistent"},
        })
        instances = expand_repeats(obj, 640, 360)
        assert len(instances) == 0


class TestExpandRepeatsOpacityClamp:
    def test_opacity_clamped_to_one(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [0.5, 0.5],
            "opacity": 2.0,
        })
        instances = expand_repeats(obj, 640, 360)
        assert instances[0]["opacity"] <= 1.0

    def test_negative_opacity_clamped(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [0.5, 0.5],
            "opacity": -0.5,
        })
        instances = expand_repeats(obj, 640, 360)
        assert instances[0]["opacity"] >= 0.0
