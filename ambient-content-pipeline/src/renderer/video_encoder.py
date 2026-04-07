"""FFmpeg subprocess wrapper for streaming frames to MP4."""

import io
import subprocess
import threading
from typing import TYPE_CHECKING

from src.errors.exceptions import RendererError

if TYPE_CHECKING:
    from PIL import Image


class VideoEncoder:
    """Streams raw RGB frames to an ffmpeg subprocess to produce an MP4 file."""

    def __init__(self, output_path: str, width: int, height: int, fps: int = 30) -> None:
        if width <= 0 or height <= 0 or fps <= 0:
            raise RendererError(f"Invalid encoder params: width={width}, height={height}, fps={fps}")
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self._process: subprocess.Popen[bytes] | None = None
        self._stderr_thread: threading.Thread | None = None
        self._stderr_output: str = ""

    def _drain_stderr(self) -> None:
        if self._process and self._process.stderr:
            buf = io.StringIO()
            for line in self._process.stderr:
                buf.write(line.decode("utf-8", errors="replace"))
            self._stderr_output = buf.getvalue()

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
            self._stderr_output = ""
            self._stderr_thread = threading.Thread(
                target=self._drain_stderr, daemon=True
            )
            self._stderr_thread.start()
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
        if rgb_image.size != (self.width, self.height):
            raise RendererError(
                f"Frame size {rgb_image.size} doesn't match encoder {self.width}x{self.height}"
            )
        raw_bytes = rgb_image.tobytes()

        try:
            self._process.stdin.write(raw_bytes)
        except BrokenPipeError:
            if self._stderr_thread:
                self._stderr_thread.join(timeout=5)
            raise RendererError(
                f"ffmpeg pipe broken. stderr: {self._stderr_output}"
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

        try:
            self._process.wait(timeout=300)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=10)
            raise RendererError("ffmpeg encoding timed out after 300s")

        if self._process.returncode != 0:
            if self._stderr_thread:
                self._stderr_thread.join(timeout=5)
            raise RendererError(
                f"ffmpeg exited with code {self._process.returncode}. stderr: {self._stderr_output}"
            )

        self._process = None
