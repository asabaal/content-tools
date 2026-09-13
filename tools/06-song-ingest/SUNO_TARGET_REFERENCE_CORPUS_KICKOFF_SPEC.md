# Suno Target Reference Corpus — Kickoff Specification

**Status:** Active — corrected after first local audition  
**Repository:** `asabaal/content-tools`  
**Branch:** `develop`  
**Related systems:** `tools/06-song-ingest`, existing Suno Stem Target Recommender, `asabaal/music_creation/reference_composition`  
**Primary calibration artifact:** one canonical reference composition, exactly four minutes long, rendered repeatedly across Suno Advanced Split target instruments

## 0. Current correction / authoritative constraints

This section supersedes any earlier implementation assumption that conflicts with it.

### 0.1 Exact duration

The canonical reference piece must be **exactly 4:00 / 240.000 seconds** of composition time.

Current 4:48 / 288-second artifacts are superseded and must be regenerated.

At the current fixed tempo of **100 BPM in 4/4**, exactly four minutes corresponds naturally to **100 bars**:

- 100 BPM = 0.6 seconds per beat
- 4 beats/bar = 2.4 seconds per bar
- 100 bars × 2.4 seconds = 240.0 seconds

The generator, movement contract, movement map, event manifest, tests, hashes, corpus ingest, prompt book, and all duration references must be updated together. Do not merely trim the existing 4:48 file while leaving its symbolic contract unchanged.

The **conditioning WAVs used as Suno inputs must also be exactly 240.000 seconds**. They must not carry an extra release tail beyond four minutes. A separate debug/audition file may contain a release tail if clearly labeled noncanonical and never used as Suno conditioning input.

### 0.2 Neutral conditioning input, not a multi-instrument mockup

The existing multi-GM audition render — piano + electric piano + acoustic bass + Choir Aahs + square lead + GM drums — is useful only for engineering/debugging. It is **not an acceptable Suno conditioning input**, because it injects instrumental/timbral claims into an experiment whose purpose is to ask Suno to supply the target instrumentation.

Preserve that render only as a diagnostic artifact and label it accordingly.

Before any target rendering in Suno, generate neutral conditioning versions of the exact same canonical score using the existing local tool ecosystem:

1. **Neutral piano input** — all pitched musical content represented with one clean piano timbre, with no choir, acoustic-bass patch, FX lead patch, or instrument-specific role patching.
2. **Neutral synth input** — the same symbolic material represented with one deliberately plain, low-character synth timbre (for example a basic sine/triangle/simple subtractive patch), again with no role-specific instrument identities.

The objective is to encode **notes, rhythm, harmony, register, movement order, articulation, and dynamics** while minimizing timbral contamination.

For special roles such as vocal, FX, bass, or percussion, do not switch to semantic GM instruments merely because of the role label. Use the same neutral timbral family wherever practical. If a role cannot be represented faithfully without a special treatment, document that treatment explicitly and keep it as timbrally neutral as possible.

The human artist must listen to both neutral inputs before the Suno corpus run begins. One may then be selected as the canonical conditioning representation, or both may be used in a small pilot if needed to determine which preserves structure while allowing Suno to replace timbre most effectively.

### 0.3 One-piece principle remains unchanged

There is still **one canonical composition**. Piano and synth conditioning files are two encodings of the same score, not separate compositions or etudes.

---

## 1. Purpose

Build an empirical **Suno Target Reference Corpus** that helps answer:

> Given an unknown song or stem, which documented Suno Advanced Split extraction targets are useful to extract as the initial editable instrumentation substrate for the canonical starter mix?

This is not merely an instrument-labeling exercise. The Advanced Split stage supports production: broad Suno default stems are refined into more useful artist-directed instrumental objects, which are then listened to and may receive an **artist canonical label** that differs from Suno's requested target name.

The corpus must be grounded in controlled reference audio, not only generic classifier labels.

Preserve these distinct layers:

1. **Composition ground truth** — our known notes, rhythms, chords, keys, structure, movement boundaries, roles, and timing.
2. **Neutral conditioning render** — timbrally minimal audio encoding of that score used to condition Suno.
3. **Suno target render** — Suno's realization of the same composition under a requested Advanced Split target/timbre.
4. **Suno extraction behavior** — any Advanced Split stem extracted from the render.
5. **Local analysis output** — embeddings, timbral descriptors, transcription, classifier evidence, similarity scores, etc.
6. **Suno labels** — provenance describing what was requested/extracted, not ontological truth.
7. **Artist canonical label** — the human artist's post-listening identification of what the extracted production object actually is and how it belongs in the canonical starter mix.

