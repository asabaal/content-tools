"""Tests for AI generator - no mocking approach."""

import json
import pytest
from src.ai_generator import generator


def test_generate_weekly_subthemes_exists() -> None:
    """Test that generate_weekly_subthemes function exists."""
    assert hasattr(generator, "generate_weekly_subthemes")


def test_plan_monthly_slots_exists() -> None:
    """Test that plan_monthly_slots function exists."""
    assert hasattr(generator, "plan_monthly_slots")


def test_generate_daily_text_exists() -> None:
    """Test that generate_daily_text function exists."""
    assert hasattr(generator, "generate_daily_text")


def test_check_model_available_exists() -> None:
    """Test that check_model_available function exists."""
    assert hasattr(generator, "check_model_available")


def test_call_ollama_exists() -> None:
    """Test that _call_ollama function exists."""
    assert hasattr(generator, "_call_ollama")
