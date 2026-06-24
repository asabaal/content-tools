# Background Gradient System (System A)

**Source**: `src/render/gradients.py`

Direction-based gradient backgrounds. Controlled via `gradient_direction` (string) and `gradient_params` (optional dict) in any visual context (defaults, section visual, line override, word override).

---

## How It Works

The renderer (`renderer.py:_draw_gradient`) evaluates the direction string + params to compute a 2D scalar field `t(x,y)` in [0,1], then maps that field through the color stops via `apply_color_map()`.

```
t(x,y) = compute_field(w, h, primitive, params)
output[x,y] = lerp(gradient_colors, t[x,y])
```

---

## Direction String Reference

All gradient directions are parsed by `parse_direction()` in `gradients.py:394-498`.

### Linear Gradients

| Direction String | Axis | Mapping |
|---|---|---|
| `"vertical_top_bottom"` | y, forward | t = y / h |
| `"vertical_bottom_top"` | y, reverse | t = 1 - y/h |
| `"horizontal_left_right"` | x, forward | t = x / w |
| `"horizontal_right_left"` | x, reverse | t = 1 - x/w |
| `"diagonal_tl_br"` | diagonal, forward | t = (x + y) / (w + h) |
| `"diagonal_tr_bl"` | diagonal, reverse | t = 1 - (x + y)/(w + h) |
| `"angle_<degrees>"` (e.g. `"angle_45"`) | angle, 0-360 | t = projection onto rotated axis |

`gradient_params` overrides: `axis` (`"x"` / `"y"` / `"diagonal"` / `"angle"`), `angle` (float), `reverse` (bool)

### Radial Spot Fields

**Primitive**: `spot_field`

| Direction String | Positions |
|---|---|
| `"radial_center"` | `[[0.5, 0.5]]` |
| `"radial_top"` | `[[0.5, 0.0]]` |
| `"radial_bottom"` | `[[0.5, 1.0]]` |
| `"radial_tl"` | `[[0.0, 0.0]]` |
| `"radial_br"` | `[[1.0, 1.0]]` |
| `"dual_spot_<x1>_<y1>_<x2>_<y2>"` | `[[x1,y1], [x2,y2]]` |

`gradient_params`:
| Param | Type | Default | Description |
|---|---|---|---|
| `positions` | `[[x,y], ...]` | `[[0.5,0.5]]` | Any number of spot centers (normalized 0-1) |
| `softness` | float | 1.0 | Exponent on distance (higher = softer falloff) |
| `radius_scale` | float | 2.0 | Multiplier on spot radius |
| `blend` | string | `"nearest"` | `"nearest"` = min distance, `"additive"` = sum lights, `"max"` = max lights |

**Example — 5-spot field with additive blend:**
```json
{
  "gradient_direction": "radial_center",
  "gradient_params": {
    "positions": [[0.3, 0.3], [0.7, 0.3], [0.5, 0.7], [0.2, 0.8], [0.8, 0.8]],
    "softness": 1.5,
    "radius_scale": 1.5,
    "blend": "additive"
  }
}
```

With `"additive"` blend, overlapping spots combine their light producing brighter intersections. With `"max"`, only the nearest spot at each pixel affects the color.

### Cross

| Direction String | Primitive |
|---|---|
| `"cross"` | `cross` |

`gradient_params`:
| Param | Type | Default | Description |
|---|---|---|---|
| `thickness` | float | 1.5 | Arm thickness multiplier |
| `center` | [x, y] | [0.5, 0.5] | Cross center position |
| `softness` | float | 0.0 | Edge softness (0 = hard, higher = softer) |

Produces a cruciform pattern: `t = min(|dx|, |dy|) * thickness` where dx, dy are normalized distances from center. Color stops flow from center outward.

### Diamond

| Direction String | Primitive |
|---|---|
| `"diamond"` | `diamond` |

`gradient_params`:
| Param | Type | Default | Description |
|---|---|---|---|
| `scale` | float | 1.0 | Overall size multiplier |
| `center` | [x, y] | [0.5, 0.5] | Diamond center |

Manhattan distance from center: `t = (|dx| + |dy|) / max_d`. Creates diamond-shaped isoclines.

### Conic

| Direction String | Primitive |
|---|---|
| `"conic"` or `"conic_<phase>"` (e.g. `"conic_0.8"`) | `conic` |

`gradient_params`:
| Param | Type | Default | Description |
|---|---|---|---|
| `phase` | float | 0.0 | Angular offset in radians |
| `frequency` | float | 1.0 | Number of full angular sweeps |
| `center` | [x, y] | [0.5, 0.5] | Pivot point |
| `reverse` | bool | false | Reverse sweep direction |

Angular gradient that sweeps around the center point like a clock hand.

### Spiral

| Direction String | Primitive |
|---|---|
| `"spiral"` | `spiral` |

`gradient_params`:
| Param | Type | Default | Description |
|---|---|---|---|
| `tightness` | float | 0.5 | Spiral wrap frequency |
| `phase` | float | 0.0 | Angular offset |
| `center` | [x, y] | [0.5, 0.5] | Spiral center |
| `radial_weight` | float | 1.0 | Balance between radial and angular components |

Combines radial distance and angle for spiral isoclines.

### Bands

