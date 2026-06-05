from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from render.aspect_transform import (
    ASPECT_16_9,
    ASPECT_9_16,
    CANVAS_SIZES,
    SAFE_ZONES,
    check_layout_issues,
    detect_aspect_ratio,
    find_asset_variant,
    transform_script,
    _adjust_dual_spot,
    _adjust_y,
    _effective_font_size,
    _image_aspect_label,
    _is_horizontal_image,
    _is_vertical_image,
    _scale_font_delta,
    _scale_font_size,
)


def _make_sample_script():
    return {
        "name": "Test Song",
        "defaults": {
            "background_type": "gradient",
            "background_color": "#1a1a2e",
            "font_size": 146,
            "animation_type": "fade",
            "reveal_mode": "progressive",
            "text_align": "center",
        },
        "caption_style": {
            "font_family": 0,
            "highlight_color": "#FF8C00",
            "text_position": "center",
        },
        "sections": [
            {
                "name": "intro section",
                "type": "spoken_prophetic_opening",
                "lines": [0, 1],
                "visual": {
                    "font_size": 94,
                    "text_position": "top",
                    "gradient_direction": "dual_spot_0.3_0.4_0.7_0.6",
                    "bg_animation_preset": "smooth",
                },
                "lines_overrides": {
                    "0": {"font_size": 94},
                    "1": {"font_size": 96},
                },
                "words_overrides": {
                    "0.0": {"y": 0.2},
                    "0.1": {"y": 0.2},
                    "0.2": {"y": 0.8},
                    "1.0": {"y": 0.5},
                },
            },
            {
                "name": "verse section",
                "type": "melodic_testimony_verse",
                "lines": [2, 3, 4, 5],
                "visual": {
                    "font_size": 100,
                    "text_position": "center",
                    "gradient_direction": "cross",
                    "bg_animation_preset": "dreamy",
                },
                "lines_overrides": {
                    "2": {"font_size": 94},
                    "3": {"font_size": 98},
                    "4": {"font_size": 100},
                    "5": {"font_size": 104},
                },
                "words_overrides": {
                    "2.0": {"y": 0.2, "font_size_delta": 0},
                    "2.1": {"y": 0.2, "font_size_delta": 6},
                    "2.2": {"y": 0.2, "font_size_delta": 10},
                    "3.0": {"y": 0.5},
                },
            },
        ],
        "intro": {
            "image": "/fake/intro_brand.png",
            "title": "Test Song",
            "subtitle": "",
            "duration": 4.789,
        },
        "outro": {
            "image": "/fake/intro_brand.png",
            "logo": "/fake/outro_logo.png",
            "text": "Presented by",
        },
    }


class TestConstants:
    def test_valid_aspects(self):
        assert ASPECT_16_9 in {"16:9", "9:16"}
        assert ASPECT_9_16 in {"16:9", "9:16"}

    def test_canvas_sizes(self):
        assert CANVAS_SIZES[ASPECT_16_9] == (1920, 1080)
        assert CANVAS_SIZES[ASPECT_9_16] == (1080, 1920)

    def test_safe_zones(self):
        sz_169 = SAFE_ZONES[ASPECT_16_9]
        assert sz_169["top"] < sz_169["bottom"]
        sz_916 = SAFE_ZONES[ASPECT_9_16]
        assert sz_916["top"] < sz_916["bottom"]


class TestScaleFontSize:
    def test_169_to_916_reduces(self):
        result = _scale_font_size(146, ASPECT_16_9, ASPECT_9_16)
        assert result < 146
        assert result == round(146 * 1080 / 1920)

    def test_916_to_169_increases(self):
        result = _scale_font_size(82, ASPECT_9_16, ASPECT_16_9)
        assert result > 82
        assert result == round(82 * 1920 / 1080)

    def test_minimum_16(self):
        result = _scale_font_size(1, ASPECT_16_9, ASPECT_9_16)
        assert result >= 16

    def test_rounding(self):
        result = _scale_font_size(100, ASPECT_16_9, ASPECT_9_16)
        assert isinstance(result, int)


class TestScaleFontDelta:
    def test_positive_delta(self):
        result = _scale_font_delta(10, ASPECT_16_9, ASPECT_9_16)
        assert result == round(10 * 1080 / 1920)

    def test_negative_delta(self):
        result = _scale_font_delta(-5, ASPECT_16_9, ASPECT_9_16)
        assert result < 0

    def test_zero_delta(self):
        result = _scale_font_delta(0, ASPECT_16_9, ASPECT_9_16)
        assert result == 0

    def test_round_trip(self):
        original = 8
        to_916 = _scale_font_delta(original, ASPECT_16_9, ASPECT_9_16)
        back = _scale_font_delta(to_916, ASPECT_9_16, ASPECT_16_9)
        assert abs(back - original) <= 1


class TestAdjustY:
    def test_center_stays_near_center(self):
        result = _adjust_y(0.5, ASPECT_16_9, ASPECT_9_16)
        assert 0.4 < result < 0.6

    def test_169_to_916_top(self):
        result = _adjust_y(0.2, ASPECT_16_9, ASPECT_9_16)
        assert result < 0.2

    def test_169_to_916_bottom(self):
        result = _adjust_y(0.8, ASPECT_16_9, ASPECT_9_16)
        assert result > 0.8

    def test_round_trip_y(self):
        original = 0.3
        to_916 = _adjust_y(original, ASPECT_16_9, ASPECT_9_16)
        back = _adjust_y(to_916, ASPECT_9_16, ASPECT_16_9)
        assert abs(back - original) < 0.05

    def test_clamped_to_safe_zone(self):
        result = _adjust_y(0.01, ASPECT_16_9, ASPECT_9_16)
        safe = SAFE_ZONES[ASPECT_9_16]
        assert result >= safe["top"]

    def test_clamped_bottom(self):
        result = _adjust_y(0.99, ASPECT_16_9, ASPECT_9_16)
        safe = SAFE_ZONES[ASPECT_9_16]
        assert result <= safe["bottom"]


