# Cool Dog Minor Bounce — deterministic source loop

This is an **original, internal Cool Dog development/demo asset**. It was created in response to a request referencing a rights-sensitive commercial composition, but it does **not** reproduce or interpolate that composition's melody. Do not relabel it as an authorized derivative or imply clearance of third-party music rights.

- Tempo: 124 BPM
- Key/mode: E Aeolian, with chromatic D-sharp approach tones
- Length: 12 bars / 23.2258 seconds
- Instrumentation: additive synth lead, restrained sine-harmonic bass, primitive FM-like blips, synthesized kick and high-passed noise hats
- Musical treatment: playful staccato eighth-note cells, minor-third and seventh motion, chromatic turnaround, octave lift, four-bar bass cycle, and sparse arcade call-and-response
- Loop design: all voices have zero-ended envelopes, there is no reverb or delay, no fade is applied, and the twelve-bar ending points directly back to beat one

The note data lives in `render_loop.py` as beat/pitch/duration tuples and compact eighth-note pitch sequences. MIDI note numbers make the melody and harmony directly inspectable and editable.

## Regenerate

From the `content-tools` repository root:

```bash
python3 projects/cool-dog/experiments/minor-bounce/render_loop.py
```

Requirements already present in the development environment: Python 3, NumPy, SciPy, mido, and FFmpeg with `libmp3lame`.

The command deterministically renders four candidates, their MIDI files, `validation.json`, and copies the selected candidate to `cooldog_minor_bounce_final.{wav,mp3,mid}`.

## Candidates

1. `a_aeolian_skip`: straight 122 BPM Aeolian, driest and simplest.
2. `b_dorian_arcade`: 126 BPM Dorian with a brighter sixth, swing, and answer bleeps.
3. `c_phrygian_wink`: 120 BPM flattened-second color; stranger and more angular.
4. `d_aeolian_bounce` (selected): 124 BPM Aeolian, light swing, chromatic turnaround, octave variation, and restrained bleeps. It best balances mischievous minor color with a buoyant game-loop feel.

## Rights note

Internal prototype only. Rights-sensitive project context; no public distribution authorization is asserted. The delivered melody is original and should still receive normal project/legal review before release.
