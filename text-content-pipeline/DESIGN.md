# Text Content Pipeline System

## Purpose

A deterministic pipeline that converts human-defined monthly themes into daily publishable images without requiring daily judgment, creativity, or renegotiation of meaning.

This is NOT:
- A creativity engine
- An engagement optimizer
- A social media growth tool
- Content ideation assistant

This IS:
- Coherence distribution system
- Execution automation system
- Typesetting engine for thoughts

---

## Core Design Principles

### Principle 1: Meaning is human-defined, never inferred
The system never decides:
- What the theme is
- What matters
- What is true
- What should be said

All meaning enters the system explicitly.

### Principle 2: Time is deterministic
- Weeks are Monday–Sunday
- A week belongs to the month where Monday falls
- No fuzzy boundaries
- No sliding windows

### Principle 3: Judgment frequency decreases as time scale decreases

| Time Scale | Judgment Location |
|------------|-------------------|
| Monthly    | Human + AI conversation |
| Weekly     | Human (light touch) |
| Daily      | System only |

The system exists to push judgment upward so daily execution is mechanical.

### Principle 4: System expands meaning downward, not upward
- Monthly theme → weekly sub-themes
- Weekly sub-themes → daily content slots
- Slots → formatted artifacts

No synthesis flows upward. Ever.

---

## Pipeline Architecture

```
payload
  ↓
calendar (resolve all weeks for month)
  ↓
if weekly_subthemes missing:
    ✨ AI WEEKLY SUBTHEME DERIVATION ✨
  ↓
✨ AI MONTHLY SLOT PLANNING ✨
  ↓
slots (validation + application)
  ↓
✨ AI MONTHLY TEXT GENERATION ✨
  ↓
renderer
  ↓
artifacts (full month)
```

---

## Module Architecture

### payload
**Responsibility**: Define Month Payload schema, validate required fields

**Owns**:
- Month Payload definition
- Validation errors
- Schema versioning

**Must NOT**: Know calendar logic, rendering, or CLI concerns

### calendar
**Responsibility**: Resolve dates and weeks deterministically

**Owns**:
- Monday-determines-month rule
- Week start and end calculation
- 4 vs 5 week resolution
- Video week identification

**Input**: Validated Month Payload  
**Output**: Resolved Month Calendar

**Must NOT**: Assign content slots, interpret meaning, or render anything

### slots
**Responsibility**: Assign daily slot functions to dates, validate constraints

**Owns**:
- Daily slot enum
- Weekly rotation logic
- Sunday human slot reservation
- Video week exclusions

**Input**: Resolved Month Calendar  
**Output**: Daily Slot Schedule

**Must NOT**: Generate text, render visuals, or modify calendar structure

### ai_generator
**Responsibility**: Generate text for slots and assign slot types using local AI

**Owns**:
- Prompt templates
- Model invocation (Ollama, gpt-oss:20b default)
- Output validation
- Failure handling

**Three AI Touchpoints**:
1. **Weekly Subtheme Derivation** (conditional, only if missing from payload)
2. **Monthly Slot Planning** (always runs)
3. **Monthly Text Generation** (always runs)

**Must NOT**: Know calendar logic, scheduling, or renderer details

### renderer
**Responsibility**: Turn finalized text into images

**Owns**:
- HTML template
- CSS presets (colorful backgrounds only - no white/neutral)
- Headless browser wrapper
- Image output

**Input**: Text content, style preset, dimensions  
**Output**: Image artifacts (PNG)

**Must NOT**: Know about weeks/slots or decide content

### pipeline
**Responsibility**: Orchestrate stages in order

**Owns**:
- Stage sequencing
- Dependency wiring
- Failure propagation
- Artifact handoff

**Must NOT**: Contain business logic, reimplement validation, or special-case behavior

### cli
**Responsibility**: Expose pipeline via commands

**Owns**:
- Command definitions
- Argument parsing
- Help text
- Exit codes
- Human-readable summaries

**Must NOT**: Implement pipeline logic or contain rendering code

### config
**Responsibility**: Centralize constants and defaults