class TestAdjustDualSpot:
    def test_non_dual_spot_unchanged(self):
        assert _adjust_dual_spot("cross", ASPECT_16_9, ASPECT_9_16) == "cross"
        assert _adjust_dual_spot("radial_center", ASPECT_16_9, ASPECT_9_16) == "radial_center"

    def test_dual_spot_transformed(self):
        result = _adjust_dual_spot("dual_spot_0.3_0.4_0.7_0.6", ASPECT_16_9, ASPECT_9_16)
        assert result.startswith("dual_spot_")
        parts = result.split("_")
        assert len(parts) >= 6
        for i in range(2, 6):
            val = float(parts[i])
            assert 0.1 <= val <= 0.9

    def test_dual_spot_916_to_169(self):
        result = _adjust_dual_spot("dual_spot_0.3_0.4_0.7_0.6", ASPECT_9_16, ASPECT_16_9)
        assert result.startswith("dual_spot_")
        parts = result.split("_")
        for i in range(2, 6):
            val = float(parts[i])
            assert 0.1 <= val <= 0.9

    def test_dual_spot_same_aspect_passthrough(self):
        result = _adjust_dual_spot("dual_spot_0.3_0.4_0.7_0.6", ASPECT_16_9, ASPECT_16_9)
        parts = result.split("_")
        assert float(parts[2]) == 0.3
        assert float(parts[3]) == 0.4
        assert float(parts[4]) == 0.7
        assert float(parts[5]) == 0.6

    def test_dual_spot_too_few_parts(self):
        result = _adjust_dual_spot("dual_spot_0.3", ASPECT_16_9, ASPECT_9_16)
        assert result == "dual_spot_0.3"

    def test_dual_spot_bad_coords(self):
        result = _adjust_dual_spot("dual_spot_a_b_c_d", ASPECT_16_9, ASPECT_9_16)
        assert result == "dual_spot_a_b_c_d"

    def test_round_trip_dual_spot(self):
        original = "dual_spot_0.3_0.4_0.7_0.6"
        to_916 = _adjust_dual_spot(original, ASPECT_16_9, ASPECT_9_16)
        back = _adjust_dual_spot(to_916, ASPECT_9_16, ASPECT_16_9)
        orig_parts = [float(p) for p in original.split("_")[2:6]]
        back_parts = [float(p) for p in back.split("_")[2:6]]
        for o, b in zip(orig_parts, back_parts):
            assert abs(o - b) < 0.15


class TestImageAspectLabel:
    def test_horizontal(self, tmp_path):
        img = Image.new("RGB", (200, 100))
        p = tmp_path / "h.png"
        img.save(p)
        assert _image_aspect_label(p) == "horizontal"

    def test_vertical(self, tmp_path):
        img = Image.new("RGB", (100, 200))
        p = tmp_path / "v.png"
        img.save(p)
        assert _image_aspect_label(p) == "vertical"

    def test_square(self, tmp_path):
        img = Image.new("RGB", (100, 100))
        p = tmp_path / "s.png"
        img.save(p)
        assert _image_aspect_label(p) == "square"

    def test_nonexistent(self, tmp_path):
        assert _image_aspect_label(tmp_path / "nonexistent.png") == "unknown"

    def test_not_an_image(self, tmp_path):
        p = tmp_path / "bad.png"
        p.write_text("not an image")
        assert _image_aspect_label(p) == "unknown"


class TestIsVerticalImage:
    def test_vertical(self, tmp_path):
        p = tmp_path / "v.png"
        Image.new("RGB", (100, 200)).save(p)
        assert _is_vertical_image(p) is True

    def test_horizontal(self, tmp_path):
        p = tmp_path / "h.png"
        Image.new("RGB", (200, 100)).save(p)
        assert _is_vertical_image(p) is False

    def test_nonexistent(self, tmp_path):
        assert _is_vertical_image(tmp_path / "nope.png") is False


class TestIsHorizontalImage:
    def test_horizontal(self, tmp_path):
        p = tmp_path / "h.png"
        Image.new("RGB", (200, 100)).save(p)
        assert _is_horizontal_image(p) is True

    def test_vertical(self, tmp_path):
        p = tmp_path / "v.png"
        Image.new("RGB", (100, 200)).save(p)
        assert _is_horizontal_image(p) is False

    def test_nonexistent(self, tmp_path):
        assert _is_horizontal_image(tmp_path / "nope.png") is False


