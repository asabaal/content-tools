# Canvas Scene System (System B)

**Source files**: `src/canvas/` (renderer, models, geometry, lights, motion, repetition, compositing, recipes, loader, text_safety)

A full scene-graph compositing engine for complex layered background visuals. Triggered by setting the `"canvas"` key in any visual context (defaults, section visual, line override, word override). When present, the canvas scene **completely replaces** the normal background rendering.

---

## Activation

In `script.json`, anywhere visual properties are accepted:

```json
{
  "sections": [{
    "visual": {
      "canvas": { ... }
    }
  }],
  "defaults": {
    "canvas": { ... }
  }
}
```

When `canvas` is present, `renderer.py:992-994` dispatches to `canvas.renderer.render_canvas()` instead of `_draw_background()`.

---

## Top-Level Schema

```json
{
  "canvas": {
    "width": 1920,
    "height": 1080,
    "base_color": "#0d1117"
  },
  "palette": {
    "primary": "#2E86C1",
    "secondary": "#8E44AD"
  },
  "layers": ["background", "middleground", "foreground"],
  "objects": {
    "background": { ... CanvasObject ... },
    "middleground": { ... CanvasObject ... },
    "foreground": { ... CanvasObject ... }
  },
  "text_safety": { ... }
}
```

| Field | Type | Description |
|---|---|---|
| `canvas` | dict | Canvas dimensions and base fill color |
| `palette` | dict | Named color references used by `$name` in fill/stroke/color fields |
| `layers` | string[] | Ordered list of object IDs to render (z-order) |
| `objects` | dict | Named object definitions (key = object ID) |
| `text_safety` | dict | Optional overlay to protect text readability against busy backgrounds |

---

## CanvasObject Fields

Each entry in `objects` is a dict with these fields:

```json
"object_id": {
  "type": "shape",
  "geometry": { "shape": "rectangle" },
  "position": [0.5, 0.5],
  "size": [1.0, 1.0],
  "rotation": 0,
  "opacity": 1.0,
  "style": {
    "fill": "$primary",
    "stroke": "none",
    "stroke_width": 2,
    "corner_radius": 0,
    "blend_mode": "normal",
    "glow": "none",
    "glow_radius": 10,
    "glow_intensity": 0.5,
    "blur": 0
  },
  "motion": { "type": "static" },
  "repeat": { "mode": "none" },
  "mask": null,
  "timing": {},
  "children": []
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `type` | string | — | Object type (required): `shape`, `light`, `gradient`, `path`, `image`, `texture`, `mask`, `group` |
| `geometry` | dict | `{}` | Type-specific geometry config |
| `position` | [x,y] or dict | canvas center | Center position. Values 0.0-1.0 = normalized, >1.0 = absolute pixels. Dict form: `{"x": 0.5, "y": 0.5}` |
| `size` | [w,h] or dict | canvas size | Width/height. Values 0.0-1.0 = normalized, >1.0 = absolute pixels. Dict form: `{"w": 1.0, "h": 1.0}` |
| `rotation` | float | 0 | Rotation in degrees |
| `opacity` | float | 1.0 | 0.0 (transparent) to 1.0 (opaque) |
| `style` | dict | `{}` | Fill, stroke, blend mode, glow, blur |
| `motion` | dict | `{"type": "static"}` | Animation over time |
| `repeat` | dict | `{"mode": "none"}` | Instance repetition |
| `mask` | string | null | Object ID to use as alpha mask |
| `timing` | dict | `{}` | Reserved for future use |
| `children` | string[] | `[]` | Child object IDs (for `group` type only) |

### Palette References in Style

Colors in `style` can reference palette keys with `$` prefix:

```json
"palette": { "primary": "#2E86C1" },
"style": { "fill": "$primary" }
```

This resolves `$primary` → `#2E86C1` at render time.

---

## Object Types

### 1. `shape` — Geometric Shapes

`geometry.shape` selects the shape type.

