"""Tests for animation frame generators.

Validates that all animation types operate on the entire background as a
continuous field G(x,y,t) with no localized artifacts, bands, or block patterns.
"""

import numpy as np
import pytest
from PIL import Image

from src.config.defaults import AnimType
from src.renderer.animation import AnimationFrameGenerator

WIDTH, HEIGHT = 200, 200
GRADIENT_COLORS = ["#4A90E2", "#2C3E50"]


def _make_gen(anim_type: AnimType, **kwargs: object) -> AnimationFrameGenerator:
    defaults: dict = dict(
        anim_type=anim_type,
        intensity=0.3,
        speed=1.0,
        width=WIDTH,
        height=HEIGHT,
        seed=42,
        gradient_colors=GRADIENT_COLORS,
    )
    defaults.update(kwargs)
    return AnimationFrameGenerator(**defaults)


def _pixel_diff_pct(img_a: Image.Image, img_b: Image.Image) -> float:
    a = np.array(img_a, dtype=np.int16)
    b = np.array(img_b, dtype=np.int16)
    diff = np.abs(a - b).sum(axis=2)
    changed = np.count_nonzero(diff > 0)
    return changed / diff.size


class TestDrift:
    def test_full_frame_change(self):
        gen = _make_gen("drift")
        f0 = gen.generate_background_frame(0.0)
        f_mid = gen.generate_background_frame(0.5)
        assert _pixel_diff_pct(f0, f_mid) > 0.95

    def test_smooth_no_hard_edges(self):
        gen = _make_gen("drift")
        frame = gen.generate_background_frame(0.5)
        arr = np.array(frame, dtype=np.float64)
        dx = np.abs(np.diff(arr, axis=1))
        dy = np.abs(np.diff(arr, axis=0))
        assert dx.max() < 30
        assert dy.max() < 30

    def test_uniform_shift(self):
        gen = _make_gen("drift", width=100, height=100, intensity=0.2)
        f0 = gen.generate_background_frame(0.0)
        f1 = gen.generate_background_frame(0.25)
        assert _pixel_diff_pct(f0, f1) > 0.5


class TestFlow:
    def test_full_frame_change(self):
        gen = _make_gen("flow", intensity=0.4)
        f0 = gen.generate_background_frame(0.0)
        f_mid = gen.generate_background_frame(0.5)
        assert _pixel_diff_pct(f0, f_mid) > 0.95

    def test_per_pixel_variation(self):
        gen = _make_gen("flow")
        frame = gen.generate_background_frame(0.5)
        arr = np.array(frame, dtype=np.int16)
        row_diffs = np.abs(np.diff(arr, axis=1)).sum(axis=2)
        assert row_diffs.max() > 0

    def test_smooth_no_hard_edges(self):
        gen = _make_gen("flow", intensity=0.4)
        frame = gen.generate_background_frame(0.5)
        arr = np.array(frame, dtype=np.float64)
        dx = np.abs(np.diff(arr, axis=1))
        dy = np.abs(np.diff(arr, axis=0))
        assert dx.max() < 40
        assert dy.max() < 40


class TestPulse:
    def test_uniform_brightness_change(self):
        gen = _make_gen("pulse")
        f0 = gen.generate_background_frame(0.0)
        f_peak = gen.generate_background_frame(0.25)
        a0 = np.array(f0, dtype=np.float64)
        a1 = np.array(f_peak, dtype=np.float64)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(a0 > 0, a1 / a0, 1.0)
        expected_ratio = np.mean(ratio[a0 > 1.0])
        assert np.allclose(ratio[a0 > 1.0], expected_ratio, atol=0.05)

    def test_brightness_range(self):
        gen = _make_gen("pulse", intensity=0.5)
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            frame = gen.generate_background_frame(t)
            arr = np.array(frame)
            assert arr.min() >= 0
            assert arr.max() <= 255

    def test_changes_over_time(self):
        gen = _make_gen("pulse")
        f_early = gen.generate_background_frame(0.0)
        f_peak = gen.generate_background_frame(0.25)
        assert _pixel_diff_pct(f_early, f_peak) > 0.0


