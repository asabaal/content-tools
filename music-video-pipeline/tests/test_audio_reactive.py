import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from render.audio_reactive import (
    apply_audio_effects,
    apply_beat_flash,
    apply_chromatic_aberration,
    apply_color_shift,
    apply_energy_burst,
    apply_energy_glow,
    apply_wave_distortion,
)


def _bgr_frame(w=64, h=64, val=128):
    return np.full((h, w, 3), val, dtype=np.uint8)


def _rgba_layer(w=64, h=64, val=128):
    return np.full((h, w, 4), val, dtype=np.uint8)


class TestApplyEnergyGlow:
    def test_zero_energy_returns_copy(self):
        frame = _bgr_frame()
        result = apply_energy_glow(frame, 0.0)
        assert result.shape == frame.shape
        assert not np.shares_memory(result, frame)

    def test_low_energy_no_crash(self):
        frame = _bgr_frame()
        result = apply_energy_glow(frame, 0.01)
        assert result.shape == frame.shape

    def test_high_energy_modifies_frame(self):
        bright = np.full((64, 64, 3), 250, dtype=np.uint8)
        result = apply_energy_glow(bright, 0.9, max_radius=15)
        assert result.shape == bright.shape
        assert result.dtype == np.uint8
        assert np.all(result >= 0)
        assert np.all(result <= 255)

    def test_custom_color(self):
        frame = _bgr_frame()
        result = apply_energy_glow(frame, 0.8, color=(0, 255, 0))
        assert result.shape == frame.shape


class TestApplyColorShift:
    def test_zero_energy_returns_copy(self):
        frame = _bgr_frame()
        result = apply_color_shift(frame, 0.5, 0.0)
        assert result.shape == frame.shape

    def test_high_energy_shifts(self):
        frame = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        result = apply_color_shift(frame, 0.5, 0.8)
        assert result.shape == frame.shape
        assert not np.array_equal(result, frame)

    def test_high_centroid_shifts_cool(self):
        frame = _bgr_frame()
        result = apply_color_shift(frame, 0.9, 0.5)
        assert result.shape == frame.shape

    def test_low_centroid_shifts_warm(self):
        frame = _bgr_frame()
        result = apply_color_shift(frame, 0.1, 0.5)
        assert result.shape == frame.shape

    def test_values_in_range(self):
        frame = _bgr_frame()
        result = apply_color_shift(frame, 0.7, 0.9)
        assert np.all(result >= 0)
        assert np.all(result <= 255)


class TestApplyBeatFlash:
    def test_no_beat_returns_copy(self):
        frame = _bgr_frame()
        result = apply_beat_flash(frame, False, 0.5)
        assert result.shape == frame.shape

    def test_beat_brightens(self):
        frame = _bgr_frame()
        result = apply_beat_flash(frame, True, 0.8)
        assert result.shape == frame.shape
        assert result.mean() >= frame.mean()

    def test_beat_high_energy(self):
        frame = _bgr_frame()
        result = apply_beat_flash(frame, True, 1.0)
        assert result.shape == frame.shape
        assert np.all(result >= 0)
        assert np.all(result <= 255)


class TestApplyWaveDistortion:
    def test_low_energy_returns_copy(self):
        layer = _rgba_layer()
        result = apply_wave_distortion(layer, 0.01, 0.0)
        assert result.shape == layer.shape

    def test_high_energy_distorts(self):
        layer = _rgba_layer()
        result = apply_wave_distortion(layer, 0.8, 1.5)
        assert result.shape == layer.shape

    def test_bgr_input(self):
        frame = _bgr_frame()
        result = apply_wave_distortion(frame, 0.8, 0.5)
        assert result.shape == frame.shape


class TestApplyChromaticAberration:
    def test_zero_energy_returns_copy(self):
        frame = _bgr_frame()
        result = apply_chromatic_aberration(frame, 0.0)
        assert result.shape == frame.shape

    def test_high_energy_shifts_channels(self):
        frame = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        result = apply_chromatic_aberration(frame, 0.9)
        assert result.shape == frame.shape
        assert not np.array_equal(result, frame)

    def test_values_in_range(self):
        frame = _bgr_frame()
        result = apply_chromatic_aberration(frame, 1.0)
        assert np.all(result >= 0)
        assert np.all(result <= 255)

    def test_rgba_layer(self):
        layer = _rgba_layer()
        result = apply_chromatic_aberration(layer, 0.8)
        assert result.shape == layer.shape


class TestApplyEnergyBurst:
    def test_low_energy_returns_copy(self):
        frame = _bgr_frame()
        result = apply_energy_burst(frame, 0.3)
        assert result.shape == frame.shape

    def test_high_energy_produces_burst(self):
        frame = _bgr_frame()
        result = apply_energy_burst(frame, 0.8)
        assert result.shape == frame.shape
        assert np.all(result >= 0)
        assert np.all(result <= 255)

    def test_custom_center(self):
        frame = _bgr_frame()
        result = apply_energy_burst(frame, 0.9, center=(32, 32))
        assert result.shape == frame.shape

    def test_very_high_energy(self):
        frame = _bgr_frame()
        result = apply_energy_burst(frame, 1.0)
        assert result.shape == frame.shape


class TestApplyAudioEffects:
    def test_no_reactivity_returns_copy(self):
        frame = _bgr_frame()
        audio = {"energy": 0.8, "centroid": 0.5, "is_beat": True}
        result = apply_audio_effects(frame, audio, 1.0, reactivity=[])
        assert result.shape == frame.shape

    def test_energy_reactivity(self):
        frame = _bgr_frame()
        audio = {"energy": 0.8, "centroid": 0.5, "is_beat": False}
        result = apply_audio_effects(frame, audio, 1.0, reactivity=["energy"])
        assert result.shape == frame.shape

    def test_drums_reactivity(self):
        frame = _bgr_frame()
        audio = {"energy": 0.8, "centroid": 0.5, "is_beat": True}
        result = apply_audio_effects(frame, audio, 1.0, reactivity=["drums"])
        assert result.shape == frame.shape

    def test_vocals_reactivity(self):
        frame = _bgr_frame()
        audio = {"energy": 0.5, "centroid": 0.5, "is_beat": False}
        result = apply_audio_effects(frame, audio, 1.0, reactivity=["vocals"])
        assert result.shape == frame.shape

    def test_all_reactivities(self):
        frame = _bgr_frame()
        audio = {"energy": 0.9, "centroid": 0.7, "is_beat": True}
        result = apply_audio_effects(frame, audio, 2.0, reactivity=["energy", "drums", "vocals"])
        assert result.shape == frame.shape
        assert np.all(result >= 0)
        assert np.all(result <= 255)

    def test_default_reactivity_none(self):
        frame = _bgr_frame()
        audio = {"energy": 0.8, "centroid": 0.5, "is_beat": True}
        result = apply_audio_effects(frame, audio, 1.0)
        assert result.shape == frame.shape

    def test_missing_audio_keys(self):
        frame = _bgr_frame()
        result = apply_audio_effects(frame, {}, 1.0, reactivity=["energy"])
        assert result.shape == frame.shape

    def test_low_energy_vocals_skipped(self):
        frame = _bgr_frame()
        audio = {"energy": 0.1, "centroid": 0.5, "is_beat": False}
        result = apply_audio_effects(frame, audio, 1.0, reactivity=["vocals"])
        assert result.shape == frame.shape


class TestApplyEnergyBurstEdgeCases:
    def test_zero_center(self):
        frame = _bgr_frame()
        result = apply_energy_burst(frame, 0.9, center=(0, 0))
        assert result.shape == frame.shape