```json
{
  "type": "shape",
  "geometry": { "shape": "rectangle" },
  "style": { "fill": "#4A90E2", "stroke": "#ffffff", "stroke_width": 2 }
}
```

| Shape | `geometry` Params | Rendering |
|---|---|---|
| `"rectangle"` / `"rect"` | — | Rectangle. `style.corner_radius` > 0 = rounded rect |
| `"circle"` / `"ellipse"` | — | Ellipse filling the bounding box |
| `"diamond"` | — | 4-point rhombus |
| `"polygon"` | `sides` (default 6) | N-sided regular polygon |
| `"hexagon"` | (auto, sides=6) | 6-sided regular polygon |
| `"octagon"` | (auto, sides=8) | 8-sided regular polygon |
| `"pentagon"` | (auto, sides=5) | 5-sided regular polygon |
| `"triangle"` | (auto, sides=3) | 3-sided regular polygon |
| `"line"` | `end: [x,y]` | Line from center to end point |
| `"ring"` | `inner_ratio` (default 0.6) | Donut shape (outer circle - inner circle) |
| `"arc"` | `start_angle`, `end_angle` | Arc segment (degrees) |
| `"grid"` | `rows`, `cols`, `gap` | Grid of rectangles |

**Style fields for shapes:**

| Style Field | Type | Description |
|---|---|---|
| `fill` | hex or `"none"` | Fill color. Can use `$palette_key` |
| `stroke` | hex or `"none"` | Outline color. Can use `$palette_key` |
| `stroke_width` | int | Outline thickness in pixels |
| `corner_radius` | float | Rounded corner radius (rectangle only) |
| `blend_mode` | string | See blend modes table |
| `glow` | hex or `"none"` | Glow color |
| `glow_radius` | int | Gaussian blur radius for glow |
| `glow_intensity` | float | Glow brightness multiplier (0-1) |
| `blur` | float | Gaussian blur on the rendered layer |

---

### 2. `light` — Light Sources

Lights render colored illumination that fades with distance. They produce additive-looking results that work best on dark base colors.

```json
{
  "type": "light",
  "geometry": { "shape": "radial" },
  "style": { "color": "$primary", "intensity": 1.2, "softness": 0.8, "blend_mode": "add" }
}
```

| Light Type | `geometry` Params | Behavior |
|---|---|---|
| `"radial"` | — | Circular falloff from center. Alpha = `(1 - dist) * softness` |
| `"conic"` | `offset` (radians), `stops` (int) | Angular gradient sweeping around center |
| `"spot"` | `angle` (degrees), `spread` (float) | Directional cone of light |

**Style fields for lights:**

| Style Field | Type | Description |
|---|---|---|
| `color` | hex | Light color. Can use `$palette_key` |
| `intensity` | float | Brightness multiplier (0.0+) |
| `softness` | float | Falloff curve (1.0 = linear, higher = softer) |
| `blend_mode` | string | Typically `"add"` or `"screen"` for best results |

---

### 3. `gradient` — Color Gradients

```json
{
  "type": "gradient",
  "geometry": { "direction": "vertical" },
  "style": { "colors": ["#ff0000", "#00ff00", "#0000ff"] }
}
```

| `geometry.direction` | Behavior |
|---|---|
| `"vertical"` | Top-to-bottom |
| `"horizontal"` | Left-to-right |
| `"angle_<deg>"` | Linear at angle (e.g. `"angle_45"`) |
| `"radial"` | Center outward |
| `"conic"` | Angular around center |

Multiple color stops with linear interpolation between them.

---

### 4. `path` — Arbitrary Paths

```json
{
  "type": "path",
  "geometry": {
    "points": [[0.1, 0.5], [0.3, 0.3], [0.5, 0.5], [0.7, 0.7], [0.9, 0.5]],
    "closed": false
  },
  "style": { "stroke": "$primary", "stroke_width": 3 }
}
```

