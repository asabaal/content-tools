# Suno Target Reference Corpus — Kickoff Specification

**Status:** Ready for implementation  
**Repository:** `asabaal/content-tools`  
**Branch:** `develop`  
**Related systems:** `tools/06-song-ingest`, existing Suno Stem Target Recommender, `asabaal/music_creation` reference-composition tooling  
**Primary calibration artifact:** one canonical reference composition rendered repeatedly across Suno Advanced Split target instruments

## 1. Purpose

Build an empirical **Suno Target Reference Corpus** that lets Asabaal Ventures answer a concrete question:

> Given an unknown song or stem, which of Suno's documented Advanced Split extraction targets are actually present or worth extracting?

The corpus must be grounded in controlled reference audio, not only generic classifier labels. We will create **one canonical symbolic composition** containing a deliberately broad set of musical test conditions, render that same piece repeatedly in Suno with different target instruments/timbres, and use those renders as reference exemplars for target assignment.

The system must preserve the distinction between:

1. **Composition ground truth** — the notes, rhythms, chords, keys, structure, and intended role we generated ourselves.
2. **Rendered reference audio** — Suno's realization of that known composition as a requested target instrument/timbre.
3. **Suno extraction behavior** — where useful, Suno's own extracted target/stem from the reference render.
4. **Local analysis output** — our instrument-target classification, embeddings/features, audio-to-MIDI, and other derived evidence.
5. **Suno MIDI/reference outputs** — useful comparison evidence, never canonical truth.

The immediate validation target is `hippie activist.`.

---

## 2. Core Experimental Principle

There is **one canonical reference piece**.

Do not create a separate etude per instrument.

The same underlying composition is rendered again and again across target instruments. This holds pitch, harmony, rhythm, form, and section timing as constant as possible while changing the intended instrument/timbre.

This turns the reference corpus into a controlled comparison surface.

Conceptually:

```text
canonical_reference_piece.mid
        |
        +--> render as Organ
        +--> render as Piano
        +--> render as Electric guitar
        +--> render as Strings
        +--> render as Brass
        +--> render as Synth pad
        +--> render as Synth keys
        +--> render as Woodwinds
        +--> ...
```

For each target render, preserve the exact prompt, model/version, date, render identifier, source symbolic artifact version, and any extraction artifacts.

---

## 3. Repo Responsibilities

### 3.1 `asabaal/music_creation`

Use the **music creation repo** to construct the canonical composition and its symbolic ground truth.

This repo should own the generator/source-of-truth artifacts for the piece, including at minimum:

- specification for the composition
- generator code or reproducible score-construction code
- canonical MIDI
- MusicXML if practical
- section/movement map
- exact note/chord/key metadata
- test-event manifest
- validation tools for the symbolic score

Do not hand-author an opaque MIDI file without reproducible source.

### 3.2 `asabaal/content-tools`

Content Tools owns the ingestion, analysis, corpus organization, comparison, target assignment, prompt-book generation, validation, and downstream benchmarking.

The implementation here should integrate with the existing `tools/06-song-ingest` pipeline and the existing Suno-target recommender rather than duplicate them.

---

## 4. Canonical Reference Piece

### 4.1 One complete composition

Create a single coherent musical piece, likely around **4–6 minutes**, long enough to exercise the required musical conditions without becoming random or purely mechanical.

It should still sound like a real composition. The goal is a musically valid reference work that doubles as a calibration suite.

### 4.2 Required musical coverage

The piece must deliberately include all of the following within the same composition:

#### Tonal/key coverage

- all 12 major keys
- all 12 minor keys
- controlled modulation between keys
- clear tonal centers long enough for analysis
- chromatic material where useful

#### Scale and melodic coverage

- major scales
- natural/harmonic/melodic minor material where musically appropriate
- chromatic runs
- arpeggios
- isolated-note passages
- stepwise melody
- intervallic melody
- repeated notes
- register sweeps

