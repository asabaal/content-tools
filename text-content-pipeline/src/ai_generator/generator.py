"""AI text and slot generation using Ollama."""

import json
from typing import Any

import httpx

from src.ai_generator import prompts
from src.weekly_calendar.resolver import ResolvedCalendar
from src.config.defaults import (
    AI_MAX_RETRIES,
    AI_TIMEOUT,
    AI_TEMPERATURE,
    DEFAULT_AI_BASE_URL,
    DEFAULT_AI_MODEL,
    MAX_WORDS_PER_SLOT,
)
from src.errors.exceptions import AIGenerationError, ModelUnavailableError
from src.slots.enum import SlotFunction


async def generate_weekly_subtitle(weekly_subtheme: str) -> str:
    """Generate a short subtitle from a weekly subtheme.

    Args:
        weekly_subtheme: The full weekly subtheme text

    Returns:
        Short subtitle (3-6 words)

    Raises:
        AIGenerationError: If generation fails
    """
    prompt = prompts.WEEKLY_SUBTITLE_PROMPT.format(
        weekly_subtheme=weekly_subtheme,
    )

    response = await _call_ollama(
        prompt=prompt,
        touchpoint="weekly_subtitle_generation",
    )

    return response.strip()


async def generate_weekly_subthemes(monthly_theme: str, num_weeks: int) -> list[str]:
    """Generate weekly subthemes using AI (touchpoint 1).

    Args:
        monthly_theme: The monthly theme to break down
        num_weeks: Number of weeks in the month

    Returns:
        List of weekly subthemes

    Raises:
        AIGenerationError: If generation fails
    """
    prompt = prompts.WEEKLY_SUBTHEME_PROMPT.format(
        monthly_theme=monthly_theme,
        num_weeks=num_weeks,
    )

    response = await _call_ollama(
        prompt=prompt,
        touchpoint="weekly_subtheme_derivation",
    )

    # Parse JSON response
    try:
        subthemes = json.loads(response)
        if not isinstance(subthemes, list):
            raise ValueError("Response is not a list")
        if len(subthemes) != num_weeks:
            raise ValueError(f"Expected {num_weeks} subthemes, got {len(subthemes)}")
        return [str(s) for s in subthemes]
    except json.JSONDecodeError as e:
        raise AIGenerationError(
            f"Failed to parse AI response as JSON: {e}",
            touchpoint="weekly_subtheme_derivation",
        )
    except ValueError as e:
        raise AIGenerationError(
            f"Invalid subthemes response: {e}",
            touchpoint="weekly_subtheme_derivation",
        )


async def plan_monthly_slots(calendar: ResolvedCalendar) -> dict[str, str]:
    """Generate monthly slot plan using AI (touchpoint 2).

    Args:
        calendar: Resolved calendar structure

    Returns:
        Mapping of date strings to slot type strings

    Raises:
        AIGenerationError: If generation fails
    """
    # Format weekly subthemes
    weekly_subthemes = calendar.weekly_subthemes or []
    weekly_subthemes_formatted = prompts.format_weekly_subthemes(weekly_subthemes)

    # Format calendar structure (including dates)
    calendar_structure = []
    automated_dates_list = []  # Explicit list of dates needing slots

    for week in calendar.weeks:
        # Collect Monday-Saturday dates
        from datetime import datetime, timedelta
        monday = datetime.strptime(week.monday_date, "%Y-%m-%d")
        week_dates = []
        for day_offset in range(6):
            date = monday + timedelta(days=day_offset)
            week_dates.append(date.strftime("%Y-%m-%d"))

        calendar_structure.append(
            {
                "week_number": week.week_number,
                "monday_date": week.monday_date,
                "sunday_date": week.sunday_date,
                "subtheme": week.subtheme,
                "is_video_week": week.is_video_week,
                "month": calendar.month,  # Add explicit month
                "year": calendar.year,  # Add explicit year
                "automated_dates": week_dates,  # Explicit dates for this week
            }
        )
        automated_dates_list.extend(week_dates)

    calendar_structure_formatted = prompts.format_calendar_structure(calendar_structure, sorted(automated_dates_list))

    prompt = prompts.MONTHLY_SLOT_PLANNING_PROMPT.format(
        monthly_theme=calendar.monthly_theme,
        weekly_subthemes_formatted=weekly_subthemes_formatted,
        calendar_structure_formatted=calendar_structure_formatted,
    )

    response = await _call_ollama(
        prompt=prompt,
        touchpoint="monthly_slot_planning",
    )

    # Parse JSON response
    try:
        slot_plan = json.loads(response)
        if not isinstance(slot_plan, dict):
            raise ValueError("Response is not a dictionary")
        return {str(k): str(v) for k, v in slot_plan.items()}
    except json.JSONDecodeError as e:
        raise AIGenerationError(
            f"Failed to parse AI response as JSON: {e}",
            touchpoint="monthly_slot_planning",
        )
    except ValueError as e:
        raise AIGenerationError(
            f"Invalid slot plan response: {e}",
            touchpoint="monthly_slot_planning",
        )


