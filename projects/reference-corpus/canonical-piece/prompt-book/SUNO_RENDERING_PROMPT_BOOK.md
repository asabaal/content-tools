# Suno Rendering Prompt Book — Calibration Suite

_Generated 2026-09-13T22:33:34.487008+00:00 · 90 targets · 180 prompts · all validated at 900–1000 characters inclusive._

## The calibration suite (three canonical references)

One piece per measurement problem; every Suno Advanced Split target renders its family's reference. Never per-target etudes.

1. **Pitched / Harmonic Reference — 4:00** — 'The Steward's Calibration': nine movements, all 24 keys, progressions, scales, intervals 2nds–octaves, chord types, textures, articulations, registers, two solos, dense finale. Conditioning candidates: neutral piano and neutral plain synth.
2. **Percussion Timing Reference — 2:00** — onset/timing stress test on a neutral click: subdivisions through quintuplets, dotted figures, accents, rests, syncopation, 3+3+2 groupings, simultaneous/staggered events, call-and-response, 3/4, 6/8, 5/8 (3+2, 2+3), 7/8 (2+2+3, 3+2+2). Conditioning: neutral click, NOT a drum kit.
3. **Vocal Timing Reference — 2:00** — non-lexical 'ah' timing probe: note lengths, sustains, staccato, legato, melisma, dotted and tied rhythms, pickups, contours (ascending/descending/arch/repeated), registers, 1–4 part stacks, staggered backing entries, call-and-response, 3/4, 6/8, 5/8, 7/8. Conditioning: neutral ah/vox patch (GM 52 Voice Aahs via FluidR3_GM).

Invariants for every render: movement/region order, tempo, calibration-passage content and timing, target timbre dominant.

---
# FAMILY: Pitched / Harmonic Reference (pitched_harmonic)
Duration: 240 s · 61 target(s)
Reference piece: **The Steward's Calibration** — 240 s, 100 BPM, 9 movements.

**Canonical conditioning artifact(s)**
- conditioning candidate `multimodal_v1`: `canonical_reference_piece_multimodal_input.wav` (sha256 138ed5c9b767bfb2…)
- conditioning candidate `neutral_piano`: `canonical_reference_piece_piano_input.wav` (sha256 b900150511e38111…)
- conditioning candidate `neutral_synth`: `canonical_reference_piece_synth_input.wav` (sha256 bfe9612f1e3fbc6b…)

## TARGET: Accordion (`accordion`)  [beta]
_category: other · Accordion_

🟣 MAIN — 949 characters ✓
```text
TARGET INSTRUMENT: Accordion. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Render with the requested instrument as the sole melodic and harmonic voice: follow the movement map exactly, translate chord passages into idiomatic voicing, keep every calibration passage audible. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 921 characters ✓
```text
EXCLUDE for the Accordion render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Other, Harmonica, Bagpipes, Didgeridoo. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Acoustic guitar (`acoustic_guitar`)
_category: guitar · Acoustic guitar_

🟣 MAIN — 998 characters ✓
```text
TARGET INSTRUMENT: Acoustic guitar. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Guitar feature: strummed or picked chord realizations of the harmony movements, single-note scale and solo runs with bends only where the harmony allows, dual-voice flatpicking for counterpoint, low-string work for the walking-bass movement. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 959 characters ✓
```text
EXCLUDE for the Acoustic guitar render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Electric guitar, Guitar, Lead guitar, Rhythm electric guitar, Rhythm acoustic guitar, Slide guitar, Ukulele, electric guitar. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Alto saxophone (`alto_saxophone`)  [beta]
_category: woodwind · Alto saxophone_

🟣 MAIN — 942 characters ✓
```text
TARGET INSTRUMENT: Alto saxophone. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 900 characters ✓
```text
EXCLUDE for the Alto saxophone render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Tenor saxophone, Saxophone, Oboe, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Arpeggiator (`arpeggiator`)  [beta]
_category: synth · Arpeggiated synth pattern_

🟣 MAIN — 1000 characters ✓
```text
TARGET INSTRUMENT: Arpeggiator (Arpeggiated synth pattern). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 919 characters ✓
```text
EXCLUDE for the Arpeggiator render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Risers, Synth strings, Synth lead, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Bagpipes (`bagpipes`)  [beta]
_category: other · Bagpipes_

🟣 MAIN — 948 characters ✓
```text
TARGET INSTRUMENT: Bagpipes. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Render with the requested instrument as the sole melodic and harmonic voice: follow the movement map exactly, translate chord passages into idiomatic voicing, keep every calibration passage audible. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 921 characters ✓
```text
EXCLUDE for the Bagpipes render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Other, Accordion, Harmonica, Didgeridoo. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Banjo (`banjo`)  [beta]
_category: strings · Banjo_

🟣 MAIN — 940 characters ✓
```text
TARGET INSTRUMENT: Banjo. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 949 characters ✓
```text
EXCLUDE for the Banjo render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Cello, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Baritone saxophone (`baritone_saxophone`)  [beta]
_category: woodwind · Baritone saxophone_

🟣 MAIN — 946 characters ✓
```text
TARGET INSTRUMENT: Baritone saxophone. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 900 characters ✓
```text
EXCLUDE for the Baritone saxophone render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Tenor saxophone, Saxophone, Oboe, Alto saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Bass (`bass`)
_category: bass · Bass instrument, part, or line (broad)_

🟣 MAIN — 970 characters ✓
```text
TARGET INSTRUMENT: Bass (Bass instrument, part, or line (broad)). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Bass feature: carry every harmony as bass lines, feature movement VII's walking bass, octave pops and low pedal, keep the finale bass prominent, stay low with the melody hinted above. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 938 characters ✓
```text
EXCLUDE for the Bass render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Upright bass, Bass guitar, 808, synth bass, eight zero eight. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Bass guitar (`bass_guitar`)  [beta]
_category: bass · Electric bass guitar_

