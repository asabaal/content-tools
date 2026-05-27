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
