"""Suno extraction-target recommendations — canonical instrumentation stage.

Wraps the EXISTING ASABAAL VENTURES Suno Stem Target Recommender
(`analytics/suno_stem_target_recommender/` in the music_creation repository;
not reimplemented here). That tool answers, against the documented Suno
Advanced Split ontology (standard 22 / extended 86 targets):

    "Given the full mix WAV, which Suno extraction targets appear to be
     present, and with what confidence/recommendation status?"

Its ontology result is the CANONICAL instrumentation-identification output
for this pipeline. Generic AudioSet detectors (PANNs) remain supplemental
evidence only. The recommender is invoked in-place via subprocess (same
python environment) because it lives in another repository.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_REPO = os.environ.get(
    "SUNO_RECOMMENDER_REPO",
    str(Path(__file__).resolve().parents[4] / "music_creation"))
MODULE = "analytics.suno_stem_target_recommender.cli"

STATUS_ICONS = {
    "recommend_now": "🟢 recommend now",
    "recommend_broad_target": "🟡 recommend broad target",
    "review_before_extracting": "🟠 review before extracting",
    "not_recommended": "⚪ not recommended",
    "covered_by_other_recommendation": "🔵 covered by broader recommendation",
}

# Validation hints: recommendation target_id -> our extracted stem labels.
TARGET_TO_STEM_HINTS: dict[str, list[str]] = {
    "backing_vocal": ["backing vocals"],
    "lead_vocal": ["vocals"],
    "guitar": ["guitar"],
    "drums": ["drums"],
    "bass": ["bass"],
    "synth": ["synth"],
    "strings": ["strings"],
    "brass": ["brass"],
    "piano": ["keyboard"],
    "organ": ["keyboard"],
    "whistle": ["woodwinds"],
    "flute": ["woodwinds"],
    "saxophone": ["woodwinds"],
    "percussion": ["percussion"],
}


def run_extended(wav_path: Path, project_dir: Path, *,
                 title: str = "", repo: str | None = None,
                 mode: str = "extended") -> dict[str, Any]:
    """Run the recommender on `wav_path`; store reports inside the song
    package; return the parsed JSON report."""
    repo = repo or DEFAULT_REPO
    if not Path(repo).is_dir():
        raise FileNotFoundError(
            f"Suno recommender repo not found at {repo} "
            f"(set SUNO_RECOMMENDER_REPO)")
    out_dir = project_dir / "analysis" / "suno_targets"
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, "-m", MODULE, str(wav_path),
           "--mode", mode, "--output-dir", str(out_dir)]
    if title:
        cmd += ["--title", title]
    logger.info("running Suno Stem Target Recommender (%s) from %s",
                mode, repo)
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True,
                          timeout=3000)
    if proc.returncode != 0:
        raise RuntimeError(
            f"recommender failed (rc={proc.returncode}):\n{proc.stdout[-800:]}\n"
            f"{proc.stderr[-800:]}")

    reports = sorted(out_dir.glob("*_report.json"))
    if not reports:
        raise RuntimeError(f"no *_report.json produced in {out_dir}")
    report = json.loads(reports[-1].read_text())
    report["_provenance"] = {
        "tool": "ASABAAL VENTURES Suno Stem Target Recommender",
        "repo": repo,
        "module": MODULE,
        "mode": mode,
        "invocation": "subprocess (existing implementation, not reimplemented)",
        "report_files": [p.name for p in out_dir.glob("*_report.*")],
        "canonical": True,
        "role": "Suno extraction ontology — canonical instrumentation "
                "taxonomy for this pipeline; AudioSet/PANNs output remains "
                "supplemental detector evidence only",
    }
    write = out_dir / (reports[-1].stem + ".with-provenance.json")
    write.write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report


def validate_against_stems(report: dict, stems: dict[str, Path]) -> dict:
    """Useful (non-authoritative) validation: the 12 stems we actually
    extracted are evidence of what Suno itself could split. We compare the
    recommender's positive recommendations against those labels without
    treating Suno's extraction as perfect ground truth."""
    recs = report.get("recommendations", [])
    positive = [r for r in recs if r["status"] in
                ("recommend_now", "recommend_broad_target")]

    rows = []
    matched_stems: set[str] = set()
    for r in positive:
        hints = TARGET_TO_STEM_HINTS.get(r["target_id"], [])
        hits = [s for s in stems if any(h in s.lower() for h in hints)]
        matched_stems.update(hits)
        rows.append({
            "target": r["target_name"],
            "confidence": r["confidence"],
            "status": r["status"],
            "matching_extracted_stems": hits,
            "validation": ("supported" if hits else
                           "no dedicated stem (Suno may fold it into "
                           "another stem, or miss it)"),
        })
    # stems with no positive recommendation pointing at them
    uncovered = [s for s in stems if s not in matched_stems]
    return {
        "note": "Validation only — Suno's own extraction is neither ground "
                "truth nor required to match our recommendations.",
        "positive_recommendation_vs_stems": rows,
        "stems_without_matching_recommendation": uncovered,
    }