🟣 MAIN — 959 characters ✓
```text
TARGET INSTRUMENT: Bass guitar (Electric bass guitar). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Bass feature: carry every harmony as bass lines, feature movement VII's walking bass, octave pops and low pedal, keep the finale bass prominent, stay low with the melody hinted above. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 908 characters ✓
```text
EXCLUDE for the Bass guitar render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Bass, Upright bass, 808. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Bassoon (`bassoon`)  [beta]
_category: woodwind · Bassoon_

🟣 MAIN — 935 characters ✓
```text
TARGET INSTRUMENT: Bassoon. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 900 characters ✓
```text
EXCLUDE for the Bassoon render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Tenor saxophone, Saxophone, Oboe, Alto saxophone, Baritone saxophone. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Brass (`brass`)
_category: brass · Brass instruments (broad)_

🟣 MAIN — 937 characters ✓
```text
TARGET INSTRUMENT: Brass (Brass instruments (broad)). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Brass feature: bold chorale chords in harmony movements, fanfare-style phrasing of scales and intervals, marcato staccato attacks, smooth controlled legato solos. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 915 characters ✓
```text
EXCLUDE for the Brass render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Trumpet, Trombone, French horn, Tuba. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Cello (`cello`)  [beta]
_category: strings · Cello_

🟣 MAIN — 940 characters ✓
```text
TARGET INSTRUMENT: Cello. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 949 characters ✓
```text
EXCLUDE for the Cello render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Banjo, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Clarinet (`clarinet`)  [beta]
_category: woodwind · Clarinet_

🟣 MAIN — 936 characters ✓
```text
TARGET INSTRUMENT: Clarinet. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 900 characters ✓
```text
EXCLUDE for the Clarinet render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Woodwinds, Flute, Tenor saxophone, Saxophone, Oboe, Alto saxophone, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Didgeridoo (`didgeridoo`)  [beta]
_category: other · Didgeridoo_

🟣 MAIN — 950 characters ✓
```text
TARGET INSTRUMENT: Didgeridoo. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Render with the requested instrument as the sole melodic and harmonic voice: follow the movement map exactly, translate chord passages into idiomatic voicing, keep every calibration passage audible. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 921 characters ✓
```text
EXCLUDE for the Didgeridoo render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Other, Accordion, Harmonica, Bagpipes. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Double bass (`double_bass`)  [beta]
_category: strings · Double bass (orchestral)_

🟣 MAIN — 973 characters ✓
```text
TARGET INSTRUMENT: Double bass (Double bass (orchestral)). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 949 characters ✓
```text
EXCLUDE for the Double bass render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Banjo, Cello, Orchestra. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Drone (`drone`)  [beta]
_category: synth · Sustained drone / pedal tone_

🟣 MAIN — 997 characters ✓
```text
TARGET INSTRUMENT: Drone (Sustained drone / pedal tone). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 913 characters ✓
```text
EXCLUDE for the Drone render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Risers, Synth strings, Synth lead, Arpeggiator. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: 808 (`eight_zero_eight`)  [beta]
_category: bass · 808 bass / kick_

🟣 MAIN — 946 characters ✓
```text
TARGET INSTRUMENT: 808 (808 bass / kick). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Bass feature: carry every harmony as bass lines, feature movement VII's walking bass, octave pops and low pedal, keep the finale bass prominent, stay low with the melody hinted above. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 908 characters ✓
```text
EXCLUDE for the 808 render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Bass, Upright bass, Bass guitar. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Electric guitar (`electric_guitar`)
_category: guitar · Electric guitar, including lead and rhythm_

🟣 MAIN — 929 characters ✓
```text
TARGET INSTRUMENT: Electric guitar (Electric guitar, including lead and rhythm). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Guitar feature: strummed or picked chord realizations of the harmony movements, single-note scale and solo runs with bends only where the harmony allows, dual-voice flatpicking for counterpoint, low-string work for the walking-bass movement. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 959 characters ✓
```text
EXCLUDE for the Electric guitar render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Acoustic guitar, Guitar, Lead guitar, Rhythm electric guitar, Rhythm acoustic guitar, Slide guitar, Ukulele, acoustic guitar. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Electric piano (`electric_piano`)
_category: keyboard · Electric piano (Rhodes, Wurlitzer, etc.)_

🟣 MAIN — 968 characters ✓
```text
TARGET INSTRUMENT: Electric piano (Electric piano (Rhodes, Wurlitzer, etc.)). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IX must climb C to D and land the dense final E-minor cadence at full length.
```

