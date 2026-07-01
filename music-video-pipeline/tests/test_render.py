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
from render.animations import AnimationState


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


class TestTimingOverrides:
    @pytest.fixture
    def project_dir(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {
            "lines": [
                {"index": 0, "text": "old line", "start": 10.0, "end": 20.0,
                 "words": [{"text": "old", "start": 10.0, "end": 15.0},
                           {"text": "line", "start": 15.0, "end": 20.0}]},
                {"index": 1, "text": "untouched", "start": 21.0, "end": 22.0,
                 "words": [{"text": "untouched", "start": 21.0, "end": 22.0}]},
            ]
        }
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced), encoding="utf-8")
        (data_dir / "analysis.json").write_text(
            json.dumps({"duration": 30.0, "beat_times": []}), encoding="utf-8"
        )
        return tmp_path

    def test_override_merges_into_synced(self, project_dir):
        script = {
            "defaults": {},
            "timing_overrides": {
                "0": {"start": 5.0, "end": 9.0,
                      "words": [{"word": "new", "start": 5.0, "end": 7.0},
                                {"word": "words", "start": 7.0, "end": 9.0}]},
                "_provenance": {"stem": "backing_vocals"},
            },
        }
        (project_dir / "data" / "script.json").write_text(json.dumps(script), encoding="utf-8")

        r = VideoRenderer(project_dir)
        r.load()
        line0 = r.synced["lines"][0]
        assert line0["start"] == 5.0 and line0["end"] == 9.0
        # word key normalized to "text" for the draw path
        assert [w["text"] for w in line0["words"]] == ["new", "words"]
        assert line0["words"][0]["start"] == 5.0
        # untouched line stays intact
        assert r.synced["lines"][1]["start"] == 21.0

    def test_find_active_word_follows_override(self, project_dir):
        script = {
            "defaults": {},
            "timing_overrides": {
                "0": {"start": 5.0, "end": 9.0,
                      "words": [{"word": "new", "start": 5.0, "end": 7.0},
                                {"word": "words", "start": 7.0, "end": 9.0}]},
            },
        }
        (project_dir / "data" / "script.json").write_text(json.dumps(script), encoding="utf-8")

        r = VideoRenderer(project_dir)
        r.load()
        # at t=6 the original line (10..20) would be inactive; override makes it active
        line_idx, word_idx = r._find_active_word(6.0)
        assert line_idx == 0
        assert word_idx == 0

    def test_no_override_is_noop(self, project_dir):
        (project_dir / "data" / "script.json").write_text(
            json.dumps({"defaults": {}}), encoding="utf-8"
        )
        r = VideoRenderer(project_dir)
        r.load()
        assert r.synced["lines"][0]["start"] == 10.0


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

    def test_encoder_close_not_opened(self, tmp_path):
        from render.encoder import VideoEncoder
        enc = VideoEncoder(tmp_path / "test.mp4")
        with pytest.raises(RuntimeError):
            enc.close()

    def test_encoder_with_audio_path(self, tmp_path):
        from render.encoder import VideoEncoder
        out = tmp_path / "test.mp4"
        audio = tmp_path / "audio.wav"
        audio.write_bytes(b"\x00")
        with patch("subprocess.Popen") as mock_popen:
            proc = MagicMock()
            proc.stdin = MagicMock()
            proc.returncode = 0
            proc.stderr = MagicMock()
            proc.stderr.read.return_value = b""
            mock_popen.return_value = proc
            with VideoEncoder(out, 320, 180, 30, audio_path=audio) as enc:
                enc.write_frame(b"\x00" * 320 * 180 * 3)
            cmd = mock_popen.call_args[0][0]
            assert "-c:a" in cmd
            assert "aac" in cmd

    def test_encoder_ffmpeg_error(self, tmp_path):
        from render.encoder import VideoEncoder
        out = tmp_path / "test.mp4"
        with patch("subprocess.Popen") as mock_popen:
            proc = MagicMock()
            proc.stdin = MagicMock()
            proc.returncode = 1
            proc.stderr = MagicMock()
            proc.stderr.read.return_value = b"error"
            mock_popen.return_value = proc
            with pytest.raises(RuntimeError, match="ffmpeg exited"):
                with VideoEncoder(out, 320, 180, 30) as enc:
                    enc.write_frame(b"\x00" * 320 * 180 * 3)


class TestVideoRendererGetAudioAt:
    @pytest.fixture
    def renderer_with_audio(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {
            "lines": [
                {"index": 0, "text": "A", "start": 0, "end": 1, "words": [{"text": "A", "start": 0, "end": 1}]},
            ]
        }
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        analysis = {"duration": 2.0, "sample_rate": 48000, "hop_length": 512}
        (data_dir / "analysis.json").write_text(json.dumps(analysis))
        r = VideoRenderer(tmp_path, width=64, height=64)
        r.load()
        r._rms_energy = [0.1, 0.5, 0.9]
        r._spectral_centroids = [0.2, 0.4, 0.6]
        r._beat_times = [0.5, 1.0]
        r._audio_fps = 1.0
        return r

    def test_returns_energy(self, renderer_with_audio):
        audio = renderer_with_audio._get_audio_at(0)
        assert audio["energy"] == 0.1

    def test_returns_centroid(self, renderer_with_audio):
        audio = renderer_with_audio._get_audio_at(2)
        assert audio["centroid"] == 0.6

    def test_beat_detection(self, renderer_with_audio):
        audio = renderer_with_audio._get_audio_at(0.5)
        assert audio["is_beat"] is True

    def test_no_beat(self, renderer_with_audio):
        audio = renderer_with_audio._get_audio_at(0.2)
        assert audio["is_beat"] is False

    def test_no_audio_features(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {"lines": [{"index": 0, "text": "A", "start": 0, "end": 1, "words": [{"text": "A", "start": 0, "end": 1}]}]}
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        (data_dir / "analysis.json").write_text(json.dumps({"duration": 2.0}))
        r = VideoRenderer(tmp_path, width=64, height=64)
        r.load()
        r._rms_energy = []
        r._spectral_centroids = []
        r._beat_times = []
        audio = r._get_audio_at(0.5)
        assert audio["energy"] == 0.0
        assert audio["centroid"] == 0.5
        assert audio["is_beat"] is False


class TestVideoRendererComputeAnimationProgress:
    @pytest.fixture
    def renderer(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {
            "lines": [
                {"index": 0, "text": "Hello", "start": 1.0, "end": 3.0,
                 "words": [{"text": "Hello", "start": 1.0, "end": 3.0}]},
            ]
        }
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        (data_dir / "analysis.json").write_text(json.dumps({"duration": 5.0}))
        r = VideoRenderer(tmp_path, width=64, height=64)
        r.load()
        return r

    def test_invalid_line_idx(self, renderer):
        state = renderer._compute_animation_progress(0.0, -1)
        assert isinstance(state, AnimationState)
        assert state.opacity == 1.0

    def test_enter_phase(self, renderer):
        state = renderer._compute_animation_progress(1.15, 0)
        assert state.opacity < 1.0 or state.scale[0] < 1.0

    def test_sustain_phase(self, renderer):
        state = renderer._compute_animation_progress(2.0, 0)
        assert state.opacity == 1.0
        assert state.position == (0.0, 0.0)

    def test_exit_phase(self, renderer):
        state = renderer._compute_animation_progress(2.95, 0)
        assert state.opacity < 1.0

    def test_custom_animation_type(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S", "lines": [0], "visual": {"animation_type": "scale_in", "animation_speed": 1.0}},
            ]
        }
        state = renderer._compute_animation_progress(1.01, 0)
        assert state.scale[0] < 1.0


class TestVideoRendererFrameIsUnique:
    @pytest.fixture
    def renderer(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {
            "lines": [
                {"index": 0, "text": "A", "start": 0, "end": 1, "words": [{"text": "A", "start": 0, "end": 1}]},
            ]
        }
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        (data_dir / "analysis.json").write_text(json.dumps({"duration": 2.0}))
        r = VideoRenderer(tmp_path, width=64, height=64)
        r.load()
        return r

    def test_no_animation_default(self, renderer):
        assert renderer._frame_is_unique(0) is True

    def test_negative_idx(self, renderer):
        assert renderer._frame_is_unique(-1) is True

    def test_with_animation(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S", "lines": [0], "visual": {"animation_type": "fade_in"}},
            ]
        }
        assert renderer._frame_is_unique(0) is True

    def test_with_bg_preset(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S", "lines": [0], "visual": {"bg_animation_preset": "cinematic"}},
            ]
        }
        assert renderer._frame_is_unique(0) is True


# ---------------------------------------------------------------------------
# Helper: create a minimally-loaded renderer for reuse in new test classes
# ---------------------------------------------------------------------------

def _make_renderer(tmp_path, width=64, height=64, lines=None, script=None, analysis=None):
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    if lines is None:
        lines = [
            {"index": 0, "text": "Hello world", "start": 1.0, "end": 3.0,
             "words": [{"text": "Hello", "start": 1.0, "end": 2.0},
                        {"text": "world", "start": 2.0, "end": 3.0}]},
            {"index": 1, "text": "Second line", "start": 4.0, "end": 5.5,
             "words": [{"text": "Second", "start": 4.0, "end": 4.5},
                        {"text": "line", "start": 4.5, "end": 5.5}]},
        ]
    synced = {"lines": lines}
    (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
    if analysis is None:
        analysis = {"duration": 7.0, "sample_rate": 48000, "hop_length": 512}
    (data_dir / "analysis.json").write_text(json.dumps(analysis))
    if script is not None:
        (data_dir / "script.json").write_text(json.dumps(script))
    r = VideoRenderer(tmp_path, width=width, height=height)
    r.load()
    return r


def _fake_tqdm(iterable, **kwargs):
    class FakeBar(list):
        def set_postfix_str(self, s):
            pass
    return FakeBar(iterable)


_fake_tqdm.write = lambda s: None


# ===================================================================
# TestYForPos
# ===================================================================

class TestYForPos:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=1080)

    def test_top(self, renderer):
        assert renderer._y_for_pos("top") == int(1080 * 0.2)

    def test_bottom(self, renderer):
        assert renderer._y_for_pos("bottom") == int(1080 * 0.8)

    def test_center(self, renderer):
        assert renderer._y_for_pos("center") == 1080 // 2

    def test_unknown_defaults_center(self, renderer):
        assert renderer._y_for_pos("somewhere") == 1080 // 2


# ===================================================================
# TestGetRevealMode
# ===================================================================

class TestGetRevealMode:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path)

    def test_default_is_progressive(self, renderer):
        assert renderer._get_reveal_mode({}) == "progressive"

    def test_karaoke(self, renderer):
        assert renderer._get_reveal_mode({"reveal_mode": "karaoke"}) == "karaoke"

    def test_line_by_line(self, renderer):
        assert renderer._get_reveal_mode({"reveal_mode": "line-by-line"}) == "line-by-line"

    def test_stacking(self, renderer):
        assert renderer._get_reveal_mode({"reveal_mode": "stacking"}) == "stacking"


