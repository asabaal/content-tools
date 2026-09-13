# Song analysis — hippie-activist.

Generated 2026-09-13T18:15:34.660666+00:00 by song_ingest 0.1.0 (local/open-source pipeline; reference MIDI treated as independent evidence, not ground truth).

## Suno Advanced Split target recommendations (canonical)

From the Suno Stem Target Recommender (extended mode, full mix). This is the Suno-taxonomy answer; PANNs output is supplemental only.

| status | target | confidence |
|---|---|---|
| 🟢 recommend_now | Backing vocal | 0.98 |
| 🟢 recommend_now | Organ | 0.96 |
| 🟢 recommend_now | Lead vocal | 0.91 |
| 🟢 recommend_now | Guitar | 0.91 |
| 🟢 recommend_now | Whistle | 0.89 |
| 🟢 recommend_now | Drums | 0.72 |
| 🟡 recommend_broad_target | Synth | 0.67 |
| 🟡 recommend_broad_target | Strings | 0.62 |
| 🟡 recommend_broad_target | Piano | 0.56 |
| 🟡 recommend_broad_target | Brass | 0.53 |
| 🟠 review_before_extracting | Didgeridoo | 0.30 |
| 🟠 review_before_extracting | Flute | 0.30 |
| 🟠 review_before_extracting | Steel drums | 0.30 |
| 🟠 review_before_extracting | Saxophone | 0.28 |
| 🟠 review_before_extracting | Vocoder | 0.27 |
| 🟠 review_before_extracting | Banjo | 0.25 |
| ⚪ not_recommended | Bass | 0.24 |
| ⚪ not_recommended | Choir | 0.15 |

Validation vs extracted stems (non-authoritative): 10 positive recommendations; stems without a matching recommendation: FX, Percussion, Bass.

## Instrument reconciliation

| stem | claim | assessment | strong detections |
|---|---|---|---|
| Backing Vocals | Backing Vocals | unclear (no strong evidence either way) | — |
| Bass | Bass | MISLABELED? (claim absent, other content strong) | fx |
| Brass | Brass | unclear (no strong evidence either way) | — |
| Drums | Drums | consistent + multi-instrument evidence | drums, percussion |
| FX | FX | unclear (no strong evidence either way) | — |
| Guitar | Guitar | consistent + multi-instrument evidence | guitar, fx |
| Keyboard | Keyboard | unclear (no strong evidence either way) | — |
| Percussion | Percussion | weakly consistent (label barely detected) | — |
| Strings | Strings | unclear (no strong evidence either way) | — |
| Synth | Synth | unclear (no strong evidence either way) | — |
| Vocals | Vocals | weakly consistent (label barely detected) | — |
| Woodwinds | Woodwinds | unclear (no strong evidence either way) | — |

- In mix but missing from stems: {}
- Much weaker in stems than mix: {}

## Local vs Suno reference MIDI — canonical ordinal pairing

Pairing is deterministic (export order: base MIDI = first stem). Similarity compares our transcription of a stem against Suno's transcription of the SAME stem; neither is ground truth.

| stem | reference | local notes | Suno notes | density ratio | pitch-hist cosine | similarity |
|---|---|---|---|---|---|---|
| Woodwinds | hippie activist..mid | 73 | 42 | 0.5724 | 0.5988 | 0.5755 |
| Brass | hippie activist.(1).mid | 226 | 543 | 0.4173 | 0.6979 | 0.6265 |
| FX | hippie activist.(2).mid | — | — | — | — | no local transcription (V0 scope) |
| Synth | hippie activist.(3).mid | 982 | 1491 | 0.6604 | 0.9067 | 0.8022 |
| Strings | hippie activist.(4).mid | 128 | 182 | 0.6956 | 0.1773 | 0.4223 |
| Percussion | hippie activist.(5).mid | — | — | — | — | no local transcription (V0 scope) |
| Keyboard | hippie activist.(6).mid | 1712 | 1348 | 0.7867 | 0.8532 | 0.8063 |
| Guitar | hippie activist.(7).mid | 1789 | 1237 | 0.6894 | 0.9835 | 0.8622 |
| Bass | hippie activist.(8).mid | 990 | 1353 | 0.734 | 0.4443 | 0.5586 |
| Drums | hippie activist.(9).mid | — | — | — | — | no local transcription (V0 scope) |
| Backing Vocals | hippie activist.(10).mid | — | — | — | — | no local transcription (V0 scope) |
| Vocals | hippie activist.(11).mid | — | — | — | — | no local transcription (V0 scope) |

## Local MIDI transcriptions (Basic Pitch)

| stem | notes |
|---|---|
| Bass | 990 |
| Brass | 226 |
| Guitar | 1789 |
| Keyboard | 1712 |
| Strings | 128 |
| Synth | 982 |
| Woodwinds | 73 |

## Vocal transcription (faster-whisper, raw preserved)

| pass | segments | words |
|---|---|---|
| backing_vocals | 35 | 302 |
| vocals | 35 | 342 |
| combined | 49 | 335 |

