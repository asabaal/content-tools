"""Exact prompt-length validation.

Hard rules from the kickoff spec (SUNO_TARGET_REFERENCE_CORPUS_KICKOFF_SPEC.md
§10.3–10.6):

    every MAIN and EXCLUDE prompt must be 900–1000 characters INCLUSIVE
    (actual characters, not tokens). Anything outside fails.

No exceptions, no padding with meaningless filler — the builders compose
specific control directives to reach the range.
"""
from __future__ import annotations

from dataclasses import dataclass

MIN_CHARS = 900
MAX_CHARS = 1000


@dataclass
class PromptCheck:
    target_id: str
    field: str                 # "MAIN" | "EXCLUDE"
    char_count: int
    ok: bool
    problems: list[str]

    def line(self) -> str:
        mark = "✓" if self.ok else "✗ FAIL"
        return (f"🟣 {self.field} — {self.char_count} characters {mark}"
                if self.field == "MAIN" else
                f"🛑 {self.field} — {self.char_count} characters {mark}")


def check_prompt(text: str, target_id: str, field: str) -> PromptCheck:
    """Exact character count; fails <900 or >1000."""
    count = len(text)
    problems = []
    if count < MIN_CHARS:
        problems.append(f"too short: {count} < {MIN_CHARS}")
    if count > MAX_CHARS:
        problems.append(f"too long: {count} > {MAX_CHARS}")
    if not text.strip():
        problems.append("empty prompt")
    return PromptCheck(target_id=target_id, field=field, char_count=count,
                       ok=not problems, problems=problems)


def check_book(prompts: dict[str, dict[str, str]]) -> dict:
    """Validate a whole prompt book: {target_id: {"main": str, "exclude": str}}.
    Returns a report dict; `all_ok` False means DO NOT ship the book."""
    report = {"targets": len(prompts), "checks": [],
              "all_ok": True,
              "rules": f"{MIN_CHARS}–{MAX_CHARS} characters inclusive"}
    for target_id in sorted(prompts):
        for field_name, key in (("MAIN", "main"), ("EXCLUDE", "exclude")):
            check = check_prompt(prompts[target_id][key], target_id, field_name)
            report["checks"].append({
                "target_id": target_id, "field": field_name,
                "char_count": check.char_count, "ok": check.ok,
                "problems": check.problems})
            report["all_ok"] = report["all_ok"] and check.ok
    report["prompt_count"] = len(report["checks"])
    return report