The immediate validation target remains `hippie activist.`.

---

## 2. Core Experimental Principle

The same underlying composition is rendered repeatedly across Suno target instruments. Pitch, harmony, rhythm, form, section timing, and diagnostic passages should stay constant as far as Suno permits while the requested instrument/timbre changes.

Conceptually:

```text
canonical_reference_piece.mid   (known symbolic truth, exactly 4:00)
        |
        +--> neutral piano input.wav  --+
        |                               |
        +--> neutral synth input.wav  --+--> artist selects/validates conditioning source
                                         |
                                         +--> Suno: Organ
                                         +--> Suno: Piano
                                         +--> Suno: Electric guitar
                                         +--> Suno: Strings
                                         +--> Suno: Brass
                                         +--> Suno: Synth pad
                                         +--> Suno: Woodwinds
                                         +--> ...
```

For each target render preserve the exact prompt, exclude prompt, conditioning-source hash, model/version, date, render ID, target ontology version, and extraction artifacts.

---

## 3. Repo Responsibilities

### 3.1 `asabaal/music_creation`

Own the canonical composition and symbolic truth:

- composition contract
- deterministic generator
- canonical MIDI
- MusicXML if practical
- exact 4:00 timing contract
- movement map
- exact note/chord/key metadata
- event manifest
- validators
- local diagnostic render tooling
- neutral piano conditioning render
- neutral synth conditioning render
- render provenance / hashes

Do not hand-author an opaque MIDI file without reproducible source.

### 3.2 `asabaal/content-tools`

Own:

- corpus organization
- conditioning/render provenance
- Suno target ontology linkage
- ingestion
- feature extraction
- comparison
- Advanced Split target recommendation
- prompt generation and validation
- benchmark/reporting
- artist-review metadata and canonical starter-mix labeling fields

Reuse the existing `tools/06-song-ingest` pipeline and existing Suno Stem Target Recommender rather than duplicating them.

---

## 4. Canonical Reference Piece

### 4.1 Duration and form

Create **one coherent piece exactly 4:00 / 240.000 seconds long**.

Keep the established nine-movement concept unless a clearly documented redistribution is required to fit the hard four-minute budget. Preserve all required calibration coverage while compressing the existing 120-bar / 4:48 design to the exact 100-bar / 4:00 contract at 100 BPM.

The piece should remain musically coherent rather than becoming a list of disconnected tests.

### 4.2 Required musical coverage

Within the same piece preserve deliberate coverage of:

#### Tonal/key coverage
- all 12 major keys
- all 12 minor keys
- controlled modulation
- clear tonal centers
- chromatic material

#### Scale and melodic coverage
- major scales
- natural/harmonic/melodic minor material
- chromatic runs
- arpeggios
- isolated-note passages
- stepwise melody
- intervallic melody
- repeated notes
- register sweeps

#### Interval coverage
Representative ascending and descending seconds through octaves.

#### Harmonic coverage
- major/minor triads
- inversions
- suspended chords
- dominant, major, and minor sevenths
- selected extensions
- dyads
- dense and sparse voicings

#### Common progression coverage
At minimum:
- I–IV–V–I
- ii–V–I
- I–V–vi–IV
- vi–IV–I–V
- representative minor cadence/progression
- blues-derived movement

#### Texture/performance coverage
- monophonic melody
- dyads
- polyphonic/counterpoint passage
- full chordal playing
- sparse/dense accompaniment
- sustained/legato
- staccato/articulated material
- repeated-note attacks
- syncopation
- low/mid/high register
- at least two musically interesting solo passages
- dense musical finale/climax
- bass-role behavior
- percussion/rhythm behavior
- vocal-role behavior
- FX/transition behavior

### 4.3 Ground-truth manifest

Every important event remains machine-readable, including section, key, role, group, pitch, onset, duration, velocity, and expected texture. The manifest must be regenerated from the corrected 4:00 score, not hand-edited.

---

## 5. Rendering and Conditioning Artifacts

Use explicit artifact classes so debug audio can never be confused with Suno input.

Recommended local naming:

```text
reference_composition/output/
  canonical_reference_piece.mid
  canonical_reference_piece_debug.wav
  canonical_reference_piece_piano_input.wav
  canonical_reference_piece_synth_input.wav
  event_manifest.json
  movement_map.json
  composition_version.json
  conditioning_render_notes.json
```

### Debug render

`canonical_reference_piece_debug.wav` may use contrasting role-specific GM patches for engineering purposes only. It must be marked **NOT FOR SUNO INPUT** in metadata/docs.

### Neutral piano input

`canonical_reference_piece_piano_input.wav`:

- exactly 240.000 seconds
- one clean piano timbral identity for pitched content
- no Choir Aahs
- no acoustic-bass-specific patch
- no square-lead FX patch
- no semantic instrument switching based on role labels
- score timing and dynamics preserved

### Neutral synth input

`canonical_reference_piece_synth_input.wav`:

- exactly 240.000 seconds
- one low-character synth family
- avoid pads, pronounced modulation, distortion, chorus, reverb, or expressive effects that create a strong instrument identity
- preserve score timing and dynamics
- role labels do not trigger semantic instrument substitutions

### Conditioning approval gate

Do not begin the 90-target Suno corpus run until the artist has listened to the corrected four-minute composition and neutral conditioning input(s).

---

## 6. Suno Target Taxonomy

Use the authoritative Advanced Split ontology recovered in `music_creation/analytics/suno_stem_target_recommender/`.

Current recovered project baseline: **90 targets** (22 standard + 68 beta), unless newer direct Suno evidence changes it.

Do not substitute AudioSet/PANNs labels for Suno target names. Generic detectors may provide supplemental evidence only.

---

## 7. Default Stems, Advanced Split, and Artist Canonical Labels

Keep these stages distinct:

```text
Suno generation
  -> Suno default broad stems
  -> artist + analysis choose useful Advanced Split targets
  -> Advanced Split extraction
  -> artist listens and identifies/relabels extracted production object
  -> canonical instrumentation map
  -> canonical starter-mix substrate
```

A Suno target label is an extraction request/provenance field, not necessarily the artist's final instrument identification.

Per extracted object preserve fields such as:

- `default_stem_label`
- `advanced_split_target_requested`
- `advanced_split_render_or_extraction_id`
- `artist_canonical_label`
- `artist_confidence`
- `artist_notes`
- `canonical_starter_mix_role`

Never overwrite the Suno label with the artist label; preserve both.

---

## 8. Reference Corpus Structure

A durable Content Tools shape should retain conditioning-source provenance:

```text
projects/reference-corpus/canonical-piece/
  composition-version.json
  movement-map.json
  conditioning/
    piano-input.json
    synth-input.json
  prompt-book/
  targets/
    organ/
      intended-render.wav
      suno-extracted-target.wav      # when available
      metadata.json
      prompt.txt
      exclude.txt
      analysis/
    ...
```

Large WAVs may remain local/gitignored according to repo policy; hashes, paths, and provenance must remain durable.

---

## 9. Feature and Similarity Strategy

The corpus should support:

- learned audio embeddings
- spectral/timbral descriptors
- register-aware descriptors
- pitch-normalized/reduced comparisons where useful
- attack/articulation features
- sustain/decay behavior
- harmonic/percussive ratios
- temporal texture/density
- optional CLAP-style semantic similarity

Unknown songs/default stems can then be compared against known Suno target exemplars rather than depending on one generic classifier.

---

## 10. MIDI Benchmarking

Because the composition starts from known symbolic truth:

```text
known MIDI
   -> neutral conditioning audio
   -> Suno target render
       -> local audio-to-MIDI
       -> Suno MIDI if available
```

Compare both transcriptions to the known score using note precision/recall/F1, onset/offset agreement, pitch/octave error, polyphony, register, timing drift, and density/chord behavior.

Suno MIDI is comparison evidence, never ground truth.

---

## 11. Suno Rendering Prompt Book

After the corrected 4:00 composition and movement map are regenerated, rebuild the prompt book from those artifacts.

The prompt book must accurately state:

- **exact duration: 4:00 / 240 seconds**
- corrected movement boundaries
- key/modulation journey
- harmonic/melodic/interval tests
- polyphonic/chordal tests
- articulation/register tests
- solos
- special-role sections
- conditioning-source instructions
- invariants across renders

For every target provide:

1. **🟣 MAIN / DEFAULT**
2. **🛑 EXCLUDE / AVOID**

