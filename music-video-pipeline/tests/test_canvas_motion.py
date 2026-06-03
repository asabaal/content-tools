import numpy as np
import pytest

from canvas.motion import apply_motion, transform_layer, place_layer
from canvas.models import CanvasObject


class TestApplyMotionStatic:
    def test_static_returns_same(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [0.5, 0.5],
            "motion": {},
        })
        result = apply_motion(obj, (320.0, 180.0), 0.0, 1.0, 0.0, 640, 360)
        assert result["position"] == (320.0, 180.0)
        assert result["rotation"] == 0.0
        assert result["opacity"] == 1.0

    def test_no_motion_dict(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
        })
        result = apply_motion(obj, (100.0, 200.0), 45.0, 0.8, 1.0, 640, 360)
        assert result["position"] == (100.0, 200.0)
        assert result["rotation"] == 45.0
        assert result["opacity"] == 0.8

    def test_non_dict_motion_returns_same(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
        })
        obj.motion = "not a dict"
        result = apply_motion(obj, (100.0, 200.0), 0.0, 1.0, 1.0, 640, 360)
        assert result["position"] == (100.0, 200.0)


class TestApplyMotionRotate:
    def test_rotates_over_time(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "motion": {"type": "rotate", "speed": 1.0},
        })
        r0 = apply_motion(obj, (0, 0), 0.0, 1.0, 0.0, 640, 360)
        r1 = apply_motion(obj, (0, 0), 0.0, 1.0, 1.0, 640, 360)
        assert r1["rotation"] > r0["rotation"]


class TestApplyMotionDrift:
    def test_drifts_position(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "motion": {"type": "drift", "speed": 1.0, "amplitude": 0.1},
        })
        r0 = apply_motion(obj, (320.0, 180.0), 0.0, 1.0, 0.0, 640, 360)
        r1 = apply_motion(obj, (320.0, 180.0), 0.0, 1.0, 0.5, 640, 360)
        assert r0["position"] != r1["position"]


class TestApplyMotionPulse:
    def test_pulses_opacity(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "motion": {"type": "pulse", "speed": 1.0, "amplitude": 0.3},
        })
        r0 = apply_motion(obj, (0, 0), 0.0, 1.0, 0.0, 640, 360)
        r1 = apply_motion(obj, (0, 0), 0.0, 1.0, 0.25, 640, 360)
        assert r0["opacity"] != r1["opacity"]


class TestApplyMotionBreathe:
    def test_breathe_modulates_opacity(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "motion": {"type": "breathe", "speed": 1.0, "amplitude": 0.2},
        })
        r0 = apply_motion(obj, (0, 0), 0.0, 1.0, 0.0, 640, 360)
        assert 0.0 <= r0["opacity"] <= 1.0


class TestApplyMotionZoom:
    def test_zoom_returns_rotation(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "motion": {"type": "zoom", "speed": 1.0},
        })
        result = apply_motion(obj, (0, 0), 0.0, 1.0, 1.0, 640, 360)
        assert "rotation" in result


class TestApplyMotionShimmer:
    def test_shimmer_modulates_opacity(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "motion": {"type": "shimmer", "speed": 2.0, "amplitude": 0.5},
        })
        r0 = apply_motion(obj, (0, 0), 0.0, 1.0, 0.0, 640, 360)
        r1 = apply_motion(obj, (0, 0), 0.0, 1.0, 0.3, 640, 360)
        assert r0["opacity"] != r1["opacity"]


class TestApplyMotionOrbit:
    def test_orbit_moves_position(self):
        obj = CanvasObject.from_dict({
            "type": "shape",
            "motion": {"type": "orbit", "speed": 1.0, "radius": 0.1, "center": [0.5, 0.5]},
        })
        r0 = apply_motion(obj, (320.0, 180.0), 0.0, 1.0, 0.0, 640, 360)
        r1 = apply_motion(obj, (320.0, 180.0), 0.0, 1.0, 0.25, 640, 360)
        assert r0["position"] != r1["position"]


class TestApplyMotionUnknown:
    def test_unknown_returns_same(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "motion": {"type": "nonexistent"},
        })
        result = apply_motion(obj, (100.0, 200.0), 0.0, 1.0, 1.0, 640, 360)
        assert result["position"] == (100.0, 200.0)


class TestApplyMotionOpacityClamp:
    def test_opacity_clamped_to_one(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "motion": {"type": "pulse", "speed": 100, "amplitude": 5.0},
        })
        result = apply_motion(obj, (0, 0), 0.0, 1.0, 0.0, 640, 360)
        assert result["opacity"] <= 1.0

    def test_opacity_clamped_to_zero(self):
        obj = CanvasObject.from_dict({
            "type": "shape", "motion": {"type": "pulse", "speed": 100, "amplitude": 5.0},
        })
        result = apply_motion(obj, (0, 0), 0.0, 1.0, 0.5, 640, 360)
        assert result["opacity"] >= 0.0


class TestTransformLayer:
    def test_no_rotation_returns_same(self):
        layer = np.zeros((16, 16, 4), dtype=np.uint8)
        layer[7, 7, :] = 255
        result = transform_layer(layer, (8, 8), 0.0, 16, 16)
        assert np.array_equal(result, layer)

    def test_rotation_changes_pixels(self):
        layer = np.zeros((32, 32, 4), dtype=np.uint8)
        layer[0, :, :] = 255
        result = transform_layer(layer, (16, 16), 90.0, 32, 32)
        assert not np.array_equal(result, layer)

    def test_3channel(self):
        layer = np.zeros((16, 16, 3), dtype=np.uint8)
        layer[7, 7, :] = 255
        result = transform_layer(layer, (8, 8), 45.0, 16, 16)
        assert result.shape[2] == 3


class TestPlaceLayer:
    def test_center_placement(self):
        layer = np.full((16, 16, 4), 255, dtype=np.uint8)
        result = place_layer(layer, (32.0, 32.0), 64, 64, 1.0)
        assert result.shape == (64, 64, 4)
        assert np.count_nonzero(result[:, :, 3]) > 0

    def test_corner_placement(self):
        layer = np.full((8, 8, 4), 255, dtype=np.uint8)
        result = place_layer(layer, (4.0, 4.0), 64, 64, 1.0)
        assert result.shape == (64, 64, 4)
        assert np.count_nonzero(result[:, :, 3]) > 0

    def test_out_of_bounds(self):
        layer = np.full((16, 16, 4), 255, dtype=np.uint8)
        result = place_layer(layer, (-100.0, -100.0), 64, 64, 1.0)
        assert np.count_nonzero(result[:, :, 3]) == 0

    def test_opacity_modulation(self):
        layer = np.full((16, 16, 4), 200, dtype=np.uint8)
        r1 = place_layer(layer, (32.0, 32.0), 64, 64, 1.0)
        r2 = place_layer(layer, (32.0, 32.0), 64, 64, 0.5)
        assert np.max(r2[:, :, 3]) < np.max(r1[:, :, 3])

    def test_3channel_input(self):
        layer = np.full((16, 16, 3), 255, dtype=np.uint8)
        result = place_layer(layer, (32.0, 32.0), 64, 64, 1.0)
        assert result.shape == (64, 64, 4)
        assert np.count_nonzero(result[:, :, 3]) > 0

    def test_full_canvas_layer(self):
        layer = np.full((64, 64, 4), 128, dtype=np.uint8)
        result = place_layer(layer, (32.0, 32.0), 64, 64, 1.0)
        assert result.shape == (64, 64, 4)
        assert np.count_nonzero(result[:, :, 3]) > 0
