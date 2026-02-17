"""Pipeline orchestrator for end-to-end execution."""

import asyncio
import json
from pathlib import Path
from typing import Literal

from src.ai_generator import generator
from src.config import defaults
from src.config.defaults import (
    IMAGE_FORMAT,
    IMAGES_DIR,
    PLANS_DIR,
)
from src.errors.exceptions import (
    AIGenerationError,
    PipelineError,
)
from src.payload import schema, validation
from src.renderer import html_renderer
from src.slots import scheduler
from src.slots.enum import SlotFunction
from src.weekly_calendar.resolver import resolve_calendar, ResolvedCalendar


async def run_full_pipeline(
    payload: schema.MonthlyPayload,
    model: str | None = None,
    background_color: str | None = None,
    skip_rendering: bool = False,
    skip_text_generation: bool = False,
    output_dir: str | None = None,
) -> dict:
    """Run the complete pipeline from payload to images.

    Args:
        payload: Validated monthly payload
        model: Optional AI model override
        skip_rendering: If True, skip image rendering
        skip_text_generation: If True, skip AI text generation
        output_dir: Optional custom output directory (default: outputs)

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

    try:
        # Stage 1: Resolve calendar
        print("Stage 1: Resolving calendar...")
        calendar = resolve_calendar(payload)

        # Stage 2: AI Weekly Subtheme Derivation (if needed)
        if calendar.weekly_subthemes is None:
            print("Stage 2a: Deriving weekly subthemes using AI...")
            weekly_subthemes = await generator.generate_weekly_subthemes(
                monthly_theme=calendar.monthly_theme,
                num_weeks=len(calendar.weeks),
            )
            calendar.weekly_subthemes = weekly_subthemes
            print(f"  Derived {len(weekly_subthemes)} weekly subthemes")
        else:
            print("Stage 2a: Using provided weekly subthemes (skipping AI derivation)")

        # Stage 2b: Generate weekly subtitles for display
        print("Stage 2b: Generating weekly subtitles...")
        weekly_subtitles = {}
        if calendar.weekly_subthemes:
            for i, subtheme in enumerate(calendar.weekly_subthemes, 1):
                subtitle = await generator.generate_weekly_subtitle(subtheme)
                weekly_subtitles[i] = subtitle
                print(f"  Week {i}: {subtitle}")

        # Stage 3: AI Monthly Slot Planning
        print("Stage 2c: Planning monthly slots using AI...")
        slot_plan = await generator.plan_monthly_slots(calendar)
        print(f"  Generated slot plan for {len(slot_plan)} dates")

        # Stage 4: Apply and validate slot plan
        print("Stage 3: Applying and validating slot plan...")
        scheduler.validate_slot_plan(calendar, slot_plan)
        schedule = scheduler.apply_slot_plan(calendar, slot_plan)
        print(f"  Created schedule with {len(schedule.slots)} total slots")

        # Save slot plan for inspection
        plan_path = _save_plan(calendar, slot_plan, schedule, plans_dir, weekly_subtitles)
        print(f"  Saved slot plan: {plan_path}")

        # Stage 5: AI Monthly Text Generation
        if not skip_text_generation:
            print("Stage 4: Generating daily text using AI...")
            generated_texts = {}

            for slot in schedule.slots:
                if slot.is_automated:
                    try:
                        text = await generator.generate_daily_text(
                            slot_type=slot.slot_type,
                            monthly_theme=calendar.monthly_theme,
                            weekly_subtheme=slot.subtheme or "",
                        )
                        generated_texts[slot.date] = text
                        print(f"  Generated text for {slot.date}")
                    except AIGenerationError as e:
                        print(f"  Warning: Failed to generate text for {slot.date}: {e}")
                        generated_texts[slot.date] = ""
        else:
            print("Stage 4: Skipping text generation")
            generated_texts = {slot.date: "[PLACEHOLDER]" for slot in schedule.slots if slot.is_automated}

        # Stage 6: Render images
        if not skip_rendering:
            print("Stage 5: Rendering images...")
            rendered_images = []

            for slot in schedule.slots:
                if slot.is_automated:
                    try:
                        text = generated_texts.get(slot.date, "")
                        if text:
                            # Parse date for filename
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

                            output_path = html_renderer.get_output_path(
                                year=year,
                                month=month,
                                day=day,
                                monthly_theme=calendar.monthly_theme,
                                week_number=slot.week_number,
                                subtheme=weekly_subtitles.get(slot.week_number, slot.subtheme or ""),
                                slot_type=slot.slot_type.value,
                                images_dir=images_dir,
                            )

                            await html_renderer.render_text_to_image(
                                text=text,
                                slot_info=slot_info,
                                output_path=output_path,
                                style_preset=payload.style_preset,
                                background_color=background_color,
                            )
                            rendered_images.append(output_path)
                            print(f"  Rendered: {output_path}")
                    except Exception as e:
                        print(f"  Warning: Failed to render {slot.date}: {e}")

            print(f"  Rendered {len(rendered_images)} images")
        else:
            print("Stage 5: Skipping image rendering")
            rendered_images = []

        # Return results
        return {
            "calendar": calendar,
            "schedule": schedule,
            "slot_plan": slot_plan,
            "generated_texts": generated_texts,
            "rendered_images": rendered_images,
            "plan_path": plan_path,
        }

    except Exception as e:
        if isinstance(e, PipelineError):
            raise
        raise PipelineError(f"Pipeline failed: {e}") from e


def _save_plan(
    calendar,  # ResolvedCalendar
    slot_plan: dict[str, str],
    schedule,  # scheduler.DailySlotSchedule
    plans_dir: Path | None = None,
    weekly_subtitles: dict[int, str] | None = None,
) -> str:
    """Save slot plan to JSON file.

    Args:
        calendar: Resolved calendar
        slot_plan: Date to slot type mapping
        schedule: Complete daily slot schedule
        plans_dir: Optional custom directory for plans
        weekly_subtitles: Optional dict of week number to subtitle

    Returns:
        Path to saved plan file
    """
    dir_path = plans_dir or PLANS_DIR
    filename = f"{calendar.year}-{calendar.month:02d}_plan.json"
    path = dir_path / filename

    plan_data = {
        "year": calendar.year,
        "month": calendar.month,
        "monthly_theme": calendar.monthly_theme,
        "weekly_subthemes": calendar.weekly_subthemes,
        "weekly_subtitles": weekly_subtitles,
        "weekly_subthemes_source": schedule.weekly_subthemes_source,
        "slot_plan": slot_plan,
        "schedule_summary": [
            {
                "date": slot.date,
                "weekday": slot.weekday,
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


async def validate_and_run(payload_path: str, background_color: str | None = None, output_dir: str | None = None, **kwargs) -> dict:
    """Validate payload and run pipeline.

    Args:
        payload_path: Path to payload JSON file
        background_color: Optional background color override
        output_dir: Optional custom output directory
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

    print(f"Validated payload for {payload.year}-{payload.month:02d}: {payload.monthly_theme}")

    # Run pipeline
    return await run_full_pipeline(payload, background_color=background_color, output_dir=output_dir, **kwargs)
