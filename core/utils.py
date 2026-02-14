"""
Utility functions for content-tools.
"""


def format_time(seconds: float, format_type: str = "standard") -> str:
    """
    Format seconds into a human-readable time string.
    
    Args:
        seconds: Time in seconds
        format_type: One of "standard", "short", "ms", "hms"
    
    Returns:
        Formatted time string
    
    Examples:
        format_time(65.5) -> "1:05"
        format_time(65.5, "ms") -> "1:05.500"
        format_time(3661, "hms") -> "1:01:01"
    """
    if seconds < 0:
        return ""
    
    total_seconds = seconds
    hours = int(total_seconds // 3600)
    total_seconds %= 3600
    minutes = int(total_seconds // 60)
    secs = int(total_seconds % 60)
    millis = int((total_seconds % 1) * 1000)
    
    if format_type == "ms":
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}.{millis:03d}"
        return f"{minutes}:{secs:02d}.{millis:03d}"
    
    if format_type == "hms":
        return f"{hours}:{minutes:02d}:{secs:02d}"
    
    if format_type == "short":
        if minutes == 0:
            return f"{secs}s"
        return f"{minutes}:{secs:02d}"
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    
    return f"{minutes}:{secs:02d}"


def parse_time(time_str: str) -> float:
    """
    Parse a time string into seconds.
    
    Supports formats: "1:30", "1:30.5", "1:30:00", "90s"
    
    Args:
        time_str: Time string to parse
    
    Returns:
        Time in seconds
    """
    time_str = time_str.strip().lower()
    
    if time_str.endswith("s"):
        return float(time_str[:-1])
    
    parts = time_str.split(":")
    
    if len(parts) == 1:
        return float(parts[0])
    
    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes) * 60 + float(seconds)
    
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    
    raise ValueError(f"Invalid time format: {time_str}")


def word_count(text: str) -> int:
    """Count words in a text string."""
    return len(text.split())


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
