"""Tests for slot enum definitions."""

import pytest
from src.slots.enum import SlotFunction


def test_enum_values_exist() -> None:
    """Test all expected enum values exist."""
    assert SlotFunction.DECLARATIVE_STATEMENT == "declarative_statement"
    assert SlotFunction.EXCERPT == "excerpt"
    assert SlotFunction.PROCESS_NOTE == "process_note"
    assert SlotFunction.UNANSWERED_QUESTION == "unanswered_question"
    assert SlotFunction.REFRAMING == "reframing"
    assert SlotFunction.QUIET_OBSERVATION == "quiet_observation"
    assert SlotFunction.HUMAN_INTENTIONAL == "human_intentional"


def test_enum_is_string() -> None:
    """Test enum is a string enum."""
    assert isinstance(SlotFunction.DECLARATIVE_STATEMENT, str)
    assert isinstance(SlotFunction.EXCERPT, str)


def test_is_automated() -> None:
    """Test is_automated method."""
    automated_slots = [
        SlotFunction.DECLARATIVE_STATEMENT,
        SlotFunction.EXCERPT,
        SlotFunction.PROCESS_NOTE,
        SlotFunction.UNANSWERED_QUESTION,
        SlotFunction.REFRAMING,
        SlotFunction.QUIET_OBSERVATION,
    ]
    
    for slot in automated_slots:
        assert slot.is_automated() is True
    
    assert SlotFunction.HUMAN_INTENTIONAL.is_automated() is False


def test_automated_slots_classmethod() -> None:
    """Test automated_slots classmethod returns all automated types."""
    automated = SlotFunction.automated_slots()
    
    assert len(automated) == 6
    assert SlotFunction.HUMAN_INTENTIONAL not in automated
    
    expected_slots = {
        SlotFunction.DECLARATIVE_STATEMENT,
        SlotFunction.EXCERPT,
        SlotFunction.PROCESS_NOTE,
        SlotFunction.UNANSWERED_QUESTION,
        SlotFunction.REFRAMING,
        SlotFunction.QUIET_OBSERVATION,
    }
    assert set(automated) == expected_slots
