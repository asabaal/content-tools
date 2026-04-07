"""FFmpeg subprocess wrapper for streaming frames to MP4."""

import subprocess
from typing import TYPE_CHECKING

from src.errors.exceptions import RendererError

if TYPE_CHECKING:
    from PIL import Image


class VideoEncoder:
    """Streams raw RGB frames to an ffmpeg subprocess to produce an MP4 file."""

    def __init__(self, output_path: str, width: int, height: int, fps: int = 30) -> None:
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self._process: subprocess.Popen[bytes] | None = None

    def __enter__(self) -> "VideoEncoder":
        self.open()
        return self

    def __exit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object) -> None:
        self.close()

    def open(self) -> None:
        """Start the ffmpeg subprocess."""
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "rgb24",
            "-s", f"{self.width}x{self.height}",
            "-r", str(self.fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            self.output_path,
        ]

        try:
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            raise RendererError(
                "ffmpeg not found. Install ffmpeg and ensure it is on PATH."
            )

    def write_frame(self, image: "Image.Image") -> None:
        """Write a single PIL Image frame to the encoder.

        Args:
            image: PIL Image to write (will be converted to RGB)

        Raises:
            RendererError: If the encoder is not open or ffmpeg fails
        """
        if self._process is None or self._process.stdin is None:
            raise RendererError("VideoEncoder is not open")

        rgb_image = image.convert("RGB")
        raw_bytes = rgb_image.tobytes()

        try:
            self._process.stdin.write(raw_bytes)
        except BrokenPipeError:
            stderr_output = ""
            if self._process.stderr:
                stderr_output = self._process.stderr.read().decode("utf-8", errors="replace")
            raise RendererError(
                f"ffmpeg pipe broken. stderr: {stderr_output}"
            )

    def close(self) -> None:
        """Close the pipe and wait for ffmpeg to finalize the output file."""
        if self._process is None:
            return

        if self._process.stdin is not None:
            try:
                self._process.stdin.close()
            except BrokenPipeError:
                pass

        self._process.wait()

        if self._process.returncode != 0:
            stderr_output = ""
            if self._process.stderr:
                stderr_output = self._process.stderr.read().decode("utf-8", errors="replace")
            raise RendererError(
                f"ffmpeg exited with code {self._process.returncode}. stderr: {stderr_output}"
            )

        self._process = None
