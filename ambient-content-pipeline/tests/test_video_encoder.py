"""Tests for video encoder module."""

import pytest
from unittest.mock import patch, MagicMock
from src.renderer.video_encoder import VideoEncoder
from src.errors.exceptions import RendererError


def test_video_encoder_context_manager() -> None:
    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stderr = MagicMock()
        mock_proc.wait.return_value = None
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with VideoEncoder("/tmp/out.mp4", 1080, 1080, 30) as encoder:
            assert encoder._process is not None

        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "-y" in cmd
        assert "rawvideo" in cmd
        assert "1080x1080" in cmd
        assert "libx264" in cmd


def test_video_encoder_ffmpeg_not_found() -> None:
    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_popen.side_effect = FileNotFoundError()
        encoder = VideoEncoder("/tmp/out.mp4", 1080, 1080)
        with pytest.raises(RendererError, match="ffmpeg not found"):
            encoder.open()


def test_video_encoder_write_frame() -> None:
    from PIL import Image

    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stderr = MagicMock()
        mock_proc.wait.return_value = None
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with VideoEncoder("/tmp/out.mp4", 100, 100, 30) as encoder:
            img = Image.new("RGB", (100, 100), (255, 0, 0))
            encoder.write_frame(img)
            mock_proc.stdin.write.assert_called_once()


def test_video_encoder_write_frame_not_open() -> None:
    from PIL import Image

    encoder = VideoEncoder("/tmp/out.mp4", 100, 100)
    img = Image.new("RGB", (100, 100), (0, 0, 0))
    with pytest.raises(RendererError, match="not open"):
        encoder.write_frame(img)


def test_video_encoder_write_frame_broken_pipe() -> None:
    from PIL import Image

    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stdin.write.side_effect = BrokenPipeError()
        mock_proc.stderr.read.return_value = b"encode error"
        mock_proc.wait.return_value = None
        mock_proc.returncode = 1
        mock_popen.return_value = mock_proc

        encoder = VideoEncoder("/tmp/out.mp4", 100, 100, 30)
        encoder._process = mock_proc

        img = Image.new("RGB", (100, 100), (0, 0, 0))
        with pytest.raises(RendererError, match="pipe broken"):
            encoder.write_frame(img)


def test_video_encoder_close_nonzero_exit() -> None:
    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stderr.read.return_value = b"encode failure"
        mock_proc.returncode = 1
        mock_popen.return_value = mock_proc

        encoder = VideoEncoder("/tmp/out.mp4", 100, 100, 30)
        encoder._process = mock_proc
        with pytest.raises(RendererError, match="exited with code 1"):
            encoder.close()


def test_video_encoder_close_no_process() -> None:
    encoder = VideoEncoder("/tmp/out.mp4", 100, 100)
    encoder._process = None
    encoder.close()


def test_video_encoder_close_broken_pipe_on_stdin_close() -> None:
    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stdin.close.side_effect = BrokenPipeError()
        mock_proc.stderr = MagicMock()
        mock_proc.wait.return_value = None
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        encoder = VideoEncoder("/tmp/out.mp4", 100, 100, 30)
        encoder._process = mock_proc
        encoder.close()
        assert encoder._process is None


def test_video_encoder_cmd_params() -> None:
    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stderr = MagicMock()
        mock_proc.wait.return_value = None
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with VideoEncoder("/tmp/out.mp4", 1920, 1080, 24) as encoder:
            pass

        cmd = mock_popen.call_args[0][0]
        assert "1920x1080" in cmd
        assert "24" in cmd
        assert "yuv420p" in cmd
        assert "+faststart" in cmd


def test_video_encoder_writes_rgb() -> None:
    from PIL import Image

    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stderr = MagicMock()
        mock_proc.wait.return_value = None
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with VideoEncoder("/tmp/out.mp4", 100, 100, 30) as encoder:
            img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
            encoder.write_frame(img)

        written_bytes = mock_proc.stdin.write.call_args[0][0]
        assert len(written_bytes) == 100 * 100 * 3


def test_video_encoder_invalid_params() -> None:
    with pytest.raises(RendererError, match="Invalid encoder params"):
        VideoEncoder("/tmp/out.mp4", 0, 100, 30)
    with pytest.raises(RendererError, match="Invalid encoder params"):
        VideoEncoder("/tmp/out.mp4", 100, -1, 30)
    with pytest.raises(RendererError, match="Invalid encoder params"):
        VideoEncoder("/tmp/out.mp4", 100, 100, 0)


def test_video_encoder_write_frame_wrong_size() -> None:
    from PIL import Image

    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stderr = MagicMock()
        mock_proc.wait.return_value = None
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with VideoEncoder("/tmp/out.mp4", 100, 100, 30) as encoder:
            wrong_size_img = Image.new("RGB", (200, 200), (0, 0, 0))
            with pytest.raises(RendererError, match="doesn't match"):
                encoder.write_frame(wrong_size_img)


def test_video_encoder_write_frame_not_open_no_stdin() -> None:
    from PIL import Image

    encoder = VideoEncoder("/tmp/out.mp4", 100, 100)
    mock_proc = MagicMock()
    mock_proc.stdin = None
    encoder._process = mock_proc

    img = Image.new("RGB", (100, 100), (0, 0, 0))
    with pytest.raises(RendererError, match="not open"):
        encoder.write_frame(img)


def test_video_encoder_close_broken_pipe_on_stdin_close_with_stderr() -> None:
    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stdin.close.side_effect = BrokenPipeError()
        mock_proc.stderr = MagicMock()
        mock_proc.wait.return_value = None
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        encoder = VideoEncoder("/tmp/out.mp4", 100, 100, 30)
        encoder._process = mock_proc
        encoder.close()
        assert encoder._process is None


def test_video_encoder_close_timeout() -> None:
    import subprocess

    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stderr = MagicMock()
        mock_proc.wait.side_effect = [
            subprocess.TimeoutExpired(cmd="ffmpeg", timeout=300),
            None,
        ]
        mock_proc.kill.return_value = None
        mock_popen.return_value = mock_proc

        encoder = VideoEncoder("/tmp/out.mp4", 100, 100, 30)
        encoder._process = mock_proc
        with pytest.raises(RendererError, match="timed out"):
            encoder.close()
        mock_proc.kill.assert_called_once()


def test_video_encoder_close_nonzero_with_stderr_thread() -> None:
    import threading

    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stderr = MagicMock()
        mock_proc.wait.return_value = None
        mock_proc.returncode = 1
        mock_popen.return_value = mock_proc

        encoder = VideoEncoder("/tmp/out.mp4", 100, 100, 30)
        encoder._process = mock_proc
        encoder._stderr_thread = threading.Thread(target=lambda: None, daemon=True)
        encoder._stderr_thread.start()
        with pytest.raises(RendererError, match="exited with code 1"):
            encoder.close()


def test_video_encoder_write_frame_broken_pipe_with_stderr_thread() -> None:
    import threading
    from PIL import Image

    with patch("src.renderer.video_encoder.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stdin.write.side_effect = BrokenPipeError()
        mock_proc.stderr = MagicMock()
        mock_proc.wait.return_value = None
        mock_proc.returncode = 1
        mock_popen.return_value = mock_proc

        encoder = VideoEncoder("/tmp/out.mp4", 100, 100, 30)
        encoder._process = mock_proc
        encoder._stderr_thread = threading.Thread(target=lambda: None, daemon=True)
        encoder._stderr_thread.start()

        img = Image.new("RGB", (100, 100), (0, 0, 0))
        with pytest.raises(RendererError, match="pipe broken"):
            encoder.write_frame(img)
