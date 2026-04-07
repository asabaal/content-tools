"""End-to-end tests — full pipeline and rerender flows.

These tests exercise the complete pipeline from payload to rendered output,
including animated video, TTS, text_color, and bg_music flows.

Marked with @pytest.mark.e2e so they can be run separately:
    pytest -m e2e
    pytest -m "not e2e"   (skip slow e2e tests)
"""

import json
import os
import tempfile

import pytest
from pathlib import Path

from src.renderer.html_renderer import render_text_to_image, render_animated_video
from src.renderer.tts import generate_tts, get_audio_duration
from src.renderer.audio_mix import prepare_slot_audio
from src.renderer.video_encoder import VideoEncoder
from src.renderer.music_gen import calculate_slot_video_duration
from src.config.defaults import COLORFUL_PRESETS, auto_contrast_color, companion_color
from src.pipeline.orchestrator import run_full_pipeline
from src.payload.schema import MonthlyPayload, WeekRule, VideoWeek
from src.renderer.template_builder import build_html


pytestmark = pytest.mark.e2e


SLOT_INFO = {
    "type": "declarative_statement",
    "year": "2026",
    "month": "4",
    "day": "22",
    "week_number": "4",
    "subtheme": "Abiding in Christ",
    "subtheme_subtitle": "Staying Connected",
    "monthly_theme": "Stabilizing in Christ",
}


@pytest.mark.asyncio
async def test_e2e_static_image_render():
    """Render a real PNG image from text content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "test.png")
        result = await render_text_to_image(
            text="God is our refuge and strength",
            slot_info=SLOT_INFO,
            output_path=out_path,
        )
        assert os.path.exists(result)
        assert os.path.getsize(result) > 1000

        from PIL import Image
        img = Image.open(result)
        assert img.size == (1080, 1080)


@pytest.mark.asyncio
async def test_e2e_static_image_text_color():
    """Render with explicit text_color override."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "test_color.png")
        result = await render_text_to_image(
            text="Faith over fear",
            slot_info=SLOT_INFO,
            output_path=out_path,
            text_color="#FF0000",
        )
        assert os.path.exists(result)
        assert os.path.getsize(result) > 1000


@pytest.mark.asyncio
async def test_e2e_static_image_auto_contrast_dark():
    """Auto-contrast selects white text on dark background."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "auto_dark.png")
        result = await render_text_to_image(
            text="Deep waters",
            slot_info=SLOT_INFO,
            output_path=out_path,
            background_color="#1a1a2e",
        )
        assert os.path.exists(result)


@pytest.mark.asyncio
async def test_e2e_static_image_auto_contrast_light():
    """Auto-contrast selects black text on light background."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "auto_light.png")
        result = await render_text_to_image(
            text="Bright mornings",
            slot_info=SLOT_INFO,
            output_path=out_path,
            background_color="#FFFFCC",
        )
        assert os.path.exists(result)


@pytest.mark.asyncio
async def test_e2e_static_image_gradient():
    """Render with gradient background."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "gradient.png")
        result = await render_text_to_image(
            text="Gradient test",
            slot_info=SLOT_INFO,
            output_path=out_path,
            gradient_direction="diagonal_tl_br",
            gradient_colors=["#667eea", "#764ba2"],
        )
        assert os.path.exists(result)
        assert os.path.getsize(result) > 1000


@pytest.mark.asyncio
async def test_e2e_static_image_texture():
    """Render with texture overlay."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "texture.png")
        result = await render_text_to_image(
            text="Textured output",
            slot_info=SLOT_INFO,
            output_path=out_path,
            texture_type="noise_fine",
            texture_opacity=0.15,
        )
        assert os.path.exists(result)
        assert os.path.getsize(result) > 1000