🛑 EXCLUDE — 943 characters ✓
```text
EXCLUDE for the Electric piano render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Piano, Organ, Keyboards, Celesta, Harpsichord, Melodica. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Fiddle (`fiddle`)  [beta]
_category: strings · Fiddle (violin played in folk style)_

🟣 MAIN — 980 characters ✓
```text
TARGET INSTRUMENT: Fiddle (Fiddle (violin played in folk style)). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 949 characters ✓
```text
EXCLUDE for the Fiddle render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Strings, Harp, Violin, Mandolin, Banjo, Cello, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Flute (`flute`)  [beta]
_category: woodwind · Flute_

🟣 MAIN — 933 characters ✓
```text
TARGET INSTRUMENT: Flute. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 900 characters ✓
```text
EXCLUDE for the Flute render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Woodwinds, Clarinet, Tenor saxophone, Saxophone, Oboe, Alto saxophone, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: French horn (`french_horn`)  [beta]
_category: brass · French horn_

🟣 MAIN — 915 characters ✓
```text
TARGET INSTRUMENT: French horn. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Brass feature: bold chorale chords in harmony movements, fanfare-style phrasing of scales and intervals, marcato staccato attacks, smooth controlled legato solos. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 915 characters ✓
```text
EXCLUDE for the French horn render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Brass, Trumpet, Trombone, Tuba. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Guitar (`guitar`)
_category: guitar · Guitar (broad - any type)_

🟣 MAIN — 903 characters ✓
```text
TARGET INSTRUMENT: Guitar (Guitar (broad - any type)). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Guitar feature: strummed or picked chord realizations of the harmony movements, single-note scale and solo runs with bends only where the harmony allows, dual-voice flatpicking for counterpoint, low-string work for the walking-bass movement. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 951 characters ✓
```text
EXCLUDE for the Guitar render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Electric guitar, Acoustic guitar, Lead guitar, Rhythm electric guitar, Rhythm acoustic guitar, Slide guitar, Ukulele, ukulele. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Harmonica (`harmonica`)  [beta]
_category: other · Harmonica_

🟣 MAIN — 949 characters ✓
```text
TARGET INSTRUMENT: Harmonica. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Render with the requested instrument as the sole melodic and harmonic voice: follow the movement map exactly, translate chord passages into idiomatic voicing, keep every calibration passage audible. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 921 characters ✓
```text
EXCLUDE for the Harmonica render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Other, Accordion, Bagpipes, Didgeridoo. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Harp (`harp`)  [beta]
_category: strings · Harp_

🟣 MAIN — 939 characters ✓
```text
TARGET INSTRUMENT: Harp. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 949 characters ✓
```text
EXCLUDE for the Harp render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Strings, Fiddle, Violin, Mandolin, Banjo, Cello, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Harpsichord (`harpsichord`)  [beta]
_category: keyboard · Harpsichord_

🟣 MAIN — 958 characters ✓
```text
TARGET INSTRUMENT: Harpsichord. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 943 characters ✓
```text
EXCLUDE for the Harpsichord render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Piano, Organ, Electric piano, Keyboards, Celesta, Melodica. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Keyboards (`keyboards`)
_category: keyboard · General keyboard instruments_

🟣 MAIN — 987 characters ✓
```text
TARGET INSTRUMENT: Keyboards (General keyboard instruments). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 943 characters ✓
```text
EXCLUDE for the Keyboards render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Piano, Organ, Electric piano, Celesta, Harpsichord, Melodica. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Koto (`koto`)  [beta]
_category: strings · Koto (Japanese string instrument)_

🟣 MAIN — 975 characters ✓
```text
TARGET INSTRUMENT: Koto (Koto (Japanese string instrument)). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 942 characters ✓
```text
EXCLUDE for the Koto render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Banjo, Cello, Orchestra. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Lead guitar (`lead_guitar`)
_category: guitar · Lead/featured guitar part_

🟣 MAIN — 908 characters ✓
```text
TARGET INSTRUMENT: Lead guitar (Lead/featured guitar part). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Guitar feature: strummed or picked chord realizations of the harmony movements, single-note scale and solo runs with bends only where the harmony allows, dual-voice flatpicking for counterpoint, low-string work for the walking-bass movement. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 942 characters ✓
```text
EXCLUDE for the Lead guitar render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Electric guitar, Acoustic guitar, Guitar, Rhythm electric guitar, Rhythm acoustic guitar, Slide guitar, Ukulele. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Mandolin (`mandolin`)  [beta]
_category: strings · Mandolin_

🟣 MAIN — 943 characters ✓
```text
TARGET INSTRUMENT: Mandolin. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 949 characters ✓
```text
EXCLUDE for the Mandolin render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Banjo, Cello, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Melodica (`melodica`)  [beta]
_category: keyboard · Melodica_

🟣 MAIN — 955 characters ✓
```text
TARGET INSTRUMENT: Melodica. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 943 characters ✓
```text
EXCLUDE for the Melodica render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Piano, Organ, Electric piano, Keyboards, Celesta, Harpsichord. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Oboe (`oboe`)  [beta]
_category: woodwind · Oboe_

🟣 MAIN — 932 characters ✓
```text
TARGET INSTRUMENT: Oboe. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 900 characters ✓
```text
EXCLUDE for the Oboe render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Tenor saxophone, Saxophone, Alto saxophone, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Orchestra (`orchestra`)  [beta]
_category: strings · Full orchestral arrangement_

🟣 MAIN — 974 characters ✓
```text
TARGET INSTRUMENT: Orchestra (Full orchestral arrangement). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 949 characters ✓
```text
EXCLUDE for the Orchestra render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Banjo, Cello, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Organ (`organ`)
_category: keyboard · Organ (pipe, electric, or digital)_

🟣 MAIN — 989 characters ✓
```text
TARGET INSTRUMENT: Organ (Organ (pipe, electric, or digital)). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 970 characters ✓
```text
EXCLUDE for the Organ render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Piano, Electric piano, Keyboards, Celesta, Harpsichord, Melodica, electric piano, accordion. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Other (`other`)
_category: other · Elements not matching other targets_

🟣 MAIN — 983 characters ✓
```text
TARGET INSTRUMENT: Other (Elements not matching other targets). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Render with the requested instrument as the sole melodic and harmonic voice: follow the movement map exactly, translate chord passages into idiomatic voicing, keep every calibration passage audible. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 921 characters ✓
```text
EXCLUDE for the Other render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Accordion, Harmonica, Bagpipes, Didgeridoo. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Piano (`piano`)
_category: keyboard · Acoustic piano_

🟣 MAIN — 969 characters ✓
```text
TARGET INSTRUMENT: Piano (Acoustic piano). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Keyboard feature: block chords and arpeggios in harmony movements, clean single-note runs for scales and interval studies, counterpoint split between hands, sustain pedal only where the score marks legato. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 972 characters ✓
```text
EXCLUDE for the Piano render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Organ, Electric piano, Keyboards, Celesta, Harpsichord, Melodica, electric piano, harpsichord. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Piccolo (`piccolo`)  [beta]
_category: woodwind · Piccolo_

🟣 MAIN — 935 characters ✓
```text
TARGET INSTRUMENT: Piccolo. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 900 characters ✓
```text
EXCLUDE for the Piccolo render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Tenor saxophone, Saxophone, Oboe, Alto saxophone, Baritone saxophone. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Rhythm acoustic guitar (`rhythm_acoustic_guitar`)  [beta]
_category: guitar · Acoustic guitar playing rhythm parts_

🟣 MAIN — 930 characters ✓
```text
TARGET INSTRUMENT: Rhythm acoustic guitar (Acoustic guitar playing rhythm parts). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Guitar feature: strummed or picked chord realizations of the harmony movements, single-note scale and solo runs with bends only where the harmony allows, dual-voice flatpicking for counterpoint, low-string work for the walking-bass movement. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 942 characters ✓
```text
EXCLUDE for the Rhythm acoustic guitar render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Electric guitar, Acoustic guitar, Guitar, Lead guitar, Rhythm electric guitar, Slide guitar, Ukulele. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Rhythm electric guitar (`rhythm_electric_guitar`)
_category: guitar · Electric guitar playing rhythm parts_

🟣 MAIN — 930 characters ✓
```text
TARGET INSTRUMENT: Rhythm electric guitar (Electric guitar playing rhythm parts). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Guitar feature: strummed or picked chord realizations of the harmony movements, single-note scale and solo runs with bends only where the harmony allows, dual-voice flatpicking for counterpoint, low-string work for the walking-bass movement. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 942 characters ✓
```text
EXCLUDE for the Rhythm electric guitar render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Electric guitar, Acoustic guitar, Guitar, Lead guitar, Rhythm acoustic guitar, Slide guitar, Ukulele. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Risers (`risers`)  [beta]
_category: synth · Rising tonal or noise sweeps / transition effects_

🟣 MAIN — 905 characters ✓
```text
TARGET INSTRUMENT: Risers (Rising tonal or noise sweeps / transition effects). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 919 characters ✓
```text
EXCLUDE for the Risers render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Synth strings, Synth lead, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Saxophone (`saxophone`)  [beta]
_category: woodwind · Saxophone (broad)_

🟣 MAIN — 957 characters ✓
```text
TARGET INSTRUMENT: Saxophone (Saxophone (broad)). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 900 characters ✓
```text
EXCLUDE for the Saxophone render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Tenor saxophone, Oboe, Alto saxophone, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Sitar (`sitar`)  [beta]
_category: strings · Sitar_

🟣 MAIN — 940 characters ✓
```text
TARGET INSTRUMENT: Sitar. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 943 characters ✓
```text
EXCLUDE for the Sitar render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Banjo, Cello, Orchestra. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Slide guitar (`slide_guitar`)  [beta]
_category: guitar · Slide or bottleneck guitar_

🟣 MAIN — 910 characters ✓
```text
TARGET INSTRUMENT: Slide guitar (Slide or bottleneck guitar). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Guitar feature: strummed or picked chord realizations of the harmony movements, single-note scale and solo runs with bends only where the harmony allows, dual-voice flatpicking for counterpoint, low-string work for the walking-bass movement. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 942 characters ✓
```text
EXCLUDE for the Slide guitar render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Electric guitar, Acoustic guitar, Guitar, Lead guitar, Rhythm electric guitar, Rhythm acoustic guitar, Ukulele. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Strings (`strings`)
_category: strings · String section or string instruments_

🟣 MAIN — 981 characters ✓
```text
TARGET INSTRUMENT: Strings (String section or string instruments). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 949 characters ✓
```text
EXCLUDE for the Strings render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Harp, Fiddle, Violin, Mandolin, Banjo, Cello, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth (`synth`)
_category: synth · General synthesizer (broad)_

🟣 MAIN — 996 characters ✓
```text
TARGET INSTRUMENT: Synth (General synthesizer (broad)). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 919 characters ✓
```text
EXCLUDE for the Synth render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Synth pad, Synth bass, Synth keys, Risers, Synth strings, Synth lead, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth bass (`synth_bass`)
_category: synth · Synthesizer bass_

🟣 MAIN — 990 characters ✓
```text
TARGET INSTRUMENT: Synth bass (Synthesizer bass). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 919 characters ✓
```text
EXCLUDE for the Synth bass render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Synth, Synth pad, Synth keys, Risers, Synth strings, Synth lead, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth brass (`synth_brass`)  [beta]
_category: synth · Synthesizer brass_

🟣 MAIN — 992 characters ✓
```text
TARGET INSTRUMENT: Synth brass (Synthesizer brass). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 919 characters ✓
```text
EXCLUDE for the Synth brass render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Risers, Synth strings, Synth lead, Arpeggiator. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth keys (`synth_keys`)
_category: synth · Synthesizer keyboard (leads, stabs, comping)_

🟣 MAIN — 904 characters ✓
```text
TARGET INSTRUMENT: Synth keys (Synthesizer keyboard (leads, stabs, comping)). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 919 characters ✓
```text
EXCLUDE for the Synth keys render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Risers, Synth strings, Synth lead, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth lead (`synth_lead`)  [beta]
_category: synth · Synthesizer lead / melody voice_

🟣 MAIN — 969 characters ✓
```text
TARGET INSTRUMENT: Synth lead (Synthesizer lead / melody voice). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IX must climb C to D and land the dense final E-minor cadence at full length.
```

🛑 EXCLUDE — 919 characters ✓
```text
EXCLUDE for the Synth lead render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Risers, Synth strings, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth pad (`synth_pad`)
_category: synth · Sustained atmospheric synthesizer pad_

