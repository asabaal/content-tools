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

## License

[To be determined by user]
