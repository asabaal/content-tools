from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from render.readability import (
    _srgb_to_linear,
    relative_luminance,
    contrast_ratio,
    wcag_level,
    estimate_busyness,
    check_readability,
    recommend_preset_for_visual,
    ReadabilityReport,
)


class TestSrgbToLinear:
    def test_zero(self):
        assert _srgb_to_linear(0) == 0.0

    def test_max(self):
        assert _srgb_to_linear(255) == pytest.approx(1.0, abs=0.01)

    def test_mid(self):
        val = _srgb_to_linear(128)
        assert 0.2 < val < 0.3

    def test_low_linear(self):
        assert _srgb_to_linear(10) == pytest.approx(10 / 255 / 12.92, abs=1e-6)

    def test_high_curve(self):
        assert _srgb_to_linear(200) > 0.5


class TestRelativeLuminance:
    def test_black(self):
        assert relative_luminance("#000000") == pytest.approx(0.0, abs=0.001)

    def test_white(self):
        assert relative_luminance("#ffffff") == pytest.approx(1.0, abs=0.001)

    def test_red(self):
        lum = relative_luminance("#ff0000")
        assert 0.2 < lum < 0.3

    def test_green_dominant(self):
        lum = relative_luminance("#00ff00")
        assert 0.6 < lum < 0.8

    def test_blue_low(self):
        lum = relative_luminance("#0000ff")
        assert 0.0 < lum < 0.2

    def test_invalid_length(self):
        with pytest.raises(ValueError):
            relative_luminance("#fff")

    def test_invalid_length_8(self):
        with pytest.raises(ValueError):
            relative_luminance("#fffffff")

    def test_gray_mid(self):
        lum = relative_luminance("#808080")
        assert 0.1 < lum < 0.5

    def test_dark_purple(self):
        lum = relative_luminance("#1a1a2e")
        assert 0.0 < lum < 0.1


class TestContrastRatio:
    def test_black_white(self):
        r = contrast_ratio("#000000", "#ffffff")
        assert r == pytest.approx(21.0, abs=0.1)

    def test_same_color(self):
        r = contrast_ratio("#ff0000", "#ff0000")
        assert r == pytest.approx(1.0, abs=0.01)

    def test_similar_colors(self):
        r = contrast_ratio("#1a1a1a", "#1a1a2e")
        assert r < 1.5

    def test_high_contrast(self):
        r = contrast_ratio("#000000", "#ffff00")
        assert r > 10.0

    def test_dark_vs_dark(self):
        r = contrast_ratio("#0a0a0a", "#111111")
        assert r < 2.0


class TestWcagLevel:
    def test_aaa_normal(self):
        assert wcag_level(7.0) == "AAA"

    def test_aa_normal(self):
        assert wcag_level(4.5) == "AA"

    def test_fail_normal(self):
        assert wcag_level(3.0) == "fail"

    def test_aaa_large(self):
        assert wcag_level(4.5, large_text=True) == "AAA"

    def test_aa_large(self):
        assert wcag_level(3.0, large_text=True) == "AA"

    def test_fail_large(self):
        assert wcag_level(2.0, large_text=True) == "fail"

    def test_very_high(self):
        assert wcag_level(15.0) == "AAA"

    def test_borderline_aa(self):
        assert wcag_level(4.6) == "AA"