**Owns**:
- Default image dimensions
- Default style preset (colorful)
- Paths
- Feature flags

**Must NOT**: Become a logic dumping ground

### errors
**Responsibility**: Typed, meaningful failures

**Owns**:
- Validation errors
- Calendar resolution errors
- Renderer failures
- CLI user errors

---

## Data Schemas

### Month Payload Schema

**Required Fields**:
```json
{
  "year": 2026,
  "month": 2,
  "monthly_theme": "Evolving in Christ",
  "weekly_subthemes": ["Orientation", "Resistance", "Formation", "Integration"], // Optional
  "week_rule": "monday_determines_month",
  "video_week": "last_week"
}
```

**Optional Fields**:
```json
{
  "style_preset": "default",
  "notes": "Any human notes"
}
```

**Validation Rules**:
- `weekly_subthemes` must be length 4 or 5 (or omitted for AI derivation)
- If 5 subthemes provided, month must resolve to 5 Mondays
- No empty strings
- Order is authoritative and preserved

### Daily Slot Functions (Fixed Enum)

```
DECLARATIVE_STATEMENT
EXCERPT
PROCESS_NOTE
UNANSWERED_QUESTION
REFRAMING
QUIET_OBSERVATION
HUMAN_INTENTIONAL  // Sunday only
```

### Resolved Calendar Structure

```json
{
  "weeks": [
    {
      "week_number": 1,
      "monday_date": "2026-02-02",
      "sunday_date": "2026-02-08",
      "subtheme": "Orientation",
      "is_video_week": false
    }
  ]
}
```

### Daily Slot Schedule

```json
{
  "slots": [
    {
      "date": "2026-02-02",
      "slot_type": "DECLARATIVE_STATEMENT",
      "subtheme": "Orientation",
      "is_automated": true
    },
    {
      "date": "2026-02-08",
      "slot_type": "HUMAN_INTENTIONAL",
      "subtheme": "Orientation",
      "is_automated": false
    }
  ]
}
```

---

## AI Integration

### Default Configuration

- **Provider**: Ollama
- **Model**: gpt-oss:20b
- **Invocation**: Local only
- **Temperature/Settings**: Sane fixed defaults

### AI Touchpoint 1: Weekly Subtheme Derivation (Conditional)

**When it runs**: Only if `weekly_subthemes` NOT provided in payload

**Input**:
- Monthly theme
- Number of weeks in month
- Optional guidance (e.g., "culminating structure", "progressive arc")

**Constraints**:
- Must output 4 or 5 subthemes
- Must be ordered
- Must be short phrases
- Must not introduce new domains

**Output**: Ordered list of weekly subthemes

### AI Touchpoint 2: Monthly Slot Planning

**Purpose**: Decide which slot enum appears on which day

**Input**:
- Monthly theme
- Weekly subthemes (human or AI-derived)
- Calendar structure (weeks and weekdays)
- Slot enum list

**Constraints**:
- Sunday excluded
- Video days excluded
- Each enum may appear 0–2 times per week (not more)
- No enums outside defined set

**Output**: Structured mapping: `date → slot enum` for full month

### AI Touchpoint 3: Monthly Text Generation

**Purpose**: Generate draft text for every automated slot

**Input** (per slot, batched):
- Monthly theme
- Weekly subtheme
- Slot enum
- Date (optional context)
- Length and tone constraints

**Output**: Plain text per slot

**Constraints**:
- Plain text only
- No markdown
- No emojis
- No hashtags
- No formatting
- No explanations

---

## Visual Layer

### Strategy

Text Card System - text-forward images with colorful backgrounds.

### Visual Stack

**Layer 1: Canvas (fixed)**
- Aspect ratio: 1:1 (square) or 4:5 (portrait)
- Background: **Colorful only** (no white/neutral/grayscale)
- Padding: Generous, consistent

**Layer 2: Text Block (variable but constrained)**
- Single column
- Left-aligned or center-aligned
- Max width constraint
- Auto line wrapping
- One font family
- Two weights max (regular + bold)
- Auto-sizing within bounds

