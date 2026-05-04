"""Tests for CLI commands."""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from click.testing import CliRunner

from src.cli.commands import cli, _parse_feedback, _refine_post_with_ai


@pytest.fixture
def runner():
    return CliRunner()


class TestParseFeedback:
    def test_single_entry(self):
        result = _parse_feedback("2026-05-04::Too generic")
        assert result == [("2026-05-04", "Too generic")]

    def test_multiple_entries(self):
        result = _parse_feedback("2026-05-04::Too generic|2026-05-05::Too abstract")
        assert result == [("2026-05-04", "Too generic"), ("2026-05-05", "Too abstract")]

    def test_missing_separator(self):
        with pytest.raises(ValueError, match="Expected format"):
            _parse_feedback("2026-05-04 Too generic")

    def test_empty_date(self):
        with pytest.raises(ValueError, match="Expected format"):
            _parse_feedback("::feedback text")

    def test_empty_feedback(self):
        with pytest.raises(ValueError, match="Expected format"):
            _parse_feedback("2026-05-04::")

    def test_empty_string(self):
        with pytest.raises(ValueError, match="No valid feedback"):
            _parse_feedback("")

    def test_whitespace_ignored(self):
        result = _parse_feedback(" 2026-05-04 :: feedback text ")
        assert result == [("2026-05-04", "feedback text")]


@pytest.mark.asyncio
async def test_refine_post_with_ai() -> None:
    with patch("src.cli.commands.generator._call_ollama", new_callable=AsyncMock, return_value="Refined text"):
        result = await _refine_post_with_ai(
            original_post="Original post",
            feedback="Make it shorter",
            slot_type="declarative_statement",
            monthly_theme="Test Theme",
            weekly_subtheme="Test Sub",
            max_words=50,
        )
        assert result == "Refined text"


