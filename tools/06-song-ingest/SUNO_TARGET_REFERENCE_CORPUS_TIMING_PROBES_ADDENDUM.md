# Suno Target Reference Corpus — Timing-Probe Addendum

**Status:** Authoritative correction/addition to `SUNO_TARGET_REFERENCE_CORPUS_KICKOFF_SPEC.md`  
**Applies to:** Suno Target Reference Corpus calibration design  
**Repository:** `asabaal/content-tools` / `develop`

## 1. Revised calibration architecture

The corpus now uses **three canonical calibration pieces**, each optimized for a different measurement problem. This supersedes the earlier assumption that one universal piece must carry pitched, percussion, vocal, and FX behavior simultaneously.

The design is still controlled: there are three fixed modality references, not separate pieces per Suno target.

### A. Pitched / harmonic instrument calibration

- **Exact duration:** 4:00 / 240.000 seconds
- Purpose: pitch, harmony, timbre, register, articulation, melodic/chordal behavior, transcription, and pitched-instrument target comparison
- Conditioning candidates: neutral piano and neutral plain synth
- No semantic vocal, percussion, bass-patch, or FX-patch contamination merely because a symbolic track has that role
- This remains the main reference for pitched/harmonic Suno targets

### B. Percussion timing calibration

- **Exact duration:** 2:00 / 120.000 seconds
- Purpose: onset/timing alignment, rhythmic pattern recovery, grouping, meter, subdivision, density, accents, and percussion-role timing
- This is a separate canonical timing piece, not a shortened copy of the pitched piece
- It should use a deliberately neutral transient/click-like source representation rather than a realistic drum kit whenever practical, so the input encodes timing without asserting a target drum/percussion identity

### C. Vocal timing calibration

- **Exact duration:** 2:00 / 120.000 seconds
- Purpose: vocal onset/offset alignment, phrase timing, syllabic vs sustained behavior, melodic contour timing, grouping, density, meter, harmony-entry timing, and vocal-role timing
- Use a **neutral non-lexical `ah` / vox-like reference sound** as the conditioning voice. No lyrics are required for this timing probe.
- The vocal timbre is intentional here because this artifact measures vocal timing behavior rather than neutral instrument timbre.

The three pieces form one calibration suite:

```text
CALIBRATION SUITE

1. Pitched/Harmonic Reference ........ 4:00
2. Percussion Timing Reference ....... 2:00
3. Vocal Timing Reference ............ 2:00
```

Do not create 90 unrelated pieces. Suno targets map into one of these canonical probe families.

---

## 2. Percussion Timing Reference — required design

### 2.1 Timing contract

The percussion piece must be **exactly 120.000 seconds** before any noncanonical audition tail.

Prefer a fixed tempo unless a tempo-change test is intentionally justified. A practical default is **120 BPM**, which gives exactly 240 quarter-note beats in two minutes and makes meter/subdivision validation straightforward.

If another tempo is used, preserve the hard 120.000-second contract and document why.

### 2.2 Coverage goal

This is not an exhaustive timbre piece. It is a **timing-alignment stress test**.

Within two minutes include deliberate variation in:

- rhythmic patterns
- onset spacing
- durations where the source supports them
- rests / silence windows
- accents / velocity
- sparse vs dense sections
- repeated patterns / ostinati
- isolated hits
- bursts / fills
- syncopation
- offbeats
- quarter/eighth/sixteenth subdivisions
- dotted figures
- triplets / tuplets
- ties or events spanning metric boundaries where meaningful
- simultaneous hits
- staggered/layered entries
- call-and-response groupings
- crescendo/decrescendo or velocity contour
- density contour
- low/mid/high neutral lanes or equivalent nonsemantic structural lanes if needed for multi-lane timing

### 2.3 Meter and grouping coverage

Include several clearly delimited time-signature/grouping regions. At minimum exercise representative material in:

- 4/4
- 3/4
- 6/8
- 5/4 or 5/8 with asymmetric grouping
- 7/8 with asymmetric grouping