| Direction String | Primitive |
|---|---|
| `"bands"` | `bands` |

`gradient_params`:
| Param | Type | Default | Description |
|---|---|---|---|
| `axis` | string | `"y"` | `"x"` = vertical bands, `"y"` = horizontal bands |
| `frequency` | int | auto | Number of bands |
| `phase` | float | 0.0 | Band offset |
| `wave` | bool | false | Enable wavy bands |
| `wave_amplitude` | float | 0.1 | Wave distortion amount |
| `wave_frequency` | float | 3.0 | Wave oscillation frequency |

Creates parallel color bands. With `wave: true`, bands become wavy/sinuous.

### Rings

| Direction String | Primitive |
|---|---|
| `"rings"` or `"rings_<frequency>"` (e.g. `"rings_10"`) | `rings` |

`gradient_params`:
| Param | Type | Default | Description |
|---|---|---|---|
| `center` | [x, y] | [0.5, 0.5] | Ring center |
| `frequency` | float | 5.0 | Number of concentric rings |
| `phase` | float | 0.0 | Ring offset |
| `contrast` | float | 1.0 | Ring sharpness (higher = sharper transitions) |
| `radial_scale` | float | 1.0 | Ring spacing multiplier |

Uses `sin(dist * freq * 2π)` for smooth ring transitions. Higher contrast gives sharper ring edges.

### Grid

| Direction String | Primitive |
|---|---|
| `"grid"` or `"grid_<frequency>"` (e.g. `"grid_8"`) | `grid` |

`gradient_params`:
| Param | Type | Default | Description |
|---|---|---|---|
| `freq_x` | float | 5.0 | Horizontal frequency |
| `freq_y` | float | 5.0 | Vertical frequency |
| `phase_x` | float | 0.0 | Horizontal phase offset |
| `phase_y` | float | 0.0 | Vertical phase offset |
| `shape` | string | `"diamond"` | `"diamond"` = sin(x)+sin(y), `"checker"` = binary checkerboard, `"dots"` = sin(x)*sin(y) |
| `contrast` | float | 1.0 | Sharpness of transitions |

### Scatter Field

| Direction String | Primitive |
|---|---|
| `"scatter_field"` | `scatter_field` |

`gradient_params`:
| Param | Type | Default | Description |
|---|---|---|---|
| `count` | int | 20 | Number of scattered elements (max 200) |
| `seed` | int | 42 | Random seed for reproducibility |
| `shape` | string | `"dot"` | `"dot"` (circular), `"diamond"`, or `"ring"` |
| `size` | float | 0.05 | Element size (normalized) |
| `size_jitter` | float | 0.3 | Random variance in element sizes (0 = uniform) |
| `blend` | string | `"max"` | `"max"` or `"additive"` |

Randomly scatters shape elements across the canvas. Each element creates a local gradient spot. Processed in chunks of 8 for performance.

### Burst

| Direction String | Primitive |
|---|---|
| `"burst"` or `"burst_<ray_count>"` (e.g. `"burst_12"`) | `burst` |

`gradient_params`:
| Param | Type | Default | Description |
|---|---|---|---|
| `center` | [x, y] | [0.5, 0.5] | Burst center |
| `ray_count` | int | 8 | Number of rays (minimum 2) |
| `phase` | float | 0.0 | Angular offset |
| `sharpness` | float | 0.5 | Ray edge sharpness (0-1) |
| `radial_falloff` | float | 1.0 | How quickly rays fade from center |

Creates a radial starburst with configurable ray count and sharpness.

---

## Named Recipes

Convenience aliases that expand to specific primitive + params:

| Recipe Name | Expands To |
|---|---|
| `"diamond_field"` | `grid` with `shape: "diamond"`, `freq_x: 8`, `freq_y: 8` |
| `"expanding_ring"` | `rings` with `frequency: 5`, `contrast: 0.8` |
| `"conic_burst"` | `burst` with `ray_count: 12`, `sharpness: 0.7` |
| `"playful_scatter"` | `scatter_field` with `count: 30`, `shape: "diamond"`, `size: 0.04`, `blend: "max"` |

---

## Usage in script.json

```json
{
  "defaults": {
    "background_type": "gradient",
    "gradient_colors": ["#111117", "#211e29", "#3a2a4a"],
    "gradient_direction": "cross",
    "gradient_params": {
      "thickness": 2.0,
      "softness": 0.3
    }
  },
  "sections": [
    {
      "name": "Chorus",
      "lines": [0, 1],
      "visual": {
        "background_type": "gradient",
        "gradient_colors": ["#2d311a", "#2f3922", "#4a5a30"],
        "gradient_direction": "dual_spot_0.3_0.3_0.7_0.7",
        "gradient_params": {
          "blend": "additive",
          "softness": 1.2
        }
      }
    }
  ]
}
```

When no `gradient_direction` is specified or the string is empty, it defaults to `spot_field` with a single center spot (equivalent to `radial_center`).

---

## See Also

- `src/render/gradients.py` — All primitive implementations
- `src/render/renderer.py` — `_draw_gradient()` and `_draw_background()` call sites
- `docs/CANVAS_SCENE_SYSTEM.md` — System B for multi-object scene compositions
- `scripts/feature_explorer.py` — Reference list of tested gradient directions
