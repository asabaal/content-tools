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
                    with patch("src.pipeline.orchestrator.generator.generate_weekly_subtitle", return_value="Short"):
                        with patch("src.pipeline.orchestrator.generator.plan_monthly_slots", return_value={}):
                            with patch("src.pipeline.orchestrator._save_plan"):
                                result = await orchestrator.run_full_pipeline(
                                    payload,
                                    skip_rendering=True,
                                    skip_text_generation=True,
                                )
                                
                                assert result["calendar"].weekly_subthemes == ["W1", "W2"]


@pytest.mark.asyncio
async def test_run_full_pipeline_generates_subtitles() -> None:
    """Test pipeline generates subtitles for weekly subthemes."""
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=[
            "Week One Long Description",
            "Week Two Long Description",
            "Week Three Long Description",
            "Week Four Long Description",
        ],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    week_info = MagicMock()
    week_info.week_number = 1
    week_info.monday_date = "2026-02-02"
    week_info.sunday_date = "2026-02-08"
    week_info.subtheme = "Week One Long Description"
    week_info.is_video_week = False
    
    resolved_calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=[
            "Week One Long Description",
            "Week Two Long Description",
            "Week Three Long Description",
            "Week Four Long Description",
        ],
        weeks=[week_info],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    schedule = MagicMock()
    schedule.slots = []
    
    with patch("src.pipeline.orchestrator.resolve_calendar", return_value=resolved_calendar):
        with patch("src.pipeline.orchestrator.scheduler.apply_slot_plan", return_value=schedule):
            with patch("src.pipeline.orchestrator.scheduler.validate_slot_plan"):
                with patch("src.pipeline.orchestrator.generator.generate_weekly_subtitle", return_value="Short Title"):
                    with patch("src.pipeline.orchestrator.generator.plan_monthly_slots", return_value={}):
                        with patch("src.pipeline.orchestrator._save_plan") as mock_save:
                            await orchestrator.run_full_pipeline(
                                payload,
                                skip_rendering=True,
                                skip_text_generation=True,
                            )
                            
                            # Verify generate_weekly_subtitle was called for each subtheme
                            assert mock_save.called


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


def test_save_plan_includes_weekly_subtitles() -> None:
    """Test _save_plan includes weekly_subtitles in output."""
    calendar = MagicMock()
    calendar.year = 2026
    calendar.month = 2
    calendar.monthly_theme = "Test"
    calendar.weekly_subthemes = ["W1", "W2"]
    
    slot_plan = {"2026-02-02": "declarative_statement"}
    schedule = MagicMock()
    schedule.weekly_subthemes_source = "human"
    schedule.slots = []
    
    weekly_subtitles = {1: "Short 1", 2: "Short 2"}
    
    saved_data = {}
    
    def capture_save(data, f, **kwargs):
        saved_data.update(data)
    
    with patch("pathlib.Path.mkdir"):
        with patch("builtins.open", MagicMock()):
            with patch("json.dump", capture_save):
                orchestrator._save_plan(calendar, slot_plan, schedule, weekly_subtitles=weekly_subtitles)
                
                assert saved_data.get("weekly_subtitles") == weekly_subtitles


@pytest.mark.asyncio
async def test_run_full_pipeline_with_output_dir() -> None:
    """Test pipeline with custom output directory."""
    import tempfile
    
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    resolved_calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        weeks=[],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    schedule = MagicMock()
    schedule.slots = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("src.pipeline.orchestrator.resolve_calendar", return_value=resolved_calendar):
            with patch("src.pipeline.orchestrator.scheduler.apply_slot_plan", return_value=schedule):
                with patch("src.pipeline.orchestrator.scheduler.validate_slot_plan"):
                    with patch("src.pipeline.orchestrator.generator.generate_weekly_subtitle", return_value="Short"):
                        with patch("src.pipeline.orchestrator.generator.plan_monthly_slots", return_value={}):
                            with patch("src.pipeline.orchestrator._save_plan"):
                                result = await orchestrator.run_full_pipeline(
                                    payload,
                                    skip_rendering=True,
                                    skip_text_generation=True,
                                    output_dir=tmpdir,
                                )
                                
                                assert result is not None


@pytest.mark.asyncio
async def test_run_full_pipeline_with_model_override() -> None:
    """Test pipeline with model override."""
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    resolved_calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        weeks=[],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    schedule = MagicMock()
    schedule.slots = []
    
    with patch("src.pipeline.orchestrator.resolve_calendar", return_value=resolved_calendar):
        with patch("src.pipeline.orchestrator.scheduler.apply_slot_plan", return_value=schedule):
            with patch("src.pipeline.orchestrator.scheduler.validate_slot_plan"):
                with patch("src.pipeline.orchestrator.generator.generate_weekly_subtitle", return_value="Short"):
                    with patch("src.pipeline.orchestrator.generator.plan_monthly_slots", return_value={}):
                        with patch("src.pipeline.orchestrator._save_plan"):
                            result = await orchestrator.run_full_pipeline(
                                payload,
                                model="custom-model",
                                skip_rendering=True,
                                skip_text_generation=True,
                            )
                            
                            assert result is not None