**Layer 3: Minimal Metadata (optional)**
- Month theme (small text)
- Week sub-theme
- Date
- Subtle divider

**Style Presets**
Monthly selection controlling:
- Background color (colorful only)
- Text color
- Font size scale
- Padding
- Alignment

### Renderer Choice

HTML + CSS → headless browser → PNG images

**Why**:
- Best text layout with least custom logic
- Browser handles wrapping, fonts, spacing
- Visual tweaks are CSS-only
- Low maintenance over time

**Implementation**:
- Generate HTML file with placeholders filled
- CSS applies layout and fonts
- Headless browser screenshots the page
- Image saved as PNG

---

## CLI Commands

### init-month
Initialize a new month payload file.
- Creates payload scaffold (JSON or YAML)
- Includes required fields
- Leaves weekly sub-themes empty or placeholder
- Fails if file exists unless forced

### validate
Validate a month payload without running pipeline.
- Schema validation
- Week count validation
- Monday rule validation
- Clear error messages
- No side effects

### resolve-calendar
Run Stage 1 only.
- Reads payload
- Outputs resolved calendar (JSON)
- No rendering
- No slots yet

### generate-slots
Run Stage 2 only.
- Requires resolved calendar
- Outputs daily slot schedule
- Sundays reserved
- Video week respected

### render-images
Run Stage 3 only.
- Takes finalized slot text input
- Applies style preset (colorful)
- Writes images to disk
- No publishing

### assign-slots
Run AI slot planning for inspection.
- Runs AI slot assignment for month
- Outputs slot mapping
- Can be inspected before proceeding

### generate-text
Run AI for scheduled slots.
- Runs AI generation for month
- Writes draft text files
- Skips locked slots

### preview-prompt
Print AI prompt for inspection.
- Prints AI prompt for given slot
- Does not call model

### inspect-slot-plan
Inspect AI-generated slot plan.

### inspect-text-drafts
Inspect AI-generated text drafts.

### run-all
Run full pipeline end-to-end.
- validate → resolve → slot → render
- Stops on first failure
- Outputs summary

---

## End-to-End Demo Requirement

### Test Concept
"The only three things that matter are faith, hope, and love, but the greatest of these is love."

### Mode A: Explicit Weekly Subthemes

**Input**:
```json
{
  "year": 2026,
  "month": 3,
  "monthly_theme": "The only three things that matter are faith, hope, and love, but the greatest of these is love.",
  "weekly_subthemes": ["Faith", "Hope", "Love", "The Primacy of Love"],
  "week_rule": "monday_determines_month",
  "video_week": "last_week"
}
```

**Expected**:
- Weekly subtheme AI derivation is SKIPPED
- Slot planning uses provided subthemes
- Text generation runs normally
- Images produced with colorful backgrounds

### Mode B: No Weekly Subthemes

**Input**:
```json
{
  "year": 2026,
  "month": 3,
  "monthly_theme": "The only three things that matter are faith, hope, and love, but the greatest of these is love.",
  "week_rule": "monday_determines_month",
  "video_week": "last_week"
}
```

**Expected**:
- AI weekly subtheme derivation runs
- Produces 4 or 5 ordered subthemes
- Those derived subthemes used downstream
- Slot planning and text generation proceed identically
- Images produced with colorful backgrounds

### Critical Invariant
After weekly subthemes exist (whether human or AI-derived):
- All downstream stages must behave identically
- No branching logic beyond that point

---

## Constraints and Rules

### Week Rule
- Weeks run Monday through Sunday
- A week belongs to the month where Monday falls
- If month contains 4 Mondays, it has 4 weeks
- If month contains 5 Mondays, it has 5 weeks

### Slot Constraints
- Each slot enum may be used 0, 1, or 2 times per week
- No enum may be used more than 2 times
- Total automated days must be filled
- Sunday is HUMAN_INTENTIONAL (non-AI)
- Video days excluded from automated text

### Visual Constraints
- **No white/neutral backgrounds** - colorful only
- Text as primary object
- No photos of you
- No symbolic imagery
- No icons implying meaning
- No AI-generated art
- No mood-based color decisions per post

