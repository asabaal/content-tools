# Static-Background Investigation — Slate-Only Remediation Pass

Status: Investigation complete. Cause confirmed. Low-risk system-level fix
recommended (not yet applied this pass per scope; see below).

## affected projects / sections

Observed during review of the Slate-only renders (the 7 songs:
asabaal, blessed-the-name, misclassified, the-first-scroll, culture-creator,
the-devil-s-playbook, covenant-keeping-god).

- the-first-scroll: 1 section explicitly carries `bg_animation_preset: "minimal"`
  → fully static background while lyrics are on screen.
- asabaal previously had 2 `minimal` sections; these were switched to `smooth`
  during this pass, so they now move.
- Any other section whose resolved preset lands on `minimal` (see cause below)
  will also render static.

## observed background behavior

Background is completely frozen (no pan, no zoom, no particle, no color drift,
no audio reactivity) for the full duration of the affected section, even while
lyric text is animating on top of it. Other sections in the same video move
normally, so the issue is section-localised, not project-wide.

## common configuration patterns

Across the slate scripts the populated presets are:
`smooth, cinematic, energetic, dreamy` (all of which move) plus `minimal`
(which does not). The static cases correlate 1:1 with the `minimal` preset and
with sections that resolve to `minimal` via fallback.

## likely cause

Two pre-existing systemic issues, both pointing at the `minimal` preset:

1. `minimal` is defined as a no-op:
   `effect_presets.py:71-75` — `effects=[]`, `audio_reactivity=[]`.
   Any section that selects `minimal` gets zero motion by construction.

2. `minimal` is the universal silent fallback:
   - `get_preset()` (`effect_presets.py:153`) returns `PRESETS["minimal"]`
     for any unrecognised preset name, so a typo'd/legacy name degrades to
     static with no warning.
   - `get_preset_for_section()` (`effect_presets.py:160`) falls back to
     `"minimal"` for any section type not in `PRESET_BY_SECTION`
     (which only covers intro/verse/chorus/hook/bridge/pre_chorus/outro).
     Exotic types (interlude, spoken, rap, pre_hook, post_hook, etc.) therefore
     resolve to static.

A third, already-fixed contributor: when a section had no `bg_animation_preset`
at all, the renderer used to return the frame unmodified (static). The fallback
added this pass at `renderer.py:438-443` now derives a preset from the nearest
section's type, which resolves most of those gaps — but it still funnels
through `get_preset_for_section`, so exotic section types can still land on
`minimal`/static.

## confirmed cause

Yes. `minimal` is an empty no-op preset and is the default fallback for both
unknown preset names and unknown section types. Selecting it (directly or via
fallback) yields a static background.

## recommended fix options

1. (System-level, preferred, low-risk) Give `minimal` real but subtle motion so
   it is never literally static — e.g. a slow ken_burns + faint color_drift,
   matching the calm intent without freezing. One change in `effect_presets.py`
   fixes every direct and fallback path at once.

2. (System-level, low-risk) Change the two fallback defaults from `"minimal"` to
   `"smooth"` in `get_preset` / `get_preset_for_section`, so unknown names/types
   get gentle motion instead of none. Keep `minimal` available only as an
   explicit, documented "intentionally still" choice.

3. (System-level, medium-risk) Add audio reactivity (`["energy"]`) to `minimal`
   so even a "calm" section breathes with the track.

4. (Script-level, not recommended) Sweep every slate script to remove/replace
   `minimal`. High effort, must be repeated for every future script, and does
   not address the fallback paths.

## estimated scope / risk of each fix

- Option 1: ~5 lines in one file. Risk: very low — only affects sections
  currently rendering static, which is the desired change. Visual delta is
  subtle.
- Option 2: ~2 lines. Risk: low — changes the fallback only; explicit preset
  selections unchanged.
- Option 3: ~1 line. Risk: low, but motion depends on audio energy being
  available.
- Option 4: per-script edits across N songs. Risk: low but effort scales with
  catalogue size and is fragile against new scripts.

## system-level vs script-level

System-level (Option 1 and/or 2) is strongly preferable. The root cause lives
in the preset definition and its fallback defaults, not in the song scripts.
A single `effect_presets.py` change fixes all current and future slate videos
without per-script churn.

## constraint note

Per the remediation pass scope, no broad static-background fix was implemented
this pass. The renderer-side fallback for missing `bg_animation_preset`
(`renderer.py:438-443`) was the only related change applied, and it is
behaviour-preserving for sections that already specify a preset. Implementing
Option 1 or 2 above is recommended as a small follow-up.