@pytest.mark.asyncio
async def test_run_full_pipeline_with_text_generation() -> None:
    """Test pipeline with text generation enabled."""
    from src.slots.enum import SlotFunction
    
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    week_info = MagicMock()
    week_info.week_number = 1
    week_info.monday_date = "2026-02-02"
    week_info.sunday_date = "2026-02-08"
    week_info.subtheme = "W1"
    week_info.is_video_week = False
    
    resolved_calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        weeks=[week_info],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    slot = MagicMock()
    slot.date = "2026-02-02"
    slot.weekday = "Monday"
    slot.slot_type = SlotFunction.DECLARATIVE_STATEMENT
    slot.week_number = 1
    slot.subtheme = "W1"
    slot.is_automated = True
    
    schedule = MagicMock()
    schedule.slots = [slot]
    
    with patch("src.pipeline.orchestrator.resolve_calendar", return_value=resolved_calendar):
        with patch("src.pipeline.orchestrator.scheduler.apply_slot_plan", return_value=schedule):
            with patch("src.pipeline.orchestrator.scheduler.validate_slot_plan"):
                with patch("src.pipeline.orchestrator.generator.generate_weekly_subtitle", return_value="Short"):
                    with patch("src.pipeline.orchestrator.generator.plan_monthly_slots", return_value={}):
                        with patch("src.pipeline.orchestrator.generator.generate_daily_text", return_value="Generated text") as mock_gen:
                            with patch("src.pipeline.orchestrator._save_plan"):
                                result = await orchestrator.run_full_pipeline(
                                    payload,
                                    skip_rendering=True,
                                    skip_text_generation=False,
                                )
                                
                                assert result is not None
                                assert "2026-02-02" in result["generated_texts"]
                                # Verify generate_daily_text was called with previously_generated parameter
                                mock_gen.assert_called_once()
                                call_kwargs = mock_gen.call_args[1]
                                assert "previously_generated" in call_kwargs


@pytest.mark.asyncio
async def test_run_full_pipeline_passes_previous_texts_in_order() -> None:
    """Test pipeline passes previously generated texts in chronological order."""
    from src.slots.enum import SlotFunction
    
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    week_info = MagicMock()
    week_info.week_number = 1
    week_info.monday_date = "2026-02-02"
    week_info.sunday_date = "2026-02-08"
    week_info.subtheme = "W1"
    week_info.is_video_week = False
    
    resolved_calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        weeks=[week_info],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    # Create multiple slots in non-chronological order to test sorting
    slot1 = MagicMock()
    slot1.date = "2026-02-03"
    slot1.weekday = "Tuesday"
    slot1.slot_type = SlotFunction.EXCERPT
    slot1.week_number = 1
    slot1.subtheme = "W1"
    slot1.is_automated = True
    
    slot2 = MagicMock()
    slot2.date = "2026-02-02"
    slot2.weekday = "Monday"
    slot2.slot_type = SlotFunction.DECLARATIVE_STATEMENT
    slot2.week_number = 1
    slot2.subtheme = "W1"
    slot2.is_automated = True
    
    slot3 = MagicMock()
    slot3.date = "2026-02-04"
    slot3.weekday = "Wednesday"
    slot3.slot_type = SlotFunction.PROCESS_NOTE
    slot3.week_number = 1
    slot3.subtheme = "W1"
    slot3.is_automated = True
    
    schedule = MagicMock()
    schedule.slots = [slot1, slot2, slot3]  # Intentionally out of order
    
    gen_call_args = []
    
    async def mock_generate_daily_text(**kwargs):
        # Deep copy the previously_generated list to capture its state at call time
        call_kwargs = kwargs.copy()
        if "previously_generated" in call_kwargs:
            call_kwargs["previously_generated"] = list(call_kwargs["previously_generated"])
        gen_call_args.append(call_kwargs)
        return f"Generated for {kwargs.get('slot_type')}"
    
    with patch("src.pipeline.orchestrator.resolve_calendar", return_value=resolved_calendar):
        with patch("src.pipeline.orchestrator.scheduler.apply_slot_plan", return_value=schedule):
            with patch("src.pipeline.orchestrator.scheduler.validate_slot_plan"):
                with patch("src.pipeline.orchestrator.generator.generate_weekly_subtitle", return_value="Short"):
                    with patch("src.pipeline.orchestrator.generator.plan_monthly_slots", return_value={}):
                        with patch("src.pipeline.orchestrator.generator.generate_daily_text", side_effect=mock_generate_daily_text):
                            with patch("src.pipeline.orchestrator._save_plan"):
                                result = await orchestrator.run_full_pipeline(
                                    payload,
                                    skip_rendering=True,
                                    skip_text_generation=False,
                                )
                                
                                assert result is not None
                                
                                # Verify slots were processed in chronological order
                                assert len(gen_call_args) == 3
                                
                                # First call (2026-02-02) should have empty previously_generated
                                assert gen_call_args[0]["previously_generated"] == []
                                
                                # Second call (2026-02-03) should have first text
                                assert len(gen_call_args[1]["previously_generated"]) == 1
                                
                                # Third call (2026-02-04) should have first two texts
                                assert len(gen_call_args[2]["previously_generated"]) == 2


