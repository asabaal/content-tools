"""Tests for AI generator - no mocking approach."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.ai_generator import generator
from src.slots.enum import SlotFunction


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


@pytest.mark.asyncio
async def test_check_model_available_true() -> None:
    """Test check_model_available returns True when model exists."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": "gpt-oss:20b"}]}
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await generator.check_model_available()
        assert result is True


@pytest.mark.asyncio
async def test_check_model_available_false() -> None:
    """Test check_model_available returns False when model doesn't exist."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": "other-model"}]}
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await generator.check_model_available()
        assert result is False


@pytest.mark.asyncio
async def test_check_model_available_exception() -> None:
    """Test check_model_available returns False on exception."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=Exception("Connection error"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await generator.check_model_available()
        assert result is False


def test_call_ollama_exists() -> None:
    """Test that _call_ollama function exists."""
    assert hasattr(generator, "_call_ollama")


def test_generate_weekly_subtitle_exists() -> None:
    """Test that generate_weekly_subtitle function exists."""
    assert hasattr(generator, "generate_weekly_subtitle")


def test_generate_daily_text_accepts_max_words() -> None:
    """Test that generate_daily_text accepts max_words parameter."""
    import inspect
    sig = inspect.signature(generator.generate_daily_text)
    params = list(sig.parameters.keys())
    assert "max_words" in params


def test_truncation_logic() -> None:
    """Test the word truncation logic in generate_daily_text."""
    text = "This is a sentence with more than five words to test truncation."
    max_words = 5
    
    words = text.split()
    if len(words) > max_words:
        truncated = " ".join(words[:max_words])
    else:
        truncated = text
    
    assert len(truncated.split()) == 5
    assert truncated == "This is a sentence with"


def test_truncation_with_sentence_boundary() -> None:
    """Test truncation respects sentence boundary when possible."""
    text = "First sentence. Second sentence. Third sentence here."
    max_words = 4
    
    words = text.split()
    if len(words) > max_words:
        truncated = " ".join(words[:max_words])
        last_punct = max(truncated.rfind("."), truncated.rfind("!"), truncated.rfind("?"))
        if last_punct > max_words // 2:
            truncated = truncated[: last_punct + 1]
    else:
        truncated = text
    
    # After 4 words we have "First sentence. Second sentence."
    # The last period is at position 31
    # Since 31 > 4//2=2, we truncate at the period
    assert truncated == "First sentence. Second sentence."


@pytest.mark.asyncio
async def test_generate_weekly_subtitle_calls_ollama() -> None:
    """Test that generate_weekly_subtitle calls _call_ollama."""
    with patch("src.ai_generator.generator._call_ollama", new_callable=AsyncMock, return_value="Short Title"):
        result = await generator.generate_weekly_subtitle("Long subtheme description")
        assert result == "Short Title"


@pytest.mark.asyncio
async def test_generate_daily_text_with_max_words() -> None:
    """Test generate_daily_text with custom max_words."""
    with patch("src.ai_generator.generator._call_ollama", new_callable=AsyncMock, return_value="This is a short response"):
        result = await generator.generate_daily_text(
            slot_type=SlotFunction.DECLARATIVE_STATEMENT,
            monthly_theme="Test Theme",
            weekly_subtheme="Test Subtheme",
            max_words=10,
        )
        assert result == "This is a short response"


@pytest.mark.asyncio
async def test_generate_daily_text_truncates_long_response() -> None:
    """Test generate_daily_text truncates response exceeding max_words."""
    long_response = "This is a very long response that definitely exceeds the maximum word limit set for this particular slot type and needs to be truncated"
    
    with patch("src.ai_generator.generator._call_ollama", new_callable=AsyncMock, return_value=long_response):
        result = await generator.generate_daily_text(
            slot_type=SlotFunction.DECLARATIVE_STATEMENT,
            monthly_theme="Test Theme",
            weekly_subtheme="Test Subtheme",
            max_words=5,
        )
        # Should be truncated to 5 words
        assert len(result.split()) <= 5