🟣 MAIN — 974 characters ✓
```text
TARGET INSTRUMENT: Synth pad (Sustained atmospheric synthesizer pad). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IX must climb C to D and land the dense final E-minor cadence at full length.
```

🛑 EXCLUDE — 919 characters ✓
```text
EXCLUDE for the Synth pad render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Synth, Synth bass, Synth keys, Risers, Synth strings, Synth lead, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Synth strings (`synth_strings`)  [beta]
_category: synth · Synthesizer string pads_

🟣 MAIN — 1000 characters ✓
```text
TARGET INSTRUMENT: Synth strings (Synthesizer string pads). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 919 characters ✓
```text
EXCLUDE for the Synth strings render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Risers, Synth lead, Arpeggiator, Synth brass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Tenor saxophone (`tenor_saxophone`)  [beta]
_category: woodwind · Tenor saxophone_

🟣 MAIN — 943 characters ✓
```text
TARGET INSTRUMENT: Tenor saxophone. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 900 characters ✓
```text
EXCLUDE for the Tenor saxophone render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Woodwinds, Flute, Clarinet, Saxophone, Oboe, Alto saxophone, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Theremin (`theremin`)  [beta]
_category: synth · Theremin_

🟣 MAIN — 969 characters ✓
```text
TARGET INSTRUMENT: Theremin. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Synthesizer feature: pads or keys for harmony movements per their character, sharp monophonic leads for scales and solos, sequenced bass for movement VII, tempo-locked arpeggiator only where the score notates arpeggios. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 916 characters ✓
```text
EXCLUDE for the Theremin render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Synth, Synth pad, Synth bass, Synth keys, Risers, Synth strings, Synth lead, Arpeggiator. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Trombone (`trombone`)  [beta]
_category: brass · Trombone_

🟣 MAIN — 912 characters ✓
```text
TARGET INSTRUMENT: Trombone. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Brass feature: bold chorale chords in harmony movements, fanfare-style phrasing of scales and intervals, marcato staccato attacks, smooth controlled legato solos. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 915 characters ✓
```text
EXCLUDE for the Trombone render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Brass, Trumpet, French horn, Tuba. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Trumpet (`trumpet`)  [beta]
_category: brass · Trumpet_

🟣 MAIN — 911 characters ✓
```text
TARGET INSTRUMENT: Trumpet. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Brass feature: bold chorale chords in harmony movements, fanfare-style phrasing of scales and intervals, marcato staccato attacks, smooth controlled legato solos. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 915 characters ✓
```text
EXCLUDE for the Trumpet render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Brass, Trombone, French horn, Tuba. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Tuba (`tuba`)  [beta]
_category: brass · Tuba_

🟣 MAIN — 908 characters ✓
```text
TARGET INSTRUMENT: Tuba. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Brass feature: bold chorale chords in harmony movements, fanfare-style phrasing of scales and intervals, marcato staccato attacks, smooth controlled legato solos. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 915 characters ✓
```text
EXCLUDE for the Tuba render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Brass, Trumpet, Trombone, French horn. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Ukulele (`ukulele`)  [beta]
_category: guitar · Ukulele_

🟣 MAIN — 990 characters ✓
```text
TARGET INSTRUMENT: Ukulele. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Guitar feature: strummed or picked chord realizations of the harmony movements, single-note scale and solo runs with bends only where the harmony allows, dual-voice flatpicking for counterpoint, low-string work for the walking-bass movement. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 942 characters ✓
```text
EXCLUDE for the Ukulele render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Electric guitar, Acoustic guitar, Guitar, Lead guitar, Rhythm electric guitar, Rhythm acoustic guitar, Slide guitar. No sung vocals, lyrics or humming. No drum kit beyond what the score notates.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Upright bass (`upright_bass`)
_category: bass · Double bass / upright bass_

🟣 MAIN — 966 characters ✓
```text
TARGET INSTRUMENT: Upright bass (Double bass / upright bass). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Bass feature: carry every harmony as bass lines, feature movement VII's walking bass, octave pops and low pedal, keep the finale bass prominent, stay low with the melody hinted above. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 908 characters ✓
```text
EXCLUDE for the Upright bass render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Bass, Bass guitar, 808. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Viola (`viola`)  [beta]
_category: strings · Viola_

🟣 MAIN — 940 characters ✓
```text
TARGET INSTRUMENT: Viola. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 943 characters ✓
```text
EXCLUDE for the Viola render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Strings, Harp, Fiddle, Violin, Mandolin, Banjo, Cello, Orchestra. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Violin (`violin`)  [beta]
_category: strings · Violin_

🟣 MAIN — 941 characters ✓
```text
TARGET INSTRUMENT: Violin. Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Strings feature: bowed sustained chords in harmony movements, legato single-line scales and solos, pizzicato for staccato and percussion movements, rich contrapuntal double-stops in movement V. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 949 characters ✓
```text
EXCLUDE for the Violin render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Strings, Harp, Fiddle, Mandolin, Banjo, Cello, Orchestra, Double bass. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Woodwinds (`woodwinds`)  [beta]
_category: woodwind · General woodwind instruments (broad)_

🟣 MAIN — 976 characters ✓
```text
TARGET INSTRUMENT: Woodwinds (General woodwind instruments (broad)). Realize 'The Steward's Calibration': 4:00 instrumental reference, 100 BPM, 4/4, 100 bars, nine movements in strict order: Majors Parade; Minors Parade; Scales, Intervals, Registers; Progression Journey (ii-V-I, pop loops, blues, modulation); Counterpoint, Voicings, Articulation; Two Solos; Bass / Low-Register Behavior; Transitional / Rhythmic Behavior; Finale. Woodwind feature: fluid single-line scales and solos with breath phrasing, gently articulated chord stabs in harmony movements, airy register sweeps, light tonguing on staccato material. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops in G, and the A blues over dominant sevenths.
```

🛑 EXCLUDE — 900 characters ✓
```text
EXCLUDE for the Woodwinds render of 'The Steward's Calibration'. No choir or vocal 'ah' pads, no semantic drum-kit percussion, and no cinematic FX styling anywhere — the transitional/rhythmic movement is played on the target instrument itself. No other instrument takes the lead — especially Flute, Clarinet, Tenor saxophone, Saxophone, Oboe, Alto saxophone, Baritone saxophone, Bassoon. No sung vocals, lyrics or humming. No drum kit beyond what the score notates. No synthesized imitation of this acoustic instrument.  No genre transformation away from the neutral reference arrangement. No arrangement drift: no added countermelodies, re-harmony, tempo change, movement reordering, or simplification of calibration passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

