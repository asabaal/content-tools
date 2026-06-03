import numpy as np
import pytest

from canvas.text_safety import render_text_safety_overlay


class TestRenderTextSafetyNone:
    def test_none_mode(self):
        overlay = render_text_safety_overlay(64, 64, {"mode": "none"})
        assert overlay.shape == (64, 64, 4)
        assert np.count_nonzero(overlay) == 0

    def test_empty_config(self):
        overlay = render_text_safety_overlay(64, 64, {})
        assert overlay.shape == (64, 64, 4)
        assert np.count_nonzero(overlay) == 0

    def test_none_config(self):
        overlay = render_text_safety_overlay(64, 64, None)
        assert overlay.shape == (64, 64, 4)
        assert np.count_nonzero(overlay) == 0


class TestRenderTextSafetyDimCenter:
    def test_basic(self):
        overlay = render_text_safety_overlay(64, 64, {"mode": "dim_center", "strength": 0.5})
        assert overlay.shape == (64, 64, 4)
        assert np.count_nonzero(overlay[:, :, 3]) > 0

    def test_center_darker(self):
        overlay = render_text_safety_overlay(64, 64, {"mode": "dim_center", "strength": 0.8})
        center_alpha = overlay[32, 32, 3]
        corner_alpha = overlay[0, 0, 3]
        assert center_alpha > corner_alpha

    def test_dim_alias(self):
        overlay = render_text_safety_overlay(64, 64, {"mode": "dim", "strength": 0.5})
        assert overlay.shape == (64, 64, 4)
        assert np.count_nonzero(overlay[:, :, 3]) > 0


class TestRenderTextSafetyVignetteText:
    def test_basic(self):
        overlay = render_text_safety_overlay(64, 64, {"mode": "vignette_text", "strength": 0.5})
        assert overlay.shape == (64, 64, 4)
        assert np.count_nonzero(overlay[:, :, 3]) > 0


class TestRenderTextSafetyUnknown:
    def test_unknown_mode_returns_blank(self):
        overlay = render_text_safety_overlay(64, 64, {"mode": "nonexistent"})
        assert overlay.shape == (64, 64, 4)
        assert np.count_nonzero(overlay) == 0


class TestRenderTextSafetySize:
    def test_custom_size(self):
        overlay = render_text_safety_overlay(1920, 1080, {"mode": "dim_center", "strength": 0.3})
        assert overlay.shape == (1080, 1920, 4)

    def test_tiny_size(self):
        overlay = render_text_safety_overlay(1, 1, {"mode": "dim_center", "strength": 0.5})
        assert overlay.shape == (1, 1, 4)
