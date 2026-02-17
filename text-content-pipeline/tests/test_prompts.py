"""Tests for AI prompt templates."""

import pytest
from src.ai_generator.prompts import (
    format_weekly_subthemes,
    format_calendar_structure,
    WEEKLY_SUBTHEME_PROMPT,
    WEEKLY_SUBTITLE_PROMPT,
    MONTHLY_SLOT_PLANNING_PROMPT,
    TEXT_GENERATION_PROMPTS,
)
from src.slots.enum import SlotFunction


def test_format_weekly_subthemes_basic() -> None:
    """Test formatting weekly subthemes."""
    subthemes = ["Week 1", "Week 2", "Week 3"]
    result = format_weekly_subthemes(subthemes)
    
    assert "Week 1: Week 1" in result
    assert "Week 2: Week 2" in result
    assert "Week 3: Week 3" in result


def test_format_weekly_subthemes_empty() -> None:
    """Test formatting empty subtheme list."""
    result = format_weekly_subthemes([])
    assert result == ""


def test_format_calendar_structure_basic() -> None:
    """Test formatting calendar structure."""
    calendar_info = [
        {
            "week_number": 1,
            "monday_date": "2026-02-02",
            "sunday_date": "2026-02-08",
            "subtheme": "Test Subtheme",
            "month": 2,
            "year": 2026,
            "is_video_week": False,
        }
    ]
    
    result = format_calendar_structure(calendar_info)
    
    assert "Week 1:" in result
    assert "2026-02-02 - 2026-02-08" in result
    assert "Subtheme: Test Subtheme" in result
    assert "Video week: False" in result


def test_format_calendar_structure_with_automated_dates() -> None:
    """Test formatting calendar with automated dates."""
    calendar_info = [
        {
            "week_number": 1,
            "monday_date": "2026-02-02",
            "sunday_date": "2026-02-08",
            "subtheme": "Sub",
            "month": 2,
            "year": 2026,
            "is_video_week": False,
        }
    ]
    automated_dates = ["2026-02-02", "2026-02-03"]
    
    result = format_calendar_structure(calendar_info, automated_dates)
    
    assert "Automated dates requiring slot assignments (2 total):" in result
    assert "- 2026-02-02 (Monday)" in result
    assert "- 2026-02-03 (Tuesday)" in result


def test_weekly_subtheme_prompt_exists() -> None:
    """Test that weekly subtheme prompt template exists."""
    assert WEEKLY_SUBTHEME_PROMPT is not None
    assert "Monthly theme:" in WEEKLY_SUBTHEME_PROMPT
    assert "Number of weeks in month:" in WEEKLY_SUBTHEME_PROMPT


def test_monthly_slot_planning_prompt_exists() -> None:
    """Test that monthly slot planning prompt template exists."""
    assert MONTHLY_SLOT_PLANNING_PROMPT is not None
    assert "Monthly theme:" in MONTHLY_SLOT_PLANNING_PROMPT
    assert "Weekly subthemes:" in MONTHLY_SLOT_PLANNING_PROMPT


def test_text_generation_prompts_exist() -> None:
    """Test that all text generation prompts exist."""
    assert len(TEXT_GENERATION_PROMPTS) == 6
    
    required_slots = [
        SlotFunction.DECLARATIVE_STATEMENT,
        SlotFunction.EXCERPT,
        SlotFunction.PROCESS_NOTE,
        SlotFunction.UNANSWERED_QUESTION,
        SlotFunction.REFRAMING,
        SlotFunction.QUIET_OBSERVATION,
    ]
    
    for slot in required_slots:
        assert slot in TEXT_GENERATION_PROMPTS
        assert "Monthly theme:" in TEXT_GENERATION_PROMPTS[slot]
        assert "Weekly subtheme:" in TEXT_GENERATION_PROMPTS[slot]


def test_text_generation_prompt_declarative_statement() -> None:
    """Test declarative statement prompt has correct instructions."""
    prompt = TEXT_GENERATION_PROMPTS[SlotFunction.DECLARATIVE_STATEMENT]
    
    assert "One sentence only" in prompt
    assert "A grounded, factual statement" in prompt
    assert "No question marks" in prompt