| Field | Type | Description |
|---|---|---|
| `points` | [[x,y], ...] | Path vertices. 0.0-1.0 normalized or absolute pixels |
| `closed` | bool | If true + fill color = filled polygon |

When `closed: true` and `fill` is set, renders as a filled polygon. Otherwise renders as a stroked polyline.

---

### 5. `image` — Bitmap Images

```json
{
  "type": "image",
  "geometry": { "src": "/path/to/image.png" }
}
```

| Field | Type | Description |
|---|---|---|
| `src` | string | File path to image (also accepts `path` as alias) |

Loads the image, converts to RGBA, and renders it at the object's position/size.

---

### 6. `texture` — Procedural Noise Textures

```json
{
  "type": "texture",
  "geometry": { "noise_type": "grain", "seed": 42 }
}
```

| `noise_type` | Effect |
|---|---|
| `"noise"` / `"grain"` / `"noise_grain"` | Random noise, 50 intensity, 80 alpha |
| `"paper"` | Subtle paper texture, 20 intensity, 60 alpha |
| `"film"` | Film grain, 40 intensity, 70 alpha |

---

### 7. `mask` — Alpha Masks

Used as a mask reference on another object. The mask object's ID goes in the other object's `mask` field.

```json
{
  "type": "mask",
  "geometry": { "shape": "circle" },
  "position": [0.5, 0.5],
  "size": [0.5, 0.5]
}
```

| `geometry.shape` | Behavior |
|---|---|
| `"rectangle"` / `"rect"` | Hard-edged rectangular mask |
| `"circle"` / `"ellipse"` | Soft circular mask (Gaussian falloff) |
| `"gradient"` | Linear gradient mask. `geometry.direction`: `"vertical"` or `"horizontal"` |

Example — apply a mask to an object:
```json
{
  "objects": {
    "photo": {
      "type": "image",
      "geometry": { "src": "photo.png" },
      "mask": "circle_mask"
    },
    "circle_mask": {
      "type": "mask",
      "geometry": { "shape": "circle" },
      "position": [0.5, 0.5],
      "size": [0.6, 0.6]
    }
  }
}
```

---

### 8. `group` — Composite Groups

Groups apply a shared transform (position, rotation, opacity, motion) to all children:

```json
{
  "type": "group",
  "position": [0.5, 0.5],
  "rotation": 0,
  "opacity": 1.0,
  "motion": { "type": "rotate", "speed": 0.5 },
  "children": ["child1", "child2"]
}
```

Children are rendered in order with child transforms merged onto the group transform (rotation and opacity are cumulative).

---

## Blend Modes

Set via `style.blend_mode`. Available modes:

| Mode | Formula | Use Case |
|---|---|---|
| `"normal"` | src | Standard alpha blending |
| `"screen"` | dst + src - dst*src/255 | Lighten, brighten |
| `"multiply"` | dst * src / 255 | Darken, tint |
| `"overlay"` | conditional multiply/screen | Contrast enhancement |
| `"soft_light"` | soft light formula | Subtle lighting |
| `"add"` | dst + src | Brighten, glow effects |
| `"lighten"` | max(dst, src) | Keep brightest |
| `"darken"` | min(dst, src) | Keep darkest |

---

## Motion System

Each object can have a `motion` dict that animates its position, rotation, or opacity over time `t` (seconds from render start).

```json
"motion": { "type": "drift", "speed": 1.0, "amplitude": 0.05, "phase": 0.0 }
```

