"""Tests for calendar week resolution."""

from datetime import datetime
import pytest
from src.weekly_calendar.resolver import (
    resolve_calendar,
    _find_mondays_in_month,
    ResolvedCalendar,
    WeekInfo,
)
from src.payload.schema import MonthlyPayload, VideoWeek, WeekRule
from src.errors.exceptions import CalendarResolutionError


def test_find_mondays_in_month_february_2026() -> None:
    """Test finding mondays in February 2026."""
    mondays = _find_mondays_in_month(2026, 2)
    
    assert len(mondays) == 4
    assert [d.day for d in mondays] == [2, 9, 16, 23]


def test_find_mondays_in_month_march_2026() -> None:
    """Test finding mondays in March 2026."""
    mondays = _find_mondays_in_month(2026, 3)
    
    assert len(mondays) == 5
    assert [d.day for d in mondays] == [2, 9, 16, 23, 30]


def test_find_mondays_in_month_january_2026() -> None:
    """Test finding mondays in January 2026."""
    mondays = _find_mondays_in_month(2026, 1)
    
    assert len(mondays) == 4
    assert [d.day for d in mondays] == [5, 12, 19, 26]


def test_resolve_calendar_with_subthemes() -> None:
    """Test resolving calendar with provided weekly subthemes."""
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["Week 1", "Week 2", "Week 3", "Week 4"],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
        style_preset="default",
        notes=None,
    )
    
    calendar = resolve_calendar(payload)
    
    assert calendar.year == 2026
    assert calendar.month == 2
    assert calendar.monthly_theme == "Test Theme"
    assert calendar.weekly_subthemes == ["Week 1", "Week 2", "Week 3", "Week 4"]
    assert len(calendar.weeks) == 4
    
    for i, week in enumerate(calendar.weeks):
        assert isinstance(week, WeekInfo)
        assert week.week_number == i + 1
        assert week.subtheme == ["Week 1", "Week 2", "Week 3", "Week 4"][i]
        assert week.is_video_week == (i == 3)


def test_resolve_calendar_without_subthemes() -> None:
    """Test resolving calendar without weekly subthemes."""
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=None,
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
        style_preset="default",
        notes=None,
    )
    
    calendar = resolve_calendar(payload)
    
    assert calendar.weekly_subthemes is None
    assert len(calendar.weeks) == 4
    
    for week in calendar.weeks:
        assert week.subtheme is None


def test_resolve_calendar_mismatched_subtheme_count() -> None:
    """Test error when subtheme count doesn't match mondays count."""
    from unittest.mock import patch
    
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["Week 1", "Week 2", "Week 3", "Week 4"],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
        style_preset="default",
        notes=None,
    )
    
    with patch("src.weekly_calendar.resolver._find_mondays_in_month") as mock_find:
        mock_find.return_value = [
            datetime(2026, 2, 2),
            datetime(2026, 2, 9),
        ]
        with pytest.raises(CalendarResolutionError) as exc_info:
            resolve_calendar(payload)
        
        assert "weekly_subthemes count (4) does not match number of Mondays (2)" in str(exc_info.value)


def test_resolve_calendar_no_mondays_in_month() -> None:
    """Test error when month has no mondays."""
    from unittest.mock import patch
    
    payload = MonthlyPayload(
        year=2026,
        month=2,
        monthly_theme="Test Theme",
        weekly_subthemes=["Week 1", "Week 2", "Week 3", "Week 4"],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
        style_preset="default",
        notes=None,
    )
    
    with patch("src.weekly_calendar.resolver._find_mondays_in_month", return_value=[]):
        with pytest.raises(CalendarResolutionError) as exc_info:
            resolve_calendar(payload)
        
        assert "No Mondays found" in str(exc_info.value)


def test_week_info_structure() -> None:
    """Test WeekInfo dataclass structure."""
    week = WeekInfo(
        week_number=1,
        monday_date="2026-02-02",
        sunday_date="2026-02-08",
        subtheme="Test Subtheme",
        is_video_week=False,
    )
    
    assert week.week_number == 1
    assert week.monday_date == "2026-02-02"
    assert week.sunday_date == "2026-02-08"
    assert week.subtheme == "Test Subtheme"
    assert week.is_video_week is False


def test_resolved_calendar_structure() -> None:
    """Test ResolvedCalendar dataclass structure."""
    weeks = [
        WeekInfo(week_number=1, monday_date="2026-02-02", sunday_date="2026-02-08"),
    ]
    
    calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test",
        weekly_subthemes=["Week 1"],
        weeks=weeks,
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    assert calendar.year == 2026
    assert calendar.month == 2
    assert calendar.monthly_theme == "Test"
    assert len(calendar.weeks) == 1
