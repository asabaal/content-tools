"""`ingest-song` — orchestrate the local music ingestion pipeline.

Usage (from the content-tools repository root, with the shared music env):

  /mnt/storage/python_env/basic_audio_env/bin/python \
      tools/06-song-ingest/song_ingest/cli.py ingest "projects/hippie-activist."
  ... --stages discover,detect,reconcile   # subset
  ... --detector panns_cnn14 --midi-backend basic_pitch
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL_ROOT = Path(__file__).resolve().parents[1]
for p in (REPO_ROOT, REPO_ROOT / "music-video-pipeline" / "src", TOOL_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from song_ingest import __version__  # noqa: E402
from song_ingest.manifest import build_manifest, file_entry, now_iso, write_json  # noqa: E402

logger = logging.getLogger("song_ingest")

DEFAULT_STAGES = ["discover", "detect", "reconcile", "midi", "vocals",
                  "compare", "manifest"]

# Stems that never go through pitch transcription (no meaningful pitches).
NON_PITCHED = {"drums", "percussion", "fx"}
VOCAL_STEMS = {"vocals": "lead", "backing vocals": "backing"}


# ---------------------------------------------------------------- stages ----

def stage_discover(project: Path, ctx: dict) -> dict:
    from audio.ingest import discover_inputs  # existing content-tools ingestion
    result = discover_inputs(project)
    ctx["ingest"] = {
        "tier": result.tier,
        "audio": str(result.audio_path) if result.audio_path else None,
        "lyrics": str(result.lyrics_path) if result.lyrics_path else None,
    }
    # The stock discovery finds stems inside "*stem*" zips; loose
    # `N Name.wav` stems (our common case) are picked up from disk.
    stems = _stems_from_disk(project)
    mix = ctx["ingest"].get("audio")
    stems = {name: path for name, path in stems.items()
             if str(path) != mix}          # the mix is not a stem
    ctx["stems"] = stems
    ctx["reference_midi"] = sorted(project.glob("*.mid"))
    logger.info("discovered: tier=%s stems=%d midi=%d",
                result.tier, len(ctx["stems"]), len(ctx["reference_midi"]))
    return ctx["ingest"]


def _stems_from_disk(project: Path) -> dict[str, Path]:
    """Fallback/robust stem discovery: `N Name.wav` in the project dir."""
    import re
    pattern = re.compile(r"^(\d+)\s+(.+)\.(wav|mp3|flac)$", re.IGNORECASE)
    stems = {}
    for f in sorted(project.iterdir()):
        m = pattern.match(f.name)
        if m:
            stems[m.group(2).replace("_", " ").strip()] = f
    return stems


def stage_detect(project: Path, ctx: dict, detector_name: str) -> dict:
    from song_ingest.detectors import get_detector
    detector = get_detector(detector_name)
    out_dir = project / "analysis" / "instruments"
    mix_path = Path(ctx["ingest"]["audio"]) if ctx["ingest"]["audio"] \
        else project / "0 hippie activist..wav"
    stems = ctx.get("stems") or _stems_from_disk(project)

    logger.info("detecting instruments: mix + %d stems (%s)",
                len(stems), detector_name)
    mix_result = detector.detect(mix_path)
    write_json(out_dir / "full_mix.json", mix_result)

    stem_results = {}
    for name, path in sorted(stems.items()):
        logger.info("  stem: %s", name)
        stem_results[name] = detector.detect(path)
        write_json(out_dir / "stems" /
                   f"{path.stem.replace(' ', '_')}.json", stem_results[name])

    ctx["stems"] = stems
    ctx["detect"] = {"mix": mix_result, "stems": stem_results,
                     "detector": detector_name}
    return {"mix": mix_result["file"], "stems": len(stem_results)}


def stage_reconcile(project: Path, ctx: dict) -> dict:
    from song_ingest.reconcile import reconcile
    stems = ctx["stems"]
    claimed = {name: name for name in stems}   # filename IS the claim
    report = reconcile(ctx["detect"]["mix"], ctx["detect"]["stems"], claimed)
    path = write_json(project / "analysis" / "stems" / "reconciliation.json",
                      report)
    ctx["reconcile"] = report
    return {"report": str(path)}


def _is_pitched(stem_name: str, recon: dict) -> bool:
    low = stem_name.lower()
    if any(k in low for k in NON_PITCHED):
        return False
    if any(k in low for k in VOCAL_STEMS):
        return False
    entry = recon["per_stem"].get(stem_name, {})
    # trust the claim unless detection strongly contradicts with only
    # non-pitched content
    return True


def stage_midi(project: Path, ctx: dict, backend_name: str) -> dict:
    from song_ingest.transcribe_midi import get_backend
    backend = get_backend(backend_name)
    stems = ctx["stems"]
    recon = ctx.get("reconcile")
    out_dir = project / "derived" / "midi"
    records = {}
    for name, path in sorted(stems.items()):
        if not _is_pitched(name, recon or {}):
            logger.info("midi: skipping non-pitched/vocal stem %s", name)
            continue
        out_midi = out_dir / f"{path.stem.replace(' ', '_')}.mid"
        logger.info("transcribing to MIDI: %s", name)
        records[name] = backend.transcribe(path, out_midi)
    summary = write_json(project / "analysis" / "midi" / "transcriptions.json",
                         {"backend": backend_name, "stems": records})
    ctx["midi"] = records
    return {"stems_transcribed": len(records), "summary": str(summary)}


def stage_vocals(project: Path, ctx: dict, model_size: str) -> dict:
    from song_ingest.transcribe_vocals import mix_wavs, transcribe_vocals
    stems = ctx["stems"]
    vocal_stems = {name: path for name, path in stems.items()
                   if any(k in name.lower() for k in VOCAL_STEMS)}
    if not vocal_stems:
        logger.warning("no vocal stems found")
        return {"status": "no vocal stems"}
    combined = mix_wavs(
        [vocal_stems[n] for n in sorted(vocal_stems)
         if "backing" not in n.lower() or True],
        project / "derived" / "vocals" / "vocals_combined.wav")
    named = {f"{name.lower().replace(' ', '_')}": path
             for name, path in vocal_stems.items()}
    named["combined"] = combined
    results = transcribe_vocals(named, project / "derived" / "transcripts",
                                model_size=model_size)
    write_json(project / "analysis" / "vocals" / "transcription_index.json",
               {"model": f"faster-whisper/{model_size}", "passes": results})
    ctx["vocals"] = results
    return results


def stage_compare(project: Path, ctx: dict) -> dict:
    from song_ingest.compare_midi import (
        compare_metrics, correlate_references_to_stems, midi_metrics)

    references = {}
    for f in sorted(project.glob("*.mid")):
        references[f.name] = midi_metrics(f)
    local = {name: midi_metrics(Path(rec["midi"]))
             for name, rec in ctx.get("midi", {}).items()}

    comparisons = {}
    for name, lm in local.items():
        best = None
        for ref_name, rm in references.items():
            cmp = compare_metrics(lm, rm)
            if best is None or cmp["similarity_score"] > best[1]:
                best = (ref_name, cmp["similarity_score"], cmp)
        comparisons[name] = {
            "local": lm,
            "best_matching_reference": {"file": best[0],
                                        "similarity": best[1],
                                        "detail": best[2]} if best else None,
            "note": "structural similarity only; not a correctness verdict "
                    "in either direction",
        }

    correlation = correlate_references_to_stems(local, references)
    out_dir = project / "analysis" / "comparisons"
    write_json(out_dir / "local-vs-reference.json",
               {"comparisons": comparisons,
                "reference_metrics": references})
    corr_path = write_json(out_dir / "reference-stem-correlation.json",
                           correlation)
    ctx["compare"] = {"comparisons": comparisons, "correlation": correlation}
    return {"references": len(references), "local": len(local),
            "correlation": str(corr_path)}


def stage_manifest(project: Path, ctx: dict) -> dict:
    import basic_pitch
    from song_ingest.detectors import sha256_file

    stems = ctx.get("stems", {})
    source = {
        "full_mix": ctx["ingest"].get("audio"),
        "stems": {name: {"path": str(path),
                         "sha256": sha256_file(path)}
                  for name, path in stems.items()},
        "reference_midi": [file_entry(f, "external reference "
                                         "(manually extracted; NOT ground truth)")
                           for f in sorted(project.glob("*.mid"))],
        "lyrics_known": ctx["ingest"].get("lyrics"),
        "archive": [file_entry(f, "original archive")
                    for f in sorted(project.glob("*.zip"))],
    }
    analysis = {"instruments": "analysis/instruments/",
                "reconciliation": "analysis/stems/reconciliation.json",
                "midi": "analysis/midi/transcriptions.json",
                "vocals": "analysis/vocals/transcription_index.json",
                "comparisons": "analysis/comparisons/"}
    derived = {"midi": "derived/midi/", "transcripts": "derived/transcripts/",
               "combined_vocals_wav": "derived/vocals/vocals_combined.wav"}
    manifest = build_manifest(project, source=source, analysis=analysis,
                              derived=derived,
                              tool_versions={
                                  "song_ingest": __version__,
                                  "detector": ctx.get("detect", {})
                                  .get("detector"),
                                  "midi_backend": "basic_pitch "
                                  f"{getattr(basic_pitch, '__version__', '0.4.0')}",
                                  "vocal_asr": "faster-whisper (via "
                                  "music-video-pipeline AudioAnalyzer)",
                              })
    path = write_json(project / "manifest.json", manifest)
    write_report(project, ctx)
    return {"manifest": str(path)}


def write_report(project: Path, ctx: dict) -> None:
    lines = [f"# Song analysis — {project.name}", "",
             f"Generated {now_iso()} by song_ingest {__version__} "
             "(local/open-source pipeline; reference MIDI treated as "
             "independent evidence, not ground truth).", ""]

    recon = ctx.get("reconcile")
    if recon:
        lines += ["## Instrument reconciliation", "",
                  "| stem | claim | assessment | strong detections |",
                  "|---|---|---|---|"]
        for name, entry in recon["per_stem"].items():
            lines.append(f"| {name} | {entry.get('claimed_label','')} "
                         f"| {entry.get('assessment','')} "
                         f"| {', '.join(entry.get('detected_strong', [])) or '—'} |")
        fmv = recon["full_mix_vs_stems"]
        lines += ["", f"- In mix but missing from stems: "
                  f"{json.dumps(fmv['in_mix_but_missing_from_stems'])}",
                  f"- Much weaker in stems than mix: "
                  f"{json.dumps(fmv['much_weaker_in_stems_than_mix'])}",
                  ""]

    corr = ctx.get("compare", {}).get("correlation")
    if corr:
        lines += ["## Proposed reference-MIDI ↔ stem mapping "
                  "(similarity-based, to inspect)", "",
                  "| stem | reference | similarity |", "|---|---|---|"]
        for stem, m in corr["proposed_mapping"].items():
            lines.append(f"| {stem} | {m['reference']} | {m['similarity']:.3f} |")
        lines.append("")

    midi = ctx.get("midi", {})
    if midi:
        lines += ["## Local MIDI transcriptions (Basic Pitch)", "",
                  "| stem | notes |", "|---|---|"]
        for name, rec in midi.items():
            lines.append(f"| {name} | {rec['note_count']} |")
        lines.append("")

    vocals = ctx.get("vocals", {})
    if vocals:
        lines += ["## Vocal transcription (faster-whisper, raw preserved)", "",
                  "| pass | segments | words |", "|---|---|---|"]
        for name, rec in vocals.items():
            lines.append(f"| {name} | {rec.get('segments')} "
                         f"| {rec.get('words')} |")
        lines.append("")

    (project / "ANALYSIS_REPORT.md").write_text("\n".join(lines) + "\n")


# ----------------------------------------------------------------- main ----

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ingest-song")
    ap.add_argument("command", choices=["ingest"])
    ap.add_argument("project", type=Path)
    ap.add_argument("--stages", default=",".join(DEFAULT_STAGES))
    ap.add_argument("--detector", default="panns_cnn14")
    ap.add_argument("--midi-backend", default="basic_pitch")
    ap.add_argument("--vocal-model", default="small")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    stages = [s.strip() for s in args.stages.split(",") if s.strip()]
    project = args.project.resolve()
    if not project.is_dir():
        print(f"project dir not found: {project}", file=sys.stderr)
        return 2

    ctx: dict = {}
    results: dict = {}
    for stage in stages:
        logger.info("=== stage: %s ===", stage)
        if stage == "discover":
            results[stage] = stage_discover(project, ctx)
        elif stage == "detect":
            results[stage] = stage_detect(project, ctx, args.detector)
        elif stage == "reconcile":
            results[stage] = stage_reconcile(project, ctx)
        elif stage == "midi":
            results[stage] = stage_midi(project, ctx, args.midi_backend)
        elif stage == "vocals":
            results[stage] = stage_vocals(project, ctx, args.vocal_model)
        elif stage == "compare":
            results[stage] = stage_compare(project, ctx)
        elif stage == "manifest":
            results[stage] = stage_manifest(project, ctx)
        else:
            print(f"unknown stage {stage}", file=sys.stderr)
            return 2
    print(json.dumps({k: v for k, v in results.items()}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