---
# FAMILY: Percussion Timing Reference (percussion_timing)
Duration: 120 s · 24 target(s)
Reference piece: **Percussion Timing Reference** — 120 s, 120 BPM, 11 timing regions.

**Canonical conditioning artifact(s)**
- conditioning candidate `neutral_click`: `percussion_timing_reference_click_input.wav` (sha256 6807e6650a9af6ac…)

## TARGET: Bells (`bells`)  [beta]  _multi-family: percussion_timing, pitched_harmonic_
_category: percussion · General bell sounds / glockenspiel-like_

🟣 MAIN — 936 characters ✓
```text
TARGET INSTRUMENT: Bells. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 973 characters ✓
```text
EXCLUDE for the Bells render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Shaker, Glockenspiel, Timpani. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Bongos (`bongos`)  [beta]
_category: percussion · Bongos_

🟣 MAIN — 937 characters ✓
```text
TARGET INSTRUMENT: Bongos. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 972 characters ✓
```text
EXCLUDE for the Bongos render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Celesta (`celesta`)  [beta]  _multi-family: percussion_timing, pitched_harmonic_
_category: keyboard · Celesta_

🟣 MAIN — 938 characters ✓
```text
TARGET INSTRUMENT: Celesta. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 964 characters ✓
```text
EXCLUDE for the Celesta render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Piano, Organ, Electric piano, Keyboards, Harpsichord, Melodica. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Clap (`clap`)  [beta]
_category: percussion · Hand claps / drum machine clap_