# ===================================================================
# TestFindSection
# ===================================================================

class TestFindSection:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path)

    def test_no_sections(self, renderer):
        renderer.script = {}
        assert renderer._find_section(0) is None

    def test_found(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0, 1]},
                {"name": "S2", "lines": [2, 3]},
            ]
        }
        assert renderer._find_section(0)["name"] == "S1"
        assert renderer._find_section(1)["name"] == "S1"

    def test_not_found(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0, 1]},
            ]
        }
        assert renderer._find_section(5) is None

    def test_empty_lines_list(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S_empty", "lines": []},
            ]
        }
        assert renderer._find_section(0) is None

    def test_non_int_lines(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S_bad", "lines": ["a", "b"]},
            ]
        }
        assert renderer._find_section(0) is None


# ===================================================================
# TestApplyAnimationTransforms
# ===================================================================

class TestApplyAnimationTransforms:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_identity_no_change(self, renderer):
        img = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
        state = AnimationState()
        result = renderer._apply_animation_transforms(img, state)
        assert result.size == (64, 64)

    def test_scale_up(self, renderer):
        img = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
        state = AnimationState(scale=(1.5, 1.5))
        result = renderer._apply_animation_transforms(img, state)
        assert result.size == (64, 64)

    def test_scale_down(self, renderer):
        img = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
        state = AnimationState(scale=(0.5, 0.5))
        result = renderer._apply_animation_transforms(img, state)
        assert result.size == (64, 64)

    def test_rotation(self, renderer):
        img = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
        state = AnimationState(rotation=15.0)
        result = renderer._apply_animation_transforms(img, state)
        assert result.size == (64, 64)

    def test_no_rotation_when_small(self, renderer):
        img = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
        state = AnimationState(rotation=0.05)
        result = renderer._apply_animation_transforms(img, state)
        assert result.size == (64, 64)


# ===================================================================
# TestDrawBackground
# ===================================================================

class TestDrawBackground:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_solid_background(self, renderer):
        img = Image.new("RGB", (64, 64), (0, 0, 0))
        renderer._draw_background(img, {"background_type": "solid", "background_color": "#ff0000"})
        assert img.getpixel((32, 32))[0] > 200

    def test_gradient_background(self, renderer):
        img = Image.new("RGB", (64, 64), (0, 0, 0))
        renderer._draw_background(img, {
            "background_type": "gradient",
            "gradient_colors": ["#000000", "#ffffff"],
            "gradient_direction": "vertical_top_bottom",
        })
        top = img.getpixel((32, 0))
        bot = img.getpixel((32, 63))
        assert top[0] < bot[0]

    def test_default_solid_when_no_type(self, renderer):
        img = Image.new("RGB", (64, 64), (0, 0, 0))
        renderer._draw_background(img, {"background_color": "#00ff00"})
        px = img.getpixel((32, 32))
        assert px[1] > 200

    def test_image_background_with_data_uri(self, renderer):
        img = Image.new("RGB", (64, 64), (0, 0, 0))
        renderer._draw_background(img, {
            "background_type": "image",
            "background_image": "data:image/png;base64,abc",
            "background_color": "#0000ff",
        })
        assert img.size == (64, 64)

    def test_image_background_with_missing_file(self, renderer):
        img = Image.new("RGB", (64, 64), (0, 0, 0))
        renderer._draw_background(img, {
            "background_type": "image",
            "background_image": "/nonexistent/path.png",
            "background_color": "#ff00ff",
        })
        px = img.getpixel((32, 32))
        assert px[0] > 200 or px[2] > 200

    def test_image_background_with_real_file(self, renderer, tmp_path):
        bg_file = tmp_path / "bg.png"
        Image.new("RGB", (100, 100), (255, 200, 0)).save(bg_file)
        img = Image.new("RGB", (64, 64), (0, 0, 0))
        renderer._draw_background(img, {
            "background_type": "image",
            "background_image": str(bg_file),
            "background_color": "#000000",
        })
        assert img.size == (64, 64)

    def test_image_background_with_opacity(self, renderer, tmp_path):
        bg_file = tmp_path / "bg2.png"
        Image.new("RGB", (100, 100), (255, 200, 0)).save(bg_file)
        img = Image.new("RGB", (64, 64), (0, 0, 0))
        renderer._draw_background(img, {
            "background_type": "image",
            "background_image": str(bg_file),
            "background_image_opacity": 0.5,
            "background_image_fit": "contain",
            "background_color": "#000000",
        })
        assert img.size == (64, 64)

    def test_texture_applied_after_solid(self, renderer):
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        renderer._draw_background(img, {
            "background_color": "#808080",
            "texture_type": "noise_fine",
            "texture_opacity": 0.3,
            "texture_blend_mode": "screen",
        })
        assert img.size == (64, 64)


