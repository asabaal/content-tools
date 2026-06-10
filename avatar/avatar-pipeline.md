# Asabaal Avatar Cutscene Pipeline

## Static Comics + Motion Comics Project Plan and Technical Specification

## 1. Project Purpose

The goal of this project is to create a reusable avatar-based visual content pipeline for producing static comics, visual-novel style panels, and upgraded motion-comic videos featuring a stylized character based on Asabaal.

The character is not intended to be a photorealistic copy of the real person. The goal is to create a recognizable, stylized, reusable self-avatar that can appear consistently across image and video content.

This pipeline supports:

* Static comic panels
* Visual-novel dialogue scenes
* Social-media image posts
* Motion-comic videos
* Game cutscene prototypes
* Reusable character assets for future animation workflows

The core production principle is:

> The avatar is a reusable identity system, not a one-off generated image.

## 2. Core Strategy

The pipeline will use a hybrid approach:

1. Create a canonical avatar design.
2. Use that avatar as the identity anchor.
3. Generate or compose static comic panels.
4. Use replacement, inpainting, and reference workflows to preserve identity.
5. Upgrade static panels into motion comics using camera movement, fades, dialogue timing, music, and effects.
6. Optionally use 3D later as a pose/composition scaffold, not as the first required milestone.

This avoids relying on the image model to perfectly regenerate the same character from prompt text alone.

## 3. Production Tiers

### Tier 1: Static Comic Panels

The first milestone is the ability to create consistent still images featuring the Asabaal avatar.

Output examples:

* Single-panel posts
* Multi-panel comic strips
* Visual novel stills
* Dialogue scenes
* Character reaction panels
* Story/lore panels

Primary output formats:

* PNG
* JPG
* WebP
* Optional PDF/contact-sheet exports later

### Tier 2: Motion Comics

The second milestone is turning static panels into lightly animated video content.

Motion-comic features:

* Slow zooms
* Camera pans
* Panel fades
* Dialogue text reveal
* Captions
* Music
* Voiceover
* Sound effects
* Parallax later if assets are separated into layers

Primary output formats:

* MP4 horizontal, 16:9
* MP4 vertical, 9:16
* Optional square, 1:1

### Tier 3: 3D-Assisted Avatar Control

The third milestone is optional but important for long-term consistency.

Possible uses:

* Generate a rough 3D version of the avatar
* Use a rigged mannequin or rough 3D character as a pose reference
* Render pose references in Blender
* Feed those pose references into the image pipeline
* Use the canonical avatar image to restore identity

This is not required for the first static comic system.

## 4. Avatar Identity System

The project should begin by defining a canonical avatar, not by generating random images.

The avatar should have a structured character profile.

### Character Profile Fields

```json
{
  "character_id": "asabaal_avatar",
  "display_name": "Asabaal",
  "character_type": "stylized_self_avatar",
  "likeness_target": "recognizable stylized avatar, not photoreal clone",
  "visual_identity": {
    "face": "",
    "hair": "",
    "body_proportions": "",
    "core_outfit": "",
    "color_palette": [],
    "accessories": [],
    "symbolic_motifs": []
  },
  "continuity_rules": {
    "must_keep": [],
    "may_vary": [],
    "must_not_change": []
  },
  "style_targets": {
    "primary_style": "",
    "secondary_styles": [],
    "forbidden_styles": []
  },
  "asset_paths": {
    "canonical_front": "",
    "canonical_face": "",
    "canonical_full_body": "",
    "character_sheet": "",
    "pose_references": [],
    "three_d_model": ""
  }
}
```

### Identity Anchors

The avatar should preserve:

* Face impression
* Hair shape/color
* Body silhouette
* Core outfit shape
* Color palette
* Signature accessory or symbol
* Overall emotional presence

The avatar may vary:

* Pose
* Expression
* Lighting
* Scene outfit details
* Background
* Camera angle
* Degree of stylization

The avatar should not drift into:

* A different person
* Random hairstyle changes
* Unexplained outfit replacements
* Changed body proportions
* Lost signature motifs
* Inconsistent face structure

## 5. Recommended Project Structure

Inside the existing local generation suite:

```text
/mnt/storage/ai_scripts/local_generation_suite/

characters/
  README.md
  scripts/
    create_character_project.py
    inspect_character_project.py
    generate_character_sheet.py
    replace_character_in_panel.py
  templates/
    character_profile.template.json
  projects/
    asabaal_avatar/
      character_profile.json
      references/
        canonical_front.png
        canonical_face.png
        canonical_full_body.png
        character_sheet.png
      prompts/
        identity.md
        outfit.md
        continuity_rules.md
        negative.md
      generated_images/
      masks/
      poses/
      three_d/
        raw/
        cleaned/
        rigged/
      cutscene_assets/

cutscenes/
  README.md
  scripts/
    create_cutscene_project.py
    assemble_static_comic.py
    assemble_visual_novel_scene.py
    assemble_motion_comic.py
    export_cutscene_assets.py
  templates/
    cutscene_scene.template.json
  projects/
  outputs/

three_d/
  README.md
  scripts/
    run_sf3d.py
    run_hunyuan3d.py
    inspect_3d_asset.py
  outputs/
```

