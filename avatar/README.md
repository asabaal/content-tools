# 3D Asset Visualization Tool

Standalone tool for loading, inspecting, and rendering preview images of 3D asset files using Blender in background mode.

## What This Tool Does

This tool loads any 3D asset file you point it at and produces:

- Rendered preview images from multiple angles
- A contact sheet combining all views
- An inspection report (`asset_report.json`) with geometry, material, and texture details
- Optionally, an imported `.blend` file you can open in Blender
- Optionally, a 360-degree turntable render

**This tool is standalone.** It does not depend on, import from, or integrate with any project that produced the asset. It simply loads a file from whatever path you provide.

### Note on `.glb` Files

A `.glb` file is a 3D asset (Binary glTF), not a Blender `.blend` project. This tool imports `.glb` files into Blender, renders previews, and optionally saves the result as a `.blend` file you can open and edit.

## Supported Formats

| Format | Extension |
|--------|-----------|
| Binary glTF | `.glb` |
| glTF | `.gltf` |
| Wavefront OBJ | `.obj` |
| Autodesk FBX | `.fbx` |
| Blender | `.blend` |

## Requirements

- Blender 4.0+ (tested with Blender 5.0.1)
- Python Pillow (optional, for contact sheet generation)

## Usage

### Render Preview Images

```bash
blender --background --python scripts/render_asset_preview.py -- \
  --asset /absolute/path/to/asset.glb \
  --output-dir outputs/my_preview \
  --material-mode clay \
  --save-blend
```

Using a relative path from the project root:

```bash
blender --background --python scripts/render_asset_preview.py -- \
  --asset examples/sample.glb \
  --output-dir outputs/sample_preview \
  --material-mode clay
```

### Inspect an Asset (No Rendering)

```bash
blender --background --python scripts/inspect_3d_asset.py -- \
  --asset /path/to/asset.glb
```

With JSON output:

```bash
blender --background --python scripts/inspect_3d_asset.py -- \
  --asset /path/to/asset.glb \
  --output-json outputs/inspection.json
```

## CLI Arguments (render_asset_preview.py)

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--asset` | Yes | - | Path to `.glb`, `.gltf`, `.obj`, `.fbx`, or `.blend` |
| `--output-dir` | No | `outputs/<name>_<timestamp>` | Output directory |
| `--material-mode` | No | `original` | `original`, `clay`, `normal`, or `wireframe` |
| `--resolution` | No | `1024` | Render resolution in pixels |
| `--engine` | No | `eevee` | `eevee` or `cycles` |
| `--transparent` | No | - | Render with transparent background |
| `--save-blend` | No | - | Save imported scene as `imported_asset.blend` |
| `--turntable` | No | - | Create a 36-frame turntable render |
| `--views` | No | `front,side,back,three_quarter,top` | Comma-separated view list |

## Material Modes

- **`original`**: Preserve imported materials as-is.
- **`clay`**: Replace all materials with a neutral matte gray. Useful when textures are missing or broken.
- **`normal`**: Attempt a diagnostic normal-style material. Falls back to clay if not practical.
- **`wireframe`**: Attempt a wireframe render via Freestyle. Falls back to clay if not practical.

## Missing Material/Texture Warnings

If the tool detects geometry but no texture images or meaningful material textures, it prints:

```
WARNING: Asset appears to have geometry but no texture images/material textures.
```

This is common with AI-generated 3D assets where geometry is produced but textures are stored separately or not included. Use `--material-mode clay` to get a clean preview regardless of texture availability.

## Path Resolution Rules

- Absolute paths are used directly.
- Relative paths are resolved relative to the current working directory (project root).
- No project-specific path logic is applied.

## Output Files

After running, the output directory contains:

| File | Description |
|------|-------------|
| `front.png` | Front view render |
| `side.png` | Side view render |
| `back.png` | Back view render |
| `three_quarter.png` | Three-quarter perspective render |
| `top.png` | Top-down view render |
| `contact_sheet.png` | All views combined (requires Pillow) |
| `imported_asset.blend` | Blender file (only with `--save-blend`) |
| `asset_report.json` | Detailed inspection report |
| `turntable/` | 36 PNG frames (only with `--turntable`) |

## asset_report.json Fields

```json
{
  "input_asset_path": "original CLI argument",
  "resolved_asset_path": "absolute resolved path",
  "file_extension": ".glb",
  "file_size_bytes": 258296,
  "file_size_human": "252.2 KB",
  "mesh_object_count": 1,
  "material_count": 2,
  "texture_image_count": 1,
  "vertex_count": 5000,
  "face_polygon_count": 4800,
  "bounding_box_dimensions": {"x": 1.0, "y": 1.0, "z": 1.0},
  "has_armature": false,
  "has_animations": false,
  "material_names": ["Material"],
  "image_names": ["texture.png"],
  "rendered_views": {"front": "front.png", "side": "side.png"},
  "saved_blend_path": "outputs/preview/imported_asset.blend",
  "warnings": []
}
```

## Project Structure

```
avatar/
  README.md
  scripts/
    render_asset_preview.py
    inspect_3d_asset.py
  outputs/
  examples/
```
