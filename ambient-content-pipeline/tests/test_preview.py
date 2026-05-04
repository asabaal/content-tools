"""Tests for HTML preview generation."""

import json
import pytest
from pathlib import Path
from src.cli.preview import (
    _slot_pill,
    _date_display,
    _infer_week_number,
    generate_preview,
)


def test_slot_pill_known_type() -> None:
    pill = _slot_pill("declarative_statement")
    assert "#3B82F6" in pill
    assert "Declarative" in pill


def test_slot_pill_unknown_type() -> None:
    pill = _slot_pill("unknown_type")
    assert "unknown_type" in pill


def test_date_display() -> None:
    assert _date_display("2026-05-10") == "5/10"
    assert _date_display("2026-12-01") == "12/1"


def test_infer_week_number_month_boundary() -> None:
    """Test _infer_week_number when first Monday falls in previous month (line 69)."""
    # September 2026: 1st is Tuesday. The Monday before (Aug 31) is in prev month,
    # so first_monday rolls forward to Sep 7.
    assert _infer_week_number("2026-09-07", 2026, 9) == 1
    assert _infer_week_number("2026-09-14", 2026, 9) == 2


def test_infer_week_number_normal() -> None:
    assert _infer_week_number("2026-05-04", 2026, 5) == 1
    assert _infer_week_number("2026-05-11", 2026, 5) == 2
    assert _infer_week_number("2026-05-25", 2026, 5) == 4


def test_generate_preview_creates_html(tmp_path: Path) -> None:
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()

    plan_data = {
        "year": 2026,
        "month": 5,
        "monthly_theme": "As God Has Said",
        "weekly_subthemes": ["Week One", "Week Two"],
        "weekly_subtitles": {"1": "W1 Sub"},
        "slot_plan": {"2026-05-04": "declarative_statement"},
        "schedule_summary": [
            {
                "date": "2026-05-04",
                "weekday": "Monday",
                "week_number": 1,
                "slot_type": "declarative_statement",
                "subtheme": "Week One",
                "is_automated": True,
            },
            {
                "date": "2026-05-10",
                "weekday": "Sunday",
                "week_number": 1,
                "slot_type": "human_intentional",
                "subtheme": "Week One",
                "is_automated": False,
            },
        ],
    }
    (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))

    texts_data = {
        "texts": {"2026-05-04": "God said let there be light"}
    }
    (plans_dir / "2026-05_texts.json").write_text(json.dumps(texts_data))

    result = generate_preview(tmp_path, year=2026, month=5)
    assert result == tmp_path / "preview.html"
    html = result.read_text(encoding="utf-8")
    assert "As God Has Said" in html
    assert "God said let there be light" in html
    assert "Human Intentional" in html
    assert "5/4" in html
    assert "5/10" in html
    assert "Week One" in html
    assert "W1 Sub" in html


def test_generate_preview_no_plan_files(tmp_path: Path) -> None:
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()
    with pytest.raises(FileNotFoundError, match="No plan file"):
        generate_preview(tmp_path)


def test_generate_preview_specific_month_not_found(tmp_path: Path) -> None:
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()
    (plans_dir / "2026-04_plan.json").write_text("{}")
    with pytest.raises(FileNotFoundError, match="No plan file for 2026-05"):
        generate_preview(tmp_path, year=2026, month=5)


def test_generate_preview_no_texts_file(tmp_path: Path) -> None:
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()
    plan_data = {
        "year": 2026, "month": 5, "monthly_theme": "T",
        "weekly_subthemes": [], "schedule_summary": [],
    }
    (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
    with pytest.raises(FileNotFoundError, match="No texts file"):
        generate_preview(tmp_path, year=2026, month=5)


def test_generate_preview_uses_latest_plan_without_year_month(tmp_path: Path) -> None:
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()

    plan_a = {
        "year": 2026, "month": 2, "monthly_theme": "Feb",
        "weekly_subthemes": [], "schedule_summary": [],
    }
    plan_b = {
        "year": 2026, "month": 5, "monthly_theme": "May",
        "weekly_subthemes": ["W1"],
        "schedule_summary": [
            {"date": "2026-05-04", "weekday": "Monday", "week_number": 1,
             "slot_type": "declarative_statement", "subtheme": "W1", "is_automated": True},
        ],
    }
    (plans_dir / "2026-02_plan.json").write_text(json.dumps(plan_a))
    (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_b))
    (plans_dir / "2026-05_texts.json").write_text(json.dumps({"texts": {"2026-05-04": "Hello"}}))

    result = generate_preview(tmp_path)
    html = result.read_text(encoding="utf-8")
    assert "May" in html


def test_generate_preview_infers_week_number(tmp_path: Path) -> None:
    plans_dir = tmp_path / "plans"
    plans_dir.mkdir()

    plan_data = {
        "year": 2026, "month": 5, "monthly_theme": "T",
        "weekly_subthemes": ["W1", "W2"],
        "schedule_summary": [
            {"date": "2026-05-04", "weekday": "Monday", "slot_type": "declarative_statement",
             "subtheme": "W1", "is_automated": True},
            {"date": "2026-05-11", "weekday": "Monday", "slot_type": "excerpt",
             "subtheme": "W2", "is_automated": True},
        ],
    }
    (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
    (plans_dir / "2026-05_texts.json").write_text(json.dumps({"texts": {"2026-05-04": "A", "2026-05-11": "B"}}))

    result = generate_preview(tmp_path, year=2026, month=5)
    html = result.read_text(encoding="utf-8")
    assert "Week 1" in html
    assert "Week 2" in html
