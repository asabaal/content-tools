import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from render.background_video import (
    BackgroundImageSource,
    BackgroundVideoSource,
    create_background_source,
)


class TestBackgroundVideoSource:
    def test_no_paths_returns_none(self):
        src = BackgroundVideoSource([], 64, 64)
        assert src.get_frame(0.0) is None

    @patch("render.background_video.cv2.VideoCapture")
    def test_nonexistent_path(self, mock_cap_cls):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cap_cls.return_value = mock_cap
        src = BackgroundVideoSource(["/nonexistent/file.mp4"], 64, 64)
        assert src.get_frame(0.0) is None

    def test_close_clears_captures(self):
        src = BackgroundVideoSource([], 64, 64)
        src._captures[0] = MagicMock()
        src.close()
        assert len(src._captures) == 0

    def test_get_frame_pil_none(self):
        src = BackgroundVideoSource([], 64, 64)
        assert src.get_frame_pil(0.0) is None

    def test_beat_switching(self):
        src = BackgroundVideoSource(["a.mp4", "b.mp4"], 64, 64, beat_times=[1.0, 2.0])
        idx = src._current_clip_index(0.5)
        assert idx == 0
        idx = src._current_clip_index(1.5)
        assert idx == 1
        idx = src._current_clip_index(2.5)
        assert idx == 0


class TestBackgroundImageSource:
    def test_no_paths_returns_none(self):
        src = BackgroundImageSource([], 64, 64)
        assert src.get_frame(0.0) is None

    def test_nonexistent_path_returns_none(self):
        src = BackgroundImageSource(["/nonexistent/img.png"], 64, 64)
        assert src.get_frame(0.0) is None

    def test_get_frame_pil_none(self):
        src = BackgroundImageSource([], 64, 64)
        assert src.get_frame_pil(0.0) is None

    def test_close_clears(self):
        src = BackgroundImageSource([], 64, 64)
        src._images = [np.zeros((64, 64, 3), dtype=np.uint8)]
        src._loaded = True
        src.close()
        assert len(src._images) == 0

    def test_beat_switching(self):
        src = BackgroundImageSource(["a.png", "b.png"], 64, 64, beat_times=[1.0, 2.0])
        src._images = [np.zeros((64, 64, 3), dtype=np.uint8), np.ones((64, 64, 3), dtype=np.uint8)]
        src._loaded = True
        idx = src._current_index(0.5)
        assert idx == 0
        idx = src._current_index(1.5)
        assert idx == 1

    def test_single_image_no_beats(self):
        src = BackgroundImageSource(["a.png"], 64, 64)
        src._images = [np.zeros((64, 64, 3), dtype=np.uint8)]
        src._loaded = True
        idx = src._current_index(5.0)
        assert idx == 0