#### Interval coverage

Include representative intervals across the octave, both ascending and descending where practical:

- seconds
- thirds
- fourths
- fifths
- sixths
- sevenths
- octaves

#### Harmonic coverage

- major/minor triads
- inversions
- suspended chords
- dominant sevenths
- major/minor sevenths
- selected extended chords
- dyads
- dense chord voicings
- sparse voicings

#### Common progression coverage

Include musically coherent examples of common progressions, including at least:

- I–IV–V–I
- ii–V–I
- I–V–vi–IV
- vi–IV–I–V
- representative minor cadences/progressions
- blues-derived movement where useful

#### Texture and performance-role coverage

- monophonic melody
- dyads
- polyphonic/counterpoint passage
- full chordal playing
- sparse accompaniment
- dense accompaniment
- sustained/legato playing
- staccato/articulated playing
- repeated-note attacks
- rhythmic/syncopated passage
- low-register material
- mid-register material
- high-register material
- at least two musically interesting solo passages
- one dense musical finale or climax

### 4.3 Ground-truth event manifest

Every important test event or section should be machine-readable.

Example conceptual schema:

```json
{
  "event_id": "minor_arpeggio_a_01",
  "section": "minor_arpeggios",
  "key": "A minor",
  "role": "melody",
  "pitch": "E4",
  "midi_note": 64,
  "onset_seconds": 92.5,
  "duration_seconds": 0.75,
  "velocity": 86,
  "expected_texture": "monophonic"
}
```

The exact schema may evolve, but the symbolic truth must be queryable and reproducible.

---

## 5. Target Families and One-Piece Principle

The piece is singular, but different sections can emphasize different target families.

Do **not** create unrelated songs for drums, vocals, FX, etc. Instead, the canonical piece should contain dedicated passages suitable for evaluating these roles while preserving one-piece identity.

Useful internal movement families include:

- pitched melodic/harmonic instruments
- bass behavior
- drums/percussion behavior
- vocal/choral behavior
- FX/transition behavior
- role-specific guitar/keyboard/synth behavior

If some Suno targets cannot sensibly realize every passage, preserve that limitation as part of the experiment rather than silently changing the underlying reference composition.

---

## 6. Suno Target Taxonomy

Use the **documented Suno Advanced Split target ontology already captured in the project**, including the standard and extended/beta target sets.

Do not substitute generic AudioSet/PANNs class names for the canonical target vocabulary.

The existing Suno Stem Target Recommender and its target ontology should remain authoritative for the target list unless updated evidence shows Suno changed the available options.

Generic detectors such as PANNs may contribute supporting evidence, but the output surface for this work must answer in Suno target terms.

---

## 7. Reference Corpus Structure

Design a durable corpus structure in Content Tools. A reasonable target shape is:

```text
reference-corpus/
  suno-targets/
    canonical-piece/
      composition-version.json
      movement-map.json
      prompt-book/
      targets/
        organ/
          intended-render.wav
          suno-extracted-target.wav        # when available
          metadata.json
          prompt.txt
          exclude.txt
          analysis/
        piano/
        electric-guitar/
        ...
```

Do not commit large WAVs if repo policy says they remain local/gitignored; preserve hashes, paths, provenance, and metadata in Git.

---

## 8. Feature and Similarity Strategy

The corpus should support comparison features that are useful even when pitch differs or transcription is imperfect.

At minimum plan for:

- learned audio embeddings
- spectral/timbral descriptors
- register-aware descriptors
- pitch-normalized or pitch-reduced comparisons where useful
- attack/articulation features
- sustain/decay behavior
- harmonic/percussive ratios
- temporal texture/density
- optional CLAP-style semantic similarity

The target-assignment stage should be able to compare an unknown audio segment/stem against target reference profiles rather than depend on only one generic classifier.

Preserve per-model/per-feature provenance.

---

