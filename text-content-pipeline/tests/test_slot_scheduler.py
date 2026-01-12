"""Tests for slot scheduling logic."""

import pytest
from src.slots.scheduler import (
    apply_slot_plan,
    validate_slot_plan,
    DailySlot,
    DailySlotSchedule,
)
from src.weekly_calendar.resolver import ResolvedCalendar, WeekInfo
from src.slots.enum import SlotFunction
from src.errors.exceptions import SlotAssignmentError
from src.payload.schema import WeekRule, VideoWeek


@pytest.fixture
def sample_calendar() -> ResolvedCalendar:
    """Create a sample calendar for testing."""
    weeks = [
        WeekInfo(
            week_number=1,
            monday_date="2026-02-02",
            sunday_date="2026-02-08",
            subtheme="Week 1 Subtheme",
            is_video_week=False,
        ),
        WeekInfo(
            week_number=2,
            monday_date="2026-02-09",
            sunday_date="2026-02-15",
            subtheme="Week 2 Subtheme",
            is_video_week=False,
        ),
    ]
    
    return ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["Week 1 Subtheme", "Week 2 Subtheme"],
        weeks=weeks,
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )


@pytest.fixture
def valid_slot_plan() -> dict[str, str]:
    """Create a valid slot plan for the sample calendar."""
    return {
        "2026-02-02": "declarative_statement",
        "2026-02-03": "excerpt",
        "2026-02-04": "process_note",
        "2026-02-05": "unanswered_question",
        "2026-02-06": "reframing",
        "2026-02-07": "quiet_observation",
        "2026-02-09": "excerpt",
        "2026-02-10": "declarative_statement",
        "2026-02-11": "process_note",
        "2026-02-12": "unanswered_question",
        "2026-02-13": "reframing",
        "2026-02-14": "quiet_observation",
    }


def test_validate_slot_plan_valid(valid_slot_plan: dict[str, str], sample_calendar: ResolvedCalendar) -> None:
    """Test validation of a valid slot plan."""
    validate_slot_plan(sample_calendar, valid_slot_plan)


def test_validate_slot_plan_invalid_slot_type(sample_calendar: ResolvedCalendar) -> None:
    """Test validation fails with invalid slot type."""
    invalid_plan = {
        "2026-02-02": "invalid_type",
    }
    
    with pytest.raises(SlotAssignmentError) as exc_info:
        validate_slot_plan(sample_calendar, invalid_plan)
    
    assert "Invalid slot type" in str(exc_info.value)


def test_apply_slot_plan_valid(valid_slot_plan: dict[str, str], sample_calendar: ResolvedCalendar) -> None:
    """Test applying a valid slot plan."""
    schedule = apply_slot_plan(sample_calendar, valid_slot_plan)
    
    assert isinstance(schedule, DailySlotSchedule)
    assert schedule.monthly_theme == "Test Theme"
    assert schedule.year == 2026
    assert schedule.month == 2
    assert len(schedule.slots) == 14  # 6 days + 1 Sunday = 7 days per week, 2 weeks
    assert schedule.weekly_subthemes_source == "human"


def test_apply_slot_plan_creates_sunday_slots(valid_slot_plan: dict[str, str], sample_calendar: ResolvedCalendar) -> None:
    """Test that Sunday slots are automatically created as human_intentional."""
    schedule = apply_slot_plan(sample_calendar, valid_slot_plan)
    
    sunday_slots = [s for s in schedule.slots if s.weekday == "Sunday"]
    assert len(sunday_slots) == 2
    
    for sunday in sunday_slots:
        assert sunday.slot_type == SlotFunction.HUMAN_INTENTIONAL
        assert sunday.is_automated is False


def test_apply_slot_plan_assigns_subthemes(valid_slot_plan: dict[str, str], sample_calendar: ResolvedCalendar) -> None:
    """Test that subthemes are correctly assigned from calendar."""
    schedule = apply_slot_plan(sample_calendar, valid_slot_plan)
    
    week1_slots = [s for s in schedule.slots if s.week_number == 1]
    week2_slots = [s for s in schedule.slots if s.week_number == 2]
    
    for slot in week1_slots:
        assert slot.subtheme == "Week 1 Subtheme"
    
    for slot in week2_slots:
        assert slot.subtheme == "Week 2 Subtheme"


def test_apply_slot_plan_missing_dates(sample_calendar: ResolvedCalendar) -> None:
    """Test error when slot plan is missing dates."""
    incomplete_plan = {
        "2026-02-02": "declarative_statement",
    }
    
    with pytest.raises(SlotAssignmentError) as exc_info:
        apply_slot_plan(sample_calendar, incomplete_plan)
    
    assert "Missing slot assignments for:" in str(exc_info.value)


