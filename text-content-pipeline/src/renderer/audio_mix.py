"""Audio mixing for TTS + background music via ffmpeg."""

import subprocess

from src.config.defaults import ACE_STEP_MUSIC_VOLUME, ACE_STEP_TTS_DELAY
from src.errors.exceptions import RendererError


def prepare_slot_audio(
    tts_path: str,
    music_path: str,
    output_path: str,
    tts_duration: float,
    slot_video_duration: float,
    music_volume: float = ACE_STEP_MUSIC_VOLUME,
) -> tuple[str, float]:
    """Mix TTS narration with trimmed background music.

    1. Trim monthly music track to slot_video_duration
    2. Pad TTS with delay before speech starts
    3. Mix TTS at 1.0 + music at music_volume
    4. Return (mixed_audio_path, slot_video_duration)
    """
    delay_ms = int(ACE_STEP_TTS_DELAY * 1000)

    filter_complex = (
        f"[0:a]adelay={delay_ms}|{delay_ms}[tts];"
        f"[1:a]atrim=0:{slot_video_duration},asetpts=PTS-STARTPTS[volume];"
        f"[volume]volume={music_volume}[music];"
        f"[tts][music]amix=inputs=2:duration=longest:dropout_transition=2[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", tts_path,
        "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ar", "44100",
        "-ac", "1",
        output_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        raise RendererError("ffmpeg audio mixing timed out")

    if result.returncode != 0:
        raise RendererError(f"ffmpeg audio mixing failed: {result.stderr.strip()}")

    return output_path, slot_video_duration
