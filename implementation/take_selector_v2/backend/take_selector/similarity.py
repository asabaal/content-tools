"""
Similarity scoring for transcript segments.

Provides deterministic similarity metrics to identify candidate duplicate takes.
"""

from typing import List, Tuple

from .data_loader import Segment


def compute_segment_similarity(segment_a: Segment, segment_b: Segment) -> float:
    """
    Compute similarity between two transcript segments.
    
    Uses Jaccard similarity on word tokens for a deterministic, explainable score.
    Jaccard similarity = |intersection| / |union| of word sets.
    
    Args:
        segment_a: First segment to compare
        segment_b: Second segment to compare
        
    Returns:
        Similarity score between 0.0 (no similarity) and 1.0 (identical)
        
    Examples:
        >>> s1 = Segment("1", 0, 5, "hello world")
        >>> s2 = Segment("2", 0, 5, "hello universe")
        >>> compute_segment_similarity(s1, s2)
        0.3333...
    """
    text_a = segment_a.text.strip()
    text_b = segment_b.text.strip()
    
    if not text_a and not text_b:
        return 1.0
    if not text_a or not text_b:
        return 0.0
    
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    
    intersection = words_a & words_b
    union = words_a | words_b
    
    return len(intersection) / len(union)


def find_candidate_duplicates(
    segments: List[Segment],
    threshold: float = 0.7
) -> List[Tuple[str, str, float]]:
    """
    Find candidate duplicate pairs from a list of segments.
    
    Compares all segment pairs and returns those with similarity above threshold.
    Results are sorted by similarity score in descending order.
    
    Args:
        segments: List of segments to analyze for duplicates
        threshold: Minimum similarity score to consider as a candidate (0.0 to 1.0)
        
    Returns:
        List of tuples (segment_id_a, segment_id_b, similarity_score) sorted by score
        
    Raises:
        ValueError: If threshold is not in [0.0, 1.0]
        
    Examples:
        >>> segments = [
        ...     Segment("1", 0, 5, "hello world"),
        ...     Segment("2", 0, 5, "hello world"),
        ...     Segment("3", 0, 5, "different text")
        ... ]
        >>> pairs = find_candidate_duplicates(segments, threshold=0.9)
        >>> len(pairs)
        1
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")
    
    candidates = []
    n = len(segments)
    
    for i in range(n):
        for j in range(i + 1, n):
            similarity = compute_segment_similarity(segments[i], segments[j])
            if similarity >= threshold:
                candidates.append((
                    segments[i].segment_id,
                    segments[j].segment_id,
                    similarity
                ))
    
    candidates.sort(key=lambda x: x[2], reverse=True)
    
    return candidates