### AI Constraints
- Uses local models only (Ollama, gpt-oss:20b default)
- No cloud fallback
- No silent substitution
- Fails loudly if model unavailable
- AI assists execution, not discernment
- AI fills slots, does not create structure
- All AI output is editable, replaceable, ignorable

---

## Testing Strategy

### Unit Tests Cover
- Payload validation
- Week resolution logic
- Daily slot assignment
- Renderer invocation boundaries
- File output existence
- Prompt construction
- Enum handling
- Validation logic
- Error paths

### AI Integration Tests (Real Model Calls)
- Weekly subtheme derivation (only when missing)
- Monthly slot planning
- Monthly text generation
- All using gpt-oss:20b via Ollama

### System Tests
- End-to-end run: payload → weeks → slots → images
- Correct number of outputs
- No Sunday artifacts
- No video-day artifacts
- All files created

### Explicitly NOT Tested
- Pixel perfection
- Typography aesthetics
- Browser rendering quirks
- Visual alignment
- Semantic quality ("is this good theology")
- Stylistic judgments

---

## Non-Goals

- Visual regression testing
- Publishing automation
- Social platform APIs
- Font experimentation
- Responsive breakpoints
- Mobile-specific layouts
- Animations
- Interactivity
- Optimizing engagement
- Suggesting content ideas
- Inferring meaning
- Varying cadence based on metrics

---

## Project Structure

```
text-content-pipeline/
├── src/
│   ├── __init__.py
│   ├── payload/
│   │   ├── __init__.py
│   │   ├── schema.py
│   │   └── validation.py
│   ├── calendar/
│   │   ├── __init__.py
│   │   └── resolver.py
│   ├── slots/
│   │   ├── __init__.py
│   │   ├── enum.py
│   │   └── scheduler.py
│   ├── ai_generator/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   └── prompts.py
│   ├── renderer/
│   │   ├── __init__.py
│   │   ├── html_renderer.py
│   │   └── templates/
│   │       ├── template.html
│   │       └── styles/
│   │           ├── default.css
│   │           ├── warm.css
│   │           └── cool.css
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── orchestrator.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── commands.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── defaults.py
│   └── errors/
│       ├── __init__.py
│       └── exceptions.py
├── tests/
│   ├── test_payload.py
│   ├── test_calendar.py
│   ├── test_slots.py
│   ├── test_ai_generator.py
│   ├── test_renderer.py
│   ├── test_pipeline.py
│   └── test_cli.py
├── examples/
│   ├── demo_explicit.json
│   └── demo_derived.json
├── outputs/
│   ├── images/
│   └── plans/
├── DESIGN.md
├── README.md
├── pyproject.toml
└── requirements.txt
```

---

## Implementation Order

### Stage 1: Foundation
1. Project structure
2. Config module
3. Errors module
4. Payload schema and validation

### Stage 2: Calendar Resolution
5. Calendar module with Monday rule
6. Week resolution tests

### Stage 3: Slot System
7. Slot enum definitions
8. Slot scheduler
9. Slot assignment tests

### Stage 4: AI Generator
10. AI generator module
11. Prompt templates (3 touchpoints)
12. Ollama integration
13. AI integration tests (real model calls)

### Stage 5: Renderer
14. HTML templates (colorful backgrounds)
15. CSS presets (no white/neutral)
16. Headless browser integration
17. Renderer tests

### Stage 6: Pipeline Orchestration
18. Pipeline orchestrator
19. Stage wiring
20. End-to-end tests

### Stage 7: CLI
21. CLI commands
22. Argument parsing
23. Help text
24. CLI tests

### Stage 8: Demo
25. Demo examples (both modes)
26. Demo validation

---

## Success Criteria

The system is complete when:
1. User can define a month payload
2. CLI validates it
3. Calendar resolves correctly
4. Daily slots assigned respecting constraints
5. AI generates text using local model
6. At least one text post renders to colorful image
7. All logic covered by tests
8. Pipeline runs end-to-end from CLI
9. Demo works in both modes (explicit and derived weekly subthemes)

---

## Technical Decisions