| Motion Type | Parameters | Effect |
|---|---|---|
| `"static"` | — | No motion (default) |
| `"rotate"` | `speed` | Continuous rotation: `rot += t * speed * 60` |
| `"drift"` | `speed`, `amplitude`, `phase` | Sine-wave drift: `x += sin(t * speed * 2π + phase) * amplitude * w` |
| `"pulse"` | `speed`, `amplitude`, `phase` | Opacity pulse: `opacity *= 0.7 + 0.3 * (1 + sin(...)) / 2` |
| `"breathe"` | `speed`, `phase` | Slow opacity breathing: `opacity *= 0.5 + 0.5 * sin(t * speed * π + phase) * 0.5` |
| `"zoom"` | `speed`, `amplitude` | Scale over time: `factor = 1 + amplitude * t * speed` |
| `"shimmer"` | `speed`, `phase` | Rapid shimmer: `opacity *= 0.3 + 0.7 * sin(t * speed * 4π + phase)` |
| `"orbit"` | `speed`, `amplitude`, `phase` | Circular orbit: `x += orbit_r * cos(...), y += orbit_r * sin(...)` |

---

## Repetition System

Each object can be repeated multiple times via the `repeat` dict.

```json
"repeat": { "mode": "grid", "rows": 3, "cols": 5, "spacing": 0.15 }
```

### Repeat Modes

#### `"none"` — Single instance (default)

#### `"grid"` — Rectangular array
| Param | Type | Default | Description |
|---|---|---|---|
| `rows` | int | 3 | Number of rows |
| `cols` | int | 3 | Number of columns |
| `spacing` / `spacing_x` / `spacing_y` | float | 0.15 | Spacing between instances (normalized 0-1) |
| `jitter_x` | float | 0 | Random horizontal jitter |
| `jitter_y` | float | 0 | Random vertical jitter |
| `seed` | int | 42 | Random seed for jitter |

#### `"radial"` — Circular arrangement
| Param | Type | Default | Description |
|---|---|---|---|
| `count` | int | 8 | Number of instances |
| `radius` | float | 0.3 | Radius of arrangement (normalized) |
| `center` | [x,y] | object position | Center of arrangement |
| `start_angle` | float | 0 | Starting angle offset (radians) |

Each instance is also rotated by its angular position in the circle.

#### `"random"` — Random scatter
| Param | Type | Default | Description |
|---|---|---|---|
| `count` | int | 10 | Number of instances |
| `seed` | int | 42 | Random seed |
| `area` | dict | `{x:0.1, y:0.1, w:0.8, h:0.8}` | Bounding area for scatter |
| `scale_variance` | float | 0.3 | Random size variance |
| `opacity_variance` | float | 0.2 | Random opacity variance |

#### `"mirror"` — Reflected copies
| Param | Type | Default | Description |
|---|---|---|---|
| `axes` | string | `"x"` | `"x"`, `"y"`, or `"xy"` for mirror axes |

Creates mirrored copies across the canvas center.

---

## Text Safety Overlay

Protects text readability by dimming the background in text-safe areas:

```json
"text_safety": {
  "mode": "dim_center",
  "width": 0.6,
  "height": 0.4,
  "strength": 0.3,
  "margin": 0.2
}
```

| Mode | Effect |
|---|---|
| `"none"` | No overlay |
| `"dim_center"` / `"dim"` | Elliptical dimming zone in center. `width`/`height` define safe zone size, `strength` controls darkness |
| `"vignette_text"` | Edge vignette that darkens from edges. `margin` controls how far vignette extends inward, `strength` controls darkness |

---

## Canvas Recipes

The `recipes.py` module provides convenience functions that generate full canvas scene configs. These can be used as starting points or called programmatically.

Available recipes:
- **`cross`** — Two intersecting semi-transparent bars forming a cross
- **`conic`** — Conic light with 5-color stop gradient
- **`diamond`** — One or more diamond shapes in grid repeat
- **`dual_spot`** — Two radial lights at configurable positions
- **`spiral`** — Rotating spiral path
- **`bands`** — Horizontal bands via repeat grid
- **`radial_center`** / **`radial_tl`** / **`radial_br`** — Single radial light at position