Useful internal groupings include:

- 2+2
- 3+3
- 3+3+2
- 2+3
- 3+2
- 2+2+3

The exact sequence is implementation-owned, but it must fit coherently inside exactly two minutes and be machine-readable.

### 2.4 Neutral percussion-conditioning sound

Do not use a full semantic GM drum kit as the canonical Suno input if a more neutral option exists.

Inspect the existing music tool ecosystem and prefer a simple transient/click/impulse-like sound that makes onsets unambiguous without already sounding like kick, snare, hi-hat, conga, etc.

If multiple timing lanes are needed, use the least-semantic differentiation practical and document it. The objective is **timing structure first, target timbre later**.

A separate debug render may use a conventional kit for human comprehension, but mark it **NOT FOR SUNO INPUT**.

### 2.5 Ground-truth manifest

Every timing event should preserve enough data for exact alignment scoring, including where applicable:

- event ID
- absolute onset time
- duration / gate
- MIDI tick / beat location
- bar and beat
- meter
- subdivision type
- grouping pattern
- lane / role
- velocity / accent
- density class
- section ID
- pattern ID
- simultaneous-event group

The local/Suno outputs can then be scored against real onset ground truth rather than only compared to each other.

---

## 3. Vocal Timing Reference — required design

### 3.1 Timing contract

The vocal piece must be **exactly 120.000 seconds** before any noncanonical audition tail.

A fixed tempo such as **120 BPM** is preferred unless another choice provides a materially better alignment probe.

### 3.2 Conditioning voice

Use a **neutral non-lexical vocal `ah` / vox-like sound** as the reference frame.

This should be a simple, intelligible vocal sound with minimal stylistic identity. Do not use lyrics for the canonical timing probe. The purpose is to measure timing and contour, not language generation.

Use the existing local ecosystem/sample/soundfont capability where possible. Record the exact patch/sample/source and hash/provenance.

### 3.3 Required vocal timing coverage

Within two minutes include deliberately different:

- note lengths
- onset spacings
- rests / breath-sized gaps
- repeated-note pulses
- staccato vocal attacks
- long sustained vowels
- legato connected phrases
- syllabic-style one-note-per-attack patterns using repeated `ah`
- melismatic-style multiple-note phrases under a sustained/non-lexical vocal sound
- syncopated entries
- offbeat entries
- triplets / tuplets
- dotted rhythms
- ties across barlines
- sparse vs dense phrases
- accelerating/decelerating **density** while tempo remains controlled
- ascending contours
- descending contours
- arch contours
- repeated-pitch contours
- interval leaps
- low/mid/high vocal-register regions within a practical generic range
- single-voice passages
- unison stacked entries
- two-/three-/four-part simultaneous harmony entries where practical
- staggered backing-vocal/choir-style entries
- call-and-response timing
- short pickup/anacrusis behavior

### 3.4 Meter and grouping coverage

As with percussion, include multiple clearly identified metric regions, at minimum representative examples in:

- 4/4
- 3/4
- 6/8
- one asymmetric 5-based meter/grouping
- one asymmetric 7-based meter/grouping

The goal is not musical novelty for its own sake; the goal is to create known timing structures that expose onset, offset, grouping, and phrase-alignment behavior.

### 3.5 Ground-truth manifest

Preserve at minimum:

- event ID
- voice ID
- absolute onset
- duration
- pitch
- contour class
- register class
- bar / beat
- meter
- subdivision
- phrase ID
- grouping pattern
- articulation class
- density class
- simultaneous-harmony group
- section ID

If the neutral `ah` source is sample-based, preserve sample/source identity and any pitch/time-stretch transformation provenance.

---

## 4. Target-family routing

Add an explicit ontology-to-calibration-family mapping in Content Tools.

### Pitched/harmonic reference

Default home for pitched instrumental targets: keys, guitars, strings, brass, woodwinds, synths, basses, organ, piano, etc.

