"""Pipeline orchestrator for end-to-end execution."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Literal

from src.ai_generator import generator
from src.config import defaults
from src.config.defaults import (
    IMAGE_FORMAT,
    IMAGES_DIR,
    PLANS_DIR,
    AnimType,
    GradientDirection,
    TextureBlendMode,
    TextureType,
)
from src.errors.exceptions import (
    AIGenerationError,
    PipelineError,
)
from src.payload import schema, validation
from src.renderer import html_renderer
from src.slots import scheduler
from src.slots.enum import SlotFunction
from src.weekly_calendar.resolver import ResolvedCalendar, resolve_calendar

logger = logging.getLogger(__name__)


async def run_full_pipeline(
    payload: schema.MonthlyPayload,
    model: str | None = None,
    background_color: str | None = None,
    skip_rendering: bool = False,
    skip_text_generation: bool = False,
    output_dir: str | None = None,
    gradient_direction: GradientDirection | None = None,
    gradient_colors: list[str] | None = None,
    gradient_stops: list[float] | None = None,
    texture_type: TextureType | None = None,
    texture_opacity: float | None = None,
    texture_blend_mode: TextureBlendMode | None = None,
    animate: bool = False,
    anim_type: AnimType | None = None,
    anim_intensity: float | None = None,
    anim_speed: float | None = None,
    anim_loop: int | None = None,
    anim_seed: int | None = None,
    audio: bool = False,
    audio_voice: str | None = None,
    text_color: str | None = None,
    bg_music: bool = False,
    bg_music_prompt: str | None = None,
    bg_image: bool = False,
    bg_image_prompt: str | None = None,
    bg_image_path: str | None = None,
    bg_image_seed: int | None = None,
) -> dict:
    """Run the complete pipeline from payload to images.

    Args:
        payload: Validated monthly payload
        model: Optional AI model override
        skip_rendering: If True, skip image rendering
        skip_text_generation: If True, skip AI text generation
        output_dir: Optional custom output directory (default: outputs)
        animate: If True, produce animated video output
        anim_type: Animation type
        anim_intensity: Animation intensity (0.0-0.5)
        anim_speed: Animation speed (0.1-2.0)
        anim_loop: Loop duration in seconds
        anim_seed: Seed for deterministic animation
        audio: If True, generate TTS audio for each video
        audio_voice: Edge TTS voice name for audio generation
        text_color: Optional text color override. Auto-computed from background if not provided.
        bg_music: If True, generate background music via ACE-Step and mix with TTS. Implies animate+audio.
        bg_music_prompt: Optional music prompt. Auto-generated from monthly theme if not provided.

    Returns:
        Dictionary with pipeline results and outputs

    Raises:
        PipelineError: If any stage fails
    """
    plans_dir = Path(output_dir) / "plans" if output_dir else PLANS_DIR
    images_dir = Path(output_dir) / "images" if output_dir else IMAGES_DIR
    if output_dir:
        plans_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)

    if model:
        from src.config import defaults

        old_model = defaults.DEFAULT_AI_MODEL
        defaults.DEFAULT_AI_MODEL = model
    else:
        old_model = None

    from src.config.defaults import DEFAULT_TTS_VOICE

    if bg_music:
        animate = True
        audio = True

    try:
        # Stage 1: Resolve calendar
        logger.info("Stage 1: Resolving calendar...")
        calendar = resolve_calendar(payload)

        # Stage 2: AI Weekly Subtheme Derivation (if needed)
        if calendar.weekly_subthemes is None:
            logger.info("Stage 2a: Deriving weekly subthemes using AI...")
            weekly_subthemes = await generator.generate_weekly_subthemes(
                monthly_theme=calendar.monthly_theme,
                num_weeks=len(calendar.weeks),
            )
            calendar.weekly_subthemes = weekly_subthemes
            logger.info(f"  Derived {len(weekly_subthemes)} weekly subthemes")
        else:
            logger.info("Stage 2a: Using provided weekly subthemes (skipping AI derivation)")

        # Stage 2b: Generate weekly subtitles for display
        logger.info("Stage 2b: Generating weekly subtitles...")
        weekly_subtitles = {}
        if calendar.weekly_subthemes:
            for i, subtheme in enumerate(calendar.weekly_subthemes, 1):
                subtitle = await generator.generate_weekly_subtitle(subtheme)
                weekly_subtitles[i] = subtitle
                logger.info(f"  Week {i}: {subtitle}")

        # Stage 3: AI Monthly Slot Planning
        logger.info("Stage 2c: Planning monthly slots using AI...")
        slot_plan = await generator.plan_monthly_slots(calendar)
        logger.info(f"  Generated slot plan for {len(slot_plan)} dates")

        # Stage 4: Apply and validate slot plan
        logger.info("Stage 3: Applying and validating slot plan...")
        scheduler.validate_slot_plan(calendar, slot_plan)
        schedule = scheduler.apply_slot_plan(calendar, slot_plan)
        logger.info(f"  Created schedule with {len(schedule.slots)} total slots")

        # Save slot plan for inspection
        plan_path = _save_plan(
            calendar,
            slot_plan,
            schedule,
            plans_dir,
            weekly_subtitles,
            payload.style_preset,
            background_color,
            gradient_direction,
            gradient_colors,
            gradient_stops,
            texture_type,
            texture_opacity,
            texture_blend_mode,
            animate=animate,
            anim_type=anim_type,
            anim_intensity=anim_intensity,
            anim_speed=anim_speed,
            anim_loop=anim_loop,
            anim_seed=anim_seed,
        )
        logger.info(f"  Saved slot plan: {plan_path}")

        # Stage 5: AI Monthly Text Generation
        if not skip_text_generation:
            logger.info("Stage 4: Generating daily text using AI...")
            generated_texts = {}

            # Sort slots by date to ensure chronological processing
            sorted_slots = sorted(
                [s for s in schedule.slots if s.is_automated],
                key=lambda s: s.date,
            )

            # Accumulate generated texts to avoid duplication
            previous_texts: list[str] = []

            for slot in sorted_slots:
                try:
                    text = await generator.generate_daily_text(
                        slot_type=slot.slot_type,
                        monthly_theme=calendar.monthly_theme,
                        weekly_subtheme=slot.subtheme or "",
                        previously_generated=previous_texts,
                    )
                    generated_texts[slot.date] = text
                    previous_texts.append(text)
                    logger.info(f"  Generated text for {slot.date}")
                except AIGenerationError as e:
                    logger.info(f"  Warning: Failed to generate text for {slot.date}: {e}")
                    generated_texts[slot.date] = ""
        else:
            logger.info("Stage 4: Skipping text generation")
            generated_texts = {
                slot.date: "[PLACEHOLDER]" for slot in schedule.slots if slot.is_automated
            }

        # Save generated texts for re-rendering
        texts_path = _save_texts(calendar.year, calendar.month, generated_texts, plans_dir)
        logger.info(f"  Saved texts: {texts_path}")

        # Stage 4.5: TTS pre-pass (only when bg_music is enabled)
        tts_paths: dict[str, str] = {}
        tts_durations: dict[str, float] = {}
        monthly_music_path: str | None = None
        actual_music_prompt: str | None = None

        if bg_music and not skip_rendering:
            logger.info("Stage 4.5: TTS pre-pass (generating all TTS audio)...")
            import tempfile
            from src.renderer.tts import generate_tts, get_audio_duration

            for slot in schedule.slots:
                if slot.is_automated:
                    text = generated_texts.get(slot.date, "")
                    if text:
                        tts_tmp = tempfile.NamedTemporaryFile(
                            suffix=".mp3", delete=False, dir=str(images_dir)
                        )
                        tts_tmp.close()
                        tts_path = tts_tmp.name
                        logger.info(f"  TTS for {slot.date}...")
                        await generate_tts(
                            text=text,
                            output_path=tts_path,
                            voice=audio_voice or DEFAULT_TTS_VOICE,
                        )
                        dur = get_audio_duration(tts_path)
                        tts_paths[slot.date] = tts_path
                        tts_durations[slot.date] = dur
                        logger.info(f"    {dur:.1f}s")

            if not tts_durations:
                logger.info("  No TTS generated, skipping music")
                bg_music = False
            else:
                # Stage 4.6: Generate monthly background music
                logger.info("Stage 4.6: Generating monthly background music...")
                from src.renderer.music_gen import (
                    calculate_music_duration,
                    generate_background_music,
                    generate_music_prompt_from_theme,
                )

                if bg_music_prompt:
                    actual_music_prompt = bg_music_prompt
                else:
                    logger.info("  Auto-generating music prompt from theme...")
                    actual_music_prompt = await generate_music_prompt_from_theme(
                        calendar.monthly_theme
                    )

                max_tts = max(tts_durations.values())
                music_dur = calculate_music_duration(max_tts)
                audio_dir = images_dir / "audio"
                audio_dir.mkdir(parents=True, exist_ok=True)
                monthly_music_path = str(audio_dir / "bg_music.wav")

                logger.info(f"  Prompt: {actual_music_prompt}")
                logger.info(f"  Duration: {music_dur:.1f}s (max TTS: {max_tts:.1f}s)")
                await generate_background_music(
                    prompt=actual_music_prompt,
                    duration=music_dur,
                    output_path=monthly_music_path,
                )
                logger.info(f"  Music saved: {monthly_music_path}")

                with open(plan_path, "r", encoding="utf-8") as f:
                    plan_update = json.load(f)
                plan_update["render_config"]["bg_music"] = True
                plan_update["render_config"]["bg_music_prompt"] = actual_music_prompt
                plan_update["render_config"]["bg_music_path"] = monthly_music_path
                with open(plan_path, "w", encoding="utf-8") as f:
                    json.dump(plan_update, f, indent=2, ensure_ascii=False)
                logger.info(f"  Updated plan with music config")

        # Stage 5.5: Background image generation (once per month)
        effective_bg_image_path = bg_image_path
        if bg_image and not skip_rendering and not bg_image_path:
            import tempfile

            from src.renderer import image_gen as img_gen

            if not bg_image_prompt:
                logger.info("  Auto-generating background image prompt from theme...")
                bg_image_prompt = await img_gen.generate_image_prompt_from_theme(
                    calendar.monthly_theme
                )
                logger.info(f"  Image prompt: {bg_image_prompt}")

            image_dir = images_dir / "ai_backgrounds"
            image_dir.mkdir(parents=True, exist_ok=True)
            bg_image_out = str(image_dir / "bg_image.png")

            logger.info(f"  Generating background image (this may take several minutes on CPU)...")
            effective_bg_image_path = await img_gen.generate_background_image(
                prompt=bg_image_prompt,
                output_path=bg_image_out,
                seed=bg_image_seed,
            )
            logger.info(f"  Background image saved: {effective_bg_image_path}")

            with open(plan_path, "r", encoding="utf-8") as f:
                plan_update = json.load(f)
            plan_update["render_config"]["bg_image"] = True
            plan_update["render_config"]["bg_image_prompt"] = bg_image_prompt
            plan_update["render_config"]["bg_image_path"] = effective_bg_image_path
            if bg_image_seed is not None:
                plan_update["render_config"]["bg_image_seed"] = bg_image_seed
            with open(plan_path, "w", encoding="utf-8") as f:
                json.dump(plan_update, f, indent=2, ensure_ascii=False)

        # Stage 6: Render images or videos
        if not skip_rendering:
            if animate:
                logger.info("Stage 5: Rendering animated videos...")
            else:
                logger.info("Stage 5: Rendering images...")
            rendered_images = []

            for slot in schedule.slots:
                if slot.is_automated:
                    try:
                        text = generated_texts.get(slot.date, "")
                        if text:
                            year, month, day = map(int, slot.date.split("-"))

                            slot_info = {
                                "type": slot.slot_type.value,
                                "year": year,
                                "month": month,
                                "day": day,
                                "week_number": str(slot.week_number),
                                "subtheme": slot.subtheme or "",
                                "subtheme_subtitle": weekly_subtitles.get(slot.week_number, ""),
                                "monthly_theme": calendar.monthly_theme,
                            }

                            if animate:
                                output_path = html_renderer.get_video_output_path(
                                    year=year,
                                    month=month,
                                    day=day,
                                    monthly_theme=calendar.monthly_theme,
                                    week_number=slot.week_number,
                                    subtheme=weekly_subtitles.get(
                                        slot.week_number, slot.subtheme or ""
                                    ),
                                    slot_type=slot.slot_type.value,
                                    images_dir=images_dir,
                                )

                                audio_path = None
                                video_dur = None

                                if bg_music and slot.date in tts_paths:
                                    import tempfile
                                    from src.renderer.audio_mix import prepare_slot_audio
                                    from src.renderer.music_gen import calculate_slot_video_duration

                                    slot_tts_path = tts_paths[slot.date]
                                    slot_tts_dur = tts_durations[slot.date]
                                    slot_video_dur = calculate_slot_video_duration(slot_tts_dur)

                                    mixed_tmp = tempfile.NamedTemporaryFile(
                                        suffix=".mp3", delete=False, dir=str(images_dir)
                                    )
                                    mixed_tmp.close()
                                    logger.info(f"  Mixing audio for {slot.date}...")
                                    audio_path, video_dur = prepare_slot_audio(
                                        tts_path=slot_tts_path,
                                        music_path=monthly_music_path or "",
                                        output_path=mixed_tmp.name,
                                        tts_duration=slot_tts_dur,
                                        slot_video_duration=slot_video_dur,
                                    )

                                elif audio and text:
                                    import tempfile
                                    from src.renderer.tts import generate_tts

                                    audio_tmp = tempfile.NamedTemporaryFile(
                                        suffix=".mp3", delete=False, dir=str(images_dir)
                                    )
                                    audio_tmp.close()
                                    audio_path = audio_tmp.name
                                    logger.info(f"  Generating TTS audio...")
                                    await generate_tts(
                                        text=text,
                                        output_path=audio_path,
                                        voice=audio_voice or DEFAULT_TTS_VOICE,
                                    )

                                await html_renderer.render_animated_video(
                                    text=text,
                                    slot_info=slot_info,
                                    output_path=output_path,
                                    style_preset=payload.style_preset,
                                    background_color=background_color,
                                    gradient_direction=gradient_direction,
                                    gradient_colors=gradient_colors,
                                    gradient_stops=gradient_stops,
                                    texture_type=texture_type,
                                    texture_opacity=texture_opacity,
                                    texture_blend_mode=texture_blend_mode,
                                    anim_type=anim_type or "drift",
                                    anim_intensity=anim_intensity
                                    if anim_intensity is not None
                                    else 0.2,
                                    anim_speed=anim_speed if anim_speed is not None else 1.0,
                                    anim_loop=anim_loop if anim_loop is not None else 60,
                                    anim_seed=anim_seed,
                                    audio_path=audio_path,
                                    text_color=text_color,
                                    video_duration=video_dur,
                                    background_image_path=effective_bg_image_path,
                                )

                            else:
                                output_path = html_renderer.get_output_path(
                                    year=year,
                                    month=month,
                                    day=day,
                                    monthly_theme=calendar.monthly_theme,
                                    week_number=slot.week_number,
                                    subtheme=weekly_subtitles.get(
                                        slot.week_number, slot.subtheme or ""
                                    ),
                                    slot_type=slot.slot_type.value,
                                    images_dir=images_dir,
                                )

                                await html_renderer.render_text_to_image(
                                    text=text,
                                    slot_info=slot_info,
                                    output_path=output_path,
                                    style_preset=payload.style_preset,
                                    background_color=background_color,
                                    gradient_direction=gradient_direction,
                                    gradient_colors=gradient_colors,
                                    gradient_stops=gradient_stops,
                                    texture_type=texture_type,
                                    texture_opacity=texture_opacity,
                                    texture_blend_mode=texture_blend_mode,
                                    text_color=text_color,
                                    background_image_path=effective_bg_image_path,
                                )
                            rendered_images.append(output_path)
                            logger.info(f"  Rendered: {output_path}")
                    except Exception as e:
                        logger.info(f"  Warning: Failed to render {slot.date}: {e}")

            label = "videos" if animate else "images"
            logger.info(f"  Rendered {len(rendered_images)} {label}")
        else:
            logger.info("Stage 5: Skipping image rendering")
            rendered_images = []

        # Return results
        return {
            "calendar": calendar,
            "schedule": schedule,
            "slot_plan": slot_plan,
            "generated_texts": generated_texts,
            "rendered_images": rendered_images,
            "plan_path": plan_path,
            "texts_path": texts_path,
        }

    except Exception as e:
        if isinstance(e, PipelineError):
            raise
        raise PipelineError(f"Pipeline failed: {e}") from e
    finally:
        if old_model is not None:
            from src.config import defaults
            defaults.DEFAULT_AI_MODEL = old_model


def _save_plan(
    calendar,  # ResolvedCalendar
    slot_plan: dict[str, str],
    schedule,  # scheduler.DailySlotSchedule
    plans_dir: Path | None = None,
    weekly_subtitles: dict[int, str] | None = None,
    style_preset: str = "default",
    background_color: str | None = None,
    gradient_direction: GradientDirection | None = None,
    gradient_colors: list[str] | None = None,
    gradient_stops: list[float] | None = None,
    texture_type: TextureType | None = None,
    texture_opacity: float | None = None,
    texture_blend_mode: TextureBlendMode | None = None,
    animate: bool = False,
    anim_type: AnimType | None = None,
    anim_intensity: float | None = None,
    anim_speed: float | None = None,
    anim_loop: int | None = None,
    anim_seed: int | None = None,
    bg_music: bool = False,
    bg_music_prompt: str | None = None,
    bg_music_path: str | None = None,
) -> str:
    """Save slot plan to JSON file.

    Args:
        calendar: Resolved calendar
        slot_plan: Date to slot type mapping
        schedule: Complete daily slot schedule
        plans_dir: Optional custom directory for plans
        weekly_subtitles: Optional dict of week number to subtitle
        style_preset: Style preset name
        background_color: Optional background color override
        gradient_direction: Optional gradient direction
        gradient_colors: Optional gradient colors
        gradient_stops: Optional gradient stops
        texture_type: Optional texture type
        texture_opacity: Optional texture opacity
        texture_blend_mode: Optional texture blend mode

    Returns:
        Path to saved plan file
    """
    dir_path = plans_dir or PLANS_DIR
    filename = f"{calendar.year}-{calendar.month:02d}_plan.json"
    path = dir_path / filename

    render_config = {
        "style_preset": style_preset,
        "background_color": background_color,
    }
    if gradient_direction is not None:
        render_config["gradient_direction"] = gradient_direction
    if gradient_colors is not None:
        render_config["gradient_colors"] = gradient_colors
    if gradient_stops is not None:
        render_config["gradient_stops"] = gradient_stops
    if texture_type is not None:
        render_config["texture_type"] = texture_type
    if texture_opacity is not None:
        render_config["texture_opacity"] = texture_opacity
    if texture_blend_mode is not None:
        render_config["texture_blend_mode"] = texture_blend_mode
    if animate:
        render_config["animate"] = True
        if anim_type is not None:
            render_config["anim_type"] = anim_type
        if anim_intensity is not None:
            render_config["anim_intensity"] = anim_intensity
        if anim_speed is not None:
            render_config["anim_speed"] = anim_speed
        if anim_loop is not None:
            render_config["anim_loop"] = anim_loop
        if anim_seed is not None:
            render_config["anim_seed"] = anim_seed
    if bg_music:
        render_config["bg_music"] = True
        if bg_music_prompt:
            render_config["bg_music_prompt"] = bg_music_prompt
        if bg_music_path:
            render_config["bg_music_path"] = bg_music_path

    plan_data = {
        "year": calendar.year,
        "month": calendar.month,
        "monthly_theme": calendar.monthly_theme,
        "weekly_subthemes": calendar.weekly_subthemes,
        "weekly_subtitles": weekly_subtitles,
        "weekly_subthemes_source": schedule.weekly_subthemes_source,
        "render_config": render_config,
        "slot_plan": slot_plan,
        "schedule_summary": [
            {
                "date": slot.date,
                "weekday": slot.weekday,
                "week_number": slot.week_number,
                "slot_type": slot.slot_type.value,
                "subtheme": slot.subtheme,
                "is_automated": slot.is_automated,
            }
            for slot in schedule.slots
        ],
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan_data, f, indent=2, ensure_ascii=False)

    return str(path)


def _save_texts(
    year: int,
    month: int,
    generated_texts: dict[str, str],
    plans_dir: Path | None = None,
) -> str:
    """Save generated texts to JSON file.

    Args:
        year: Year of the content
        month: Month of the content
        generated_texts: Dict mapping date strings to generated text
        plans_dir: Optional custom directory for plans

    Returns:
        Path to saved texts file
    """
    dir_path = plans_dir or PLANS_DIR
    filename = f"{year}-{month:02d}_texts.json"
    path = dir_path / filename

    texts_data = {
        "year": year,
        "month": month,
        "texts": generated_texts,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(texts_data, f, indent=2, ensure_ascii=False)

    return str(path)


async def validate_and_run(
    payload_path: str,
    background_color: str | None = None,
    output_dir: str | None = None,
    gradient_direction: GradientDirection | None = None,
    gradient_colors: list[str] | None = None,
    gradient_stops: list[float] | None = None,
    texture_type: TextureType | None = None,
    texture_opacity: float | None = None,
    texture_blend_mode: TextureBlendMode | None = None,
    **kwargs,
) -> dict:
    """Validate payload and run pipeline.

    Args:
        payload_path: Path to payload JSON file
        background_color: Optional background color override
        output_dir: Optional custom output directory
        gradient_direction: Optional gradient direction
        gradient_colors: Optional gradient colors
        gradient_stops: Optional gradient stops
        texture_type: Optional texture type
        texture_opacity: Optional texture opacity
        texture_blend_mode: Optional texture blend mode
        **kwargs: Additional arguments for run_full_pipeline

    Returns:
        Pipeline results
    """
    # Load payload
    with open(payload_path, "r", encoding="utf-8") as f:
        payload_data = json.load(f)

    # Parse and validate payload
    payload = schema.MonthlyPayload(**payload_data)
    validation.validate_payload(payload)

    logger.info(f"Validated payload for {payload.year}-{payload.month:02d}: {payload.monthly_theme}")

    # Run pipeline
    return await run_full_pipeline(
        payload,
        background_color=background_color,
        output_dir=output_dir,
        gradient_direction=gradient_direction,
        gradient_colors=gradient_colors,
        gradient_stops=gradient_stops,
        texture_type=texture_type,
        texture_opacity=texture_opacity,
        texture_blend_mode=texture_blend_mode,
        **kwargs,
    )
