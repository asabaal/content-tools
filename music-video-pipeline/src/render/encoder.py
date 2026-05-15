from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional


class VideoEncoder:
    def __init__(
        self,
        output_path: str | Path,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        audio_path: Optional[str | Path] = None,
        bitrate: str = "5M",
    ):
        self.output_path = Path(output_path)
        self.width = width
        self.height = height
        self.fps = fps
        self.audio_path = Path(audio_path) if audio_path else None
        self.bitrate = bitrate
        self._process: Optional[subprocess.Popen] = None

    def open(self) -> "VideoEncoder":
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-pixel_format", "rgb24",
            "-video_size", f"{self.width}x{self.height}",
            "-framerate", str(self.fps),
            "-i", "-",
        ]
        if self.audio_path and self.audio_path.exists():
            cmd.extend(["-i", str(self.audio_path)])
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-b:v", self.bitrate,
            "-pix_fmt", "yuv420p",
        ])
        if self.audio_path and self.audio_path.exists():
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        cmd.extend([
            "-movflags", "+faststart",
            str(self.output_path),
        ])
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        return self

    def write_frame(self, rgb_data: bytes) -> None:
        if self._process is None:
            raise RuntimeError("Encoder not opened")
        self._process.stdin.write(rgb_data)

    def close(self) -> int:
        if self._process is None:
            raise RuntimeError("Encoder not opened")
        self._process.stdin.close()
        _, stderr = self._process.communicate()
        code = self._process.returncode
        self._process = None
        if code != 0:
            raise RuntimeError(f"ffmpeg exited with code {code}: {stderr.decode('utf-8', errors='replace')[-500:]}")
        return code

    def __enter__(self) -> "VideoEncoder":
        return self.open()

    def __exit__(self, *args) -> None:
        if self._process is not None:
            self.close()
