# Suno Rendering Prompt Book — The Steward's Calibration

_Generated 2026-09-13T18:57:09.141717+00:00 · 90 targets · 180 prompts · all validated at 900–1000 characters inclusive characters._

## What this piece is and why it exists

This is the ONE canonical reference composition of the Suno Target Reference Corpus. It is a 4:48 instrumental calibration suite: you will render the SAME piece repeatedly, once per Suno Advanced Split target, so the resulting audio differs (as much as Suno permits) only in the requested instrument/timbre. Those renders become the reference exemplars that let us decide which Suno extraction targets are actually present in unknown songs — including `projects/hippie-activist./`.

## Composition structure (invariant across ALL renders)

- Tempo/meter: 100 BPM, 4/4, 288 seconds, 120 bars, nine movements:

  * **I. Majors Parade — one bar per major key** — 0s–29s (coverage: all_12_major_keys, progression_I_IV_V_I, major_triads, full_chordal, mid_register)
  * **II. Minors Parade — one bar per minor key (harmonic minor V)** — 29s–58s (coverage: all_12_minor_keys, minor_cadence_i_iv_V_i, minor_triads, harmonic_minor_seventh, full_chordal)
  * **III. Scales, Intervals, Registers** — 58s–115s (coverage: major_scale, natural_minor_scale, harmonic_minor_scale, melodic_minor_scale, chromatic_run, stepwise_melody, intervallic_melody, intervals_2nds_through_octaves, repeated_notes, register_sweep, low_register, high_register, isolated_notes, monophonic)
  * **IV. Progression Journey (ii-V-I, pop loops, blues, modulation)** — 115s–154s (coverage: progression_ii_V_I, progression_I_V_vi_IV, progression_vi_IV_I_V, blues_movement, dominant_sevenths, controlled_modulation)
  * **V. Counterpoint, Voicings, Articulation** — 154s–192s (coverage: polyphonic_counterpoint, dyads, dense_voicings, sparse_voicings, sustained_legato, staccato, syncopation, sparse_accompaniment, dense_accompaniment)
  * **VI. Two Solos** — 192s–221s (coverage: solo_passage_1, solo_passage_2, arpeggios, intervallic_melody, register_sweep, sparse_accompaniment)
  * **VII. Bass Behavior** — 221s–240s (coverage: bass_walking, low_register, repeated_notes, sustained_legato)
  * **VIII. Percussion, FX, Vocal-role behavior** — 240s–259s (coverage: percussion_rhythmic, syncopation, fx_transition_gestures, vocal_role_sustained)
  * **IX. Finale — modulation climb and dense climax** — 259s–288s (coverage: controlled_modulation, dense_climax, dominant_sevenths, full_chordal, sustained_legato)

### Key journey

Majors Parade visits all 12 major keys (circle of fifths, C → Ab); Minors Parade visits all 12 minor keys with harmonic-minor dominants; the Progression Journey modulates C → F → G and runs an A blues; the Finale climbs C → D and closes with an E-minor cadence.

### What each render must keep (invariants)

Same movement order and boundaries; same 100 BPM; same harmonic and key journey; same melodic contours; same two solos; same dense-finale climax logic; calibration passages (scales, intervals, counterpoint, voicings, registers, articulations) must stay audible. Only the dominant instrument/timbre changes per target.

## Prompts

Paste MAIN into Suno's main/style field and EXCLUDE into the exclude/avoid field. Character counts (exact, spaces included) are printed beside each prompt — both must be 900–1000.

## TARGET: Accordion (`accordion`)  [beta]
_category: other · Accordion_

🟣 MAIN — 932 characters ✓
```text
TARGET INSTRUMENT: Accordion. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Render with the requested instrument as the sole melodic and harmonic voice: follow the movement map exactly, translate chord passages into idiomatic voicing, keep every calibration passage audible. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 938 characters ✓
```text
EXCLUDE for the Accordion render of 'The Steward's Calibration'. No other instrument takes the lead — especially Other, Harmonica, Bagpipes, Didgeridoo. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Acoustic guitar (`acoustic_guitar`)
_category: guitar · Acoustic guitar_

🟣 MAIN — 981 characters ✓
```text
TARGET INSTRUMENT: Acoustic guitar. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Guitar feature: strummed or picked chord realizations of the harmony movements, single-note scale and solo runs with bends only where the harmony allows, dual-voice flatpicking for counterpoint, low-string work for the walking-bass movement. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 912 characters ✓
```text
EXCLUDE for the Acoustic guitar render of 'The Steward's Calibration'. No other instrument takes the lead — especially Electric guitar, Guitar, Lead guitar, Rhythm electric guitar, Rhythm acoustic guitar, Slide guitar, Ukulele, electric guitar. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Alto saxophone (`alto_saxophone`)  [beta]
_category: woodwind · Alto saxophone_

🟣 MAIN — 925 characters ✓
```text
TARGET INSTRUMENT: Alto saxophone. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 930 characters ✓
```text
EXCLUDE for the Alto saxophone render of 'The Steward's Calibration'. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Tenor saxophone, Saxophone, Oboe, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Arpeggiator (`arpeggiator`)  [beta]
_category: synth · Arpeggiated synth pattern_

