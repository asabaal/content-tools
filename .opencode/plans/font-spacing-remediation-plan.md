# Font-Spacing Remediation Plan

## Status: Awaiting Review (Read-Only Phase Complete)

## Finding Summary

### Verified Spacing Defects (5 font instances, 3 artifacts)

| Artifact | Section | Current Font | Issue | Fix |
|---|---|---|---|---|
| BLESSED (THE NAME) | Hook (×3) | Font 167 — Baloo Chettan 2 | "words overlapping" | F1: Swap → Candal (306) |
| BLESSED (THE NAME) | Interlude | Font 246 — Bitcount Single | needs more spacing | F2: Swap → Albert Sans (35) |
| BLESSED (THE NAME) | Pre-Hook 2 | Font 281 — Buda | "no good, select different" | F6: Swap → Cuprum (393) |
| MISCLASSIFIED | Intro | Font 10 — Aboreto | needs more spacing | F3: Swap → Arya (126) |
| MISCLASSIFIED | Verse 2 | Font 306 — Candal | needs more spacing | F4: Swap → Belanosima (191) |
| CULTURE CREATOR | Pre-Chorus | Font 143 — Autour One | needs more spacing | F5: Swap → Anek Bangla (83) |

### Root Cause
The renderer computes word spacing purely from font_size: `max(8, font_size * 0.08)` for unstyled or `font_size * 0.35` for styled (NEON) text. There is **no configurable word-spacing, letter-spacing, or line-height** per section. Display-category fonts with tight sidebearings produce visibly crowded text at these ratios.

## Execution Plan

### Batch 1 (immediate, via existing transform system)
Apply 6 `set_section_visual` transformations to swap fonts. Each uses `{font_family: <new_id>}` targeted by section type + artifact. All changes are journaled and reversible.

### Batch 2 (manual script.json edits)
Fix 4 line-split positions (BLESSED verse 2, MISCLASSIFIED intro, THE DEVIL'S PLAYBOOK post-hook/bridge) and apply uniform sizing to THE FIRST SCROLL.

### Batch 3 (new capability)
Implement `word_spacing` multiplier property (default 1.0) in the renderer's section visual model. This is the most impactful single improvement — it can fix all spacing defects without swapping fonts.

## Validation
Each fix requires: apply transform → re-render at affected timestamp → extract frame → compare with original → visual sign-off.

## Full Report
The complete HTML report with font inventory, pattern matrix, and transformation tables was generated as analysis output in the conversation.
