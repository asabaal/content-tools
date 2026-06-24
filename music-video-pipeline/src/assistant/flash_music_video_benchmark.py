from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .flash_music_video_validation import (
    check_run_metadata,
    parse_response_json,
    redact_api_keys,
    validate_candidate_patch_fields,
    validate_no_api_key_leak,
    validate_source_evidence_paths,
)

BENCHMARK_DIR = Path(__file__).resolve().parent.parent.parent / "benchmarks" / "glm47flash_music_video_v0"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

ALLOWED_FIXTURE_FILES = {
    "lyrics_synced.json",
    "analysis.json",
    "mvp_project.json",
    "script.json",
    "script_16x9.json",
    "script_9x16.json",
    "script_bare.json",
}

FIXTURE_SOURCE_REL = "../projects/prophetic-preprint/projects/ai-psalm-9/data"

DEFAULT_ENDPOINT = "https://api.z.ai/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4.7-flash"

CASE_NAMES = ["system_discovery", "feature_ledger", "candidate_section_patches", "safe_boundary"]

CONFIRMED_SCRIPT_FIELDS = {
    "background_type", "background_color", "gradient_colors", "gradient_direction",
    "texture_type", "texture_opacity", "texture_blend_mode",
    "font_size", "font_family",
    "animation_type", "animation_speed",
    "reveal_mode", "reveal_words", "reveal_slide",
    "reactivity",
    "text_position", "text_style", "text_style_colors",
    "text_color", "text_auto_contrast",
    "bg_animation_preset",
    "text_backdrop", "text_backdrop_color", "text_backdrop_opacity",
    "text_backdrop_padding", "text_backdrop_radius",
    "text_align", "text_shadow", "outline",
    "highlight_color", "letter_spacing",
    "background_image", "background_image_opacity", "background_image_fit",
    "gradient_params",
    "y", "x", "font_size_delta",
    "canvas",
    "background_video",
    "name", "type", "lines",
    "lines_overrides", "words_overrides",
    "visual", "defaults", "caption_style",
    "intro", "outro",
    "image", "title", "subtitle", "duration", "text", "logo",
    "_aspect_meta",
}


def _sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    h.update(filepath.read_bytes())
    return h.hexdigest()


def _load_case_def(case_name: str) -> dict:
    case_path = BENCHMARK_DIR / "cases" / f"{case_name}.json"
    if not case_path.exists():
        raise FileNotFoundError(f"Case definition not found: {case_path}")
    return json.loads(case_path.read_text(encoding="utf-8"))


def _load_prompt(case_name: str) -> str:
    prompt_path = BENCHMARK_DIR / "prompts" / f"{case_name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def _load_fixture(fixture_dir: Path) -> dict[str, dict]:
    result = {}
    for fname in ALLOWED_FIXTURE_FILES:
        fp = fixture_dir / fname
        if fp.exists():
            result[fname] = json.loads(fp.read_text(encoding="utf-8"))
    return result


def _load_evidence_manifest() -> dict:
    manifest_path = BENCHMARK_DIR / "evidence_manifest.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {}


CONFIRMED_FIXTURE_FILES_SORTED = sorted(ALLOWED_FIXTURE_FILES)


