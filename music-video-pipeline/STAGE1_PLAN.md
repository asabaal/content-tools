# Stage 1 (Ingest) + Stage 2 (Analyze) Implementation Plan

**Status**: COMPLETE
**Tests**: 265 passed, 100% coverage
**Type**: CLI (`mvp init`, `mvp analyze`, `mvp info`)

---

## User Stories

**US-1.1**: As a creator with a Suno output directory, I want to point the pipeline at my data folder and have it discover all available inputs (audio, stems, MIDI, lyrics), so I don't need to specify each file individually.

**US-1.2**: As a creator with just an MP3 and lyrics file, I want to provide explicit file paths, so the pipeline works with any audio source.

**US-1.3**: As a creator, I want the pipeline to tell me what it found and what tier of analysis is available, so I know what capabilities are enabled.

**US-2.1**: As a creator, I want the pipeline to analyze my audio with the best available data — using MIDI tempo when available, per-stem energy profiles when stems are present — so later stages produce the best results.

**US-2.2**: As a creator, I want lyrics with section markers (like `[Verse]`) to be parsed correctly, so sections aren't counted as lyric lines and word counts are accurate.

**US-2.3**: As a creator, I want to create an instrumental video, running analysis without lyrics.

---

## User Journeys

### Journey A: Suno output directory (full tier)
```
$ mvp init --name "I Never Asked To Be Queer" --data-dir ./data/i-never-asked-to-be-queer

  Project: "I Never Asked To Be Queer"
  Location: /path/to/project

  Running ingest...
    Input tier: full
    Audio: found
    Lyrics: found
    Stems: 8
    MIDI: 8
    Tempo-locked stems: yes

  Analyzing audio: I Never Asked To Be Queer.wav
    Duration:  2:36 (156.1s)
    BPM:       104 (from MIDI)
    Beats:     261
    Onsets:    729
    Stems analyzed: 8

  Importing lyrics: lyrics.txt
    Format: TXT
    Lines: 49, Words: 404
    Sections: 9 (intro, intro, verse, verse_2, verse_3, verse_4, verse_5, outro, ...)
    Time range: 0:00 - 2:33

  Saved: mvp_project.json
  Next: Run `mvp sync` to align lyrics to audio.
```

### Journey B: Basic audio + lyrics
```
$ mvp init --name "My Song" --audio song.mp3 --lyrics lyrics.srt

  Project: "My Song"
  Location: /path/to/project
  Created project structure.

  Running ingest...
    Input tier: standard
    Audio: found
    Lyrics: found
    Stems: 0
    MIDI: 0

  Analyzing audio: song.mp3
    Duration:  3:28 (208.4s)
    BPM:       124
    Beats:     431
    Onsets:    892

  Importing lyrics: lyrics.srt
    Format: SRT
    Lines: 24, Words: 187
    Time range: 0:01 - 3:25

  Next: Run `mvp sync` to align lyrics to audio.
```

### Journey C: Instrumental (no lyrics)
```
$ mvp init --name "Beat Track" --audio song.mp3

  Analyzing audio: song.mp3
  ...
  Lyrics: none (instrumental mode)
```

### Journey D: Inspect project
```
$ mvp info

  Project: "I Never Asked To Be Queer"
  Input tier: full
  Audio: 2:36, 104 BPM (from MIDI), 261 beats
  Lyrics: TXT, 49 lines, 404 words, 9 sections
  Pipeline: [✓] ingest [✓] analyze [ ] sync [ ] structure [ ] design [ ] render
  Next: Run `mvp sync`
```

---

## Workflows

### W-1.1: Ingest (`mvp init`)