🟣 MAIN — 935 characters ✓
```text
TARGET INSTRUMENT: Clap. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 970 characters ✓
```text
EXCLUDE for the Clap render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Congas (`congas`)  [beta]
_category: percussion · Congas_

🟣 MAIN — 937 characters ✓
```text
TARGET INSTRUMENT: Congas. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 972 characters ✓
```text
EXCLUDE for the Congas render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Cowbell (`cowbell`)  [beta]
_category: percussion · Cowbell_

🟣 MAIN — 938 characters ✓
```text
TARGET INSTRUMENT: Cowbell. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 973 characters ✓
```text
EXCLUDE for the Cowbell render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Cymbals (`cymbals`)  [beta]
_category: percussion · Cymbals (hi-hat, ride, crash, etc.)_

🟣 MAIN — 938 characters ✓
```text
TARGET INSTRUMENT: Cymbals. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 973 characters ✓
```text
EXCLUDE for the Cymbals render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Djembe (`djembe`)  [beta]
_category: percussion · Djembe (African hand drum)_

🟣 MAIN — 937 characters ✓
```text
TARGET INSTRUMENT: Djembe. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 972 characters ✓
```text
EXCLUDE for the Djembe render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Drums (`drums`)
_category: percussion · Drum kit or drum machine (broad)_

🟣 MAIN — 936 characters ✓
```text
TARGET INSTRUMENT: Drums. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 973 characters ✓
```text
EXCLUDE for the Drums render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel, Timpani. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Glockenspiel (`glockenspiel`)  [beta]  _multi-family: percussion_timing, pitched_harmonic_
_category: percussion · Glockenspiel_

🟣 MAIN — 943 characters ✓
```text
TARGET INSTRUMENT: Glockenspiel. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 973 characters ✓
```text
EXCLUDE for the Glockenspiel render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Timpani. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Hi-hat (`hi_hat`)  [beta]
_category: percussion · Hi-hat (open or closed)_

🟣 MAIN — 937 characters ✓
```text
TARGET INSTRUMENT: Hi-hat. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 972 characters ✓
```text
EXCLUDE for the Hi-hat render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Kick (`kick`)  [beta]
_category: percussion · Kick drum_

🟣 MAIN — 935 characters ✓
```text
TARGET INSTRUMENT: Kick. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 973 characters ✓
```text
EXCLUDE for the Kick render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Snare, Tambourine, Bells, Shaker, Glockenspiel, Timpani. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Marimba (`marimba`)  [beta]
_category: percussion · Marimba_

🟣 MAIN — 938 characters ✓
```text
TARGET INSTRUMENT: Marimba. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 973 characters ✓
```text
EXCLUDE for the Marimba render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Music box (`music_box`)  [beta]
_category: percussion · Music box_

🟣 MAIN — 940 characters ✓
```text
TARGET INSTRUMENT: Music box. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 975 characters ✓
```text
EXCLUDE for the Music box render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Percussion (`percussion`)
_category: percussion · General percussion instruments_

