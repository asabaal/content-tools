# Final Content Authority Model

**Definition**: Authoritative means what ships into the final rendered video.

---

## Level 1: Candidate Transcript Authority

**Purpose**: Establish the best available text for the raw material, before final inclusion decisions.

### Tool Flow
- **Tool 01 (Transcribe)**: Produces draft text with timing from source media.
- **Tool 02 (Review)**: Edits the text for accuracy, corrects transcription errors.

### Lock Point
End of Tool 02 locks candidate transcript text.

### What is Authoritative
- Word text content (what the speaker actually said)
- Word segmentation structure
- Word timing within source media

### Meaning
These are the words we believe the speaker said, and these are the words downstream tools reference. But this is NOT yet the final transcript for the finished video.

### Artifact
- `data/transcript_combined.json` - Reviewed transcript with corrected segments and word text

---

## Level 2: Shipped Content Authority

**Purpose**: Define what actually ships, including removal of words.

### Tool Flow
- **Tool 03 (Take Selection)**: Chooses which segments or takes are allowed into the piece. Produces the selected candidate set via `selected_segment` per clip.
- **Tool 04 (Assemble)**: Defines the final playback timeline by:
  - Ordering clips via `timeline_position`
  - Trimming clip boundaries via `trim_start` / `trim_end`
  - Deleting regions via `deleted_regions` (can remove silence AND spoken regions)

### Lock Point
End of Tool 04 locks:
- Final timeline ordering
- Final duration
- Shipped transcript

### What is Authoritative
- The final ordered set of playable segments
- The final duration
- The shipped transcript (derived from playable segments)
- Audio/video continuity

### How Shipped Transcript is Computed
The shipped transcript = candidate transcript filtered by:
1. Selection filtering (which segments/takes are included)
2. Playable segment overlap (which words fall within trim range minus deleted regions)

### Artifact
- `data/project.json` with:
  - `clips[*].selected_segment` - selection authority
  - `clips[*].trim_start`, `clips[*].trim_end` - timeline boundaries
  - `clips[*].deleted_regions` - removed regions within timeline
  - `clips[*].timeline_position` - ordering
  - `clips[*].in_timeline`, `clips[*].enabled` - inclusion flags

---

## Level 3: Overlay Style Authority

**Purpose**: Presentation authority only - how shipped words are displayed.

### Tool Flow
- **Tool 05A (Caption Style)**: Sets caption grouping, breaks, emphasis, and colors for the shipped transcript.
- **Tool 05B (Render)**: Burns in or muxes captions according to style spec. Does NOT change shipped content.

### Lock Point
End of Tool 05A locks overlay spec.

### What is Authoritative
- Visual styling (font, size, position, background)
- Word grouping (which words appear together)
- Per-word styling (emphasis, colors)

### Artifact
- `data/project.json` with:
  - `caption_style` - visual styling configuration
  - `word_colors` - per-word color assignments
  - `caption_breaks` - word grouping (optional)

---

## Lock Point Artifacts Summary

| After Tool | Artifact | Location |
|------------|----------|----------|
| Tool 02 | Reviewed transcript | `data/transcript_combined.json` |
| Tool 03 | Selection (which segments/takes) | `data/project.json` → `clips[*].selected_segment` |
| Tool 04 | Assembly (playable segments, deletions, duration) | `data/project.json` → `clips[*].trim_*`, `clips[*].deleted_regions`, `clips[*].timeline_position` |
| Tool 05A | Caption style overlay | `data/project.json` → `caption_style`, `word_colors` |

---

## Invariants

These invariants prevent bugs like duplication, missing content, and timeline corruption.

### Invariant 1: Trim Bounds Must Not Exceed Selected Bounds
At Level 2, a clip must not expand its playable range beyond what Level 1 and 2 selection allow.

**Concretely**: If a clip references a `selected_segment`, its `trim_start` and `trim_end` must be within those selected bounds.

**Why**: If trims exceed selection bounds, you can accidentally include extra words and duplicate content.

### Invariant 2: Playable Segments Must Not Overlap
Within the final timeline, playable segments must not overlap unless explicitly intended (e.g., layered audio).

**Why**: Overlapping segments cause duplicated words in the shipped transcript and audio/video glitches.

### Invariant 3: Output Duration Must Match Sum of Playable Segments
The final rendered video duration must equal the sum of all playable segments (within tolerance).

**Why**: Duration mismatch indicates missing content or extra content that shouldn't exist.

---

## Single Sentence Summary

Tool 02 locks the candidate transcript. Tools 03 and 04 lock what actually ships, including which words survive. Tool 05 locks how those shipped words are displayed.
