from typing import List, Optional
from .models import Segment, Word


class SegmentManager:
    def __init__(self):
        self._segments: List[Segment] = []

    def add_segment(self, segment: Segment) -> None:
        self._segments.append(segment)

    def remove_segment(self, segment_id: str) -> bool:
        for i, seg in enumerate(self._segments):
            if seg.id == segment_id:
                del self._segments[i]
                return True
        return False

    def get_segment(self, segment_id: str) -> Optional[Segment]:
        for seg in self._segments:
            if seg.id == segment_id:
                return seg
        return None

    def get_all_segments(self) -> List[Segment]:
        return self._segments.copy()

    def update_text(self, segment_id: str, new_text: str) -> bool:
        seg = self.get_segment(segment_id)
        if seg:
            seg.text = new_text
            return True
        return False

    def get_segment_at_time(self, timestamp: float) -> Optional[Segment]:
        for seg in self._segments:
            if seg.start_time <= timestamp <= seg.end_time:
                return seg
        return None

    def get_segments_in_range(self, start: float, end: float) -> List[Segment]:
        return [
            seg for seg in self._segments
            if not (seg.end_time < start or seg.start_time > end)
        ]

    def reorder_segments(self, segment_ids: List[str]) -> bool:
        new_order = []
        for seg_id in segment_ids:
            seg = self.get_segment(seg_id)
            if not seg:
                return False
            new_order.append(seg)
        
        if len(new_order) != len(self._segments):
            return False
        
        self._segments = new_order
        return True

    def create_segment_from_words(
        self, 
        id: str, 
        words: List[Word],
        text: Optional[str] = None
    ) -> Segment:
        if not words:
            raise ValueError("Cannot create segment from empty word list")
        
        start = min(w.start_time for w in words)
        end = max(w.end_time for w in words)
        
        if text is None:
            text = " ".join(w.text for w in words)
        
        return Segment(id=id, text=text, start_time=start, end_time=end, words=words.copy())