### Language
Python 3.11+ for:
- Strong type hints
- Rich ecosystem for testing, CLI, AI
- HTML/CSS generation

### Configuration Format
JSON for:
- Strict, explicit structure
- Tool ecosystem support
- Easy programmatic manipulation

### CSS Presets
All presets use **colorful backgrounds** only:
- Deep blue, vibrant purple, rich teal, warm orange, etc.
- No white, off-white, gray, beige, or neutral tones
- High contrast text for readability

### Browser Rendering
Playwright or Selenium for headless rendering:
- Stable, well-maintained
- Cross-platform
- Excellent text rendering

---

## Planned: Background Music Integration (ACE-Step)

### Overview

Add AI-generated background music to animated video output using the ACE-Step v1-3.5B music generation model. One music track is generated per month, reused across all slots. Music is mixed with TTS narration audio and muxed into the final video.

### Why Subprocess (Not Direct Import)

ACE-Step runs in a dedicated Python 3.10 environment (`/mnt/storage/python_env/ace_step_env/`) with pinned ML dependencies (PyTorch 2.9.1+cu128, transformers 4.50.0, diffusers 0.36.0). TCP runs in Python 3.12. These environments cannot share an import space. TCP calls ACE-Step via `subprocess.run()`, reads JSON stdout, and picks up the generated WAV file.

### Audio Timing Logic

Music and video duration are derived entirely from TTS duration. No fixed defaults.

**For a slot with TTS duration `D` seconds:**
```
tts_delay        = 0.5 seconds (silence before speech starts)
tail             = min(3.0, D * 0.25)
slot_video_dur   = tts_delay + D + tail
```

**Examples:**
| TTS Duration | Delay | Tail | Video Duration |
|-------------|-------|------|----------------|
| 6s          | 0.5s  | 1.5s | 8.0s           |
| 12s         | 0.5s  | 3.0s | 15.5s          |
| 20s         | 0.5s  | 3.0s | 23.5s          |
| 40s         | 0.5s  | 3.0s | 43.5s          |

### Music Generation: Per-Month, Reused Per-Slot

One music track is generated per pipeline run. Its length is determined by the longest TTS in the batch:

```
music_duration = 0.5 + max(all_tts_durations) + min(3.0, max(all_tts_durations) * 0.25)
```

Each slot trims this track to its own `slot_video_dur`. This avoids generating 20+ separate music tracks while ensuring every video has a music bed.

### Pipeline Flow (Revised)

The existing pipeline has TTS generation embedded inside the rendering loop. Background music requires knowing all TTS durations before generating the track. The revised flow extracts TTS into a pre-pass:

```
Stage 1:    Calendar resolution                     (existing, unchanged)
Stage 2a:   Weekly subtheme derivation               (existing, unchanged)
Stage 2b:   Weekly subtitle generation               (existing, unchanged)
Stage 2c:   Monthly slot planning                    (existing, unchanged)
Stage 3:    Slot plan validation & application       (existing, unchanged)
Stage 4:    Daily text generation                    (existing, unchanged)
Stage 4.5:  TTS pre-pass                             (NEW - generate all TTS, record durations)
Stage 4.6:  Monthly background music generation      (NEW - one track at max duration)
Stage 5:    Rendering loop                           (MODIFIED - uses pre-generated TTS + music)
```

When `--bg-music` is not set, Stages 4.5 and 4.6 are skipped entirely. The rendering loop falls back to the current inline TTS behavior. No regression risk.

### Rendering Loop (Modified)

Per slot in the rendering loop:

1. **With bg_music + audio**: Trim monthly music to `slot_video_dur`, mix with TTS (TTS delayed 0.5s, music at 30% volume), pass mixed audio to `render_animated_video` with explicit `video_duration`
2. **With audio only** (no bg_music): Existing TTS-only behavior unchanged
3. **No audio**: Existing silent video behavior unchanged

### Data Flow Diagram

