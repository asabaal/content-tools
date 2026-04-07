"""HTML renderer using headless browser."""

import io
import math
from datetime import datetime
from pathlib import Path
from typing import Literal

from PIL import Image
from playwright.async_api import async_playwright

from src.config.defaults import (
    ANIM_FPS,
    AUDIO_PAD_SECONDS,
    COLORFUL_PRESETS,
    DEFAULT_ANIM_INTENSITY,
    DEFAULT_ANIM_LOOP,
    DEFAULT_ANIM_SPEED,
    DEFAULT_ANIM_TYPE,
    DEFAULT_IMAGE_HEIGHT,
    DEFAULT_IMAGE_WIDTH,
    IMAGE_FORMAT,
    IMAGES_DIR,
    AnimType,
    GradientDirection,
    TextureBlendMode,
    TextureType,
)
from src.renderer.tts import get_audio_duration, mux_audio_video
from src.errors.exceptions import RendererError
from src.renderer.animation import AnimationFrameGenerator
from src.renderer.template_builder import build_html
from src.renderer.video_encoder import VideoEncoder


async def render_text_to_image(
    text: str,
    slot_info: dict[str, str],
    output_path: str = "",
    style_preset: str = "default",
    background_color: str | None = None,
    aspect_ratio: Literal["1:1", "4:5"] = "1:1",
    gradient_direction: GradientDirection | None = None,
    gradient_colors: list[str] | None = None,
    gradient_stops: list[float] | None = None,
    texture_type: TextureType | None = None,
    texture_opacity: float | None = None,
    texture_blend_mode: TextureBlendMode | None = None,
    text_color: str | None = None,
) -> str:
    """Render text content to a PNG image.

    Args:
        text: The text content to render
        slot_info: Dictionary with slot information (type, date, week_number, subtheme, subtheme_subtitle, monthly_theme)
        output_path: Path where image should be saved (or None to let function generate)
        style_preset: Name of colorful style preset
        background_color: Optional override color
        aspect_ratio: Image aspect ratio ("1:1" or "4:5")
        gradient_direction: Optional gradient direction
        gradient_colors: Optional list of 2-4 hex color strings
        gradient_stops: Optional normalized stop positions (0.0-1.0)
        texture_type: Optional texture overlay type
        texture_opacity: Optional texture opacity (0.0-1.0)
        texture_blend_mode: Optional texture blend mode
        text_color: Optional text color override. Auto-computed from background if not provided.

    Returns:
        Path to rendered image file

    Raises:
        RendererError: If rendering fails
    """
    if style_preset not in COLORFUL_PRESETS:
        raise RendererError(
            f"Invalid style preset '{style_preset}'. Available: {list(COLORFUL_PRESETS.keys())}"
        )

    preset = COLORFUL_PRESETS[style_preset].copy()

    if background_color:
        preset["background"] = background_color

    if aspect_ratio == "4:5":
        width = 1080
        height = 1350
    else:
        width = DEFAULT_IMAGE_WIDTH
        height = DEFAULT_IMAGE_HEIGHT

    html_content = build_html(
        text,
        slot_info,
        preset,
        width,
        height,
        gradient_direction=gradient_direction,
        gradient_colors=gradient_colors,
        gradient_stops=gradient_stops,
        texture_type=texture_type,
        texture_opacity=texture_opacity,
        texture_blend_mode=texture_blend_mode,
        text_color=text_color,
    )

    # Generate filename if not provided
    if not output_path:
        output_path = get_output_path(
            year=int(slot_info.get("year", datetime.now().year)),
            month=int(slot_info.get("month", datetime.now().month)),
            day=int(slot_info.get("day", datetime.now().day)),
            monthly_theme=slot_info.get("monthly_theme", ""),
            week_number=int(slot_info.get("week_number", 1)),
            subtheme=slot_info.get("subtheme", ""),
            slot_type=slot_info.get("type", "post"),
        )

    # Render to image
    return await _render_html_to_image(html_content, output_path, width, height)