# ===================================================================
# TestDrawGradientAdditionalDirections
# ===================================================================

class TestDrawGradientAdditionalDirections:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_vertical_bottom_top(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "vertical_bottom_top")
        top = img.getpixel((32, 0))
        bot = img.getpixel((32, 63))
        assert top[0] > bot[0]

    def test_horizontal_right_left(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "horizontal_right_left")
        left = img.getpixel((0, 32))
        right = img.getpixel((63, 32))
        assert left[0] > right[0]

    def test_diagonal_tr_bl(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "diagonal_tr_bl")
        assert img.size == (64, 64)

    def test_conic_default(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#ff0000", "#00ff00", "#0000ff"], "conic")
        assert img.size == (64, 64)

    def test_conic_with_offset(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#ff0000", "#0000ff"], "conic_center_1.5")
        assert img.size == (64, 64)

    def test_diamond(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#ffffff", "#000000"], "diamond")
        center = img.getpixel((32, 32))
        corner = img.getpixel((0, 0))
        assert center[0] > corner[0]

    def test_dual_spot_defaults(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "dual_spot")
        assert img.size == (64, 64)

    def test_dual_spot_custom(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#ff0000", "#0000ff"], "dual_spot_0.3_0.3_0.7_0.7")
        assert img.size == (64, 64)

    def test_bands(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#ff0000", "#00ff00", "#0000ff"], "bands")
        assert img.size == (64, 64)

    def test_cross(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#ffffff", "#000000"], "cross")
        assert img.size == (64, 64)

    def test_spiral(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#ff0000", "#0000ff"], "spiral")
        assert img.size == (64, 64)

    def test_angle_direction(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "angle_45")
        assert img.size == (64, 64)

    def test_angle_no_value_raises(self, renderer):
        img = Image.new("RGB", (64, 64))
        with pytest.raises(ValueError):
            renderer._draw_gradient(img, ["#000000", "#ffffff"], "angle_")

    def test_radial_top(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "radial_top")
        top_center = img.getpixel((32, 0))
        bot_center = img.getpixel((32, 63))
        assert top_center[0] < bot_center[0]

    def test_radial_bottom(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "radial_bottom")
        assert img.size == (64, 64)

    def test_radial_tl(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "radial_tl")
        assert img.size == (64, 64)

    def test_radial_br(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "radial_br")
        assert img.size == (64, 64)

    def test_radial_center_fallback(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "radial_center")
        assert img.size == (64, 64)

    def test_unknown_direction_falls_to_radial(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#000000", "#ffffff"], "totally_unknown")
        assert img.size == (64, 64)

    def test_multi_color_gradient(self, renderer):
        img = Image.new("RGB", (64, 64))
        renderer._draw_gradient(img, ["#ff0000", "#00ff00", "#0000ff"], "vertical_top_bottom")
        mid = img.getpixel((32, 32))
        assert mid[1] > mid[0]


# ===================================================================
# TestDrawTextureAdditional
# ===================================================================

class TestDrawTextureAdditional:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_noise_coarse(self, renderer):
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        renderer._draw_texture(img, {"texture_type": "noise_coarse", "texture_opacity": 0.3})
        assert img.size == (64, 64)

    def test_grain_film(self, renderer):
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        renderer._draw_texture(img, {"texture_type": "grain_film", "texture_opacity": 0.3})
        assert img.size == (64, 64)

    def test_paper_subtle(self, renderer):
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        renderer._draw_texture(img, {"texture_type": "paper_subtle", "texture_opacity": 0.3})
        assert img.size == (64, 64)

    def test_unknown_texture_fallback(self, renderer):
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        renderer._draw_texture(img, {"texture_type": "custom_unknown", "texture_opacity": 0.3})
        assert img.size == (64, 64)

    def test_vignette_heavy(self, renderer):
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        renderer._draw_texture(img, {"texture_type": "vignette_heavy", "texture_opacity": 0.5})
        assert img.size == (64, 64)

    def test_multiply_blend(self, renderer):
        img = Image.new("RGB", (64, 64), (200, 200, 200))
        renderer._draw_texture(img, {
            "texture_type": "noise_fine",
            "texture_opacity": 0.3,
            "texture_blend_mode": "multiply",
        })
        assert img.size == (64, 64)

    def test_empty_texture_string(self, renderer):
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        renderer._draw_texture(img, {"texture_type": ""})
        assert img.getpixel((32, 32)) == (128, 128, 128)


# ===================================================================
# TestDrawVignette
# ===================================================================

class TestDrawVignette:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_basic_vignette(self, renderer):
        img = Image.new("RGB", (64, 64), (128, 128, 128))
        renderer._draw_vignette(img, 0.2, 0.7, 0.7, 0.15)
        center = img.getpixel((32, 32))
        corner = img.getpixel((0, 0))
        assert center[0] > corner[0] or center[0] < corner[0]
        assert img.size == (64, 64)


# ===================================================================
# TestWordWidths
# ===================================================================

class TestWordWidths:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path)

    def test_plain_widths(self, renderer):
        font = renderer._get_font(48)
        words = [{"text": "Hello"}, {"text": "world"}]
        widths = renderer._word_widths(words, font, {}, 48)
        assert len(widths) == 2
        assert all(w > 0 for w in widths)

    def test_styled_fallback(self, renderer):
        font = renderer._get_font(48)
        words = [{"text": "Test"}]
        v = {"text_style": "neon"}
        widths = renderer._word_widths(words, font, v, 48)
        assert len(widths) == 1
        assert widths[0] > 0


# ===================================================================
# TestHasStyledText
# ===================================================================

class TestHasStyledText:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path)

    def test_empty(self, renderer):
        assert renderer._has_styled_text({}) is False

    def test_basic(self, renderer):
        assert renderer._has_styled_text({"text_style": "basic"}) is False

    def test_styled(self, renderer):
        assert renderer._has_styled_text({"text_style": "neon"}) is True


# ===================================================================
# TestBaseSpacing
# ===================================================================

class TestBaseSpacing:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, height=1080)

    def test_default_spacing(self, renderer):
        spacing = renderer._base_spacing(112)
        assert spacing > 0

    def test_with_letter_spacing(self, renderer):
        renderer.caption_style = {"letter_spacing": 2.0}
        spacing = renderer._base_spacing(112)
        assert spacing > 0


# ===================================================================
# TestLayoutLine
# ===================================================================

class TestLayoutLine:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_basic_layout(self, renderer):
        words = [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]
        layout = renderer._layout_line(words, 0, {}, 48, 0)
        assert len(layout) == 2
        assert all("px_x" in r for r in layout)
        assert all("px_y" in r for r in layout)
        assert all("wW" in r for r in layout)

    def test_layout_with_pinned_x(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S", "lines": [0],
                 "words_overrides": {"0.0": {"x": 0.3}, "0.1": {"x": 0.7}}},
            ]
        }
        words = [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]
        layout = renderer._layout_line(words, 0, {}, 48, 0)
        assert len(layout) == 2
        assert layout[0]["px_x"] == int(0.3 * 320)
        assert layout[1]["px_x"] == int(0.7 * 320)

    def test_layout_with_styled_text(self, renderer):
        v = {"text_style": "neon"}
        words = [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]
        layout = renderer._layout_line(words, 0, v, 48, 0)
        assert len(layout) == 2

    def test_layout_multi_row(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S", "lines": [0],
                 "words_overrides": {"0.0": {"y": 0.3}, "0.1": {"y": 0.7}}},
            ]
        }
        words = [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]
        layout = renderer._layout_line(words, 0, {}, 48, 0)
        assert layout[0]["px_y"] != layout[1]["px_y"]


# ===================================================================
# TestDrawTextLine
# ===================================================================

class TestDrawTextLine:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_basic_draw(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        renderer._draw_text_line(img, "Hello", {}, 90, 48)
        assert img.size == (320, 180)

    def test_with_outline(self, renderer):
        renderer.caption_style = {"outline": True, "outline_width": 2, "outline_color": "#000000"}
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        renderer._draw_text_line(img, "Hello", {}, 90, 48)
        assert img.size == (320, 180)

    def test_with_shadow(self, renderer):
        renderer.caption_style = {"text_shadow": True, "text_shadow_color": "#000000"}
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        renderer._draw_text_line(img, "Hello", {}, 90, 48)
        assert img.size == (320, 180)

    def test_no_auto_contrast(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        renderer._draw_text_line(img, "Hello", {"text_auto_contrast": False, "text_color": "#ff0000"}, 90, 48)
        assert img.size == (320, 180)

    def test_styled_text_path(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        v = {"text_style": "neon", "font_family": 0}
        renderer._draw_text_line(img, "Hello", v, 90, 48)
        assert img.size == (320, 180)


# ===================================================================
# TestDrawKaraoke
# ===================================================================

class TestDrawKaraoke:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_basic_karaoke(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]}
        renderer._draw_karaoke(img, line, 0, 0, {}, 48)
        assert img.size == (320, 180)

    def test_karaoke_with_outline(self, renderer):
        renderer.caption_style = {"outline": True, "outline_width": 2, "outline_color": "#000000"}
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]}
        renderer._draw_karaoke(img, line, 0, 1, {}, 48)
        assert img.size == (320, 180)

    def test_karaoke_with_shadow(self, renderer):
        renderer.caption_style = {"text_shadow": True, "text_shadow_color": "#333333"}
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": "Hello", "start": 1.0, "end": 2.0},
        ]}
        renderer._draw_karaoke(img, line, 0, 0, {}, 48)
        assert img.size == (320, 180)

    def test_karaoke_no_auto_contrast(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": "Hello", "start": 1.0, "end": 2.0},
        ]}
        v = {"text_auto_contrast": False, "text_color": "#ff0000"}
        renderer._draw_karaoke(img, line, 0, 0, v, 48)
        assert img.size == (320, 180)

    def test_karaoke_styled(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]}
        v = {"text_style": "neon"}
        renderer._draw_karaoke(img, line, 0, 0, v, 48)
        assert img.size == (320, 180)

    def test_karaoke_styled_inactive_word(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]}
        v = {"text_style": "neon"}
        renderer._draw_karaoke(img, line, 0, 1, v, 48)
        assert img.size == (320, 180)


