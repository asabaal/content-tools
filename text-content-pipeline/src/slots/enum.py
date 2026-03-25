"""Daily slot function enum definitions."""

from enum import Enum, auto


class SlotFunction(str, Enum):
    """Daily content slot functions."""

    DECLARATIVE_STATEMENT = "declarative_statement"
    EXCERPT = "excerpt"
    PROCESS_NOTE = "process_note"
    UNANSWERED_QUESTION = "unanswered_question"
    REFRAMING = "reframing"
    QUIET_OBSERVATION = "quiet_observation"
    HUMAN_INTENTIONAL = "human_intentional"

    def is_automated(self) -> bool:
        """Check if this slot type is automated (non-human)."""
        return self != SlotFunction.HUMAN_INTENTIONAL

    @classmethod
    def automated_slots(cls) -> list["SlotFunction"]:
        """Get all automated slot types (excluding human)."""
        return [s for s in cls if s != SlotFunction.HUMAN_INTENTIONAL]
