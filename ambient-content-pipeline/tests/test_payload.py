"""Tests for payload schema and validation."""

import pytest
import json
from pydantic import ValidationError as PydanticValidationError

from src.errors.exceptions import ValidationError
from src.payload import schema, validation


def test_valid_payload():
    """Test creating a valid monthly payload."""
    payload_data = {
        "year": 2026,
        "month": 3,
        "monthly_theme": "Test theme",
        "weekly_subthemes": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "week_rule": "monday_determines_month",
        "video_week": "last_week",
        "style_preset": "default",
    }

    payload = schema.MonthlyPayload(**payload_data)
    assert payload.year == 2026
    assert payload.month == 3
    assert payload.monthly_theme == "Test theme"
    assert len(payload.weekly_subthemes) == 4


def test_payload_without_weekly_subthemes():
    """Test payload without weekly subthemes (AI derivation mode)."""
    payload_data = {
        "year": 2026,
        "month": 3,
        "monthly_theme": "Test theme",
        "week_rule": "monday_determines_month",
        "video_week": "last_week",
    }

    payload = schema.MonthlyPayload(**payload_data)
    assert payload.weekly_subthemes is None


def test_invalid_weekly_subthemes_count():
    """Test that invalid subthemes count raises error."""
    payload_data = {
        "year": 2026,
        "month": 3,
        "monthly_theme": "Test theme",
        "weekly_subthemes": ["Week 1", "Week 2"],  # Only 2 weeks
    }

    with pytest.raises(PydanticValidationError, match="weekly_subthemes must contain exactly 4 or 5"):
        schema.MonthlyPayload(**payload_data)


def test_invalid_weekly_subthemes_empty_list():
    """Test that empty weekly_subthemes list raises error."""
    payload_data = {
        "year": 2026,
        "month": 3,
        "monthly_theme": "Test theme",
        "weekly_subthemes": [],  # Empty list
    }

    with pytest.raises(PydanticValidationError, match="weekly_subthemes cannot be an empty list"):
        schema.MonthlyPayload(**payload_data)


def test_invalid_weekly_subthemes_empty_string():
    """Test that empty strings in weekly_subthemes raises error."""
    payload_data = {
        "year": 2026,
        "month": 3,
        "monthly_theme": "Test theme",
        "weekly_subthemes": ["Week 1", "", "Week 3", "Week 4"],  # Empty string at index 1
    }

    with pytest.raises(PydanticValidationError, match="weekly_subthemes\\[1\\] cannot be empty"):
        schema.MonthlyPayload(**payload_data)


def test_invalid_year_range():
    """Test that invalid year raises error."""
    payload_data = {
        "year": 2019,  # Too old
        "month": 3,
        "monthly_theme": "Test theme",
    }

    with pytest.raises(PydanticValidationError, match="greater than or equal to 2020"):
        schema.MonthlyPayload(**payload_data)


def test_invalid_month_range():
    """Test that invalid month raises error."""
    payload_data = {
        "year": 2026,
        "month": 13,  # Invalid
        "monthly_theme": "Test theme",
    }

    with pytest.raises(PydanticValidationError, match="less than or equal to 12"):
        schema.MonthlyPayload(**payload_data)


def test_invalid_style_preset():
    """Test that invalid style preset raises error."""
    payload_data = {
        "year": 2026,
        "month": 3,
        "monthly_theme": "Test theme",
        "style_preset": "invalid_preset",
    }

    with pytest.raises(PydanticValidationError, match="Invalid style_preset"):
        schema.MonthlyPayload(**payload_data)


def test_validate_payload():
    """Test payload validation logic."""
    # March 2026 has 5 Mondays, so we need 5 subthemes
    payload_data = {
        "year": 2026,
        "month": 3,
        "monthly_theme": "Test theme",
        "weekly_subthemes": ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"],
        "week_rule": "monday_determines_month",
        "video_week": "last_week",
    }

    payload = schema.MonthlyPayload(**payload_data)
    validation.validate_payload(payload)  # Should not raise


def test_validate_payload_wrong_weekly_count():
    """Test that mismatched weekly subthemes count raises error."""
    payload_data = {
        "year": 2026,
        "month": 3,
        "monthly_theme": "Test theme",
        "weekly_subthemes": ["Week 1", "Week 2", "Week 3", "Week 4"],  # Only 4, but March has 5
        "week_rule": "monday_determines_month",
        "video_week": "last_week",
    }

    payload = schema.MonthlyPayload(**payload_data)
    with pytest.raises(ValidationError, match="does not match number of Mondays"):
        validation.validate_payload(payload)


def test_validate_payload_invalid_style_preset():
    """Test that invalid style_preset raises error in validation."""
    from unittest.mock import patch
    
    # Use February 2026 which has 4 Mondays
    payload_data = {
        "year": 2026,
        "month": 2,
        "monthly_theme": "Test theme",
        "weekly_subthemes": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "style_preset": "default",
    }

    payload = schema.MonthlyPayload(**payload_data)
    # Mock COLORFUL_PRESETS to simulate invalid preset and modify payload
    with patch("src.config.defaults.COLORFUL_PRESETS", {}):
        # Directly modify to bypass pydantic validation
        object.__setattr__(payload, "style_preset", "invalid_preset")
        with pytest.raises(ValidationError, match="style_preset 'invalid_preset' is not available"):
            validation.validate_payload(payload)