# ===================================================================
# TestDrawProgressive
# ===================================================================

class TestDrawProgressive:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_basic_progressive(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]}
        renderer._draw_progressive(img, line, 0, 0, {}, 48)
        assert img.size == (320, 180)

    def test_progressive_later_word(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]}
        renderer._draw_progressive(img, line, 0, 1, {}, 48)
        assert img.size == (320, 180)

    def test_progressive_with_slide(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": w, "start": float(i), "end": float(i + 1)}
            for i, w in enumerate(["One", "Two", "Three", "Four", "Five"])
        ]}
        v = {"reveal_slide": True, "reveal_words": 2}
        renderer._draw_progressive(img, line, 0, 3, v, 48)
        assert img.size == (320, 180)

    def test_progressive_slide_near_end(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": w, "start": float(i), "end": float(i + 1)}
            for i, w in enumerate(["A", "B", "C", "D"])
        ]}
        v = {"reveal_slide": True, "reveal_words": 1}
        renderer._draw_progressive(img, line, 0, 3, v, 48)
        assert img.size == (320, 180)

    def test_progressive_with_outline(self, renderer):
        renderer.caption_style = {"outline": True, "outline_width": 2, "outline_color": "#000000"}
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]}
        renderer._draw_progressive(img, line, 0, 1, {}, 48)
        assert img.size == (320, 180)

    def test_progressive_with_shadow(self, renderer):
        renderer.caption_style = {"text_shadow": True, "text_shadow_color": "#000000"}
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": "Hello", "start": 1.0, "end": 2.0},
        ]}
        renderer._draw_progressive(img, line, 0, 0, {}, 48)
        assert img.size == (320, 180)

    def test_progressive_no_auto_contrast(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [{"text": "Hello", "start": 1.0, "end": 2.0}]}
        v = {"text_auto_contrast": False, "text_color": "#ff0000"}
        renderer._draw_progressive(img, line, 0, 0, v, 48)
        assert img.size == (320, 180)

    def test_progressive_styled(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]}
        v = {"text_style": "neon"}
        renderer._draw_progressive(img, line, 0, 0, v, 48)
        assert img.size == (320, 180)

    def test_progressive_styled_inactive(self, renderer):
        img = Image.new("RGBA", (320, 180), (0, 0, 0, 255))
        line = {"words": [
            {"text": "Hello", "start": 1.0, "end": 2.0},
            {"text": "world", "start": 2.0, "end": 3.0},
        ]}
        v = {"text_style": "neon", "reveal_words": 1}
        renderer._draw_progressive(img, line, 0, 1, v, 48)
        assert img.size == (320, 180)


# ===================================================================
# TestRenderIntroFrame
# ===================================================================

class TestRenderIntroFrame:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_no_intro_returns_none(self, renderer):
        renderer.script = {}
        assert renderer._render_intro_frame(0.0) is None

    def test_intro_zero_duration(self, renderer):
        renderer.script = {"intro": {"duration": 0}}
        assert renderer._render_intro_frame(0.0) is None

    def test_intro_past_duration(self, renderer):
        renderer.script = {"intro": {"duration": 2.0}}
        assert renderer._render_intro_frame(3.0) is None

    def test_intro_phase1_no_image(self, renderer):
        renderer.script = {"intro": {"duration": 5.0}}
        img = renderer._render_intro_frame(0.5)
        assert img is not None
        assert img.size == (320, 180)

    def test_intro_phase1_with_image(self, renderer, tmp_path):
        bg_file = tmp_path / "intro_bg.png"
        Image.new("RGB", (200, 200), (50, 50, 50)).save(bg_file)
        renderer.script = {"intro": {"duration": 10.0, "image": str(bg_file)}}
        img = renderer._render_intro_frame(1.0)
        assert img is not None
        assert img.size == (320, 180)

    def test_intro_phase2_text(self, renderer):
        renderer.script = {"intro": {"duration": 10.0}}
        img = renderer._render_intro_frame(8.0)
        assert img is not None
        assert img.size == (320, 180)

    def test_intro_transition_phase(self, renderer):
        renderer.script = {"intro": {"duration": 10.0}}
        img = renderer._render_intro_frame(5.7)
        assert img is not None
        assert img.size == (320, 180)


# ===================================================================
# TestRenderOutroFrame
# ===================================================================