## 6. Static Comic Workflow

### Step 1: Create Character Project

Command target:

```bash
python characters/scripts/create_character_project.py \
  --character-id asabaal_avatar \
  --display-name "Asabaal"
```

Expected output:

```text
characters/projects/asabaal_avatar/
  character_profile.json
  references/
  prompts/
  generated_images/
  masks/
  poses/
  three_d/
  cutscene_assets/
```

### Step 2: Create Canonical Avatar References

The user manually or semi-manually selects:

* Canonical face reference
* Canonical full-body reference
* Optional front/side/back character sheet
* Optional expression sheet

These become the identity anchors for future content.

### Step 3: Create Cutscene Project

Command target:

```bash
python cutscenes/scripts/create_cutscene_project.py \
  --cutscene-id first_avatar_scene \
  --title "First Avatar Scene"
```

Expected output:

```text
cutscenes/projects/first_avatar_scene/
  scene.json
  panels/
    raw/
    edited/
    final/
  masks/
  audio/
  exports/
```

### Step 4: Generate or Compose Raw Panels

Each panel begins as one of:

* Full scene generation
* Background generation + character placement
* Approximate character scene
* 3D/mannequin pose render
* Existing image/reference composition

The raw panel does not have to perfectly preserve identity.

### Step 5: Character Replacement / Correction

For each panel, use the canonical avatar references to correct the character.

Replacement modes:

1. Full body replacement
2. Face/head replacement
3. Outfit/detail correction
4. Hands/accessory correction
5. Symbol/motif correction

The continuity goal is not perfect one-shot generation. The goal is staged correction.

### Step 6: Export Static Comic

Supported outputs:

* Ordered panel PNGs
* Comic strip image
* Visual novel stills
* Social-media formatted versions

Example command target:

```bash
python cutscenes/scripts/assemble_static_comic.py \
  --scene cutscenes/projects/first_avatar_scene/scene.json \
  --output cutscenes/outputs/first_avatar_scene/static/
```

## 7. Motion Comic Workflow

Motion comics are created from finished static panels.

### Motion Features

Initial version:

* Fade in/out
* Pan
* Zoom
* Hold duration
* Text overlay
* Dialogue box
* Captions
* Background music
* Voiceover track

Later version:

* Layered parallax
* Particle overlays
* Animated glows
* Camera shake
* Letterboxing
* Subtitle timing
* Character blink or mouth movement experiments

### Motion Scene Spec

```json
{
  "cutscene_id": "first_avatar_scene",
  "title": "First Avatar Scene",
  "format": "vertical",
  "resolution": {
    "width": 1080,
    "height": 1920
  },
  "fps": 30,
  "shots": [
    {
      "shot_id": "001",
      "panel_path": "panels/final/001.png",
      "duration_seconds": 4,
      "camera_motion": {
        "type": "slow_zoom_in",
        "start_scale": 1.0,
        "end_scale": 1.12
      },
      "caption": "The signal appeared before I understood it.",
      "dialogue": [],
      "audio": null
    }
  ]
}
```

### Motion Comic Assembly Command

```bash
python cutscenes/scripts/assemble_motion_comic.py \
  --scene cutscenes/projects/first_avatar_scene/scene.json \
  --format vertical \
  --output cutscenes/outputs/first_avatar_scene/video/first_avatar_scene_vertical.mp4
```

## 8. 3D-Assisted Workflow

The 3D workflow is a support layer, not the first dependency.

Possible 3D roles:

* Pose reference
* Lighting reference
* Camera angle reference
* Silhouette consistency
* Future rigged avatar
* Future animation asset

The 3D model does not need to be perfect at first.

### 3D-Assisted Panel Workflow

```text
canonical avatar image
→ rough 3D character or mannequin pose
→ rendered pose reference
→ image generation / inpainting
→ final comic panel
```

If the generated 3D model is accurate:

```text
3D avatar → rig → pose → render → final or near-final panel
```

If the generated 3D model is not accurate:

```text
3D avatar/mannequin → pose scaffold → image model redraws avatar using canonical reference
```

## 9. Minimum Viable Product

The MVP does not require full animation or perfect 3D.

### MVP Requirements

The system can:

1. Create an avatar character project.
2. Store canonical avatar references.
3. Create a cutscene project.
4. Store raw and final panels.
5. Assemble ordered static panels.
6. Export a simple comic strip or visual novel sequence.
7. Create a basic motion comic MP4 using pan/zoom/fade.

### MVP Non-Requirements

The MVP does not need:

* Full 3D rigging
* Perfect text-to-3D
* Lip sync
* Facial animation
* Fully animated walking/talking characters
* Real-time game-engine integration
* Perfect character consistency in one generation pass

## 10. Development Milestones

### Milestone 1: Project Scaffolding

Deliverables:

* `characters/` module
* `cutscenes/` module
* character project creator
* cutscene project creator
* JSON templates
* README files

Success condition:

A new avatar project and cutscene project can be created from CLI commands.

### Milestone 2: Static Panel Organization

Deliverables:

* panel folder conventions
* scene JSON format
* static comic assembler
* visual novel still exporter

Success condition:

A folder of finished panels can be exported into an ordered comic strip or scene package.

### Milestone 3: Avatar Continuity Metadata

Deliverables:

* character profile schema
* continuity rules
* prompt fragments
* reference image registry

Success condition:

Each generated panel can reference the canonical avatar identity and continuity rules.

### Milestone 4: Motion Comic Assembly

Deliverables:

* simple video assembler
* pan/zoom/fade support
* caption/dialogue overlay support
* horizontal and vertical exports

Success condition:

A static cutscene can be rendered as an MP4 motion comic.

### Milestone 5: Character Replacement Workflow

Deliverables:

* mask folder conventions
* replacement script stub
* integration with local image/inpainting workflow
* before/after panel tracking

Success condition:

A raw panel with an approximate character can be corrected into a final panel using canonical avatar references.

### Milestone 6: 3D Pose Reference Integration

Deliverables:

* optional 3D asset inspection
* rough 3D model storage
* pose reference folder
* Blender render integration later

Success condition:

A posed 3D/mannequin render can be used as a reference asset for a cutscene panel.

## 11. Coding Agent Implementation Prompt

Implement the first version of the Asabaal Avatar Cutscene Pipeline inside the existing local generation suite.

Project root:

```text
/mnt/storage/ai_scripts/local_generation_suite
```

Use the existing active environment:

```text
(local_gen_suite)
```

Hardware assumption:

```text
NVIDIA 16 GB GPU, CUDA
```

Local model storage convention:

```text
/mnt/storage/models
```

Relative to project root:

```text
../../models
```

Do not put model weights inside the project tree.

Create the following modules:

```text
characters/
cutscenes/
```

Do not implement image generation yet unless there are already established image-generation scripts in the suite that can be safely reused. The first task is project structure, metadata, panel organization, and assembly.

Create:

```text
characters/scripts/create_character_project.py
characters/scripts/inspect_character_project.py
characters/templates/character_profile.template.json
characters/README.md

cutscenes/scripts/create_cutscene_project.py
cutscenes/scripts/assemble_static_comic.py
cutscenes/scripts/assemble_motion_comic.py
cutscenes/templates/cutscene_scene.template.json
cutscenes/README.md
```

`create_character_project.py` should create:

```text
characters/projects/<character_id>/
  character_profile.json
  references/
  prompts/
  generated_images/
  masks/
  poses/
  three_d/
    raw/
    cleaned/
    rigged/
  cutscene_assets/
```

`create_cutscene_project.py` should create:

```text
cutscenes/projects/<cutscene_id>/
  scene.json
  panels/
    raw/
    edited/
    final/
  masks/
  audio/
  exports/
```

`assemble_static_comic.py` should take ordered final panel images and create a single comic-strip PNG or a copied ordered export folder.

`assemble_motion_comic.py` should take ordered final panel images and create a simple MP4 using hold durations, fade transitions, and optional slow zoom/pan.

Use Python libraries already present where possible. If new dependencies are needed, prefer lightweight common packages such as Pillow and moviepy, but inspect the existing environment first and do not break existing image/audio/video/llm workflows.

Do not reinstall torch.

Add documentation explaining that the purpose of the pipeline is to create a reusable stylized avatar of Asabaal for static comics and motion comics, with possible later 3D pose-reference integration.

The system should treat the avatar as a continuity-managed character project, not as a single image.

````

## 12. First Practical Output Target

The first real test should be:

```text
A 4-panel static comic featuring the Asabaal avatar.
````

Then:

```text
The same 4 panels exported as a 20-second vertical motion comic.
```

This proves the pipeline can produce both image content and video content from the same cutscene project.

## 13. Long-Term Vision

The long-term system becomes a local avatar production studio:

```text
self-avatar
→ static panels
→ visual novel scenes
→ motion comics
→ 3D pose references
→ game cutscene prototypes
→ eventually full animation
```

The core value is reusable identity, not one-off generation.
