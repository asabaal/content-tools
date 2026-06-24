from __future__ import annotations

import json
import re
from typing import Any

ALLOWED_STATUS_VALUES = {"confirmed", "inference", "unknown"}


def parse_response_json(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        start = 0
        for i, line in enumerate(lines):
            if line.startswith("```"):
                start = i + 1
                break
        end = len(lines)
        for i in range(len(lines) - 1, start - 1, -1):
            if lines[i].startswith("```"):
                end = i
                break
        text = "\n".join(lines[start:end]).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Response is not valid JSON: {e}") from e


def check_required_keys(data: dict, required_keys: list[str], path: str = "") -> list[str]:
    errors: list[str] = []
    for key in required_keys:
        full_path = f"{path}.{key}" if path else key
        if key not in data:
            errors.append(f"Missing required key: {full_path}")
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and k in ("pipeline_stages", "features", "candidate_patches", "evidence"):
                if k == "pipeline_stages":
                    for i, stage in enumerate(v):
                        if isinstance(stage, dict):
                            errors += check_required_keys(
                                stage, ["stage", "input_artifacts", "output_artifacts", "status"],
                                f"pipeline_stages[{i}]",
                            )
                            status = stage.get("status")
                            if status not in ALLOWED_STATUS_VALUES:
                                errors.append(
                                    f"pipeline_stages[{i}].status='{status}' not in {ALLOWED_STATUS_VALUES}"
                                )
                elif k == "features":
                    for i, feat in enumerate(v):
                        if isinstance(feat, dict):
                            errors += check_required_keys(
                                feat, ["script_field_or_concept", "supported_values_or_shape", "status"],
                                f"features[{i}]",
                            )
                            status = feat.get("status")
                            if status not in ALLOWED_STATUS_VALUES:
                                errors.append(
                                    f"features[{i}].status='{status}' not in {ALLOWED_STATUS_VALUES}"
                                )
                elif k == "candidate_patches":
                    for i, patch in enumerate(v):
                        if isinstance(patch, dict):
                            errors += check_required_keys(
                                patch, ["brief_id", "patch", "field_rationales"],
                                f"candidate_patches[{i}]",
                            )
                elif k == "evidence":
                    for i, ev in enumerate(v):
                        if isinstance(ev, dict):
                            errors += check_required_keys(ev, ["path", "claim"], f"evidence[{i}]")
    return errors


def validate_source_evidence_paths(
    data: dict,
    manifest_paths: set[str],
    path: str = "",
) -> list[str]:
    errors: list[str] = []
    if isinstance(data, dict):
        if "path" in data and path.endswith(".path") or "source_evidence" in data:
            for key, value in data.items():
                if key == "path" and isinstance(value, str):
                    if value not in manifest_paths:
                        errors.append(f"Evidence path not in manifest: '{value}' (at {path}.path)")
                elif key == "source_evidence" and isinstance(value, list):
                    for i, entry in enumerate(value):
                        if isinstance(entry, dict) and "path" in entry:
                            p = entry["path"]
                            if p not in manifest_paths:
                                errors.append(
                                    f"Evidence path not in manifest: '{p}' (at {path}.source_evidence[{i}].path)"
                                )
        for k, v in data.items():
            sub = f"{path}.{k}" if path else k
            if isinstance(v, dict):
                errors += validate_source_evidence_paths(v, manifest_paths, sub)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        errors += validate_source_evidence_paths(item, manifest_paths, f"{sub}[{i}]")
    return errors


def validate_candidate_patch_fields(
    data: dict,
    confirmed_fields: set[str],
    path: str = "",
) -> list[str]:
    errors: list[str] = []
    if isinstance(data, dict):
        patches = data.get("candidate_patches", [])
        for i, patch in enumerate(patches):
            if isinstance(patch, dict):
                p = patch.get("patch", {})
                if isinstance(p, dict):
                    for field in p:
                        if field not in confirmed_fields:
                            errors.append(
                                f"candidate_patches[{i}].patch uses unsupported field '{field}'"
                            )
        for k, v in data.items():
            sub = f"{path}.{k}" if path else k
            if isinstance(v, dict):
                errors += validate_candidate_patch_fields(v, confirmed_fields, sub)
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        errors += validate_candidate_patch_fields(item, confirmed_fields, f"{sub}[{i}]")
    return errors


def check_run_metadata(meta: dict) -> list[str]:
    errors: list[str] = []
    required = ["model", "case_name", "attempt", "timestamp", "http_status"]
    for key in required:
        if key not in meta:
            errors.append(f"Run metadata missing required key: {key}")
    return errors


API_KEY_PATTERNS = [
    re.compile(r"ZAI_API_KEY"),
    re.compile(r"Authorization:\s*Bearer\s+\S+"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
]


def redact_api_keys(text: str) -> str:
    for pattern in API_KEY_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def validate_no_api_key_leak(text: str) -> list[str]:
    leaks: list[str] = []
    for pattern in API_KEY_PATTERNS:
        if pattern.search(text):
            leaks.append(f"Pattern found: {pattern.pattern}")
    return leaks