def prepare_fixtures(source_dir: str | None = None) -> Path:
    if source_dir is None:
        source_dir = str((REPO_ROOT / FIXTURE_SOURCE_REL).resolve())
    source = Path(source_dir).resolve()
    if not source.exists():
        raise FileNotFoundError(f"Fixture source path does not exist: {source}")
    if not source.is_dir():
        raise NotADirectoryError(f"Fixture source is not a directory: {source}")

    fixture_dir = BENCHMARK_DIR / "fixture" / "ai_psalm_9"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    copied_files: list[dict] = []
    for fname in ALLOWED_FIXTURE_FILES:
        src = source / fname
        if src.exists() and src.is_file() and src.suffix == ".json":
            dst = fixture_dir / fname
            shutil.copy2(str(src), str(dst))
            copied_files.append({
                "file": fname,
                "sha256": _sha256(dst),
                "size_bytes": dst.stat().st_size,
            })

    if not copied_files:
        raise RuntimeError(f"No allowed JSON files found in {source}")

    try:
        source_rel = str(source.relative_to(REPO_ROOT))
    except ValueError:
        source_rel = str(source)

    manifest = {
        "benchmark": "GLM-4.7-Flash Music Video Scripting Benchmark v0",
        "fixture_name": "ai_psalm_9",
        "source_path": source_rel,
        "description": "Read-only fixture derived from AI Psalm 9 project data",
        "usage_policy": "This fixture is read-only and derived from AI Psalm 9. Do not modify.",
        "copied_files": copied_files,
        "copy_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path = fixture_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return fixture_dir


def build_evidence_bundle() -> dict:
    src_root = REPO_ROOT / "src"
    templates_dir = REPO_ROOT / "templates"
    fixture_dir = BENCHMARK_DIR / "fixture" / "ai_psalm_9"

    evidence_files: dict[str, list[str]] = {
        "source_code": [
            "src/scriptgen/generator.py",
            "src/scriptgen/rules.py",
            "src/scriptgen/moods.py",
            "src/scriptgen/palette.py",
            "src/scriptgen/color_presets.py",
            "src/render/renderer.py",
            "src/render/aspect_transform.py",
            "src/render/effect_presets.py",
            "src/render/animations.py",
            "src/render/audio_reactive.py",
            "src/render/frame_effects.py",
            "src/render/gradients.py",
            "src/render/text_styles.py",
            "src/render/font_styles.py",
            "src/render/encoder.py",
            "src/pipeline/models.py",
            "src/canvas/models.py",
            "src/canvas/renderer.py",
            "src/canvas/geometry.py",
            "src/canvas/motion.py",
            "src/canvas/lights.py",
            "src/canvas/compositing.py",
            "src/canvas/repetition.py",
            "src/canvas/text_safety.py",
            "src/audio/analyzer.py",
            "src/audio/features.py",
            "src/lyrics/parser.py",
            "src/lyrics/synchronizer.py",
            "scripts/apply_profile.py",
        ],
        "templates": [
            "templates/default.json",
            "templates/dynamic.json",
            "templates/elegant.json",
            "templates/energetic.json",
            "templates/extreme.json",
            "templates/modern.json",
        ],
        "tests": [
            "tests/test_generator.py",
            "tests/test_models.py",
            "tests/test_rules.py",
            "tests/test_canvas_models.py",
            "tests/test_canvas_renderer.py",
            "tests/test_aspect_transform.py",
            "tests/test_render.py",
        ],
    }

    includes: dict[str, list[dict]] = {"source_code": [], "templates": [], "tests": [], "fixtures": []}
    all_manifest_paths: set[str] = set()

    all_raw: list[dict] = []

    for category, rel_paths in evidence_files.items():
        for rel_path in rel_paths:
            full = (REPO_ROOT / rel_path).resolve()
            if full.exists():
                content = full.read_text(encoding="utf-8")
                digest = hashlib.sha256(content.encode()).hexdigest()
                entry = {
                    "path": rel_path,
                    "size_bytes": full.stat().st_size,
                    "sha256": digest,
                }
                includes[category].append(entry)
                all_manifest_paths.add(rel_path)
                all_raw.append({"path": rel_path, "content": content})
            else:
                all_raw.append({"path": rel_path, "content": f"/* FILE NOT FOUND: {full} */"})

    for fname in sorted(ALLOWED_FIXTURE_FILES):
        fp = fixture_dir / fname
        if fp.exists():
            content = fp.read_text(encoding="utf-8")
            digest = hashlib.sha256(content.encode()).hexdigest()
            rel = f"benchmarks/glm47flash_music_video_v0/fixture/ai_psalm_9/{fname}"
            entry = {
                "path": rel,
                "size_bytes": fp.stat().st_size,
                "sha256": digest,
            }
            includes["fixtures"].append(entry)
            all_manifest_paths.add(rel)
            all_manifest_paths.add(fname)
            all_raw.append({"path": rel, "content": content})

    manifest = {
        "benchmark": "GLM-4.7-Flash Music Video Scripting Benchmark v0",
        "evidence_bundle_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "includes": includes,
        "all_manifest_paths": sorted(all_manifest_paths),
        "unresolved_areas": [
            "Canvas geometry/motion/lights may produce visual output not fully describable by script fields alone",
            "Color preset system (color_presets.py) modifies multiple fields; interactions are complex",
            "Some template values may not be consumed by current renderer (e.g., unused template keys)",
            "Audio reactivity behavior depends on runtime energy data, not script-level guarantees",
        ],
    }

    manifest_path = BENCHMARK_DIR / "evidence_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


class ZAIAPIRunner:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_ENDPOINT,
        timeout: int = 120,
        max_retries: int = 3,
        api_key: str | None = None,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.api_key = api_key or os.environ.get("ZAI_API_KEY", "")

    def call(
        self,
        messages: list[dict],
        case_name: str = "",
        attempt: int = 1,
        dry_run: bool = False,
    ) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 16384,
        }

        if dry_run:
            safe_headers = {k: "[REDACTED]" if k == "Authorization" else v for k, v in headers.items()}
            payload["_dry_run"] = True
            return {
                "dry_run": True,
                "payload_summary": {
                    "url": self.base_url,
                    "headers": safe_headers,
                    "payload_keys": list(payload.keys()),
                    "model": self.model,
                    "message_count": len(messages),
                    "case_name": case_name,
                    "attempt": attempt,
                    "thinking_enabled": False,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        last_error: Exception | None = None
        for retry in range(self.max_retries):
            try:
                body = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    self.base_url,
                    data=body,
                    headers=headers,
                    method="POST",
                )
                t0 = time.time()
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                elapsed = time.time() - t0
                http_status = resp.status

                parsed = json.loads(raw)
                raw_content = parsed["choices"][0]["message"]["content"]

                usage = parsed.get("usage", {})
                parsed_output = None
                parse_error = None
                try:
                    parsed_output = parse_response_json(raw_content)
                except ValueError as e:
                    parse_error = str(e)

                redacted_raw = redact_api_keys(raw)
                api_leaks = validate_no_api_key_leak(raw)

                return {
                    "dry_run": False,
                    "model": self.model,
                    "case_name": case_name,
                    "attempt": attempt,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "http_status": http_status,
                    "elapsed_seconds": round(elapsed, 3),
                    "usage": {
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    },
                    "thinking_enabled": False,
                    "raw_response_json": parsed if isinstance(parsed, dict) else {},
                    "raw_content": redacted_raw,
                    "parsed_output": parsed_output,
                    "parse_error": parse_error,
                    "api_key_leaks": api_leaks,
                    "error": None,
                }
            except urllib.error.HTTPError as e:
                last_error = e
                error_body = e.read().decode("utf-8", errors="replace")
                if retry < self.max_retries - 1 and e.code >= 500:
                    time.sleep(2 ** retry)
                    continue
                return {
                    "dry_run": False,
                    "model": self.model,
                    "case_name": case_name,
                    "attempt": attempt,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "http_status": e.code,
                    "elapsed_seconds": 0.0,
                    "usage": {},
                    "thinking_enabled": False,
                    "raw_response_json": {},
                    "raw_content": "",
                    "parsed_output": None,
                    "parse_error": None,
                    "api_key_leaks": [],
                    "error": f"HTTP {e.code}: {error_body[:500]}",
                }
            except Exception as e:
                last_error = e
                if retry < self.max_retries - 1:
                    time.sleep(2 ** retry)
                    continue
                return {
                    "dry_run": False,
                    "model": self.model,
                    "case_name": case_name,
                    "attempt": attempt,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "http_status": 0,
                    "elapsed_seconds": 0.0,
                    "usage": {},
                    "thinking_enabled": False,
                    "raw_response_json": {},
                    "raw_content": "",
                    "parsed_output": None,
                    "parse_error": None,
                    "api_key_leaks": [],
                    "error": f"{type(last_error).__name__}: {last_error}",
                }
        return {
            "dry_run": False,
            "model": self.model,
            "case_name": case_name,
            "attempt": attempt,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "http_status": 0,
            "elapsed_seconds": 0.0,
            "usage": {},
            "thinking_enabled": False,
            "raw_response_json": {},
            "raw_content": "",
            "parsed_output": None,
            "parse_error": None,
            "api_key_leaks": [],
            "error": f"Exhausted retries: {last_error}",
        }


def run_case(
    case_name: str,
    runner: ZAIAPIRunner,
    attempts: int = 3,
    output_dir: Path | None = None,
    dry_run: bool = False,
) -> list[dict]:
    if case_name not in CASE_NAMES:
        raise ValueError(f"Unknown case '{case_name}'. Choose from: {CASE_NAMES}")

    case_def = _load_case_def(case_name)
    prompt_text = _load_prompt(case_name)
    evidence = _load_evidence_manifest()
    fixture_dir = BENCHMARK_DIR / "fixture" / "ai_psalm_9"
    fixtures = _load_fixture(fixture_dir)

    MAX_FIXTURE_SIZE = 12000
    fixture_block = []
    fixture_summary = []

    for fname in sorted(ALLOWED_FIXTURE_FILES):
        if fname in fixtures:
            data = fixtures[fname]
            top_keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
            fixture_summary.append(f"  {fname}: top-level keys={top_keys}, {len(json.dumps(data))} bytes")

    fixture_block.append("### Fixture Summary (AI Psalm 9)\n" + "\n".join(fixture_summary))

    for fname in sorted(ALLOWED_FIXTURE_FILES):
        if fname in fixtures:
            data = fixtures[fname]
            data_str = json.dumps(data, indent=2)
            if len(data_str) > MAX_FIXTURE_SIZE:
                truncated = data_str[:MAX_FIXTURE_SIZE]
                fixture_block.append(
                    f"### {fname} (truncated, {len(data_str)} bytes)\n"
                    f"```json\n{truncated}\n... [truncated]\n```"
                )
            else:
                fixture_block.append(f"### {fname}\n```json\n{data_str}\n```")

    system_prompt = case_def.get("system_prompt", "")
    user_prompt = prompt_text

    if "{{EVIDENCE_MANIFEST}}" in user_prompt:
        manifest_summary = json.dumps(evidence.get("all_manifest_paths", []), indent=2)
        user_prompt = user_prompt.replace("{{EVIDENCE_MANIFEST}}", manifest_summary)

    if "{{FIXTURE_DATA}}" in user_prompt:
        user_prompt = user_prompt.replace("{{FIXTURE_DATA}}", "\n\n".join(fixture_block))

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    results: list[dict] = []
    for attempt in range(1, attempts + 1):
        result = runner.call(messages, case_name=case_name, attempt=attempt, dry_run=dry_run)
        results.append(result)

        if output_dir:
            case_dir = output_dir / case_name
            case_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            attempt_file = case_dir / f"attempt_{attempt}_{ts}.json"
            safe = {k: v for k, v in result.items() if k != "api_key"}
            safe["raw_content"] = redact_api_keys(safe.get("raw_content", ""))
            if "raw_response_json" in safe:
                safe["raw_response_json"] = redact_api_keys(json.dumps(safe["raw_response_json"]))
                try:
                    safe["raw_response_json"] = json.loads(safe["raw_response_json"])
                except (json.JSONDecodeError, TypeError):
                    pass
            attempt_file.write_text(json.dumps(safe, indent=2, ensure_ascii=False), encoding="utf-8")

    return results


def _validate_results(results: list[dict]) -> list[str]:
    errors: list[str] = []
    for result in results:
        if result.get("dry_run"):
            continue
        meta_errors = check_run_metadata(result)
        errors.extend(meta_errors)

        leak_errors = validate_no_api_key_leak(result.get("raw_content", ""))
        errors.extend(f"API key leak: {e}" for e in leak_errors)

        parsed = result.get("parsed_output")
        if parsed is None:
            parse_err = result.get("parse_error")
            if parse_err:
                errors.append(f"Attempt {result.get('attempt')}: parse error - {parse_err}")
            continue

        manifest = _load_evidence_manifest()
        manifest_paths = set(manifest.get("all_manifest_paths", []))

        path_errors = validate_source_evidence_paths(parsed, manifest_paths)
        errors.extend(f"Attempt {result.get('attempt')}: {e}" for e in path_errors)

        case_name = result.get("case_name", "")
        if case_name == "candidate_section_patches":
            field_errors = validate_candidate_patch_fields(parsed, CONFIRMED_SCRIPT_FIELDS)
            errors.extend(f"Attempt {result.get('attempt')}: {e}" for e in field_errors)

        if case_name == "system_discovery":
            from .flash_music_video_validation import check_required_keys
            key_errors = check_required_keys(parsed, ["pipeline_stages", "unresolved_questions"])
            errors.extend(f"Attempt {result.get('attempt')}: {e}" for e in key_errors)
        elif case_name == "feature_ledger":
            from .flash_music_video_validation import check_required_keys
            key_errors = check_required_keys(parsed, ["features", "unsupported_or_unproven_claims"])
            errors.extend(f"Attempt {result.get('attempt')}: {e}" for e in key_errors)
        elif case_name == "candidate_section_patches":
            from .flash_music_video_validation import check_required_keys
            key_errors = check_required_keys(parsed, ["candidate_patches"])
            errors.extend(f"Attempt {result.get('attempt')}: {e}" for e in key_errors)
        elif case_name == "safe_boundary":
            from .flash_music_video_validation import check_required_keys
            key_errors = check_required_keys(parsed, [
                "can_fully_complete_with_current_script_surface",
                "confirmed_capabilities",
                "requirements_not_proven_or_not_supported",
                "recommended_escalation",
                "reasoning_summary",
            ])
            errors.extend(f"Attempt {result.get('attempt')}: {e}" for e in key_errors)

    return errors


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="GLM-4.7-Flash Music Video Scripting Benchmark v0",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    fixtures_parser = sub.add_parser("fixtures", help="Prepare benchmark fixtures")
    fixtures_parser.add_argument("--source", default=None, help="Source directory override")

    evidence_parser = sub.add_parser("evidence", help="Build evidence bundle")

    run_parser = sub.add_parser("run", help="Run benchmark cases")
    run_parser.add_argument("--dry-run", action="store_true", help="Print request payload, no network call")
    run_parser.add_argument("--case", choices=CASE_NAMES, default=None, help="Run a single case")
    run_parser.add_argument("--attempts", type=int, default=3, help="Attempts per case")
    run_parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name")
    run_parser.add_argument("--base-url", default=DEFAULT_ENDPOINT, help="API base URL")
    run_parser.add_argument("--output-dir", default=None, help="Output directory for results (default: benchmark results/)")

    args = parser.parse_args(argv)

    if args.command == "fixtures":
        try:
            fixture_dir = prepare_fixtures(args.source)
            print(f"Fixtures prepared at {fixture_dir}")
            manifest = json.loads((fixture_dir / "manifest.json").read_text())
            for f in manifest["copied_files"]:
                print(f"  {f['file']}  ({f['size_bytes']} bytes, sha256={f['sha256'][:12]}...)")
            return 0
        except (FileNotFoundError, NotADirectoryError, RuntimeError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1

    elif args.command == "evidence":
        manifest = build_evidence_bundle()
        total = sum(len(v) for v in manifest["includes"].values())
        print(f"Evidence bundle built: {total} files across {len(manifest['includes'])} categories")
        for cat, entries in manifest["includes"].items():
            print(f"  {cat}: {len(entries)} files")
        print(f"Unresolved areas: {len(manifest['unresolved_areas'])}")
        return 0

    elif args.command == "run":
        output_dir = Path(args.output_dir) if args.output_dir else BENCHMARK_DIR / "results"

        api_key = os.environ.get("ZAI_API_KEY", "")
        if not api_key and not args.dry_run:
            print("ERROR: ZAI_API_KEY not set and --dry-run not specified", file=sys.stderr)
            return 1

        runner = ZAIAPIRunner(
            model=args.model,
            base_url=args.base_url,
            max_retries=args.attempts,
            api_key=api_key,
        )

        cases = [args.case] if args.case else CASE_NAMES

        all_results: dict[str, list[dict]] = {}
        all_errors: list[str] = []

        for case_name in cases:
            print(f"\n{'='*60}")
            print(f"Case: {case_name}")
            print(f"{'='*60}")
            results = run_case(
                case_name=case_name,
                runner=runner,
                attempts=args.attempts,
                output_dir=output_dir,
                dry_run=args.dry_run,
            )
            all_results[case_name] = results

            for r in results:
                if r.get("dry_run"):
                    ps = r.get("payload_summary", {})
                    print(f"  [DRY RUN] Attempt {ps.get('attempt', 1)}:")
                    print(f"    URL: {ps.get('url')}")
                    print(f"    Model: {ps.get('model')}")
                    print(f"    Messages: {ps.get('message_count')}")
                    print(f"    Payload keys: {ps.get('payload_keys')}")
                elif r.get("error"):
                    print(f"  [{r.get('http_status', 'ERR')}] Attempt {r.get('attempt')}: ERROR - {r.get('error')[:100]}")
                else:
                    status = r.get("http_status", 0)
                    elapsed = r.get("elapsed_seconds", 0)
                    tokens = r.get("usage", {}).get("total_tokens", "?")
                    parse = "OK" if r.get("parsed_output") else f"PARSE ERROR: {r.get('parse_error', 'unknown')}"
                    print(f"  [{status}] Attempt {r.get('attempt')}: {elapsed}s, {tokens} tokens, {parse}")

            if not args.dry_run:
                case_errors = _validate_results(results)
                all_errors.extend(case_errors)

        if all_errors:
            print(f"\n{'='*60}")
            print(f"Validation errors ({len(all_errors)}):")
            for err in all_errors:
                print(f"  - {err}")

        summary = {
            "benchmark": "GLM-4.7-Flash Music Video Scripting Benchmark v0",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "cases_run": cases,
            "attempts_per_case": args.attempts,
            "model": args.model,
            "dry_run": args.dry_run,
            "total_validation_errors": len(all_errors),
        }
        summary_path = output_dir / "run_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nSummary saved to {summary_path}")

        if all_errors:
            return 2
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
