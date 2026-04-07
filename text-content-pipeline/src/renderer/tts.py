"""Text-to-speech audio generation using edge-tts."""

import asyncio
import subprocess
import tempfile
from pathlib import Path

from src.config.defaults import DEFAULT_TTS_VOICE
from src.errors.exceptions import RendererError


async def generate_tts(
    text: str,
    output_path: str,
    voice: str = DEFAULT_TTS_VOICE,
) -> str:
    """Generate a TTS audio file from text.

    Args:
        text: The text to convert to speech
        output_path: Where to save the audio file (.mp3)
        voice: Edge TTS voice name

    Returns:
        Path to the generated audio file

    Raises:
        RendererError: If TTS generation fails
    """
    try:
        import edge_tts
    except ImportError as e:
        raise RendererError("edge-tts not installed. Run: pip install edge-tts") from e

    try:
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(output_path)
        return output_path
    except Exception as e:
        raise RendererError(f"TTS generation failed: {e}") from e


def get_audio_duration(audio_path: str) -> float:
    """Get duration of an audio file in seconds using ffprobe.

    Args:
        audio_path: Path to the audio file

    Returns:
        Duration in seconds

    Raises:
        RendererError: If ffprobe fails or file not found
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                audio_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise RendererError("ffprobe not found. Install ffmpeg and ensure it is on PATH.")
    except subprocess.CalledProcessError as e:
        raise RendererError(f"ffprobe failed: {e.stderr}") from e

    import json

    info = json.loads(result.stdout)
    duration_str = info.get("format", {}).get("duration", "0")
    return float(duration_str)


def mux_audio_video(video_path: str, audio_path: str, output_path: str) -> str:
    """Mux audio into a video file using ffmpeg.

    Args:
        video_path: Path to the video-only file
        audio_path: Path to the audio file
        output_path: Path for the final video with audio

    Returns:
        Path to the output file

    Raises:
        RendererError: If ffmpeg muxing fails
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        output_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise RendererError("ffmpeg not found. Install ffmpeg and ensure it is on PATH.")

    if result.returncode != 0:
        raise RendererError(f"ffmpeg mux failed: {result.stderr}")

    return output_path
