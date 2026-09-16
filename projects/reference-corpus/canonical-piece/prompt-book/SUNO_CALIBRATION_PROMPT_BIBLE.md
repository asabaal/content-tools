# Suno Calibration Prompt Bible — Solo/Lead Generation Prompts

_Generated 2026-09-16T19:57:56.281269+00:00 · 90 calibration instruments · SOLO + LEAD attempt per instrument · every prompt ≤ 1000 characters._

> **SUPERSESSION NOTE.** This Bible replaces the MAIN/EXCLUDE prompts of `SUNO_RENDERING_PROMPT_BOOK.md` for CALIBRATION GENERATION ONLY. That book remains the authoritative source for per-target CONDITIONING prompts (audio uploaded to condition a render). Older generation prompts are preserved in Git history and in `validation-report.json` lineage.

## Strategy

One instrument at a time. ~60-second clip. Two attempts:

1. **SOLO / ISOLATION** — the target instrument is the only musical instrument present. Natural resonance, mechanical noise, breath and playing character are welcome; everything else is not.
2. **FEATURED-LEAD** — the target is the unmistakable lead and primary sonic subject; sparse subordinate support allowed, never competing, never disappearing.

Human-in-the-loop workflow: generate the instrument's Solo attempt, listen/audit; generate the Lead attempt, listen/audit; refine if necessary; approve; move to the next instrument.

## Calibration sequence

1. `organ`
2. `piano`
3. `electric_piano`
4. `keyboards`
5. `celesta`
6. `harpsichord`
7. `melodica`
8. `guitar`
9. `acoustic_guitar`
10. `electric_guitar`
11. `lead_guitar`
12. `rhythm_electric_guitar`
13. `rhythm_acoustic_guitar`
14. `slide_guitar`
15. `ukulele`
16. `bass`
17. `bass_guitar`
18. `upright_bass`
19. `eight_zero_eight`
20. `strings`
21. `violin`
22. `fiddle`
23. `viola`
24. `cello`
25. `double_bass`
26. `harp`
27. `mandolin`
28. `banjo`
29. `sitar`
30. `koto`
31. `orchestra`
32. `woodwinds`
33. `flute`
34. `piccolo`
35. `oboe`
36. `clarinet`
37. `bassoon`
38. `saxophone`
39. `alto_saxophone`
40. `tenor_saxophone`
41. `baritone_saxophone`
42. `harmonica`
43. `brass`
44. `trumpet`
45. `trombone`
46. `french_horn`
47. `tuba`
48. `synth`
49. `synth_lead`
50. `synth_keys`
51. `synth_pad`
52. `synth_bass`
53. `synth_brass`
54. `synth_strings`
55. `arpeggiator`
56. `drone`
57. `theremin`
58. `risers`
59. `drums`
60. `kick`
61. `snare`
62. `hi_hat`
63. `cymbals`
64. `clap`
65. `percussion`
66. `tambourine`
67. `shaker`
68. `bells`
69. `glockenspiel`
70. `marimba`
71. `vibraphone`
72. `xylophone`
73. `timpani`
74. `steel_drums`
75. `music_box`
76. `bongos`
77. `congas`
78. `djembe`
79. `tabla`
80. `taiko`
81. `cowbell`
82. `lead_vocal`
83. `backing_vocal`
84. `choir`
85. `vocoder`
86. `whistle`
87. `accordion`
88. `bagpipes`
89. `didgeridoo`
90. `other`

---

