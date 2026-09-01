# Cool Dog section palette

Deterministic instrumental sketches for twelve song functions. This palette continues the **original** minor-bounce Motif A from the earlier experiment and introduces an original Motif B for “Steward of the Shards.” It does not reproduce or interpolate the melody of the referenced commercial composition.

Every section folder contains WAV, MP3, MIDI, and `section.json`. The manifest records tempo, mode, chord voicings (as MIDI pitches), motif treatment, instrumentation, event counts, duration, endpoint continuity, and WAV checksum.

## Regenerate

From the `content-tools` root:

```bash
python3 projects/cool-dog/experiments/section-palette/render_palette.py
```

Dependencies: Python 3, NumPy, SciPy, mido, and FFmpeg with libmp3lame. Synthesis and percussion seeds are fixed; no text-to-music model is used.

## Motifs

- Motif A / Cool Dog: compact staccato E-minor cell carried from `minor-bounce`, transformed through fragmentation, augmentation, reharmonization, octave displacement, and counterpoint.
- Motif B / Steward: rising fifth and inward semitone followed by an open ascent. It debuts in section 7 and progressively combines with A.

## Rights note

Internal development/demo material. The project context references a rights-sensitive third-party composition, but this delivered palette uses original melodic note data. No public-distribution clearance is asserted; normal legal/project review remains necessary.
