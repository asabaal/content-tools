"""Month payload schema and validation."""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class WeekRule(str, Enum):
    """Rules for week-month association."""

    MONDAY_DETERMINES_MONTH = "monday_determines_month"


class VideoWeek(str, Enum):
    """Rules for video week placement."""

    LAST_WEEK = "last_week"


class MonthlyPayload(BaseModel):
    """Monthly theme and structure definition."""

    year: int = Field(..., ge=2020, le=2100, description="Calendar year")
    month: int = Field(..., ge=1, le=12, description="Calendar month (1-12)")
    monthly_theme: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Main monthly theme",
    )
    weekly_subthemes: list[str] | None = Field(
        default=None,
        description="Optional ordered list of weekly subthemes (4-5)",
    )
    week_rule: WeekRule = Field(
        default=WeekRule.MONDAY_DETERMINES_MONTH,
        description="Rule for week-month association",
    )
    video_week: VideoWeek = Field(
        default=VideoWeek.LAST_WEEK,
        description="When to schedule the video week",
    )
    style_preset: str = Field(
        default="default",
        description="Visual style preset name",
    )
    notes: str | None = Field(
        default=None,
        description="Optional human notes (ignored by system)",
    )

    @field_validator("weekly_subthemes")
    @classmethod
    def validate_weekly_subthemes(cls, v: list[str] | None) -> list[str] | None:
        """Validate weekly subthemes list."""
        if v is None:
            return None

        if not v:
            raise ValueError("weekly_subthemes cannot be an empty list")

        if len(v) not in (4, 5):
            raise ValueError("weekly_subthemes must contain exactly 4 or 5 subthemes")

        # Validate no empty strings
        for i, subtheme in enumerate(v):
            if not subtheme or not subtheme.strip():
                raise ValueError(f"weekly_subthemes[{i}] cannot be empty")

        # Return stripped versions
        return [s.strip() for s in v]

    @field_validator("style_preset")
    @classmethod
    def validate_style_preset(cls, v: str) -> str:
        """Validate style preset exists."""
        from src.config.defaults import COLORFUL_PRESETS

        if v not in COLORFUL_PRESETS:
            raise ValueError(
                f"Invalid style_preset '{v}'. Must be one of: {list(COLORFUL_PRESETS.keys())}"
            )
        return v