## TARGET: Organ (`organ`) — _keyboard_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 774 characters
```text
Organ solo reference recording. A single organ, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. open with a full-voiced sustained chord, move to a single-line melody over held chords, add registration/timbre shifts, finish with a slow swelled chord full keyboard, favoring the rich mid register legato sweeps, held chords, sharp staccato jabs; articulation comes from key attack and release, not decay Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 663 characters
```text
Organ featured-lead performance. The organ is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. open with a full-voiced sustained chord, move to a single-line melody over held chords, add registration/timbre shifts, finish with a slow swelled chord full keyboard, favoring the rich mid register legato sweeps, held chords, sharp staccato jabs; articulation comes from key attack and release, not decay Supporting context: light unobtrusive bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the organ.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Piano (`piano`) — _keyboard_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 722 characters
```text
Piano solo reference recording. A single piano, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. lone single-line melody, then arpeggios, then full chords, then bass-register octaves; pedal half-pedal color; finish with a long decaying chord low bass register to sparkling top legato pedaled phrases vs dry staccato; wide dynamic swings from pp to ff Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 626 characters
```text
Piano featured-lead performance. The piano is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. lone single-line melody, then arpeggios, then full chords, then bass-register octaves; pedal half-pedal color; finish with a long decaying chord low bass register to sparkling top legato pedaled phrases vs dry staccato; wide dynamic swings from pp to ff Supporting context: very light brushed drums or soft bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the piano.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Electric piano (`electric_piano`) — _keyboard_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 675 characters
```text
Electric piano solo reference recording. A single electric piano, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. comping stabs, rolled chords, single-line melody with tremolo-shake accents, glissando mid register centered soft TouchScale dynamics; tine bark on hard strikes; sustain with gentle wobble Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 580 characters
```text
Electric piano featured-lead performance. The electric piano is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. comping stabs, rolled chords, single-line melody with tremolo-shake accents, glissando mid register centered soft TouchScale dynamics; tine bark on hard strikes; sustain with gentle wobble Supporting context: soft upright bass and brushes far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the electric piano.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Keyboards (`keyboards`) — _keyboard_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 615 characters
```text
Keyboards solo reference recording. A single keyboards, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. alternate chords, single lines and arpeggios; show both soft and bright patches full keyboard legato and staccato contrast, dynamic swells Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 498 characters
```text
Keyboards featured-lead performance. The keyboards is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. alternate chords, single lines and arpeggios; show both soft and bright patches full keyboard legato and staccato contrast, dynamic swells Supporting context: minimal bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the keyboards.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Celesta (`celesta`) — _keyboard_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 588 characters
```text
Celesta solo reference recording. A single celesta, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. sparse high melodies, gentle arpeggios, paired notes high register light touch, crystalline attacks, let tails ring Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 470 characters
```text
Celesta featured-lead performance. The celesta is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. sparse high melodies, gentle arpeggios, paired notes high register light touch, crystalline attacks, let tails ring Supporting context: soft warm pad far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the celesta.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Harpsichord (`harpsichord`) — _keyboard_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 638 characters
```text
Harpsichord solo reference recording. A single harpsichord, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. ornamented lines, trills, rolled chords, terraced echo dynamics between registers mid-to-high register crisp detached notes, ornaments, repeated-note figures Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 538 characters
```text
Harpsichord featured-lead performance. The harpsichord is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. ornamented lines, trills, rolled chords, terraced echo dynamics between registers mid-to-high register crisp detached notes, ornaments, repeated-note figures Supporting context: light cello-style bass line far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the harpsichord.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Melodica (`melodica`) — _keyboard_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 630 characters
```text
Melodica solo reference recording. A single melodica, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. single-line melodies with audible breath phrasing, short stabs, tremolo mid-to-high reedy register breath-attack tongueing, dynamic swells following breath Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 516 characters
```text
Melodica featured-lead performance. The melodica is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. single-line melodies with audible breath phrasing, short stabs, tremolo mid-to-high reedy register breath-attack tongueing, dynamic swells following breath Supporting context: sparse soft bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the melodica.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Guitar (`guitar`) — _guitar_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 608 characters
```text
Guitar solo reference recording. A single guitar, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. strummed chords, fingerpicking, single-line runs, bends, harmonics full guitar range palm-muted vs open, bends, slides, natural harmonics Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 492 characters
```text
Guitar featured-lead performance. The guitar is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. strummed chords, fingerpicking, single-line runs, bends, harmonics full guitar range palm-muted vs open, bends, slides, natural harmonics Supporting context: sparse soft bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the guitar.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Acoustic guitar (`acoustic_guitar`) — _guitar_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 639 characters
```text
Acoustic guitar solo reference recording. A single acoustic guitar, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. strummed progressions, Travis-style fingerpicking, hammer-ons/pull-offs, percussive body hits warm mid register open ringing chords vs muted precision Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 536 characters
```text
Acoustic guitar featured-lead performance. The acoustic guitar is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. strummed progressions, Travis-style fingerpicking, hammer-ons/pull-offs, percussive body hits warm mid register open ringing chords vs muted precision Supporting context: occasional soft bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the acoustic guitar.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Electric guitar (`electric_guitar`) — _guitar_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 633 characters
```text
Electric guitar solo reference recording. A single electric guitar, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. clean comping, driven chords, single-note runs, bends, vibrato, harmonics full electric register palm muting, bends, slides, pick attack variety Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 537 characters
```text
Electric guitar featured-lead performance. The electric guitar is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. clean comping, driven chords, single-note runs, bends, vibrato, harmonics full electric register palm muting, bends, slides, pick attack variety Supporting context: sparse bass and light drums far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the electric guitar.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Lead guitar (`lead_guitar`) — _guitar_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 604 characters
```text
Lead guitar solo reference recording. A single lead guitar, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. expressive bends, vibrato, fast runs, sustain shaping, harmonics lead register legato slides, wide vibrato, dynamic picking Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 504 characters
```text
Lead guitar featured-lead performance. The lead guitar is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. expressive bends, vibrato, fast runs, sustain shaping, harmonics lead register legato slides, wide vibrato, dynamic picking Supporting context: sparse bass and light drums far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the lead guitar.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Rhythm electric guitar (`rhythm_electric_guitar`) — _guitar_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 645 characters
```text
Rhythm electric guitar solo reference recording. A single rhythm electric guitar, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. chord-groove patterns, muted 16th chugs, voicing changes, dynamic pushes mid chord register tight palm muting vs open chords, accent placement Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 554 characters
```text
Rhythm electric guitar featured-lead performance. The rhythm electric guitar is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. chord-groove patterns, muted 16th chugs, voicing changes, dynamic pushes mid chord register tight palm muting vs open chords, accent placement Supporting context: sparse bass-and-drums bed far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the rhythm electric guitar.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Rhythm acoustic guitar (`rhythm_acoustic_guitar`) — _guitar_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 632 characters
```text
Rhythm acoustic guitar solo reference recording. A single rhythm acoustic guitar, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. strumming pattern variety, dynamic swells, muted percussive strums mid chord register accents on/off the beat, tight muted strums Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 527 characters
```text
Rhythm acoustic guitar featured-lead performance. The rhythm acoustic guitar is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. strumming pattern variety, dynamic swells, muted percussive strums mid chord register accents on/off the beat, tight muted strums Supporting context: sparse bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the rhythm acoustic guitar.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Slide guitar (`slide_guitar`) — _guitar_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 619 characters
```text
Slide guitar solo reference recording. A single slide guitar, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. bottleneck glissandi, sustained slide vibrato, open-tuning chords mid register smooth slides into exact pitches, behind-the-nut textures Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 504 characters
```text
Slide guitar featured-lead performance. The slide guitar is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. bottleneck glissandi, sustained slide vibrato, open-tuning chords mid register smooth slides into exact pitches, behind-the-nut textures Supporting context: sparse bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the slide guitar.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Ukulele (`ukulele`) — _guitar_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 593 characters
```text
Ukulele solo reference recording. A single ukulele, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. bright strumming patterns, fingerpicks, chunky muted strums compact high register rapid strumming, light staccato chunks Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 478 characters
```text
Ukulele featured-lead performance. The ukulele is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. bright strumming patterns, fingerpicks, chunky muted strums compact high register rapid strumming, light staccato chunks Supporting context: sparse soft bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the ukulele.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Bass (`bass`) — _bass_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 580 characters
```text
Bass solo reference recording. A single bass, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. walking lines, groove patterns, slides, octaves, held pedals low register tight vs sustained, ghost notes, slides Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 470 characters
```text
Bass featured-lead performance. The bass is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. walking lines, groove patterns, slides, octaves, held pedals low register tight vs sustained, ghost notes, slides Supporting context: sparse unobtrusive drums far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the bass.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Bass guitar (`bass_guitar`) — _bass_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 598 characters
```text
Bass guitar solo reference recording. A single bass guitar, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. fingerstyle grooves, picked lines, slides, hammer-ons, harmonics low register punchy gates, slides, muted ghost notes Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 489 characters
```text
Bass guitar featured-lead performance. The bass guitar is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. fingerstyle grooves, picked lines, slides, hammer-ons, harmonics low register punchy gates, slides, muted ghost notes Supporting context: sparse light drums far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the bass guitar.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Upright bass (`upright_bass`) — _bass_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 595 characters
```text
Upright bass solo reference recording. A single upright bass, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. jazz walking lines, arco sustained swells, slaps deepest acoustic register thumpy pizzicato, singing arco, slaps Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 488 characters
```text
Upright bass featured-lead performance. The upright bass is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. jazz walking lines, arco sustained swells, slaps deepest acoustic register thumpy pizzicato, singing arco, slaps Supporting context: brushed cymbal wash far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the upright bass.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: 808 (`eight_zero_eight`) — _bass_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 586 characters
```text
808 solo reference recording. A single 808, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. gliding sub lines, booming hits with pitch slides, long decays sub register saturated sustain, pitch glide, hard restarts Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 471 characters
```text
808 featured-lead performance. The 808 is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. gliding sub lines, booming hits with pitch slides, long decays sub register saturated sustain, pitch glide, hard restarts Supporting context: sparse tight hi-hats far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the 808.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Strings (`strings`) — _strings_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 634 characters
```text
Strings solo reference recording. A single strings, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. sustained chord swells, unison melodic lines, pizzicato passages, tremolo waves wide orchestral register legato bows, detaché, pizzicato, tremolo, dynamic swells Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 519 characters
```text
Strings featured-lead performance. The strings is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. sustained chord swells, unison melodic lines, pizzicato passages, tremolo waves wide orchestral register legato bows, detaché, pizzicato, tremolo, dynamic swells Supporting context: sparse soft bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the strings.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Violin (`violin`) — _strings_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 607 characters
```text
Violin solo reference recording. A single violin, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. lyrical melodies, double stops, spiccato runs, wide vibrato, harmonics high expressive register legato bowing, spiccato, martelé accents Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 498 characters
```text
Violin featured-lead performance. The violin is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. lyrical melodies, double stops, spiccato runs, wide vibrato, harmonics high expressive register legato bowing, spiccato, martelé accents Supporting context: soft piano or low drone far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the violin.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Fiddle (`fiddle`) — _strings_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 596 characters
```text
Fiddle solo reference recording. A single fiddle, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. dance-reel figures, droning open strings, double-stop shuffles, chops high folk register driving bow rhythms, slides, accents Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 484 characters
```text
Fiddle featured-lead performance. The fiddle is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. dance-reel figures, droning open strings, double-stop shuffles, chops high folk register driving bow rhythms, slides, accents Supporting context: occasional soft bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the fiddle.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Viola (`viola`) — _strings_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 584 characters
```text
Viola solo reference recording. A single viola, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. sustained inner-voice chords, mellow melodies, gentle pizzicato mid string register legato, detache, soft pizzicato Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 469 characters
```text
Viola featured-lead performance. The viola is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. sustained inner-voice chords, mellow melodies, gentle pizzicato mid string register legato, detache, soft pizzicato Supporting context: sparse low strings far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the viola.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Cello (`cello`) — _strings_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 624 characters
```text
Cello solo reference recording. A single cello, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. long singing melodies, rich double stops, pizzicato bass lines, dramatic swells low-to-mid expressive register broad legato, spiccato, sul ponticello color Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 507 characters
```text
Cello featured-lead performance. The cello is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. long singing melodies, rich double stops, pizzicato bass lines, dramatic swells low-to-mid expressive register broad legato, spiccato, sul ponticello color Supporting context: sparse low drone far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the cello.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Double bass (`double_bass`) — _strings_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 594 characters
```text
Double bass solo reference recording. A single double bass, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. sustained low lines, pizzicato walking, resonant swells deepest orchestral register broad bows, rounded pizzicato Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 485 characters
```text
Double bass featured-lead performance. The double bass is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. sustained low lines, pizzicato walking, resonant swells deepest orchestral register broad bows, rounded pizzicato Supporting context: sparse mid strings far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the double bass.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Harp (`harp`) — _strings_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 601 characters
```text
Harp solo reference recording. A single harp, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. rolled chords, flowing arpeggios, sweeping glissandi, harmonics very wide plucked register felty plucks, ringing decays, damped muting Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 484 characters
```text
Harp featured-lead performance. The harp is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. rolled chords, flowing arpeggios, sweeping glissandi, harmonics very wide plucked register felty plucks, ringing decays, damped muting Supporting context: none; harp is self-sufficient — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the harp.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Mandolin (`mandolin`) — _strings_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 609 characters
```text
Mandolin solo reference recording. A single mandolin, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. tremolo melodies, cross-picking, fast fiddle-style runs, chop chords high paired-string register constant tremolo shimmer, sharp picks Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 496 characters
```text
Mandolin featured-lead performance. The mandolin is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. tremolo melodies, cross-picking, fast fiddle-style runs, chop chords high paired-string register constant tremolo shimmer, sharp picks Supporting context: occasional guitar far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the mandolin.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Banjo (`banjo`) — _strings_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 598 characters
```text
Banjo solo reference recording. A single banjo, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. rolling fingerpicks, drone-string figures, speed runs, drop-thumb bright plucked register snappy attacks, ringing drone vs damped Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 480 characters
```text
Banjo featured-lead performance. The banjo is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. rolling fingerpicks, drone-string figures, speed runs, drop-thumb bright plucked register snappy attacks, ringing drone vs damped Supporting context: occasional bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the banjo.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Sitar (`sitar`) — _strings_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 617 characters
```text
Sitar solo reference recording. A single sitar, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. meend slides into pitches, jawari buzz, slow alap then rhythmic compositions wide microtonal register pulls (meend), rapid passages, resonant drones Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 514 characters
```text
Sitar featured-lead performance. The sitar is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. meend slides into pitches, jawari buzz, slow alap then rhythmic compositions wide microtonal register pulls (meend), rapid passages, resonant drones Supporting context: occasional tanpura-style drone far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the sitar.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Koto (`koto`) — _strings_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 585 characters
```text
Koto solo reference recording. A single koto, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. descending figures, pitch presses, graduated string plucks wide zither register plucks, suri glides, left-hand presses Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 443 characters
```text
Koto featured-lead performance. The koto is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. descending figures, pitch presses, graduated string plucks wide zither register plucks, suri glides, left-hand presses Supporting context: none — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the koto.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Orchestra (`orchestra`) — _strings_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 607 characters
```text
Orchestra solo reference recording. A single orchestra, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. one short arch: strings theme, wind answer, brass peak, timpani close full orchestra section-by-section contrast, unified dynamics Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 506 characters
```text
Orchestra featured-lead performance. The orchestra is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. one short arch: strings theme, wind answer, brass peak, timpani close full orchestra section-by-section contrast, unified dynamics Supporting context: none; the ensemble itself is the subject — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the orchestra.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Woodwinds (`woodwinds`) — _woodwind_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 583 characters
```text
Woodwinds solo reference recording. A single woodwinds, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. blended chord swells, unison lines, staggered entries wide woodwind register soft tongueing, legato blends Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 468 characters
```text
Woodwinds featured-lead performance. The woodwinds is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. blended chord swells, unison lines, staggered entries wide woodwind register soft tongueing, legato blends Supporting context: sparse strings far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the woodwinds.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Flute (`flute`) — _woodwind_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 587 characters
```text
Flute solo reference recording. A single flute, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. fast chromatic runs, bird-like figures, breathy tones, wide leaps high register single/double tonguing, breath accents Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 477 characters
```text
Flute featured-lead performance. The flute is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. fast chromatic runs, bird-like figures, breathy tones, wide leaps high register single/double tonguing, breath accents Supporting context: sparse harp-like chords far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the flute.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Piccolo (`piccolo`) — _woodwind_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 568 characters
```text
Piccolo solo reference recording. A single piccolo, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. sparkling high figures, trills, cutting melodic lines very high register crisp tonguing, trills Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 429 characters
```text
Piccolo featured-lead performance. The piccolo is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. sparkling high figures, trills, cutting melodic lines very high register crisp tonguing, trills Supporting context: none — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the piccolo.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Oboe (`oboe`) — _woodwind_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 604 characters
```text
Oboe solo reference recording. A single oboe, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. long expressive cantilena, pastoral figures, dynamic control at both extremes mid-high reedy register smooth tongueing, expressive swells Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 489 characters
```text
Oboe featured-lead performance. The oboe is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. long expressive cantilena, pastoral figures, dynamic control at both extremes mid-high reedy register smooth tongueing, expressive swells Supporting context: sparse soft strings far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the oboe.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Clarinet (`clarinet`) — _woodwind_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 599 characters
```text
Clarinet solo reference recording. A single clarinet, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. liquid legato lines, chalumeau-low figures, wide leaps, glissandi wide reedy register legato tongueing, whisper-soft to full Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 488 characters
```text
Clarinet featured-lead performance. The clarinet is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. liquid legato lines, chalumeau-low figures, wide leaps, glissandi wide reedy register legato tongueing, whisper-soft to full Supporting context: sparse soft strings far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the clarinet.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Bassoon (`bassoon`) — _woodwind_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 606 characters
```text
Bassoon solo reference recording. A single bassoon, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. staccato low figures, singing mid-register lines, rapid repeated notes low reedy register detached low notes, surprisingly agile runs Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 467 characters
```text
Bassoon featured-lead performance. The bassoon is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. staccato low figures, singing mid-register lines, rapid repeated notes low reedy register detached low notes, surprisingly agile runs Supporting context: none — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the bassoon.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Saxophone (`saxophone`) — _woodwind_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 623 characters
```text
Saxophone solo reference recording. A single saxophone, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. breathy ballad phrases, punchy rhythmic figures, growl and subtone colors, fast runs wide sax register tongued accents, slurs, ghost notes, growls Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 521 characters
```text
Saxophone featured-lead performance. The saxophone is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. breathy ballad phrases, punchy rhythmic figures, growl and subtone colors, fast runs wide sax register tongued accents, slurs, ghost notes, growls Supporting context: sparse hammond-style chords far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the saxophone.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Alto saxophone (`alto_saxophone`) — _woodwind_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 610 characters
```text
Alto saxophone solo reference recording. A single alto saxophone, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. nimble bebop-style lines, lyrical phrases, alt-register brightness mid-high sax register flexible tongueing, slurs, accents Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 505 characters
```text
Alto saxophone featured-lead performance. The alto saxophone is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. nimble bebop-style lines, lyrical phrases, alt-register brightness mid-high sax register flexible tongueing, slurs, accents Supporting context: sparse organ chords far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the alto saxophone.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Tenor saxophone (`tenor_saxophone`) — _woodwind_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 604 characters
```text
Tenor saxophone solo reference recording. A single tenor saxophone, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. ballad breathiness, hard-driving rhythm figures, subtone to full-ball mid sax register slurs, smears, ghosted notes Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 500 characters
```text
Tenor saxophone featured-lead performance. The tenor saxophone is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. ballad breathiness, hard-driving rhythm figures, subtone to full-ball mid sax register slurs, smears, ghosted notes Supporting context: sparse organ chords far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the tenor saxophone.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Baritone saxophone (`baritone_saxophone`) — _woodwind_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 608 characters
```text
Baritone saxophone solo reference recording. A single baritone saxophone, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. low honking figures, foundation lines, surprisingly agile runs low sax register fat tongueed attacks, slap tongue Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 499 characters
```text
Baritone saxophone featured-lead performance. The baritone saxophone is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. low honking figures, foundation lines, surprisingly agile runs low sax register fat tongueed attacks, slap tongue Supporting context: sparse bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the baritone saxophone.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Harmonica (`harmonica`) — _other_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 607 characters
```text
Harmonica solo reference recording. A single harmonica, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. cross-drawn bends, wails, train rhythms, chord.vamp breathing compact reed register bent notes, tongue-block chord stabs, hand wah Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 491 characters
```text
Harmonica featured-lead performance. The harmonica is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. cross-drawn bends, wails, train rhythms, chord.vamp breathing compact reed register bent notes, tongue-block chord stabs, hand wah Supporting context: sparse guitar far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the harmonica.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Brass (`brass`) — _brass_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 595 characters
```text
Brass solo reference recording. A single brass, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. chorale chords, stabs, swells, falls, doits, unified articulation wide brass register accented attacks, marcato, smooth swells Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 483 characters
```text
Brass featured-lead performance. The brass is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. chorale chords, stabs, swells, falls, doits, unified articulation wide brass register accented attacks, marcato, smooth swells Supporting context: sparse rhythm section far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the brass.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Trumpet (`trumpet`) — _brass_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 615 characters
```text
Trumpet solo reference recording. A single trumpet, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. fanfare figures, lyrical mid-register lines, shakes, falls, Harmon mute color bright lead register tongued attacks, shakes, plunger/mute color Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 505 characters
```text
Trumpet featured-lead performance. The trumpet is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. fanfare figures, lyrical mid-register lines, shakes, falls, Harmon mute color bright lead register tongued attacks, shakes, plunger/mute color Supporting context: sparse rhythm section far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the trumpet.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Trombone (`trombone`) — _brass_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 606 characters
```text
Trombone solo reference recording. A single trombone, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. glissandi, warm ballad lines, punchy stabs, plunger mute talk mid-low brass register slide glissandi, marcato stabs, legato phrases Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 497 characters
```text
Trombone featured-lead performance. The trombone is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. glissandi, warm ballad lines, punchy stabs, plunger mute talk mid-low brass register slide glissandi, marcato stabs, legato phrases Supporting context: sparse rhythm section far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the trombone.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: French horn (`french_horn`) — _brass_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 623 characters
```text
French horn solo reference recording. A single french horn, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. sustained harmonies, hunting-style figures, stopped-horn color, long swells mid brass register smooth legato, stopped accents, hand-mute color Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 515 characters
```text
French horn featured-lead performance. The french horn is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. sustained harmonies, hunting-style figures, stopped-horn color, long swells mid brass register smooth legato, stopped accents, hand-mute color Supporting context: sparse soft strings far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the french horn.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Tuba (`tuba`) — _brass_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 611 characters
```text
Tuba solo reference recording. A single tuba, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. oom-pah foundation lines, melodic low passages, dynamic swells lowest brass register round attacks, clear note separation, breath-length phrases Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 469 characters
```text
Tuba featured-lead performance. The tuba is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. oom-pah foundation lines, melodic low passages, dynamic swells lowest brass register round attacks, clear note separation, breath-length phrases Supporting context: none — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the tuba.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Synth (`synth`) — _synth_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 635 characters
```text
Synth solo reference recording. A single synth, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. single-line lead with portamento, chord stabs, arpeggios, filter sweeps, register jumps full range sharp envelopes vs slow filter swells; staccato and legato contrast Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 519 characters
```text
Synth featured-lead performance. The synth is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. single-line lead with portamento, chord stabs, arpeggios, filter sweeps, register jumps full range sharp envelopes vs slow filter swells; staccato and legato contrast Supporting context: minimal soft bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the synth.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Synth lead (`synth_lead`) — _synth_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 633 characters
```text
Synth lead solo reference recording. A single synth lead, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. portamento slides, pitch-bend expressions, fast runs, held notes with filter movement lead register legato slides, trills, vibrato via slow pitch movement Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 517 characters
```text
Synth lead featured-lead performance. The synth lead is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. portamento slides, pitch-bend expressions, fast runs, held notes with filter movement lead register legato slides, trills, vibrato via slow pitch movement Supporting context: minimal bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the synth lead.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Synth keys (`synth_keys`) — _synth_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 594 characters
```text
Synth keys solo reference recording. A single synth keys, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. rhythmic comping stabs, short lead phrases, chord punches mid register tight stabs with fast release vs held chords Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 487 characters
```text
Synth keys featured-lead performance. The synth keys is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. rhythmic comping stabs, short lead phrases, chord punches mid register tight stabs with fast release vs held chords Supporting context: sparse drums and bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the synth keys.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Synth pad (`synth_pad`) — _synth_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 645 characters
```text
Synth pad solo reference recording. A single synth pad, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. slow evolving chord changes, subtle internal movement, gentle filter opening wide sustained register very slow swells, no percussive attacks; dynamics by slow crescendo Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 554 characters
```text
Synth pad featured-lead performance. The synth pad is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. slow evolving chord changes, subtle internal movement, gentle filter opening wide sustained register very slow swells, no percussive attacks; dynamics by slow crescendo Supporting context: a sparse slow melodic line far above is acceptable — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the synth pad.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Synth bass (`synth_bass`) — _synth_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 596 characters
```text
Synth bass solo reference recording. A single synth bass, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. repeating filtered figures, octave jumps, slide accents low electronic register gated envelopes, filter opens, slides Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 480 characters
```text
Synth bass featured-lead performance. The synth bass is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. repeating filtered figures, octave jumps, slide accents low electronic register gated envelopes, filter opens, slides Supporting context: sparse drums far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the synth bass.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Synth brass (`synth_brass`) — _synth_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 602 characters
```text
Synth brass solo reference recording. A single synth brass, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. staccato chord stabs, swelled hits, short fanfare phrases mid register tight envelope attacks, accented hits, slow swells Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 496 characters
```text
Synth brass featured-lead performance. The synth brass is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. staccato chord stabs, swelled hits, short fanfare phrases mid register tight envelope attacks, accented hits, slow swells Supporting context: sparse drums and bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the synth brass.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Synth strings (`synth_strings`) — _synth_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 604 characters
```text
Synth strings solo reference recording. A single synth strings, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. slow chord progressions, gentle movement inside chords, swells wide register slow attacks, long sustains, soft releases Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 510 characters
```text
Synth strings featured-lead performance. The synth strings is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. slow chord progressions, gentle movement inside chords, swells wide register slow attacks, long sustains, soft releases Supporting context: a quiet solo melody far above is acceptable — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the synth strings.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Arpeggiator (`arpeggiator`) — _synth_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 662 characters
```text
Arpeggiator solo reference recording. A single arpeggiator, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. one chord held while the arpeggio pattern climbs and falls; pattern-rate and direction changes; gate-length variation wide register machine-even 16ths, tempo-locked, no humanization Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 546 characters
```text
Arpeggiator featured-lead performance. The arpeggiator is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. one chord held while the arpeggio pattern climbs and falls; pattern-rate and direction changes; gate-length variation wide register machine-even 16ths, tempo-locked, no humanization Supporting context: minimal pad far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the arpeggiator.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Drone (`drone`) — _synth_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 629 characters
```text
Drone solo reference recording. A single drone, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. one long held tone with slow overtone movement, slow beat frequencies, subtle intensity swell low-to-mid register no attacks; a single continuous swell and fade Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 510 characters
```text
Drone featured-lead performance. The drone is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. one long held tone with slow overtone movement, slow beat frequencies, subtle intensity swell low-to-mid register no attacks; a single continuous swell and fade Supporting context: none; this is a pure drone — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the drone.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Theremin (`theremin`) — _synth_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 631 characters
```text
Theremin solo reference recording. A single theremin, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. sliding glissando melodies, wide vibrato, extreme legato, sudden register jumps high expressive register everything connected; dynamics swell by volume-hand Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 515 characters
```text
Theremin featured-lead performance. The theremin is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. sliding glissando melodies, wide vibrato, extreme legato, sudden register jumps high expressive register everything connected; dynamics swell by volume-hand Supporting context: sparse low pad far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the theremin.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Risers (`risers`) — _synth_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 636 characters
```text
Risers solo reference recording. A single risers, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. one long upward sweep, a downward fall, short riser stabs; varying lengths and speeds full sweep range continuous acceleration of brightness and pitch, clean endings Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 510 characters
```text
Risers featured-lead performance. The risers is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. one long upward sweep, a downward fall, short riser stabs; varying lengths and speeds full sweep range continuous acceleration of brightness and pitch, clean endings Supporting context: none; risers alone — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the risers.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Drums (`drums`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 661 characters
```text
Drums solo reference recording. A single drums, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. grooves at varied densities, fills, ghost notes, rimshots, tom patterns, cymbal colors, tempo-locked and free passages kit-wide accents, ghost notes, open/closed contrast, buzz and press rolls Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 531 characters
```text
Drums featured-lead performance. The drums is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. grooves at varied densities, fills, ghost notes, rimshots, tom patterns, cymbal colors, tempo-locked and free passages kit-wide accents, ghost notes, open/closed contrast, buzz and press rolls Supporting context: none; kit alone — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the drums.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Kick (`kick`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 587 characters
```text
Kick solo reference recording. A single kick, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. varied spacings, double-stroke runs, dynamics from ghost to accented lowest lane tight low thump, muffled vs open beater Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 478 characters
```text
Kick featured-lead performance. The kick is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. varied spacings, double-stroke runs, dynamics from ghost to accented lowest lane tight low thump, muffled vs open beater Supporting context: occasional low click layer acceptable — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the kick.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Snare (`snare`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 600 characters
```text
Snare solo reference recording. A single snare, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. rudiments, rolls from soft to full, rim clicks, ghost-note grooves mid snare register crack accents vs ghost softness, buzz sustain Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 482 characters
```text
Snare featured-lead performance. The snare is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. rudiments, rolls from soft to full, rim clicks, ghost-note grooves mid snare register crack accents vs ghost softness, buzz sustain Supporting context: occasional kick far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the snare.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Hi-hat (`hi_hat`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 600 characters
```text
Hi-hat solo reference recording. A single hi-hat, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. eighth/sixteenth patterns, open-closed contrasts, foot splashes, accented taps high lane tight chick, sizzle open, pedal splashes Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 483 characters
```text
Hi-hat featured-lead performance. The hi-hat is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. eighth/sixteenth patterns, open-closed contrasts, foot splashes, accented taps high lane tight chick, sizzle open, pedal splashes Supporting context: occasional kick far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the hi-hat.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Cymbals (`cymbals`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 623 characters
```text
Cymbals solo reference recording. A single cymbals, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. crash accents with decay, ride pulse patterns, choked stabs, bowed-like swell high shimmer register attack then long shimmer, choke cuts, swell blooms Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 509 characters
```text
Cymbals featured-lead performance. The cymbals is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. crash accents with decay, ride pulse patterns, choked stabs, bowed-like swell high shimmer register attack then long shimmer, choke cuts, swell blooms Supporting context: sparse soft pulse far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the cymbals.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Clap (`clap`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 600 characters
```text
Clap solo reference recording. A single clap, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. single claps, rolling stacks, varied spacing, machine-tight grids vs human timing mid percussive lane sharp attack, tiny natural tail Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 458 characters
```text
Clap featured-lead performance. The clap is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. single claps, rolling stacks, varied spacing, machine-tight grids vs human timing mid percussive lane sharp attack, tiny natural tail Supporting context: none — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the clap.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Percussion (`percussion`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 615 characters
```text
Percussion solo reference recording. A single percussion, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. rotate among distinct unpitched hits and textures; vary density, accents and spacing percussion lanes varied strikes, mutes and textures Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 479 characters
```text
Percussion featured-lead performance. The percussion is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. rotate among distinct unpitched hits and textures; vary density, accents and spacing percussion lanes varied strikes, mutes and textures Supporting context: none — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the percussion.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Tambourine (`tambourine`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 599 characters
```text
Tambourine solo reference recording. A single tambourine, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. eighth/sixteenth shakes, thumb rolls, accented downbeats, knee clicks high jingle lane sustained shake vs single accents Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 486 characters
```text
Tambourine featured-lead performance. The tambourine is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. eighth/sixteenth shakes, thumb rolls, accented downbeats, knee clicks high jingle lane sustained shake vs single accents Supporting context: occasional kick far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the tambourine.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Shaker (`shaker`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 610 characters
```text
Shaker solo reference recording. A single shaker, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. even sixteenths with accent rotation, speed changes, direction reversals high granular lane consistent micro-accents, dynamics by intensity Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 470 characters
```text
Shaker featured-lead performance. The shaker is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. even sixteenths with accent rotation, speed changes, direction reversals high granular lane consistent micro-accents, dynamics by intensity Supporting context: none — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the shaker.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Bells (`bells`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 593 characters
```text
Bells solo reference recording. A single bells, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. sparse melodies, tolling repeated notes, gentle arpeggios with long decays high register clean strikes, let every decay ring Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 468 characters
```text
Bells featured-lead performance. The bells is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. sparse melodies, tolling repeated notes, gentle arpeggios with long decays high register clean strikes, let every decay ring Supporting context: soft pad far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the bells.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Glockenspiel (`glockenspiel`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 594 characters
```text
Glockenspiel solo reference recording. A single glockenspiel, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. high melodic figures, fast light runs, paired intervals very high register crisp attacks, natural ringing decay Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 481 characters
```text
Glockenspiel featured-lead performance. The glockenspiel is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. high melodic figures, fast light runs, paired intervals very high register crisp attacks, natural ringing decay Supporting context: soft warm pad far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the glockenspiel.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Marimba (`marimba`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 607 characters
```text
Marimba solo reference recording. A single marimba, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. rolling two-mallet lines, cross-rhythms, bass-note-plus-melody texture low-to-mid wooden register round mallet attacks, muting control Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 487 characters
```text
Marimba featured-lead performance. The marimba is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. rolling two-mallet lines, cross-rhythms, bass-note-plus-melody texture low-to-mid wooden register round mallet attacks, muting control Supporting context: soft shaker far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the marimba.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Vibraphone (`vibraphone`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 616 characters
```text
Vibraphone solo reference recording. A single vibraphone, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. long ringing melodies with tremolo speed changes, soft mallet chords, damping control mid-to-high register tremolo warmth, damped vs open Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 497 characters
```text
Vibraphone featured-lead performance. The vibraphone is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. long ringing melodies with tremolo speed changes, soft mallet chords, damping control mid-to-high register tremolo warmth, damped vs open Supporting context: soft bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the vibraphone.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Xylophone (`xylophone`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 588 characters
```text
Xylophone solo reference recording. A single xylophone, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. fast technical runs, glissandi, crisp rhythmic figures high wooden register sharp dry attacks, rapid repetition Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 451 characters
```text
Xylophone featured-lead performance. The xylophone is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. fast technical runs, glissandi, crisp rhythmic figures high wooden register sharp dry attacks, rapid repetition Supporting context: none — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the xylophone.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Timpani (`timpani`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 608 characters
```text
Timpani solo reference recording. A single timpani, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. marked hits, rolls from pp to ff, pitch-shift accents between two drums low kettle register deep mallet strokes, tuned accent intervals Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 469 characters
```text
Timpani featured-lead performance. The timpani is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. marked hits, rolls from pp to ff, pitch-shift accents between two drums low kettle register deep mallet strokes, tuned accent intervals Supporting context: none — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the timpani.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Steel drums (`steel_drums`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 607 characters
```text
Steel drums solo reference recording. A single steel drums, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. calypso-style melodic lines, rolls around the pan, bass-pan support figures mid register bouncy mallet attack, ringing sustain Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 499 characters
```text
Steel drums featured-lead performance. The steel drums is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. calypso-style melodic lines, rolls around the pan, bass-pan support figures mid register bouncy mallet attack, ringing sustain Supporting context: sparse light groove far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the steel drums.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Music box (`music_box`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 617 characters
```text
Music box solo reference recording. A single music box, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. simple high melodies with natural mechanical unevenness, slow winding-down feel very high tine register tiny plucked attacks, delicate decay Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 480 characters
```text
Music box featured-lead performance. The music box is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. simple high melodies with natural mechanical unevenness, slow winding-down feel very high tine register tiny plucked attacks, delicate decay Supporting context: none — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the music box.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Bongos (`bongos`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 612 characters
```text
Bongos solo reference recording. A single bongos, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. fast finger patterns, open/muted strokes, martillo accents, fills between drums high hand-drum register open tone vs muted tip strokes, slaps Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 497 characters
```text
Bongos featured-lead performance. The bongos is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. fast finger patterns, open/muted strokes, martillo accents, fills between drums high hand-drum register open tone vs muted tip strokes, slaps Supporting context: occasional shaker far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the bongos.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Congas (`congas`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 607 characters
```text
Congas solo reference recording. A single congas, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. tumbao patterns, open/muted/slap strokes, slow-to-fast phrase density mid hand-drum register bass tone, open tone, slap, heel-toe muting Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 492 characters
```text
Congas featured-lead performance. The congas is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. tumbao patterns, open/muted/slap strokes, slow-to-fast phrase density mid hand-drum register bass tone, open tone, slap, heel-toe muting Supporting context: occasional shaker far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the congas.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Djembe (`djembe`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 602 characters
```text
Djembe solo reference recording. A single djembe, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. bass/tone/slap vocabulary, speed builds, alternating-hand patterns wide hand-drum register deep bass, cutting slap, tone in between Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 493 characters
```text
Djembe featured-lead performance. The djembe is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. bass/tone/slap vocabulary, speed builds, alternating-hand patterns wide hand-drum register deep bass, cutting slap, tone in between Supporting context: occasional bell pattern far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the djembe.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Tabla (`tabla`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 620 characters
```text
Tabla solo reference recording. A single tabla, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. kayda-style phrase patterns, tuned ring strokes, fast tihai endings pitched tabla register finger tips, heel pressure pitch-bends, ringing open strokes Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 503 characters
```text
Tabla featured-lead performance. The tabla is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. kayda-style phrase patterns, tuned ring strokes, fast tihai endings pitched tabla register finger tips, heel pressure pitch-bends, ringing open strokes Supporting context: occasional drone far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the tabla.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Taiko (`taiko`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 634 characters
```text
Taiko solo reference recording. A single taiko, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. powerful synchronized patterns, dynamics from soft rim to full body hits, accelerating finishes very low register full-body impact with resonance, arm-weight strokes Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 522 characters
```text
Taiko featured-lead performance. The taiko is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. powerful synchronized patterns, dynamics from soft rim to full body hits, accelerating finishes very low register full-body impact with resonance, arm-weight strokes Supporting context: occasional deep voice far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the taiko.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Cowbell (`cowbell`) — _percussion_
_calibration family: percussion_timing_

### SOLO / ISOLATION ATTEMPT — 588 characters
```text
Cowbell solo reference recording. A single cowbell, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. syncopated bell patterns, spacing variation, accent displacement metallic mid lane wooden-stick ping, muted vs open Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 449 characters
```text
Cowbell featured-lead performance. The cowbell is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. syncopated bell patterns, spacing variation, accent displacement metallic mid lane wooden-stick ping, muted vs open Supporting context: none — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the cowbell.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Lead vocal (`lead_vocal`) — _vocal_
_calibration family: vocal_timing_

### SOLO / ISOLATION ATTEMPT — 617 characters
```text
Lead vocal solo reference recording. A single lead vocal, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. Non-lexical vocalise only ('ah' and 'oo'); no lyrics. non-lexical vocalise ('ah', 'oo'): long tones, fast runs, slides, breaths, soft-to-full dynamics expressive lead range legato phrases, staccato bursts, melisma, controlled breath Expose timbre, phrasing, breath, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 519 characters
```text
Lead vocal featured-lead performance. The lead vocal is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. Non-lexical vocalise ('ah'); no lyrics, no words. non-lexical vocalise ('ah', 'oo'): long tones, fast runs, slides, breaths, soft-to-full dynamics expressive lead range legato phrases, staccato bursts, melisma, controlled breath Supporting context: none in Solo mode — sparse, subordinate, never competing. The voice never disappears.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Backing vocal (`backing_vocal`) — _vocal_
_calibration family: vocal_timing_

### SOLO / ISOLATION ATTEMPT — 596 characters
```text
Backing vocal solo reference recording. A single backing vocal, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. Non-lexical vocalise only ('ah' and 'oo'); no lyrics. non-lexical 'ah'/'ooh' stacks, staggered entries, register contrasts, call-and-response supportive mid register soft onsets, held vowels, blend control Expose timbre, phrasing, breath, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 521 characters
```text
Backing vocal featured-lead performance. The backing vocal is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. Non-lexical vocalise ('ah'); no lyrics, no words. non-lexical 'ah'/'ooh' stacks, staggered entries, register contrasts, call-and-response supportive mid register soft onsets, held vowels, blend control Supporting context: none; the harmony voices are the subject — sparse, subordinate, never competing. The voice never disappears.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Choir (`choir`) — _vocal_
_calibration family: vocal_timing_

### SOLO / ISOLATION ATTEMPT — 567 characters
```text
Choir solo reference recording. A single choir, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. Non-lexical vocalise only ('ah' and 'oo'); no lyrics. sustained swells, staggered entries, homophonic motion, intimate-to-full dynamics wide choral range soft vowel attacks, long legato vowels Expose timbre, phrasing, breath, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 487 characters
```text
Choir featured-lead performance. The choir is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. Non-lexical vocalise ('ah'); no lyrics, no words. sustained swells, staggered entries, homophonic motion, intimate-to-full dynamics wide choral range soft vowel attacks, long legato vowels Supporting context: none beyond the choir's own harmony — sparse, subordinate, never competing. The voice never disappears.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Vocoder (`vocoder`) — _vocal_
_calibration family: vocal_timing_

### SOLO / ISOLATION ATTEMPT — 594 characters
```text
Vocoder solo reference recording. A single vocoder, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. Non-lexical vocalise only ('ah' and 'oo'); no lyrics. non-lexical vocoded 'ah' phrases tracking harmony, gated rhythm syllables, robot portamento mid electronic register gated syllabic attacks, smooth chord tracking Expose timbre, phrasing, breath, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 513 characters
```text
Vocoder featured-lead performance. The vocoder is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. Non-lexical vocalise ('ah'); no lyrics, no words. non-lexical vocoded 'ah' phrases tracking harmony, gated rhythm syllables, robot portamento mid electronic register gated syllabic attacks, smooth chord tracking Supporting context: sparse electronic bass far beneath — sparse, subordinate, never competing. The voice never disappears.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Whistle (`whistle`) — _vocal_
_calibration family: vocal_timing_

### SOLO / ISOLATION ATTEMPT — 597 characters
```text
Whistle solo reference recording. A single whistle, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. whistled tunes, trills, slides, dynamic breath control high whistle register clean attacks, legato slides, vibrato variation Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 482 characters
```text
Whistle featured-lead performance. The whistle is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. whistled tunes, trills, slides, dynamic breath control high whistle register clean attacks, legato slides, vibrato variation Supporting context: sparse soft bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the whistle.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Accordion (`accordion`) — _other_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 607 characters
```text
Accordion solo reference recording. A single accordion, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. bellows swells, musette shimmer, chord pulses, single-line songs wide reed register bellows attack, shake, dynamic bellows control Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 489 characters
```text
Accordion featured-lead performance. The accordion is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. bellows swells, musette shimmer, chord pulses, single-line songs wide reed register bellows attack, shake, dynamic bellows control Supporting context: sparse bass far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the accordion.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Bagpipes (`bagpipes`) — _other_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 631 characters
```text
Bagpipes solo reference recording. A single bagpipes, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. continuous air drone, ornamented chanter grace-note figures, no silence possible piercing high chanter register grace-note ornaments between sustained tones Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 528 characters
```text
Bagpipes featured-lead performance. The bagpipes is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. continuous air drone, ornamented chanter grace-note figures, no silence possible piercing high chanter register grace-note ornaments between sustained tones Supporting context: none; drones are part of the instrument — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the bagpipes.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Didgeridoo (`didgeridoo`) — _other_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 635 characters
```text
Didgeridoo solo reference recording. A single didgeridoo, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. circular-breathing drone, rhythmic tongue/diaphragm pulses, harmonic color changes very low drone register pulsed breathing patterns over a continuous drone Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 522 characters
```text
Didgeridoo featured-lead performance. The didgeridoo is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. circular-breathing drone, rhythmic tongue/diaphragm pulses, harmonic color changes very low drone register pulsed breathing patterns over a continuous drone Supporting context: occasional clap far beneath — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the didgeridoo.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

## TARGET: Other (`other`) — _other_
_calibration family: pitched_harmonic_

### SOLO / ISOLATION ATTEMPT — 642 characters
```text
Other solo reference recording. A single other, completely unaccompanied — no drums, no percussion, no bass, no pads, no drones, no accompaniment, no orchestration, no second instrument, no ensemble, no vocals, no ambient or cinematic bed. About sixty seconds. Instrument-reference performance, not a song. one clear identity shown solo: its tone, attack and behavior; do not montage many different instruments whatever the chosen element uses consistent, recognizable, repeatable Natural resonance, mechanical noise, breath and physical playing character are welcome. Expose timbre, attack, sustain, decay, dynamics and expressive character.
```

### FEATURED-LEAD ATTEMPT — 501 characters
```text
Other featured-lead performance. The other is the unmistakable lead and primary sonic subject for the entire sixty seconds. Instrument calibration reference, not a full song. one clear identity shown solo: its tone, attack and behavior; do not montage many different instruments whatever the chosen element uses consistent, recognizable, repeatable Supporting context: none — sparse, subordinate, never competing for lead status. No dense arrangement, no vocals, no extended passage without the other.
```

### Render log

| field | value |
|---|---|
| Suno model/version | |
| render ID | |
| generation date | |
| keeper/reject | |
| audit notes | |
| approved? | |

