# Unified Editor Implementation Plan

**Status**: IN PROGRESS (Phase A: Backend)
**Replaces**: `tools/03-sync/`, `tools/04-structure/`, `tools/05-visual-design/`
**New tool**: `tools/editor/index.html` served at `/editor`

---

## Overview

A single timeline-driven browser editor that handles word/line timing, song structure, and per-section visual styling. The user does all creative work (except final render) in one workspace.

### What it replaces

| Old tool | Functionality | Status |
|----------|--------------|--------|
| `tools/03-sync/` | Line/word timing, waveform, audio playback | Removed |
| `tools/04-structure/` | Section definitions (never built) | Removed |
| `tools/05-visual-design/` | Visual design (never built) | Removed |
| `tools/analysis/` | Alignment quality review | Kept as-is |

### What it preserves from 03-sync

- Audio playback with seek/loop
- Waveform rendering with beat markers
- Word box dragging (body, left edge, right edge)
- Source indicators (transcription, onset, interpolated)
- Save/load synced lyrics
- Keyboard shortcuts (space, arrows, escape)
- Unsaved changes guard

---

## Layout

```
+-------------------------------------------------------------------+
|  MVP Editor           [Auto-Sync] [Save] [Render]   status        |
+---------+-------------------------------------------+-------------+
| Section |  TIMELINE                                 | Properties  |
|  List   |                                           |   Panel     |
|         |  [Intro][  Verse 1  ][ Chorus ][V2][ Out] |             |
| Intro   |  ==waveform=================================| (context    |
| Verse 1 |  beat markers, playhead, word boxes       |  dependent  |
| Chorus  |  click-to-seek, zoom/scroll               |  on         |
| Verse 2 |                                           |  selected   |
| Outro   +-------------------------------------------+  item)      |
|         |  DETAIL AREA                              |             |
| + Add   |                                           |             |
|         |  Line selected -> word timing table        |             |
|         |  Section selected -> visual properties     |             |
|         |  Nothing selected -> summary               |             |
+---------+-------------------------------------------+-------------+
```

### Three interaction contexts

**Timeline (center)**:
- Waveform with colored section overlay bands
- Section boundaries as draggable vertical dividers
- Lyrics text rows within section bands
- Word boxes on zoom-in (inherited from 03-sync)
- Beat markers, playhead, click-to-seek
- Zoom in/out, horizontal scroll

**Section list (left sidebar)**:
- Each section as a row: type icon + name + line count
- Click to select -> properties panel shows section editor
- Buttons to: split, merge with adjacent, delete
- "+" button to add new section

**Properties panel (right sidebar)** — context-dependent:
- **Line selected**: word timing table (start/end/source per word), line start/end, confidence
- **Section selected**: section type dropdown, template dropdown, visual property editors
- **Nothing selected**: summary stats (total lines, sections, timing coverage)

---

## Section Types

Core types (dropdown):

| Type | Label |
|------|-------|
| `verse` | Verse |
| `chorus` | Chorus |
| `bridge` | Bridge |
| `intro` | Intro |
| `outro` | Outro |
| `pre_chorus` | Pre-Chorus |
| `hook` | Hook |
| `interlude` | Interlude |
| `instrumental` | Instrumental |

Custom types: free text input, stored as `"type": "custom", "custom_type": "breakdown"`

---

## Data Models

### `structure.json`

```json
{
  "sections": [
    {
      "id": "s0",
      "type": "intro",
      "name": "Intro",
      "start_line": 0,
      "end_line": 3,
      "tags": [],
      "visual": {
        "background_type": "gradient",
        "background_color": "#4A90E2",
        "gradient_colors": ["#4A90E2", "#8E44AD"],
        "gradient_direction": "diagonal_tl_br",
        "texture_type": "none",
        "texture_opacity": 0.15,
        "text_color": null,
        "text_auto_contrast": true,
        "font_size": 48,
        "animation_type": "fade",
        "animation_speed": 1.0,
        "reactivity": ["vocals"]
      }
    }
  ]
}
```

### Visual properties (per section, matches ACP specificity)

| Property | Type | Options | ACP equivalent |
|----------|------|---------|----------------|
| `background_type` | str | `"solid"`, `"gradient"`, `"image"` | Background system |
| `background_color` | str | hex color | Style preset `background` |
| `gradient_colors` | list[str] or null | 2-4 hex strings | `--gradient-colors` |
| `gradient_direction` | str | 9 directions (see below) | `--gradient-direction` |
| `texture_type` | str | 7 types (see below) | `--texture-type` |
| `texture_opacity` | float | 0.0-1.0 | `--texture-opacity` |
| `text_color` | str or null | hex or null (auto) | `--text-color` |
| `text_auto_contrast` | bool | true/false | `auto_contrast_color()` |
| `font_size` | int | pixels | Style preset `font_size` |
| `animation_type` | str | 6 types (see below) | `--anim-type` |
| `animation_speed` | float | 0.1-2.0 | `--anim-speed` |
| `reactivity` | list[str] | stem types | N/A (new for music) |

