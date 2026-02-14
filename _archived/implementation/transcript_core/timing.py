from typing import List
from .models import Word, Segment


class TimingManager:
    @staticmethod
    def redistribute_word_timings(segment: Segment, new_text: str) -> List[Word]:
        if not segment.words:
            return []
        
        original_words = segment.words.copy()
        new_word_texts = new_text.split()
        
        if not new_word_texts:
            return []
        
        total_duration = segment.duration
        segment_start = segment.start_time
        
        if len(original_words) == len(new_word_texts):
            return TimingManager._equal_distribution(
                segment_start, total_duration, new_word_texts, original_words
            )
        
        return TimingManager._proportional_distribution(
            segment_start, total_duration, new_word_texts, original_words
        )

    @staticmethod
    def _equal_distribution(
        start: float, 
        duration: float, 
        new_texts: List[str],
        original_words: List[Word]
    ) -> List[Word]:
        if not new_texts:
            return []
        
        count = len(new_texts)
        if count == 1:
            word_duration = duration
            return [
                Word(
                    id=f"word_0",
                    text=new_texts[0],
                    start_time=start,
                    end_time=start + duration
                )
            ]
        
        result = []
        avg_duration = duration / count
        
        for i, text in enumerate(new_texts):
            word_start = start + (i * avg_duration)
            word_end = start + ((i + 1) * avg_duration)
            result.append(
                Word(
                    id=f"word_{i}",
                    text=text,
                    start_time=word_start,
                    end_time=word_end
                )
            )
        
        return result

    @staticmethod
    def _proportional_distribution(
        start: float,
        duration: float,
        new_texts: List[str],
        original_words: List[Word]
    ) -> List[Word]:
        if not new_texts:
            return []
        
        count = len(new_texts)
        if count == 1:
            return [
                Word(
                    id="word_0",
                    text=new_texts[0],
                    start_time=start,
                    end_time=start + duration
                )
            ]
        
        total_chars = sum(len(text) for text in new_texts)
        result = []
        current_time = start
        
        for i, text in enumerate(new_texts):
            if i == count - 1:
                word_end = start + duration
            else:
                char_proportion = len(text) / total_chars
                word_duration = duration * char_proportion
                word_end = current_time + word_duration
            
            result.append(
                Word(
                    id=f"word_{i}",
                    text=text,
                    start_time=current_time,
                    end_time=word_end
                )
            )
            current_time = word_end
        
        return result

    @staticmethod
    def shift_segment_timings(segment: Segment, shift_amount: float) -> None:
        segment.start_time += shift_amount
        segment.end_time += shift_amount
        
        for word in segment.words:
            word.start_time += shift_amount
            word.end_time += shift_amount

    @staticmethod
    def set_segment_duration(segment: Segment, new_duration: float) -> None:
        if new_duration <= 0:
            raise ValueError("Duration must be positive")
        
        scale_factor = new_duration / segment.duration
        
        segment.end_time = segment.start_time + new_duration
        
        for word in segment.words:
            word_duration = word.duration * scale_factor
            relative_start = word.start_time - segment.start_time
            word.start_time = segment.start_time + (relative_start * scale_factor)
            word.end_time = word.start_time + word_duration

    @staticmethod
    def get_word_at_time(segment: Segment, timestamp: float) -> Word | None:
        for word in segment.words:
            if word.start_time <= timestamp <= word.end_time:
                return word
        return None

    @staticmethod
    def adjust_segment_boundaries(
        segment: Segment,
        new_start: float,
        new_end: float
    ) -> None:
        old_duration = segment.duration
        new_duration = new_end - new_start
        
        if new_duration <= 0:
            raise ValueError("Segment duration must be positive")
        
        segment.start_time = new_start
        segment.end_time = new_end
        
        if segment.words and old_duration > 0:
            scale_factor = new_duration / old_duration
            
            for word in segment.words:
                relative_start = word.start_time - segment.start_time
                new_word_start = relative_start * scale_factor
                word_duration = word.duration * scale_factor
                word.start_time = segment.start_time + new_word_start
                word.end_time = word.start_time + word_duration
