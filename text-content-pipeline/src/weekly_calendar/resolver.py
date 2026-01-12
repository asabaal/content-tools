"""Calendar week resolution with Monday ownership rule."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from src.config.defaults import VIDEO_WEEK_RULE, WEEK_RULE
from src.errors.exceptions import CalendarResolutionError
from src.payload.schema import MonthlyPayload, VideoWeek, WeekRule


@dataclass
class WeekInfo:
    """Information about a resolved week."""

    week_number: int
    monday_date: str
    sunday_date: str
    subtheme: str | None = None
    is_video_week: bool = False


@dataclass
class ResolvedCalendar:
    """Resolved calendar with weeks assigned."""

    year: int
    month: int
    monthly_theme: str
    weekly_subthemes: list[str] | None
    weeks: list[WeekInfo]
    week_rule: WeekRule
    video_week: VideoWeek


def resolve_calendar(payload: MonthlyPayload) -> ResolvedCalendar:
    """Resolve calendar weeks based on Monday ownership rule.

    Args:
        payload: Validated monthly payload

    Returns:
        Resolved calendar structure

    Raises:
        CalendarResolutionError: If resolution fails
    """
    # Find all Mondays in the month
    mondays = _find_mondays_in_month(payload.year, payload.month)

    if not mondays:
        raise CalendarResolutionError(
            f"No Mondays found in {payload.year}-{payload.month:02d}"
        )

    # Validate weekly_subthemes count matches Mondays count
    if payload.weekly_subthemes is not None:
        if len(payload.weekly_subthemes) != len(mondays):
            raise CalendarResolutionError(
                f"weekly_subthemes count ({len(payload.weekly_subthemes)}) "
                f"does not match number of Mondays ({len(mondays)})"
            )
        weekly_subthemes = payload.weekly_subthemes
    else:
        weekly_subthemes = None

    # Determine video week index
    if payload.video_week == VideoWeek.LAST_WEEK:
        video_week_index = len(mondays) - 1  # Last week
    else:
        raise CalendarResolutionError(
            f"Video week rule '{payload.video_week}' not implemented"
        )

    # Build week info for each Monday
    weeks: list[WeekInfo] = []

    for i, monday in enumerate(mondays):
        # Calculate Sunday for this week
        sunday = monday + timedelta(days=6)

        # Get subtheme if available
        subtheme = None
        if weekly_subthemes is not None:
            subtheme = weekly_subthemes[i]

        # Check if this is video week
        is_video_week = i == video_week_index

        week_info = WeekInfo(
            week_number=i + 1,
            monday_date=monday.strftime("%Y-%m-%d"),
            sunday_date=sunday.strftime("%Y-%m-%d"),
            subtheme=subtheme,
            is_video_week=is_video_week,
        )
        weeks.append(week_info)

    return ResolvedCalendar(
        year=payload.year,
        month=payload.month,
        monthly_theme=payload.monthly_theme,
        weekly_subthemes=weekly_subthemes,
        weeks=weeks,
        week_rule=payload.week_rule,
        video_week=payload.video_week,
    )


def _find_mondays_in_month(year: int, month: int) -> list[datetime]:
    """Find all Monday dates in a given month.

    Args:
        year: Calendar year
        month: Calendar month (1-12)

    Returns:
        List of Monday dates in chronological order
    """
    mondays: list[datetime] = []

    # Iterate through all days of the month
    for day in range(1, 32):
        try:
            date = datetime(year, month, day)
            if date.weekday() == 0:  # Monday is 0
                mondays.append(date)
        except ValueError:
            # Day is out of range for this month
            pass

    return mondays