**Gradient directions** (same as ACP):
`vertical_top_bottom`, `vertical_bottom_top`, `horizontal_left_right`, `horizontal_right_left`, `diagonal_tl_br`, `diagonal_tr_bl`, `radial_center`, `radial_top`, `radial_bottom`

**Texture types** (same as ACP):
`none`, `noise_fine`, `noise_coarse`, `grain_film`, `paper_subtle`, `vignette_soft`, `vignette_heavy`

**Animation types**:
`fade`, `slide`, `scale`, `typewriter`, `pulse`, `none`

**Reactivity options**:
`vocals`, `drums`, `bass`, `synth`, `energy` — list of stems/features that drive visual changes

### Python dataclasses

```python
@dataclass
class SectionVisual:
    background_type: str = "solid"
    background_color: str = "#1a1a2e"
    gradient_colors: Optional[List[str]] = None
    gradient_direction: str = "vertical_top_bottom"
    texture_type: str = "none"
    texture_opacity: float = 0.15
    text_color: Optional[str] = None
    text_auto_contrast: bool = True
    font_size: int = 48
    animation_type: str = "fade"
    animation_speed: float = 1.0
    reactivity: List[str] = field(default_factory=lambda: ["vocals"])

    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, d: dict) -> "SectionVisual": ...

@dataclass
class StructureSection:
    id: str
    type: str
    custom_type: Optional[str] = None
    name: str
    start_line: int
    end_line: int
    tags: List[str] = field(default_factory=list)
    visual: SectionVisual = field(default_factory=SectionVisual)

    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, d: dict) -> "StructureSection": ...
```

---

## Templates

6 predefined visual presets in `templates/` as JSON files. Each is a `SectionVisual` dict.

| Template | Background | Texture | Animation | Reactivity |
|----------|-----------|---------|-----------|------------|
| `default` | Dark solid `#1a1a2e` | none | fade | vocals |
| `elegant` | Subtle gradient `#1a1a2e` -> `#16213e` | vignette_soft | fade | energy |
| `modern` | Solid `#16213e` | none | slide | none |
| `energetic` | Bright gradient `#E67E22` -> `#C0392B` | noise_fine | pulse | drums, bass |
| `dynamic` | Gradient `#4A90E2` -> `#8E44AD` | none | scale | energy |
| `extreme` | Vibrant gradient `#8E44AD` -> `#C0392B` | grain_film | pulse | all |

Users pick a template -> visual properties populated -> customize from there.

---

## Section Editing

### Auto-generation

When editor loads with no `structure.json`:
1. Read section markers from `lyrics_raw.json` (each line has a `section` field)
2. Group consecutive lines with same section_type into sections
3. Assign IDs (s0, s1, s2, ...)
4. Apply `default` template to all sections
5. Return generated structure

### CRUD operations

- **Create**: Insert section boundary between existing sections (splits section at line boundary)
- **Delete**: Merge section with adjacent (lines absorbed by neighbor)
- **Resize**: Drag section boundary on timeline (changes `start_line`/`end_line`)
- **Change type**: Dropdown in properties panel
- **Change visual**: All visual properties editable in properties panel

### Constraints

- Every line must belong to exactly one section (no gaps, no overlaps)
- Section boundaries are between lines (not within a line)
- `start_line` and `end_line` are inclusive

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/structure` | Load `structure.json` |
| POST | `/api/structure` | Save `structure.json` |
| GET | `/api/templates` | List template names + visual presets |
| POST | `/api/auto-generate-structure` | Build initial structure from lyrics markers |
| GET | `/api/alignment-analysis` | Word timing data (already exists) |
| POST | `/api/auto-sync` | Transcription-merged sync (already exists) |
| GET/POST | `/api/lyrics-synced` | Synced lyrics (already exists) |

---

## CLI Changes

`mvp sync` updated to:
1. Run auto-sync (as before)
2. Auto-generate `structure.json` from section markers
3. Save both files

`mvp serve` updated to:
- Serve editor at `/editor`
- Keep analysis tool at `/tools/analysis/`
- Redirect `/` to `/editor`

---

## Implementation Phases

### Phase A: Backend (current)
- `StructureSection` + `SectionVisual` dataclasses in `src/pipeline/models.py`
- 6 template JSON files in `templates/`
- 4 new API endpoints in `serve.py`
- Auto-generate structure from lyrics section markers
- Tests, 100% coverage

### Phase B: Editor — timeline + sections
- Build on 03-sync's audio/waveform/drag infrastructure
- Section overlay rendering on timeline (colored bands)
- Section list sidebar with CRUD
- Section boundary dragging on timeline
- Auto-generate structure on load (if missing)
- Line selection -> word timing table in properties panel
- Save structure + synced lyrics

### Phase C: Editor — properties + visual styling
- Section selection -> visual properties panel
- Template dropdown per section
- Color pickers, sliders, dropdowns for visual properties
- Live section preview (CSS colors in timeline bands)

### Phase D: Cleanup
- Remove `tools/03-sync/`, `tools/04-structure/`, `tools/05-visual-design/`
- Serve editor at `/editor`
- Update routing in `serve.py`
- Update DESIGN.md implementation phases