```
1. Validate inputs
   - If --data-dir: directory must exist
   - If --audio/--lyrics: files must exist, supported formats
   - Fail fast with clear errors

2. Create project directory structure
   - data/raw/, data/assets/, data/output/, data/cache/

3. Copy explicit files to data/raw/ (if using --audio/--lyrics)
   Store data_dir path if using --data-dir

4. Scan for inputs (from data_dir or raw/):
   a. Find audio file (prefer WAV > FLAC > MP3)
   b. Find lyrics file (first .srt/.lrc/.txt)
   c. Find stem ZIPs (filenames containing "Stems")
   d. Find MIDI ZIPs (filenames containing "MIDI")
   e. Detect tempo-locked stems ("(NNNBPM)" in filename)

5. Extract archives:
   a. Preferred stem ZIP: tempo-locked > first regular
   b. Extract to data/cache/stems/ and data/cache/midi/
   c. Parse stem names ("0 Lead Vocals.wav" → type="lead_vocals")
   d. Parse MIDI instrument names ("Song (Vocals).mid" → "Vocals")

6. Determine input tier (basic/standard/enhanced/full)

7. Write ingest.json

8. Auto-run W-2.1 and W-2.2 unless --no-analyze
```

### W-2.1: Audio Analysis (`mvp analyze`)

```
1. Load project state + ingest.json

2. Full mix analysis (librosa):
   - Beat detection, onset detection
   - RMS energy (normalized 0-1)
   - Spectral centroids (normalized 0-1)
   - Zero crossing rate
   - Waveform peaks (100/sec)

3. If MIDI available:
   - Extract tempo via pretty_midi
   - Use as authoritative BPM (replaces librosa estimate)

4. If stems available:
   - Per-stem analysis: energy profile, onset count
   - Stored in AudioFeatures.stem_features

5. Save analysis.json, waveforms.json

6. Update project audio_info (with midi_bpm if available)
```

### W-2.2: Lyrics Import

```
1. Detect format from extension (.srt/.lrc/.txt)

2. Parse into LyricLine[] with LyricWord[]

3. For TXT format: parse section markers
   - Lines matching [Section Type, tag1, tag2] are parsed as LyricSection
   - Section markers excluded from lines and word counts
   - Each lyric line gets a section reference

4. Validate (at least 1 line for non-sections-only files)

5. Save lyrics_raw.json (includes sections array)

6. Update project lyrics_info (with has_sections, section_count)
```

---

## Output Files

### ingest.json
```json
{
  "tier": "full",
  "audio_path": "/path/to/song.wav",
  "lyrics_path": "/path/to/lyrics.txt",
  "stems": [
    {"name": "Lead Vocals", "stem_type": "lead_vocals", "path": "...", "format": "wav"},
    {"name": "Drums", "stem_type": "drums", "path": "...", "format": "wav"}
  ],
  "midi_files": [
    {"name": "Song (Vocals).mid", "path": "...", "instrument": "Vocals", "note_count": 0, "duration": 0}
  ],
  "has_tempo_locked_stems": true
}
```

### analysis.json
```json
{
  "duration": 156.12,
  "sample_rate": 48000,
  "bpm": 103.8,
  "midi_tempo": 103.8,
  "beat_confidence": 0.34,
  "beat_times": [0.46, 0.94, ...],
  "onset_times": [0.01, 0.12, ...],
  "rms_energy": [0.0, ...],
  "spectral_centroids": [0.0, ...],
  "zero_crossing_rate": [0.0, ...],
  "frame_rate": 93.8,
  "hop_length": 512,
  "n_fft": 2048,
  "stem_features": [
    {"stem_type": "lead_vocals", "name": "Lead Vocals", "energy": 0.297, "onset_count": 559}
  ]
}
```

### waveforms.json
```json
{
  "peaks_per_second": 100,
  "duration": 156.12,
  "total_peaks": 15612,
  "peaks": [0.0123, 0.0456, ...]
}
```

### lyrics_raw.json
```json
{
  "format": "txt",
  "source_file": "lyrics.txt",
  "total_lines": 49,
  "total_words": 404,
  "has_sections": true,
  "section_count": 9,
  "lines": [
    {
      "index": 0,
      "text": "I never asked to be queer",
      "start": 0.0,
      "end": 3.0,
      "words": [...],
      "section": {"section_type": "intro", "index": null, "tags": []}
    }
  ],
  "sections": [
    {"raw_marker": "Intro, swooshy", "section_type": "intro", "index": null, "tags": ["swooshy"]},
    {"raw_marker": "Verse 3, double time, female", "section_type": "verse", "index": 3, "tags": ["double_time", "female"]}
  ]
}
```