def test_apply_slot_plan_date_not_in_plan(sample_calendar: ResolvedCalendar) -> None:
    """Test error when applying slot plan with date not found in plan."""
    # Create a plan that misses one date - this should trigger missing dates error
    incomplete_plan = {
        "2026-02-02": "declarative_statement",
        "2026-02-03": "excerpt",
        "2026-02-04": "process_note",
        "2026-02-05": "unanswered_question",
        "2026-02-06": "reframing",
        # Missing 2026-02-07
        "2026-02-09": "excerpt",
        "2026-02-10": "declarative_statement",
        "2026-02-11": "process_note",
        "2026-02-12": "unanswered_question",
        "2026-02-13": "reframing",
        "2026-02-14": "quiet_observation",
    }
    
    with pytest.raises(SlotAssignmentError) as exc_info:
        apply_slot_plan(sample_calendar, incomplete_plan)
    
    assert "Missing slot assignments for:" in str(exc_info.value)


def test_apply_slot_plan_extra_dates(valid_slot_plan: dict[str, str], sample_calendar: ResolvedCalendar) -> None:
    """Test error when slot plan has extra dates."""
    extra_plan = valid_slot_plan.copy()
    extra_plan["2026-02-16"] = "declarative_statement"
    
    with pytest.raises(SlotAssignmentError) as exc_info:
        apply_slot_plan(sample_calendar, extra_plan)
    
    assert "Extra slot assignments for:" in str(exc_info.value)


def test_validate_weekly_constraints(sample_calendar: ResolvedCalendar) -> None:
    """Test that weekly constraints are validated (max 2 per type per week)."""
    valid_plan = {
        "2026-02-02": "declarative_statement",
        "2026-02-03": "declarative_statement",
        "2026-02-04": "excerpt",
        "2026-02-05": "excerpt",
        "2026-02-06": "process_note",
        "2026-02-07": "process_note",
        "2026-02-09": "declarative_statement",
        "2026-02-10": "excerpt",
        "2026-02-11": "process_note",
        "2026-02-12": "unanswered_question",
        "2026-02-13": "reframing",
        "2026-02-14": "quiet_observation",
    }
    
    validate_slot_plan(sample_calendar, valid_plan)


def test_validate_weekly_constraints_violation(sample_calendar: ResolvedCalendar) -> None:
    """Test error when weekly constraints are violated."""
    violation_plan = {
        "2026-02-02": "declarative_statement",
        "2026-02-03": "declarative_statement",
        "2026-02-04": "declarative_statement",
        "2026-02-05": "excerpt",
        "2026-02-06": "excerpt",
        "2026-02-07": "process_note",
        "2026-02-09": "declarative_statement",
        "2026-02-10": "excerpt",
        "2026-02-11": "process_note",
        "2026-02-12": "unanswered_question",
        "2026-02-13": "reframing",
        "2026-02-14": "quiet_observation",
    }
    
    with pytest.raises(SlotAssignmentError) as exc_info:
        validate_slot_plan(sample_calendar, violation_plan)
    
    assert "appears 3 times" in str(exc_info.value)
    assert "maximum 2" in str(exc_info.value)


def test_daily_slot_structure() -> None:
    """Test DailySlot dataclass structure."""
    slot = DailySlot(
        date="2026-02-02",
        weekday="Monday",
        slot_type=SlotFunction.DECLARATIVE_STATEMENT,
        subtheme="Test Subtheme",
        week_number=1,
        is_automated=True,
    )
    
    assert slot.date == "2026-02-02"
    assert slot.weekday == "Monday"
    assert slot.slot_type == SlotFunction.DECLARATIVE_STATEMENT
    assert slot.subtheme == "Test Subtheme"
    assert slot.week_number == 1
    assert slot.is_automated is True


def test_apply_slot_plan_without_weekly_subthemes(sample_calendar: ResolvedCalendar) -> None:
    """Test applying slot plan when calendar has no weekly subthemes."""
    sample_calendar.weekly_subthemes = None
    
    valid_plan = {
        "2026-02-02": "declarative_statement",
        "2026-02-03": "excerpt",
        "2026-02-04": "process_note",
        "2026-02-05": "unanswered_question",
        "2026-02-06": "reframing",
        "2026-02-07": "quiet_observation",
        "2026-02-09": "excerpt",
        "2026-02-10": "declarative_statement",
        "2026-02-11": "process_note",
        "2026-02-12": "unanswered_question",
        "2026-02-13": "reframing",
        "2026-02-14": "quiet_observation",
    }
    
    schedule = apply_slot_plan(sample_calendar, valid_plan)
    assert schedule.weekly_subthemes_source == "ai"