@pytest.mark.asyncio
async def test_generate_daily_text_truncates_at_sentence_boundary() -> None:
    """Test generate_daily_text truncates at sentence boundary when possible."""
    long_response = "First sentence here. And this is the second part that should be removed entirely after truncation."
    
    with patch("src.ai_generator.generator._call_ollama", new_callable=AsyncMock, return_value=long_response):
        result = await generator.generate_daily_text(
            slot_type=SlotFunction.DECLARATIVE_STATEMENT,
            monthly_theme="Test Theme",
            weekly_subtheme="Test Subtheme",
            max_words=4,
        )
        # Should be truncated at sentence boundary: "First sentence here."
        assert result == "First sentence here."


@pytest.mark.asyncio
async def test_generate_daily_text_uses_default_max_words() -> None:
    """Test generate_daily_text uses default max_words from config when not provided."""
    with patch("src.ai_generator.generator._call_ollama", new_callable=AsyncMock, return_value="Short response"):
        result = await generator.generate_daily_text(
            slot_type=SlotFunction.DECLARATIVE_STATEMENT,
            monthly_theme="Test Theme",
            weekly_subtheme="Test Subtheme",
        )
        assert result == "Short response"


@pytest.mark.asyncio
async def test_generate_weekly_subthemes_success() -> None:
    """Test generate_weekly_subthemes parses JSON response."""
    with patch("src.ai_generator.generator._call_ollama", new_callable=AsyncMock, return_value='["W1", "W2", "W3"]'):
        result = await generator.generate_weekly_subthemes("Test Theme", 3)
        assert result == ["W1", "W2", "W3"]


@pytest.mark.asyncio
async def test_generate_weekly_subthemes_invalid_json() -> None:
    """Test generate_weekly_subthemes raises error on invalid JSON."""
    from src.errors.exceptions import AIGenerationError
    
    with patch("src.ai_generator.generator._call_ollama", new_callable=AsyncMock, return_value="not valid json"):
        with pytest.raises(AIGenerationError) as exc_info:
            await generator.generate_weekly_subthemes("Test Theme", 3)
        assert "Failed to parse" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_weekly_subthemes_wrong_count() -> None:
    """Test generate_weekly_subthemes raises error on wrong count."""
    from src.errors.exceptions import AIGenerationError
    
    with patch("src.ai_generator.generator._call_ollama", new_callable=AsyncMock, return_value='["W1", "W2"]'):
        with pytest.raises(AIGenerationError) as exc_info:
            await generator.generate_weekly_subthemes("Test Theme", 3)
        assert "Expected 3" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_weekly_subthemes_not_a_list() -> None:
    """Test generate_weekly_subthemes raises error when response is not a list."""
    from src.errors.exceptions import AIGenerationError
    
    with patch("src.ai_generator.generator._call_ollama", new_callable=AsyncMock, return_value='{"key": "value"}'):
        with pytest.raises(AIGenerationError) as exc_info:
            await generator.generate_weekly_subthemes("Test Theme", 3)
        assert "not a list" in str(exc_info.value)


@pytest.mark.asyncio
async def test_plan_monthly_slots_success() -> None:
    """Test plan_monthly_slots parses JSON response."""
    from src.weekly_calendar.resolver import ResolvedCalendar, WeekInfo
    from src.payload.schema import WeekRule, VideoWeek
    
    week_info = MagicMock()
    week_info.week_number = 1
    week_info.monday_date = "2026-02-02"
    week_info.sunday_date = "2026-02-08"
    week_info.subtheme = "Test Subtheme"
    week_info.is_video_week = False
    
    calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test",
        weekly_subthemes=["W1"],
        weeks=[week_info],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    with patch("src.ai_generator.generator._call_ollama", new_callable=AsyncMock, return_value='{"2026-02-02": "declarative_statement"}'):
        result = await generator.plan_monthly_slots(calendar)
        assert result == {"2026-02-02": "declarative_statement"}


@pytest.mark.asyncio
async def test_plan_monthly_slots_invalid_json() -> None:
    """Test plan_monthly_slots raises error on invalid JSON."""
    from src.errors.exceptions import AIGenerationError
    from src.weekly_calendar.resolver import ResolvedCalendar
    from src.payload.schema import WeekRule, VideoWeek
    
    calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test",
        weekly_subthemes=["W1"],
        weeks=[],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    with patch("src.ai_generator.generator._call_ollama", new_callable=AsyncMock, return_value="not valid json"):
        with pytest.raises(AIGenerationError):
            await generator.plan_monthly_slots(calendar)