class TestEstimateBusyness:
    def test_empty_visual(self):
        assert estimate_busyness({}) == "low"

    def test_simple_gradient(self):
        assert estimate_busyness({"gradient_direction": "vertical"}) == "low"

    def test_conic_medium(self):
        assert estimate_busyness({"gradient_direction": "conic"}) == "medium"

    def test_spiral_medium(self):
        assert estimate_busyness({"gradient_direction": "spiral"}) == "medium"

    def test_rings_medium(self):
        assert estimate_busyness({"gradient_direction": "rings"}) == "medium"

    def test_diamond_medium(self):
        assert estimate_busyness({"gradient_direction": "diamond"}) == "medium"

    def test_bands_medium(self):
        assert estimate_busyness({"gradient_direction": "bands"}) == "medium"

    def test_grid_medium(self):
        assert estimate_busyness({"gradient_direction": "grid"}) == "medium"

    def test_burst_medium(self):
        assert estimate_busyness({"gradient_direction": "burst"}) == "medium"

    def test_scatter_medium(self):
        assert estimate_busyness({"gradient_direction": "scatter_field"}) == "medium"

    def test_spot_field_low(self):
        assert estimate_busyness({"gradient_direction": "spot_field"}) == "low"

    def test_dual_spot_low(self):
        assert estimate_busyness({"gradient_direction": "dual_spot"}) == "low"

    def test_radial_center_low(self):
        assert estimate_busyness({"gradient_direction": "radial_center"}) == "low"

    def test_high_frequency(self):
        vis = {"gradient_direction": "vertical", "gradient_params": {"frequency": 7}}
        assert estimate_busyness(vis) == "low"

    def test_very_high_frequency(self):
        vis = {"gradient_direction": "conic", "gradient_params": {"frequency": 10}}
        assert estimate_busyness(vis) == "medium"

    def test_medium_frequency(self):
        vis = {"gradient_direction": "vertical", "gradient_params": {"frequency": 4}}
        assert estimate_busyness(vis) == "low"

    def test_texture_grain(self):
        vis = {"texture_type": "noise_grain"}
        assert estimate_busyness(vis) == "low"

    def test_texture_grain_conic(self):
        vis = {"texture_type": "noise_grain", "gradient_direction": "conic"}
        assert estimate_busyness(vis) == "medium"

    def test_texture_opacity(self):
        vis = {"texture_opacity": 0.3}
        assert estimate_busyness(vis) == "low"

    def test_many_colors(self):
        vis = {"gradient_colors": ["#ff0000", "#00ff00", "#0000ff", "#ffff00"]}
        assert estimate_busyness(vis) == "low"

    def test_many_colors_conic(self):
        vis = {"gradient_colors": ["#ff0000", "#00ff00", "#0000ff", "#ffff00"], "gradient_direction": "conic"}
        assert estimate_busyness(vis) == "medium"

    def test_energetic_preset(self):
        vis = {"bg_animation_preset": "energetic"}
        assert estimate_busyness(vis) == "low"

    def test_psychedelic_preset(self):
        vis = {"bg_animation_preset": "psychedelic", "gradient_direction": "conic"}
        assert estimate_busyness(vis) == "medium"

    def test_intense_preset(self):
        vis = {"bg_animation_preset": "intense"}
        assert estimate_busyness(vis) == "low"

    def test_freq_x_param(self):
        vis = {"gradient_params": {"freq_x": 7}}
        assert estimate_busyness(vis) == "low"

    def test_conic_with_frequency(self):
        vis = {"gradient_direction": "conic", "gradient_params": {"frequency": 5}}
        assert estimate_busyness(vis) == "medium"

    def test_conic_high_freq_texture(self):
        vis = {
            "gradient_direction": "conic",
            "gradient_params": {"frequency": 10},
            "texture_type": "noise_grain",
            "texture_opacity": 0.3,
            "gradient_colors": ["#ff0000", "#00ff00", "#0000ff", "#ffff00"],
        }
        assert estimate_busyness(vis) == "high"

    def test_combined_high(self):
        vis = {
            "gradient_direction": "conic",
            "bg_animation_preset": "energetic",
            "gradient_params": {"frequency": 7},
        }
        assert estimate_busyness(vis) == "high"