```
                    ┌─────────────────────┐
                    │  Stage 4: AI Text   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Stage 4.5: TTS      │  NEW
                    │ Pre-pass             │
                    │ (all slots, record   │
                    │  durations)          │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Stage 4.6: Music    │  NEW
                    │ Generate 1 track    │
                    │ (duration = f(max   │
                    │  tts_duration))     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
         ┌────▼─────┐   ┌─────▼────┐    ┌──────▼──────┐
         │  Slot 1   │   │  Slot 2   │   │  Slot N     │
         │  Trim     │   │  Trim     │   │  Trim       │
         │  music    │   │  music    │   │  music      │
         │  Mix TTS  │   │  Mix TTS  │   │  Mix TTS    │
         │  Render   │   │  Render   │   │  Render     │
         └──────────┘   └──────────┘    └─────────────┘
```

### New Files

#### `test-models/run_ace_step_pipe.py` (Subprocess Entry Point)

Machine-readable version of the existing `run_ace_step.py`. Designed for `subprocess.run()` invocation:

- **Args**: `--prompt` (required), `--duration` (required, no default), `--steps`, `--guidance`, `--seed`, `--outfile` (required)
- **Stdout**: JSON only. `{"status":"ok","path":"/path/to/file.wav","duration":23.5}` or `{"status":"error","message":"..."}`
- **Exit code**: 0 on success, 1 on failure
- **Behavior**: Sets CWD to `test-models/` for predictable output paths. Handles `GradientCheckpointingLayer` stub automatically. No emojis, no progress bars, no stderr chatter.

Based on the working script at `run_ace_step.py`. Key API surface from the pipeline:

```python
pipeline = ACEStepPipeline(device_id=0, dtype="bfloat16", torch_compile=False, cpu_offload=False)
pipeline.load_checkpoint()

result = pipeline(
    prompt="...",
    audio_duration=30.0,
    infer_step=20,
    guidance_scale=7.0,
    lyrics="",
    manual_seeds=[42],
)
# result = ["/path/to/output.wav", {...metadata...}]
```

Full ACE-Step invocation details are in `test-models/ACE_STEP_GUIDE.md`.

### ACE-Step Parameter Rationale for Background Music

The integration uses specific ACE-Step parameter values optimized for the background music use case. These differ from the model's defaults, which are tuned for full-song generation with vocals.

| Parameter | Model Default | TCP Default | Rationale |
|-----------|--------------|-------------|-----------|
| `infer_step` | 60 | 20 (configurable) | Background music doesn't need production-level detail. 20 steps is sufficient quality at ~3x the speed. Can increase to 30-50 for final output. |
| `guidance_scale` | 15.0 | 7.0 | Lower guidance produces more creative, less forced output. Background music should blend, not demand attention. Higher values make the music too rigidly follow the prompt. |
| `scheduler_type` | "euler" | "euler" | Fastest good-quality solver. No reason to change. |
| `cfg_type` | "apg" | "apg" | Adaptive Projected Guidance produces the smoothest results. No reason to change. |
| `lyrics` | None | "" (empty string) | Instrumental only. The pipeline will crash if passed `None` — must be empty string. |
| `audio_duration` | 60.0 | Computed from TTS lengths | Derived from `0.5 + max(all_tts_durations) + min(3.0, max_tts * 0.25)`. Never a fixed value. |

#### Why these choices work for ambient background music

**Lower guidance (7.0 vs 15.0):** The model's default 15.0 guidance is designed for songs where you want the music to precisely follow a detailed prompt (specific instruments, genre, vocal style, tempo). Background music benefits from a more relaxed interpretation — the model fills in gaps creatively rather than forcing a specific arrangement. At 15.0, background music can sound over-compressed and fatiguing.

**Fewer steps (20 vs 60):** Each denoising step is a full forward pass through the 24-layer transformer. For background music where subtle timbral details are less critical (the music will be mixed at 30% volume under speech), 20 steps produces output that is perceptually equivalent to 60 steps when played at low volume. The time savings is significant: ~65s vs ~195s on CPU for a 30s track.