class TestFindAssetVariant:
    def test_finds_vertical_variant(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        h_img = assets / "intro_brand.png"
        Image.new("RGB", (1672, 941)).save(h_img)

        v_img = assets / "ChatGPT_Image_vertical.png"
        Image.new("RGB", (941, 1672)).save(v_img)

        result = find_asset_variant(str(h_img), ASPECT_9_16, [assets])
        assert result is not None
        assert "ChatGPT" in Path(result).name

    def test_finds_horizontal_variant(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        v_img = assets / "intro_vertical.png"
        Image.new("RGB", (941, 1672)).save(v_img)

        h_img = assets / "ChatGPT_Image_horizontal.png"
        Image.new("RGB", (1672, 941)).save(h_img)

        result = find_asset_variant(str(v_img), ASPECT_16_9, [assets])
        assert result is not None
        assert "ChatGPT" in Path(result).name

    def test_returns_none_when_no_variant(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        h_img = assets / "intro_brand.png"
        Image.new("RGB", (1672, 941)).save(h_img)

        other_h = assets / "other_horizontal.png"
        Image.new("RGB", (800, 400)).save(other_h)

        result = find_asset_variant(str(h_img), ASPECT_9_16, [assets])
        assert result is None

    def test_nonexistent_original(self, tmp_path):
        result = find_asset_variant("/nonexistent/image.png", ASPECT_9_16, [tmp_path])
        assert result is None

    def test_unreadable_original_falls_back(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        bad_orig = assets / "bad_original.png"
        bad_orig.write_text("not an image")

        v_img = assets / "ChatGPT_vertical.png"
        Image.new("RGB", (100, 200)).save(v_img)

        result = find_asset_variant(str(bad_orig), ASPECT_9_16, [assets])
        assert result is not None

    def test_corrupt_candidate_vertical(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        h_img = assets / "intro_brand.png"
        Image.new("RGB", (200, 100)).save(h_img)

        corrupt = assets / "ChatGPT_corrupt.png"
        corrupt.write_text("not an image")

        good_v = assets / "ChatGPT_good.png"
        Image.new("RGB", (100, 200)).save(good_v)

        result = find_asset_variant(str(h_img), ASPECT_9_16, [assets])
        assert result is not None
        assert "good" in Path(result).name

    def test_corrupt_candidate_horizontal(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        v_img = assets / "intro_vertical.png"
        Image.new("RGB", (100, 200)).save(v_img)

        corrupt = assets / "ChatGPT_corrupt.png"
        corrupt.write_text("not an image")

        good_h = assets / "ChatGPT_good.png"
        Image.new("RGB", (200, 100)).save(good_h)

        result = find_asset_variant(str(v_img), ASPECT_16_9, [assets])
        assert result is not None
        assert "good" in Path(result).name

    def test_dimension_open_exception_vertical(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        h_img = assets / "intro_brand.png"
        Image.new("RGB", (200, 100)).save(h_img)

        v_img = assets / "ChatGPT_vertical.png"
        Image.new("RGB", (100, 200)).save(v_img)

        real_open = Image.open
        call_count = [0]

        def flaky_open(path, *a, **kw):
            call_count[0] += 1
            if call_count[0] > 2:
                raise RuntimeError("flaky")
            return real_open(path, *a, **kw)

        with patch("PIL.Image.open", side_effect=flaky_open):
            result = find_asset_variant(str(h_img), ASPECT_9_16, [assets])
        assert result is not None

    def test_dimension_open_exception_horizontal(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        v_img = assets / "intro_vertical.png"
        Image.new("RGB", (100, 200)).save(v_img)

        h_img = assets / "ChatGPT_horizontal.png"
        Image.new("RGB", (200, 100)).save(h_img)

        real_open = Image.open
        call_count = [0]

        def flaky_open(path, *a, **kw):
            call_count[0] += 1
            if call_count[0] > 2:
                raise RuntimeError("flaky")
            return real_open(path, *a, **kw)

        with patch("PIL.Image.open", side_effect=flaky_open):
            result = find_asset_variant(str(v_img), ASPECT_16_9, [assets])
        assert result is not None

    def test_empty_search_dirs(self, tmp_path):
        h_img = tmp_path / "intro.png"
        Image.new("RGB", (200, 100)).save(h_img)
        result = find_asset_variant(str(h_img), ASPECT_9_16, [])
        assert result is None

    def test_nonexistent_search_dir(self, tmp_path):
        h_img = tmp_path / "intro.png"
        Image.new("RGB", (200, 100)).save(h_img)
        result = find_asset_variant(str(h_img), ASPECT_9_16, [tmp_path / "nonexistent"])
        assert result is None

    def test_outro_image_swapped(self, tmp_path):
        assets = tmp_path / "data" / "assets"
        assets.mkdir(parents=True)

        h_img = assets / "intro_brand.png"
        Image.new("RGB", (200, 100)).save(h_img)

        v_img = assets / "ChatGPT_Image_vertical.png"
        Image.new("RGB", (100, 200)).save(v_img)

        script = _make_sample_script()
        script["intro"]["image"] = str(h_img)
        script["outro"]["image"] = str(h_img)

        from render.aspect_transform import _swap_branded_images
        _swap_branded_images(script, ASPECT_16_9, ASPECT_9_16, tmp_path)

        assert script["intro"]["image"] == str(v_img)
        assert script["outro"]["image"] == str(v_img)

    def test_prefers_chatgpt_over_non_chatgpt(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        h_img = assets / "intro_brand.png"
        Image.new("RGB", (200, 100)).save(h_img)

        regular_v = assets / "regular_vertical.png"
        Image.new("RGB", (100, 200)).save(regular_v)

        chatgpt_v = assets / "ChatGPT_Image_May29_vertical.png"
        Image.new("RGB", (100, 200)).save(chatgpt_v)

        result = find_asset_variant(str(h_img), ASPECT_9_16, [assets])
        assert result is not None
        assert "ChatGPT" in Path(result).name

    def test_prefers_exact_dimension_match(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        h_img = assets / "intro_brand.png"
        Image.new("RGB", (200, 100)).save(h_img)

        close_match = assets / "ChatGPT_close.png"
        Image.new("RGB", (110, 190)).save(close_match)

        exact_match = assets / "ChatGPT_exact.png"
        Image.new("RGB", (100, 200)).save(exact_match)

        result = find_asset_variant(str(h_img), ASPECT_9_16, [assets])
        assert result is not None
        assert "exact" in Path(result).name

    def test_dimension_ratio_between_08_and_095(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        h_img = assets / "intro_brand.png"
        Image.new("RGB", (200, 100)).save(h_img)

        chatgpt_v = assets / "ChatGPT_close_match.png"
        Image.new("RGB", (120, 180)).save(chatgpt_v)

        regular_v = assets / "regular_close.png"
        Image.new("RGB", (120, 180)).save(regular_v)

        result = find_asset_variant(str(h_img), ASPECT_9_16, [assets])
        assert result is not None
        assert "ChatGPT" in Path(result).name

    def test_horizontal_with_dim_ratio(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        v_img = assets / "intro_vertical.png"
        Image.new("RGB", (100, 200)).save(v_img)

        chatgpt_h = assets / "ChatGPT_horizontal_exact.png"
        Image.new("RGB", (200, 100)).save(chatgpt_h)

        chatgpt_h_close = assets / "ChatGPT_horizontal_close.png"
        Image.new("RGB", (180, 120)).save(chatgpt_h_close)

        result = find_asset_variant(str(v_img), ASPECT_16_9, [assets])
        assert result is not None
        assert "exact" in Path(result).name

    def test_skips_original_file(self, tmp_path):
        assets = tmp_path / "assets"
        assets.mkdir()

        h_img = assets / "intro_brand.png"
        Image.new("RGB", (200, 100)).save(h_img)

        result = find_asset_variant(str(h_img), ASPECT_9_16, [assets])
        assert result is None


class TestTransformScript:
    def test_basic_169_to_916(self):
        script = _make_sample_script()
        result = transform_script(script, ASPECT_16_9, ASPECT_9_16)

        assert result["defaults"]["font_size"] < script["defaults"]["font_size"]
        assert result["sections"][0]["visual"]["font_size"] < script["sections"][0]["visual"]["font_size"]
        assert result["name"] == "Test Song"
        assert result["sections"][0]["name"] == "intro section"
        assert result["sections"][0]["type"] == "spoken_prophetic_opening"
        assert result["sections"][0]["lines"] == [0, 1]
        assert result["sections"][1]["lines"] == [2, 3, 4, 5]

    def test_basic_916_to_169(self):
        script = _make_sample_script()
        result = transform_script(script, ASPECT_9_16, ASPECT_16_9)

        assert result["defaults"]["font_size"] > script["defaults"]["font_size"]
        assert result["name"] == "Test Song"

    def test_does_not_modify_original(self):
        script = _make_sample_script()
        original_font = script["defaults"]["font_size"]
        original_fs = json.dumps(script)

        transform_script(script, ASPECT_16_9, ASPECT_9_16)

        assert script["defaults"]["font_size"] == original_font
        assert json.dumps(script) == original_fs

    def test_aspect_meta_added(self):
        script = _make_sample_script()
        result = transform_script(script, ASPECT_16_9, ASPECT_9_16)

        meta = result["_aspect_meta"]
        assert meta["source_aspect"] == ASPECT_16_9
        assert meta["target_aspect"] == ASPECT_9_16
        assert meta["target_width"] == 1080
        assert meta["target_height"] == 1920

    def test_y_positions_adjusted(self):
        script = _make_sample_script()
        result = transform_script(script, ASPECT_16_9, ASPECT_9_16)

        wo = result["sections"][0]["words_overrides"]
        assert wo["0.0"]["y"] != 0.2
        assert wo["0.2"]["y"] != 0.8

    def test_font_deltas_scaled(self):
        script = _make_sample_script()
        result = transform_script(script, ASPECT_16_9, ASPECT_9_16)

        wo = result["sections"][1]["words_overrides"]
        assert wo["2.1"]["font_size_delta"] < 6
        assert wo["2.2"]["font_size_delta"] < 10

    def test_dual_spot_direction_adjusted(self):
        script = _make_sample_script()
        result = transform_script(script, ASPECT_16_9, ASPECT_9_16)

        direction = result["sections"][0]["visual"]["gradient_direction"]
        assert direction.startswith("dual_spot_")

    def test_preserves_non_layout_values(self):
        script = _make_sample_script()
        result = transform_script(script, ASPECT_16_9, ASPECT_9_16)

        assert result["caption_style"]["highlight_color"] == "#FF8C00"
        assert result["caption_style"]["font_family"] == 0
        assert result["sections"][0]["visual"]["text_position"] == "top"
        assert result["sections"][0]["visual"]["bg_animation_preset"] == "smooth"
        assert result["intro"]["duration"] == 4.789
        assert result["outro"]["text"] == "Presented by"

    def test_invalid_source_raises(self):
        with pytest.raises(ValueError, match="Invalid source"):
            transform_script({}, "4:3", ASPECT_9_16)

    def test_invalid_target_raises(self):
        with pytest.raises(ValueError, match="Invalid target"):
            transform_script({}, ASPECT_16_9, "4:3")

    def test_same_aspect_raises(self):
        with pytest.raises(ValueError, match="same"):
            transform_script({}, ASPECT_16_9, ASPECT_16_9)

    def test_branded_images_swapped(self, tmp_path):
        script = _make_sample_script()

        assets = tmp_path / "data" / "assets"
        assets.mkdir(parents=True)

        h_intro = assets / "intro_brand.png"
        Image.new("RGB", (200, 100)).save(h_intro)
        script["intro"]["image"] = str(h_intro)

        v_intro = assets / "ChatGPT_Image_vertical.png"
        Image.new("RGB", (100, 200)).save(v_intro)

        result = transform_script(script, ASPECT_16_9, ASPECT_9_16, project_dir=tmp_path)

        assert result["intro"]["image"] != str(h_intro)
        assert "ChatGPT" in Path(result["intro"]["image"]).name

    def test_no_project_dir_skips_image_swap(self):
        script = _make_sample_script()
        result = transform_script(script, ASPECT_16_9, ASPECT_9_16)
        assert result["intro"]["image"] == "/fake/intro_brand.png"

    def test_lines_overrides_font_sizes_scaled(self):
        script = _make_sample_script()
        result = transform_script(script, ASPECT_16_9, ASPECT_9_16)

        for key in ["0", "1"]:
            original = script["sections"][0]["lines_overrides"][key]["font_size"]
            transformed = result["sections"][0]["lines_overrides"][key]["font_size"]
            assert transformed < original


class TestDetectAspectRatio:
    def test_default_169(self, tmp_path):
        data = tmp_path / "data"
        data.mkdir()
        assert detect_aspect_ratio(tmp_path) == ASPECT_16_9

    def test_detects_916_from_video_file(self, tmp_path):
        out = tmp_path / "output"
        out.mkdir()
        (out / "video_9x16.mp4").write_bytes(b"fake")
        assert detect_aspect_ratio(tmp_path) == ASPECT_9_16

    def test_detects_916_from_vertical_video(self, tmp_path):
        out = tmp_path / "output"
        out.mkdir()
        (out / "video_vertical.mp4").write_bytes(b"fake")
        assert detect_aspect_ratio(tmp_path) == ASPECT_9_16

    def test_detects_169_from_horizontal_video(self, tmp_path):
        out = tmp_path / "output"
        out.mkdir()
        (out / "video_16x9.mp4").write_bytes(b"fake")
        assert detect_aspect_ratio(tmp_path) == ASPECT_16_9

    def test_detects_from_script_meta(self, tmp_path):
        data = tmp_path / "data"
        data.mkdir()
        script = {"_aspect_meta": {"target_aspect": "9:16"}}
        (data / "script.json").write_text(json.dumps(script))
        assert detect_aspect_ratio(tmp_path) == ASPECT_9_16

    def test_bad_script_json_falls_back(self, tmp_path):
        data = tmp_path / "data"
        data.mkdir()
        (data / "script.json").write_text("not json{{{")
        assert detect_aspect_ratio(tmp_path) == ASPECT_16_9


class TestCheckLayoutIssues:
    def test_clean_script_no_issues(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16", "target_width": 1080, "target_height": 1920}
        script["defaults"]["font_size"] = 50
        issues = check_layout_issues(script, ASPECT_9_16)
        assert all(i["check"] != "font_size" for i in issues if "effective_size" in i)

    def test_missing_meta(self):
        script = _make_sample_script()
        issues = check_layout_issues(script, ASPECT_9_16)
        assert any(i["check"] == "meta" for i in issues)

    def test_font_too_small(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        script["defaults"]["font_size"] = 10
        issues = check_layout_issues(script, ASPECT_9_16)
        font_issues = [i for i in issues if i["check"] == "font_size" and i.get("severity") == "error"]
        assert len(font_issues) > 0
        assert any("below minimum" in i["issue"] for i in font_issues)

    def test_word_outside_safe_zone_top(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        script["defaults"]["font_size"] = 50
        script["sections"][0]["words_overrides"]["0.0"]["y"] = 0.01
        issues = check_layout_issues(script, ASPECT_9_16)
        safe_issues = [i for i in issues if i["check"] == "safe_zone"]
        assert any("above safe zone" in i["issue"] for i in safe_issues)

    def test_word_outside_safe_zone_bottom(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        script["defaults"]["font_size"] = 50
        script["sections"][0]["words_overrides"]["0.0"]["y"] = 0.99
        issues = check_layout_issues(script, ASPECT_9_16)
        safe_issues = [i for i in issues if i["check"] == "safe_zone"]
        assert any("below safe zone" in i["issue"] for i in safe_issues)

    def test_image_mismatch_horizontal_in_vertical(self, tmp_path):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}

        h_img = tmp_path / "intro.png"
        Image.new("RGB", (200, 100)).save(h_img)
        script["intro"]["image"] = str(h_img)

        issues = check_layout_issues(script, ASPECT_9_16)
        img_issues = [i for i in issues if i["check"] == "image_mismatch"]
        assert len(img_issues) > 0
        assert any("horizontal" in i["issue"] for i in img_issues)

    def test_image_mismatch_vertical_in_horizontal(self, tmp_path):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "16:9"}

        v_img = tmp_path / "intro.png"
        Image.new("RGB", (100, 200)).save(v_img)
        script["intro"]["image"] = str(v_img)

        issues = check_layout_issues(script, ASPECT_16_9)
        img_issues = [i for i in issues if i["check"] == "image_mismatch"]
        assert len(img_issues) > 0
        assert any("vertical" in i["issue"] for i in img_issues)

    def test_scene_order_preserved(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        source = _make_sample_script()
        issues = check_layout_issues(script, ASPECT_9_16, source_script=source)
        scene_issues = [i for i in issues if i["check"] == "scene_order"]
        assert len(scene_issues) == 0

    def test_scene_order_changed_line_count(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        source = _make_sample_script()
        source["sections"][0]["lines"] = [0]
        issues = check_layout_issues(script, ASPECT_9_16, source_script=source)
        scene_issues = [i for i in issues if i["check"] == "scene_order"]
        assert any("Lines changed" in i["issue"] for i in scene_issues)

    def test_section_count_changed(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        source = _make_sample_script()
        source["sections"].append(source["sections"][0].copy())
        issues = check_layout_issues(script, ASPECT_9_16, source_script=source)
        scene_issues = [i for i in issues if i["check"] == "scene_order"]
        assert any("Section count changed" in i["issue"] for i in scene_issues)

    def test_section_name_changed(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        source = _make_sample_script()
        source["sections"][0]["name"] = "different name"
        issues = check_layout_issues(script, ASPECT_9_16, source_script=source)
        assert any("Section name changed" in i["issue"] for i in issues)

    def test_section_type_changed(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        source = _make_sample_script()
        source["sections"][0]["type"] = "different_type"
        issues = check_layout_issues(script, ASPECT_9_16, source_script=source)
        assert any("Section type changed" in i["issue"] for i in issues)

    def test_project_name_changed(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        source = _make_sample_script()
        source["name"] = "Different Song"
        issues = check_layout_issues(script, ASPECT_9_16, source_script=source)
        assert any("Project name changed" in i["issue"] for i in issues)

    def test_dual_spot_near_edge(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        script["sections"][0]["visual"]["gradient_direction"] = "dual_spot_0.03_0.4_0.98_0.6"
        issues = check_layout_issues(script, ASPECT_9_16)
        bg_issues = [i for i in issues if i["check"] == "background_geometry"]
        assert len(bg_issues) > 0

    def test_section_font_too_small(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        script["defaults"]["font_size"] = 50
        script["sections"][0]["visual"]["font_size"] = 5
        issues = check_layout_issues(script, ASPECT_9_16)
        assert any(i["check"] == "font_size" and i.get("section") == "intro section" for i in issues)

    def test_word_delta_makes_font_too_small(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        script["sections"][1]["visual"]["font_size"] = 30
        script["sections"][1]["words_overrides"]["2.1"]["font_size_delta"] = -30
        issues = check_layout_issues(script, ASPECT_9_16)
        assert any(i["check"] == "font_size" and i.get("word_key") == "2.1" for i in issues)

    def test_image_nonexistent_no_mismatch(self, tmp_path):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        script["intro"]["image"] = "/nonexistent/image.png"
        issues = check_layout_issues(script, ASPECT_9_16)
        img_issues = [i for i in issues if i["check"] == "image_mismatch"]
        assert len(img_issues) == 0

    def test_bad_dual_spot_values(self):
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        script["sections"][0]["visual"]["gradient_direction"] = "dual_spot_x_y_z_w"
        issues = check_layout_issues(script, ASPECT_9_16)
        bg_issues = [i for i in issues if i["check"] == "background_geometry"]
        assert len(bg_issues) == 0


class TestEffectiveFontSize:
    def test_base_1080(self):
        assert _effective_font_size(100, 1080) == 100

    def test_1920_height(self):
        assert _effective_font_size(100, 1920) == int(100 * 1920 / 1080)

    def test_small_height(self):
        assert _effective_font_size(100, 540) == int(100 * 540 / 1080)


class TestTransformIntegration:
    def test_full_transform_round_trip(self):
        original = _make_sample_script()
        to_916 = transform_script(original, ASPECT_16_9, ASPECT_9_16)

        assert to_916["_aspect_meta"]["target_aspect"] == ASPECT_9_16
        assert to_916["sections"][0]["lines"] == [0, 1]
        assert to_916["sections"][1]["lines"] == [2, 3, 4, 5]
        assert to_916["name"] == original["name"]
        assert to_916["intro"]["duration"] == original["intro"]["duration"]
        assert to_916["outro"]["text"] == original["outro"]["text"]

    def test_text_layout_recomputed_not_copied(self):
        original = _make_sample_script()
        original_fs = original["sections"][0]["visual"]["font_size"]
        original_y = original["sections"][0]["words_overrides"]["0.0"]["y"]

        result = transform_script(original, ASPECT_16_9, ASPECT_9_16)
        result_fs = result["sections"][0]["visual"]["font_size"]
        result_y = result["sections"][0]["words_overrides"]["0.0"]["y"]

        assert result_fs != original_fs
        assert result_y != original_y

        ratio = 1080 / 1920
        assert abs(result_fs - round(original_fs * ratio)) <= 1


class TestEnsureTextFits:
    def _make_long_line_synced(self):
        return {
            "lines": [
                {
                    "words": [
                        {"text": "You", "start": 0.0, "end": 0.2},
                        {"text": "come", "start": 0.2, "end": 0.4},
                        {"text": "just", "start": 0.4, "end": 0.6},
                        {"text": "in", "start": 0.6, "end": 0.8},
                        {"text": "time", "start": 0.8, "end": 1.0},
                        {"text": "as", "start": 1.0, "end": 1.2},
                        {"text": "the", "start": 1.2, "end": 1.4},
                        {"text": "skin", "start": 1.4, "end": 1.6},
                        {"text": "that", "start": 1.6, "end": 1.8},
                        {"text": "you", "start": 1.8, "end": 2.0},
                        {"text": "chose", "start": 2.0, "end": 2.2},
                    ]
                },
            ]
        }

    def test_reduces_oversized_line_font(self, tmp_path):
        from render.aspect_transform import _ensure_text_fits, CANVAS_SIZES, SAFE_ZONES
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        script["defaults"]["font_size"] = 82
        script["sections"][0]["visual"]["font_size"] = 82
        script["sections"][0]["lines"] = [0]
        script["sections"][0]["lines_overrides"] = {"0": {"font_size": 84}}
        synced = self._make_long_line_synced()

        _ensure_text_fits(script, "9:16", synced["lines"])

        new_fs = script["sections"][0]["lines_overrides"]["0"]["font_size"]
        assert new_fs < 84

    def test_no_reduction_when_line_fits(self):
        from render.aspect_transform import _ensure_text_fits
        script = _make_sample_script()
        script["_aspect_meta"] = {"target_aspect": "9:16"}
        script["defaults"]["font_size"] = 30
        script["sections"][0]["visual"]["font_size"] = 30
        script["sections"][0]["lines"] = [0]
        script["sections"][0]["lines_overrides"] = {}
        synced = {
            "lines": [{"words": [{"text": "Hi", "start": 0.0, "end": 0.3}]}]
        }

        _ensure_text_fits(script, "9:16", synced["lines"])

        assert "0" not in script["sections"][0].get("lines_overrides", {})

    def test_transform_with_project_dir_loads_synced(self, tmp_path):
        original = _make_sample_script()
        original["sections"][0]["lines"] = [0]
        original["sections"][0]["lines_overrides"] = {"0": {"font_size": 150}}

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "script.json").write_text(json.dumps(original), encoding="utf-8")
        synced = {
            "lines": [
                {
                    "words": [
                        {"text": "A", "start": 0.0, "end": 0.2},
                        {"text": "very", "start": 0.2, "end": 0.4},
                        {"text": "long", "start": 0.4, "end": 0.6},
                        {"text": "line", "start": 0.6, "end": 0.8},
                        {"text": "of", "start": 0.8, "end": 1.0},
                        {"text": "text", "start": 1.0, "end": 1.2},
                        {"text": "here", "start": 1.2, "end": 1.4},
                    ]
                },
            ]
        }
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced), encoding="utf-8")

        result = transform_script(original, ASPECT_16_9, ASPECT_9_16, project_dir=tmp_path)

        line_fs = result["sections"][0]["lines_overrides"]["0"]["font_size"]
        scaled_fs = round(150 * 1080 / 1920)
        assert line_fs < scaled_fs

    def test_transform_without_project_dir_skips_fitting(self):
        original = _make_sample_script()
        original["sections"][0]["lines_overrides"] = {"0": {"font_size": 150}}

        result = transform_script(original, ASPECT_16_9, ASPECT_9_16)

        scaled_fs = round(150 * 1080 / 1920)
        assert result["sections"][0]["lines_overrides"]["0"]["font_size"] == scaled_fs


def _write_wav(path, duration=1.0, sr=22050, freq=440.0):
    import soundfile as sf
    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
    sig = (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    sf.write(str(path), sig, sr)


class TestTransformCommand:
    @pytest.fixture
    def runner(self):
        from click.testing import CliRunner
        return CliRunner()

    @pytest.fixture
    def project_with_script(self, tmp_path):
        from cli.commands import cli
        from click.testing import CliRunner

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")

        runner = CliRunner()
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        synced = {
            "lines": [
                {"index": 0, "text": "Hello world", "start": 0.0, "end": 0.5,
                 "words": [{"text": "Hello", "start": 0.0, "end": 0.3}, {"text": "world", "start": 0.3, "end": 0.5}]},
            ]
        }
        (tmp_path / "data" / "lyrics_synced.json").write_text(json.dumps(synced), encoding="utf-8")

        script = _make_sample_script()
        (tmp_path / "data" / "script.json").write_text(json.dumps(script), encoding="utf-8")

        return tmp_path

    def test_transform_help(self, runner):
        from cli.commands import cli
        result = runner.invoke(cli, ["transform", "--help"])
        assert result.exit_code == 0
        assert "target-aspect" in result.output

    def test_transform_skip_render(self, runner, project_with_script):
        from cli.commands import cli
        result = runner.invoke(cli, ["transform", "--project", str(project_with_script),
                                      "--target-aspect", "9:16", "--skip-render"])
        assert result.exit_code == 0
        assert (project_with_script / "data" / "script_9x16.json").exists()

    def test_transform_creates_script_file(self, runner, project_with_script):
        from cli.commands import cli
        result = runner.invoke(cli, ["transform", "--project", str(project_with_script),
                                      "--target-aspect", "9:16", "--skip-render"])
        assert result.exit_code == 0

        transformed_path = project_with_script / "data" / "script_9x16.json"
        assert transformed_path.exists()

        transformed = json.loads(transformed_path.read_text())
        assert transformed["_aspect_meta"]["target_aspect"] == "9:16"

    def test_transform_does_not_modify_original(self, runner, project_with_script):
        from cli.commands import cli

        original_text = (project_with_script / "data" / "script.json").read_text()
        original_data = json.loads(original_text)
        original_fs = original_data["defaults"]["font_size"]

        result = runner.invoke(cli, ["transform", "--project", str(project_with_script),
                                      "--target-aspect", "9:16", "--skip-render"])
        assert result.exit_code == 0

        after_text = (project_with_script / "data" / "script.json").read_text()
        assert after_text == original_text
        after_data = json.loads(after_text)
        assert after_data["defaults"]["font_size"] == original_fs

    def test_transform_same_aspect_fails(self, runner, project_with_script):
        from cli.commands import cli
        result = runner.invoke(cli, ["transform", "--project", str(project_with_script),
                                      "--source-aspect", "16:9", "--target-aspect", "16:9", "--skip-render"])
        assert result.exit_code != 0

    def test_transform_no_script_fails(self, runner, tmp_path):
        from cli.commands import cli
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--dir", str(tmp_path)])
        (tmp_path / "data" / "script.json").unlink(missing_ok=True)
        result = runner.invoke(cli, ["transform", "--project", str(tmp_path),
                                      "--target-aspect", "9:16", "--skip-render"])
        assert result.exit_code != 0

    def test_transform_with_render(self, runner, project_with_script):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock

        with patch("render.renderer.VideoRenderer") as MockRenderer:
            mock_instance = MagicMock()
            mock_instance.duration = 1.0
            mock_instance.audio_path = None
            mock_instance.load.return_value = None
            mock_instance.render.return_value = project_with_script / "output" / "video_9x16.mp4"
            MockRenderer.return_value = mock_instance

            (project_with_script / "output").mkdir(exist_ok=True)
            out_file = project_with_script / "output" / "video_9x16.mp4"
            out_file.write_bytes(b"fake video")

            result = runner.invoke(cli, ["transform", "--project", str(project_with_script),
                                          "--source-aspect", "16:9",
                                          "--target-aspect", "9:16", "--skip-audit"])
            assert result.exit_code == 0

    def test_transform_with_audit(self, runner, project_with_script):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock

        with patch("render.renderer.VideoRenderer") as MockRenderer:
            mock_render = MagicMock()
            mock_render.duration = 1.0
            mock_render.audio_path = None
            mock_render.load.return_value = None
            mock_render.render.return_value = project_with_script / "output" / "video_9x16.mp4"
            mock_render.synced = {
                "lines": [
                    {"index": 0, "text": "Hello world", "start": 0.0, "end": 0.5,
                     "words": [{"text": "Hello", "start": 0.0, "end": 0.3}, {"text": "world", "start": 0.3, "end": 0.5}]},
                ]
            }
            mock_render.render_frame.return_value = Image.new("RGB", (540, 960), (0, 0, 0))
            MockRenderer.return_value = mock_render

            (project_with_script / "output").mkdir(exist_ok=True)
            out_file = project_with_script / "output" / "video_9x16.mp4"
            out_file.write_bytes(b"fake video")

            result = runner.invoke(cli, ["transform", "--project", str(project_with_script),
                                          "--source-aspect", "16:9",
                                          "--target-aspect", "9:16"])
            assert result.exit_code == 0
            assert (project_with_script / "output" / "audit_9x16" / "summary.json").exists()

            summary = json.loads((project_with_script / "output" / "audit_9x16" / "summary.json").read_text())
            assert summary["aspect_ratio"] == "9:16"

    def test_transform_with_audit_timing_issues(self, runner, project_with_script):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock

        with patch("render.renderer.VideoRenderer") as MockRenderer:
            mock_render = MagicMock()
            mock_render.duration = 5.0
            mock_render.audio_path = None
            mock_render.load.return_value = None
            mock_render.render.return_value = project_with_script / "output" / "video_9x16.mp4"
            mock_render.synced = {
                "lines": [
                    {"index": 0, "text": "Bad timing", "start": 0.0, "end": 5.0,
                     "words": [
                         {"text": "Bad", "start": 0.0, "end": 3.0},
                         {"text": "short", "start": 3.01, "end": 3.02},
                         {"text": "long", "start": 3.5, "end": 1.0},
                         {"text": "gap", "start": 5.0, "end": 5.5},
                     ]},
                ]
            }
            mock_render.render_frame.return_value = Image.new("RGB", (540, 960), (0, 0, 0))
            MockRenderer.return_value = mock_render

            (project_with_script / "output").mkdir(exist_ok=True)
            out_file = project_with_script / "output" / "video_9x16.mp4"
            out_file.write_bytes(b"fake video")

            result = runner.invoke(cli, ["transform", "--project", str(project_with_script),
                                          "--source-aspect", "16:9",
                                          "--target-aspect", "9:16"])
            assert result.exit_code == 0

    def test_transform_with_audit_render_error(self, runner, project_with_script):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock

        call_count = [0]

        def mock_render_frame(t):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("frame render error")
            return Image.new("RGB", (540, 960), (0, 0, 0))

        with patch("render.renderer.VideoRenderer") as MockRenderer:
            mock_render = MagicMock()
            mock_render.duration = 1.0
            mock_render.audio_path = None
            mock_render.load.return_value = None
            mock_render.render.return_value = project_with_script / "output" / "video_9x16.mp4"
            mock_render.synced = {
                "lines": [
                    {"index": 0, "text": "Test", "start": 0.0, "end": 0.5,
                     "words": [
                         {"text": "Test", "start": 0.0, "end": 0.3},
                         {"text": "more", "start": 0.3, "end": 0.5},
                     ]},
                ]
            }
            mock_render.render_frame = mock_render_frame
            MockRenderer.return_value = mock_render

            (project_with_script / "output").mkdir(exist_ok=True)
            out_file = project_with_script / "output" / "video_9x16.mp4"
            out_file.write_bytes(b"fake video")

            result = runner.invoke(cli, ["transform", "--project", str(project_with_script),
                                          "--source-aspect", "16:9",
                                          "--target-aspect", "9:16"])
            assert result.exit_code == 0

    def test_transform_no_synced_fails(self, runner, project_with_script):
        from cli.commands import cli
        (project_with_script / "data" / "lyrics_synced.json").unlink()
        result = runner.invoke(cli, ["transform", "--project", str(project_with_script),
                                      "--target-aspect", "9:16", "--skip-render"])
        assert result.exit_code != 0

    def test_transform_with_output_path(self, runner, project_with_script):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock

        custom_out = project_with_script / "custom_output.mp4"

        with patch("render.renderer.VideoRenderer") as MockRenderer:
            mock_instance = MagicMock()
            mock_instance.duration = 1.0
            mock_instance.audio_path = None
            mock_instance.load.return_value = None
            mock_instance.render.return_value = custom_out
            MockRenderer.return_value = mock_instance

            custom_out.write_bytes(b"fake video")

            result = runner.invoke(cli, ["transform", "--project", str(project_with_script),
                                          "--source-aspect", "16:9",
                                          "--target-aspect", "9:16",
                                          "--output", str(custom_out),
                                          "--skip-audit"])
            assert result.exit_code == 0

    def test_transform_with_many_layout_issues(self, runner, tmp_path):
        from cli.commands import cli
        from click.testing import CliRunner

        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        r = CliRunner()
        r.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        synced = {
            "lines": [{"index": 0, "text": "Hello world", "start": 0.0, "end": 0.5,
                        "words": [{"text": "Hello", "start": 0.0, "end": 0.3}, {"text": "world", "start": 0.3, "end": 0.5}]}]
        }
        (tmp_path / "data" / "lyrics_synced.json").write_text(json.dumps(synced))

        script = {
            "name": "Test",
            "defaults": {"font_size": 94},
            "sections": [],
            "intro": {"image": "/fake", "duration": 1},
            "outro": {"image": "/fake", "text": "By"},
        }
        for i in range(12):
            script["sections"].append({
                "name": f"section_{i}",
                "type": "verse",
                "lines": [i],
                "visual": {"font_size": 94},
                "lines_overrides": {},
                "words_overrides": {f"{i}.0": {"font_size_delta": -90}},
            })
        (tmp_path / "data" / "script.json").write_text(json.dumps(script))

        result = r.invoke(cli, ["transform", "--project", str(tmp_path),
                                 "--source-aspect", "16:9",
                                 "--target-aspect", "9:16", "--skip-render"])
        assert result.exit_code == 0
        assert "... and" in result.output

    def test_transform_with_audio_from_project(self, runner, project_with_script):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock

        audio_dir = project_with_script / "cache" / "stems"
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_file = audio_dir / "combined_mix.wav"
        _write_wav(audio_file)

        proj_data = json.loads((project_with_script / "data" / "mvp_project.json").read_text())
        proj_data["paths"]["audio"] = "cache/stems/combined_mix.wav"
        (project_with_script / "data" / "mvp_project.json").write_text(json.dumps(proj_data))

        with patch("render.renderer.VideoRenderer") as MockRenderer:
            mock_instance = MagicMock()
            mock_instance.duration = 1.0
            mock_instance.audio_path = None
            mock_instance.load.return_value = None
            mock_instance.render.return_value = project_with_script / "output" / "video_9x16.mp4"
            MockRenderer.return_value = mock_instance

            (project_with_script / "output").mkdir(exist_ok=True)
            out_file = project_with_script / "output" / "video_9x16.mp4"
            out_file.write_bytes(b"fake video")

            result = runner.invoke(cli, ["transform", "--project", str(project_with_script),
                                          "--source-aspect", "16:9",
                                          "--target-aspect", "9:16", "--skip-audit"])
            assert result.exit_code == 0
            assert "combined_mix.wav" in result.output

    def test_transform_auto_detect_source(self, runner, project_with_script):
        from cli.commands import cli
        result = runner.invoke(cli, ["transform", "--project", str(project_with_script),
                                      "--target-aspect", "9:16", "--skip-render"])
        assert result.exit_code == 0
        assert "Auto-detected" in result.output


class TestAuditCommandAspectAware:
    @pytest.fixture
    def runner(self):
        from click.testing import CliRunner
        return CliRunner()

    def _setup_project(self, tmp_path, runner):
        from cli.commands import cli
        wav = tmp_path / "song.wav"
        _write_wav(wav)
        srt = tmp_path / "lyrics.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,500\nHello world\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--name", "Test", "--audio", str(wav), "--lyrics", str(srt), "--dir", str(tmp_path)])

        synced = {
            "lines": [
                {"index": 0, "text": "Hello world", "start": 0.0, "end": 0.5,
                 "words": [{"text": "Hello", "start": 0.0, "end": 0.3}, {"text": "world", "start": 0.3, "end": 0.5}]},
            ]
        }
        (tmp_path / "data" / "lyrics_synced.json").write_text(json.dumps(synced), encoding="utf-8")

    def test_audit_default_still_works(self, runner, tmp_path):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock
        self._setup_project(tmp_path, runner)

        mock_renderer = MagicMock()
        mock_renderer.synced = {"lines": [{"words": [{"text": "Hi", "start": 0.0, "end": 0.3}]}]}
        mock_renderer.load.return_value = None
        mock_renderer.render_frame.return_value = Image.new("RGB", (960, 540), (0, 0, 0))

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(cli, ["audit", "--project", str(tmp_path), "--json-only"])

        assert result.exit_code == 0
        assert (tmp_path / "output" / "audit" / "summary.json").exists()

    def test_audit_with_aspect_ratio(self, runner, tmp_path):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock
        self._setup_project(tmp_path, runner)

        mock_renderer = MagicMock()
        mock_renderer.synced = {"lines": [{"words": [{"text": "Hi", "start": 0.0, "end": 0.3}]}]}
        mock_renderer.load.return_value = None
        mock_renderer.render_frame.return_value = Image.new("RGB", (540, 960), (0, 0, 0))

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(cli, ["audit", "--project", str(tmp_path),
                                          "--aspect-ratio", "9:16", "--json-only"])

        assert result.exit_code == 0
        assert (tmp_path / "output" / "audit_9x16" / "summary.json").exists()

        summary = json.loads((tmp_path / "output" / "audit_9x16" / "summary.json").read_text())
        assert summary["aspect_ratio"] == "9:16"
        assert summary["render_width"] == 540
        assert summary["render_height"] == 960

    def test_audit_with_script_file(self, runner, tmp_path):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock
        self._setup_project(tmp_path, runner)

        script = _make_sample_script()
        (tmp_path / "data" / "script_9x16.json").write_text(json.dumps(script), encoding="utf-8")

        mock_renderer = MagicMock()
        mock_renderer.synced = {"lines": [{"words": [{"text": "Hi", "start": 0.0, "end": 0.3}]}]}
        mock_renderer.load.return_value = None
        mock_renderer.render_frame.return_value = Image.new("RGB", (540, 960), (0, 0, 0))

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(cli, ["audit", "--project", str(tmp_path),
                                          "--script", "script_9x16.json",
                                          "--aspect-ratio", "9:16", "--json-only"])

        assert result.exit_code == 0
        assert "script_9x16.json" in result.output

    def test_audit_16x9_aspect_ratio(self, runner, tmp_path):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock
        self._setup_project(tmp_path, runner)

        mock_renderer = MagicMock()
        mock_renderer.synced = {"lines": [{"words": [{"text": "Hi", "start": 0.0, "end": 0.3}]}]}
        mock_renderer.load.return_value = None
        mock_renderer.render_frame.return_value = Image.new("RGB", (960, 540), (0, 0, 0))

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(cli, ["audit", "--project", str(tmp_path),
                                          "--aspect-ratio", "16:9", "--json-only"])

        assert result.exit_code == 0
        assert (tmp_path / "output" / "audit_16x9" / "summary.json").exists()

    def test_audit_custom_output_overrides(self, runner, tmp_path):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock
        self._setup_project(tmp_path, runner)

        mock_renderer = MagicMock()
        mock_renderer.synced = {"lines": [{"words": [{"text": "Hi", "start": 0.0, "end": 0.3}]}]}
        mock_renderer.load.return_value = None
        mock_renderer.render_frame.return_value = Image.new("RGB", (540, 960), (0, 0, 0))

        custom = tmp_path / "my_audit"
        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(cli, ["audit", "--project", str(tmp_path),
                                          "--aspect-ratio", "9:16", "--json-only",
                                          "--output", str(custom)])

        assert result.exit_code == 0
        assert (custom / "summary.json").exists()

    def test_audit_explicit_dimensions_override_aspect(self, runner, tmp_path):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock
        self._setup_project(tmp_path, runner)

        mock_renderer = MagicMock()
        mock_renderer.synced = {"lines": [{"words": [{"text": "Hi", "start": 0.0, "end": 0.3}]}]}
        mock_renderer.load.return_value = None
        mock_renderer.render_frame.return_value = Image.new("RGB", (320, 180), (0, 0, 0))
        mock_renderer.caption_style = {"font_size": 112}
        mock_renderer.get_visual.return_value = {"font_size": 112, "font_family": 0}
        mock_renderer._layout_line.return_value = [
            {"px_x": 160, "px_y": 90, "wW": 20, "word_size": 16, "x": None},
        ]

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(cli, ["audit", "--project", str(tmp_path),
                                          "--aspect-ratio", "9:16",
                                          "--width", "320", "--height", "180",
                                          "--json-only"])

        assert result.exit_code == 0

    def test_audit_9x16_detects_text_overflow(self, runner, tmp_path):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock
        self._setup_project(tmp_path, runner)

        mock_renderer = MagicMock()
        mock_renderer.synced = {"lines": [{"words": [
            {"text": "Hello", "start": 0.0, "end": 0.3},
            {"text": "world", "start": 0.3, "end": 0.5},
        ]}]}
        mock_renderer.load.return_value = None
        mock_renderer.render_frame.return_value = Image.new("RGB", (540, 960), (0, 0, 0))
        mock_renderer.caption_style = {"font_size": 112}
        mock_renderer.get_visual.return_value = {"font_size": 112, "font_family": 0}
        mock_renderer._layout_line.return_value = [
            {"px_x": -20, "px_y": 480, "wW": 100, "word_size": 47, "x": None},
            {"px_x": 560, "px_y": 480, "wW": 80, "word_size": 47, "x": None},
        ]

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(cli, ["audit", "--project", str(tmp_path),
                                          "--aspect-ratio", "9:16", "--json-only"])

        assert result.exit_code == 0
        assert "Text overflow" in result.output
        summary = json.loads((tmp_path / "output" / "audit_9x16" / "summary.json").read_text())
        assert "overflow_issues" in summary
        assert len(summary["overflow_issues"]) >= 2

    def test_audit_16x9_no_text_overflow(self, runner, tmp_path):
        from cli.commands import cli
        from unittest.mock import patch, MagicMock
        self._setup_project(tmp_path, runner)

        mock_renderer = MagicMock()
        mock_renderer.synced = {"lines": [{"words": [
            {"text": "Hello", "start": 0.0, "end": 0.3},
            {"text": "world", "start": 0.3, "end": 0.5},
        ]}]}
        mock_renderer.load.return_value = None
        mock_renderer.render_frame.return_value = Image.new("RGB", (960, 540), (0, 0, 0))
        mock_renderer.caption_style = {"font_size": 112}
        mock_renderer.get_visual.return_value = {"font_size": 112, "font_family": 0}
        mock_renderer._layout_line.return_value = [
            {"px_x": 400, "px_y": 270, "wW": 100, "word_size": 47, "x": None},
            {"px_x": 550, "px_y": 270, "wW": 80, "word_size": 47, "x": None},
        ]

        with patch("render.renderer.VideoRenderer", return_value=mock_renderer):
            result = runner.invoke(cli, ["audit", "--project", str(tmp_path),
                                          "--aspect-ratio", "16:9", "--json-only"])

        assert result.exit_code == 0
        summary = json.loads((tmp_path / "output" / "audit_16x9" / "summary.json").read_text())
        assert summary.get("overflow_issues") is None or len(summary.get("overflow_issues", [])) == 0