class TestCheckReadability:
    def test_good_contrast_white_on_dark(self):
        report = check_readability("#ffffff", {"background_color": "#000000"})
        assert report.contrast_ratio > 10.0
        assert report.contrast_status == "pass"
        assert report.readability_score > 60

    def test_bad_contrast_dark_on_dark(self):
        report = check_readability("#1a1a2e", {"background_color": "#1a1a2e"})
        assert report.contrast_ratio < 2.0
        assert report.contrast_status == "fail"
        assert len(report.issues) > 0

    def test_moderate_contrast(self):
        report = check_readability("#888888", {"background_color": "#000000"})
        assert report.contrast_ratio > 3.0
        assert report.readability_score > 0

    def test_with_backdrop_clean_bg(self):
        report = check_readability(
            "#ffffff",
            {"background_color": "#000000"},
            has_backdrop=True,
            backdrop_config={"color": "#000000", "opacity": 0.5},
        )
        assert report.readability_score > 0
        assert len(report.recommendations) > 0

    def test_with_backdrop_busy_bg(self):
        report = check_readability(
            "#ffffff",
            {"background_color": "#1a1a2e", "gradient_direction": "conic"},
            has_backdrop=True,
            backdrop_config={"color": "#000000", "opacity": 0.5},
        )
        assert report.readability_score > 0

    def test_no_backdrop_busy_bg(self):
        vis = {
            "background_color": "#1a1a2e",
            "gradient_direction": "conic",
            "gradient_colors": ["#ff0000", "#00ff00", "#0000ff", "#ffff00"],
            "gradient_params": {"frequency": 10},
            "texture_type": "noise_grain",
            "texture_opacity": 0.3,
        }
        report = check_readability("#ffffff", vis, has_backdrop=False)
        assert report.text_box_recommendation == "use"
        assert any("backdrop" in r.lower() or "text box" in r.lower() for r in report.recommendations)

    def test_no_backdrop_medium_bg(self):
        report = check_readability(
            "#ffffff",
            {"background_color": "#1a1a2e", "gradient_direction": "conic"},
            has_backdrop=False,
        )
        assert report.text_box_recommendation == "optional"

    def test_large_text_relaxed(self):
        report = check_readability("#888888", {"background_color": "#000000"}, text_size=72)
        assert report.readability_score > 0

    def test_small_text_strict(self):
        report = check_readability("#888888", {"background_color": "#000000"}, text_size=50)
        assert report.readability_score > 0

    def test_recommended_text_color(self):
        report = check_readability("#1a1a2e", {"background_color": "#1a1a2e"})
        assert report.recommended_text_color is not None

    def test_recommended_text_box_needed(self):
        vis = {
            "background_color": "#1a1a2e",
            "gradient_direction": "conic",
            "gradient_params": {"frequency": 10},
            "texture_type": "noise_grain",
            "texture_opacity": 0.3,
            "gradient_colors": ["#ff0000", "#00ff00", "#0000ff", "#ffff00"],
        }
        report = check_readability("#ffffff", vis, has_backdrop=False)
        assert report.recommended_text_box is not None
        assert report.recommended_text_box["enabled"] is True

    def test_recommended_text_box_unneeded(self):
        report = check_readability(
            "#ffffff",
            {"background_color": "#000000"},
            has_backdrop=True,
            backdrop_config={"color": "#000000", "opacity": 0.5},
        )
        if report.recommended_text_box:
            assert report.recommended_text_box["enabled"] is False

    def test_asdict(self):
        report = check_readability("#ffffff", {"background_color": "#000000"})
        d = report.asdict()
        assert "readability_score" in d
        assert "contrast_ratio" in d
        assert "issues" in d
        assert isinstance(d["issues"], list)

    def test_scores_bounded(self):
        report = check_readability("#ffffff", {"background_color": "#000000"})
        assert 0 <= report.readability_score <= 100
        assert 0 <= report.aesthetic_score <= 100

    def test_non_pure_color_recommendation(self):
        report = check_readability("#555555", {"background_color": "#333333"})
        assert report.contrast_ratio < 3.0
        assert report.recommended_text_color is not None

    def test_high_contrast_no_issues(self):
        report = check_readability("#ffffff", {"background_color": "#000000"})
        assert len(report.issues) == 0

    def test_asdict_rounding(self):
        report = check_readability("#ffffff", {"background_color": "#000000"})
        d = report.asdict()
        assert isinstance(d["readability_score"], float)
        assert isinstance(d["contrast_ratio"], float)


class TestRecommendPresetForVisual:
    def test_returns_string_or_none(self):
        result = recommend_preset_for_visual({"background_color": "#1a1a2e"})
        assert result is None or isinstance(result, str)

    def test_dark_bg(self):
        result = recommend_preset_for_visual({"background_color": "#0a0a0a"})
        assert result is not None

    def test_bright_bg(self):
        result = recommend_preset_for_visual({"background_color": "#f0f0f0"})
        assert result is None or isinstance(result, str)

    def test_with_gradient_colors(self):
        result = recommend_preset_for_visual({
            "background_color": "#1a1a2e",
            "gradient_colors": ["#ff6b6b", "#4cc9f0"],
        })
        assert result is None or isinstance(result, str)

    def test_busy_background(self):
        result = recommend_preset_for_visual({
            "background_color": "#1a1a2e",
            "gradient_direction": "conic",
            "gradient_colors": ["#ff0000", "#00ff00", "#0000ff", "#ffff00"],
        })
        assert result is None or isinstance(result, str)

    def test_invalid_color(self):
        result = recommend_preset_for_visual({"background_color": "not_a_color"})
        assert result is None


class TestReadabilityReport:
    def test_default_lists(self):
        report = ReadabilityReport(
            readability_score=50.0,
            aesthetic_score=50.0,
            contrast_status="pass",
            contrast_ratio=7.0,
            background_busyness="low",
            text_box_recommendation="avoid",
            recommended_text_color=None,
            recommended_text_box=None,
            recommended_color_preset=None,
        )
        assert report.issues == []
        assert report.recommendations == []

    def test_custom_issues(self):
        report = ReadabilityReport(
            readability_score=10.0,
            aesthetic_score=10.0,
            contrast_status="fail",
            contrast_ratio=1.5,
            background_busyness="high",
            text_box_recommendation="use",
            recommended_text_color="#ffffff",
            recommended_text_box={"enabled": True},
            recommended_color_preset=None,
            issues=["low contrast"],
            recommendations=["use backdrop"],
        )
        assert len(report.issues) == 1
        assert len(report.recommendations) == 1