class TestPreviewCommand:
    def test_preview_with_plan_dir(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "T",
            "weekly_subthemes": [], "schedule_summary": [],
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        (plans_dir / "2026-05_texts.json").write_text(json.dumps({"texts": {}}))

        with patch("src.cli.commands.generate_preview", return_value=tmp_path / "preview.html"):
            result = runner.invoke(cli, ["preview", "--plan-dir", str(tmp_path)])
            assert result.exit_code == 0
            assert "Preview generated" in result.output

    def test_preview_with_open(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "T",
            "weekly_subthemes": [], "schedule_summary": [],
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        (plans_dir / "2026-05_texts.json").write_text(json.dumps({"texts": {}}))

        with patch("src.cli.commands.generate_preview", return_value=tmp_path / "preview.html"), \
             patch("webbrowser.open") as mock_open:
            result = runner.invoke(cli, ["preview", "--plan-dir", str(tmp_path), "--open"])
            assert result.exit_code == 0
            mock_open.assert_called_once()

    def test_preview_missing_args(self, runner):
        result = runner.invoke(cli, ["preview"])
        assert result.exit_code != 0

    def test_preview_dir_not_found(self, runner):
        result = runner.invoke(cli, ["preview", "--plan-dir", "/nonexistent/path"])
        assert result.exit_code != 0

    def test_preview_file_not_found_error(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()

        with patch("src.cli.commands.generate_preview", side_effect=FileNotFoundError("No plan file")):
            result = runner.invoke(cli, ["preview", "--plan-dir", str(tmp_path)])
            assert result.exit_code != 0
            assert "No plan file" in result.output


class TestRegenTextCommand:
    def _make_plan_dir(self, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "Test",
            "weekly_subthemes": ["W1"],
            "schedule_summary": [
                {"date": "2026-05-04", "weekday": "Monday", "week_number": 1,
                 "slot_type": "declarative_statement", "subtheme": "W1", "is_automated": True},
                {"date": "2026-05-05", "weekday": "Tuesday", "week_number": 1,
                 "slot_type": "excerpt", "subtheme": "W1", "is_automated": True},
            ],
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        texts_data = {"texts": {"2026-05-04": "Old text 1", "2026-05-05": "Old text 2"}}
        (plans_dir / "2026-05_texts.json").write_text(json.dumps(texts_data))
        return tmp_path

    def test_regen_text_success(self, runner, tmp_path):
        plan_dir = self._make_plan_dir(tmp_path)

        with patch("src.cli.commands.generator.check_model_available", new_callable=AsyncMock, return_value=True), \
             patch("src.cli.commands.generator.generate_daily_text", new_callable=AsyncMock, return_value="New text"):
            result = runner.invoke(cli, [
                "regen-text", "--plan-dir", str(plan_dir),
                "--dates", "2026-05-04",
            ])
            assert result.exit_code == 0
            assert "Regenerating" in result.output
            texts = json.loads((plan_dir / "plans" / "2026-05_texts.json").read_text())
            assert texts["texts"]["2026-05-04"] == "New text"

    def test_regen_text_invalid_date(self, runner, tmp_path):
        plan_dir = self._make_plan_dir(tmp_path)

        result = runner.invoke(cli, [
            "regen-text", "--plan-dir", str(plan_dir),
            "--dates", "2026-05-20",
        ])
        assert result.exit_code != 0
        assert "not found in plan" in result.output

    def test_regen_text_no_plan_files(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()

        result = runner.invoke(cli, [
            "regen-text", "--plan-dir", str(tmp_path),
            "--dates", "2026-05-04",
        ])
        assert result.exit_code != 0
        assert "No plan file" in result.output

    def test_regen_text_model_unavailable(self, runner, tmp_path):
        plan_dir = self._make_plan_dir(tmp_path)

        with patch("src.cli.commands.generator.check_model_available", new_callable=AsyncMock, return_value=False):
            result = runner.invoke(cli, [
                "regen-text", "--plan-dir", str(plan_dir),
                "--dates", "2026-05-04",
            ])
            assert result.exit_code != 0
            assert "not found in Ollama" in result.output

    def test_regen_text_with_preview(self, runner, tmp_path):
        plan_dir = self._make_plan_dir(tmp_path)

        with patch("src.cli.commands.generator.check_model_available", new_callable=AsyncMock, return_value=True), \
             patch("src.cli.commands.generator.generate_daily_text", new_callable=AsyncMock, return_value="New text"), \
             patch("src.cli.commands.generate_preview", return_value=tmp_path / "preview.html") as mock_preview:
            result = runner.invoke(cli, [
                "regen-text", "--plan-dir", str(plan_dir),
                "--dates", "2026-05-04", "--preview",
            ])
            assert result.exit_code == 0
            mock_preview.assert_called_once()

    def test_regen_text_with_model_override(self, runner, tmp_path):
        plan_dir = self._make_plan_dir(tmp_path)

        with patch("src.cli.commands.generator.check_model_available", new_callable=AsyncMock, return_value=True), \
             patch("src.cli.commands.generator.generate_daily_text", new_callable=AsyncMock, return_value="New text"):
            result = runner.invoke(cli, [
                "regen-text", "--plan-dir", str(plan_dir),
                "--dates", "2026-05-04", "--model", "custom-model",
            ])
            assert result.exit_code == 0


class TestPreviewYearMonth:
    def test_preview_with_year_month(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "T",
            "weekly_subthemes": [], "schedule_summary": [],
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        (plans_dir / "2026-05_texts.json").write_text(json.dumps({"texts": {}}))
        outputs_dir = tmp_path / "202605"
        outputs_dir.mkdir()

        with patch("src.cli.commands.generate_preview", return_value=tmp_path / "preview.html"):
            result = runner.invoke(cli, ["preview", "--year", "2026", "--month", "5"])
            assert result.exit_code == 0

    def test_preview_year_month_fallback_to_outputs(self, runner, tmp_path, monkeypatch):
        """When outputs/YYYYMM dir doesn't exist, falls back to outputs/."""
        outputs_dir = tmp_path / "outputs"
        outputs_dir.mkdir()
        plans_dir = outputs_dir / "plans"
        plans_dir.mkdir()
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "T",
            "weekly_subthemes": [], "schedule_summary": [],
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        (plans_dir / "2026-05_texts.json").write_text(json.dumps({"texts": {}}))

        monkeypatch.chdir(tmp_path)
        with patch("src.cli.commands.generate_preview", return_value=tmp_path / "preview.html"):
            result = runner.invoke(cli, ["preview", "--year", "2026", "--month", "5"])
            assert result.exit_code == 0


class TestRegenTextEdgeCases:
    def _setup(self, tmp_path, schedule_override=None):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        schedule = schedule_override or [
            {"date": "2026-05-04", "weekday": "Monday", "week_number": 1,
             "slot_type": "declarative_statement", "subtheme": "W1", "is_automated": True},
        ]
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "Test",
            "weekly_subthemes": ["W1"],
            "schedule_summary": schedule,
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        (plans_dir / "2026-05_texts.json").write_text(json.dumps({"texts": {"2026-05-04": "Old"}}))
        return tmp_path

    def test_no_matching_plan_for_month(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        (plans_dir / "2026-04_plan.json").write_text("{}")
        (plans_dir / "2026-04_texts.json").write_text("{}")

        result = runner.invoke(cli, [
            "regen-text", "--plan-dir", str(tmp_path), "--dates", "2026-05-04",
        ])
        assert "No plan file for 2026-05" in result.output

    def test_no_matching_texts_for_month(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        (plans_dir / "2026-05_plan.json").write_text("{}")
        (plans_dir / "2026-04_texts.json").write_text("{}")

        result = runner.invoke(cli, [
            "regen-text", "--plan-dir", str(tmp_path), "--dates", "2026-05-04",
        ])
        assert "No texts file for 2026-05" in result.output

    def test_no_texts_files_at_all(self, runner, tmp_path):
        """When plan files exist but no texts files at all (line 619-620)."""
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        (plans_dir / "2026-05_plan.json").write_text("{}")

        result = runner.invoke(cli, [
            "regen-text", "--plan-dir", str(tmp_path), "--dates", "2026-05-04",
        ])
        assert result.exit_code != 0
        assert "No texts file" in result.output

    def test_unknown_slot_type(self, runner, tmp_path):
        plan_dir = self._setup(tmp_path, schedule_override=[
            {"date": "2026-05-04", "weekday": "Monday", "week_number": 1,
             "slot_type": "fake_type", "subtheme": "W1", "is_automated": True},
        ])

        with patch("src.cli.commands.generator.check_model_available", new_callable=AsyncMock, return_value=True):
            result = runner.invoke(cli, [
                "regen-text", "--plan-dir", str(plan_dir), "--dates", "2026-05-04",
            ])
            assert "Unknown slot type" in result.output

    def test_temperature_override(self, runner, tmp_path):
        plan_dir = self._setup(tmp_path)

        with patch("src.cli.commands.generator.check_model_available", new_callable=AsyncMock, return_value=True), \
             patch("src.cli.commands.generator.generate_daily_text", new_callable=AsyncMock, return_value="New"):
            result = runner.invoke(cli, [
                "regen-text", "--plan-dir", str(plan_dir),
                "--dates", "2026-05-04", "--temperature", "0.8",
            ])
            assert result.exit_code == 0

    def test_generation_failure(self, runner, tmp_path):
        plan_dir = self._setup(tmp_path)

        with patch("src.cli.commands.generator.check_model_available", new_callable=AsyncMock, return_value=True), \
             patch("src.cli.commands.generator.generate_daily_text", new_callable=AsyncMock, side_effect=RuntimeError("boom")):
            result = runner.invoke(cli, [
                "regen-text", "--plan-dir", str(plan_dir), "--dates", "2026-05-04",
            ])
            assert "Failed to regenerate" in result.output

    def test_preview_failure(self, runner, tmp_path):
        plan_dir = self._setup(tmp_path)

        with patch("src.cli.commands.generator.check_model_available", new_callable=AsyncMock, return_value=True), \
             patch("src.cli.commands.generator.generate_daily_text", new_callable=AsyncMock, return_value="New"), \
             patch("src.cli.commands.generate_preview", side_effect=Exception("Preview error")):
            result = runner.invoke(cli, [
                "regen-text", "--plan-dir", str(plan_dir),
                "--dates", "2026-05-04", "--preview",
            ])
            assert "Preview generation failed" in result.output


class TestRerenderEdgeCases:
    def _setup(self, tmp_path, render_config=None):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        rc = render_config or {"animate": True, "style_preset": "default"}
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "Test",
            "weekly_subthemes": ["W1"],
            "schedule_summary": [
                {"date": "2026-05-04", "weekday": "Monday", "week_number": 1,
                 "slot_type": "declarative_statement", "subtheme": "W1", "is_automated": True},
            ],
            "render_config": rc,
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        (plans_dir / "2026-05_texts.json").write_text(json.dumps({"texts": {"2026-05-04": "Text"}}))
        return tmp_path

    def test_texts_file_not_found_for_year_month(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "Test",
            "weekly_subthemes": [], "schedule_summary": [],
            "render_config": {"style_preset": "default"},
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        (plans_dir / "2026-04_texts.json").write_text("{}")

        result = runner.invoke(cli, [
            "rerender", "--plan-dir", str(tmp_path),
            "--year", "2026", "--month", "5", "--all",
        ])
        assert result.exit_code != 0
        assert "No texts file for 2026-05" in result.output

    def test_saved_music_not_found(self, runner, tmp_path):
        plan_dir = self._setup(tmp_path, render_config={
            "animate": True, "style_preset": "default",
            "bg_music": True, "bg_music_path": "/nonexistent/music.wav",
        })

        with patch("src.renderer.music_gen.generate_music_prompt_from_theme", new_callable=AsyncMock, return_value="piano"), \
             patch("src.renderer.music_gen.calculate_music_duration", return_value=10.0), \
             patch("src.renderer.music_gen.generate_background_music", new_callable=AsyncMock, return_value="/tmp/bg_music.wav"), \
             patch("src.renderer.tts.generate_tts", new_callable=AsyncMock, return_value="/tmp/tts.mp3"), \
             patch("src.renderer.tts.get_audio_duration", return_value=5.0), \
             patch("src.renderer.audio_mix.prepare_slot_audio", return_value=("/tmp/mixed.mp3", 10.0)), \
             patch("src.cli.commands.html_renderer.render_animated_video", new_callable=AsyncMock, return_value="/tmp/video.mp4"), \
             patch("src.cli.commands.html_renderer.get_video_output_path", return_value="/tmp/video.mp4"):
            result = runner.invoke(cli, [
                "rerender", "--plan-dir", str(plan_dir), "--date", "2026-05-04",
            ])
            assert "Saved music file not found" in result.output

    def test_bg_music_prompt_only(self, runner, tmp_path):
        plan_dir = self._setup(tmp_path, render_config={
            "animate": True, "style_preset": "default",
        })

        with patch("src.renderer.music_gen.calculate_music_duration", return_value=10.0), \
             patch("src.renderer.music_gen.generate_background_music", new_callable=AsyncMock, return_value="/tmp/bg_music.wav"), \
             patch("src.renderer.tts.generate_tts", new_callable=AsyncMock, return_value="/tmp/tts.mp3"), \
             patch("src.renderer.tts.get_audio_duration", return_value=5.0), \
             patch("src.renderer.audio_mix.prepare_slot_audio", return_value=("/tmp/mixed.mp3", 10.0)), \
             patch("src.cli.commands.html_renderer.render_animated_video", new_callable=AsyncMock, return_value="/tmp/video.mp4"), \
             patch("src.cli.commands.html_renderer.get_video_output_path", return_value="/tmp/video.mp4"):
            result = runner.invoke(cli, [
                "rerender", "--plan-dir", str(plan_dir),
                "--date", "2026-05-04", "--bg-music-prompt", "ambient guitar",
            ])
            assert result.exit_code == 0

    def test_auto_music_prompt(self, runner, tmp_path):
        plan_dir = self._setup(tmp_path, render_config={
            "animate": True, "style_preset": "default",
        })

        with patch("src.renderer.music_gen.generate_music_prompt_from_theme", new_callable=AsyncMock, return_value="auto piano") as mock_auto, \
             patch("src.renderer.music_gen.calculate_music_duration", return_value=10.0), \
             patch("src.renderer.music_gen.generate_background_music", new_callable=AsyncMock, return_value="/tmp/bg_music.wav"), \
             patch("src.renderer.tts.generate_tts", new_callable=AsyncMock, return_value="/tmp/tts.mp3"), \
             patch("src.renderer.tts.get_audio_duration", return_value=5.0), \
             patch("src.renderer.audio_mix.prepare_slot_audio", return_value=("/tmp/mixed.mp3", 10.0)), \
             patch("src.cli.commands.html_renderer.render_animated_video", new_callable=AsyncMock, return_value="/tmp/video.mp4"), \
             patch("src.cli.commands.html_renderer.get_video_output_path", return_value="/tmp/video.mp4"):
            result = runner.invoke(cli, [
                "rerender", "--plan-dir", str(plan_dir),
                "--date", "2026-05-04", "--regen-music",
            ])
            assert result.exit_code == 0
            mock_auto.assert_called_once()


class TestRefinePostsEdgeCases:
    def test_refine_render_failure(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "Test",
            "weekly_subthemes": ["W1"], "weekly_subtitles": {"1": "Short"},
            "schedule_summary": [
                {"date": "2026-05-04", "weekday": "Monday", "week_number": 1,
                 "slot_type": "declarative_statement", "subtheme": "W1", "is_automated": True},
            ],
            "render_config": {"style_preset": "default"},
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        (plans_dir / "2026-05_texts.json").write_text(json.dumps({"texts": {"2026-05-04": "Original"}}))

        with patch("src.cli.commands._refine_post_with_ai", new_callable=AsyncMock, return_value="Refined"), \
             patch("src.cli.commands.html_renderer.get_output_path", return_value="/tmp/img.png"), \
             patch("src.cli.commands.html_renderer.render_text_to_image", new_callable=AsyncMock, side_effect=Exception("Render failed")):
            result = runner.invoke(cli, [
                "refine-posts", "--plan-dir", str(tmp_path),
                "--feedback", "2026-05-04::Too generic",
            ], input="1\n")
            assert result.exit_code == 0
            assert "Failed to render" in result.output

    def test_refine_choice_2_refine(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "Test",
            "weekly_subthemes": ["W1"], "weekly_subtitles": {"1": "Short"},
            "schedule_summary": [
                {"date": "2026-05-04", "weekday": "Monday", "week_number": 1,
                 "slot_type": "declarative_statement", "subtheme": "W1", "is_automated": True},
            ],
            "render_config": {"style_preset": "default"},
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        (plans_dir / "2026-05_texts.json").write_text(json.dumps({"texts": {"2026-05-04": "Original"}}))

        with patch("src.cli.commands._refine_post_with_ai", new_callable=AsyncMock, return_value="Refined"), \
             patch("src.cli.commands.html_renderer.get_output_path", return_value="/tmp/img.png"), \
             patch("src.cli.commands.html_renderer.render_text_to_image", new_callable=AsyncMock, return_value="/tmp/img.png"):
            result = runner.invoke(cli, [
                "refine-posts", "--plan-dir", str(tmp_path),
                "--feedback", "2026-05-04::Too generic",
            ], input="2\nshorter\n1\n")
            assert result.exit_code == 0
            assert "Post updated" in result.output


class TestRunAllCommand:
    def test_run_all_animate_implies_audio_and_bg_music(self, runner, tmp_path):
        payload_data = {
            "year": 2026, "month": 2, "monthly_theme": "Test",
            "weekly_subthemes": ["W1", "W2", "W3", "W4"], "week_rule": "monday_determines_month",
            "video_week": "last_week", "style_preset": "default",
        }
        payload_path = tmp_path / "payload.json"
        payload_path.write_text(json.dumps(payload_data))

        with patch("src.cli.commands.generator.check_model_available", new_callable=AsyncMock, return_value=True), \
             patch("src.cli.commands.orchestrator.run_full_pipeline", new_callable=AsyncMock, return_value={
                 "rendered_images": ["/tmp/video.mp4"], "plan_path": "/tmp/plan.json",
                 "texts_path": "/tmp/texts.json",
             }) as mock_pipeline:
            result = runner.invoke(cli, [
                "run-all", "--payload", str(payload_path), "--animate",
                "--skip-text",
            ])
            assert result.exit_code == 0
            call_kwargs = mock_pipeline.call_args[1]
            assert call_kwargs["animate"] is True
            assert call_kwargs["bg_music"] is True
            assert "Rendered videos" in result.output


class TestRerenderCommand:
    def _make_plan_dir(self, tmp_path, *, with_music=False, with_animate=True):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        render_config = {"style_preset": "default"}
        if with_animate:
            render_config["animate"] = True
        if with_music:
            render_config["bg_music"] = True
            render_config["bg_music_prompt"] = "piano"
            render_config["bg_music_path"] = str(tmp_path / "audio" / "bg_music.wav")
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "Test",
            "weekly_subthemes": ["W1"],
            "schedule_summary": [
                {"date": "2026-05-04", "weekday": "Monday", "week_number": 1,
                 "slot_type": "declarative_statement", "subtheme": "W1", "is_automated": True},
            ],
            "render_config": render_config,
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        texts_data = {"texts": {"2026-05-04": "Generated text"}}
        (plans_dir / "2026-05_texts.json").write_text(json.dumps(texts_data))
        if with_music:
            audio_dir = tmp_path / "audio"
            audio_dir.mkdir(parents=True, exist_ok=True)
            (audio_dir / "bg_music.wav").write_bytes(b"fake")
        return tmp_path

    def test_rerender_no_plan_files(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()

        result = runner.invoke(cli, [
            "rerender", "--plan-dir", str(tmp_path), "--all",
        ])
        assert result.exit_code != 0
        assert "No plan file" in result.output

    def test_rerender_no_texts_files(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        (plans_dir / "2026-05_plan.json").write_text("{}")

        result = runner.invoke(cli, [
            "rerender", "--plan-dir", str(tmp_path), "--all",
        ])
        assert result.exit_code != 0
        assert "No texts file" in result.output

    def test_rerender_neither_date_nor_all(self, runner, tmp_path):
        self._make_plan_dir(tmp_path)

        result = runner.invoke(cli, [
            "rerender", "--plan-dir", str(tmp_path),
        ])
        assert result.exit_code != 0
        assert "Must specify --date or --all" in result.output

    def test_rerender_missing_date_in_plan(self, runner, tmp_path):
        self._make_plan_dir(tmp_path)

        result = runner.invoke(cli, [
            "rerender", "--plan-dir", str(tmp_path),
            "--date", "2026-05-20",
        ])
        # Date not in schedule, so no slot found - command completes but skips
        assert "No slot found" in result.output or "No text" in result.output or result.exit_code == 0

    def test_rerender_static_image(self, runner, tmp_path):
        plan_dir = self._make_plan_dir(tmp_path, with_animate=False)

        with patch("src.cli.commands.html_renderer.render_text_to_image", new_callable=AsyncMock, return_value="/tmp/img.png") as mock_render, \
             patch("src.cli.commands.html_renderer.get_output_path", return_value="/tmp/img.png"):
            result = runner.invoke(cli, [
                "rerender", "--plan-dir", str(plan_dir),
                "--date", "2026-05-04",
            ])
            assert result.exit_code == 0
            mock_render.assert_called_once()

    def test_rerender_animate_video(self, runner, tmp_path):
        plan_dir = self._make_plan_dir(tmp_path, with_animate=True)

        with patch("src.cli.commands.html_renderer.render_animated_video", new_callable=AsyncMock, return_value="/tmp/video.mp4") as mock_render, \
             patch("src.cli.commands.html_renderer.get_video_output_path", return_value="/tmp/video.mp4"):
            result = runner.invoke(cli, [
                "rerender", "--plan-dir", str(plan_dir),
                "--date", "2026-05-04",
            ])
            assert result.exit_code == 0
            mock_render.assert_called_once()

    def test_rerender_all_flag(self, runner, tmp_path):
        plan_dir = self._make_plan_dir(tmp_path, with_animate=True)

        with patch("src.cli.commands.html_renderer.render_animated_video", new_callable=AsyncMock, return_value="/tmp/video.mp4") as mock_render, \
             patch("src.cli.commands.html_renderer.get_video_output_path", return_value="/tmp/video.mp4"):
            result = runner.invoke(cli, [
                "rerender", "--plan-dir", str(plan_dir),
                "--all",
            ])
            assert result.exit_code == 0
            mock_render.assert_called_once()

    def test_rerender_year_month_filter(self, runner, tmp_path):
        plan_dir = self._make_plan_dir(tmp_path)

        with patch("src.cli.commands.html_renderer.render_animated_video", new_callable=AsyncMock, return_value="/tmp/video.mp4"), \
             patch("src.cli.commands.html_renderer.get_video_output_path", return_value="/tmp/video.mp4"):
            result = runner.invoke(cli, [
                "rerender", "--plan-dir", str(plan_dir),
                "--year", "2026", "--month", "5", "--all",
            ])
            assert result.exit_code == 0

    def test_rerender_year_month_not_found(self, runner, tmp_path):
        self._make_plan_dir(tmp_path)

        result = runner.invoke(cli, [
            "rerender", "--plan-dir", str(tmp_path),
            "--year", "2027", "--month", "1", "--all",
        ])
        assert result.exit_code != 0

    def test_rerender_missing_text_warns(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "Test",
            "weekly_subthemes": ["W1"],
            "schedule_summary": [
                {"date": "2026-05-04", "weekday": "Monday", "week_number": 1,
                 "slot_type": "declarative_statement", "subtheme": "W1", "is_automated": True},
            ],
            "render_config": {"animate": True, "style_preset": "default"},
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        (plans_dir / "2026-05_texts.json").write_text(json.dumps({"texts": {}}))

        result = runner.invoke(cli, [
            "rerender", "--plan-dir", str(tmp_path),
            "--date", "2026-05-04",
        ])
        assert "No text for" in result.output

    def test_rerender_with_bg_music(self, runner, tmp_path):
        plan_dir = self._make_plan_dir(tmp_path, with_music=True, with_animate=True)

        with patch("src.cli.commands.html_renderer.render_animated_video", new_callable=AsyncMock, return_value="/tmp/video.mp4") as mock_render, \
             patch("src.cli.commands.html_renderer.get_video_output_path", return_value="/tmp/video.mp4"), \
             patch("src.renderer.tts.generate_tts", new_callable=AsyncMock, return_value="/tmp/tts.mp3"), \
             patch("src.renderer.tts.get_audio_duration", return_value=5.0), \
             patch("src.renderer.audio_mix.prepare_slot_audio", return_value=("/tmp/mixed.mp3", 10.0)):
            result = runner.invoke(cli, [
                "rerender", "--plan-dir", str(plan_dir),
                "--date", "2026-05-04",
            ])
            assert result.exit_code == 0
            mock_render.assert_called_once()
            assert mock_render.call_args[1]["audio_path"] is not None


class TestRefinePostsCommand:
    def test_refine_invalid_feedback(self, runner, tmp_path):
        result = runner.invoke(cli, [
            "refine-posts", "--plan-dir", str(tmp_path),
            "--feedback", "invalid-no-separator",
        ])
        assert result.exit_code != 0

    def test_refine_no_plan_files(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()

        result = runner.invoke(cli, [
            "refine-posts", "--plan-dir", str(tmp_path),
            "--feedback", "2026-05-04::Too generic",
        ])
        assert result.exit_code != 0
        assert "No plan file" in result.output

    def test_refine_no_texts_files(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        (plans_dir / "2026-05_plan.json").write_text("{}")

        result = runner.invoke(cli, [
            "refine-posts", "--plan-dir", str(tmp_path),
            "--feedback", "2026-05-04::Too generic",
        ])
        assert result.exit_code != 0
        assert "No texts file" in result.output

    def _make_refine_dir(self, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "Test",
            "weekly_subthemes": ["W1"], "weekly_subtitles": {"1": "Short"},
            "schedule_summary": [
                {"date": "2026-05-04", "weekday": "Monday", "week_number": 1,
                 "slot_type": "declarative_statement", "subtheme": "W1", "is_automated": True},
            ],
            "render_config": {"style_preset": "default"},
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        texts_data = {"texts": {"2026-05-04": "Original post text"}}
        (plans_dir / "2026-05_texts.json").write_text(json.dumps(texts_data))
        return tmp_path

    def test_refine_accept(self, runner, tmp_path):
        plan_dir = self._make_refine_dir(tmp_path)

        with patch("src.cli.commands._refine_post_with_ai", new_callable=AsyncMock, return_value="Refined post"), \
             patch("src.cli.commands.html_renderer.get_output_path", return_value="/tmp/img.png"), \
             patch("src.cli.commands.html_renderer.render_text_to_image", new_callable=AsyncMock, return_value="/tmp/img.png"):
            result = runner.invoke(cli, [
                "refine-posts", "--plan-dir", str(plan_dir),
                "--feedback", "2026-05-04::Too generic",
            ], input="1\n")
            assert result.exit_code == 0
            assert "Post updated" in result.output
            texts = json.loads((plan_dir / "plans" / "2026-05_texts.json").read_text())
            assert texts["texts"]["2026-05-04"] == "Refined post"

    def test_refine_skip(self, runner, tmp_path):
        plan_dir = self._make_refine_dir(tmp_path)

        with patch("src.cli.commands._refine_post_with_ai", new_callable=AsyncMock, return_value="Refined"):
            result = runner.invoke(cli, [
                "refine-posts", "--plan-dir", str(plan_dir),
                "--feedback", "2026-05-04::Too generic",
            ], input="3\n")
            assert result.exit_code == 0
            assert "Skipped" in result.output

    def test_refine_exit_early(self, runner, tmp_path):
        plan_dir = self._make_refine_dir(tmp_path)

        with patch("src.cli.commands._refine_post_with_ai", new_callable=AsyncMock, return_value="Refined"):
            result = runner.invoke(cli, [
                "refine-posts", "--plan-dir", str(plan_dir),
                "--feedback", "2026-05-04::Too generic",
            ], input="4\n")
            assert result.exit_code == 0
            assert "Exited early" in result.output

    def test_refine_date_not_in_texts(self, runner, tmp_path):
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir()
        plan_data = {
            "year": 2026, "month": 5, "monthly_theme": "Test",
            "weekly_subthemes": ["W1"],
            "schedule_summary": [
                {"date": "2026-05-04", "weekday": "Monday", "week_number": 1,
                 "slot_type": "declarative_statement", "subtheme": "W1", "is_automated": True},
            ],
            "render_config": {"style_preset": "default"},
        }
        (plans_dir / "2026-05_plan.json").write_text(json.dumps(plan_data))
        (plans_dir / "2026-05_texts.json").write_text(json.dumps({"texts": {}}))

        result = runner.invoke(cli, [
            "refine-posts", "--plan-dir", str(tmp_path),
            "--feedback", "2026-05-04::Too generic",
        ])
        assert result.exit_code == 0
        assert "No post found" in result.output or "skipping" in result.output

    def test_refine_ai_failure(self, runner, tmp_path):
        plan_dir = self._make_refine_dir(tmp_path)

        with patch("src.cli.commands._refine_post_with_ai", new_callable=AsyncMock, side_effect=Exception("AI error")):
            result = runner.invoke(cli, [
                "refine-posts", "--plan-dir", str(plan_dir),
                "--feedback", "2026-05-04::Too generic",
            ])
            assert result.exit_code == 0
            assert "AI refinement failed" in result.output
