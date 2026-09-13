"""Stem reconciliation: filenames are claims, not truth.

Compares full-mix instrument detections against per-stem detections and the
stems' *claimed* labels (parsed from filenames by the existing
`audio.ingest` stem-name pattern). Contradictory evidence is preserved,
never discarded.
"""
from __future__ import annotations

from typing import Any

# Claimed stem label (from filename) -> expected canonical instruments.
# A stem may legitimately carry more than one canonical instrument; anything
# outside `expected` but strongly detected is flagged as multi/bleed.
CLAIM_TO_CANONICAL: dict[str, list[str]] = {
    "vocals": ["vocals"],
    "backing vocals": ["vocals"],
    "backing_vocals": ["vocals"],
    "drums": ["drums"],
    "percussion": ["percussion", "drums"],
    "bass": ["bass"],
    "guitar": ["guitar"],
    "keyboard": ["keys", "piano", "organ"],
    "synth": ["synth"],
    "strings": ["strings"],
    "brass": ["brass"],
    "woodwinds": ["woodwinds"],
    "fx": ["fx"],
}

STRONG = 0.30   # canonical confidence considered "present"
WEAK = 0.10     # below this = "not detected"


def _canon(result: dict) -> dict[str, float]:
    return result.get("canonical", {})


def reconcile(mix_result: dict, stem_results: dict[str, dict],
              claimed_labels: dict[str, str]) -> dict[str, Any]:
    """Build the reconciliation report.

    mix_result: detector output for the full mix
    stem_results: {stem_name: detector output}
    claimed_labels: {stem_name: claimed label from filename}
    """
    mix_canon = _canon(mix_result)

    per_stem: dict[str, Any] = {}
    union: dict[str, float] = {}
    for name, det in stem_results.items():
        canon = _canon(det)
        for inst, conf in canon.items():
            union[inst] = max(union.get(inst, 0.0), conf)

        claim = claimed_labels.get(name, "").lower().replace("-", " ")
        expected = CLAIM_TO_CANONICAL.get(claim)
        detected_strong = [i for i, c in canon.items() if c >= STRONG]

        entry: dict[str, Any] = {
            "claimed_label": claimed_labels.get(name),
            "expected_canonical": expected,
            "detected_canonical": canon,
            "detected_strong": detected_strong,
            "top_raw": det.get("clipwise", [])[:5],
        }
        if expected is None:
            entry["assessment"] = "no-mapping (free observation)"
        else:
            claimed_hits = [i for i in expected if canon.get(i, 0.0) >= STRONG]
            claimed_weak = [i for i in expected
                            if WEAK <= canon.get(i, 0.0) < STRONG]
            unexpected = [i for i in detected_strong if i not in expected]
            entry.update({
                "claim_supported": bool(claimed_hits),
                "claim_weak": claimed_weak,
                "unexpected_strong": unexpected,
            })
            if claimed_hits and not unexpected:
                entry["assessment"] = "consistent"
            elif claimed_hits and unexpected:
                entry["assessment"] = "consistent + multi-instrument evidence"
            elif claimed_weak and not detected_strong:
                entry["assessment"] = "weakly consistent (label barely detected)"
            elif not claimed_hits and unexpected:
                entry["assessment"] = "MISLABELED? (claim absent, other content strong)"
            else:
                entry["assessment"] = "unclear (no strong evidence either way)"
        per_stem[name] = entry

    # Full-mix vs union-of-stems
    missing_from_stems = {i: c for i, c in mix_canon.items()
                          if c >= STRONG and union.get(i, 0.0) < WEAK}
    weaker_in_stems = {i: {"mix": c, "best_stem": union.get(i, 0.0)}
                       for i, c in mix_canon.items()
                       if c >= STRONG and WEAK <= union.get(i, 0.0) < c * 0.5}
    only_in_stems = {i: c for i, c in union.items()
                     if c >= STRONG and mix_canon.get(i, 0.0) < WEAK}

    return {
        "mix_canonical": mix_canon,
        "stem_union": dict(sorted(union.items(), key=lambda kv: -kv[1])),
        "per_stem": per_stem,
        "full_mix_vs_stems": {
            "in_mix_but_missing_from_stems": missing_from_stems,
            "much_weaker_in_stems_than_mix": weaker_in_stems,
            "in_stems_but_not_mix": only_in_stems,
        },
        "thresholds": {"strong": STRONG, "weak": WEAK},
        "notes": "Confidence values are detector-specific (PANNs sigmoid "
                 "probabilities); thresholds are V0 heuristics. Contradictory "
                 "evidence is preserved, not resolved.",
    }