**Prompt style for background music:** Effective prompts describe mood and texture rather than specific arrangements. "Gentle ambient piano with soft string pads, slow tempo, peaceful atmosphere, no vocals" works better than "A pop song with verse-chorus structure, piano intro, string crescendo at 1:30". The model responds best to genre + instrument + mood + tempo descriptors. Prompts are limited to 256 tokens (~150-200 words) by the UMT5 text encoder — not a constraint for the short prompts this use case requires.

#### When to deviate from these defaults

- **Increase `infer_step` to 40-50** if the music will be listened to on its own (not as background), or if the generated output has audible artifacts at 20 steps
- **Increase `guidance_scale` to 10-15** if the music doesn't match the prompt well at 7.0 — this can happen with unusual genre combinations
- **Change `scheduler_type` to "heun"** for marginally smoother output when using fewer steps (the second-order solver compensates for low step counts)
- **Set a fixed `manual_seeds`** during development for A/B testing prompt changes without seed variance confusing the results

#### `src/renderer/music_gen.py` (Subprocess Wrapper)

Runs in TCP's Python 3.12 process. Calls the pipe script via subprocess.

```python
def calculate_music_duration(max_tts_duration: float) -> float:
    """Music track length from the longest TTS in the batch.
    tail = min(3.0, max_tts_duration * 0.25)
    return 0.5 + max_tts_duration + tail
    """

def calculate_slot_video_duration(tts_duration: float) -> float:
    """Per-slot video duration.
    tail = min(3.0, tts_duration * 0.25)
    return 0.5 + tts_duration + tail
    """

def generate_background_music(
    prompt: str,
    duration: float,
    output_path: str,
    steps: int = 20,
    guidance: float = 7.0,
    seed: int | None = None,
) -> str:
    """Call ACE-Step via subprocess. Returns path to WAV file.

    Raises RendererError on subprocess failure, timeout, or missing output.
    """
```

#### `src/renderer/audio_mix.py` (Audio Mixing)

Uses ffmpeg for all audio operations. No Python audio libraries needed.

```python
def prepare_slot_audio(
    tts_path: str,
    music_path: str,
    output_path: str,
    tts_duration: float,
    music_volume: float = 0.3,
) -> tuple[str, float]:
    """Full audio pipeline for one slot.

    1. Trim monthly music to slot_video_duration
    2. Pad TTS with 0.5s silence at start (adelay)
    3. Mix: TTS at 1.0 + music at music_volume (amix)
    4. Return (mixed_audio_path, slot_video_duration)
    """
```

ffmpeg filter chain:
- Trim music: `ffmpeg -i music.wav -t <duration> -c copy trimmed.wav`
- Pad TTS: `adelay=500|500`
- Mix: `-filter_complex "[0:a]adelay=500|500[tts];[1:a]volume=0.3[music];[tts][music]amix=inputs=2:duration=longest:dropout_transition=2"`

### Modified Files

#### `src/config/defaults.py`

Add ACE-Step constants:

```python
ACE_STEP_PYTHON = "/mnt/storage/python_env/ace_step_env/bin/python"
ACE_STEP_SCRIPT = "/mnt/storage/Projects/code/test-models/run_ace_step_pipe.py"
ACE_STEP_DEFAULT_STEPS = 20
ACE_STEP_DEFAULT_GUIDANCE = 7.0
ACE_STEP_MUSIC_VOLUME = 0.3
ACE_STEP_TTS_DELAY = 0.5
ACE_STEP_MIN_TAIL = 3.0
ACE_STEP_TAIL_RATIO = 0.25
```

No default duration constant. Duration is always computed from TTS lengths.

#### `src/renderer/html_renderer.py`

Add optional `video_duration: float | None = None` parameter to `render_animated_video()`:

```python
# Replace the current audio-duration-based loop calculation:
if video_duration is not None:
    effective_loop = max(1, math.ceil(video_duration))
elif audio_path:
    audio_dur = get_audio_duration(audio_path)
    effective_loop = max(1, math.ceil(audio_dur + AUDIO_PAD_SECONDS))
```

This avoids double-padding when the mixed audio already has the correct total duration baked in.

#### `src/pipeline/orchestrator.py`

Add to `run_full_pipeline()` signature:

```python
bg_music: bool = False,
bg_music_prompt: str | None = None,
```