🟣 MAIN — 941 characters ✓
```text
TARGET INSTRUMENT: Percussion. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 973 characters ✓
```text
EXCLUDE for the Percussion render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel, Timpani. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Shaker (`shaker`)  [beta]
_category: percussion · Shaker / maraca-style percussion_

🟣 MAIN — 937 characters ✓
```text
TARGET INSTRUMENT: Shaker. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 973 characters ✓
```text
EXCLUDE for the Shaker render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Glockenspiel, Timpani. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Snare (`snare`)  [beta]
_category: percussion · Snare drum_

🟣 MAIN — 936 characters ✓
```text
TARGET INSTRUMENT: Snare. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 973 characters ✓
```text
EXCLUDE for the Snare render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Tambourine, Bells, Shaker, Glockenspiel, Timpani. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Steel drums (`steel_drums`)  [beta]
_category: percussion · Steel drums / steelpan_

🟣 MAIN — 942 characters ✓
```text
TARGET INSTRUMENT: Steel drums. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 977 characters ✓
```text
EXCLUDE for the Steel drums render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Tabla (`tabla`)  [beta]
_category: percussion · Tabla (Indian hand drums)_

🟣 MAIN — 936 characters ✓
```text
TARGET INSTRUMENT: Tabla. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 971 characters ✓
```text
EXCLUDE for the Tabla render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Taiko (`taiko`)  [beta]
_category: percussion · Taiko (Japanese drum)_

🟣 MAIN — 936 characters ✓
```text
TARGET INSTRUMENT: Taiko. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 971 characters ✓
```text
EXCLUDE for the Taiko render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Tambourine (`tambourine`)  [beta]
_category: percussion · Tambourine_

🟣 MAIN — 941 characters ✓
```text
TARGET INSTRUMENT: Tambourine. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 973 characters ✓
```text
EXCLUDE for the Tambourine render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Bells, Shaker, Glockenspiel, Timpani. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Timpani (`timpani`)  [beta]  _multi-family: percussion_timing, pitched_harmonic_
_category: percussion · Timpani / kettle drums_

🟣 MAIN — 938 characters ✓
```text
TARGET INSTRUMENT: Timpani. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 973 characters ✓
```text
EXCLUDE for the Timpani render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Vibraphone (`vibraphone`)  [beta]
_category: percussion · Vibraphone / vibes_

🟣 MAIN — 941 characters ✓
```text
TARGET INSTRUMENT: Vibraphone. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 976 characters ✓
```text
EXCLUDE for the Vibraphone render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Xylophone (`xylophone`)  [beta]
_category: percussion · Xylophone_

🟣 MAIN — 940 characters ✓
```text
TARGET INSTRUMENT: Xylophone. Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral click transient (no drum-kit styling), 120 BPM, eleven regions: pulse 44; subdivisions; accents isolated rests; syncopation groupings; simultaneous staggered; tuplets bursts; call response density; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Percussion timing feature: place every onset exactly where the score places it, keep subdivisions even, accents clearly louder, silence windows silent, simultaneous hits exactly together, staggered rolls evenly spaced, and hold 120 BPM with no drift across any meter change. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 975 characters ✓
```text
EXCLUDE for the Xylophone render of 'Percussion Timing Reference'. No realistic drum-kit styling that turns the neutral click into a kick, snare, hi-hat, conga or cymbal identity; no pitched melodic material, no lyrics, no vocals. Avoid nearby percussion targets dominating: Drums, Percussion, Kick, Snare, Tambourine, Bells, Shaker, Glockenspiel. No groove reinterpretation, ghost-note restyling, tempo drift, meter re-grouping or simplification of the subdivision, tuplet, accent and asymmetric-meter calibration passages. No added reverb tails, room sound or samples that blur onset timing. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

---
# FAMILY: Vocal Timing Reference (vocal_timing)
Duration: 120 s · 5 target(s)
Reference piece: **Vocal Timing Reference** — 120 s, 120 BPM, 11 timing regions.

**Canonical conditioning artifact(s)**
- conditioning candidate `neutral_ah_vox`: `vocal_timing_reference_vox_input.wav` (sha256 cba3eb6c21847ba0…)

## TARGET: Backing vocal (`backing_vocal`)
_category: vocal · Secondary or harmony vocal parts_

🟣 MAIN — 907 characters ✓
```text
TARGET VOICE: Backing vocal. Perform 'Vocal Timing Reference': 2:00 non-lexical vocal timing probe ('ah' vowel only, no words), 120 BPM, eleven regions: single voice pulses; note lengths articulation; contours leaps; registers; syncopation pickups; tuplets dotted; harmony stagger call response; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Vocal timing feature: every onset and offset lands exactly on the score position; staccato short, sustains full length, legato connected; breaths only in written rests; 120 BPM steady through every meter change; the vowel never becomes a word. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 960 characters ✓
```text
EXCLUDE for the Backing vocal render of 'Vocal Timing Reference'. No lexical lyrics or words — the non-lexical 'ah' vowel only; no spoken passages. Avoid other voice types taking the lead, especially: Lead vocal, Vocoder, Choir, Whistle. No vibrato so heavy that onsets and offsets blur; no pitch correction artifacts, formant shifts or doubles that move the written timing; no melisma replacing notated single notes. No arrangement drift: no added ad-libs, no tempo drift, no meter re-grouping, no simplification of the contour, register, stagger and asymmetric-meter passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Choir (`choir`)  [beta]
_category: vocal · Choral or ensemble vocals_

