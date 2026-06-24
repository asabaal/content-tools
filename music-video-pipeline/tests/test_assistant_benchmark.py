from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from assistant.flash_music_video_benchmark import (
    BENCHMARK_DIR,
    REPO_ROOT,
    ZAIAPIRunner,
    build_evidence_bundle,
    prepare_fixtures,
    run_case,
    CONFIRMED_SCRIPT_FIELDS,
)
from assistant.flash_music_video_validation import (
    check_required_keys,
    check_run_metadata,
    parse_response_json,
    redact_api_keys,
    validate_candidate_patch_fields,
    validate_no_api_key_leak,
    validate_source_evidence_paths,
)


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def temp_source(tmp_path: Path) -> Path:
    src = tmp_path / "source_data"
    src.mkdir()
    for fname in ["lyrics_synced.json", "analysis.json", "mvp_project.json", "script.json"]:
        _write_json(src / fname, {"test": fname, "data": True})
    _write_json(src / "ingest.json", {"should": "not", "be": "copied"})
    _write_json(src / "lyrics_raw.json", {"should": "not", "be": "copied"})
    return src


class TestFixturePreparation:
    def test_copies_only_allowlist(self, temp_source: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("assistant.flash_music_video_benchmark.BENCHMARK_DIR", temp_source.parent / "benchmark")
        fixture_dir = prepare_fixtures(str(temp_source))
        manifest = json.loads((fixture_dir / "manifest.json").read_text())
        copied = {f["file"] for f in manifest["copied_files"]}
        assert "lyrics_synced.json" in copied
        assert "analysis.json" in copied
        assert "mvp_project.json" in copied
        assert "script.json" in copied
        assert "ingest.json" not in copied
        assert "lyrics_raw.json" not in copied

    def test_generates_manifest(self, temp_source: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("assistant.flash_music_video_benchmark.BENCHMARK_DIR", temp_source.parent / "benchmark2")
        fixture_dir = prepare_fixtures(str(temp_source))
        manifest = json.loads((fixture_dir / "manifest.json").read_text())
        assert "source_path" in manifest
        assert "copied_files" in manifest
        assert "copy_timestamp" in manifest
        assert manifest["usage_policy"].startswith("This fixture is read-only")
        for f in manifest["copied_files"]:
            assert "file" in f
            assert "sha256" in f
            assert "size_bytes" in f

    def test_never_writes_to_source(self, temp_source: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        original_manifest = temp_source / "manifest.json"
        monkeypatch.setattr("assistant.flash_music_video_benchmark.BENCHMARK_DIR", temp_source.parent / "benchmark3")
        prepare_fixtures(str(temp_source))
        assert not original_manifest.exists()

    def test_fails_on_missing_source(self) -> None:
        with pytest.raises(FileNotFoundError):
            prepare_fixtures("/nonexistent/path")

    def test_fails_on_no_allowed_files(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty_data"
        empty.mkdir()
        _write_json(empty / "something_else.json", {"a": 1})
        with pytest.raises(RuntimeError, match="No allowed JSON files"):
            prepare_fixtures(str(empty))

    def test_is_idempotent(self, temp_source: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("assistant.flash_music_video_benchmark.BENCHMARK_DIR", temp_source.parent / "benchmark4")
        first = prepare_fixtures(str(temp_source))
        second = prepare_fixtures(str(temp_source))
        # Compare copied file digests, not timestamps
        m1 = json.loads((first / "manifest.json").read_text())
        m2 = json.loads((second / "manifest.json").read_text())
        f1 = {f["file"]: f["sha256"] for f in m1["copied_files"]}
        f2 = {f["file"]: f["sha256"] for f in m2["copied_files"]}
        assert f1 == f2


class TestEvidenceBundle:
    def test_manifest_is_deterministic(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("assistant.flash_music_video_benchmark.BENCHMARK_DIR", BENCHMARK_DIR)
        m1 = build_evidence_bundle()
        m2 = build_evidence_bundle()
        assert m1["all_manifest_paths"] == m2["all_manifest_paths"]

    def test_includes_source_categories(self) -> None:
        assert "source_code" in m_includes
        assert "templates" in m_includes
        assert "tests" in m_includes

    def test_each_entry_has_sha256(self) -> None:
        for cat in ("source_code", "templates", "tests"):
            for entry in m_includes[cat]:
                assert "sha256" in entry
                assert len(entry["sha256"]) == 64


m_includes = build_evidence_bundle().get("includes", {})


class TestValidation:
    def test_parse_valid_json(self) -> None:
        result = parse_response_json('{"a": 1}')
        assert result == {"a": 1}

    def test_parse_json_from_code_block(self) -> None:
        result = parse_response_json("```json\n{\"a\": 1}\n```")
        assert result == {"a": 1}

    def test_parse_invalid_json_raises(self) -> None:
        with pytest.raises(ValueError, match="not valid JSON"):
            parse_response_json("{invalid}")

    def test_check_required_keys_present(self) -> None:
        errors = check_required_keys({"a": 1, "b": 2}, ["a", "b"])
        assert errors == []

    def test_check_required_keys_missing(self) -> None:
        errors = check_required_keys({"a": 1}, ["a", "b"])
        assert any("b" in e for e in errors)

    def test_validate_evidence_paths_rejects_nonexistent(self) -> None:
        data = {
            "pipeline_stages": [
                {
                    "stage": "test",
                    "status": "confirmed",
                    "source_evidence": [{"path": "nonexistent.py", "claim": "test"}],
                }
            ]
        }
        errors = validate_source_evidence_paths(data, {"real.py", "other.py"})
        assert any("nonexistent.py" in e for e in errors)

    def test_validate_evidence_paths_passes_valid(self) -> None:
        data = {
            "pipeline_stages": [
                {
                    "stage": "test",
                    "status": "confirmed",
                    "source_evidence": [{"path": "real.py", "claim": "test"}],
                }
            ]
        }
        errors = validate_source_evidence_paths(data, {"real.py"})
        assert errors == []

    def test_unsupported_candidate_field_rejected(self) -> None:
        data = {
            "candidate_patches": [
                {
                    "brief_id": "restrained_testimony",
                    "patch": {"quantum_fluctuation_field": 42},
                    "field_rationales": [],
                }
            ]
        }
        errors = validate_candidate_patch_fields(data, CONFIRMED_SCRIPT_FIELDS)
        assert any("quantum_fluctuation_field" in e for e in errors)

    def test_valid_candidate_field_passes(self) -> None:
        data = {
            "candidate_patches": [
                {
                    "brief_id": "restrained_testimony",
                    "patch": {"background_type": "solid", "font_size": 100},
                    "field_rationales": [],
                }
            ]
        }
        errors = validate_candidate_patch_fields(data, CONFIRMED_SCRIPT_FIELDS)
        assert errors == []

    def test_check_run_metadata_complete(self) -> None:
        meta = {
            "model": "glm-4.7-flash",
            "case_name": "test",
            "attempt": 1,
            "timestamp": "now",
            "http_status": 200,
        }
        assert check_run_metadata(meta) == []

    def test_check_run_metadata_incomplete(self) -> None:
        assert check_run_metadata({"model": "test"}) != []

    def test_api_key_redaction(self) -> None:
        text = 'Authorization: Bearer sk-my-secret-key-12345'
        result = redact_api_keys(text)
        assert "sk-my-secret-key-12345" not in result
        assert "[REDACTED]" in result

    def test_api_key_leak_detection(self) -> None:
        text = 'export ZAI_API_KEY="my-secret"'
        leaks = validate_no_api_key_leak(text)
        assert len(leaks) > 0

    def test_no_false_positive_leak(self) -> None:
        text = "this is clean text with no keys"
        assert validate_no_api_key_leak(text) == []


class TestSampleValidation:
    """Tests that a structurally valid sample output passes validation."""

    SAMPLE = {
        "pipeline_stages": [
            {
                "stage": "Audio Analysis",
                "input_artifacts": ["audio.wav"],
                "output_artifacts": ["analysis.json"],
                "source_evidence": [
                    {
                        "path": "src/audio/analyzer.py",
                        "symbol_or_line_range": "AudioAnalyzer.analyze",
                        "claim": "Audio analysis produces rms_energy and spectral_centroids",
                    }
                ],
                "status": "confirmed",
            }
        ],
        "unresolved_questions": ["How are font fallback paths resolved on non-Linux systems?"],
    }

    def test_parseable(self) -> None:
        text = json.dumps(self.SAMPLE)
        parsed = parse_response_json(text)
        assert parsed["pipeline_stages"][0]["stage"] == "Audio Analysis"

    def test_required_keys(self) -> None:
        errors = check_required_keys(self.SAMPLE, ["pipeline_stages", "unresolved_questions"])
        assert errors == []

    def test_status_values(self) -> None:
        for stage in self.SAMPLE["pipeline_stages"]:
            assert stage["status"] in {"confirmed", "inference", "unknown"}


class TestDryRun:
    def test_dry_run_makes_no_network_request(self) -> None:
        runner = ZAIAPIRunner(api_key="test-key")
        result = runner.call(
            messages=[{"role": "user", "content": "hello"}],
            case_name="test",
            attempt=1,
            dry_run=True,
        )
        assert result["dry_run"] is True
        assert "payload_summary" in result
        ps = result["payload_summary"]
        assert ps["model"] == "glm-4.7-flash"
        assert ps["message_count"] == 1

    def test_dry_run_redacts_auth_header(self) -> None:
        runner = ZAIAPIRunner(api_key="secret-123")
        result = runner.call(
            messages=[{"role": "user", "content": "hi"}],
            dry_run=True,
        )
        auth = result["payload_summary"]["headers"].get("Authorization", "")
        assert "secret-123" not in auth


class TestAPIRunner:
    def test_requires_api_key_for_live(self) -> None:
        runner = ZAIAPIRunner(api_key="")
        result = runner.call(
            messages=[{"role": "user", "content": "test"}],
            dry_run=False,
        )
        assert not result["dry_run"]
        assert result.get("error") is not None  # will fail because no real key

    def test_retry_logs_error_info(self) -> None:
        runner = ZAIAPIRunner(api_key="fake-key", base_url="https://nonexistent.example.com/api", max_retries=1)
        result = runner.call(
            messages=[{"role": "user", "content": "test"}],
            dry_run=False,
        )
        assert result.get("error") is not None


class TestIntegrationWithMocks:
    def test_run_case_dry_returns_summary(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("assistant.flash_music_video_benchmark.BENCHMARK_DIR", BENCHMARK_DIR)
        runner = ZAIAPIRunner(api_key="test-key")
        results = run_case("system_discovery", runner, attempts=1, dry_run=True)
        assert len(results) == 1
        assert results[0]["dry_run"] is True
        assert results[0]["payload_summary"]["case_name"] == "system_discovery"