## 9. MIDI Benchmarking

Because the canonical composition originates as known symbolic data, it becomes real ground truth for transcription evaluation.

For each rendered target:

```text
known ground-truth MIDI
        |
        v
Suno-rendered audio
   |              |
   v              v
local MIDI     Suno MIDI (if extracted)
```

Compare local and Suno transcription independently against the known source composition.

Metrics should eventually include:

- note precision/recall/F1
- onset tolerance matches
- offset/duration agreement
- pitch-class and exact-pitch agreement
- octave-error rate
- polyphony agreement
- register agreement
- timing drift
- chord/note-density behavior

Do not call agreement with Suno “accuracy” unless ground truth supports that claim.

---

## 10. Suno Rendering Prompt Book — Required Deliverable

After the canonical piece itself is complete and validated, generate a **copy-paste-ready Suno Rendering Prompt Book**.

This is a mandatory project deliverable.

### 10.1 Document contents

The prompt book must begin with a concise but complete explanation of:

- what the reference piece is
- why it exists
- total duration
- movement/section structure
- key/modulation journey
- harmonic tests
- melodic/interval tests
- polyphonic/chordal tests
- articulation/register tests
- solo passages
- percussion/vocal/FX passages where applicable
- what must remain invariant across target renders

### 10.2 Prompt pair for every target

For each target to be rendered, produce:

1. **🟣 MAIN / DEFAULT** prompt
2. **🛑 EXCLUDE / AVOID** prompt

These are separate Suno fields and each receives its own full character budget.

### 10.3 Hard prompt-length rules

For **every MAIN prompt** and **every EXCLUDE prompt**:

- hard maximum: **1000 characters**
- required working minimum: **900 characters**
- target range: **900–1000 characters inclusive**
- count actual characters, not tokens or words
- no prompt may be delivered without passing the checker
- character counts must be printed beside the final prompt

Anything below 900 or above 1000 **fails validation**.

Do not satisfy the minimum with meaningless padding. Use the available characters for specific, useful control instructions.

### 10.4 Prompt invariants

Every target prompt must preserve the canonical composition's identity and structure as strongly as Suno permits.

Prompts should communicate, as appropriate:

- same reference composition
- same movement order
- same harmonic/key journey
- same melodic contour/roles
- same solos and climactic logic
- same tempo/form unless a target physically requires adaptation
- requested target timbre/instrument clearly dominant
- appropriate articulation and register
- avoidance of substitutions by neighboring target classes
- avoidance of arrangement drift that undermines controlled comparison

### 10.5 Target-specific exclusions

EXCLUDE prompts must be genuinely target-specific where useful. They should suppress:

- nearby/confusable instruments
- unwanted ensemble substitutions
- inappropriate genre transformations
- excessive added instrumentation
- form changes
- tempo drift
- simplification of the calibration passages
- unwanted vocals for instrumental targets
- unwanted percussion or pads where they would contaminate the target
- synthetic/processed versions when an acoustic target is intended, and vice versa

### 10.6 Programmatic prompt validation

Implement a validator/checker in Content Tools that:

1. loads every MAIN and EXCLUDE prompt
2. counts exact characters
3. fails if `<900`
4. fails if `>1000`
5. reports character counts
6. can be run automatically in tests/CI/local validation

The prompt-generation workflow should iterate until every final prompt passes.

The final prompt book should show, for example:

```text
TARGET: Organ

🟣 MAIN / DEFAULT — 963 characters ✓
[copy-paste prompt]

🛑 EXCLUDE / AVOID — 947 characters ✓
[copy-paste prompt]
```

### 10.7 Render log fields

Each target entry should also provide a place to record:

- Suno model/version
- render ID
- generation date
- keeper/reject status
- deviations from canonical structure
- extraction performed?
- extracted target/stem path/hash
- MIDI extracted?
- notes

---

## 11. Integration with `hippie activist.`