🟣 MAIN — 983 characters ✓
```text
TARGET INSTRUMENT: Arpeggiator (Arpeggiated synth pattern). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Arpeggiator render of 'The Steward's Calibration'. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Risers, Synth strings, Synth lead, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Backing vocal (`backing_vocal`)
_category: vocal · Secondary or harmony vocal parts_

🟣 MAIN — 977 characters ✓
```text
TARGET INSTRUMENT: Backing vocal (Secondary or harmony vocal parts). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Vocal feature: sing the lead melody throughout, deliver movement VIII's motif as sustained legato 'ah' lines, layer movement V chords as 'ooh' pads, and render the percussion movement as vocal percussion. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 914 characters ✓
```text
EXCLUDE for the Backing vocal render of 'The Steward's Calibration'. No other instrument takes the lead — especially Lead vocal, Vocoder, Choir, Whistle. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Bagpipes (`bagpipes`)  [beta]
_category: other · Bagpipes_

🟣 MAIN — 931 characters ✓
```text
TARGET INSTRUMENT: Bagpipes. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Render with the requested instrument as the sole melodic and harmonic voice: follow the movement map exactly, translate chord passages into idiomatic voicing, keep every calibration passage audible. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 938 characters ✓
```text
EXCLUDE for the Bagpipes render of 'The Steward's Calibration'. No other instrument takes the lead — especially Other, Accordion, Harmonica, Didgeridoo. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Banjo (`banjo`)  [beta]
_category: strings · Banjo_

🟣 MAIN — 923 characters ✓
```text
TARGET INSTRUMENT: Banjo. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 902 characters ✓
```text
EXCLUDE for the Banjo render of 'The Steward's Calibration'. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Cello, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Baritone saxophone (`baritone_saxophone`)  [beta]
_category: woodwind · Baritone saxophone_

🟣 MAIN — 929 characters ✓
```text
TARGET INSTRUMENT: Baritone saxophone. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 930 characters ✓
```text
EXCLUDE for the Baritone saxophone render of 'The Steward's Calibration'. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Tenor saxophone, Saxophone, Oboe, Alto saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Bass (`bass`)
_category: bass · Bass instrument, part, or line (broad)_

🟣 MAIN — 953 characters ✓
```text
TARGET INSTRUMENT: Bass (Bass instrument, part, or line (broad)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Bass feature: carry every harmony as bass lines, feature movement VII's walking bass, octave pops and low pedal, keep the finale bass prominent, stay low with the melody hinted above. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 955 characters ✓
```text
EXCLUDE for the Bass render of 'The Steward's Calibration'. No other instrument takes the lead — especially Upright bass, Bass guitar, 808, synth bass, eight zero eight. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Bass guitar (`bass_guitar`)  [beta]
_category: bass · Electric bass guitar_

🟣 MAIN — 942 characters ✓
```text
TARGET INSTRUMENT: Bass guitar (Electric bass guitar). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Bass feature: carry every harmony as bass lines, feature movement VII's walking bass, octave pops and low pedal, keep the finale bass prominent, stay low with the melody hinted above. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 925 characters ✓
```text
EXCLUDE for the Bass guitar render of 'The Steward's Calibration'. No other instrument takes the lead — especially Bass, Upright bass, 808. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Bassoon (`bassoon`)  [beta]
_category: woodwind · Bassoon_

🟣 MAIN — 918 characters ✓
```text
TARGET INSTRUMENT: Bassoon. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 930 characters ✓
```text
EXCLUDE for the Bassoon render of 'The Steward's Calibration'. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Tenor saxophone, Saxophone, Oboe, Alto saxophone, Baritone saxophone. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Bells (`bells`)  [beta]
_category: percussion · General bell sounds / glockenspiel-like_

🟣 MAIN — 989 characters ✓
```text
TARGET INSTRUMENT: Bells (General bell sounds / glockenspiel-like). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Bells render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Shaker, Glockenspiel, Timpani. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Bongos (`bongos`)  [beta]
_category: percussion · Bongos_

🟣 MAIN — 948 characters ✓
```text
TARGET INSTRUMENT: Bongos. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 935 characters ✓
```text
EXCLUDE for the Bongos render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Brass (`brass`)
_category: brass · Brass instruments (broad)_

🟣 MAIN — 920 characters ✓
```text
TARGET INSTRUMENT: Brass (Brass instruments (broad)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Brass feature: bold chorale chords in harmony movements, fanfare-style phrasing of scales and intervals, marcato staccato attacks, smooth controlled legato solos. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 932 characters ✓
```text
EXCLUDE for the Brass render of 'The Steward's Calibration'. No other instrument takes the lead — especially Trumpet, Trombone, French horn, Tuba. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Celesta (`celesta`)  [beta]
_category: keyboard · Celesta_

🟣 MAIN — 937 characters ✓
```text
TARGET INSTRUMENT: Celesta. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 960 characters ✓
```text
EXCLUDE for the Celesta render of 'The Steward's Calibration'. No other instrument takes the lead — especially Piano, Organ, Electric piano, Keyboards, Harpsichord, Melodica. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Cello (`cello`)  [beta]
_category: strings · Cello_

🟣 MAIN — 923 characters ✓
```text
TARGET INSTRUMENT: Cello. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 902 characters ✓
```text
EXCLUDE for the Cello render of 'The Steward's Calibration'. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Banjo, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Choir (`choir`)  [beta]
_category: vocal · Choral or ensemble vocals_

🟣 MAIN — 962 characters ✓
```text
TARGET INSTRUMENT: Choir (Choral or ensemble vocals). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Vocal feature: sing the lead melody throughout, deliver movement VIII's motif as sustained legato 'ah' lines, layer movement V chords as 'ooh' pads, and render the percussion movement as vocal percussion. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 937 characters ✓
```text
EXCLUDE for the Choir render of 'The Steward's Calibration'. No other instrument takes the lead — especially Lead vocal, Backing vocal, Vocoder, Whistle, lead vocal, synth pad. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Clap (`clap`)  [beta]
_category: percussion · Hand claps / drum machine clap_

🟣 MAIN — 979 characters ✓
```text
TARGET INSTRUMENT: Clap (Hand claps / drum machine clap). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 933 characters ✓
```text
EXCLUDE for the Clap render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Clarinet (`clarinet`)  [beta]
_category: woodwind · Clarinet_

🟣 MAIN — 919 characters ✓
```text
TARGET INSTRUMENT: Clarinet. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 930 characters ✓
```text
EXCLUDE for the Clarinet render of 'The Steward's Calibration'. No other instrument takes the lead — especially Woodwinds, Flute, Tenor saxophone, Saxophone, Oboe, Alto saxophone, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Congas (`congas`)  [beta]
_category: percussion · Congas_

🟣 MAIN — 948 characters ✓
```text
TARGET INSTRUMENT: Congas. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 935 characters ✓
```text
EXCLUDE for the Congas render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Cowbell (`cowbell`)  [beta]
_category: percussion · Cowbell_

🟣 MAIN — 949 characters ✓
```text
TARGET INSTRUMENT: Cowbell. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Cowbell render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Cymbals (`cymbals`)  [beta]
_category: percussion · Cymbals (hi-hat, ride, crash, etc.)_

🟣 MAIN — 987 characters ✓
```text
TARGET INSTRUMENT: Cymbals (Cymbals (hi-hat, ride, crash, etc.)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Cymbals render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Didgeridoo (`didgeridoo`)  [beta]
_category: other · Didgeridoo_

🟣 MAIN — 933 characters ✓
```text
TARGET INSTRUMENT: Didgeridoo. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Render with the requested instrument as the sole melodic and harmonic voice: follow the movement map exactly, translate chord passages into idiomatic voicing, keep every calibration passage audible. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 938 characters ✓
```text
EXCLUDE for the Didgeridoo render of 'The Steward's Calibration'. No other instrument takes the lead — especially Other, Accordion, Harmonica, Bagpipes. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Djembe (`djembe`)  [beta]
_category: percussion · Djembe (African hand drum)_

🟣 MAIN — 977 characters ✓
```text
TARGET INSTRUMENT: Djembe (Djembe (African hand drum)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 935 characters ✓
```text
EXCLUDE for the Djembe render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Double bass (`double_bass`)  [beta]
_category: strings · Double bass (orchestral)_

🟣 MAIN — 956 characters ✓
```text
TARGET INSTRUMENT: Double bass (Double bass (orchestral)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 902 characters ✓
```text
EXCLUDE for the Double bass render of 'The Steward's Calibration'. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Banjo, Cello, Orchestra. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Drone (`drone`)  [beta]
_category: synth · Sustained drone / pedal tone_

🟣 MAIN — 980 characters ✓
```text
TARGET INSTRUMENT: Drone (Sustained drone / pedal tone). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 930 characters ✓
```text
EXCLUDE for the Drone render of 'The Steward's Calibration'. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Risers, Synth strings, Synth lead, Arpeggiator. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Drums (`drums`)
_category: percussion · Drum kit or drum machine (broad)_

🟣 MAIN — 982 characters ✓
```text
TARGET INSTRUMENT: Drums (Drum kit or drum machine (broad)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Drums render of 'The Steward's Calibration'. No other instrument takes the lead — especially Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel, Timpani. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: 808 (`eight_zero_eight`)  [beta]
_category: bass · 808 bass / kick_

🟣 MAIN — 929 characters ✓
```text
TARGET INSTRUMENT: 808 (808 bass / kick). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Bass feature: carry every harmony as bass lines, feature movement VII's walking bass, octave pops and low pedal, keep the finale bass prominent, stay low with the melody hinted above. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 925 characters ✓
```text
EXCLUDE for the 808 render of 'The Steward's Calibration'. No other instrument takes the lead — especially Bass, Upright bass, Bass guitar. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Electric guitar (`electric_guitar`)
_category: guitar · Electric guitar, including lead and rhythm_

🟣 MAIN — 948 characters ✓
```text
TARGET INSTRUMENT: Electric guitar (Electric guitar, including lead and rhythm). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strummed/picked chords for harmony; single-note runs for scales and solos; dual-voice counterpoint. No drift; every calibration passage stays intact; the requested instrument is dominant. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 912 characters ✓
```text
EXCLUDE for the Electric guitar render of 'The Steward's Calibration'. No other instrument takes the lead — especially Acoustic guitar, Guitar, Lead guitar, Rhythm electric guitar, Rhythm acoustic guitar, Slide guitar, Ukulele, acoustic guitar. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Electric piano (`electric_piano`)
_category: keyboard · Electric piano (Rhodes, Wurlitzer, etc.)_

🟣 MAIN — 987 characters ✓
```text
TARGET INSTRUMENT: Electric piano (Electric piano (Rhodes, Wurlitzer, etc.)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 960 characters ✓
```text
EXCLUDE for the Electric piano render of 'The Steward's Calibration'. No other instrument takes the lead — especially Piano, Organ, Keyboards, Celesta, Harpsichord, Melodica. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Fiddle (`fiddle`)  [beta]
_category: strings · Fiddle (violin played in folk style)_

🟣 MAIN — 963 characters ✓
```text
TARGET INSTRUMENT: Fiddle (Fiddle (violin played in folk style)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 902 characters ✓
```text
EXCLUDE for the Fiddle render of 'The Steward's Calibration'. No other instrument takes the lead — especially Strings, Harp, Violin, Mandolin, Banjo, Cello, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Flute (`flute`)  [beta]
_category: woodwind · Flute_

🟣 MAIN — 916 characters ✓
```text
TARGET INSTRUMENT: Flute. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 930 characters ✓
```text
EXCLUDE for the Flute render of 'The Steward's Calibration'. No other instrument takes the lead — especially Woodwinds, Clarinet, Tenor saxophone, Saxophone, Oboe, Alto saxophone, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: French horn (`french_horn`)  [beta]
_category: brass · French horn_

🟣 MAIN — 976 characters ✓
```text
TARGET INSTRUMENT: French horn. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Brass feature: bold chorale chords in harmony movements, fanfare-style phrasing of scales and intervals, marcato staccato attacks, smooth controlled legato solos. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. IX must climb C to D and land the dense final E-minor cadence at full length.
```

🛑 EXCLUDE — 932 characters ✓
```text
EXCLUDE for the French horn render of 'The Steward's Calibration'. No other instrument takes the lead — especially Brass, Trumpet, Trombone, Tuba. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Glockenspiel (`glockenspiel`)  [beta]
_category: percussion · Glockenspiel_

🟣 MAIN — 954 characters ✓
```text
TARGET INSTRUMENT: Glockenspiel. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Glockenspiel render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Timpani. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Guitar (`guitar`)
_category: guitar · Guitar (broad - any type)_

🟣 MAIN — 1000 characters ✓
```text
TARGET INSTRUMENT: Guitar (Guitar (broad - any type)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Guitar feature: strummed or picked chord realizations of the harmony movements, single-note scale and solo runs with bends only where the harmony allows, dual-voice flatpicking for counterpoint, low-string work for the walking-bass movement. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 904 characters ✓
```text
EXCLUDE for the Guitar render of 'The Steward's Calibration'. No other instrument takes the lead — especially Electric guitar, Acoustic guitar, Lead guitar, Rhythm electric guitar, Rhythm acoustic guitar, Slide guitar, Ukulele, ukulele. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Harmonica (`harmonica`)  [beta]
_category: other · Harmonica_

🟣 MAIN — 932 characters ✓
```text
TARGET INSTRUMENT: Harmonica. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Render with the requested instrument as the sole melodic and harmonic voice: follow the movement map exactly, translate chord passages into idiomatic voicing, keep every calibration passage audible. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 938 characters ✓
```text
EXCLUDE for the Harmonica render of 'The Steward's Calibration'. No other instrument takes the lead — especially Other, Accordion, Bagpipes, Didgeridoo. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Harp (`harp`)  [beta]
_category: strings · Harp_

🟣 MAIN — 922 characters ✓
```text
TARGET INSTRUMENT: Harp. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 902 characters ✓
```text
EXCLUDE for the Harp render of 'The Steward's Calibration'. No other instrument takes the lead — especially Strings, Fiddle, Violin, Mandolin, Banjo, Cello, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Harpsichord (`harpsichord`)  [beta]
_category: keyboard · Harpsichord_

🟣 MAIN — 941 characters ✓
```text
TARGET INSTRUMENT: Harpsichord. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 960 characters ✓
```text
EXCLUDE for the Harpsichord render of 'The Steward's Calibration'. No other instrument takes the lead — especially Piano, Organ, Electric piano, Keyboards, Celesta, Melodica. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Hi-hat (`hi_hat`)  [beta]
_category: percussion · Hi-hat (open or closed)_

🟣 MAIN — 974 characters ✓
```text
TARGET INSTRUMENT: Hi-hat (Hi-hat (open or closed)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 935 characters ✓
```text
EXCLUDE for the Hi-hat render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Keyboards (`keyboards`)
_category: keyboard · General keyboard instruments_

🟣 MAIN — 970 characters ✓
```text
TARGET INSTRUMENT: Keyboards (General keyboard instruments). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 960 characters ✓
```text
EXCLUDE for the Keyboards render of 'The Steward's Calibration'. No other instrument takes the lead — especially Piano, Organ, Electric piano, Celesta, Harpsichord, Melodica. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Kick (`kick`)  [beta]
_category: percussion · Kick drum_

🟣 MAIN — 958 characters ✓
```text
TARGET INSTRUMENT: Kick (Kick drum). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Kick render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Snare, Tambourine, Bells, Shaker, Glockenspiel, Timpani. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Koto (`koto`)  [beta]
_category: strings · Koto (Japanese string instrument)_

🟣 MAIN — 958 characters ✓
```text
TARGET INSTRUMENT: Koto (Koto (Japanese string instrument)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 959 characters ✓
```text
EXCLUDE for the Koto render of 'The Steward's Calibration'. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Banjo, Cello, Orchestra. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Lead guitar (`lead_guitar`)
_category: guitar · Lead/featured guitar part_

🟣 MAIN — 927 characters ✓
```text
TARGET INSTRUMENT: Lead guitar (Lead/featured guitar part). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strummed/picked chords for harmony; single-note runs for scales and solos; dual-voice counterpoint. No drift; every calibration passage stays intact; the requested instrument is dominant. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 959 characters ✓
```text
EXCLUDE for the Lead guitar render of 'The Steward's Calibration'. No other instrument takes the lead — especially Electric guitar, Acoustic guitar, Guitar, Rhythm electric guitar, Rhythm acoustic guitar, Slide guitar, Ukulele. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Lead vocal (`lead_vocal`)
_category: vocal · Primary vocal performance, lead singer_

🟣 MAIN — 980 characters ✓
```text
TARGET INSTRUMENT: Lead vocal (Primary vocal performance, lead singer). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Vocal feature: sing the lead melody throughout, deliver movement VIII's motif as sustained legato 'ah' lines, layer movement V chords as 'ooh' pads, and render the percussion movement as vocal percussion. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 930 characters ✓
```text
EXCLUDE for the Lead vocal render of 'The Steward's Calibration'. No other instrument takes the lead — especially Backing vocal, Vocoder, Choir, Whistle, choir, vocoder. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Mandolin (`mandolin`)  [beta]
_category: strings · Mandolin_

🟣 MAIN — 926 characters ✓
```text
TARGET INSTRUMENT: Mandolin. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 902 characters ✓
```text
EXCLUDE for the Mandolin render of 'The Steward's Calibration'. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Banjo, Cello, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Marimba (`marimba`)  [beta]
_category: percussion · Marimba_

🟣 MAIN — 949 characters ✓
```text
TARGET INSTRUMENT: Marimba. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Marimba render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Melodica (`melodica`)  [beta]
_category: keyboard · Melodica_

🟣 MAIN — 938 characters ✓
```text
TARGET INSTRUMENT: Melodica. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 960 characters ✓
```text
EXCLUDE for the Melodica render of 'The Steward's Calibration'. No other instrument takes the lead — especially Piano, Organ, Electric piano, Keyboards, Celesta, Harpsichord. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Music box (`music_box`)  [beta]
_category: percussion · Music box_

🟣 MAIN — 951 characters ✓
```text
TARGET INSTRUMENT: Music box. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 938 characters ✓
```text
EXCLUDE for the Music box render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Oboe (`oboe`)  [beta]
_category: woodwind · Oboe_

🟣 MAIN — 915 characters ✓
```text
TARGET INSTRUMENT: Oboe. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 930 characters ✓
```text
EXCLUDE for the Oboe render of 'The Steward's Calibration'. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Tenor saxophone, Saxophone, Alto saxophone, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Orchestra (`orchestra`)  [beta]
_category: strings · Full orchestral arrangement_

🟣 MAIN — 957 characters ✓
```text
TARGET INSTRUMENT: Orchestra (Full orchestral arrangement). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 902 characters ✓
```text
EXCLUDE for the Orchestra render of 'The Steward's Calibration'. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Banjo, Cello, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Organ (`organ`)
_category: keyboard · Organ (pipe, electric, or digital)_

🟣 MAIN — 972 characters ✓
```text
TARGET INSTRUMENT: Organ (Organ (pipe, electric, or digital)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 923 characters ✓
```text
EXCLUDE for the Organ render of 'The Steward's Calibration'. No other instrument takes the lead — especially Piano, Electric piano, Keyboards, Celesta, Harpsichord, Melodica, electric piano, accordion. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Other (`other`)
_category: other · Elements not matching other targets_

🟣 MAIN — 966 characters ✓
```text
TARGET INSTRUMENT: Other (Elements not matching other targets). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Render with the requested instrument as the sole melodic and harmonic voice: follow the movement map exactly, translate chord passages into idiomatic voicing, keep every calibration passage audible. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 938 characters ✓
```text
EXCLUDE for the Other render of 'The Steward's Calibration'. No other instrument takes the lead — especially Accordion, Harmonica, Bagpipes, Didgeridoo. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Percussion (`percussion`)
_category: percussion · General percussion instruments_

🟣 MAIN — 985 characters ✓
```text
TARGET INSTRUMENT: Percussion (General percussion instruments). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Percussion render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel, Timpani. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Piano (`piano`)
_category: keyboard · Acoustic piano_

🟣 MAIN — 952 characters ✓
```text
TARGET INSTRUMENT: Piano (Acoustic piano). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 925 characters ✓
```text
EXCLUDE for the Piano render of 'The Steward's Calibration'. No other instrument takes the lead — especially Organ, Electric piano, Keyboards, Celesta, Harpsichord, Melodica, electric piano, harpsichord. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Piccolo (`piccolo`)  [beta]
_category: woodwind · Piccolo_

🟣 MAIN — 918 characters ✓
```text
TARGET INSTRUMENT: Piccolo. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 930 characters ✓
```text
EXCLUDE for the Piccolo render of 'The Steward's Calibration'. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Tenor saxophone, Saxophone, Oboe, Alto saxophone, Baritone saxophone. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Rhythm acoustic guitar (`rhythm_acoustic_guitar`)  [beta]
_category: guitar · Acoustic guitar playing rhythm parts_

🟣 MAIN — 949 characters ✓
```text
TARGET INSTRUMENT: Rhythm acoustic guitar (Acoustic guitar playing rhythm parts). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strummed/picked chords for harmony; single-note runs for scales and solos; dual-voice counterpoint. No drift; every calibration passage stays intact; the requested instrument is dominant. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 959 characters ✓
```text
EXCLUDE for the Rhythm acoustic guitar render of 'The Steward's Calibration'. No other instrument takes the lead — especially Electric guitar, Acoustic guitar, Guitar, Lead guitar, Rhythm electric guitar, Slide guitar, Ukulele. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Rhythm electric guitar (`rhythm_electric_guitar`)
_category: guitar · Electric guitar playing rhythm parts_

🟣 MAIN — 949 characters ✓
```text
TARGET INSTRUMENT: Rhythm electric guitar (Electric guitar playing rhythm parts). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strummed/picked chords for harmony; single-note runs for scales and solos; dual-voice counterpoint. No drift; every calibration passage stays intact; the requested instrument is dominant. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 959 characters ✓
```text
EXCLUDE for the Rhythm electric guitar render of 'The Steward's Calibration'. No other instrument takes the lead — especially Electric guitar, Acoustic guitar, Guitar, Lead guitar, Rhythm acoustic guitar, Slide guitar, Ukulele. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Risers (`risers`)  [beta]
_category: synth · Rising tonal or noise sweeps / transition effects_

🟣 MAIN — 950 characters ✓
```text
TARGET INSTRUMENT: Risers (Rising tonal or noise sweeps / transition effects). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Pads/keys for harmony; mono leads for scales and solos; sequenced bass; arpeggiator only where notated. No drift; every calibration passage stays intact; the requested instrument is dominant. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Risers render of 'The Steward's Calibration'. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Synth strings, Synth lead, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Saxophone (`saxophone`)  [beta]
_category: woodwind · Saxophone (broad)_

🟣 MAIN — 940 characters ✓
```text
TARGET INSTRUMENT: Saxophone (Saxophone (broad)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 930 characters ✓
```text
EXCLUDE for the Saxophone render of 'The Steward's Calibration'. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Tenor saxophone, Oboe, Alto saxophone, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Shaker (`shaker`)  [beta]
_category: percussion · Shaker / maraca-style percussion_

🟣 MAIN — 983 characters ✓
```text
TARGET INSTRUMENT: Shaker (Shaker / maraca-style percussion). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Shaker render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Glockenspiel, Timpani. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Sitar (`sitar`)  [beta]
_category: strings · Sitar_

🟣 MAIN — 923 characters ✓
```text
TARGET INSTRUMENT: Sitar. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 960 characters ✓
```text
EXCLUDE for the Sitar render of 'The Steward's Calibration'. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Banjo, Cello, Orchestra. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Slide guitar (`slide_guitar`)  [beta]
_category: guitar · Slide or bottleneck guitar_

🟣 MAIN — 929 characters ✓
```text
TARGET INSTRUMENT: Slide guitar (Slide or bottleneck guitar). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strummed/picked chords for harmony; single-note runs for scales and solos; dual-voice counterpoint. No drift; every calibration passage stays intact; the requested instrument is dominant. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 959 characters ✓
```text
EXCLUDE for the Slide guitar render of 'The Steward's Calibration'. No other instrument takes the lead — especially Electric guitar, Acoustic guitar, Guitar, Lead guitar, Rhythm electric guitar, Rhythm acoustic guitar, Ukulele. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Snare (`snare`)  [beta]
_category: percussion · Snare drum_

🟣 MAIN — 960 characters ✓
```text
TARGET INSTRUMENT: Snare (Snare drum). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Snare render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Tambourine, Bells, Shaker, Glockenspiel, Timpani. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Steel drums (`steel_drums`)  [beta]
_category: percussion · Steel drums / steelpan_

🟣 MAIN — 978 characters ✓
```text
TARGET INSTRUMENT: Steel drums (Steel drums / steelpan). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 940 characters ✓
```text
EXCLUDE for the Steel drums render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Strings (`strings`)
_category: strings · String section or string instruments_

🟣 MAIN — 964 characters ✓
```text
TARGET INSTRUMENT: Strings (String section or string instruments). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 902 characters ✓
```text
EXCLUDE for the Strings render of 'The Steward's Calibration'. No other instrument takes the lead — especially Harp, Fiddle, Violin, Mandolin, Banjo, Cello, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth (`synth`)
_category: synth · General synthesizer (broad)_

🟣 MAIN — 979 characters ✓
```text
TARGET INSTRUMENT: Synth (General synthesizer (broad)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Synth render of 'The Steward's Calibration'. No other instrument takes the lead — especially Synth pad, Synth bass, Synth keys, Risers, Synth strings, Synth lead, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth bass (`synth_bass`)
_category: synth · Synthesizer bass_

🟣 MAIN — 973 characters ✓
```text
TARGET INSTRUMENT: Synth bass (Synthesizer bass). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Synth bass render of 'The Steward's Calibration'. No other instrument takes the lead — especially Synth, Synth pad, Synth keys, Risers, Synth strings, Synth lead, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth brass (`synth_brass`)  [beta]
_category: synth · Synthesizer brass_

🟣 MAIN — 975 characters ✓
```text
TARGET INSTRUMENT: Synth brass (Synthesizer brass). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Synth brass render of 'The Steward's Calibration'. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Risers, Synth strings, Synth lead, Arpeggiator. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth keys (`synth_keys`)
_category: synth · Synthesizer keyboard (leads, stabs, comping)_

🟣 MAIN — 949 characters ✓
```text
TARGET INSTRUMENT: Synth keys (Synthesizer keyboard (leads, stabs, comping)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Pads/keys for harmony; mono leads for scales and solos; sequenced bass; arpeggiator only where notated. No drift; every calibration passage stays intact; the requested instrument is dominant. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Synth keys render of 'The Steward's Calibration'. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Risers, Synth strings, Synth lead, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth lead (`synth_lead`)  [beta]
_category: synth · Synthesizer lead / melody voice_

🟣 MAIN — 988 characters ✓
```text
TARGET INSTRUMENT: Synth lead (Synthesizer lead / melody voice). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Synth lead render of 'The Steward's Calibration'. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Risers, Synth strings, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth pad (`synth_pad`)
_category: synth · Sustained atmospheric synthesizer pad_

🟣 MAIN — 993 characters ✓
```text
TARGET INSTRUMENT: Synth pad (Sustained atmospheric synthesizer pad). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Synth pad render of 'The Steward's Calibration'. No other instrument takes the lead — especially Synth, Synth bass, Synth keys, Risers, Synth strings, Synth lead, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth strings (`synth_strings`)  [beta]
_category: synth · Synthesizer string pads_

🟣 MAIN — 983 characters ✓
```text
TARGET INSTRUMENT: Synth strings (Synthesizer string pads). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Synth strings render of 'The Steward's Calibration'. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Risers, Synth lead, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Tabla (`tabla`)  [beta]
_category: percussion · Tabla (Indian hand drums)_

🟣 MAIN — 975 characters ✓
```text
TARGET INSTRUMENT: Tabla (Tabla (Indian hand drums)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 934 characters ✓
```text
EXCLUDE for the Tabla render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Taiko (`taiko`)  [beta]
_category: percussion · Taiko (Japanese drum)_

🟣 MAIN — 971 characters ✓
```text
TARGET INSTRUMENT: Taiko (Taiko (Japanese drum)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 934 characters ✓
```text
EXCLUDE for the Taiko render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Tambourine (`tambourine`)  [beta]
_category: percussion · Tambourine_

🟣 MAIN — 952 characters ✓
```text
TARGET INSTRUMENT: Tambourine. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Tambourine render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Bells, Shaker, Glockenspiel, Timpani. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Tenor saxophone (`tenor_saxophone`)  [beta]
_category: woodwind · Tenor saxophone_

🟣 MAIN — 926 characters ✓
```text
TARGET INSTRUMENT: Tenor saxophone. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 930 characters ✓
```text
EXCLUDE for the Tenor saxophone render of 'The Steward's Calibration'. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Saxophone, Oboe, Alto saxophone, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Theremin (`theremin`)  [beta]
_category: synth · Theremin_

🟣 MAIN — 952 characters ✓
```text
TARGET INSTRUMENT: Theremin. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 933 characters ✓
```text
EXCLUDE for the Theremin render of 'The Steward's Calibration'. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Risers, Synth strings, Synth lead, Arpeggiator. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Timpani (`timpani`)  [beta]
_category: percussion · Timpani / kettle drums_

🟣 MAIN — 974 characters ✓
```text
TARGET INSTRUMENT: Timpani (Timpani / kettle drums). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 936 characters ✓
```text
EXCLUDE for the Timpani render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Trombone (`trombone`)  [beta]
_category: brass · Trombone_

🟣 MAIN — 973 characters ✓
```text
TARGET INSTRUMENT: Trombone. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Brass feature: bold chorale chords in harmony movements, fanfare-style phrasing of scales and intervals, marcato staccato attacks, smooth controlled legato solos. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. IX must climb C to D and land the dense final E-minor cadence at full length.
```

🛑 EXCLUDE — 932 characters ✓
```text
EXCLUDE for the Trombone render of 'The Steward's Calibration'. No other instrument takes the lead — especially Brass, Trumpet, French horn, Tuba. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Trumpet (`trumpet`)  [beta]
_category: brass · Trumpet_

🟣 MAIN — 972 characters ✓
```text
TARGET INSTRUMENT: Trumpet. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Brass feature: bold chorale chords in harmony movements, fanfare-style phrasing of scales and intervals, marcato staccato attacks, smooth controlled legato solos. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. IX must climb C to D and land the dense final E-minor cadence at full length.
```

🛑 EXCLUDE — 932 characters ✓
```text
EXCLUDE for the Trumpet render of 'The Steward's Calibration'. No other instrument takes the lead — especially Brass, Trombone, French horn, Tuba. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Tuba (`tuba`)  [beta]
_category: brass · Tuba_

🟣 MAIN — 969 characters ✓
```text
TARGET INSTRUMENT: Tuba. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Brass feature: bold chorale chords in harmony movements, fanfare-style phrasing of scales and intervals, marcato staccato attacks, smooth controlled legato solos. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. IX must climb C to D and land the dense final E-minor cadence at full length.
```

🛑 EXCLUDE — 932 characters ✓
```text
EXCLUDE for the Tuba render of 'The Steward's Calibration'. No other instrument takes the lead — especially Brass, Trumpet, Trombone, French horn. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Ukulele (`ukulele`)  [beta]
_category: guitar · Ukulele_

🟣 MAIN — 973 characters ✓
```text
TARGET INSTRUMENT: Ukulele. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Guitar feature: strummed or picked chord realizations of the harmony movements, single-note scale and solo runs with bends only where the harmony allows, dual-voice flatpicking for counterpoint, low-string work for the walking-bass movement. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 959 characters ✓
```text
EXCLUDE for the Ukulele render of 'The Steward's Calibration'. No other instrument takes the lead — especially Electric guitar, Acoustic guitar, Guitar, Lead guitar, Rhythm electric guitar, Rhythm acoustic guitar, Slide guitar. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Upright bass (`upright_bass`)
_category: bass · Double bass / upright bass_

🟣 MAIN — 949 characters ✓
```text
TARGET INSTRUMENT: Upright bass (Double bass / upright bass). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Bass feature: carry every harmony as bass lines, feature movement VII's walking bass, octave pops and low pedal, keep the finale bass prominent, stay low with the melody hinted above. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 925 characters ✓
```text
EXCLUDE for the Upright bass render of 'The Steward's Calibration'. No other instrument takes the lead — especially Bass, Bass guitar, 808. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Vibraphone (`vibraphone`)  [beta]
_category: percussion · Vibraphone / vibes_

🟣 MAIN — 973 characters ✓
```text
TARGET INSTRUMENT: Vibraphone (Vibraphone / vibes). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 939 characters ✓
```text
EXCLUDE for the Vibraphone render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Viola (`viola`)  [beta]
_category: strings · Viola_

🟣 MAIN — 923 characters ✓
```text
TARGET INSTRUMENT: Viola. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 960 characters ✓
```text
EXCLUDE for the Viola render of 'The Steward's Calibration'. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Banjo, Cello, Orchestra. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Violin (`violin`)  [beta]
_category: strings · Violin_

🟣 MAIN — 924 characters ✓
```text
TARGET INSTRUMENT: Violin. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 902 characters ✓
```text
EXCLUDE for the Violin render of 'The Steward's Calibration'. No other instrument takes the lead — especially Strings, Harp, Fiddle, Mandolin, Banjo, Cello, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Vocoder (`vocoder`)  [beta]
_category: vocal · Vocoder-processed vocal_

🟣 MAIN — 962 characters ✓
```text
TARGET INSTRUMENT: Vocoder (Vocoder-processed vocal). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Vocal feature: sing the lead melody throughout, deliver movement VIII's motif as sustained legato 'ah' lines, layer movement V chords as 'ooh' pads, and render the percussion movement as vocal percussion. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 914 characters ✓
```text
EXCLUDE for the Vocoder render of 'The Steward's Calibration'. No other instrument takes the lead — especially Lead vocal, Backing vocal, Choir, Whistle. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Whistle (`whistle`)  [beta]
_category: vocal · Human whistle_

🟣 MAIN — 952 characters ✓
```text
TARGET INSTRUMENT: Whistle (Human whistle). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Vocal feature: sing the lead melody throughout, deliver movement VIII's motif as sustained legato 'ah' lines, layer movement V chords as 'ooh' pads, and render the percussion movement as vocal percussion. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 914 characters ✓
```text
EXCLUDE for the Whistle render of 'The Steward's Calibration'. No other instrument takes the lead — especially Lead vocal, Backing vocal, Vocoder, Choir. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Woodwinds (`woodwinds`)  [beta]
_category: woodwind · General woodwind instruments (broad)_

🟣 MAIN — 959 characters ✓
```text
TARGET INSTRUMENT: Woodwinds (General woodwind instruments (broad)). Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 930 characters ✓
```text
EXCLUDE for the Woodwinds render of 'The Steward's Calibration'. No other instrument takes the lead — especially Flute, Clarinet, Tenor saxophone, Saxophone, Oboe, Alto saxophone, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Xylophone (`xylophone`)  [beta]
_category: percussion · Xylophone_

🟣 MAIN — 951 characters ✓
```text
TARGET INSTRUMENT: Xylophone. Realize 'The Steward's Calibration': 4:48 instrumental reference, 100 BPM, 4/4, nine movements in strict order. I Majors Parade: one bar per major key, I-IV-V-I. II Minors Parade: one bar per minor key, i-iv-V-i. III Scales & Intervals: scales, chromatic run, intervals 2nds-octaves both ways, register sweep. IV Progression Journey: ii-V-I, I-V-vi-IV, vi-IV-I-V, A blues. V Counterpoint & Voicings: two voices, dyads, dense/sparse voicings, sus chords, inverted staccato. VI Two Solos. VII Bass Behavior. VIII Percussion & FX. IX Finale: dense climax, E-minor cadence. Percussion feature: perform movement VIII's syncopated groove as the continuous backbone, map every movement's chord rhythm to articulated hits, render movement III runs as tonal strikes and the solos as fill figures. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift.
```

🛑 EXCLUDE — 938 characters ✓
```text
EXCLUDE for the Xylophone render of 'The Steward's Calibration'. No other instrument takes the lead — especially Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No sung vocals, lyrics or humming.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement. No early fade of the final cadence; let it ring to full length. No inserted transitions, breakdowns or drops between movements.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

