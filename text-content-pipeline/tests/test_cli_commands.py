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


def test_show_preset_default(runner: CliRunner) -> None:
    """Test show-preset command with default preset."""
    result = runner.invoke(commands.show_preset, ["default"])
    
    assert result.exit_code == 0
    assert "#4A90E2" in result.output


def test_show_preset_invalid(runner: CliRunner) -> None:
    """Test show-preset with invalid preset."""
    result = runner.invoke(commands.show_preset, ["invalid"])
    
    assert result.exit_code != 0


def test_run_all_missing_theme(runner: CliRunner) -> None:
    """Test run-all without theme or payload."""
    result = runner.invoke(commands.run_all)
    
    assert result.exit_code != 0
    assert "With --theme, must also provide --year and --month" in result.output


def test_init_month_basic(runner: CliRunner) -> None:
    """Test init-month with year and month only."""
    result = runner.invoke(commands.init_month, ["2026", "8"])
    
    assert result.exit_code == 0
    assert "Created" in result.output
    assert "Your monthly theme here" in result.output


def test_init_month_with_theme(runner: CliRunner) -> None:
    """Test init-month with theme."""
    result = runner.invoke(commands.init_month, ["2026", "9", "--theme", "Test Theme"])
    
    assert result.exit_code == 0
    assert "Created" in result.output
    assert "Test Theme" in result.output