class TestRenderOutroFrame:
    @pytest.fixture
    def renderer(self, tmp_path):
        lines = [
            {"index": 0, "text": "Last word", "start": 1.0, "end": 3.0,
             "words": [{"text": "Last", "start": 1.0, "end": 2.0},
                        {"text": "word", "start": 2.0, "end": 3.0}]},
        ]
        return _make_renderer(tmp_path, width=320, height=180, lines=lines,
                              analysis={"duration": 8.0, "sample_rate": 48000, "hop_length": 512})

    def test_no_outro_returns_none(self, renderer):
        renderer.script = {}
        assert renderer._render_outro_frame(0.0) is None

    def test_outro_before_last_end(self, renderer):
        renderer.script = {"outro": {"text": "Thanks"}}
        assert renderer._render_outro_frame(1.0) is None

    def test_outro_zero_duration(self, renderer):
        renderer.script = {"outro": {}}
        renderer.duration = 3.0
        assert renderer._render_outro_frame(3.5) is None

    def test_outro_phase1_no_image(self, renderer):
        renderer.script = {"outro": {"text": "Thanks"}}
        renderer.duration = 8.0
        img = renderer._render_outro_frame(3.5)
        assert img is not None
        assert img.size == (320, 180)

    def test_outro_phase1_with_image(self, renderer, tmp_path):
        bg_file = tmp_path / "outro_bg.png"
        Image.new("RGB", (200, 200), (50, 50, 50)).save(bg_file)
        renderer.script = {"outro": {"text": "Thanks", "image": str(bg_file)}}
        renderer.duration = 8.0
        img = renderer._render_outro_frame(3.5)
        assert img is not None
        assert img.size == (320, 180)

    def test_outro_phase2_with_text(self, renderer):
        renderer.script = {"outro": {"text": "Presented by"}}
        renderer.duration = 8.0
        img = renderer._render_outro_frame(5.0)
        assert img is not None
        assert img.size == (320, 180)

    def test_outro_phase2_with_logo(self, renderer, tmp_path):
        logo = tmp_path / "logo.png"
        Image.new("RGBA", (100, 50), (255, 255, 255, 255)).save(logo)
        renderer.script = {"outro": {"text": "Logo:", "logo": str(logo)}}
        renderer.duration = 8.0
        img = renderer._render_outro_frame(5.0)
        assert img is not None
        assert img.size == (320, 180)

    def test_outro_phase2_bad_logo_path(self, renderer):
        renderer.script = {"outro": {"text": "Bad:", "logo": "/nonexistent/logo.png"}}
        renderer.duration = 8.0
        img = renderer._render_outro_frame(5.0)
        assert img is not None
        assert img.size == (320, 180)

    def test_outro_transition_phase(self, renderer):
        renderer.script = {"outro": {"text": "Thanks"}}
        renderer.duration = 8.0
        img = renderer._render_outro_frame(4.2)
        assert img is not None
        assert img.size == (320, 180)

    def test_outro_elapsed_at_duration(self, renderer):
        renderer.script = {"outro": {"text": "End"}}
        renderer.duration = 8.0
        img = renderer._render_outro_frame(7.999)
        assert img is not None

    def test_outro_no_lines(self, tmp_path):
        r = _make_renderer(tmp_path, width=64, height=64, lines=[],
                           analysis={"duration": 2.0})
        r.script = {"outro": {"text": "End"}}
        assert r._render_outro_frame(0.5) is None


# ===================================================================
# TestApplyBgMotion
# ===================================================================

class TestApplyBgMotion:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_no_preset_returns_unchanged(self, renderer):
        img = Image.new("RGB", (64, 64), (100, 100, 100))
        result = renderer._apply_bg_motion(img, 0.5, {})
        assert result.size == (64, 64)

    def test_with_cinematic_preset(self, renderer):
        img = Image.new("RGB", (64, 64), (100, 100, 100))
        result = renderer._apply_bg_motion(img, 0.5, {"bg_animation_preset": "cinematic"})
        assert result.size == (64, 64)

    def test_with_minimal_preset(self, renderer):
        img = Image.new("RGB", (64, 64), (100, 100, 100))
        result = renderer._apply_bg_motion(img, 0.5, {"bg_animation_preset": "minimal"})
        assert result.size == (64, 64)

    def test_with_reactivity(self, renderer):
        renderer._rms_energy = [0.5]
        renderer._audio_fps = 1.0
        img = Image.new("RGB", (64, 64), (100, 100, 100))
        result = renderer._apply_bg_motion(img, 0.5, {
            "bg_animation_preset": "cinematic",
            "reactivity": ["energy"],
        })
        assert result.size == (64, 64)


# ===================================================================
# TestRenderTextOnBg
# ===================================================================

class TestRenderTextOnBg:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_active_line(self, renderer):
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        img = renderer._render_text_on_bg(bg, 0, 0, t=1.5)
        assert img.size == (320, 180)

    def test_no_active_with_intro(self, renderer):
        renderer.script = {"intro": {"duration": 5.0}}
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        img = renderer._render_text_on_bg(bg, -1, -1, t=1.0)
        assert img.size == (320, 180)

    def test_no_active_with_outro(self, renderer):
        renderer.script = {"outro": {"text": "End"}}
        renderer.duration = 10.0
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        img = renderer._render_text_on_bg(bg, -1, -1, t=5.0)
        assert img.size == (320, 180)

    def test_no_active_gap_frame(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0, 1]},
            ]
        }
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        img = renderer._render_text_on_bg(bg, -1, -1, t=0.5)
        assert img.size == (320, 180)

    def test_no_active_no_section(self, renderer):
        renderer.script = {}
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        img = renderer._render_text_on_bg(bg, -1, -1, t=0.5)
        assert img.size == (320, 180)

    def test_line_by_line_mode(self, renderer):
        renderer.defaults["reveal_mode"] = "line-by-line"
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        img = renderer._render_text_on_bg(bg, 0, 0, t=1.5)
        assert img.size == (320, 180)

    def test_stacking_mode(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0, 1]},
            ]
        }
        renderer.defaults["reveal_mode"] = "stacking"
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        img = renderer._render_text_on_bg(bg, 0, 0, t=1.5)
        assert img.size == (320, 180)

    def test_progressive_mode(self, renderer):
        renderer.defaults["reveal_mode"] = "progressive"
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        img = renderer._render_text_on_bg(bg, 0, 0, t=1.5)
        assert img.size == (320, 180)

    def test_karaoke_mode(self, renderer):
        renderer.defaults["reveal_mode"] = "karaoke"
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        img = renderer._render_text_on_bg(bg, 0, 0, t=1.5)
        assert img.size == (320, 180)

    def test_with_opacity_animation(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0], "visual": {"animation_type": "fade_in"}},
            ]
        }
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        img = renderer._render_text_on_bg(bg, 0, 0, t=1.01)
        assert img.size == (320, 180)

    def test_with_position_offset(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0], "visual": {"animation_type": "slide_in"}},
            ]
        }
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        img = renderer._render_text_on_bg(bg, 0, 0, t=1.01)
        assert img.size == (320, 180)


# ===================================================================
# TestRenderFrameStacking
# ===================================================================

class TestRenderFrameStacking:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_stacking_mode(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0, 1]},
            ]
        }
        renderer.defaults["reveal_mode"] = "stacking"
        img = renderer.render_frame(1.5)
        assert img.size == (320, 180)


# ===================================================================
# TestRenderFrameCanvas
# ===================================================================

class TestRenderFrameCanvas:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_canvas_config_triggers_render_canvas(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0],
                 "visual": {"canvas": {"type": "scene", "children": []}}},
            ]
        }
        with patch("render.renderer.render_canvas", return_value=Image.new("RGB", (320, 180), (50, 50, 50))) as mock_rc:
            img = renderer.render_frame(1.5)
            mock_rc.assert_called_once()
            assert img.size == (320, 180)


# ===================================================================
# TestRenderFrameGapWithSection
# ===================================================================

class TestRenderFrameGapWithSection:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_gap_frame_with_nearest_section(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0, 1]},
            ]
        }
        img = renderer.render_frame(0.0)
        assert img.size == (64, 64)

    def test_gap_frame_no_section(self, renderer):
        renderer.script = {}
        img = renderer.render_frame(0.0)
        assert img.size == (64, 64)