🟣 MAIN — 977 characters ✓
```text
TARGET VOICE: Choir. Perform 'Vocal Timing Reference': 2:00 non-lexical vocal timing probe ('ah' vowel only, no words), 120 BPM, eleven regions: single voice pulses; note lengths articulation; contours leaps; registers; syncopation pickups; tuplets dotted; harmony stagger call response; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Vocal timing feature: every onset and offset lands exactly on the score position; staccato short, sustains full length, legato connected; breaths only in written rests; 120 BPM steady through every meter change; the vowel never becomes a word. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending. IX must climb C to D and land the dense final E-minor cadence at full length.
```

🛑 EXCLUDE — 903 characters ✓
```text
EXCLUDE for the Choir render of 'Vocal Timing Reference'. No lexical lyrics or words — the non-lexical 'ah' vowel only; no spoken passages. Avoid other voice types taking the lead, especially: Lead vocal, Backing vocal, Vocoder, Whistle, lead vocal, synth pad. No vibrato so heavy that onsets and offsets blur; no pitch correction artifacts, formant shifts or doubles that move the written timing; no melisma replacing notated single notes. No arrangement drift: no added ad-libs, no tempo drift, no meter re-grouping, no simplification of the contour, register, stagger and asymmetric-meter passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Lead vocal (`lead_vocal`)
_category: vocal · Primary vocal performance, lead singer_

🟣 MAIN — 904 characters ✓
```text
TARGET VOICE: Lead vocal. Perform 'Vocal Timing Reference': 2:00 non-lexical vocal timing probe ('ah' vowel only, no words), 120 BPM, eleven regions: single voice pulses; note lengths articulation; contours leaps; registers; syncopation pickups; tuplets dotted; harmony stagger call response; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Vocal timing feature: every onset and offset lands exactly on the score position; staccato short, sustains full length, legato connected; breaths only in written rests; 120 BPM steady through every meter change; the vowel never becomes a word. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 976 characters ✓
```text
EXCLUDE for the Lead vocal render of 'Vocal Timing Reference'. No lexical lyrics or words — the non-lexical 'ah' vowel only; no spoken passages. Avoid other voice types taking the lead, especially: Backing vocal, Vocoder, Choir, Whistle, choir, vocoder. No vibrato so heavy that onsets and offsets blur; no pitch correction artifacts, formant shifts or doubles that move the written timing; no melisma replacing notated single notes. No arrangement drift: no added ad-libs, no tempo drift, no meter re-grouping, no simplification of the contour, register, stagger and asymmetric-meter passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Vocoder (`vocoder`)  [beta]  _multi-family: vocal_timing, pitched_harmonic_
_category: vocal · Vocoder-processed vocal_

🟣 MAIN — 901 characters ✓
```text
TARGET VOICE: Vocoder. Perform 'Vocal Timing Reference': 2:00 non-lexical vocal timing probe ('ah' vowel only, no words), 120 BPM, eleven regions: single voice pulses; note lengths articulation; contours leaps; registers; syncopation pickups; tuplets dotted; harmony stagger call response; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Vocal timing feature: every onset and offset lands exactly on the score position; staccato short, sustains full length, legato connected; breaths only in written rests; 120 BPM steady through every meter change; the vowel never becomes a word. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 960 characters ✓
```text
EXCLUDE for the Vocoder render of 'Vocal Timing Reference'. No lexical lyrics or words — the non-lexical 'ah' vowel only; no spoken passages. Avoid other voice types taking the lead, especially: Lead vocal, Backing vocal, Choir, Whistle. No vibrato so heavy that onsets and offsets blur; no pitch correction artifacts, formant shifts or doubles that move the written timing; no melisma replacing notated single notes. No arrangement drift: no added ad-libs, no tempo drift, no meter re-grouping, no simplification of the contour, register, stagger and asymmetric-meter passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

## TARGET: Whistle (`whistle`)  [beta]
_category: vocal · Human whistle_

🟣 MAIN — 901 characters ✓
```text
TARGET VOICE: Whistle. Perform 'Vocal Timing Reference': 2:00 non-lexical vocal timing probe ('ah' vowel only, no words), 120 BPM, eleven regions: single voice pulses; note lengths articulation; contours leaps; registers; syncopation pickups; tuplets dotted; harmony stagger call response; meter 3 4; meter 6 8; meter 5 8; meter 7 8. Lanes/voices may differ by pitch only; onsets stay exactly on the written grid. Vocal timing feature: every onset and offset lands exactly on the score position; staccato short, sustains full length, legato connected; breaths only in written rests; 120 BPM steady through every meter change; the vowel never becomes a word. Keep movement order, tempo, harmony, contours and all calibration passages intact; the requested instrument stays dominant; no drift. III must contain the full chromatic run and clean 2nd-through-octave interval pairs ascending and descending.
```

🛑 EXCLUDE — 960 characters ✓
```text
EXCLUDE for the Whistle render of 'Vocal Timing Reference'. No lexical lyrics or words — the non-lexical 'ah' vowel only; no spoken passages. Avoid other voice types taking the lead, especially: Lead vocal, Backing vocal, Vocoder, Choir. No vibrato so heavy that onsets and offsets blur; no pitch correction artifacts, formant shifts or doubles that move the written timing; no melisma replacing notated single notes. No arrangement drift: no added ad-libs, no tempo drift, no meter re-grouping, no simplification of the contour, register, stagger and asymmetric-meter passages. No drum fills or cymbal crashes masking the calibration passages. No improvised melodies replacing the written ones. No key changes beyond the notated C-D-E finale journey. No distortion, tape stops, reversed audio or sweeps that alter the notation. No octave doublings that defeat the register tests. No shuffle or quantization of the even eighth notes outside the blues movement.
```

### Render log (fill after rendering)

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| conditioning source + sha256 | |
| keeper/reject | |
| deviations from canonical structure | |
| extraction performed? | |
| extracted target path/hash | |
| MIDI extracted? | |
| notes | |

