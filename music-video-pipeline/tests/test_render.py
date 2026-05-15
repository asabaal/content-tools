from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from render.renderer import VideoRenderer, _hex_to_rgb, _contrast_color, _companion_color, _find_font


class TestHexToRgb:
    def test_basic(self):
        assert _hex_to_rgb("#ff0000") == (255, 0, 0)

    def test_no_hash(self):
        assert _hex_to_rgb("00ff00") == (0, 255, 0)

    def test_dark(self):
        assert _hex_to_rgb("#1a1a2e") == (26, 26, 46)


class TestContrastColor:
    def test_dark_bg(self):
        assert _contrast_color("#000000") == "#ffffff"

    def test_light_bg(self):
        assert _contrast_color("#ffffff") == "#000000"

    def test_mid(self):
        result = _contrast_color("#888888")
        assert result in ("#000000", "#ffffff")


class TestCompanionColor:
    def test_shifts_hue(self):
        result = _companion_color("#ff0000")
        assert result.startswith("#")
        assert result != "#ff0000"

    def test_returns_hex(self):
        result = _companion_color("#4cc9f0")
        assert len(result) == 7
        int(result[1:], 16)


class TestFindFont:
    def test_returns_font(self):
        font = _find_font(48)
        assert font is not None


class TestVideoRendererLoad:
    @pytest.fixture
    def project_dir(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        synced = {
            "lines": [
                {"index": 0, "text": "Hello world", "start": 1.0, "end": 3.0,
                 "words": [{"text": "Hello", "start": 1.0, "end": 2.0}, {"text": "world", "start": 2.0, "end": 3.0}]},
                {"index": 1, "text": "Test line", "start": 4.0, "end": 5.0,
                 "words": [{"text": "Test", "start": 4.0, "end": 4.5}, {"text": "line", "start": 4.5, "end": 5.0}]},
            ]
        }
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced), encoding="utf-8")

        analysis = {"duration": 6.0, "sample_rate": 22050, "bpm": 120.0, "beat_times": [], "onset_times": []}
        (data_dir / "analysis.json").write_text(json.dumps(analysis), encoding="utf-8")

        return tmp_path

    def test_load_no_script(self, project_dir):
        r = VideoRenderer(project_dir)
        r.load()
        assert r.duration == 6.0
        assert len(r.synced["lines"]) == 2

    def test_load_with_script(self, project_dir):
        script = {
            "name": "Test",
            "defaults": {"background_color": "#ff0000", "reveal_mode": "progressive"},
            "sections": [
                {"name": "Intro", "type": "intro", "lines": [0],
                 "visual": {"background_color": "#00ff00"}},
            ],
        }
        (project_dir / "data" / "script.json").write_text(json.dumps(script), encoding="utf-8")

        r = VideoRenderer(project_dir)
        r.load()
        assert r.defaults["background_color"] == "#ff0000"

    def test_load_missing_synced(self, tmp_path):
        r = VideoRenderer(tmp_path)
        with pytest.raises(FileNotFoundError):
            r.load()


class TestVideoRendererGetVisual:
    @pytest.fixture
    def renderer(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {
            "lines": [
                {"index": 0, "text": "A", "start": 0, "end": 1, "words": [{"text": "A", "start": 0, "end": 1}]},
                {"index": 1, "text": "B", "start": 1, "end": 2, "words": [{"text": "B", "start": 1, "end": 2}]},
            ]
        }
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        (data_dir / "analysis.json").write_text(json.dumps({"duration": 3.0}))

        r = VideoRenderer(tmp_path)
        r.load()
        return r

    def test_defaults_only(self, renderer):
        renderer.defaults = {"background_color": "#111111"}
        v = renderer.get_visual(0, 0)
        assert v["background_color"] == "#111111"

    def test_section_override(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0], "visual": {"background_color": "#222222"}},
            ]
        }
        v = renderer.get_visual(0, 0)
        assert v["background_color"] == "#222222"

    def test_line_override(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0, 1], "visual": {"background_color": "#222222"},
                 "lines_overrides": {"1": {"background_color": "#333333"}}},
            ]
        }
        v = renderer.get_visual(1, 0)
        assert v["background_color"] == "#333333"

    def test_word_override(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0], "visual": {"background_color": "#222222"},
                 "words_overrides": {"0.0": {"background_color": "#444444"}}},
            ]
        }
        v = renderer.get_visual(0, 0)
        assert v["background_color"] == "#444444"