class TestDistortion:
    def test_full_frame_change(self):
        gen = _make_gen("distortion", intensity=0.5)
        f0 = gen.generate_background_frame(0.0)
        f_mid = gen.generate_background_frame(0.5)
        assert _pixel_diff_pct(f0, f_mid) > 0.80

    def test_no_block_artifacts(self):
        gen = _make_gen("distortion")
        frame = gen.generate_background_frame(0.5)
        arr = np.array(frame, dtype=np.float64)
        block_size = 4
        for by in range(0, HEIGHT - block_size, block_size):
            for bx in range(0, WIDTH - block_size, block_size):
                block = arr[by : by + block_size, bx : bx + block_size]
                uniq = np.unique(block.reshape(-1, 3), axis=0)
                assert len(uniq) > 1, f"Flat block at ({bx},{by})"

    def test_smooth_transitions(self):
        gen = _make_gen("distortion")
        frame = gen.generate_background_frame(0.5)
        arr = np.array(frame, dtype=np.float64)
        dx = np.abs(np.diff(arr, axis=1))
        dy = np.abs(np.diff(arr, axis=0))
        assert dx.max() < 30
        assert dy.max() < 30


class TestParallax:
    def test_full_frame_change(self):
        gen = _make_gen("parallax")
        f0 = gen.generate_background_frame(0.0)
        f_mid = gen.generate_background_frame(0.5)
        assert _pixel_diff_pct(f0, f_mid) > 0.95

    def test_no_horizontal_bands(self):
        gen = _make_gen("parallax")
        f0 = gen.generate_background_frame(0.0)
        f1 = gen.generate_background_frame(0.3)
        diff = np.abs(np.array(f0, dtype=np.int16) - np.array(f1, dtype=np.int16)).sum(axis=2)
        row_means = diff.mean(axis=1)
        assert row_means.std() / max(row_means.mean(), 1) < 1.0

    def test_full_coverage(self):
        gen = _make_gen("parallax")
        frame = gen.generate_background_frame(0.5)
        arr = np.array(frame)
        assert arr.min() >= 0
        assert arr.max() > 0

    def test_no_sharp_edges(self):
        gen = _make_gen("parallax")
        frame = gen.generate_background_frame(0.5)
        arr = np.array(frame, dtype=np.float64)
        dy = np.abs(np.diff(arr, axis=0))
        assert dy.max() < 30


class TestReactive:
    def test_equals_pulse(self):
        gen_r = _make_gen("reactive")
        gen_p = _make_gen("pulse")
        for t in [0.0, 0.25, 0.5, 0.75]:
            fr = gen_r.generate_background_frame(t)
            fp = gen_p.generate_background_frame(t)
            assert np.array_equal(np.array(fr), np.array(fp))


class TestDeterminism:
    @pytest.mark.parametrize("anim_type", ["drift", "flow", "pulse", "distortion", "parallax"])
    def test_same_seed_same_output(self, anim_type: AnimType):
        gen_a = _make_gen(anim_type, seed=123)
        gen_b = _make_gen(anim_type, seed=123)
        fa = gen_a.generate_background_frame(0.5)
        fb = gen_b.generate_background_frame(0.5)
        assert np.array_equal(np.array(fa), np.array(fb))

    @pytest.mark.parametrize("anim_type", ["flow", "distortion"])
    def test_different_seed_different_output(self, anim_type: AnimType):
        gen_a = _make_gen(anim_type, seed=123)
        gen_b = _make_gen(anim_type, seed=456)
        fa = gen_a.generate_background_frame(0.5)
        fb = gen_b.generate_background_frame(0.5)
        assert not np.array_equal(np.array(fa), np.array(fb))


class TestDimensions:
    @pytest.mark.parametrize("anim_type", ["drift", "flow", "pulse", "distortion", "parallax"])
    def test_output_size(self, anim_type: AnimType):
        gen = _make_gen(anim_type, width=320, height=240)
        frame = gen.generate_background_frame(0.5)
        assert frame.size == (320, 240)

    @pytest.mark.parametrize("anim_type", ["drift", "flow", "pulse", "distortion", "parallax"])
    def test_output_mode_rgb(self, anim_type: AnimType):
        gen = _make_gen(anim_type)
        frame = gen.generate_background_frame(0.5)
        assert frame.mode == "RGB"


class TestIntensityClamp:
    def test_clamp_high(self):
        gen = _make_gen("drift", intensity=1.0)
        assert gen.intensity == 0.5

    def test_clamp_negative(self):
        gen = _make_gen("drift", intensity=-0.5)
        assert gen.intensity == 0.0

    def test_zero_intensity(self):
        gen = _make_gen("drift", intensity=0.0)
        f0 = gen.generate_background_frame(0.0)
        f1 = gen.generate_background_frame(0.5)
        assert _pixel_diff_pct(f0, f1) < 0.05