@pytest.mark.asyncio
async def test_e2e_animated_video_no_audio():
    """Render animated MP4 without audio."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "anim.mp4")
        result = await render_animated_video(
            text="Animated content",
            slot_info=SLOT_INFO,
            output_path=out_path,
            anim_type="drift",
            anim_loop=2,
        )
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

        import subprocess
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", result],
            capture_output=True, text=True, check=True,
        )
        info = json.loads(probe.stdout)
        assert float(info["format"]["duration"]) >= 1.5
        video_stream = next(s for s in info["streams"] if s["codec_type"] == "video")
        assert video_stream["codec_name"] == "h264"


@pytest.mark.asyncio
async def test_e2e_animated_video_with_tts():
    """Render animated MP4 with TTS narration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tts_path = os.path.join(tmpdir, "tts.mp3")
        await generate_tts("This is a test of text to speech integration.", tts_path)
        tts_dur = get_audio_duration(tts_path)
        assert tts_dur > 1.0

        out_path = os.path.join(tmpdir, "anim_tts.mp4")
        result = await render_animated_video(
            text="Testing TTS integration",
            slot_info=SLOT_INFO,
            output_path=out_path,
            anim_type="flow",
            audio_path=tts_path,
        )
        assert os.path.exists(result)

        import subprocess
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", result],
            capture_output=True, text=True, check=True,
        )
        info = json.loads(probe.stdout)
        types = {s["codec_type"] for s in info["streams"]}
        assert "video" in types
        assert "audio" in types


@pytest.mark.asyncio
async def test_e2e_animated_video_with_video_duration():
    """Render animated MP4 with explicit video_duration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "dur.mp4")
        result = await render_animated_video(
            text="Duration test",
            slot_info=SLOT_INFO,
            output_path=out_path,
            anim_type="pulse",
            video_duration=2.0,
        )
        assert os.path.exists(result)

        import subprocess
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", result],
            capture_output=True, text=True, check=True,
        )
        info = json.loads(probe.stdout)
        dur = float(info["format"]["duration"])
        assert 1.5 <= dur <= 2.5


@pytest.mark.asyncio
async def test_e2e_tts_plus_music_mix():
    """Generate TTS, create fake music, mix them, verify output."""
    import subprocess

    with tempfile.TemporaryDirectory() as tmpdir:
        tts_path = os.path.join(tmpdir, "tts.mp3")
        await generate_tts("Short test for mixing.", tts_path)
        tts_dur = get_audio_duration(tts_path)
        assert tts_dur > 0.5

        music_path = os.path.join(tmpdir, "music.wav")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi",
             "-i", "sine=frequency=200:duration=15.0",
             "-ar", "48000", "-ac", "1", music_path],
            capture_output=True, check=True,
        )

        slot_dur = calculate_slot_video_duration(tts_dur)
        mixed_path = os.path.join(tmpdir, "mixed.mp3")

        out, dur = prepare_slot_audio(
            tts_path=tts_path,
            music_path=music_path,
            output_path=mixed_path,
            tts_duration=tts_dur,
            slot_video_duration=slot_dur,
        )

        assert os.path.exists(out)
        actual_dur = get_audio_duration(out)
        assert abs(actual_dur - slot_dur) < 0.5


@pytest.mark.asyncio
async def test_e2e_animated_video_all_types():
    """Render with each animation type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for anim_type in ["drift", "flow", "pulse", "distortion", "parallax"]:
            out_path = os.path.join(tmpdir, f"{anim_type}.mp4")
            result = await render_animated_video(
                text=f"Testing {anim_type}",
                slot_info=SLOT_INFO,
                output_path=out_path,
                anim_type=anim_type,
                anim_loop=1,
            )
            assert os.path.exists(result), f"Failed for {anim_type}"
            assert os.path.getsize(result) > 0, f"Empty for {anim_type}"


@pytest.mark.asyncio
async def test_e2e_companion_color_in_animation():
    """Verify companion color produces visually distinct gradient."""
    bg = "#E67E22"
    comp = companion_color(bg)
    assert comp != bg
    assert comp.startswith("#")
    assert len(comp) == 7

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "comp.mp4")
        result = await render_animated_video(
            text="Companion color test",
            slot_info=SLOT_INFO,
            output_path=out_path,
            background_color=bg,
            gradient_colors=[bg, comp],
            anim_loop=1,
        )
        assert os.path.exists(result)