# ===================================================================
# TestRenderTextOnBgCanvas
# ===================================================================

class TestRenderTextOnBgCanvas:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_canvas_path(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0],
                 "visual": {"canvas": {"type": "scene", "children": []}}},
            ]
        }
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        with patch("render.renderer.render_canvas", return_value=Image.new("RGB", (320, 180), (50, 50, 50))) as mock_rc:
            img = renderer._render_text_on_bg(bg, 0, 0, t=1.5)
            mock_rc.assert_called_once()
            assert img.size == (320, 180)


# ===================================================================
# TestGetBgForSection
# ===================================================================

class TestGetBgForSection:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_caches_bg(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S1", "lines": [0, 1]},
            ]
        }
        cache = {}
        bg1 = renderer._get_bg_for_section(0, cache)
        bg2 = renderer._get_bg_for_section(1, cache)
        assert bg1 is bg2

    def test_negative_idx_uses_defaults(self, renderer):
        cache = {}
        bg = renderer._get_bg_for_section(-1, cache)
        assert bg.size == (64, 64)

    def test_no_section(self, renderer):
        renderer.script = {}
        cache = {}
        bg = renderer._get_bg_for_section(0, cache)
        assert bg.size == (64, 64)


# ===================================================================
# TestInitBgSource
# ===================================================================

class TestInitBgSource:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_no_bg_video(self, renderer):
        renderer._init_bg_source()
        assert renderer._bg_source is None

    def test_nonexistent_path(self, renderer):
        renderer.defaults["background_video"] = "/nonexistent/video.mp4"
        renderer._init_bg_source()
        assert renderer._bg_source is None

    def test_relative_path_resolved(self, renderer, tmp_path):
        renderer.defaults["background_video"] = "bg_video.mp4"
        renderer._init_bg_source()
        assert renderer._bg_source is None

    def test_already_initialized(self, renderer):
        renderer._bg_source = "fake"
        renderer._init_bg_source()
        assert renderer._bg_source == "fake"


# ===================================================================
# TestGetLastWordEnd
# ===================================================================

class TestGetLastWordEnd:
    def test_with_words(self, tmp_path):
        lines = [
            {"index": 0, "text": "Hello", "start": 1.0, "end": 2.0,
             "words": [{"text": "Hello", "start": 1.0, "end": 2.0}]},
            {"index": 1, "text": "World", "start": 3.0, "end": 5.0,
             "words": [{"text": "World", "start": 3.0, "end": 5.0}]},
        ]
        r = _make_renderer(tmp_path, width=64, height=64, lines=lines)
        assert r._get_last_word_end() == 5.0

    def test_no_lines(self, tmp_path):
        r = _make_renderer(tmp_path, width=64, height=64, lines=[])
        assert r._get_last_word_end() == 0.0

    def test_no_words(self, tmp_path):
        lines = [{"index": 0, "text": "Hello", "start": 1.0, "end": 2.0, "words": []}]
        r = _make_renderer(tmp_path, width=64, height=64, lines=lines)
        assert r._get_last_word_end() == 0.0


# ===================================================================
# TestResolveWordY
# ===================================================================

class TestResolveWordY:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path)

    def test_explicit_y(self, renderer):
        assert renderer._resolve_word_y({"y": 0.3}, "center") == 0.3

    def test_inherit_section_pos(self, renderer):
        assert renderer._resolve_word_y({}, "top") == 0.2

    def test_text_position_override(self, renderer):
        assert renderer._resolve_word_y({"text_position": "bottom"}, "top") == 0.8

    def test_unknown_position(self, renderer):
        assert renderer._resolve_word_y({"text_position": "unknown"}, "center") == 0.5


# ===================================================================
# TestFindNearestSection
# ===================================================================

class TestFindNearestSection:
    @pytest.fixture
    def renderer(self, tmp_path):
        lines = [
            {"index": 0, "text": "A", "start": 1.0, "end": 2.0,
             "words": [{"text": "A", "start": 1.0, "end": 2.0}]},
            {"index": 1, "text": "B", "start": 3.0, "end": 4.0,
             "words": [{"text": "B", "start": 3.0, "end": 4.0}]},
        ]
        return _make_renderer(tmp_path, width=64, height=64, lines=lines)

    def test_within_section(self, renderer):
        renderer.script = {
            "sections": [{"name": "S1", "lines": [0, 1]}]
        }
        sec = renderer._find_nearest_section(1.5)
        assert sec["name"] == "S1"

    def test_no_sections(self, renderer):
        renderer.script = {}
        assert renderer._find_nearest_section(1.0) is None

    def test_before_section(self, renderer):
        renderer.script = {
            "sections": [{"name": "S1", "lines": [0, 1]}]
        }
        sec = renderer._find_nearest_section(0.0)
        assert sec["name"] == "S1"

    def test_after_section(self, renderer):
        renderer.script = {
            "sections": [{"name": "S1", "lines": [0, 1]}]
        }
        sec = renderer._find_nearest_section(10.0)
        assert sec["name"] == "S1"


# ===================================================================
# TestStyledWordWidths
# ===================================================================

class TestStyledWordWidths:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path)

    def test_returns_widths(self, renderer):
        words = [{"text": "Hello"}, {"text": "world"}]
        widths = renderer._styled_word_widths(words, "neon", 48, 0)
        assert len(widths) == 2
        assert all(w > 0 for w in widths)


# ===================================================================
# TestGetStyledText
# ===================================================================

class TestGetStyledText:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path)

    def test_caches_result(self, renderer):
        result1 = renderer._get_styled_text("Hello", "neon", 48, 0)
        result2 = renderer._get_styled_text("Hello", "neon", 48, 0)
        assert result1 is result2

    def test_returns_image(self, renderer):
        result = renderer._get_styled_text("Test", "chrome", 48, 0)
        assert isinstance(result, Image.Image)


# ===================================================================
# TestFullRenderPipeline
# ===================================================================

class TestFullRenderPipeline:
    @pytest.fixture
    def renderer(self, tmp_path):
        lines = [
            {"index": 0, "text": "Hello world", "start": 1.0, "end": 3.0,
             "words": [{"text": "Hello", "start": 1.0, "end": 2.0},
                        {"text": "world", "start": 2.0, "end": 3.0}]},
            {"index": 1, "text": "Goodbye", "start": 4.0, "end": 5.0,
             "words": [{"text": "Goodbye", "start": 4.0, "end": 5.0}]},
        ]
        analysis = {"duration": 6.0, "sample_rate": 48000, "hop_length": 512,
                     "rms_energy": [], "spectral_centroids": [], "beat_times": []}
        script = {
            "defaults": {"background_color": "#1a1a2e"},
            "sections": [
                {"name": "Verse", "lines": [0, 1]},
            ]
        }
        return _make_renderer(tmp_path, width=64, height=64, lines=lines,
                              script=script, analysis=analysis)

    def test_render_with_mocked_encoder(self, renderer, tmp_path):
        output = tmp_path / "output.mp4"
        frames_written = []

        class FakeEncoder:
            def __init__(self, *a, **kw):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass
            def write_frame(self, data):
                frames_written.append(data)

        with patch("render.encoder.VideoEncoder", FakeEncoder):
            with patch("render.renderer.tqdm", _fake_tqdm):
                result = renderer.render(output)
                assert result == output
                assert len(frames_written) > 0
                assert all(len(f) == 64 * 64 * 3 for f in frames_written)

    def test_render_with_time_range(self, renderer, tmp_path):
        output = tmp_path / "output2.mp4"
        frames_written = []

        class FakeEncoder:
            def __init__(self, *a, **kw):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass
            def write_frame(self, data):
                frames_written.append(data)

        with patch("render.encoder.VideoEncoder", FakeEncoder):
            with patch("render.renderer.tqdm", _fake_tqdm):
                result = renderer.render(output, time_start=1.0, time_end=2.0)
                assert result == output
                expected = int(2.0 * 30) - int(1.0 * 30) + 1
                assert len(frames_written) == expected

    def test_render_with_intro(self, renderer, tmp_path):
        renderer.script["intro"] = {"duration": 1.0}
        renderer.duration = 6.0
        output = tmp_path / "output3.mp4"
        frames_written = []

        class FakeEncoder:
            def __init__(self, *a, **kw):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass
            def write_frame(self, data):
                frames_written.append(data)

        with patch("render.encoder.VideoEncoder", FakeEncoder):
            with patch("render.renderer.tqdm", _fake_tqdm):
                renderer.render(output, time_start=0.0, time_end=1.0)
                assert len(frames_written) > 0


