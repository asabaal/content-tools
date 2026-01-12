"""Tests for CLI commands."""

from click.testing import CliRunner
import pytest

from src.cli import commands


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_list_presets(runner: CliRunner) -> None:
    """Test list-presets command."""
    result = runner.invoke(commands.list_presets)
    
    assert result.exit_code == 0
    assert "default" in result.output


def test_show_preset_invalid(runner: CliRunner) -> None:
    """Test show-preset with invalid preset."""
    result = runner.invoke(commands.show_preset, ["invalid"])
    
    assert result.exit_code != 0


def test_run_all_missing_theme(runner: CliRunner) -> None:
    """Test run-all without theme or payload."""
    result = runner.invoke(commands.run_all)
    
    assert result.exit_code != 0
    assert "With --theme, must also provide --year and --month" in result.output


def test_run_all_with_year_missing_month(runner: CliRunner) -> None:
    """Test run-all with year but no month."""
    result = runner.invoke(commands.run_all, ["--theme", "Test", "--year", "2026"])
    
    assert result.exit_code != 0
