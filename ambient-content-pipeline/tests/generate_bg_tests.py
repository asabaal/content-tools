"""Generate background test images using existing April content.

Usage:
    cd ambient-content-pipeline
    python -m tests.generate_bg_tests

Reads April 2026 plan and texts, renders 4 test images with different
gradient/texture configurations to outputs/background_tests/.
"""

import asyncio
import json
from pathlib import Path

from src.config.defaults import (
    BACKGROUND_TEST_DIR,
    COLORFUL_PRESETS,
    DEFAULT_IMAGE_WIDTH,
    DEFAULT_IMAGE_HEIGHT,
)
from src.renderer.template_builder import build_html
from src.renderer.html_renderer import _render_html_to_image

PLAN_PATH = Path("outputs/202604/plans/2026-04_plan.json")
TEXTS_PATH = Path("outputs/202604/plans/2026-04_texts.json")

TEST_CASES = [
    {
        "id": "test1_vertical_2color_notexture",
        "date": "2026-04-06",
        "gradient_direction": "vertical_top_bottom",
        "gradient_colors": ["#E67E22", "#2C3E50"],
        "gradient_stops": None,
        "texture_type": "none",
        "texture_opacity": None,
        "texture_blend_mode": None,
    },
    {
        "id": "test2_diagonal_3color_noise_fine",
        "date": "2026-04-07",
        "gradient_direction": "diagonal_tl_br",
        "gradient_colors": ["#2C3E50", "#E67E22", "#F1C40F"],
        "gradient_stops": None,
        "texture_type": "noise_fine",
        "texture_opacity": 0.7,
        "texture_blend_mode": "normal",
    },
    {
        "id": "test3_radial_2color_vignette_soft",
        "date": "2026-04-08",
        "gradient_direction": "radial_center",
        "gradient_colors": ["#1ABC9C", "#8E44AD"],
        "gradient_stops": None,
        "texture_type": "vignette_soft",
        "texture_opacity": 0.4,
        "texture_blend_mode": "normal",
    },
    {
        "id": "test4_horizontal_4color_grain_film",
        "date": "2026-04-09",
        "gradient_direction": "horizontal_left_right",
        "gradient_colors": ["#8E44AD", "#2980B9", "#27AE60", "#F39C12"],
        "gradient_stops": None,
        "texture_type": "grain_film",
        "texture_opacity": 0.5,
        "texture_blend_mode": "normal",
    },
]


async def main() -> None:
    if not PLAN_PATH.exists():
        print(f"Error: Plan file not found at {PLAN_PATH}")
        return
    if not TEXTS_PATH.exists():
        print(f"Error: Texts file not found at {TEXTS_PATH}")
        return

    with open(PLAN_PATH, "r", encoding="utf-8") as f:
        plan_data = json.load(f)
    with open(TEXTS_PATH, "r", encoding="utf-8") as f:
        texts_data = json.load(f)

    generated_texts = texts_data.get("texts", {})
    weekly_subtitles = plan_data.get("weekly_subtitles", {})
    monthly_theme = plan_data.get("monthly_theme", "")
    slot_lookup = {
        slot["date"]: slot for slot in plan_data.get("schedule_summary", [])
    }
    render_config = plan_data.get("render_config", {})
    style_preset = render_config.get("style_preset", "default")

    BACKGROUND_TEST_DIR.mkdir(parents=True, exist_ok=True)

    for tc in TEST_CASES:
        date = tc["date"]
        text = generated_texts.get(date, "")
        slot = slot_lookup.get(date)

        if not text:
            print(f"  Skipping {tc['id']}: no text for {date}")
            continue
        if not slot:
            print(f"  Skipping {tc['id']}: no slot for {date}")
            continue

        year, month, day = map(int, date.split("-"))
        slot_info = {
            "type": slot["slot_type"],
            "year": year,
            "month": month,
            "day": day,
            "week_number": str(slot.get("week_number", 1)),
            "subtheme": slot.get("subtheme", ""),
            "subtheme_subtitle": weekly_subtitles.get(slot.get("week_number", 1), ""),
            "monthly_theme": monthly_theme,
        }

        preset = COLORFUL_PRESETS[style_preset].copy()
        html_content = build_html(
            text,
            slot_info,
            preset,
            DEFAULT_IMAGE_WIDTH,
            DEFAULT_IMAGE_HEIGHT,
            gradient_direction=tc["gradient_direction"],
            gradient_colors=tc["gradient_colors"],
            gradient_stops=tc["gradient_stops"],
            texture_type=tc["texture_type"],
            texture_opacity=tc["texture_opacity"],
            texture_blend_mode=tc["texture_blend_mode"],
        )

        output_path = BACKGROUND_TEST_DIR / f"{tc['id']}.png"
        if output_path.exists():
            stem = output_path.stem
            output_path = BACKGROUND_TEST_DIR / f"{stem}_v2.png"

        try:
            await _render_html_to_image(
                html_content,
                str(output_path),
                DEFAULT_IMAGE_WIDTH,
                DEFAULT_IMAGE_HEIGHT,
            )
            print(f"  Generated: {output_path}")
        except Exception as e:
            print(f"  Failed {tc['id']}: {e}")

    print(f"\nDone. Images saved to {BACKGROUND_TEST_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