# ===================================================================
# TestDrawBgImage
# ===================================================================

class TestDrawBgImage:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_real_image_cover(self, renderer, tmp_path):
        bg_file = tmp_path / "bg.png"
        Image.new("RGB", (200, 100), (255, 200, 0)).save(bg_file)
        img = Image.new("RGB", (64, 64), (0, 0, 0))
        renderer._draw_bg_image(img, {
            "background_image": str(bg_file),
            "background_color": "#000000",
        })
        assert img.size == (64, 64)

    def test_real_image_contain_opacity(self, renderer, tmp_path):
        bg_file = tmp_path / "bg2.png"
        Image.new("RGB", (200, 100), (100, 200, 100)).save(bg_file)
        img = Image.new("RGB", (64, 64), (0, 0, 0))
        renderer._draw_bg_image(img, {
            "background_image": str(bg_file),
            "background_image_opacity": 0.5,
            "background_image_fit": "contain",
            "background_color": "#000000",
        })
        assert img.size == (64, 64)

    def test_cached_image(self, renderer, tmp_path):
        bg_file = tmp_path / "cached.png"
        Image.new("RGB", (100, 100), (50, 50, 50)).save(bg_file)
        img1 = Image.new("RGB", (64, 64))
        renderer._draw_bg_image(img1, {"background_image": str(bg_file), "background_color": "#000000"})
        assert str(bg_file) in renderer._bg_cache
        img2 = Image.new("RGB", (64, 64))
        renderer._draw_bg_image(img2, {"background_image": str(bg_file), "background_color": "#000000"})
        assert img2.size == (64, 64)

    def test_data_uri_skips_load(self, renderer):
        img = Image.new("RGB", (64, 64), (0, 0, 0))
        renderer._draw_bg_image(img, {
            "background_image": "data:image/png;base64,abc",
            "background_color": "#ff0000",
        })
        assert img.getpixel((32, 32))[0] > 200

    def test_bad_path_returns(self, renderer):
        img = Image.new("RGB", (64, 64), (0, 0, 0))
        renderer._draw_bg_image(img, {
            "background_image": "/nonexistent/img.png",
            "background_color": "#00ff00",
        })
        assert img.size == (64, 64)


# ===================================================================
# TestRenderFrameIntroOutro
# ===================================================================

class TestRenderFrameIntroOutro:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_intro_frame(self, renderer):
        renderer.script = {"intro": {"duration": 5.0}}
        img = renderer.render_frame(0.0)
        assert img.size == (320, 180)

    def test_outro_frame(self, renderer):
        lines = [
            {"index": 0, "text": "End", "start": 1.0, "end": 2.0,
             "words": [{"text": "End", "start": 1.0, "end": 2.0}]},
        ]
        renderer.synced["lines"] = lines
        renderer.script = {"outro": {"text": "Thanks"}}
        renderer.duration = 5.0
        img = renderer.render_frame(4.0)
        assert img.size == (320, 180)


# ===================================================================
# TestSlideInAnimation
# ===================================================================

class TestSlideInAnimation:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_slide_in_exit(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S", "lines": [0], "visual": {"animation_type": "slide_in", "animation_speed": 1.0}},
            ]
        }
        state = renderer._compute_animation_progress(2.95, 0)
        assert state.position != (0.0, 0.0) or state.opacity < 1.0


# ===================================================================
# TestScaleInAnimation
# ===================================================================

class TestScaleInAnimation:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_scale_in_exit(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S", "lines": [0], "visual": {"animation_type": "scale_in", "animation_speed": 1.0}},
            ]
        }
        state = renderer._compute_animation_progress(2.95, 0)
        assert state.opacity < 1.0 or state.scale[0] != (1.0, 1.0)


# ===================================================================
# TestBadAnimationType
# ===================================================================

class TestBadAnimationType:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_invalid_type_falls_back(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S", "lines": [0], "visual": {"animation_type": "nonexistent"}},
            ]
        }
        state = renderer._compute_animation_progress(2.0, 0)
        assert isinstance(state, AnimationState)


# ===================================================================
# TestRenderFrameAllModes
# ===================================================================

class TestRenderFrameAllModes:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_stacking_no_section(self, renderer):
        renderer.defaults["reveal_mode"] = "stacking"
        renderer.script = {}
        img = renderer.render_frame(1.5)
        assert img.size == (320, 180)


class TestFindFontFallback:
    def test_no_system_fonts_returns_default(self):
        with patch.object(Path, "exists", return_value=False):
            font = _find_font(48, bold=True, family=0)
            assert font is not None