New stage between text generation and rendering:

**Stage 4.5 (TTS Pre-pass)**: When `bg_music=True`, iterate all automated slots, generate TTS audio for each, record paths and durations in dicts `tts_paths` and `tts_durations`.

**Stage 4.6 (Music Generation)**: Call `generate_background_music()` once with `duration=calculate_music_duration(max(tts_durations.values()))` and the provided prompt. Store path as `monthly_music_path`.

**Stage 5 (Rendering Loop)**: When `bg_music=True`, for each slot:
1. Call `prepare_slot_audio()` to mix TTS + trimmed music
2. Call `render_animated_video()` with `audio_path=mixed_audio_path` and `video_duration=slot_video_dur`

When `bg_music=False`, the existing inline TTS behavior is unchanged.

#### `src/cli/commands.py`

Add to `run_all` command:

```
--bg-music          Enable background music (implies --animate --audio)
--bg-music-prompt   Music generation prompt (required with --bg-music)
```

Add to `rerender` command:

```
--bg-music          Reuse monthly music from plan (or regenerate with --bg-music-prompt)
--bg-music-prompt   Override saved music prompt (triggers regeneration)
```

#### `_save_plan()` in orchestrator

Save to `render_config` when bg_music is active:

```python
if bg_music:
    render_config["bg_music"] = True
    render_config["bg_music_prompt"] = bg_music_prompt
    render_config["bg_music_path"] = monthly_music_path
```

This allows `rerender` to reuse the generated track without re-running ACE-Step.

### Module Responsibility (Existing Modules)

| Module | Change | New Responsibility |
|--------|--------|--------------------|
| `config/defaults.py` | Add constants | Owns ACE-Step paths and audio timing constants |
| `renderer/music_gen.py` | NEW | Owns subprocess invocation of ACE-Step and duration calculation |
| `renderer/audio_mix.py` | NEW | Owns ffmpeg-based audio mixing (TTS + music) |
| `renderer/html_renderer.py` | Add `video_duration` param | Accepts pre-calculated duration instead of reading from audio |
| `renderer/tts.py` | No changes | Existing `mux_audio_video()` and `get_audio_duration()` reused as-is |
| `pipeline/orchestrator.py` | Add stages 4.5, 4.6 | Orchestrates TTS pre-pass, music generation, and audio mixing |
| `cli/commands.py` | Add `--bg-music` options | Exposes background music to user |

### Dependency on External State

| Dependency | Location | Notes |
|-----------|----------|-------|
| ACE-Step Python env | `/mnt/storage/python_env/ace_step_env/` | Python 3.10, torch 2.9.1+cu128 |
| ACE-Step pipe script | `/mnt/storage/Projects/code/test-models/run_ace_step_pipe.py` | Must be created |
| Model checkpoints | `~/.cache/huggingface/hub/models--ACE-Step--ACE-Step-v1-3.5B/` | 7.8 GB, auto-downloaded |
| ffmpeg + ffprobe | System PATH | Already required by TCP for video encoding |
| GPU (planned) | N/A | Not currently available. CPU works but slow (~65s for 10s audio) |

### Plan Persistence

The generated monthly music track path is saved in the plan JSON under `render_config.bg_music_path`. When `rerender` is called with `--bg-music`, it reads this path and reuses the existing WAV file. Only `--bg-music-prompt` triggers regeneration.

### Example CLI Usage

```bash
# Full pipeline with background music
python tcp.py run-all --payload 2026-04_payload.json --animate --audio --bg-music --bg-music-prompt "gentle ambient piano with soft pads"

# --bg-music implies --animate --audio, so this is equivalent:
python tcp.py run-all --payload 2026-04_payload.json --bg-music --bg-music-prompt "gentle ambient piano with soft pads"

# Rerender reusing saved music
python tcp.py rerender --plan-dir outputs/202604 --all --bg-music

# Rerender with new music prompt (regenerates)
python tcp.py rerender --plan-dir outputs/202604 --all --bg-music --bg-music-prompt "warm acoustic guitar"
```

---

## License

[To be determined by user]