### Percussion timing reference

Default home for drum/percussion/transient targets: drums, kick, snare, hi-hat, cymbals, clap, tambourine, shaker, bongos, congas, djembe, cowbell, and similar targets.

### Vocal timing reference

Default home for lead vocal, backing vocal, choir, vocoder, and related voice targets.

Some ontology targets may reasonably participate in more than one reference family (for example pitched percussion or vocoder). Preserve explicit multi-family mappings when useful rather than forcing a false single category.

---

## 5. Prompt-book implications

The existing 900–1000-character rule remains mandatory for every MAIN and EXCLUDE prompt.

However, prompt generation must now be **calibration-family aware**:

- pitched targets describe the exact 4:00 pitched/harmonic reference
- percussion targets describe the exact 2:00 percussion timing reference
- vocal targets describe the exact 2:00 vocal timing reference and neutral `ah`/vox conditioning source

Do not give percussion/vocal targets stale descriptions of the nine-movement pitched piece.

Each prompt entry must identify its canonical conditioning artifact and hash.

---

## 6. Required local artifacts

Recommended durable layout:

```text
music_creation/reference_composition/
  pitched_harmonic/
    ... exactly-4m symbolic truth + piano/synth conditioning ...
  percussion_timing/
    ... exactly-2m symbolic truth + neutral transient conditioning ...
  vocal_timing/
    ... exactly-2m symbolic truth + neutral ah/vox conditioning ...
```

The agent may preserve compatibility with the existing `reference_composition/` layout rather than move files destructively; if so, introduce clear subpackages/IDs and document migration.

Content Tools should ingest all three under one reference-corpus suite with distinct calibration IDs.

---

## 7. Corrective implementation sequence

1. Keep the current correction requiring the pitched/harmonic piece to become exactly 4:00.
2. Remove percussion/vocal-specific burden from that piece where doing so improves clarity; do not retain special-role passages merely because the old universal-piece design had them.
3. Create a deterministic **Percussion Timing Reference**, exactly 2:00.
4. Create a deterministic **Vocal Timing Reference**, exactly 2:00.
5. Build machine-readable manifests and movement/section maps for both.
6. Add validators for exact duration, meters, subdivisions, groupings, density classes, and required timing patterns.
7. Generate a neutral transient/click-like conditioning WAV for the percussion reference.
8. Generate the neutral non-lexical `ah`/vox conditioning WAV for the vocal reference.
9. Generate human-audition debug versions separately if useful, clearly marked nonconditioning.
10. Add ontology-to-calibration-family routing.
11. Rebuild prompt generation so target prompts describe the correct reference family.
12. Validate every MAIN and EXCLUDE prompt at 900–1000 characters.
13. Re-ingest corpus metadata/provenance/hashes.
14. Run all tests.
15. Stop before Suno generation and give the artist exact playback commands/paths for all conditioning candidates.

---

## 8. Acceptance criteria

The timing-probe addition is complete when:

- pitched/harmonic canonical piece = exactly 4:00
- percussion timing canonical piece = exactly 2:00
- vocal timing canonical piece = exactly 2:00
- all are deterministic and reproducible
- percussion timing coverage includes multiple meters, asymmetric groupings, subdivisions, syncopation, sparse/dense patterns, accents, simultaneous/staggered events, and timing contours
- vocal timing coverage includes multiple meters, phrase/grouping variation, note-length variation, sustained and articulated `ah` behavior, melodic contours, single/stacked/staggered voices, sparse/dense phrases, and timing complexity
- both timing pieces have event-level ground truth suitable for onset/offset alignment scoring
- percussion input does not pre-impose a realistic drum-kit identity
- vocal input uses a documented non-lexical `ah`/vox reference sound
- target-family routing is machine-readable
- prompt book describes the correct 4m/2m/2m reference per target family
- all prompts pass 900–1000 exact-character validation
- artist receives playable local files and commands
- no Suno corpus campaign has started before artist listening approval