### mvp_project.json
```json
{
  "schema_version": "1.0",
  "name": "I Never Asked To Be Queer",
  "artist": "",
  "created": "2026-05-06T10:00:00",
  "modified": "2026-05-06T10:00:00",
  "paths": {
    "audio": null,
    "lyrics": null,
    "data_dir": "/path/to/suno-output"
  },
  "input_tier": "full",
  "audio_info": {
    "duration": 156.12,
    "bpm": 103.8,
    "sample_rate": 48000,
    "beat_count": 261,
    "onset_count": 729,
    "midi_bpm": 103.8
  },
  "lyrics_info": {
    "total_lines": 49,
    "total_words": 404,
    "format": "txt",
    "first_line_time": 0.0,
    "last_line_time": 147.0,
    "has_sections": true,
    "section_count": 9
  },
  "stages": {
    "ingest": "complete",
    "analyze": "complete",
    "sync": "pending",
    "structure": "pending",
    "design": "pending",
    "render": "pending"
  }
}
```

---

## Module Files

| File | Responsibility |
|------|---------------|
| `src/pipeline/models.py` | Project state, InputTier, StemInfo, MidiFileInfo, IngestResult, stage tracking |
| `src/audio/features.py` | AudioFeatures, BeatInfo, StemFeatures dataclasses |
| `src/audio/ingest.py` | Input discovery, ZIP extraction, tier detection |
| `src/audio/analyzer.py` | Full mix analysis + per-stem analysis |
| `src/audio/midi.py` | MIDI tempo/note extraction via pretty_midi |
| `src/lyrics/parser.py` | SRT/LRC/TXT parsing with section marker support |
| `src/cli/commands.py` | Click CLI: init (with --data-dir), analyze, info commands |

---

## Test Files

| File | Count | Coverage |
|------|-------|----------|
| `tests/test_models.py` | Tests for InputTier, StemInfo, MidiFileInfo, IngestResult, ProjectPaths, StageStatus, MusicVideoProject | 100% |
| `tests/test_features.py` | Tests for BeatInfo, FrequencyBands, StemFeatures, AudioFeatures | 100% |
| `tests/test_analyzer.py` | Tests for AudioAnalyzer load, analyze, stem analysis, waveforms | 100% |
| `tests/test_ingest.py` | Tests for input discovery, ZIP extraction, tier detection, tempo-locked detection | 100% |
| `tests/test_midi.py` | Tests for MidiNote, MidiInstrument, MidiAnalysis, analyze_midi, extract_tempo | 100% |
| `tests/test_parser.py` | Tests for section markers, SRT, LRC, TXT, LyricSection, LyricLine | 100% |
| `tests/test_cli.py` | Tests for init, analyze, info commands including --data-dir mode | 100% |
| `tests/test_coverage_gaps.py` | Edge cases: MIDI without pretty_midi, stem analysis, CWD discovery, integration | 100% |

**Total**: 265 tests, 100% statement coverage

---

## Error Handling

| Error | Response |
|-------|----------|
| Data directory not found | Graceful: returns basic tier with no inputs |
| Audio not found | "No audio file found in project" |
| Unsupported audio format | "Unsupported format: .{ext}. Supported: mp3, wav, flac, ogg, m4a" |
| Lyrics not found | "Lyrics file not found: {path}" |
| Unsupported lyrics format | "Unsupported format: .{ext}. Supported: srt, lrc, txt" |
| Empty lyrics | "WARNING: No lyric lines parsed from file" |
| No project | "No project found. Run `mvp init` first." |
| pretty_midi not installed | Graceful: MIDI analysis returns empty, logs warning |
| Corrupt ZIP | Standard Python zipfile error propagated |