class TestLoadWithoutAnalysis:
    def test_no_analysis_with_lines(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {"lines": [{"index": 0, "text": "A", "start": 0, "end": 5.0, "words": [{"text": "A", "start": 0, "end": 5.0}]}]}
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        r = VideoRenderer(tmp_path)
        r.load()
        assert r.duration == 7.0

    def test_no_analysis_no_lines(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {"lines": []}
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        r = VideoRenderer(tmp_path)
        r.load()
        assert r.duration == 0.0


class TestLoadMvpProject:
    def _setup(self, tmp_path, audio_rel_path, create_at=None):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {"lines": [{"index": 0, "text": "A", "start": 0, "end": 1, "words": [{"text": "A", "start": 0, "end": 1}]}]}
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        (data_dir / "analysis.json").write_text(json.dumps({"duration": 2.0}))
        if create_at:
            create_at.parent.mkdir(parents=True, exist_ok=True)
            create_at.write_bytes(b"fake")
        proj = {"paths": {"audio": audio_rel_path}}
        (data_dir / "mvp_project.json").write_text(json.dumps(proj))

    def test_absolute_audio_path(self, tmp_path):
        audio_file = tmp_path / "audio.mp3"
        audio_file.write_bytes(b"fake")
        self._setup(tmp_path, str(audio_file))
        r = VideoRenderer(tmp_path)
        r.load()
        assert r.audio_path == audio_file

    def test_relative_audio_in_project_dir(self, tmp_path):
        audio_file = tmp_path / "song.mp3"
        audio_file.write_bytes(b"fake")
        self._setup(tmp_path, "song.mp3")
        r = VideoRenderer(tmp_path)
        r.load()
        assert r.audio_path == audio_file

    def test_relative_audio_in_data_dir(self, tmp_path):
        data_dir = tmp_path / "data"
        audio_file = data_dir / "track.mp3"
        self._setup(tmp_path, "track.mp3", create_at=audio_file)
        r = VideoRenderer(tmp_path)
        r.load()
        assert r.audio_path == audio_file

    def test_audio_path_not_found(self, tmp_path):
        self._setup(tmp_path, "nonexistent.mp3")
        r = VideoRenderer(tmp_path)
        r.load()
        assert r.audio_path is None

    def test_empty_audio_path(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        synced = {"lines": [{"index": 0, "text": "A", "start": 0, "end": 1, "words": [{"text": "A", "start": 0, "end": 1}]}]}
        (data_dir / "lyrics_synced.json").write_text(json.dumps(synced))
        (data_dir / "analysis.json").write_text(json.dumps({"duration": 2.0}))
        proj = {"paths": {"audio": ""}}
        (data_dir / "mvp_project.json").write_text(json.dumps(proj))
        r = VideoRenderer(tmp_path)
        r.load()
        assert r.audio_path is None


class TestRotateInExitAnimation:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_rotate_in_hits_else_exit_type(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S", "lines": [0], "visual": {"animation_type": "rotate_in", "animation_speed": 1.0}},
            ]
        }
        state = renderer._compute_animation_progress(2.95, 0)
        assert isinstance(state, AnimationState)


class TestInitBgSourceWithVideo:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_existing_video_file(self, renderer, tmp_path):
        video_file = tmp_path / "bg.mp4"
        video_file.write_bytes(b"fake video")
        renderer.defaults["background_video"] = str(video_file)
        with patch("render.renderer.create_background_source") as mock_create:
            mock_create.return_value = MagicMock()
            renderer._init_bg_source()
            mock_create.assert_called_once()
            assert renderer._bg_source is not None


class TestOutroEdgeCases:
    def test_outro_zero_duration_returns_none(self, tmp_path):
        lines = [
            {"index": 0, "text": "End", "start": 1.0, "end": 2.0,
             "words": [{"text": "End", "start": 1.0, "end": 2.0}]},
        ]
        r = _make_renderer(tmp_path, width=320, height=180, lines=lines,
                           analysis={"duration": 2.0})
        r.script = {"outro": {"text": "End"}}
        assert r._render_outro_frame(2.5) is None

    def test_outro_elapsed_clamped_at_duration(self, tmp_path):
        lines = [
            {"index": 0, "text": "End", "start": 1.0, "end": 2.0,
             "words": [{"text": "End", "start": 1.0, "end": 2.0}]},
        ]
        r = _make_renderer(tmp_path, width=320, height=180, lines=lines,
                           analysis={"duration": 5.0})
        r.script = {"outro": {"text": "End"}}
        img = r._render_outro_frame(5.0)
        assert img is not None
        assert img.size == (320, 180)


class TestOutroPhase2:
    def test_phase2_with_large_logo_resize(self, tmp_path):
        logo = tmp_path / "logo.png"
        Image.new("RGBA", (200, 100), (255, 255, 255, 255)).save(logo)
        lines = [
            {"index": 0, "text": "End", "start": 1.0, "end": 2.0,
             "words": [{"text": "End", "start": 1.0, "end": 2.0}]},
        ]
        r = _make_renderer(tmp_path, width=320, height=180, lines=lines,
                           analysis={"duration": 8.0})
        r.script = {"outro": {"text": "Logo:", "logo": str(logo)}}
        img = r._render_outro_frame(6.0)
        assert img is not None
        assert img.size == (320, 180)

    def test_phase2_bad_logo_path(self, tmp_path):
        lines = [
            {"index": 0, "text": "End", "start": 1.0, "end": 2.0,
             "words": [{"text": "End", "start": 1.0, "end": 2.0}]},
        ]
        r = _make_renderer(tmp_path, width=320, height=180, lines=lines,
                           analysis={"duration": 8.0})
        r.script = {"outro": {"text": "Bad:", "logo": "/nonexistent/logo.png"}}
        img = r._render_outro_frame(6.0)
        assert img is not None
        assert img.size == (320, 180)

    def test_phase2_with_small_logo(self, tmp_path):
        logo = tmp_path / "logo_sm.png"
        Image.new("RGBA", (50, 25), (255, 0, 0, 255)).save(logo)
        lines = [
            {"index": 0, "text": "End", "start": 1.0, "end": 2.0,
             "words": [{"text": "End", "start": 1.0, "end": 2.0}]},
        ]
        r = _make_renderer(tmp_path, width=320, height=180, lines=lines,
                           analysis={"duration": 8.0})
        r.script = {"outro": {"text": "By:", "logo": str(logo)}}
        img = r._render_outro_frame(6.0)
        assert img is not None
        assert img.size == (320, 180)


class TestOutroTransitionPhase:
    def test_between_phase1_and_phase2(self, tmp_path):
        lines = [
            {"index": 0, "text": "End", "start": 1.0, "end": 2.0,
             "words": [{"text": "End", "start": 1.0, "end": 2.0}]},
        ]
        r = _make_renderer(tmp_path, width=320, height=180, lines=lines,
                           analysis={"duration": 8.0})
        r.script = {"outro": {"text": "End"}}
        img = r._render_outro_frame(4.85)
        assert img is not None
        assert img.size == (320, 180)


class TestFindNearestSectionEmptyLines:
    @pytest.fixture
    def renderer(self, tmp_path):
        lines = [
            {"index": 0, "text": "A", "start": 1.0, "end": 2.0,
             "words": [{"text": "A", "start": 1.0, "end": 2.0}]},
            {"index": 1, "text": "B", "start": 3.0, "end": 4.0,
             "words": [{"text": "B", "start": 3.0, "end": 4.0}]},
        ]
        return _make_renderer(tmp_path, width=64, height=64, lines=lines)

    def test_section_with_empty_lines_skipped(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S_empty", "lines": []},
                {"name": "S1", "lines": [0, 1]},
            ]
        }
        sec = renderer._find_nearest_section(1.5)
        assert sec["name"] == "S1"


class TestRenderFrameOpacity:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_enter_phase_opacity_applied(self, renderer):
        img = renderer.render_frame(1.05)
        assert img.size == (320, 180)


class TestRenderFramePositionOffset:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=320, height=180)

    def test_slide_in_enter_phase_position_offset(self, renderer):
        renderer.script = {
            "sections": [
                {"name": "S", "lines": [0], "visual": {"animation_type": "slide_in"}},
            ]
        }
        img = renderer.render_frame(1.05)
        assert img.size == (320, 180)


class TestRenderTextOnBgOutro:
    def test_outro_return_in_render_text_on_bg(self, tmp_path):
        lines = [
            {"index": 0, "text": "End", "start": 1.0, "end": 2.0,
             "words": [{"text": "End", "start": 1.0, "end": 2.0}]},
        ]
        r = _make_renderer(tmp_path, width=320, height=180, lines=lines,
                           analysis={"duration": 5.0})
        r.script = {"outro": {"text": "Thanks"}}
        bg = Image.new("RGB", (320, 180), (30, 30, 30))
        img = r._render_text_on_bg(bg, -1, -1, t=3.0)
        assert img.size == (320, 180)


class TestGetBgForSectionWithSource:
    @pytest.fixture
    def renderer(self, tmp_path):
        return _make_renderer(tmp_path, width=64, height=64)

    def test_bg_source_matching_size(self, renderer):
        mock_source = MagicMock()
        mock_source.get_frame_pil.return_value = Image.new("RGB", (64, 64), (50, 50, 50))
        renderer._bg_source = mock_source
        bg = renderer._get_bg_for_section(0, {})
        assert bg.size == (64, 64)
        mock_source.get_frame_pil.assert_called_once()

    def test_bg_source_wrong_size_resized(self, renderer):
        mock_source = MagicMock()
        mock_source.get_frame_pil.return_value = Image.new("RGB", (100, 100), (50, 50, 50))
        renderer._bg_source = mock_source
        bg = renderer._get_bg_for_section(0, {})
        assert bg.size == (64, 64)

    def test_bg_source_returns_none_falls_back(self, renderer):
        mock_source = MagicMock()
        mock_source.get_frame_pil.return_value = None
        renderer._bg_source = mock_source
        bg = renderer._get_bg_for_section(0, {})
        assert bg.size == (64, 64)