Once the first reference-target renders exist, use them to improve target assignment for `projects/hippie-activist./`.

The system should eventually combine:

- existing Suno Stem Target Recommender evidence
- reference-corpus similarity
- generic detector evidence
- stem evidence
- known source/extraction labels
- local MIDI/transcription evidence where relevant

Do not treat any single model as unquestionable ground truth.

The specific output we want is a ranked answer to:

> Which documented Suno Advanced Split targets should we extract for `hippie activist.`?

---

## 12. Immediate Implementation Sequence

Begin now. Do not only return a plan.

### Phase A — recover and align existing systems

1. Inspect current `content-tools` `develop` state.
2. Locate/recover the existing Suno Stem Target Recommender implementation and ontology.
3. Inspect `tools/06-song-ingest` and determine the cleanest integration boundary.
4. Inspect `asabaal/music_creation` for the best place to own the canonical composition generator.
5. Document actual paths and dependencies before implementing new duplicate code.

### Phase B — define the canonical composition contract

6. Create the machine-readable composition/movement specification.
7. Define the required coverage checklist from Section 4.
8. Define the ground-truth event schema.
9. Define reproducibility requirements and validation tests.

### Phase C — start the symbolic reference composition

10. Implement the reproducible generator in `music_creation`.
11. Generate first MIDI/MusicXML outputs.
12. Validate keys, notes, chord events, movement boundaries, total duration, and required coverage.
13. Iterate until the composition contract passes automatically.

### Phase D — build corpus plumbing in Content Tools

14. Create the reference-corpus ingestion/metadata structure.
15. Add target ontology linkage and provenance.
16. Add hooks for reference audio, Suno extracted audio, embeddings/features, MIDI comparison, and render metadata.

### Phase E — build prompt-book tooling

17. Create prompt templates/generation logic only after the canonical piece structure is stable enough to describe accurately.
18. Implement exact character-count validation for MAIN and EXCLUDE fields.
19. Generate prompts for the target set.
20. Automatically iterate/fail validation until every final prompt is 900–1000 characters.
21. Produce a human-readable, copy-paste-ready prompt book with movement explanation and render log fields.

---

## 13. Non-Goals / Guardrails

- Do not create a new repository.
- Do not create multiple unrelated reference compositions.
- Do not replace Suno's documented target taxonomy with AudioSet labels.
- Do not treat Suno MIDI as ground truth.
- Do not treat Suno extraction labels as infallible.
- Do not commit huge audio artifacts against existing repo policy.
- Do not write final rendering prompts before the composition structure exists and can be described accurately.
- Do not deliver prompts outside 900–1000 characters.
- Do not pad prompts with meaningless filler to satisfy length.
- Do not duplicate existing music-analysis/recommender functionality if it can be reused or integrated.

---

## 14. Acceptance Criteria for This Kickoff

The kickoff is successful when the agent has made concrete progress and can report:

1. exact location/status of the existing Suno Stem Target Recommender
2. exact integration point in `tools/06-song-ingest`
3. exact location chosen in `music_creation` for canonical score generation
4. checked-in composition specification/movement contract
5. first reproducible generated symbolic artifact or demonstrable generator progress
6. automated validation coverage for the required musical conditions
7. Content Tools reference-corpus schema/plumbing begun
8. prompt-book generator/checker architecture begun or specified against the real movement contract
9. tests run and results
10. commits made in each touched repo
11. blockers requiring human action, especially any Suno rendering steps that must be performed manually

The agent should continue through executable work autonomously and stop only where a genuinely human/Suno UI interaction is required.

---

## 15. Handoff Principle

The human should only need to pay the **Suno interaction tax** where unavoidable: rendering/extraction inside Suno.

Everything before and after that interaction — symbolic score generation, validation, prompt construction, exact character checking, corpus bookkeeping, ingestion, feature extraction, comparison, and reporting — should be automated and reproducible locally wherever practical.