class TestVideoRendererFindActiveWord:
    @pytest.fixture
    def renderer(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {
            "lines": [
                {"index": 0, "text": "Hello world", "start": 1.0, "end": 3.0,
                 "words": [{"text": "Hello", "start": 1.0, "end": 2.0}, {"text": "world", "start": 2.0, "end": 3.0}]},
            ]
        }
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        (data_dir / "analysis.json").write_text(json.dumps({"duration": 5.0}))
        r = VideoRenderer(tmp_path)
        r.load()
        return r

    def test_active_word(self, renderer):
        line_idx, word_idx = renderer._find_active_word(1.5)
        assert line_idx == 0
        assert word_idx == 0

    def test_second_word(self, renderer):
        line_idx, word_idx = renderer._find_active_word(2.5)
        assert line_idx == 0
        assert word_idx == 1

    def test_no_active(self, renderer):
        line_idx, word_idx = renderer._find_active_word(0.5)
        assert line_idx == -1


class TestVideoRendererRenderFrame:
    @pytest.fixture
    def renderer(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {
            "lines": [
                {"index": 0, "text": "Hello world", "start": 1.0, "end": 3.0,
                 "words": [{"text": "Hello", "start": 1.0, "end": 2.0}, {"text": "world", "start": 2.0, "end": 3.0}]},
            ]
        }
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        (data_dir / "analysis.json").write_text(json.dumps({"duration": 5.0}))
        r = VideoRenderer(tmp_path, width=320, height=180)
        r.load()
        return r

    def test_frame_no_active_word(self, renderer):
        img = renderer.render_frame(0.0)
        assert img.size == (320, 180)
        assert isinstance(img, Image.Image)

    def test_frame_with_active_word(self, renderer):
        img = renderer.render_frame(1.5)
        assert img.size == (320, 180)

    def test_frame_karaoke(self, renderer):
        renderer.defaults["reveal_mode"] = "karaoke"
        img = renderer.render_frame(1.5)
        assert img.size == (320, 180)

    def test_frame_line_by_line(self, renderer):
        renderer.defaults["reveal_mode"] = "line-by-line"
        img = renderer.render_frame(1.5)
        assert img.size == (320, 180)

    def test_frame_progressive(self, renderer):
        renderer.defaults["reveal_mode"] = "progressive"
        img = renderer.render_frame(1.5)
        assert img.size == (320, 180)


class TestVideoRendererDrawGradient:
    @pytest.fixture
    def renderer(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {"lines": [{"index": 0, "text": "A", "start": 0, "end": 1, "words": [{"text": "A", "start": 0, "end": 1}]}]}
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        (data_dir / "analysis.json").write_text(json.dumps({"duration": 2.0}))
        r = VideoRenderer(tmp_path, width=64, height=64)
        r.load()
        return r

    def test_vertical_gradient(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "vertical_top_bottom")
        top = img.getpixel((32, 0))
        bot = img.getpixel((32, 63))
        assert top[0] < bot[0]

    def test_horizontal_gradient(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ff0000"], "horizontal_left_right")
        left = img.getpixel((0, 32))
        right = img.getpixel((63, 32))
        assert left[0] < right[0]

    def test_radial_gradient(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "radial_center")
        center = img.getpixel((32, 32))
        corner = img.getpixel((0, 0))
        assert center[0] < corner[0]

    def test_diagonal_gradient(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "diagonal_tl_br")
        tl = img.getpixel((0, 0))
        br = img.getpixel((63, 63))
        assert tl[0] < br[0]


class TestVideoRendererDrawTexture:
    @pytest.fixture
    def renderer(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {"lines": []}
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        (data_dir / "analysis.json").write_text(json.dumps({"duration": 1.0}))
        r = VideoRenderer(tmp_path, width=64, height=64)
        r.load()
        return r

    def test_no_texture(self, renderer):
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        renderer._draw_texture(img, {"texture_type": "none"})
        assert img.getpixel((32, 32)) == (128, 128, 128)

    def test_noise_texture(self, renderer):
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        renderer._draw_texture(img, {"texture_type": "noise_fine", "texture_opacity": 0.3, "texture_blend_mode": "screen"})
        assert img.size == (64, 64)

    def test_vignette(self, renderer):
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        renderer._draw_texture(img, {"texture_type": "vignette_soft", "texture_opacity": 0.5})
        assert img.size == (64, 64)


class TestEncoder:
    def test_encoder_import(self):
        from render.encoder import VideoEncoder
        assert VideoEncoder is not None

    def test_encoder_context_manager(self, tmp_path):
        from render.encoder import VideoEncoder
        out = tmp_path / "test.mp4"
        with patch("subprocess.Popen") as mock_popen:
            proc = MagicMock()
            proc.stdin = MagicMock()
            proc.communicate.return_value = (b"", b"")
            proc.returncode = 0
            mock_popen.return_value = proc
            with VideoEncoder(out, 320, 180, 30) as enc:
                enc.write_frame(b"\x00" * 320 * 180 * 3)
            assert mock_popen.called

    def test_encoder_not_opened(self, tmp_path):
        from render.encoder import VideoEncoder
        enc = VideoEncoder(tmp_path / "test.mp4")
        with pytest.raises(RuntimeError):
            enc.write_frame(b"\x00")