class TestCreateBackgroundSource:
    def test_nonexistent_path_returns_none(self):
        result = create_background_source("/nonexistent")
        assert result is None

    def test_empty_list_returns_none(self):
        result = create_background_source([])
        assert result is None

    def test_video_extensions_create_video_source(self):
        with patch("render.background_video.cv2.VideoCapture"):
            result = create_background_source(["/tmp/test.mp4"], 64, 64)
            assert isinstance(result, BackgroundVideoSource)

    def test_image_extensions_create_image_source(self):
        result = create_background_source(["/tmp/test.png"], 64, 64)
        assert isinstance(result, BackgroundImageSource)

    def test_single_string_path(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n")
            path = f.name
        try:
            result = create_background_source(path)
            assert isinstance(result, BackgroundImageSource)
        finally:
            os.unlink(path)


def _make_video_src(tmp_path, paths=None):
    if paths is None:
        p = tmp_path / "test.mp4"
        p.write_bytes(b"\x00" * 16)
        paths = [str(p)]
    return BackgroundVideoSource(paths, 64, 64)


class TestBackgroundVideoSourceAdvanced:
    @patch("render.background_video.cv2.VideoCapture")
    def test_get_capture_opens_video(self, mock_cap_cls, tmp_path):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 30.0
        mock_cap.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
        mock_cap_cls.return_value = mock_cap

        src = _make_video_src(tmp_path)
        cap = src._get_capture(0)
        assert cap is not None
        mock_cap_cls.assert_called_once()

    @patch("render.background_video.cv2.VideoCapture")
    def test_get_capture_cached(self, mock_cap_cls, tmp_path):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap_cls.return_value = mock_cap

        src = _make_video_src(tmp_path)
        src._get_capture(0)
        src._get_capture(0)
        assert mock_cap_cls.call_count == 1

    @patch("render.background_video.cv2.VideoCapture")
    def test_get_frame_seeks_to_correct_position(self, mock_cap_cls, tmp_path):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: 30.0 if prop == 5 else 900.0 if prop == 7 else 0.0
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cap_cls.return_value = mock_cap

        src = _make_video_src(tmp_path)
        frame = src.get_frame(5.0)
        assert frame is not None
        assert frame.shape == (64, 64, 3)
        mock_cap.set.assert_called()

    @patch("render.background_video.cv2.VideoCapture")
    def test_get_frame_read_failure(self, mock_cap_cls, tmp_path):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: 30.0 if prop == 5 else 1.0 if prop == 7 else 0.0
        mock_cap.read.return_value = (False, None)
        mock_cap_cls.return_value = mock_cap

        src = _make_video_src(tmp_path)
        frame = src.get_frame(0.0)
        assert frame is None

    @patch("render.background_video.cv2.VideoCapture")
    def test_get_frame_pil_converts(self, mock_cap_cls, tmp_path):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: 30.0 if prop == 5 else 900.0 if prop == 7 else 0.0
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cap_cls.return_value = mock_cap

        src = _make_video_src(tmp_path)
        img = src.get_frame_pil(0.0)
        assert img is not None
        assert isinstance(img, Image.Image)

    def test_close_releases_all_captures(self):
        mock_cap1 = MagicMock()
        mock_cap2 = MagicMock()
        src = BackgroundVideoSource(["a.mp4", "b.mp4"], 64, 64)
        src._captures[0] = mock_cap1
        src._captures[1] = mock_cap2
        src.close()
        mock_cap1.release.assert_called_once()
        mock_cap2.release.assert_called_once()
        assert len(src._captures) == 0

    def test_del_calls_close(self):
        src = BackgroundVideoSource(["a.mp4"], 64, 64)
        mock_cap = MagicMock()
        src._captures[0] = mock_cap
        src.__del__()
        mock_cap.release.assert_called_once()

    def test_get_capture_nonexistent_path(self):
        src = BackgroundVideoSource(["/nonexistent/path/video.mp4"], 64, 64)
        cap = src._get_capture(0)
        assert cap is None

    def test_get_capture_modulo_index(self):
        src = BackgroundVideoSource(["a.mp4"], 64, 64)
        src._captures[0] = MagicMock()
        cap = src._get_capture(5)
        assert cap is src._captures[0]


class TestBackgroundImageSourceAdvanced:
    def test_get_frame_with_null_images_returns_none(self):
        src = BackgroundImageSource(["/nonexistent.png"], 64, 64)
        src._images = [None]
        src._loaded = True
        frame = src.get_frame(0.0)
        assert frame is None

    def test_get_frame_pil_with_valid_image(self):
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        img[10:50, 10:50] = 128
        src = BackgroundImageSource(["a.png"], 64, 64)
        src._images = [img]
        src._loaded = True
        pil_img = src.get_frame_pil(0.0)
        assert pil_img is not None
        assert isinstance(pil_img, Image.Image)

    def test_get_frame_pil_none_when_no_images(self):
        src = BackgroundImageSource([], 64, 64)
        result = src.get_frame_pil(0.0)
        assert result is None

    def test_load_all_sets_loaded(self):
        src = BackgroundImageSource(["/nonexistent.png"], 64, 64)
        src._load_all()
        assert src._loaded is True

    def test_load_all_only_once(self):
        src = BackgroundImageSource(["/nonexistent.png"], 64, 64)
        src._load_all()
        first_images = list(src._images)
        src._load_all()
        assert src._images == first_images

    def test_current_index_no_beats(self):
        src = BackgroundImageSource(["a.png"], 64, 64)
        src._images = [np.zeros((64, 64, 3), dtype=np.uint8)]
        src._loaded = True
        idx = src._current_index(5.0)
        assert idx == 0

    def test_current_index_with_beats(self):
        src = BackgroundImageSource(["a.png", "b.png"], 64, 64, beat_times=[1.0, 2.0])
        src._images = [np.zeros((64, 64, 3), dtype=np.uint8), np.ones((64, 64, 3), dtype=np.uint8)]
        src._loaded = True
        idx = src._current_index(0.5)
        assert idx == 0
        idx = src._current_index(1.5)
        assert idx == 1
        idx = src._current_index(2.5)
        assert idx == 0

    def test_close_resets_loaded(self):
        src = BackgroundImageSource(["a.png"], 64, 64)
        src._images = [np.zeros((64, 64, 3), dtype=np.uint8)]
        src._loaded = True
        src.close()
        assert src._loaded is False
        assert len(src._images) == 0


class TestCreateBackgroundSourceAdvanced:
    def test_list_of_videos(self):
        with patch("render.background_video.cv2.VideoCapture"):
            result = create_background_source(["/tmp/a.mp4", "/tmp/b.avi"], 320, 240)
            assert isinstance(result, BackgroundVideoSource)
            assert result.width == 320
            assert result.height == 240

    def test_list_of_images(self):
        result = create_background_source(["/tmp/a.png", "/tmp/b.jpg"], 320, 240)
        assert isinstance(result, BackgroundImageSource)

    def test_with_beat_times(self):
        with patch("render.background_video.cv2.VideoCapture"):
            result = create_background_source(["/tmp/test.mp4"], 64, 64, beat_times=[1.0, 2.0])
            assert result.beat_times == [1.0, 2.0]

    def test_none_type_input(self):
        result = create_background_source(None)
        assert result is None


class TestCoverageGaps:
    @patch("render.background_video.cv2.VideoCapture")
    def test_get_capture_exists_but_not_opened(self, mock_cap_cls, tmp_path):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cap_cls.return_value = mock_cap
        p = tmp_path / "video.mp4"
        p.write_bytes(b"\x00" * 16)
        src = BackgroundVideoSource([str(p)], 64, 64)
        cap = src._get_capture(0)
        assert cap is None
        mock_cap_cls.assert_called_once()

    def test_load_all_with_real_image(self, tmp_path):
        import cv2
        arr = np.zeros((10, 10, 3), dtype=np.uint8)
        arr[2:8, 2:8] = 42
        img_path = str(tmp_path / "real.png")
        cv2.imwrite(img_path, arr)
        src = BackgroundImageSource([img_path], 32, 32)
        frame = src.get_frame(0.0)
        assert frame is not None
        assert frame.shape == (32, 32, 3)

    def test_load_all_corrupt_image_appends_none(self, tmp_path):
        corrupt = tmp_path / "bad.png"
        corrupt.write_bytes(b"not an image")
        src = BackgroundImageSource([str(corrupt)], 32, 32)
        src._load_all()
        assert src._images == [None]

    def test_get_frame_fallback_when_current_is_none(self):
        valid = np.zeros((64, 64, 3), dtype=np.uint8)
        src = BackgroundImageSource(["a.png", "b.png"], 64, 64)
        src._images = [None, valid]
        src._loaded = True
        src._index = 0
        frame = src.get_frame(0.0)
        assert frame is not None
        np.testing.assert_array_equal(frame, valid)