Example recipe output (cross):
```json
{
  "canvas": { "base_color": "#080e18" },
  "palette": { "primary": "#1a6078", "secondary": "#501878" },
  "layers": ["h_bar", "v_bar"],
  "objects": {
    "h_bar": {
      "type": "shape",
      "geometry": { "shape": "rectangle" },
      "position": [0.5, 0.5],
      "size": [1.0, 0.12],
      "opacity": 0.3,
      "style": { "fill": "$primary", "blend_mode": "screen" }
    },
    "v_bar": {
      "type": "shape",
      "geometry": { "shape": "rectangle" },
      "position": [0.5, 0.5],
      "size": [0.12, 1.0],
      "opacity": 0.3,
      "style": { "fill": "$primary", "blend_mode": "screen" }
    }
  }
}
```

---

## Complete Example

A 3-spot scene with rotating background diamond, pulsing radial lights, and text safety:

```json
{
  "canvas": {
    "base_color": "#0a0a1a"
  },
  "palette": {
    "blue": "#2E86C1",
    "purple": "#8E44AD",
    "gold": "#F39C12"
  },
  "layers": ["bg_diamond", "spot_left", "spot_right", "spot_center"],
  "objects": {
    "bg_diamond": {
      "type": "shape",
      "geometry": { "shape": "diamond" },
      "position": [0.5, 0.5],
      "size": [0.8, 0.8],
      "opacity": 0.15,
      "style": { "stroke": "$blue", "stroke_width": 1, "fill": "none" },
      "repeat": {
        "mode": "radial",
        "count": 6,
        "radius": 0.35
      },
      "motion": { "type": "rotate", "speed": 0.3 }
    },
    "spot_left": {
      "type": "light",
      "geometry": { "shape": "radial" },
      "position": [0.25, 0.5],
      "size": [0.5, 0.5],
      "opacity": 0.8,
      "style": { "color": "$blue", "intensity": 1.0, "softness": 0.8 },
      "motion": { "type": "pulse", "speed": 0.5, "amplitude": 0.2 }
    },
    "spot_right": {
      "type": "light",
      "geometry": { "shape": "radial" },
      "position": [0.75, 0.5],
      "size": [0.5, 0.5],
      "opacity": 0.8,
      "style": { "color": "$purple", "intensity": 1.0, "softness": 0.8 },
      "motion": { "type": "pulse", "speed": 0.7, "amplitude": 0.2 }
    },
    "spot_center": {
      "type": "light",
      "geometry": { "shape": "radial" },
      "position": [0.5, 0.5],
      "size": [0.6, 0.6],
      "opacity": 0.6,
      "style": { "color": "$gold", "intensity": 0.8, "softness": 1.2 }
    }
  },
  "text_safety": {
    "mode": "dim_center",
    "width": 0.7,
    "height": 0.5,
    "strength": 0.25
  }
}
```

---

## Performance Notes

- Canvas scenes are rendered per-frame when they contain animated objects (motion, rotation). Non-animated scenes are cached per section.
- Complex scenes with many objects/repeats are processed in chunks — scatter fields and grid repeats are bounded.
- Each object goes through: repeat expansion → motion computation → shape rendering → glow/blur → blend compositing → mask application.

---

## See Also

- `src/canvas/renderer.py` — Main canvas render loop
- `src/canvas/geometry.py` — Shape and path rendering  
- `src/canvas/lights.py` — Light and gradient rendering
- `src/canvas/motion.py` — Motion animation system
- `src/canvas/repetition.py` — Repeat/instance expansion
- `src/canvas/compositing.py` — Blend modes, glow, blur
- `src/canvas/recipes.py` — Preset scene generators
- `src/canvas/loader.py` — Scene validation
- `src/canvas/models.py` — CanvasObject/CanvasScene data models
- `src/canvas/text_safety.py` — Text safety overlay
- `docs/BACKGROUND_GRADIENTS.md` — System A for simpler direction-based gradients
- `tests/test_canvas_renderer.py` — Test coverage
- `tests/test_canvas_motion.py` — Motion tests
- `tests/test_canvas_recipes.py` — Recipe tests
