# tools/06-song-ingest — Local Music Ingestion / Ownership Pipeline

Turn a song folder (full WAV + stems + optional reference MIDIs + lyrics)
into a machine-readable analysis package **without depending on any
vendor's per-stem extraction interface**.

Part of content-tools' music toolchain. Source *discovery* reuses the
existing `music-video-pipeline` ingestion architecture
(`audio.ingest.discover_inputs`); vocal transcription reuses
`music-video-pipeline/src/audio/analyzer.py::AudioAnalyzer.transcribe_vocal_stem`
(faster-whisper, word timestamps). Instrument detection and WAV→MIDI are
new, built behind swappable backend interfaces.

## Provenance rules

* Reference MIDIs (e.g. manually extracted Suno MIDI) are **reference
  artifacts, not ground truth**. Local transcription and reference
  transcription are preserved side-by-side as two independent readings of
  the same material; comparisons may favor either.
* Raw model output is never overwritten by reconciliation. Both forms are
  stored.
* Every derived artifact records: generator + version, model/backend +
  version, parameters, input file, timestamp.

## Environment

Uses the shared music analysis environment (has basic-pitch 0.4.0,
faster-whisper, crepe, librosa, pretty_midi; now also panns-inference):

```bash
PYTHON=/mnt/storage/python_env/basic_audio_env/bin/python
```

Extra deps for this tool (`requirements.txt` here). PANNs downloads
`Cnn14_mAP=0.431.pth` (~300 MB) to `~/panns_data/` on first use.

## Usage

```bash
$PYTHON -m song_ingest.cli ingest "projects/hippie-activist."            # full vertical slice
$PYTHON -m song_ingest.cli ingest <dir> --stages detect,reconcile        # subset
$PYTHON -m song_ingest.cli detect "file.wav"                             # single-file debug
```

`ingest-song` alias: `python tools/06-song-ingest/ingest_song.py <dir>`.

## Stages

1. `discover`  — inventory sources via `audio.ingest` (reuse) + sha256 manifest
2. `detect`    — instrument detection on full mix + every stem (PANNs Cnn14, CUDA)
3. `reconcile` — full-mix vs stem-union reconciliation; stem-label vs content checks
4. `midi`      — Basic Pitch transcription of pitched instrumental stems
5. `vocals`    — faster-whisper transcription of lead / backing / combined vocals
6. `compare`   — local-vs-reference MIDI metrics + reference↔stem correlation
7. `manifest`  — final `manifest.json` + `ANALYSIS_REPORT.md`

Output lands in `<project>/analysis/`, `<project>/derived/`,
`<project>/manifest.json`, `<project>/ANALYSIS_REPORT.md`.

## Design notes

* Detector interface (`song_ingest/detectors.py`): any backend returns
  clipwise (song-level) + temporal (time-localized) evidence with
  provenance. PANNs is the V0 backend; Essentia MTG-Jamendo and CLAP are
  intended future backends behind the same interface (not installed yet —
  Essentia's instrumentation models need TensorFlow; CLAP needs
  transformers; both evaluate later).
* Transcription backend interface (`song_ingest/transcribe_midi.py`):
  Basic Pitch is the V0 default; the interface exists so backends can be
  benchmarked/swapped.
* Stem filenames are treated as **claims**, never as truth.