async def _render_html_to_image(
    html: str,
    output_path: str,
    width: int,
    height: int,
) -> str:
    """Render HTML to PNG image using Playwright.

    Args:
        html: HTML content to render
        output_path: Where to save the image
        width: Viewport width
        height: Viewport height

    Returns:
        Path to saved image

    Raises:
        RendererError: If rendering fails
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                viewport={"width": width, "height": height},
            )

            await page.set_content(html)

            screenshot_path = Path(output_path)
            await page.screenshot(
                path=str(screenshot_path),
                full_page=False,
                type="png",
            )

            await browser.close()

            return str(screenshot_path)

    except Exception as e:
        raise RendererError(f"Failed to render HTML to image: {e}") from e


def get_output_path(
    year: int,
    month: int,
    day: int,
    monthly_theme: str,
    week_number: int,
    subtheme: str,
    slot_type: str,
    images_dir: Path | None = None,
) -> str:
    """Generate output path for a daily post image.

    Args:
        year: Calendar year
        month: Calendar month (1-12)
        day: Calendar day (1-31)
        monthly_theme: Monthly theme text
        week_number: Week number
        subtheme: Subtheme text
        slot_type: Slot type identifier
        images_dir: Optional custom directory for images

    Returns:
        Full path for image file
    """
    import re

    def sanitize(s: str) -> str:
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"\s+", "-", s)
        return s[:80] if len(s) > 80 else s

    theme_part = sanitize(monthly_theme)
    subtheme_part = sanitize(subtheme) if subtheme else f"week{week_number:02d}"
    type_part = sanitize(slot_type)

    filename = f"{year:04d}{month:02d}{day:02d}_{theme_part}_week{week_number:02d}_{subtheme_part}_{type_part}.{IMAGE_FORMAT}"
    dir_path = images_dir or IMAGES_DIR
    return str(dir_path / filename)


def get_video_output_path(
    year: int,
    month: int,
    day: int,
    monthly_theme: str,
    week_number: int,
    subtheme: str,
    slot_type: str,
    images_dir: Path | None = None,
) -> str:
    """Generate output path for a daily post video.

    Args:
        year: Calendar year
        month: Calendar month (1-12)
        day: Calendar day (1-31)
        monthly_theme: Monthly theme text
        week_number: Week number
        subtheme: Subtheme text
        slot_type: Slot type identifier
        images_dir: Optional custom directory for images

    Returns:
        Full path for video file (.mp4)
    """
    import re

    def sanitize(s: str) -> str:
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"\s+", "-", s)
        return s[:80] if len(s) > 80 else s

    theme_part = sanitize(monthly_theme)
    subtheme_part = sanitize(subtheme) if subtheme else f"week{week_number:02d}"
    type_part = sanitize(slot_type)

    filename = f"{year:04d}{month:02d}{day:02d}_{theme_part}_week{week_number:02d}_{subtheme_part}_{type_part}.mp4"
    dir_path = images_dir or IMAGES_DIR
    return str(dir_path / filename)


async def _render_text_layer_to_pil(
    text: str,
    slot_info: dict[str, str],
    width: int,
    height: int,
    style_preset: str = "default",
    background_color: str | None = None,
    gradient_direction: GradientDirection | None = None,
    gradient_colors: list[str] | None = None,
    gradient_stops: list[float] | None = None,
    texture_type: TextureType | None = None,
    texture_opacity: float | None = None,
    texture_blend_mode: TextureBlendMode | None = None,
    text_color: str | None = None,
) -> Image.Image:
    """Render text content to a PIL Image with transparent background.

    Args:
        text: The text content to render
        slot_info: Dictionary with slot information
        width: Image width
        height: Image height
        style_preset: Name of colorful style preset
        background_color: Optional override color (ignored, transparent)
        gradient_direction: Optional gradient direction (ignored, transparent)
        gradient_colors: Optional gradient colors (ignored, transparent)
        gradient_stops: Optional gradient stops (ignored, transparent)
        texture_type: Optional texture overlay type (ignored, transparent)
        texture_opacity: Optional texture opacity (ignored, transparent)
        texture_blend_mode: Optional texture blend mode (ignored, transparent)
        text_color: Optional text color override. Auto-computed from background if not provided.

    Returns:
        PIL Image with RGBA (transparent background)

    Raises:
        RendererError: If rendering fails
    """
    if style_preset not in COLORFUL_PRESETS:
        raise RendererError(
            f"Invalid style preset '{style_preset}'. Available: {list(COLORFUL_PRESETS.keys())}"
        )

    preset = COLORFUL_PRESETS[style_preset].copy()

    html_content = build_html(
        text,
        slot_info,
        preset,
        width,
        height,
        gradient_direction=gradient_direction,
        gradient_colors=gradient_colors,
        gradient_stops=gradient_stops,
        texture_type=texture_type,
        texture_opacity=texture_opacity,
        texture_blend_mode=texture_blend_mode,
        transparent_bg=True,
        text_color=text_color,
    )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                viewport={"width": width, "height": height},
            )

            await page.set_content(html_content)

            screenshot_bytes = await page.screenshot(
                full_page=False,
                type="png",
                omit_background=True,
            )

            await browser.close()

        return Image.open(io.BytesIO(screenshot_bytes)).convert("RGBA")

    except Exception as e:
        raise RendererError(f"Failed to render text layer: {e}") from e


async def render_animated_video(
    text: str,
    slot_info: dict[str, str],
    output_path: str = "",
    style_preset: str = "default",
    background_color: str | None = None,
    aspect_ratio: Literal["1:1", "4:5"] = "1:1",
    gradient_direction: GradientDirection | None = None,
    gradient_colors: list[str] | None = None,
    gradient_stops: list[float] | None = None,
    texture_type: TextureType | None = None,
    texture_opacity: float | None = None,
    texture_blend_mode: TextureBlendMode | None = None,
    anim_type: AnimType = DEFAULT_ANIM_TYPE,
    anim_intensity: float = DEFAULT_ANIM_INTENSITY,
    anim_speed: float = DEFAULT_ANIM_SPEED,
    anim_loop: int = DEFAULT_ANIM_LOOP,
    anim_seed: int | None = None,
    audio_path: str | None = None,
    text_color: str | None = None,
    video_duration: float | None = None,
) -> str:
    """Render text content to an animated MP4 video.

    Args:
        text: The text content to render
        slot_info: Dictionary with slot information
        output_path: Path where video should be saved
        style_preset: Name of colorful style preset
        background_color: Optional override color
        aspect_ratio: Image aspect ratio ("1:1" or "4:5")
        gradient_direction: Optional gradient direction
        gradient_colors: Optional list of 2-4 hex color strings
        gradient_stops: Optional normalized stop positions (0.0-1.0)
        texture_type: Optional texture overlay type
        texture_opacity: Optional texture opacity (0.0-1.0)
        texture_blend_mode: Optional texture blend mode
        anim_type: Animation type (drift, flow, pulse, distortion, parallax, reactive)
        anim_intensity: Animation intensity (0.0-0.5)
        anim_speed: Animation speed (0.1-2.0)
        anim_loop: Loop duration in seconds
        anim_seed: Optional seed for deterministic output
        audio_path: Optional path to audio file. If provided, overrides
            anim_loop with audio duration and muxes audio into final video.
        text_color: Optional text color override. Auto-computed from background if not provided.
        video_duration: Optional explicit video duration in seconds. If provided, overrides
            both anim_loop and audio-derived duration. Use when mixed audio already has correct length.

    Returns:
        Path to rendered video file

    Raises:
        RendererError: If rendering fails
    """
    if aspect_ratio == "4:5":
        width = 1080
        height = 1350
    else:
        width = DEFAULT_IMAGE_WIDTH
        height = DEFAULT_IMAGE_HEIGHT

    if not output_path:
        output_path = get_video_output_path(
            year=int(slot_info.get("year", datetime.now().year)),
            month=int(slot_info.get("month", datetime.now().month)),
            day=int(slot_info.get("day", datetime.now().day)),
            monthly_theme=slot_info.get("monthly_theme", ""),
            week_number=int(slot_info.get("week_number", 1)),
            subtheme=slot_info.get("subtheme", ""),
            slot_type=slot_info.get("type", "post"),
        )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    effective_loop = anim_loop
    if video_duration is not None:
        effective_loop = max(1, math.ceil(video_duration))
        print(f"  Video duration (explicit): {video_duration:.1f}s -> video loop: {effective_loop}s")
    elif audio_path:
        audio_dur = get_audio_duration(audio_path)
        effective_loop = max(1, math.ceil(audio_dur + AUDIO_PAD_SECONDS))
        print(f"  Audio duration: {audio_dur:.1f}s -> video loop: {effective_loop}s")

    print("  Rendering text layer for animation...")
    text_layer = await _render_text_layer_to_pil(
        text=text,
        slot_info=slot_info,
        width=width,
        height=height,
        style_preset=style_preset,
        background_color=background_color,
        gradient_direction=gradient_direction,
        gradient_colors=gradient_colors,
        gradient_stops=gradient_stops,
        texture_type=texture_type,
        texture_opacity=texture_opacity,
        texture_blend_mode=texture_blend_mode,
        text_color=text_color,
    )

    effective_colors = gradient_colors
    if not effective_colors:
        from src.config.defaults import companion_color

        preset = COLORFUL_PRESETS.get(style_preset, {})
        bg = background_color or preset.get("background", "#4A90E2")
        effective_colors = [bg, companion_color(bg)]

    generator = AnimationFrameGenerator(
        anim_type=anim_type,
        intensity=anim_intensity,
        speed=anim_speed,
        width=width,
        height=height,
        seed=anim_seed,
        gradient_colors=effective_colors,
    )

    total_frames = ANIM_FPS * effective_loop

    print(f"  Encoding video: {total_frames} frames at {ANIM_FPS}fps ({effective_loop}s)...")

    video_only_path = output_path
    if audio_path:
        video_only_path = str(Path(output_path).with_suffix(".video_only.mp4"))

    with VideoEncoder(video_only_path, width, height, fps=ANIM_FPS) as encoder:
        for i in range(total_frames):
            t = i / total_frames
            bg_frame = generator.generate_background_frame(t)

            bg_rgba = bg_frame.convert("RGBA")
            composite = Image.alpha_composite(bg_rgba, text_layer)

            encoder.write_frame(composite.convert("RGB"))

            if (i + 1) % (ANIM_FPS * 5) == 0:
                print(f"    Progress: {i + 1}/{total_frames} frames")

    if audio_path and Path(audio_path).is_file():
        mux_audio_video(
            video_path=video_only_path,
            audio_path=audio_path,
            output_path=output_path,
        )
        if video_only_path != output_path:
            Path(video_only_path).unlink(missing_ok=True)
        print(f"  Muxed audio into video")
    elif video_only_path != output_path:
        Path(video_only_path).rename(output_path)

    return output_path
