from dataclasses import dataclass, field
from typing import List, Optional
from datetime import timedelta


@dataclass
class Word:
    id: str
    text: str
    start_time: float
    end_time: float

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass
class Segment:
    id: str
    text: str
    start_time: float
    end_time: float
    words: List[Word] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def word_count(self) -> int:
        return len(self.words)


@dataclass
class Take:
    id: str
    segment: Segment
    is_active: bool = False


@dataclass
class Group:
    id: str
    takes: List[Take] = field(default_factory=list)

    @property
    def active_take(self) -> Optional[Take]:
        for take in self.takes:
            if take.is_active:
                return take
        return None

    @property
    def count(self) -> int:
        return len(self.takes)


@dataclass
class Transcript:
    segments: List[Segment] = field(default_factory=list)
    groups: List[Group] = field(default_factory=list)

    @property
    def segment_count(self) -> int:
        return len(self.segments)

    @property
    def group_count(self) -> int:
        return len(self.groups)

    @property
    def duration(self) -> float:
        if not self.segments:
            return 0.0
        return max(seg.end_time for seg in self.segments)