Each individual prompt must be **900–1000 characters inclusive**, counted exactly. `<900` or `>1000` fails. No meaningless padding.

Prompt generation/tests must fail if stale 4:48 / 288-second wording survives anywhere in the generated prompt book or target metadata.

Each target render log should include:

- conditioning input used (`piano` or `synth` + SHA256)
- Suno model/version
- render ID
- generation date
- keeper/reject
- structural deviations
- extraction performed?
- extracted path/hash
- MIDI extracted?
- artist canonical label
- artist confidence/notes
- canonical starter-mix role

---

## 12. Corrective Implementation Sequence

This is now a correction pass against the implemented kickoff.

1. Pull latest `music_creation` and `content-tools` branches.
2. Preserve the existing multi-GM preview as a clearly labeled **debug-only** artifact; do not use it as Suno input.
3. Change the composition contract from 120 bars / 4:48 to **100 bars / exactly 4:00 at 100 BPM, 4/4**.
4. Reallocate the nine movements within 100 bars while preserving all required coverage and musical coherence.
5. Regenerate canonical MIDI, event manifest, movement map, composition version, and hashes.
6. Update/add automated tests that assert the symbolic piece is exactly 240.000 seconds and 100 bars.
7. Ensure the MIDI serialization fix remains intact and no timing drift reappears.
8. Generate `canonical_reference_piece_piano_input.wav` using one neutral piano timbre.
9. Generate `canonical_reference_piece_synth_input.wav` using one deliberately plain synth timbre from the existing local ecosystem.
10. Ensure each canonical conditioning WAV is exactly 240.000 seconds with no post-four-minute release tail.
11. Validate non-silence, clipping, movement coverage, source hash, tempo/meter, and timing against the corrected movement map.
12. Re-ingest the corrected artifacts into Content Tools.
13. Rebuild all corpus metadata and prompt-book outputs from the corrected movement map.
14. Re-run the prompt checker: all 180 prompts must remain 900–1000 characters and `all_ok: true`.
15. Add stale-duration tests so `4:48`, `288 seconds`, and the superseded 120-bar contract cannot leak into current prompt/corpus outputs.
16. Stop before the 90-target Suno rendering campaign and hand both neutral files to the artist for listening/selection.

---

## 13. Guardrails

- One composition, not per-instrument etudes.
- **Exactly four minutes.** Do not exceed 4:00.
- Do not merely truncate a longer symbolic composition.
- Do not use the multi-GM debug render as Suno conditioning audio.
- Do not inject Choir Aahs, bass patches, guitar patches, drum kits, or other semantic instrumentation into the neutral conditioning input simply because a track has that role name.
- Do not create a new repo.
- Do not replace the Suno ontology with AudioSet labels.
- Do not treat Suno MIDI or Suno target names as canonical artistic truth.
- Do not write stale prompt-book timing descriptions.
- Do not deliver prompts outside 900–1000 characters.
- Do not duplicate existing analysis/recommender infrastructure.

---

## 14. Acceptance Criteria for the Correction

The correction is complete only when the agent can report:

1. corrected composition contract = **100 bars, 100 BPM, 4/4, exactly 240.000 seconds**
2. all nine movements retained/rebalanced with required coverage still passing
3. regenerated MIDI + manifest + movement map + hashes
4. exact-duration automated validation passing
5. `canonical_reference_piece_debug.wav` clearly marked nonconditioning/debug-only
6. `canonical_reference_piece_piano_input.wav` created and exactly 240.000 seconds
7. `canonical_reference_piece_synth_input.wav` created and exactly 240.000 seconds
8. neutral renders contain no role-specific semantic GM instrumentation contamination
9. Content Tools corpus re-ingested against corrected hashes
10. prompt book rebuilt with correct 4:00 movement descriptions
11. all 180 MAIN/EXCLUDE prompts still validate at 900–1000 characters
12. tests passing in both repos
13. commits pushed
14. exact local commands/paths for the artist to listen to both conditioning candidates
15. no Suno target campaign launched before artist approval

---

## 15. Handoff Principle

The human should only pay the unavoidable **Suno interaction tax** after the local score and neutral input have passed artist listening review.

Everything before and after that interaction — symbolic score generation, duration enforcement, neutral rendering, validation, prompt construction, exact character checking, corpus bookkeeping, ingestion, feature extraction, comparison, reporting, and provenance — should remain automated and reproducible locally wherever practical.
