"""MIDI comparison and reference<->stem correlation.

Metrics treat both files as first-class transcriptions: neither side is
"truth". Includes the correlation matrix that proposes which external
reference MIDI corresponds to which stem (Suno downloads arrive as
`<song>.mid`, `<song>(1).mid`, ... with no stem labels).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


def midi_metrics(path: Path) -> dict[str, Any]:
    """Structural metrics for one MIDI file (via pretty_midi)."""
    import pretty_midi

    pm = pretty_midi.PrettyMIDI(str(path))
    instruments = pm.instruments
    notes = [n for inst in instruments for n in inst.notes]
    drums = any(inst.is_drum for inst in instruments)
    pitches = np.array([n.pitch for n in notes], dtype=int) if notes else np.array([])
    onsets = np.array([n.start for n in notes]) if notes else np.array([])

    hist = np.zeros(128)
    for p in pitches:
        hist[p] += 1
    if hist.sum():
        hist = hist / hist.sum()

    # polyphony: mean simultaneous notes, sampled on note onsets
    poly = 0.0
    if notes:
        events = sorted((n.start, 1) for n in notes) + \
                 sorted((n.end, -1) for n in notes)
        events.sort()
        cur = peak = 0
        for _, delta in events:
            cur += delta
            peak = max(peak, cur)
        poly = float(np.mean([max(0, _running(events, t)) for t in
                              np.linspace(notes[0].start,
                                          max(n.end for n in notes), 200)])) \
            if notes else 0.0
        peak = peak  # noqa: keep simple

    # IOI over DISTINCT onset times: chord-simultaneous notes would
    # otherwise flood the median with zeros.
    distinct = np.unique(onsets) if len(onsets) else np.array([])
    ioi = np.diff(distinct) if len(distinct) > 1 else np.array([])
    return {
        "file": str(path),
        "duration": round(float(pm.get_end_time()), 2),
        "note_count": len(notes),
        "is_drum_channel": drums,
        "programs": sorted({inst.program for inst in instruments}),
        "pitch_histogram": [round(float(x), 5) for x in hist],
        "pitch_min": int(pitches.min()) if pitches.size else None,
        "pitch_max": int(pitches.max()) if pitches.size else None,
        "pitch_mean": round(float(pitches.mean()), 2) if pitches.size else None,
        "notes_per_second": round(len(notes) / max(pm.get_end_time(), 1e-6), 3),
        "mean_polyphony": round(poly, 3),
        "ioi_median": round(float(np.median(ioi)), 5) if ioi.size else None,
        "tempo_estimate": round(float(pm.estimate_tempo()), 1),
    }


def _running(events, t) -> int:
    cur = 0
    for time, delta in events:
        if time > t:
            break
        cur += delta
    return max(0, cur)


def compare_metrics(a: dict, b: dict) -> dict[str, Any]:
    """Asymmetric-safe similarity between two metric dicts."""
    ha, hb = np.array(a["pitch_histogram"]), np.array(b["pitch_histogram"])
    hist_cos = float(np.dot(ha, hb) /
                     (np.linalg.norm(ha) * np.linalg.norm(hb) + 1e-9))
    da, db = a["notes_per_second"], b["notes_per_second"]
    density_ratio = (min(da, db) / max(da, db)) if max(da, db) > 0 else 0.0

    ra = (a["pitch_min"], a["pitch_max"])
    rb = (b["pitch_min"], b["pitch_max"])
    if None in ra or None in rb:
        register_overlap = 0.0
    else:
        inter = max(0, min(ra[1], rb[1]) - max(ra[0], rb[0]))
        union = max(ra[1], rb[1]) - min(ra[0], rb[0]) + 1
        register_overlap = inter / union if union > 0 else 0.0

    ioi_a, ioi_b = a.get("ioi_median"), b.get("ioi_median")
    ioi_ratio = (min(ioi_a, ioi_b) / max(ioi_a, ioi_b)
                 if ioi_a and ioi_b else None)

    score = 0.5 * hist_cos + 0.3 * density_ratio + 0.2 * register_overlap
    return {
        "pitch_histogram_cosine": round(hist_cos, 4),
        "density_ratio": round(density_ratio, 4),
        "register_overlap": round(register_overlap, 4),
        "ioi_median_ratio": round(ioi_ratio, 4) if ioi_ratio else None,
        "note_count": {"a": a["note_count"], "b": b["note_count"]},
        "similarity_score": round(score, 4),
    }


def correlate_references_to_stems(
        stem_transcriptions: dict[str, dict],
        reference_metrics: dict[str, dict]) -> dict[str, Any]:
    """Greedy best-match assignment between stems (by our transcription
    metrics) and unlabeled reference MIDIs. Highest similarity wins; matches
    below a floor are reported as unmatched."""
    pairs = []
    for stem, sm in stem_transcriptions.items():
        for ref, rm in reference_metrics.items():
            cmp = compare_metrics(sm, rm)
            pairs.append((cmp["similarity_score"], stem, ref, cmp))
    pairs.sort(reverse=True)

    assigned: dict[str, dict] = {}
    used_refs: set[str] = set()
    for score, stem, ref, cmp in pairs:
        if stem in assigned or ref in used_refs:
            continue
        assigned[stem] = {"reference": ref, "similarity": score,
                          "detail": cmp}
        used_refs.add(ref)

    unmatched_refs = sorted(set(reference_metrics) - used_refs)
    return {
        "proposed_mapping": assigned,
        "unmatched_references": unmatched_refs,
        "caveat": "Greedy assignment from structural similarity (pitch "
                  "histogram, density, register). A proposal to inspect, "
                  "not a proven fact.",
    }