@pytest.mark.asyncio
async def test_e2e_build_html_auto_contrast_all_presets():
    """Verify auto-contrast works with every preset background."""
    for name, preset in COLORFUL_PRESETS.items():
        bg = str(preset.get("background", "#4A90E2"))
        expected = auto_contrast_color(bg)
        html = build_html(
            "Test", SLOT_INFO, preset, 1080, 1080,
        )
        assert expected in html, f"Preset {name}: expected {expected} in HTML for bg {bg}"


def test_e2e_rerender_single_post():
    """Full rerender of a single post from saved plan."""
    import asyncio
    with tempfile.TemporaryDirectory() as tmpdir:
        plan_dir = Path(tmpdir)
        plans_dir = plan_dir / "plans"
        plans_dir.mkdir()

        plan_data = {
            "year": 2026, "month": 4, "monthly_theme": "Test E2E",
            "weekly_subthemes": ["W1"],
            "weekly_subtitles": {1: "Sub"},
            "weekly_subthemes_source": "human",
            "render_config": {
                "style_preset": "warm",
                "background_color": "#E67E22",
            },
            "schedule_summary": [
                {"date": "2026-04-22", "weekday": "Wednesday", "week_number": 1,
                 "slot_type": "declarative_statement", "subtheme": "W1", "is_automated": True},
            ],
        }
        with open(plans_dir / "2026-04_plan.json", "w") as f:
            json.dump(plan_data, f)

        texts_data = {"texts": {"2026-04-22": "End to end rerender test content"}}
        with open(plans_dir / "2026-04_texts.json", "w") as f:
            json.dump(texts_data, f)

        images_dir = plan_dir / "images"
        images_dir.mkdir()

        from src.cli import commands
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(commands.rerender, [
            "--plan-dir", str(plan_dir),
            "--date", "2026-04-22",
            "--animate",
            "--anim-type", "drift",
            "--anim-loop", "2",
        ])

        assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"
        mp4_files = list(images_dir.glob("*.mp4"))
        assert len(mp4_files) == 1


def test_e2e_rerender_with_audio():
    """Rerender a single post with TTS audio."""
    import asyncio
    with tempfile.TemporaryDirectory() as tmpdir:
        plan_dir = Path(tmpdir)
        plans_dir = plan_dir / "plans"
        plans_dir.mkdir()

        plan_data = {
            "year": 2026, "month": 4, "monthly_theme": "Audio Test",
            "weekly_subthemes": ["W1"],
            "weekly_subtitles": {1: "Sub"},
            "weekly_subthemes_source": "human",
            "render_config": {"style_preset": "default", "animate": True},
            "schedule_summary": [
                {"date": "2026-04-22", "weekday": "Wednesday", "week_number": 1,
                 "slot_type": "declarative_statement", "subtheme": "W1", "is_automated": True},
            ],
        }
        with open(plans_dir / "2026-04_plan.json", "w") as f:
            json.dump(plan_data, f)

        texts_data = {"texts": {"2026-04-22": "Testing audio rendering end to end."}}
        with open(plans_dir / "2026-04_texts.json", "w") as f:
            json.dump(texts_data, f)

        from src.cli import commands
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(commands.rerender, [
            "--plan-dir", str(plan_dir),
            "--date", "2026-04-22",
            "--animate",
            "--anim-type", "drift",
            "--audio",
        ])

        assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"

        images_dir = plan_dir / "images"
        mp4_files = list(images_dir.glob("*.mp4"))
        assert len(mp4_files) >= 1

        import subprocess
        for mp4 in mp4_files:
            if "video_only" not in mp4.name:
                probe = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json",
                     "-show_streams", str(mp4)],
                    capture_output=True, text=True, check=True,
                )
                info = json.loads(probe.stdout)
                types = {s["codec_type"] for s in info["streams"]}
                assert "audio" in types, f"No audio stream in {mp4.name}"
