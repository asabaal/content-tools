from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.models import MusicVideoProject, SUPPORTED_AUDIO, SUPPORTED_LYRICS
from audio.analyzer import AudioAnalyzer
from audio.ingest import ingest_project
from lyrics.parser import LyricParser, LyricsResult

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _find_project(project_dir: str | None) -> Path:
    if project_dir:
        p = Path(project_dir).resolve()
        if (p / "data" / "mvp_project.json").exists():
            return p
        raise click.ClickException(f"No project found at {p}")
    cwd = Path.cwd()
    if (cwd / "data" / "mvp_project.json").exists():
        return cwd
    raise click.ClickException("No project found in current directory. Run `mvp init` first.")


def _validate_audio(ctx, param, value):
    if value is None:
        return None
    p = Path(value)
    if not p.exists():
        raise click.BadParameter(f"Audio file not found: {value}")
    if p.suffix.lower() not in SUPPORTED_AUDIO:
        raise click.BadParameter(f"Unsupported audio format: {p.suffix}. Supported: {', '.join(sorted(SUPPORTED_AUDIO))}")
    return p


def _validate_lyrics(ctx, param, value):
    if value is None:
        return None
    p = Path(value)
    if not p.exists():
        raise click.BadParameter(f"Lyrics file not found: {value}")
    if p.suffix.lower() not in SUPPORTED_LYRICS:
        raise click.BadParameter(f"Unsupported lyrics format: {p.suffix}. Supported: {', '.join(sorted(SUPPORTED_LYRICS))}")
    return p


