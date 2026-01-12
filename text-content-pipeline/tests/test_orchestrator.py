"""Tests for pipeline orchestrator."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.pipeline import orchestrator
from src.payload.schema import MonthlyPayload, WeekRule, VideoWeek
from src.weekly_calendar.resolver import ResolvedCalendar, WeekInfo


@pytest.mark.asyncio
async def test_run_full_pipeline_derives_subthemes() -> None:
    """Test pipeline derives weekly subthemes when not provided."""
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=None,
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    resolved_calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=None,
        weeks=[],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    schedule = MagicMock()
    schedule.slots = []
    
    with patch("src.pipeline.orchestrator.resolve_calendar", return_value=resolved_calendar):
        with patch("src.pipeline.orchestrator.scheduler.apply_slot_plan", return_value=schedule):
            with patch("src.pipeline.orchestrator.scheduler.validate_slot_plan"):
                with patch("src.pipeline.orchestrator.generator.generate_weekly_subthemes", return_value=["W1", "W2"]):
                    with patch("src.pipeline.orchestrator.generator.plan_monthly_slots", return_value={}):
                        with patch("src.pipeline.orchestrator._save_plan"):
                            result = await orchestrator.run_full_pipeline(
                                payload,
                                skip_rendering=True,
                                skip_text_generation=True,
                            )
                            
                            assert result["calendar"].weekly_subthemes == ["W1", "W2"]


def test_save_plan_creates_json() -> None:
    """Test _save_plan creates JSON file."""
    calendar = MagicMock()
    calendar.year = 2026
    calendar.month = 2
    calendar.monthly_theme = "Test"
    
    slot_plan = {"2026-02-02": "declarative_statement"}
    schedule = MagicMock()
    
    with patch("pathlib.Path.mkdir"):
        with patch("builtins.open", create_callable=MagicMock()):
            with patch("json.dump"):
                result = orchestrator._save_plan(calendar, slot_plan, schedule)
                
                assert result is not None
                assert "2026" in str(result)