def test_text_generation_prompt_excerpt() -> None:
    """Test excerpt prompt has correct instructions."""
    prompt = TEXT_GENERATION_PROMPTS[SlotFunction.EXCERPT]
    
    assert "A single paragraph or quote" in prompt
    assert "No commentary added" in prompt


def test_text_generation_prompt_process_note() -> None:
    """Test process note prompt has correct instructions."""
    prompt = TEXT_GENERATION_PROMPTS[SlotFunction.PROCESS_NOTE]
    
    assert "reflective process note" in prompt
    assert "No conclusions or finality" in prompt


def test_text_generation_prompt_unanswered_question() -> None:
    """Test unanswered question prompt has correct instructions."""
    prompt = TEXT_GENERATION_PROMPTS[SlotFunction.UNANSWERED_QUESTION]
    
    assert "open-ended question" in prompt
    assert "No answer provided" in prompt


def test_text_generation_prompt_reframing() -> None:
    """Test reframing prompt has correct instructions."""
    prompt = TEXT_GENERATION_PROMPTS[SlotFunction.REFRAMING]
    
    assert "reframing statement" in prompt
    assert "not X, but Y" in prompt


def test_text_generation_prompt_quiet_observation() -> None:
    """Test quiet observation prompt has correct instructions."""
    prompt = TEXT_GENERATION_PROMPTS[SlotFunction.QUIET_OBSERVATION]
    
    assert "quiet observation" in prompt
    assert "No interpretation or judgment" in prompt


def test_format_calendar_structure_multiple_weeks() -> None:
    """Test formatting calendar with multiple weeks."""
    calendar_info = [
        {
            "week_number": 1,
            "monday_date": "2026-02-02",
            "sunday_date": "2026-02-08",
            "subtheme": "Week 1",
            "month": 2,
            "year": 2026,
            "is_video_week": False,
        },
        {
            "week_number": 2,
            "monday_date": "2026-02-09",
            "sunday_date": "2026-02-15",
            "subtheme": "Week 2",
            "month": 2,
            "year": 2026,
            "is_video_week": True,
        }
    ]
    
    result = format_calendar_structure(calendar_info)
    
    assert "Week 1:" in result
    assert "Week 2:" in result
    assert "Video week: False" in result
    assert "Video week: True" in result


def test_format_weekly_subthemes_long_subtheme() -> None:
    """Test formatting with long subtheme names."""
    subthemes = ["This is a very long subtheme name for testing"]
    result = format_weekly_subthemes(subthemes)
    
    assert "Week 1: This is a very long subtheme name for testing" in result


def test_weekly_subtitle_prompt_exists() -> None:
    """Test that weekly subtitle prompt template exists."""
    assert WEEKLY_SUBTITLE_PROMPT is not None
    assert "weekly_subtheme" in WEEKLY_SUBTITLE_PROMPT
    assert "3-6 words" in WEEKLY_SUBTITLE_PROMPT


def test_weekly_subtitle_prompt_formatting() -> None:
    """Test that weekly subtitle prompt can be formatted."""
    formatted = WEEKLY_SUBTITLE_PROMPT.format(
        weekly_subtheme="Week 1 Evidence of the walk"
    )
    assert "Week 1 Evidence of the walk" in formatted


def test_text_generation_prompts_have_max_words() -> None:
    """Test that all text generation prompts include max_words placeholder."""
    for slot, prompt in TEXT_GENERATION_PROMPTS.items():
        assert "{max_words}" in prompt, f"Missing max_words in {slot.value} prompt"


def test_text_generation_prompts_format_with_max_words() -> None:
    """Test that text generation prompts can be formatted with max_words."""
    for slot, prompt in TEXT_GENERATION_PROMPTS.items():
        formatted = prompt.format(
            monthly_theme="Test Theme",
            weekly_subtheme="Test Subtheme",
            max_words=50,
        )
        assert "50" in formatted
        assert "Test Theme" in formatted
        assert "Test Subtheme" in formatted
