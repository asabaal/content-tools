"""Month payload validation logic."""

from datetime import datetime

from src.errors.exceptions import ValidationError
from src.payload.schema import MonthlyPayload


def validate_payload(payload: MonthlyPayload) -> None:
    """Validate monthly payload structure and constraints.

    Args:
        payload: The monthly payload to validate

    Raises:
        ValidationError: If validation fails
    """
    # Basic structure validation is done by Pydantic
    # Here we do cross-field validation

    # Check if weekly_subthemes are provided but count doesn't match actual weeks
    if payload.weekly_subthemes is not None:
        num_mondays = _count_mondays_in_month(payload.year, payload.month)

        if len(payload.weekly_subthemes) != num_mondays:
            raise ValidationError(
                f"weekly_subthemes count ({len(payload.weekly_subthemes)}) "
                f"does not match number of Mondays in {payload.year}-{payload.month:02d} ({num_mondays})"
            )

    # Validate style_preset is available
    from src.config.defaults import COLORFUL_PRESETS

    if payload.style_preset not in COLORFUL_PRESETS:
        raise ValidationError(
            f"style_preset '{payload.style_preset}' is not available. "
            f"Available presets: {list(COLORFUL_PRESETS.keys())}"
        )


def _count_mondays_in_month(year: int, month: int) -> int:
    """Count Mondays in a given month.

    Args:
        year: Calendar year
        month: Calendar month (1-12)

    Returns:
        Number of Mondays in the month
    """
    count = 0

    # Iterate through all days of the month
    for day in range(1, 32):
        try:
            date = datetime(year, month, day)
            if date.weekday() == 0:  # Monday is 0 in Python
                count += 1
        except ValueError:
            # Day is out of range for this month (e.g., Feb 30)
            pass

    return count