def _format_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}" if m < 60 else f"{m // 60}:{m % 60:02d}:{s:02d}"


def _to_relative(abs_path: str, base_dir: Path) -> str:
    try:
        return str(Path(abs_path).relative_to(base_dir))
    except ValueError:
        return abs_path


def _run_ingest(proj: MusicVideoProject) -> dict | None:
    audio_path = proj.paths.resolve_audio(proj.data_dir)
    lyrics_path = proj.paths.resolve_lyrics(proj.data_dir)

    if audio_path is None and proj.paths.data_dir is None:
        return None

    scan_dir = proj.raw_dir
    if proj.paths.data_dir:
        scan_dir = Path(proj.paths.data_dir)

    if not scan_dir.exists():
        return None

    result = ingest_project(scan_dir, proj.cache_dir)
    result_data = result.to_dict()
    proj.ingest_file.write_text(json.dumps(result_data, indent=2, ensure_ascii=False), encoding="utf-8")

    if result.audio_path and not proj.paths.audio:
        proj.paths.audio = _to_relative(result.audio_path, proj.data_dir)

    if result.lyrics_path and not proj.paths.lyrics:
        proj.paths.lyrics = _to_relative(result.lyrics_path, proj.data_dir)

    proj.input_tier = result.tier

    click.echo(f"    Input tier: {result.tier}")
    click.echo(f"    Audio: {'found' if result.audio_path else 'none'}")
    click.echo(f"    Lyrics: {'found' if result.lyrics_path else 'none'}")
    click.echo(f"    Stems: {len(result.stems)}")
    click.echo(f"    MIDI: {len(result.midi_files)}")
    if result.has_tempo_locked_stems:
        click.echo(f"    Tempo-locked stems: yes")

    return result_data


def _run_analysis(proj: MusicVideoProject, verbose: bool = False) -> None:
    audio_path = proj.paths.resolve_audio(proj.data_dir)
    if audio_path is None:
        raise click.ClickException("No audio file found in project. Set one with --audio.")

    midi_tempo = None
    ingest_data = None
    if proj.ingest_file.exists():
        ingest_data = json.loads(proj.ingest_file.read_text(encoding="utf-8"))

    if ingest_data and ingest_data.get("midi_files"):
        from audio.midi import extract_tempo
        for mf in ingest_data["midi_files"]:
            mpath = mf.get("path", "")
            if mpath and Path(mpath).exists():
                t = extract_tempo(mpath)
                if t is not None:
                    midi_tempo = t
                    break

    stem_validation = {}
    vocal_candidates_info = []
    stem_features = []
    all_stem_paths = []
    combined_mix_path = None

    if ingest_data and ingest_data.get("stems"):
        import librosa

        click.echo(f"\n  Validating stems...")
        for sf_entry in ingest_data["stems"]:
            spath = sf_entry.get("path", "")
            stem_type = sf_entry.get("stem_type", "").lower()
            stem_name = sf_entry.get("name", "")
            if not spath or not Path(spath).exists():
                continue

            try:
                stem_dur = float(librosa.get_duration(path=str(spath)))
            except Exception:
                stem_dur = 0.0

            verdict = "ok"
            reason = ""
            dur_ratio = 1.0

            if stem_dur < 1.0:
                verdict = "truncated"
                reason = f"Stem duration {stem_dur:.1f}s is too short"

            stem_validation[stem_type] = {
                "file": Path(spath).name,
                "stem_duration": round(stem_dur, 1),
                "verdict": verdict,
            }
            if reason:
                stem_validation[stem_type]["reason"] = reason

            if verdict == "ok":
                all_stem_paths.append({"path": spath, "stem_type": stem_type, "name": stem_name})

            if "vocal" in stem_type and verdict == "ok":
                vocal_candidates_info.append({"path": spath, "stem_type": stem_type, "name": stem_name})

        if all_stem_paths:
            click.echo(f"    Generating combined mix from {len(all_stem_paths)} stems...")
            combined_audio = None
            combined_sr = None
            for sp in all_stem_paths:
                audio, sr = librosa.load(str(sp["path"]), sr=None, mono=True)
                if combined_audio is None:
                    combined_audio = audio
                    combined_sr = sr
                else:
                    min_len = min(len(combined_audio), len(audio))
                    combined_audio[:min_len] += audio[:min_len]
            if combined_audio is not None:
                import numpy as np
                peak = np.max(np.abs(combined_audio))
                if peak > 0:
                    combined_audio = combined_audio / peak
                combined_mix_path = proj.data_dir / "cache" / "stems" / "combined_mix.wav"
                combined_mix_path.parent.mkdir(parents=True, exist_ok=True)
                import soundfile as sf_write
                sf_write.write(str(combined_mix_path), combined_audio, combined_sr)
                click.echo(f"    Combined mix: {len(combined_audio)/combined_sr:.1f}s -> {combined_mix_path.name}")

    if combined_mix_path is not None:
        click.echo(f"\n  Analyzing combined mix (from stems): {combined_mix_path.name}")
        analysis_audio_path = combined_mix_path
        proj.paths.audio = f"cache/stems/combined_mix.wav"
    else:
        click.echo(f"\n  Analyzing audio: {audio_path.name}")
        analysis_audio_path = audio_path

    analyzer = AudioAnalyzer()
    features = analyzer.analyze(analysis_audio_path)
    peaks, _ = analyzer.generate_waveforms()

    if all_stem_paths:
        for sp in all_stem_paths:
            sf_result = analyzer.analyze_stem(sp["path"], sp["stem_type"], sp["name"])
            stem_features.append(sf_result)

        if not vocal_candidates_info and any(sv.get("verdict") == "truncated" for k, sv in stem_validation.items() if "vocal" in k):
            click.echo(f"    WARNING: All vocal stems truncated, using full-mix onsets as fallback", err=True)
            stem_validation["fallback"] = "full_mix"
            stem_validation["note"] = "Full-mix onsets include non-vocal events. Sync accuracy may be lower."

        features.stem_features = stem_features

    if midi_tempo is not None:
        features.midi_tempo = midi_tempo

    proj.data_dir.mkdir(parents=True, exist_ok=True)

    analysis_data = features.to_dict()

    if vocal_candidates_info:
        import numpy as np

        transcriptions = {}
        for vc in vocal_candidates_info:
            stype = vc["stem_type"]
            click.echo(f"    Transcribing {vc['name']}...")
            try:
                trans = analyzer.transcribe_vocal_stem(vc["path"])
                trans["source"] = Path(vc["path"]).name
                trans["stem_type"] = stype
                if stem_validation:
                    trans["stem_validation"] = stem_validation
                transcriptions[stype] = trans
                (proj.data_dir / f"vocal_transcription_{stype}.json").write_text(
                    json.dumps(trans, indent=2, ensure_ascii=False), encoding="utf-8"
                )
            except Exception as e:
                click.echo(f"    WARNING: Transcription of {vc['name']} failed: {e}", err=True)

        if not transcriptions:
            click.echo(f"    WARNING: All vocal transcriptions failed", err=True)
            vocal_candidates_info = []

        if vocal_candidates_info:
            lyrics_lines = None
            if proj.lyrics_raw_file.exists():
                try:
                    raw_ld = json.loads(proj.lyrics_raw_file.read_text(encoding="utf-8"))
                    from lyrics.parser import LyricLine
                    lyrics_lines = [LyricLine(index=ld.get("index", i), text=ld["text"], start=0.0, end=0.0, words=[])
                                    for i, ld in enumerate(raw_ld.get("lines", [])) if ld.get("text", "").strip()]
                except Exception:
                    pass

            def _score_transcription(trans):
                if lyrics_lines is None or not trans.get("segments"):
                    return 1.0, {}
                from lyrics.alignment_analyzer import _align_lyrics_to_segments
                _, match_ratios, _ = _align_lyrics_to_segments(lyrics_lines, trans["segments"])
                non_empty = [l for l in lyrics_lines if l.text.strip()]
                covered = sum(1 for i in range(len(non_empty)) if match_ratios.get(i, 0.0) > 0.9)
                total = len(non_empty)
                return covered / total if total > 0 else 0.0, match_ratios

            scored = {st: _score_transcription(tr) for st, tr in transcriptions.items()}

            active_stem_type = None
            per_line_source = {}
            combined_segments = []

            if len(transcriptions) == 1:
                active_stem_type = list(transcriptions.keys())[0]
            else:
                best_stype = max(scored, key=lambda k: scored[k][0])
                if scored[best_stype][0] >= 1.0:
                    active_stem_type = best_stype
                    click.echo(f"    {best_stype} covers all lyrics — using as primary vocal source")
                else:
                    click.echo(f"    No single stem covers all lyrics, merging transcriptions...")
                    active_stem_type = "combined"

                    non_empty = [l for l in lyrics_lines if l.text.strip()] if lyrics_lines else []
                    for li, line in enumerate(non_empty):
                        best_for_line = None
                        best_ratio = 0.0
                        for st, (coverage, match_ratios) in scored.items():
                            r = match_ratios.get(li, 0.0)
                            if r > best_ratio:
                                best_ratio = r
                                best_for_line = st
                        per_line_source[str(line.index)] = best_for_line or list(transcriptions.keys())[0]

                    all_segments = []
                    for st, tr in transcriptions.items():
                        for seg in tr.get("segments", []):
                            seg_copy = dict(seg)
                            seg_copy["stem_type"] = st
                            all_segments.append(seg_copy)
                    all_segments.sort(key=lambda s: s.get("start", 0))
                    combined_segments = all_segments

            if active_stem_type == "combined":
                active_transcription = {
                    "language": next(iter(transcriptions.values())).get("language", "en"),
                    "language_probability": next(iter(transcriptions.values())).get("language_probability", 0.0),
                    "duration": next(iter(transcriptions.values())).get("duration", 0.0),
                    "segments": combined_segments,
                    "words": [w for tr in transcriptions.values() for w in tr.get("words", [])],
                    "source": " + ".join(Path(vc["path"]).name for vc in vocal_candidates_info),
                    "vocal_source": "combined",
                    "per_line_source": per_line_source,
                }
                if stem_validation:
                    active_transcription["stem_validation"] = stem_validation

                combined_audio = None
                combined_sr = None
                for vc in vocal_candidates_info:
                    import librosa
                    audio, sr = librosa.load(str(vc["path"]), sr=None, mono=True)
                    if combined_audio is None:
                        combined_audio = audio
                        combined_sr = sr
                    else:
                        min_len = min(len(combined_audio), len(audio))
                        combined_audio[:min_len] += audio[:min_len]
                if combined_audio is not None:
                    peak = np.max(np.abs(combined_audio))
                    if peak > 0:
                        combined_audio = combined_audio / peak * min(peak, 1.0)

                click.echo(f"    Extracting vocal onsets from combined stems...")
                combined_path = proj.data_dir / "cache" / "stems" / "combined_vocals.wav"
                combined_path.parent.mkdir(parents=True, exist_ok=True)
                import soundfile as sf
                sf.write(str(combined_path), combined_audio, combined_sr)

                vocal_onsets = analyzer.extract_vocal_onsets(str(combined_path))
                analysis_data["vocal_onset_times"] = vocal_onsets.tolist()

                vocal_onset_data = {
                    "source": "combined",
                    "onset_count": len(vocal_onsets),
                    "onset_times": vocal_onsets.tolist(),
                    "vocal_source": "combined",
                }
                if stem_validation:
                    vocal_onset_data["stem_validation"] = stem_validation
                (proj.data_dir / "vocal_onsets.json").write_text(
                    json.dumps(vocal_onset_data, indent=2, ensure_ascii=False), encoding="utf-8"
                )

                click.echo(f"    Generating combined vocal waveform...")
                try:
                    vocal_peaks, vocal_dur = analyzer.generate_waveforms_for_file(str(combined_path))
                    vocal_waveform_data = {
                        "peaks_per_second": 100,
                        "duration": vocal_dur,
                        "total_peaks": len(vocal_peaks),
                        "peaks": vocal_peaks,
                        "source": "combined",
                        "vocal_source": "combined",
                        "vocal_audio_path": f"cache/stems/combined_vocals.wav",
                    }
                    (proj.data_dir / "vocal_waveforms.json").write_text(
                        json.dumps(vocal_waveform_data, indent=2, ensure_ascii=False), encoding="utf-8"
                    )
                except Exception as e:
                    click.echo(f"    WARNING: Combined waveform generation failed: {e}", err=True)

            else:
                active_transcription = transcriptions[active_stem_type]
                active_transcription["vocal_source"] = active_stem_type

                active_vc = next(vc for vc in vocal_candidates_info if vc["stem_type"] == active_stem_type)
                active_path = active_vc["path"]

                click.echo(f"    Extracting vocal onsets from {active_vc['name']}...")
                vocal_onsets = analyzer.extract_vocal_onsets(active_path)
                analysis_data["vocal_onset_times"] = vocal_onsets.tolist()

                vocal_onset_data = {
                    "source": Path(active_path).name,
                    "onset_count": len(vocal_onsets),
                    "onset_times": vocal_onsets.tolist(),
                    "vocal_source": active_stem_type,
                }
                if stem_validation:
                    vocal_onset_data["stem_validation"] = stem_validation
                (proj.data_dir / "vocal_onsets.json").write_text(
                    json.dumps(vocal_onset_data, indent=2, ensure_ascii=False), encoding="utf-8"
                )

                click.echo(f"    Generating vocal waveform for {active_vc['name']}...")
                try:
                    vocal_peaks, vocal_dur = analyzer.generate_waveforms_for_file(active_path)
                    vocal_rel = str(Path(active_path).relative_to(proj.data_dir))
                    vocal_waveform_data = {
                        "peaks_per_second": 100,
                        "duration": vocal_dur,
                        "total_peaks": len(vocal_peaks),
                        "peaks": vocal_peaks,
                        "source": Path(active_path).name,
                        "vocal_source": active_stem_type,
                        "vocal_audio_path": vocal_rel,
                    }
                    (proj.data_dir / "vocal_waveforms.json").write_text(
                        json.dumps(vocal_waveform_data, indent=2, ensure_ascii=False), encoding="utf-8"
                    )
                except Exception as e:
                    click.echo(f"    WARNING: Vocal waveform generation failed: {e}", err=True)

            (proj.data_dir / "vocal_transcription.json").write_text(
                json.dumps(active_transcription, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            analysis_data["vocal_transcription_word_count"] = len(active_transcription.get("words", []))

    elif stem_validation.get("fallback") == "full_mix":
        vocal_onset_data = {
            "source": "combined_mix (fallback)",
            "onset_count": len(features.onset_times),
            "stem_validation": stem_validation,
        }
        (proj.data_dir / "vocal_onsets.json").write_text(
            json.dumps(vocal_onset_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    proj.analysis_file.write_text(json.dumps(analysis_data, indent=2, ensure_ascii=False), encoding="utf-8")

    waveform_data = {
        "peaks_per_second": 100,
        "duration": features.duration,
        "total_peaks": len(peaks),
        "peaks": peaks,
    }
    proj.waveforms_file.write_text(json.dumps(waveform_data, indent=2, ensure_ascii=False), encoding="utf-8")

    effective_bpm = midi_tempo if midi_tempo is not None else features.beats.tempo
    proj.audio_info = type(proj.audio_info)(
        duration=features.duration,
        bpm=round(effective_bpm, 1),
        sample_rate=features.sample_rate,
        beat_count=len(features.beats.times),
        onset_count=len(features.onset_times),
        midi_bpm=midi_tempo,
    )
    proj.stages.mark_complete("analyze")

    click.echo(f"    Duration:  {_format_duration(features.duration)} ({features.duration:.1f}s)")
    click.echo(f"    BPM:       {effective_bpm:.0f}" + (" (from MIDI)" if midi_tempo else ""))
    click.echo(f"    Beats:     {len(features.beats.times)}")
    click.echo(f"    Onsets:    {len(features.onset_times)}")

    energy = float(features.rms_energy.mean())
    level = "low" if energy < 0.15 else ("medium" if energy < 0.4 else ("medium-high" if energy < 0.6 else "high"))
    click.echo(f"    Energy:    {level}")

    if features.stem_features:
        click.echo(f"    Stems analyzed: {len(features.stem_features)}")
    if vocal_candidates_info:
        vocal_onset_count = len(analysis_data.get("vocal_onset_times", []))
        click.echo(f"    Vocal onsets: {vocal_onset_count}")
        trans_count = analysis_data.get("vocal_transcription_word_count", 0)
        if trans_count:
            click.echo(f"    Transcribed words: {trans_count}")
        if len(vocal_candidates_info) > 1:
            click.echo(f"    Vocal stems transcribed: {', '.join(vc['name'] for vc in vocal_candidates_info)}")
            active_src = "combined" if active_stem_type == "combined" else next(vc['name'] for vc in vocal_candidates_info if vc['stem_type'] == active_stem_type)
            click.echo(f"    Active vocal source: {active_src}")

    if verbose:
        click.echo(f"    Sample rate: {features.sample_rate} Hz")
        click.echo(f"    Frames: {len(features.rms_energy)} @ {features.frame_rate:.1f}/s")
        click.echo(f"    Waveform peaks: {len(peaks)}")

    saved = ["analysis.json", "waveforms.json"]
    if vocal_candidates_info:
        saved.append("vocal_onsets.json")
        if analysis_data.get("vocal_transcription_word_count", 0):
            saved.append("vocal_transcription.json")
        for vc in vocal_candidates_info:
            per_stem_file = f"vocal_transcription_{vc['stem_type']}.json"
            if (proj.data_dir / per_stem_file).exists():
                saved.append(per_stem_file)
    click.echo(f"    Saved: {', '.join(saved)}")


def _run_lyrics_import(proj: MusicVideoProject) -> None:
    lyrics_path = proj.paths.resolve_lyrics(proj.data_dir)
    if lyrics_path is None:
        return

    click.echo(f"\n  Importing lyrics: {lyrics_path.name}")

    parser = LyricParser()
    result = parser.parse_file(lyrics_path)

    if result.total_lines == 0:
        click.echo("    WARNING: No lyric lines parsed from file", err=True)
        return

    result.save(proj.lyrics_raw_file)

    proj.lyrics_info = type(proj.lyrics_info)(
        total_lines=result.total_lines,
        total_words=result.total_words,
        format=result.format,
        first_line_time=result.first_line_time,
        last_line_time=result.last_line_time,
        has_sections=len(result.sections) > 0,
        section_count=len(result.sections),
    )

    click.echo(f"    Format: {result.format.upper()}")
    click.echo(f"    Lines: {result.total_lines}, Words: {result.total_words}")
    if result.sections:
        click.echo(f"    Sections: {len(result.sections)} ({', '.join(s.section_type for s in result.sections)})")
    if result.first_line_time is not None and result.last_line_time is not None:
        click.echo(f"    Time range: {_format_duration(result.first_line_time)} - {_format_duration(result.last_line_time)}")
    if result.format == "txt" and not result.sections:
        click.echo("    NOTE: Plain text detected - timing is estimated (3s per line)")
    click.echo(f"    Saved: lyrics_raw.json")


def _run_sync(proj: MusicVideoProject, verbose: bool = False) -> None:
    raw_path = proj.data_dir / "lyrics_raw.json"
    analysis_path = proj.data_dir / "analysis.json"

    if not raw_path.exists():
        return
    if not analysis_path.exists():
        return

    click.echo(f"\n  Syncing lyrics to audio...")

    import numpy as np
    from lyrics.parser import LyricLine, LyricSection, LyricWord
    from lyrics.synchronizer import LyricSynchronizer
    from audio.features import AudioFeatures, BeatInfo

    raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
    analysis_data = json.loads(analysis_path.read_text(encoding="utf-8"))

    lines = []
    for ld in raw_data.get("lines", []):
        words = [LyricWord(text=w["text"], start=w["start"], end=w["end"]) for w in ld.get("words", [])]
        section = None
        if "section" in ld and ld["section"]:
            sd = ld["section"]
            section = LyricSection(raw_marker=sd.get("raw_marker", ""), section_type=sd.get("section_type", ""), index=sd.get("index"), tags=sd.get("tags", []))
        lines.append(LyricLine(index=ld["index"], text=ld["text"], start=ld["start"], end=ld["end"], words=words, section=section))

    beats = BeatInfo(
        times=np.array(analysis_data.get("beat_times", []), dtype=float),
        tempo=analysis_data.get("bpm", 120.0),
        confidence=analysis_data.get("beat_confidence", 0.0),
    )

    features = AudioFeatures(
        duration=analysis_data.get("duration", 0.0),
        sample_rate=analysis_data.get("sample_rate", 22050),
        beats=beats,
        onset_times=np.array(analysis_data.get("onset_times", []), dtype=float),
        rms_energy=np.zeros(100),
        spectral_centroids=np.zeros(100),
        zero_crossing_rate=np.zeros(100),
    )

    transcription_segments = None
    transcription_path = proj.data_dir / "vocal_transcription.json"
    if transcription_path.exists():
        trans_data = json.loads(transcription_path.read_text(encoding="utf-8"))
        if trans_data.get("segments"):
            transcription_segments = trans_data["segments"]

    vocal_waveform_peaks = None
    vocal_waveform_pps = 100
    vw_path = proj.data_dir / "vocal_waveforms.json"
    if vw_path.exists():
        try:
            vw_data = json.loads(vw_path.read_text(encoding="utf-8"))
            vocal_waveform_peaks = vw_data.get("peaks")
            vocal_waveform_pps = vw_data.get("peaks_per_second", 100)
        except Exception:
            pass

    syncer = LyricSynchronizer(
        lines,
        features,
        vocal_onset_times=np.array(analysis_data.get("vocal_onset_times", []), dtype=float) if analysis_data.get("vocal_onset_times") else None,
        transcription_segments=transcription_segments,
        vocal_waveform_peaks=vocal_waveform_peaks,
        vocal_waveform_pps=vocal_waveform_pps,
    )
    result = syncer.synchronize()

    vocal_onset_arr = np.array(analysis_data.get("vocal_onset_times", []), dtype=float) if analysis_data.get("vocal_onset_times") else np.array([], dtype=float)
    if len(vocal_onset_arr) > 0:
        from lyrics.onset_refiner import refine_synced_lines
        result = refine_synced_lines(result, vocal_onset_arr, vocal_waveform_peaks)

    result.save(proj.data_dir / "lyrics_synced.json")

    from lyrics.alignment_analyzer import analyze_alignment
    alignment = analyze_alignment(
        lyrics=lines,
        transcription_segments=transcription_segments,
        vocal_onset_times=np.array(analysis_data.get("vocal_onset_times", []), dtype=float) if analysis_data.get("vocal_onset_times") else None,
        audio_features=features,
    )
    alignment.save(proj.data_dir / "alignment_analysis.json")

    proj.stages.mark_complete("sync")

    click.echo(f"    Lines synced: {len(result.lines)}")
    click.echo(f"    Source: {result.source}")
    click.echo(f"    Avg confidence: {result.avg_confidence:.0%}")

    if result.vocal_stem_quality != "ok":
        click.echo(f"    Vocal stem quality: {result.vocal_stem_quality}")
        click.echo(f"      Onset source: {result.onset_source} ({result.onset_count} onsets, {result.cluster_count} clusters)")

    if alignment.transcription_segment_count > 0:
        click.echo(f"    Alignment analysis:")
        click.echo(f"      Transcription segments: {alignment.transcription_segment_count}")
        click.echo(f"      Word matches: {alignment.exact_matches} exact, {alignment.partial_matches} partial")
        if alignment.lines_split > 0:  # pragma: no cover
            click.echo(f"      Lines split across segments: {alignment.lines_split}")
        click.echo(f"      Recommendation: {alignment.recommendation}")

    if verbose:
        for i, line in enumerate(result.lines):
            sec = f" [{line.section.section_type}]" if line.section else ""
            click.echo(f"    {i:3d}: {line.start:7.2f} - {line.end:7.2f}  {line.text[:40]}{sec}")

    click.echo(f"    Saved: lyrics_synced.json")


@click.group()
@click.help_option("-h", "--help")
def cli():
    """Music Video Pipeline - Create lyric videos from audio + lyrics"""
    pass


@cli.command()
@click.option("--name", "-n", required=True, help="Project name")
@click.option("--artist", "-a", default="", help="Artist name")
@click.option("--audio", callback=_validate_audio, default=None, help="Path to audio file")
@click.option("--lyrics", callback=_validate_lyrics, default=None, help="Path to lyrics file (srt, lrc, txt)")
@click.option("--data-dir", type=click.Path(exists=True), default=None, help="Data directory with all inputs (Suno output)")
@click.option("--dir", "project_dir", default=None, help="Project directory (default: current dir)")
@click.option("--no-analyze", is_flag=True, help="Skip auto-analysis")
@click.option("--no-sync", is_flag=True, help="Skip auto-sync")
def init(name, artist, audio, lyrics, data_dir, project_dir, no_analyze, no_sync):
    """Initialize a new music video project."""
    project_dir = Path(project_dir).resolve() if project_dir else Path.cwd()
    project_file = project_dir / "data" / "mvp_project.json"
    if project_file.exists():
        raise click.ClickException(f"Project already exists at {project_dir}")

    click.echo(f'\n  Project: "{name}"' + (f" by {artist}" if artist else ""))
    click.echo(f"  Location: {project_dir}")

    data_dir_path = Path(data_dir).resolve() if data_dir else None

    proj = MusicVideoProject.create(
        project_dir=project_dir,
        name=name,
        artist=artist,
        audio_path=audio,
        lyrics_path=lyrics,
        data_dir=data_dir_path,
    )

    click.echo("  Created project structure.")

    click.echo("\n  Running ingest...")
    _run_ingest(proj)

    if not no_analyze:
        resolved_audio = proj.paths.resolve_audio(proj.data_dir)
        if resolved_audio:
            _run_analysis(proj)
        resolved_lyrics = proj.paths.resolve_lyrics(proj.data_dir)
        if resolved_lyrics:
            _run_lyrics_import(proj)
        proj.save()

    if not no_sync:
        _run_sync(proj)
        proj.save()

    click.echo(f"\n  Saved: mvp_project.json")
    click.echo(f'  Next: Run `mvp serve` to review and adjust sync in browser\n')

    proj.save()


@cli.command()
@click.option("--project", "-p", "project_dir", default=None, help="Path to project directory")
@click.option("--audio", callback=_validate_audio, default=None, help="Override audio file path")
@click.option("--lyrics", callback=_validate_lyrics, default=None, help="Override/set lyrics file path")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def analyze(project_dir, audio, lyrics, verbose):
    """Run audio analysis (Stage 2)."""
    proj_dir = _find_project(project_dir)
    proj = MusicVideoProject.load(proj_dir)

    if audio:
        dest = proj.raw_dir / audio.name
        if not dest.exists():
            dest.write_bytes(audio.read_bytes())
        proj.paths.audio = f"raw/{audio.name}"

    if lyrics:
        dest = proj.raw_dir / lyrics.name
        if not dest.exists():
            dest.write_bytes(lyrics.read_bytes())
        proj.paths.lyrics = f"raw/{lyrics.name}"

    _run_analysis(proj, verbose=verbose)

    if proj.paths.lyrics:
        _run_lyrics_import(proj)

    proj.save()
    click.echo()


@cli.command()
@click.option("--project", "-p", "project_dir", default=None, help="Path to project directory")
def info(project_dir):
    """Show project information and pipeline status."""
    proj_dir = _find_project(project_dir)
    proj = MusicVideoProject.load(proj_dir)

    click.echo(f'\n  Project: "{proj.name}"' + (f" by {proj.artist}" if proj.artist else ""))
    click.echo(f"  Created: {proj.created or 'unknown'}")
    click.echo(f"  Location: {proj.project_dir}")
    click.echo(f"  Input tier: {proj.input_tier}")

    if proj.audio_info.duration > 0:
        click.echo(f"\n  Audio:")
        click.echo(f"    File: {proj.paths.audio or 'not set'}")
        click.echo(f"    Duration: {_format_duration(proj.audio_info.duration)} ({proj.audio_info.duration:.1f}s)")
        if proj.audio_info.midi_bpm:
            click.echo(f"    BPM: {proj.audio_info.bpm:.0f} (from MIDI)")
        elif proj.audio_info.bpm:
            click.echo(f"    BPM: {proj.audio_info.bpm:.0f}")
        else:
            click.echo(f"    BPM: not analyzed")
        click.echo(f"    Beats: {proj.audio_info.beat_count}")
        click.echo(f"    Onsets: {proj.audio_info.onset_count}")
    else:
        click.echo(f"\n  Audio: not analyzed")

    if proj.lyrics_info.total_lines > 0:
        click.echo(f"\n  Lyrics:")
        click.echo(f"    File: {proj.paths.lyrics}")
        click.echo(f"    Format: {proj.lyrics_info.format.upper()}")
        click.echo(f"    Lines: {proj.lyrics_info.total_lines}, Words: {proj.lyrics_info.total_words}")
        if proj.lyrics_info.has_sections:
            click.echo(f"    Sections: {proj.lyrics_info.section_count}")
    else:
        click.echo(f"\n  Lyrics: none" + (" (instrumental mode)" if proj.paths.lyrics is None else ""))

    click.echo(f"\n  Pipeline:")
    stages = proj.stages
    for s in ["ingest", "analyze", "sync", "structure", "design", "render"]:
        status = getattr(stages, s, "pending")
        mark = "\u2713" if status == "complete" else " "
        click.echo(f"    [{mark}] {s}")

    nxt = stages.next_pending()
    if nxt == "analyze":
        click.echo(f'    \u2190 Run `mvp analyze`')
    elif nxt == "sync":
        click.echo(f'    \u2190 Run `mvp sync`')
    elif nxt == "structure":
        click.echo(f'    \u2190 Run `mvp serve`')
    elif nxt == "render":
        click.echo(f'    \u2190 Run `mvp render`')
    elif nxt is None:
        click.echo(f"    All stages complete!")

    click.echo()

    files = {
        "ingest.json": proj.ingest_file,
        "analysis.json": proj.analysis_file,
        "waveforms.json": proj.waveforms_file,
        "lyrics_raw.json": proj.lyrics_raw_file,
        "mvp_project.json": proj.project_file,
    }
    click.echo("  Files:")
    for label, fpath in files.items():
        if fpath.exists():
            size = fpath.stat().st_size
            size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
            click.echo(f"    {label:20s} \u2713 ({size_str})")
        else:
            click.echo(f"    {label:20s} -")
    click.echo()


@cli.command()
@click.option("--project", "-p", "project_dir", default=None, help="Path to project directory")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def sync(project_dir, verbose):
    """Run lyrics synchronization (Stage 3)."""
    proj_dir = _find_project(project_dir)
    proj = MusicVideoProject.load(proj_dir)

    raw_path = proj.data_dir / "lyrics_raw.json"
    analysis_path = proj.data_dir / "analysis.json"

    if not raw_path.exists():
        raise click.ClickException("lyrics_raw.json not found. Run `mvp analyze` first.")
    if not analysis_path.exists():
        raise click.ClickException("analysis.json not found. Run `mvp analyze` first.")

    _run_sync(proj, verbose=verbose)
    proj.save()
    click.echo(f"    Next: Run `mvp serve` to review and adjust in browser\n")


@cli.command()
@click.option("--project", "-p", "project_dir", default=None, help="Path to project directory")
@click.option("--port", default=8900, type=int, help="Port (default: 8900)")
def serve(project_dir, port):
    """Start HTTP server for browser tools."""
    import subprocess
    import os

    proj_dir = None
    if project_dir:
        proj_dir = str(Path(project_dir).resolve())
    else:
        try:
            found = _find_project(None)
            proj_dir = str(found)
        except click.ClickException:
            pass

    serve_script = Path(__file__).resolve().parent.parent.parent / "serve.py"
    if not serve_script.exists():
        raise click.ClickException(f"serve.py not found at {serve_script}")

    cmd = [sys.executable, str(serve_script), "--port", str(port)]
    if proj_dir:
        cmd.extend(["--project", proj_dir])

    click.echo(f"  Starting server on port {port}...")
    subprocess.run(cmd)


@cli.command()
@click.option("--project", "-p", "project_dir", default=None, help="Path to project directory")
@click.option("--output", "-o", default=None, help="Output video path (default: project_dir/output/video.mp4)")
@click.option("--fps", default=30, type=int, help="Frames per second (default: 30)")
@click.option("--width", default=1920, type=int, help="Video width (default: 1920)")
@click.option("--height", default=1080, type=int, help="Video height (default: 1080)")
@click.option("--mood", default=None, type=click.Choice(["dark_moody", "bright_poppy", "warm_intimate", "cool_ethereal", "high_energy"]), help="Generate script with mood preset before rendering")
@click.option("--base-color", default=None, help="Generate script with base color hex before rendering")
@click.option("--variance", default=None, type=click.Choice(["auto", "low", "medium", "high"]), help="Section variation level (default: auto)")
@click.option("--start", "time_start", default=None, type=float, help="Start time in seconds (for previewing a section)")
@click.option("--end", "time_end", default=None, type=float, help="End time in seconds (for previewing a section)")
@click.option("--intro-image", default=None, help="Branded intro image path (shown before lyrics)")
@click.option("--intro-title", default=None, help="Title text overlaid on intro image (default: project name)")
@click.option("--intro-subtitle", default=None, help="Subtitle text shown after intro fades")
@click.option("--broll", "broll_images", multiple=True, help="B-roll image path(s), layered under gradients/animations")
@click.option("--broll-mode", "broll_mode", default="section", type=click.Choice(["section", "beat"]), help="B-roll distribution: section (round-robin) or beat (cycle on beats)")
@click.option("--broll-blend", "broll_blend", default=0.35, type=float, help="B-roll blend opacity under section gradients (default: 0.35)")
def render(project_dir, output, fps, width, height, mood, base_color, variance, time_start, time_end,
           intro_image, intro_title, intro_subtitle, broll_images, broll_mode, broll_blend):
    """Render the final video (Stage 6)."""
    from render.renderer import VideoRenderer

    proj_dir = _find_project(project_dir)
    proj = MusicVideoProject.load(proj_dir)

    data_dir = proj.data_dir
    if not (data_dir / "lyrics_synced.json").exists():
        raise click.ClickException("lyrics_synced.json not found. Run sync first.")

    needs_script = mood or base_color or variance or intro_image or broll_images or not (data_dir / "script.json").exists()
    if needs_script:
        from scriptgen import generate_script as gen

        click.echo(f"\n  Generating visual script...")
        click.echo(f"    Mood: {mood or 'auto (dark_moody)'}")
        if base_color:
            click.echo(f"    Base color: {base_color}")
        click.echo(f"    Variance: {variance or 'auto'}")

        intro_cfg = None
        if intro_image:
            p = Path(intro_image)
            if not p.is_absolute():
                p = (proj_dir / intro_image).resolve()
            intro_cfg = {
                "image": str(p),
                "title": intro_title,
                "subtitle": intro_subtitle or "",
            }
            click.echo(f"    Intro: {p.name}")

        broll_cfg = None
        if broll_images:
            resolved = []
            for bp in broll_images:
                p = Path(bp)
                if not p.is_absolute():
                    p = (proj_dir / bp).resolve()
                resolved.append(str(p))
            broll_cfg = {
                "images": resolved,
                "mode": broll_mode,
                "blend": broll_blend,
            }
            click.echo(f"    B-roll: {len(resolved)} image(s), mode={broll_mode}, blend={broll_blend}")

        result = gen(proj_dir, mood=mood, base_color=base_color, variance=variance or "auto",
                     intro=intro_cfg, broll=broll_cfg)
        script_path = data_dir / "script.json"
        script_path.write_text(json.dumps(result.script, indent=2, ensure_ascii=False), encoding="utf-8")

        click.echo(f"    Sections: {result.sections_profiled} | Variance: {result.variance_detected} | Mood: {result.mood_used}")

    if output:
        out_path = Path(output)
    elif time_start is not None or time_end is not None:
        out_dir = proj_dir / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        s = f"{time_start:.1f}" if time_start is not None else "0"
        e = f"{time_end:.1f}" if time_end is not None else "end"
        out_path = out_dir / f"preview_{s}-{e}.mp4"
    else:
        out_dir = proj_dir / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "video.mp4"

    click.echo(f"\n  Rendering video...")
    click.echo(f"    Resolution: {width}x{height}")
    click.echo(f"    FPS: {fps}")
    if time_start is not None or time_end is not None:
        click.echo(f"    Time range: {time_start or 0:.1f}s - {time_end or 'end'}s")
    click.echo(f"    Output: {out_path}")

    renderer = VideoRenderer(proj_dir, width=width, height=height, fps=fps)
    renderer.load()

    audio_path = renderer.audio_path
    if not audio_path:
        audio_rel = proj.paths.audio
        if audio_rel:
            candidate = Path(audio_rel)
            if not candidate.is_absolute():
                candidate = proj_dir / audio_rel
            if candidate.exists():
                audio_path = candidate

    click.echo(f"    Duration: {_format_duration(renderer.duration)} ({renderer.duration:.1f}s)")
    click.echo(f"    Audio: {audio_path.name if audio_path else 'none'}")

    total_frames = int(renderer.duration * fps) + 1
    click.echo(f"    Frames: {total_frames}")
    click.echo()

    renderer.render(out_path, audio_path=audio_path, time_start=time_start, time_end=time_end)

    size_mb = out_path.stat().st_size / (1024 * 1024)
    click.echo(f"\n  Done! {out_path} ({size_mb:.1f} MB)")
    proj.stages.mark_complete("render")
    proj.save()


if __name__ == "__main__":  # pragma: no cover
    cli()
