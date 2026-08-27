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
        audio_start: Optional[float] = None,
        audio_duration: Optional[float] = None,
    ):
        """Raw-RGB frame encoder with optional audio muxing.

        ``audio_start`` / ``audio_duration`` trim the audio input to the rendered
        interval. Without them the *entire* audio file is muxed, producing an
        output far longer than the video stream whenever ``time_start``/
        ``time_end`` excerpt rendering is used (the video stops but the audio
        keeps playing over a frozen frame).
        """
        self.output_path = Path(output_path)
        self.width = width
        self.height = height
        self.fps = fps
        self.audio_path = Path(audio_path) if audio_path else None
        self.bitrate = bitrate
        self.audio_start = audio_start
        self.audio_duration = audio_duration
        self._process: Optional[subprocess.Popen] = None

    def build_cmd(self) -> list[str]:
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-pixel_format", "rgb24",
            "-video_size", f"{self.width}x{self.height}",
            "-framerate", str(self.fps),
            "-i", "-",
        ]
        has_audio = self.audio_path and self.audio_path.exists()
        trimming = self.audio_start is not None or self.audio_duration is not None
        if has_audio:
            # Input-seeking options must precede the audio input they apply to,
            # so the trim affects only the audio stream, not the piped video.
            if self.audio_start is not None:
                cmd.extend(["-ss", f"{self.audio_start:.3f}"])
            if self.audio_duration is not None:
                cmd.extend(["-t", f"{self.audio_duration:.3f}"])
            cmd.extend(["-i", str(self.audio_path)])
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-b:v", self.bitrate,
            "-pix_fmt", "yuv420p",
        ])
        if has_audio and trimming:
            # Trimmed (excerpt) renders: the trimmed audio defines the output
            # length, so a frozen-frame tail can never outlive it.
            cmd.append("-shortest")
        if has_audio:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        cmd.extend([
            "-movflags", "+faststart",
            str(self.output_path),
        ])
        return cmd

    def open(self) -> "VideoEncoder":
        self._process = subprocess.Popen(
            self.build_cmd(),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
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
        self._process.wait()
        stderr = self._process.stderr.read() if self._process.stderr else b""
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
