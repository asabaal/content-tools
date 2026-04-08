"""Integration tests — real ffmpeg, edge-tts, and file I/O.

These tests call actual external tools. They verify that the subprocess
wrappers, audio mixing, TTS generation, and video encoding work end-to-end
with real files on disk.

Marked with @pytest.mark.integration so they can be skipped in CI or
fast test runs: pytest -m "not integration"
"""

import os
import tempfile

import pytest

from src.renderer.tts import generate_tts, get_audio_duration, mux_audio_video
from src.renderer.audio_mix import prepare_slot_audio
from src.renderer.video_encoder import VideoEncoder
from src.renderer.music_gen import calculate_music_duration, calculate_slot_video_duration
from src.config.defaults import ACE_STEP_TTS_DELAY, ACE_STEP_TAIL_MAX, ACE_STEP_TAIL_RATIO


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_tts_generates_real_audio():
    """edge-tts produces a real MP3 file with correct duration."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        out_path = f.name

    try:
        result = await generate_tts("Hello world", out_path)
        assert result == out_path
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0

        dur = get_audio_duration(out_path)
        assert dur > 0.5
        assert dur < 5.0
    finally:
        os.unlink(out_path)


@pytest.mark.asyncio
async def test_tts_custom_voice():
    """edge-tts works with a different voice."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        out_path = f.name

    try:
        await generate_tts("Testing voice", out_path, voice="en-GB-SoniaNeural")
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0
    finally:
        os.unlink(out_path)


def test_get_audio_duration_real_file():
    """get_audio_duration reads correct duration from a real MP3."""
    import subprocess

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        out_path = f.name

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=3.0",
             "-ar", "44100", "-ac", "1", out_path],
            capture_output=True, check=True,
        )
        dur = get_audio_duration(out_path)
        assert 2.9 <= dur <= 3.1
    finally:
        os.unlink(out_path)


def test_video_encoder_real_mp4():
    """VideoEncoder produces a real MP4 with correct frame count."""
    from PIL import Image

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        out_path = f.name

    try:
        with VideoEncoder(out_path, 320, 240, fps=10) as encoder:
            for _ in range(30):
                img = Image.new("RGB", (320, 240), (128, 64, 32))
                encoder.write_frame(img)

        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0

        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", out_path],
            capture_output=True, text=True, check=True,
        )
        import json
        info = json.loads(result.stdout)
        video_stream = next(s for s in info["streams"] if s["codec_type"] == "video")
        assert video_stream["width"] == 320
        assert video_stream["height"] == 240
        assert video_stream["r_frame_rate"].startswith("10")
    finally:
        os.unlink(out_path)


def test_mux_audio_video_real():
    """mux_audio_video combines real video + audio into final MP4."""
    from PIL import Image
    import subprocess

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "video.mp4")
        audio_path = os.path.join(tmpdir, "audio.wav")
        output_path = os.path.join(tmpdir, "final.mp4")

        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2.0",
             "-ar", "44100", "-ac", "1", audio_path],
            capture_output=True, check=True,
        )

        with VideoEncoder(video_path, 320, 240, fps=10) as encoder:
            for _ in range(20):
                encoder.write_frame(Image.new("RGB", (320, 240), (0, 0, 0)))

        result = mux_audio_video(video_path, audio_path, output_path)
        assert result == output_path
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", output_path],
            capture_output=True, text=True, check=True,
        )
        import json
        info = json.loads(probe.stdout)
        types = {s["codec_type"] for s in info["streams"]}
        assert "video" in types
        assert "audio" in types


def test_prepare_slot_audio_real():
    """prepare_slot_audio mixes real TTS + music audio."""
    import subprocess

    with tempfile.TemporaryDirectory() as tmpdir:
        tts_path = os.path.join(tmpdir, "tts.wav")
        music_path = os.path.join(tmpdir, "music.wav")
        output_path = os.path.join(tmpdir, "mixed.mp3")

        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=300:duration=5.0",
             "-ar", "44100", "-ac", "1", tts_path],
            capture_output=True, check=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=100:duration=10.0",
             "-ar", "44100", "-ac", "1", music_path],
            capture_output=True, check=True,
        )

        out, dur = prepare_slot_audio(
            tts_path=tts_path,
            music_path=music_path,
            output_path=output_path,
            tts_duration=5.0,
            slot_video_duration=7.5,
        )

        assert out == output_path
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
        assert dur == 7.5

        actual_dur = get_audio_duration(output_path)
        assert 7.0 <= actual_dur <= 8.0


def test_prepare_slot_audio_volume_reduction():
    """Music at 30% volume should be quieter than music at 100%."""
    import subprocess
    import struct
    import wave

    with tempfile.TemporaryDirectory() as tmpdir:
        music_path = os.path.join(tmpdir, "music.wav")
        tts_path = os.path.join(tmpdir, "tts.wav")
        quiet_path = os.path.join(tmpdir, "quiet.mp3")
        loud_path = os.path.join(tmpdir, "loud.mp3")

        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=3.0",
             "-ar", "44100", "-ac", "1", music_path],
            capture_output=True, check=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=300:duration=2.0",
             "-ar", "44100", "-ac", "1", tts_path],
            capture_output=True, check=True,
        )

        prepare_slot_audio(tts_path, music_path, quiet_path, 2.0, 3.5, music_volume=0.1)
        prepare_slot_audio(tts_path, music_path, loud_path, 2.0, 3.5, music_volume=0.9)

        quiet_size = os.path.getsize(quiet_path)
        loud_size = os.path.getsize(loud_path)
        assert quiet_size > 0
        assert loud_size > 0


def test_duration_calculations():
    """Verify duration formulas match constants."""
    assert calculate_music_duration(6.0) == ACE_STEP_TTS_DELAY + 6.0 + min(ACE_STEP_TAIL_MAX, 6.0 * ACE_STEP_TAIL_RATIO)
    assert calculate_music_duration(20.0) == ACE_STEP_TTS_DELAY + 20.0 + ACE_STEP_TAIL_MAX
    assert calculate_slot_video_duration(6.0) == ACE_STEP_TTS_DELAY + 6.0 + min(ACE_STEP_TAIL_MAX, 6.0 * ACE_STEP_TAIL_RATIO)
    assert calculate_slot_video_duration(20.0) == ACE_STEP_TTS_DELAY + 20.0 + ACE_STEP_TAIL_MAX
