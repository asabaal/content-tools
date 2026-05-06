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
        proj.paths.audio = result.audio_path

    if result.lyrics_path and not proj.paths.lyrics:
        proj.paths.lyrics = result.lyrics_path

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

    click.echo(f"\n  Analyzing audio: {audio_path.name}")

    analyzer = AudioAnalyzer()
    features = analyzer.analyze(audio_path)
    peaks, _ = analyzer.generate_waveforms()

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

    if ingest_data and ingest_data.get("stems"):
        stem_features = []
        for sf in ingest_data["stems"]:
            spath = sf.get("path", "")
            if spath and Path(spath).exists():
                sf_result = analyzer.analyze_stem(spath, sf.get("stem_type", ""), sf.get("name", ""))
                stem_features.append(sf_result)
        features.stem_features = stem_features

    if midi_tempo is not None:
        features.midi_tempo = midi_tempo

    proj.data_dir.mkdir(parents=True, exist_ok=True)

    analysis_data = features.to_dict()
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

    if verbose:
        click.echo(f"    Sample rate: {features.sample_rate} Hz")
        click.echo(f"    Frames: {len(features.rms_energy)} @ {features.frame_rate:.1f}/s")
        click.echo(f"    Waveform peaks: {len(peaks)}")

    click.echo(f"    Saved: analysis.json, waveforms.json")


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

    syncer = LyricSynchronizer(lines, features)
    result = syncer.synchronize()

    result.save(proj.data_dir / "lyrics_synced.json")

    proj.stages.mark_complete("sync")

    click.echo(f"    Lines synced: {len(result.lines)}")
    click.echo(f"    Source: {result.source}")
    click.echo(f"    Avg confidence: {result.avg_confidence:.0%}")

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


if __name__ == "__main__":  # pragma: no cover
    cli()
