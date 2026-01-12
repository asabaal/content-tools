"""Daily slot scheduling and validation."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from src.weekly_calendar.resolver import ResolvedCalendar, WeekInfo
from src.errors.exceptions import SlotAssignmentError
from src.slots.enum import SlotFunction


@dataclass
class DailySlot:
    """A single day's content slot."""

    date: str
    weekday: str  # "Monday", "Tuesday", etc.
    slot_type: SlotFunction
    subtheme: str | None
    week_number: int
    is_automated: bool


@dataclass
class DailySlotSchedule:
    """Complete monthly schedule of daily slots."""

    monthly_theme: str
    year: int
    month: int
    slots: list[DailySlot]
    weekly_subthemes_source: Literal["human", "ai"]


def apply_slot_plan(
    calendar: ResolvedCalendar,
    slot_plan: dict[str, str],  # date -> slot_type string
) -> DailySlotSchedule:
    """Apply AI-generated slot plan to calendar.

    Args:
        calendar: Resolved calendar
        slot_plan: Mapping of date strings to slot type strings

    Returns:
        Complete daily slot schedule

    Raises:
        SlotAssignmentError: If slot plan is invalid
    """
    # Validate slot plan covers all automated days
    expected_dates = _get_expected_automated_dates(calendar)
    plan_dates = set(slot_plan.keys())

    if plan_dates != expected_dates:
        missing = expected_dates - plan_dates
        extra = plan_dates - expected_dates
        errors = []
        if missing:
            errors.append(f"Missing slot assignments for: {sorted(missing)}")
        if extra:
            errors.append(f"Extra slot assignments for: {sorted(extra)}")
        raise SlotAssignmentError("; ".join(errors))

    # Validate slot types and apply plan
    slots: list[DailySlot] = []

    # Determine subtheme source
    subtheme_source = "human" if calendar.weekly_subthemes else "ai"

    for week in calendar.weeks:
        # Build slots for this week
        week_slots = _build_week_slots(
            week=week,
            slot_plan=slot_plan,
            subtheme_source=subtheme_source,
        )
        slots.extend(week_slots)

    return DailySlotSchedule(
        monthly_theme=calendar.monthly_theme,
        year=calendar.year,
        month=calendar.month,
        slots=slots,
        weekly_subthemes_source=subtheme_source,
    )


def validate_slot_plan(
    calendar: ResolvedCalendar,
    slot_plan: dict[str, str],
) -> None:
    """Validate a slot plan satisfies all constraints.

    Args:
        calendar: Resolved calendar
        slot_plan: Mapping of date strings to slot type strings

    Raises:
        SlotAssignmentError: If slot plan violates constraints
    """
    # Validate all slot types are valid
    for date_str, slot_type_str in slot_plan.items():
        try:
            SlotFunction(slot_type_str)
        except ValueError as e:
            raise SlotAssignmentError(
                f"Invalid slot type '{slot_type_str}' for date {date_str}: {e}"
            )

    # Validate weekly enum frequency constraints (0-2 times per week)
    _validate_weekly_constraints(calendar, slot_plan)


def _get_expected_automated_dates(calendar: ResolvedCalendar) -> set[str]:
    """Get set of dates that should have automated slots.

    Args:
        calendar: Resolved calendar

    Returns:
        Set of date strings
    """
    dates: set[str] = set()

    for week in calendar.weeks:
        monday = datetime.strptime(week.monday_date, "%Y-%m-%d")

        # Monday through Saturday (skip Sunday)
        for day_offset in range(6):
            date = monday + timedelta(days=day_offset)
            dates.add(date.strftime("%Y-%m-%d"))

    return dates


def _build_week_slots(
    week: WeekInfo,
    slot_plan: dict[str, str],
    subtheme_source: str,
) -> list[DailySlot]:
    """Build all slots for a single week.

    Args:
        week: Week information
        slot_plan: Date to slot type mapping
        subtheme_source: "human" or "ai"

    Returns:
        List of daily slots for this week
    """
    slots: list[DailySlot] = []

    monday = datetime.strptime(week.monday_date, "%Y-%m-%d")

    # Monday through Saturday
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    for day_offset, weekday_name in enumerate(weekday_names):
        date = monday + timedelta(days=day_offset)
        date_str = date.strftime("%Y-%m-%d")

        # Get slot type from plan
        if date_str not in slot_plan:
            raise SlotAssignmentError(
                f"Date {date_str} (Week {week.week_number}, {weekday_name}) not found in slot plan"
            )
        slot_type_str = slot_plan[date_str]
        slot_type = SlotFunction(slot_type_str)

        slot = DailySlot(
            date=date_str,
            weekday=weekday_name,
            slot_type=slot_type,
            subtheme=week.subtheme,
            week_number=week.week_number,
            is_automated=slot_type.is_automated(),
        )
        slots.append(slot)

    # Sunday is always HUMAN_INTENTIONAL
    sunday = monday + timedelta(days=6)
    sunday_str = sunday.strftime("%Y-%m-%d")

    human_slot = DailySlot(
        date=sunday_str,
        weekday="Sunday",
        slot_type=SlotFunction.HUMAN_INTENTIONAL,
        subtheme=week.subtheme,
        week_number=week.week_number,
        is_automated=False,
    )
    slots.append(human_slot)

    return slots


def _validate_weekly_constraints(
    calendar: ResolvedCalendar,
    slot_plan: dict[str, str],
) -> None:
    """Validate weekly enum frequency constraints (0-2 times per week).

    Args:
        calendar: Resolved calendar
        slot_plan: Date to slot type mapping

    Raises:
        SlotAssignmentError: If constraints are violated
    """
    for week in calendar.weeks:
        # Count each enum in this week
        enum_counts: dict[SlotFunction, int] = {}

        monday = datetime.strptime(week.monday_date, "%Y-%m-%d")

        # Monday through Saturday (skip Sunday)
        for day_offset in range(6):
            date = monday + timedelta(days=day_offset)
            date_str = date.strftime("%Y-%m-%d")

            # Skip dates not in slot_plan (shouldn't happen with proper AI)
            if date_str not in slot_plan:
                continue

            slot_type_str = slot_plan[date_str]
            slot_type = SlotFunction(slot_type_str)

            enum_counts[slot_type] = enum_counts.get(slot_type, 0) + 1

        # Check constraint: each enum can appear 0-2 times max
        for slot_type, count in enum_counts.items():
            if count > 2:
                raise SlotAssignmentError(
                    f"Slot type '{slot_type.value}' appears {count} times "
                    f"in week {week.week_number} (maximum 2)"
                )