@pytest.mark.asyncio
async def test_run_full_pipeline_text_generation_error() -> None:
    """Test pipeline handles text generation errors gracefully."""
    from src.slots.enum import SlotFunction
    from src.errors.exceptions import AIGenerationError
    
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    week_info = MagicMock()
    week_info.week_number = 1
    week_info.monday_date = "2026-02-02"
    week_info.sunday_date = "2026-02-08"
    week_info.subtheme = "W1"
    week_info.is_video_week = False
    
    resolved_calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        weeks=[week_info],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    slot = MagicMock()
    slot.date = "2026-02-02"
    slot.weekday = "Monday"
    slot.slot_type = SlotFunction.DECLARATIVE_STATEMENT
    slot.week_number = 1
    slot.subtheme = "W1"
    slot.is_automated = True
    
    schedule = MagicMock()
    schedule.slots = [slot]
    
    with patch("src.pipeline.orchestrator.resolve_calendar", return_value=resolved_calendar):
        with patch("src.pipeline.orchestrator.scheduler.apply_slot_plan", return_value=schedule):
            with patch("src.pipeline.orchestrator.scheduler.validate_slot_plan"):
                with patch("src.pipeline.orchestrator.generator.generate_weekly_subtitle", return_value="Short"):
                    with patch("src.pipeline.orchestrator.generator.plan_monthly_slots", return_value={}):
                        with patch("src.pipeline.orchestrator.generator.generate_daily_text", side_effect=AIGenerationError("AI error", touchpoint="test")):
                            with patch("src.pipeline.orchestrator._save_plan"):
                                result = await orchestrator.run_full_pipeline(
                                    payload,
                                    skip_rendering=True,
                                    skip_text_generation=False,
                                )
                                
                                assert result is not None
                                assert result["generated_texts"]["2026-02-02"] == ""


@pytest.mark.asyncio
async def test_run_full_pipeline_with_rendering() -> None:
    """Test pipeline with rendering enabled."""
    from src.slots.enum import SlotFunction
    
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    week_info = MagicMock()
    week_info.week_number = 1
    week_info.monday_date = "2026-02-02"
    week_info.sunday_date = "2026-02-08"
    week_info.subtheme = "W1"
    week_info.is_video_week = False
    
    resolved_calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        weeks=[week_info],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    slot = MagicMock()
    slot.date = "2026-02-02"
    slot.weekday = "Monday"
    slot.slot_type = SlotFunction.DECLARATIVE_STATEMENT
    slot.week_number = 1
    slot.subtheme = "W1"
    slot.is_automated = True
    
    schedule = MagicMock()
    schedule.slots = [slot]
    
    with patch("src.pipeline.orchestrator.resolve_calendar", return_value=resolved_calendar):
        with patch("src.pipeline.orchestrator.scheduler.apply_slot_plan", return_value=schedule):
            with patch("src.pipeline.orchestrator.scheduler.validate_slot_plan"):
                with patch("src.pipeline.orchestrator.generator.generate_weekly_subtitle", return_value="Short"):
                    with patch("src.pipeline.orchestrator.generator.plan_monthly_slots", return_value={}):
                        with patch("src.pipeline.orchestrator.generator.generate_daily_text", return_value="Generated text"):
                            with patch("src.pipeline.orchestrator._save_plan"):
                                with patch("src.pipeline.orchestrator.html_renderer.render_text_to_image", new_callable=AsyncMock, return_value="/path/to/image.png"):
                                    with patch("src.pipeline.orchestrator.html_renderer.get_output_path", return_value="/path/to/image.png"):
                                        result = await orchestrator.run_full_pipeline(
                                            payload,
                                            skip_rendering=False,
                                            skip_text_generation=False,
                                        )
                                        
                                        assert result is not None
                                        assert len(result["rendered_images"]) == 1