async def generate_daily_text(
    slot_type: SlotFunction,
    monthly_theme: str,
    weekly_subtheme: str,
    max_words: int | None = None,
    previously_generated: list[str] | None = None,
) -> str:
    """Generate text for a single daily slot using AI (touchpoint 3).

    Args:
        slot_type: The type of slot to generate
        monthly_theme: Monthly theme context
        weekly_subtheme: Weekly subtheme context
        max_words: Maximum word count (optional, uses defaults if not provided)
        previously_generated: List of previously generated texts to avoid duplication

    Returns:
        Generated plain text

    Raises:
        AIGenerationError: If generation fails
    """
    # Get max words from config if not provided
    if max_words is None:
        slot_type_str = slot_type.value if isinstance(slot_type, SlotFunction) else str(slot_type)
        max_words = MAX_WORDS_PER_SLOT.get(slot_type_str, 50)

    # Format previously generated section (empty if no previous posts)
    if previously_generated and len(previously_generated) > 0:
        formatted_prev = "\n".join(f"  - \"{text}\"" for text in previously_generated)
        previously_generated_section = f"Previously generated posts (do NOT repeat these concepts):\n{formatted_prev}\n"
    else:
        previously_generated_section = ""

    prompt = prompts.TEXT_GENERATION_PROMPTS[slot_type].format(
        monthly_theme=monthly_theme,
        weekly_subtheme=weekly_subtheme,
        max_words=max_words,
        previously_generated_section=previously_generated_section,
    )

    response = await _call_ollama(
        prompt=prompt,
        touchpoint="daily_text_generation",
    )

    # Clean up response
    text = response.strip()

    # Enforce max words (truncate if needed)
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words])
        # Try to end at a sentence boundary
        last_punct = max(text.rfind("."), text.rfind("!"), text.rfind("?"))
        if last_punct > max_words // 2:
            text = text[: last_punct + 1]

    return text


async def _call_ollama(prompt: str, touchpoint: str) -> str:
    """Call Ollama API for text generation.

    Args:
        prompt: The prompt to send
        touchpoint: Name of the AI touchpoint (for error reporting)

    Returns:
        Generated text response

    Raises:
        ModelUnavailableError: If model is not found
        AIGenerationError: If generation fails
    """
    url = f"{DEFAULT_AI_BASE_URL}/api/generate"

    payload = {
        "model": DEFAULT_AI_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": AI_TEMPERATURE,
            "top_p": 0.9,
        },
    }

    async with httpx.AsyncClient(timeout=AI_TIMEOUT) as client:
        for attempt in range(AI_MAX_RETRIES):
            try:
                response = await client.post(url, json=payload)

                if response.status_code == 404:
                    raise ModelUnavailableError(DEFAULT_AI_MODEL)

                response.raise_for_status()

                data = response.json()
                result = data.get("response", "").strip()
                if not result:
                    raise AIGenerationError(
                        "Empty response from Ollama",
                        touchpoint=touchpoint,
                    )
                return result

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ModelUnavailableError(DEFAULT_AI_MODEL)
                raise AIGenerationError(
                    f"HTTP error: {e}",
                    touchpoint=touchpoint,
                )
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt == AI_MAX_RETRIES - 1:
                    raise AIGenerationError(
                        f"Failed to connect to Ollama after {AI_MAX_RETRIES} attempts: {e}",
                        touchpoint=touchpoint,
                    )
                # Retry
                continue
            except Exception as e:
                raise AIGenerationError(
                    f"Unexpected error: {e}",
                    touchpoint=touchpoint,
                )

    raise AIGenerationError(  # pragma: no cover
        "Unexpected error in AI generation",
        touchpoint=touchpoint,
    )


async def check_model_available() -> bool:
    """Check if the default model is available in Ollama.

    Returns:
        True if model is available, False otherwise
    """
    url = f"{DEFAULT_AI_BASE_URL}/api/tags"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])

            for model in models:
                if model.get("name") == DEFAULT_AI_MODEL:
                    return True

            return False

    except Exception:
        return False
