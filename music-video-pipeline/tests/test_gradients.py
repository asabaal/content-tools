from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from render.gradients import (
    PRIMITIVES,
    RECIPES,
    MAX_SCATTER_COUNT,
    apply_color_map,
    parse_direction,
    resolve_gradient,
    compute_field,
    resolve_and_compute,
    _prim_linear,
    _prim_spot_field,
    _prim_conic,
    _prim_spiral,
    _prim_cross,
    _prim_diamond,
    _prim_bands,
    _prim_rings,
    _prim_grid,
    _prim_scatter_field,
    _prim_burst,
)

W, H = 64, 64


def _field_ok(t, w=W, h=H):
    assert t.shape == (h, w)
    assert t.dtype == np.float32
    assert t.min() >= 0.0 - 1e-6
    assert t.max() <= 1.0 + 1e-6


# ===================================================================
# Primitive field validity
# ===================================================================

class TestLinearPrimitive:
    def test_axis_y(self):
        t = _prim_linear(W, H, axis="y")
        _field_ok(t)
        assert t[0, W // 2] < t[H - 1, W // 2]

    def test_axis_y_reverse(self):
        t = _prim_linear(W, H, axis="y", reverse=True)
        _field_ok(t)
        assert t[0, W // 2] > t[H - 1, W // 2]

    def test_axis_x(self):
        t = _prim_linear(W, H, axis="x")
        _field_ok(t)
        assert t[H // 2, 0] < t[H // 2, W - 1]

    def test_axis_x_reverse(self):
        t = _prim_linear(W, H, axis="x", reverse=True)
        _field_ok(t)
        assert t[H // 2, 0] > t[H // 2, W - 1]

    def test_axis_diagonal(self):
        t = _prim_linear(W, H, axis="diagonal")
        _field_ok(t)
        assert t[0, 0] < t[H - 1, W - 1]

    def test_axis_diagonal_reverse(self):
        t = _prim_linear(W, H, axis="diagonal", reverse=True)
        _field_ok(t)
        assert t[0, 0] > t[H - 1, W - 1]

    def test_angle_45(self):
        t = _prim_linear(W, H, axis="angle", angle=45.0)
        _field_ok(t)

    def test_angle_0(self):
        t = _prim_linear(W, H, axis="angle", angle=0.0)
        _field_ok(t)

    def test_different_axes_differ(self):
        ty = _prim_linear(W, H, axis="y")
        tx = _prim_linear(W, H, axis="x")
        assert not np.allclose(ty, tx)


class TestSpotFieldPrimitive:
    def test_single_center(self):
        t = _prim_spot_field(W, H, positions=[[0.5, 0.5]])
        _field_ok(t)
        assert t[H // 2, W // 2] < t[0, 0]

    def test_single_corner(self):
        t = _prim_spot_field(W, H, positions=[[0.0, 0.0]])
        _field_ok(t)
        assert t[0, 0] < t[H - 1, W - 1]

    def test_dual_spot(self):
        t = _prim_spot_field(W, H, positions=[[0.25, 0.25], [0.75, 0.75]])
        _field_ok(t)

    def test_triple_spot(self):
        t = _prim_spot_field(W, H, positions=[[0.3, 0.6], [0.7, 0.4], [0.5, 0.2]])
        _field_ok(t)

    def test_many_spots(self):
        positions = [[i / 8, (i * 3 % 8) / 8] for i in range(8)]
        t = _prim_spot_field(W, H, positions=positions)
        _field_ok(t)

    def test_blend_nearest(self):
        t = _prim_spot_field(W, H, positions=[[0.25, 0.25], [0.75, 0.75]], blend="nearest")
        _field_ok(t)

    def test_blend_additive(self):
        t = _prim_spot_field(W, H, positions=[[0.25, 0.25], [0.75, 0.75]], blend="additive")
        _field_ok(t)

    def test_blend_max(self):
        t = _prim_spot_field(W, H, positions=[[0.25, 0.25], [0.75, 0.75]], blend="max")
        _field_ok(t)

    def test_blend_modes_differ(self):
        tn = _prim_spot_field(W, H, positions=[[0.25, 0.25], [0.75, 0.75]], blend="nearest")
        ta = _prim_spot_field(W, H, positions=[[0.25, 0.25], [0.75, 0.75]], blend="additive")
        assert not np.allclose(tn, ta)

    def test_softness(self):
        t1 = _prim_spot_field(W, H, positions=[[0.5, 0.5]], softness=1.0)
        t2 = _prim_spot_field(W, H, positions=[[0.5, 0.5]], softness=2.0)
        _field_ok(t1)
        _field_ok(t2)
        assert not np.allclose(t1, t2)

    def test_radius_scale(self):
        t1 = _prim_spot_field(W, H, positions=[[0.5, 0.5]], radius_scale=1.0)
        t2 = _prim_spot_field(W, H, positions=[[0.5, 0.5]], radius_scale=4.0)
        _field_ok(t1)
        _field_ok(t2)
        assert not np.allclose(t1, t2)

    def test_empty_positions_defaults_center(self):
        t = _prim_spot_field(W, H, positions=[])
        _field_ok(t)

    def test_single_spot_matches_radial_center(self):
        t_old = _prim_spot_field(W, H, positions=[[0.5, 0.5]])
        assert t_old[H // 2, W // 2] < t_old[0, 0]


class TestConicPrimitive:
    def test_default(self):
        t = _prim_conic(W, H)
        _field_ok(t)

    def test_phase(self):
        t0 = _prim_conic(W, H, phase=0.0)
        t1 = _prim_conic(W, H, phase=1.0)
        _field_ok(t0)
        _field_ok(t1)
        assert not np.allclose(t0, t1)

    def test_frequency_1(self):
        t = _prim_conic(W, H, frequency=1.0)
        _field_ok(t)

    def test_frequency_3(self):
        t = _prim_conic(W, H, frequency=3.0)
        _field_ok(t)
        t1 = _prim_conic(W, H, frequency=1.0)
        assert not np.allclose(t, t1)

    def test_center_offset(self):
        t_center = _prim_conic(W, H, center=[0.5, 0.5])
        t_off = _prim_conic(W, H, center=[0.25, 0.25])
        _field_ok(t_center)
        _field_ok(t_off)
        assert not np.allclose(t_center, t_off)

    def test_reverse(self):
        t_fwd = _prim_conic(W, H, reverse=False)
        t_rev = _prim_conic(W, H, reverse=True)
        _field_ok(t_fwd)
        _field_ok(t_rev)
        assert not np.allclose(t_fwd, t_rev)


class TestSpiralPrimitive:
    def test_default(self):
        t = _prim_spiral(W, H)
        _field_ok(t)

    def test_tightness_loose(self):
        t = _prim_spiral(W, H, tightness=0.2)
        _field_ok(t)

    def test_tightness_tight(self):
        t = _prim_spiral(W, H, tightness=2.0)
        _field_ok(t)

    def test_tightness_changes_output(self):
        t1 = _prim_spiral(W, H, tightness=0.2)
        t2 = _prim_spiral(W, H, tightness=2.0)
        assert not np.allclose(t1, t2)

    def test_phase(self):
        t0 = _prim_spiral(W, H, phase=0.0)
        t1 = _prim_spiral(W, H, phase=0.5)
        _field_ok(t0)
        _field_ok(t1)
        assert not np.allclose(t0, t1)

    def test_center(self):
        t = _prim_spiral(W, H, center=[0.25, 0.75])
        _field_ok(t)

    def test_radial_weight(self):
        t1 = _prim_spiral(W, H, radial_weight=0.5)
        t2 = _prim_spiral(W, H, radial_weight=2.0)
        _field_ok(t1)
        _field_ok(t2)
        assert not np.allclose(t1, t2)


class TestCrossPrimitive:
    def test_default(self):
        t = _prim_cross(W, H)
        _field_ok(t)

    def test_thin(self):
        t = _prim_cross(W, H, thickness=0.5)
        _field_ok(t)

    def test_thick(self):
        t = _prim_cross(W, H, thickness=3.0)
        _field_ok(t)

    def test_thickness_changes_output(self):
        t1 = _prim_cross(W, H, thickness=0.5)
        t2 = _prim_cross(W, H, thickness=3.0)
        assert not np.allclose(t1, t2)

    def test_softness(self):
        t = _prim_cross(W, H, softness=0.5)
        _field_ok(t)

    def test_center(self):
        t = _prim_cross(W, H, center=[0.3, 0.7])
        _field_ok(t)


class TestDiamondPrimitive:
    def test_default(self):
        t = _prim_diamond(W, H)
        _field_ok(t)
        assert t[H // 2, W // 2] < t[0, 0]

    def test_scale_small(self):
        t = _prim_diamond(W, H, scale=0.5)
        _field_ok(t)

    def test_scale_large(self):
        t = _prim_diamond(W, H, scale=2.0)
        _field_ok(t)

    def test_scale_changes_output(self):
        t1 = _prim_diamond(W, H, scale=0.5)
        t2 = _prim_diamond(W, H, scale=2.0)
        assert not np.allclose(t1, t2)

    def test_center(self):
        t = _prim_diamond(W, H, center=[0.3, 0.7])
        _field_ok(t)


class TestBandsPrimitive:
    def test_default_y(self):
        t = _prim_bands(W, H)
        _field_ok(t)

    def test_axis_x(self):
        t = _prim_bands(W, H, axis="x")
        _field_ok(t)

    def test_frequency(self):
        t = _prim_bands(W, H, frequency=5.0)
        _field_ok(t)

    def test_wave_false(self):
        t = _prim_bands(W, H, wave=False)
        _field_ok(t)

    def test_wave_true(self):
        t = _prim_bands(W, H, wave=True)
        _field_ok(t)

    def test_wave_changes_output(self):
        t_plain = _prim_bands(W, H, wave=False)
        t_wavy = _prim_bands(W, H, wave=True)
        assert not np.allclose(t_plain, t_wavy)


class TestRingsPrimitive:
    def test_default(self):
        t = _prim_rings(W, H)
        _field_ok(t)

    def test_frequency_low(self):
        t = _prim_rings(W, H, frequency=2.0)
        _field_ok(t)

    def test_frequency_high(self):
        t = _prim_rings(W, H, frequency=10.0)
        _field_ok(t)

    def test_frequency_changes_output(self):
        t1 = _prim_rings(W, H, frequency=2.0)
        t2 = _prim_rings(W, H, frequency=10.0)
        assert not np.allclose(t1, t2)

    def test_phase(self):
        t = _prim_rings(W, H, phase=1.0)
        _field_ok(t)

    def test_center(self):
        t = _prim_rings(W, H, center=[0.25, 0.75])
        _field_ok(t)

    def test_contrast(self):
        t1 = _prim_rings(W, H, contrast=0.5)
        t2 = _prim_rings(W, H, contrast=1.0)
        _field_ok(t1)
        _field_ok(t2)
        assert not np.allclose(t1, t2)

    def test_radial_scale(self):
        t = _prim_rings(W, H, radial_scale=2.0)
        _field_ok(t)


class TestGridPrimitive:
    def test_default(self):
        t = _prim_grid(W, H)
        _field_ok(t)

    def test_shape_diamond(self):
        t = _prim_grid(W, H, shape="diamond")
        _field_ok(t)

    def test_shape_checker(self):
        t = _prim_grid(W, H, shape="checker")
        _field_ok(t)

    def test_shape_dots(self):
        t = _prim_grid(W, H, shape="dots")
        _field_ok(t)

    def test_shapes_differ(self):
        td = _prim_grid(W, H, shape="diamond")
        tc = _prim_grid(W, H, shape="checker")
        tt = _prim_grid(W, H, shape="dots")
        assert not np.allclose(td, tc)
        assert not np.allclose(td, tt)
        assert not np.allclose(tc, tt)

    def test_frequency(self):
        t1 = _prim_grid(W, H, freq_x=3, freq_y=3)
        t2 = _prim_grid(W, H, freq_x=10, freq_y=10)
        _field_ok(t1)
        _field_ok(t2)
        assert not np.allclose(t1, t2)

    def test_phase(self):
        t = _prim_grid(W, H, phase_x=1.0, phase_y=0.5)
        _field_ok(t)

    def test_contrast(self):
        t = _prim_grid(W, H, contrast=0.5)
        _field_ok(t)


class TestScatterFieldPrimitive:
    def test_default(self):
        t = _prim_scatter_field(W, H)
        _field_ok(t)

    def test_deterministic_same_seed(self):
        t1 = _prim_scatter_field(W, H, seed=42)
        t2 = _prim_scatter_field(W, H, seed=42)
        assert np.allclose(t1, t2)

    def test_different_seed_different_output(self):
        t1 = _prim_scatter_field(W, H, seed=42)
        t2 = _prim_scatter_field(W, H, seed=99)
        assert not np.allclose(t1, t2)

    def test_shape_dot(self):
        t = _prim_scatter_field(W, H, shape="dot")
        _field_ok(t)

    def test_shape_diamond(self):
        t = _prim_scatter_field(W, H, shape="diamond")
        _field_ok(t)

    def test_shape_ring(self):
        t = _prim_scatter_field(W, H, shape="ring")
        _field_ok(t)

    def test_count(self):
        t = _prim_scatter_field(W, H, count=5)
        _field_ok(t)

    def test_count_large(self):
        t = _prim_scatter_field(W, H, count=50)
        _field_ok(t)

    def test_count_capped(self):
        t = _prim_scatter_field(W, H, count=MAX_SCATTER_COUNT + 100)
        _field_ok(t)

    def test_size_jitter(self):
        t = _prim_scatter_field(W, H, size_jitter=0.5)
        _field_ok(t)

    def test_blend_additive(self):
        t = _prim_scatter_field(W, H, blend="additive")
        _field_ok(t)


class TestBurstPrimitive:
    def test_default(self):
        t = _prim_burst(W, H)
        _field_ok(t)

    def test_ray_count_4(self):
        t = _prim_burst(W, H, ray_count=4)
        _field_ok(t)

    def test_ray_count_16(self):
        t = _prim_burst(W, H, ray_count=16)
        _field_ok(t)

    def test_ray_count_changes_output(self):
        t1 = _prim_burst(W, H, ray_count=4)
        t2 = _prim_burst(W, H, ray_count=16)
        assert not np.allclose(t1, t2)

    def test_phase(self):
        t = _prim_burst(W, H, phase=1.0)
        _field_ok(t)

    def test_sharpness_low(self):
        t = _prim_burst(W, H, sharpness=0.1)
        _field_ok(t)

    def test_sharpness_high(self):
        t = _prim_burst(W, H, sharpness=2.0)
        _field_ok(t)

    def test_sharpness_changes_output(self):
        t1 = _prim_burst(W, H, sharpness=0.1)
        t2 = _prim_burst(W, H, sharpness=2.0)
        assert not np.allclose(t1, t2)

    def test_radial_falloff(self):
        t1 = _prim_burst(W, H, radial_falloff=0.5)
        t2 = _prim_burst(W, H, radial_falloff=2.0)
        _field_ok(t1)
        _field_ok(t2)
        assert not np.allclose(t1, t2)

    def test_center(self):
        t = _prim_burst(W, H, center=[0.25, 0.75])
        _field_ok(t)

    def test_min_ray_count(self):
        t = _prim_burst(W, H, ray_count=1)
        _field_ok(t)


# ===================================================================
# Color mapping
# ===================================================================

class TestApplyColorMap:
    def test_two_colors(self):
        rgb_arr = np.array([[0, 0, 0], [255, 255, 255]], dtype=np.float32)
        t = np.linspace(0, 1, 64 * 64, dtype=np.float32).reshape(64, 64)
        arr = apply_color_map(t, rgb_arr)
        assert arr.shape == (64, 64, 3)
        assert arr.dtype == np.uint8

    def test_single_color(self):
        rgb_arr = np.array([[128, 64, 32]], dtype=np.float32)
        t = np.ones((10, 10), dtype=np.float32) * 0.5
        arr = apply_color_map(t, rgb_arr)
        assert arr.shape == (10, 10, 3)
        assert np.all(arr[:, :, 0] == 128)
        assert np.all(arr[:, :, 1] == 64)
        assert np.all(arr[:, :, 2] == 32)

    def test_three_colors(self):
        rgb_arr = np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255]], dtype=np.float32)
        t = np.zeros((10, 10), dtype=np.float32)
        arr = apply_color_map(t, rgb_arr)
        assert np.all(arr[:, :, 0] == 255)
        assert np.all(arr[:, :, 1] == 0)

    def test_clamps(self):
        rgb_arr = np.array([[0, 0, 0], [255, 255, 255]], dtype=np.float32)
        t = np.full((5, 5), 2.0, dtype=np.float32)
        arr = apply_color_map(t, rgb_arr)
        assert arr.dtype == np.uint8
        assert np.all(arr[:, :, 0] == 255)


# ===================================================================
# Parser — backward compat
# ===================================================================

class TestParserLinearAliases:
    def test_vertical_top_bottom(self):
        prim, params = parse_direction("vertical_top_bottom")
        assert prim == "linear"
        assert params == {"axis": "y", "reverse": False}

    def test_vertical_bottom_top(self):
        prim, params = parse_direction("vertical_bottom_top")
        assert prim == "linear"
        assert params == {"axis": "y", "reverse": True}

    def test_horizontal_left_right(self):
        prim, params = parse_direction("horizontal_left_right")
        assert prim == "linear"
        assert params == {"axis": "x", "reverse": False}

    def test_horizontal_right_left(self):
        prim, params = parse_direction("horizontal_right_left")
        assert prim == "linear"
        assert params == {"axis": "x", "reverse": True}

    def test_diagonal_tl_br(self):
        prim, params = parse_direction("diagonal_tl_br")
        assert prim == "linear"
        assert params == {"axis": "diagonal", "reverse": False}

    def test_diagonal_tr_bl(self):
        prim, params = parse_direction("diagonal_tr_bl")
        assert prim == "linear"
        assert params == {"axis": "diagonal", "reverse": True}

    def test_angle_45(self):
        prim, params = parse_direction("angle_45")
        assert prim == "linear"
        assert params == {"axis": "angle", "angle": 45.0}

    def test_angle_no_value_raises(self):
        with pytest.raises(ValueError):
            parse_direction("angle_")


class TestParserRadialAliases:
    def test_radial_center(self):
        prim, params = parse_direction("radial_center")
        assert prim == "spot_field"
        assert params == {"positions": [[0.5, 0.5]]}

    def test_radial_top(self):
        prim, params = parse_direction("radial_top")
        assert prim == "spot_field"
        assert params == {"positions": [[0.5, 0.0]]}

    def test_radial_bottom(self):
        prim, params = parse_direction("radial_bottom")
        assert prim == "spot_field"
        assert params == {"positions": [[0.5, 1.0]]}

    def test_radial_tl(self):
        prim, params = parse_direction("radial_tl")
        assert prim == "spot_field"
        assert params == {"positions": [[0.0, 0.0]]}

    def test_radial_br(self):
        prim, params = parse_direction("radial_br")
        assert prim == "spot_field"
        assert params == {"positions": [[1.0, 1.0]]}


class TestParserConicAliases:
    def test_conic_bare(self):
        prim, params = parse_direction("conic")
        assert prim == "conic"
        assert params == {"phase": 0.0}

    def test_conic_with_phase(self):
        prim, params = parse_direction("conic_0.5")
        assert prim == "conic"
        assert params == {"phase": 0.5}

    def test_conic_center_with_phase(self):
        prim, params = parse_direction("conic_center_1.5")
        assert prim == "conic"
        assert params == {"phase": 1.5}

    def test_conic_0_8(self):
        prim, params = parse_direction("conic_0.8")
        assert prim == "conic"
        assert params == {"phase": 0.8}


class TestParserDualSpotAliases:
    def test_dual_spot_bare(self):
        prim, params = parse_direction("dual_spot")
        assert prim == "spot_field"
        assert params == {"positions": [[0.25, 0.25], [0.75, 0.75]]}

    def test_dual_spot_custom(self):
        prim, params = parse_direction("dual_spot_0.3_0.6_0.7_0.4")
        assert prim == "spot_field"
        assert params == {"positions": [[0.3, 0.6], [0.7, 0.4]]}


class TestParserOtherAliases:
    def test_spiral(self):
        prim, params = parse_direction("spiral")
        assert prim == "spiral"
        assert params == {}

    def test_cross(self):
        prim, params = parse_direction("cross")
        assert prim == "cross"
        assert params == {}

    def test_diamond(self):
        prim, params = parse_direction("diamond")
        assert prim == "diamond"
        assert params == {}

    def test_bands(self):
        prim, params = parse_direction("bands")
        assert prim == "bands"
        assert params == {}


class TestParserNewPrimitives:
    def test_rings_bare(self):
        prim, params = parse_direction("rings")
        assert prim == "rings"
        assert params == {"frequency": 5.0}

    def test_rings_with_freq(self):
        prim, params = parse_direction("rings_8")
        assert prim == "rings"
        assert params == {"frequency": 8.0}

    def test_grid_bare(self):
        prim, params = parse_direction("grid")
        assert prim == "grid"
        assert params == {"freq_x": 5.0, "freq_y": 5.0}

    def test_grid_with_freq(self):
        prim, params = parse_direction("grid_10")
        assert prim == "grid"
        assert params == {"freq_x": 10.0, "freq_y": 10.0}

    def test_scatter_field(self):
        prim, params = parse_direction("scatter_field")
        assert prim == "scatter_field"
        assert params == {}

    def test_burst_bare(self):
        prim, params = parse_direction("burst")
        assert prim == "burst"
        assert params == {"ray_count": 8}

    def test_burst_with_count(self):
        prim, params = parse_direction("burst_12")
        assert prim == "burst"
        assert params == {"ray_count": 12}


class TestParserUnknown:
    def test_unknown_falls_to_spot_field_center(self):
        prim, params = parse_direction("totally_unknown")
        assert prim == "spot_field"
        assert params == {"positions": [[0.5, 0.5]]}

    def test_empty_string(self):
        prim, params = parse_direction("")
        assert prim == "spot_field"
        assert params == {"positions": [[0.5, 0.5]]}


# ===================================================================
# resolve_gradient — parameter merging
# ===================================================================

class TestResolveGradient:
    def test_no_dict(self):
        prim, params = resolve_gradient("spiral")
        assert prim == "spiral"
        assert params == {}

    def test_dict_overrides(self):
        prim, params = resolve_gradient("spiral", {"tightness": 2.0, "phase": 0.5})
        assert prim == "spiral"
        assert params["tightness"] == 2.0
        assert params["phase"] == 0.5

    def test_dict_adds_params(self):
        prim, params = resolve_gradient("conic_0.5", {"frequency": 3.0})
        assert prim == "conic"
        assert params["phase"] == 0.5
        assert params["frequency"] == 3.0

    def test_dict_wins_over_string(self):
        prim, params = resolve_gradient("dual_spot_0.3_0.6_0.7_0.4", {"blend": "additive"})
        assert prim == "spot_field"
        assert params["positions"] == [[0.3, 0.6], [0.7, 0.4]]
        assert params["blend"] == "additive"


# ===================================================================
# Recipes
# ===================================================================

class TestRecipes:
    def test_diamond_field_recipe(self):
        prim, params = parse_direction("diamond_field")
        assert prim == "grid"
        assert params["shape"] == "diamond"
        assert params["freq_x"] == 8
        assert params["freq_y"] == 8

    def test_expanding_ring_recipe(self):
        prim, params = parse_direction("expanding_ring")
        assert prim == "rings"
        assert params["frequency"] == 5
        assert params["contrast"] == 0.8

    def test_conic_burst_recipe(self):
        prim, params = parse_direction("conic_burst")
        assert prim == "burst"
        assert params["ray_count"] == 12
        assert params["sharpness"] == 0.7

    def test_playful_scatter_recipe(self):
        prim, params = parse_direction("playful_scatter")
        assert prim == "scatter_field"
        assert params["count"] == 30
        assert params["shape"] == "diamond"

    def test_recipe_params_overridden_by_dict(self):
        prim, params = resolve_gradient("diamond_field", {"freq_x": 12, "shape": "checker"})
        assert prim == "grid"
        assert params["freq_x"] == 12
        assert params["shape"] == "checker"
        assert params["freq_y"] == 8


# ===================================================================
# compute_field and resolve_and_compute
# ===================================================================

class TestComputeField:
    def test_unknown_primitive_raises(self):
        with pytest.raises(ValueError, match="Unknown gradient primitive"):
            compute_field(W, H, "nonexistent_primitive", {})

    def test_all_primitives_run(self):
        for name in PRIMITIVES:
            params = {}
            if name == "linear":
                params = {"axis": "y"}
            elif name == "spot_field":
                params = {"positions": [[0.5, 0.5]]}
            elif name == "bands":
                params = {"axis": "y"}
            t = compute_field(W, H, name, params)
            _field_ok(t)


class TestResolveAndCompute:
    def test_basic(self):
        t = resolve_and_compute("radial_center", W, H)
        _field_ok(t)

    def test_with_params(self):
        t = resolve_and_compute("conic", W, H, {"phase": 0.5, "frequency": 3.0})
        _field_ok(t)

    def test_recipe(self):
        t = resolve_and_compute("diamond_field", W, H)
        _field_ok(t)