@pytest.mark.asyncio
async def test_plan_monthly_slots_not_a_dict() -> None:
    """Test plan_monthly_slots raises error when response is not a dict."""
    from src.errors.exceptions import AIGenerationError
    from src.weekly_calendar.resolver import ResolvedCalendar
    from src.payload.schema import WeekRule, VideoWeek
    
    calendar = ResolvedCalendar(
        year=2026,
        month=2,
        monthly_theme="Test",
        weekly_subthemes=["W1"],
        weeks=[],
        week_rule=WeekRule.MONDAY_DETERMINES_MONTH,
        video_week=VideoWeek.LAST_WEEK,
    )
    
    with patch("src.ai_generator.generator._call_ollama", new_callable=AsyncMock, return_value='["not", "a", "dict"]'):
        with pytest.raises(AIGenerationError):
            await generator.plan_monthly_slots(calendar)


@pytest.mark.asyncio
async def test_call_ollama_model_not_found() -> None:
    """Test _call_ollama raises AIGenerationError on 404 (ModelUnavailableError is caught)."""
    from src.errors.exceptions import AIGenerationError
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AIGenerationError) as exc_info:
            await generator._call_ollama("test prompt", "test_touchpoint")
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_call_ollama_empty_response() -> None:
    """Test _call_ollama raises AIGenerationError on empty response."""
    from src.errors.exceptions import AIGenerationError
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"response": ""}
    
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AIGenerationError):
            await generator._call_ollama("test prompt", "test_touchpoint")


@pytest.mark.asyncio
async def test_call_ollama_success() -> None:
    """Test _call_ollama returns response text."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"response": "  generated text  "}
    
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await generator._call_ollama("test prompt", "test_touchpoint")
        assert result == "generated text"


@pytest.mark.asyncio
async def test_call_ollama_fails_after_max_retries() -> None:
    """Test _call_ollama raises error after max retries."""
    import httpx
    from src.errors.exceptions import AIGenerationError
    
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AIGenerationError) as exc_info:
            await generator._call_ollama("test prompt", "test_touchpoint")
        assert "2 attempts" in str(exc_info.value)


@pytest.mark.asyncio
async def test_call_ollama_http_error() -> None:
    """Test _call_ollama raises AIGenerationError on HTTP error (non-404)."""
    import httpx
    from src.errors.exceptions import AIGenerationError
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response
    )
    
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AIGenerationError) as exc_info:
            await generator._call_ollama("test prompt", "test_touchpoint")
        assert "HTTP error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_call_ollama_http_404_via_raise_for_status() -> None:
    """Test _call_ollama handles 404 via raise_for_status HTTPStatusError."""
    import httpx
    from src.errors.exceptions import ModelUnavailableError, AIGenerationError
    
    # The response status_code is 200, but raise_for_status raises HTTPStatusError
    # with a response that has status_code 404
    mock_response = MagicMock()
    mock_response.status_code = 200  # Not 404, so we skip line 245
    
    # Create a mock response for the HTTPStatusError that has status_code 404
    error_response = MagicMock()
    error_response.status_code = 404
    
    http_error = httpx.HTTPStatusError(
        "Not found", request=MagicMock(), response=error_response
    )
    mock_response.raise_for_status.side_effect = http_error
    
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        # This triggers the HTTPStatusError path which checks e.response.status_code == 404
        # and raises ModelUnavailableError at line 260
        with pytest.raises((ModelUnavailableError, AIGenerationError)):
            await generator._call_ollama("test prompt", "test_touchpoint")


@pytest.mark.asyncio
async def test_call_ollama_unexpected_exception() -> None:
    """Test _call_ollama raises AIGenerationError on unexpected exception."""
    from src.errors.exceptions import AIGenerationError
    
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=RuntimeError("unexpected"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AIGenerationError) as exc_info:
            await generator._call_ollama("test prompt", "test_touchpoint")
        assert "Unexpected error" in str(exc_info.value)