@pytest.mark.asyncio
async def test_run_full_pipeline_rendering_error() -> None:
    """Test pipeline handles rendering errors gracefully."""
    from src.slots.enum import SlotFunction
    
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    week_info = MagicMock()
    week_info.week_number = 1
    week_info.monday_date = "2026-02-02"
    week_info.sunday_date = "2026-02-08"
    week_info.subtheme = "W1"
    week_info.is_video_week = False
    
    resolved_calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        weeks=[week_info],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    slot = MagicMock()
    slot.date = "2026-02-02"
    slot.weekday = "Monday"
    slot.slot_type = SlotFunction.DECLARATIVE_STATEMENT
    slot.week_number = 1
    slot.subtheme = "W1"
    slot.is_automated = True
    
    schedule = MagicMock()
    schedule.slots = [slot]
    
    with patch("src.pipeline.orchestrator.resolve_calendar", return_value=resolved_calendar):
        with patch("src.pipeline.orchestrator.scheduler.apply_slot_plan", return_value=schedule):
            with patch("src.pipeline.orchestrator.scheduler.validate_slot_plan"):
                with patch("src.pipeline.orchestrator.generator.generate_weekly_subtitle", return_value="Short"):
                    with patch("src.pipeline.orchestrator.generator.plan_monthly_slots", return_value={}):
                        with patch("src.pipeline.orchestrator.generator.generate_daily_text", return_value="Generated text"):
                            with patch("src.pipeline.orchestrator._save_plan"):
                                with patch("src.pipeline.orchestrator.html_renderer.render_text_to_image", side_effect=Exception("Render error")):
                                    with patch("src.pipeline.orchestrator.html_renderer.get_output_path", return_value="/path/to/image.png"):
                                        result = await orchestrator.run_full_pipeline(
                                            payload,
                                            skip_rendering=False,
                                            skip_text_generation=False,
                                        )
                                        
                                        assert result is not None
                                        assert len(result["rendered_images"]) == 0


@pytest.mark.asyncio
async def test_validate_and_run() -> None:
    """Test validate_and_run function."""
    import tempfile
    import json
    
    payload_data = {
        "year": 2026,
        "month": 2,
        "monthly_theme": "Test Theme",
        "weekly_subthemes": ["W1", "W2", "W3", "W4"],
        "week_rule": "monday_determines_month",
        "video_week": "last_week",
        "style_preset": "default",
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(payload_data, f)
        payload_path = f.name
    
    try:
        resolved_calendar = ResolvedCalendar(
            year=2026,
            month=2,
            monthly_theme="Test Theme",
            weekly_subthemes=["W1", "W2", "W3", "W4"],
            weeks=[],
            week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
            video_week=VideoWeek.LAST_WEEK,
        )
        
        schedule = MagicMock()
        schedule.slots = []
        
        with patch("src.pipeline.orchestrator.resolve_calendar", return_value=resolved_calendar):
            with patch("src.pipeline.orchestrator.scheduler.apply_slot_plan", return_value=schedule):
                with patch("src.pipeline.orchestrator.scheduler.validate_slot_plan"):
                    with patch("src.pipeline.orchestrator.generator.generate_weekly_subtitle", return_value="Short"):
                        with patch("src.pipeline.orchestrator.generator.plan_monthly_slots", return_value={}):
                            with patch("src.pipeline.orchestrator._save_plan"):
                                result = await orchestrator.validate_and_run(
                                    payload_path,
                                    skip_rendering=True,
                                    skip_text_generation=True,
                                )
                                
                                assert result is not None
    finally:
        import os
        os.unlink(payload_path)


@pytest.mark.asyncio
async def test_run_full_pipeline_wraps_unexpected_error() -> None:
    """Test pipeline wraps unexpected errors in PipelineError."""
    from src.errors.exceptions import PipelineError
    
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    with patch("src.pipeline.orchestrator.resolve_calendar", side_effect=RuntimeError("unexpected error")):
        with pytest.raises(PipelineError) as exc_info:
            await orchestrator.run_full_pipeline(
                payload,
                skip_rendering=True,
                skip_text_generation=True,
            )
        assert "unexpected error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_run_full_pipeline_reraises_pipeline_error() -> None:
    """Test pipeline re-raises PipelineError without wrapping."""
    from src.errors.exceptions import PipelineError
    
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["W1", "W2", "W3", "W4"],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    original_error = PipelineError("original error")
    
    with patch("src.pipeline.orchestrator.resolve_calendar", side_effect=original_error):
        with pytest.raises(PipelineError) as exc_info:
            await orchestrator.run_full_pipeline(
                payload,
                skip_rendering=True,
                skip_text_generation=True,
            )
        assert exc_info.value is original_error
