"""Custom exceptions for the text content pipeline."""

from typing import Any


class PipelineError(Exception):
    """Base exception for all pipeline errors."""

    pass


class ValidationError(PipelineError):
    """Raised when payload validation fails."""

    def __init__(self, message: str, field: str | None = None) -> None:
        self.field = field
        super().__init__(message)


class CalendarResolutionError(PipelineError):
    """Raised when calendar week resolution fails."""

    pass


class SlotAssignmentError(PipelineError):
    """Raised when slot assignment fails or violates constraints."""

    pass


class AIGenerationError(PipelineError):
    """Raised when AI generation fails."""

    def __init__(self, message: str, touchpoint: str) -> None:
        self.touchpoint = touchpoint
        super().__init__(message)


class RendererError(PipelineError):
    """Raised when rendering fails."""

    pass


class ConfigurationError(PipelineError):
    """Raised when configuration is invalid."""

    pass


class ModelUnavailableError(AIGenerationError):
    """Raised when the required AI model is not available."""

    def __init__(self, model: str) -> None:
        self.model = model
        message = f"AI model '{model}' not found. Please run: ollama pull {model}"
        super().__init__(message, touchpoint="model_check")


class InvalidSlotEnumError(SlotAssignmentError):
    """Raised when an invalid slot type is provided."""

    def __init__(self, slot_type: str) -> None:
        self.slot_type = slot_type
        super().__init__(f"Invalid slot type: {slot_type}")
