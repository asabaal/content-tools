import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from render.frame_effects import (
    apply_brightness_pulse,
    apply_camera_shake,
    apply_color_shift_frame,
    apply_contrast_pulse,
    apply_frame_effect,
    apply_glitch,
    apply_motion_blur,
    apply_vignette_pulse,
    apply_wave_distortion_frame,
    apply_zoom_blur,
    apply_zoom_pulse,
    apply_bokeh_particles,
    _FRAME_EFFECTS,
)


def _frame(w=64, h=64):
    return np.random.RandomState(42).randint(0, 256, (h, w, 3), dtype=np.uint8)


class TestApplyZoomPulse:
    def test_zero_intensity_returns_copy(self):
        f = _frame()
        r = apply_zoom_pulse(f, 1.0, intensity=0.0)
        assert r.shape == f.shape

    def test_with_intensity(self):
        f = _frame()
        r = apply_zoom_pulse(f, 1.0, intensity=0.05, speed=2.0)
        assert r.shape == f.shape
        assert np.all(r >= 0)


class TestApplyCameraShake:
    def test_zero_intensity_returns_copy(self):
        f = _frame()
        r = apply_camera_shake(f, 1.0, intensity=0.0)
        assert r.shape == f.shape

    def test_with_intensity(self):
        f = _frame()
        r = apply_camera_shake(f, 1.0, intensity=5.0, seed=42)
        assert r.shape == f.shape

    def test_reproducible_same_seed(self):
        f = _frame()
        r1 = apply_camera_shake(f, 1.0, intensity=5.0, seed=42)
        r2 = apply_camera_shake(f, 1.0, intensity=5.0, seed=42)
        assert np.array_equal(r1, r2)


class TestApplyWaveDistortionFrame:
    def test_zero_intensity_returns_copy(self):
        f = _frame()
        r = apply_wave_distortion_frame(f, 1.0, intensity=0.0)
        assert r.shape == f.shape

    def test_with_intensity(self):
        f = _frame()
        r = apply_wave_distortion_frame(f, 1.0, intensity=3.0, speed=1.0)
        assert r.shape == f.shape


class TestApplyZoomBlur:
    def test_zero_intensity_returns_copy(self):
        f = _frame()
        r = apply_zoom_blur(f, 1.0, intensity=0.0)
        assert r.shape == f.shape

    def test_with_intensity(self):
        f = _frame()
        r = apply_zoom_blur(f, 1.0, intensity=0.02)
        assert r.shape == f.shape
        assert np.all(r >= 0)
        assert np.all(r <= 255)


class TestApplyColorShiftFrame:
    def test_zero_shift_returns_copy(self):
        f = _frame()
        r = apply_color_shift_frame(f, 1.0, hue_shift=0.0)
        assert r.shape == f.shape

    def test_with_shift(self):
        f = _frame()
        r = apply_color_shift_frame(f, 1.0, hue_shift=30.0)
        assert r.shape == f.shape


class TestApplyBrightnessPulse:
    def test_produces_output(self):
        f = _frame()
        r = apply_brightness_pulse(f, 1.0, speed=1.0)
        assert r.shape == f.shape
        assert np.all(r >= 0)
        assert np.all(r <= 255)


class TestApplyContrastPulse:
    def test_produces_output(self):
        f = _frame()
        r = apply_contrast_pulse(f, 1.0, speed=1.0)
        assert r.shape == f.shape
        assert np.all(r >= 0)
        assert np.all(r <= 255)


class TestApplyGlitch:
    def test_zero_intensity_returns_copy(self):
        f = _frame()
        r = apply_glitch(f, 1.0, intensity=0.0)
        assert r.shape == f.shape

    def test_low_intensity(self):
        f = _frame()
        r = apply_glitch(f, 1.0, intensity=0.3)
        assert r.shape == f.shape

    def test_high_intensity_with_channel_split(self):
        f = _frame()
        r = apply_glitch(f, 1.0, intensity=0.8)
        assert r.shape == f.shape


class TestApplyVignettePulse:
    def test_zero_intensity_returns_copy(self):
        f = _frame()
        r = apply_vignette_pulse(f, 1.0, intensity=0.0)
        assert r.shape == f.shape

    def test_with_intensity(self):
        f = _frame()
        r = apply_vignette_pulse(f, 1.0, intensity=0.5)
        assert r.shape == f.shape
        assert np.all(r >= 0)
        assert np.all(r <= 255)


class TestApplyMotionBlur:
    def test_zero_intensity_returns_copy(self):
        f = _frame()
        r = apply_motion_blur(f, angle=0.0, intensity=0.0)
        assert r.shape == f.shape

    def test_with_intensity(self):
        f = _frame()
        r = apply_motion_blur(f, angle=45.0, intensity=5.0)
        assert r.shape == f.shape

    def test_various_angles(self):
        f = _frame()
        for angle in [0, 45, 90, 135]:
            r = apply_motion_blur(f, angle=angle, intensity=3.0)
            assert r.shape == f.shape


class TestApplyFrameEffect:
    def test_known_effect(self):
        f = _frame()
        r = apply_frame_effect(f, "zoom_pulse", 1.0, {"intensity": 0.05})
        assert r.shape == f.shape

    def test_unknown_effect_returns_copy(self):
        f = _frame()
        r = apply_frame_effect(f, "nonexistent", 1.0)
        assert r.shape == f.shape

    def test_all_registered_effects(self):
        f = _frame()
        for name in _FRAME_EFFECTS:
            r = apply_frame_effect(f, name, 1.0)
            assert r.shape == f.shape, f"{name} changed shape"

    def test_no_params(self):
        f = _frame()
        r = apply_frame_effect(f, "brightness_pulse", 1.0)
        assert r.shape == f.shape


class TestApplyMotionBlurSmallIntensity:
    def test_small_intensity_clamps_size(self):
        f = _frame()
        r = apply_motion_blur(f, angle=0.0, intensity=0.7)
        assert r.shape == f.shape


class TestApplyBokehEdgeCases:
    def test_small_max_radius(self):
        f = _frame(w=64, h=64)
        r = apply_bokeh_particles(f, 0.0, count=12, speed=0.3, max_radius=1)
        assert r.shape == f.shape

    def test_tiny_frame(self):
        f = _frame(w=4, h=4)
        r = apply_bokeh_particles(f, 5.0, count=20, speed=1.0, max_radius=50)
        assert r.shape == f.shape
