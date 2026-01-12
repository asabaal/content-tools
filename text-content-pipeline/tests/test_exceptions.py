"""Tests for custom exceptions."""

import pytest
from src.errors.exceptions import (
    PipelineError,
    ValidationError,
    CalendarResolutionError,
    SlotAssignmentError,
    AIGenerationError,
    RendererError,
    ConfigurationError,
    ModelUnavailableError,
    InvalidSlotEnumError,
)


def test_pipeline_error_base() -> None:
    """Test base PipelineError can be raised."""
    with pytest.raises(PipelineError) as exc_info:
        raise PipelineError("Test error")
    
    assert str(exc_info.value) == "Test error"


def test_validation_error_basic() -> None:
    """Test ValidationError with message."""
    error = ValidationError("Invalid field")
    
    assert str(error) == "Invalid field"


def test_validation_error_with_field() -> None:
    """Test ValidationError with field attribute."""
    error = ValidationError("Invalid field", field="monthly_theme")
    
    assert error.field == "monthly_theme"
    assert str(error) == "Invalid field"


def test_calendar_resolution_error() -> None:
    """Test CalendarResolutionError."""
    with pytest.raises(CalendarResolutionError) as exc_info:
        raise CalendarResolutionError("No Mondays found")
    
    assert str(exc_info.value) == "No Mondays found"
    assert isinstance(exc_info.value, PipelineError)


def test_slot_assignment_error() -> None:
    """Test SlotAssignmentError."""
    with pytest.raises(SlotAssignmentError) as exc_info:
        raise SlotAssignmentError("Invalid slot plan")
    
    assert str(exc_info.value) == "Invalid slot plan"
    assert isinstance(exc_info.value, PipelineError)


def test_ai_generation_error() -> None:
    """Test AIGenerationError with touchpoint."""
    error = AIGenerationError("Generation failed", touchpoint="weekly_subthemes")
    
    assert str(error) == "Generation failed"
    assert error.touchpoint == "weekly_subthemes"
    assert isinstance(error, PipelineError)


def test_renderer_error() -> None:
    """Test RendererError."""
    with pytest.raises(RendererError) as exc_info:
        raise RendererError("Rendering failed")
    
    assert str(exc_info.value) == "Rendering failed"
    assert isinstance(exc_info.value, PipelineError)


def test_configuration_error() -> None:
    """Test ConfigurationError."""
    with pytest.raises(ConfigurationError) as exc_info:
        raise ConfigurationError("Invalid config")
    
    assert str(exc_info.value) == "Invalid config"
    assert isinstance(exc_info.value, PipelineError)


def test_model_unavailable_error() -> None:
    """Test ModelUnavailableError with model name."""
    error = ModelUnavailableError("gpt-oss:20b")
    
    assert "gpt-oss:20b" in str(error)
    assert "ollama pull" in str(error)
    assert error.model == "gpt-oss:20b"
    assert error.touchpoint == "model_check"
    assert isinstance(error, AIGenerationError)


def test_invalid_slot_enum_error() -> None:
    """Test InvalidSlotEnumError with slot type."""
    error = InvalidSlotEnumError("invalid_slot_type")
    
    assert "Invalid slot type: invalid_slot_type" in str(error)
    assert error.slot_type == "invalid_slot_type"
    assert isinstance(error, SlotAssignmentError)


def test_exception_hierarchy() -> None:
    """Test that all custom exceptions inherit from PipelineError."""
    
    assert issubclass(ValidationError, PipelineError)
    assert issubclass(CalendarResolutionError, PipelineError)
    assert issubclass(SlotAssignmentError, PipelineError)
    assert issubclass(AIGenerationError, PipelineError)
    assert issubclass(RendererError, PipelineError)
    assert issubclass(ConfigurationError, PipelineError)


def test_exception_catching_base_class() -> None:
    """Test that exceptions can be caught by base PipelineError."""
    
    exceptions_to_test = [
        ValidationError("test"),
        CalendarResolutionError("test"),
        SlotAssignmentError("test"),
        AIGenerationError("test", "test"),
        RendererError("test"),
        ConfigurationError("test"),
    ]
    
    for exc in exceptions_to_test:
        with pytest.raises(PipelineError):
            raise exc
