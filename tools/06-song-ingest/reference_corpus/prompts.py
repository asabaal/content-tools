"""Suno Rendering Prompt Book generation.

For every documented Suno Advanced Split target, build:
  🟣 MAIN / DEFAULT prompt — realize the canonical composition with the
     target timbre dominant
  🛑 EXCLUDE / AVOID prompt — suppress confusable instruments and drift

Deterministic. Every prompt is length-controlled into the hard 900–1000
character range (see checker.py) using SPECIFIC musical control directives
from a curated pool — never meaningless filler. The checker re-validates
every final prompt; anything outside the range raises.
"""
from __future__ import annotations

import re

from .checker import MAX_CHARS, MIN_CHARS, check_prompt

# Compressed one-piece identity: the same for every target.
def pitched_identity(mmap: dict) -> str:
    """Map-driven identity for the pitched/harmonic reference.

    Duration, bar count, movement count and movement names are read from
    the generated movement_map.json — never hardcoded here."""
    n = len(mmap["sections"])
    word = {9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}.get(n, str(n))
    dur = mmap["duration_seconds"]
    dur_str = f"{int(dur // 60)}:{int(dur % 60):02d}"
    names = []
    for s_sec in mmap["sections"]:
        # strip roman-numeral prefix and any parenthetical/detail tail
        t = re.sub(r"^[IVX]+\.?\s*", "", s_sec["title"])
        t = t.split("—")[0].strip().rstrip(".")
        names.append(t)
    return (f"Realize 'The Steward's Calibration': {dur_str} instrumental "
            f"reference, {mmap['tempo_bpm']} BPM, 4/4, "
            f"{mmap['total_bars']} bars, {word} movements in strict order: "
            + "; ".join(names) + ".")


INVARIANTS = (
    "Keep movement order, tempo, harmony, contours and all calibration "
    "passages intact; the requested instrument stays dominant; no drift.")

SHORT_INVARIANTS = ("No drift; every calibration passage stays intact; the "
                    "requested instrument is dominant.")



# ---- calibration-family identity blocks --------------------------------------
# Pitched family uses IDENTITY above (the 4:00 nine-movement piece).

PERCUSSION_IDENTITY = (
    "Perform 'Percussion Timing Reference': 2:00 timing probe on a neutral "
    "click transient (no drum-kit styling), 120 BPM, eleven regions in "
    "order. I Pulse 4/4 ostinato, downbeat accents. II Subdivisions: "
    "eighths, sixteenths, triplets, dotted eighths. III Accents, isolated "
    "hits, silence windows, crescendo then decrescendo. IV 3+3+2 "
    "syncopation, offbeats. V Simultaneous three-lane stacks, staggered "
    "sixteenth rolls. VI Quintuplet runs, burst fills. VII "
    "Call-and-response, sparse to dense. VIII 3/4. IX 6/8 (2+2+2, 3+3). X "
    "5/8 (3+2, 2+3). XI 7/8 (2+2+3, 3+2+2). Lanes differ by pitch only.")

PERCUSSION_REALIZATION = (
    "Percussion timing feature: place every onset exactly where the score "
    "places it, keep subdivisions even, accents clearly louder, silence "
    "windows silent, simultaneous hits exactly together, staggered rolls "
    "evenly spaced, and hold 120 BPM with no drift across any meter change.")

VOCAL_IDENTITY = (
    "Sing 'Vocal Timing Reference': 2:00 non-lexical vocal timing probe "
    "('ah' only, no words), 120 BPM, eleven regions in order. I "
    "repeated-pitch pulses. II staccato, sustained vowels, legato phrases, "
    "dotted rhythms, tie across a barline. III ascending, descending, arch "
    "and repeated contours with leaps. IV low/mid/high registers with "
    "breaths. V syncopated, offbeat and pickup entries. VI triplet and "
    "quintuplet melisma, dotted phrases. VII one-to-four-part stacks, "
    "staggered backings, call-and-response. VIII 3/4. IX 6/8. X 5/8 (3+2, "
    "2+3). XI 7/8 (2+2+3, 3+2+2).")

VOCAL_REALIZATION = (
    "Vocal timing feature: every onset and offset lands exactly on the "
    "score position; staccato short, sustains full length, legato "
    "connected; breaths only in written rests; 120 BPM steady through every "
    "meter change; the vowel never becomes a word.")

# Category-specific realization guidance for the MAIN prompt.
CATEGORY_REALIZATION: dict[str, str] = {
    "vocal": (
        "Vocal feature: sing the lead melody throughout, deliver movement "
        "VIII's motif as sustained legato 'ah' lines, layer movement V "
        "chords as 'ooh' pads, and render the percussion movement as vocal "
        "percussion."),
    "percussion": (
        "Percussion feature: perform movement VIII's syncopated groove as "
        "the continuous backbone, map every movement's chord rhythm to "
        "articulated hits, render movement III runs as tonal strikes and "
        "the solos as fill figures."),
    "bass": (
        "Bass feature: carry every harmony as bass lines, feature movement "
        "VII's walking bass, octave pops and low pedal, keep the finale "
        "bass prominent, stay low with the melody hinted above."),
    "keyboard": (
        "Keyboard feature: block chords and arpeggios in harmony movements, "
        "clean single-note runs for scales and interval studies, "
        "counterpoint split between hands, sustain pedal only where the "
        "score marks legato."),
    "guitar": (
        "Guitar feature: strummed or picked chord realizations of the "
        "harmony movements, single-note scale and solo runs with bends only "
        "where the harmony allows, dual-voice flatpicking for "
        "counterpoint, low-string work for the walking-bass movement."),
    "strings": (
        "Strings feature: bowed sustained chords in harmony movements, "
        "legato single-line scales and solos, pizzicato for staccato and "
        "percussion movements, rich contrapuntal double-stops in movement "
        "V."),
    "brass": (
        "Brass feature: bold chorale chords in harmony movements, "
        "fanfare-style phrasing of scales and intervals, marcato staccato "
        "attacks, smooth controlled legato solos."),
    "woodwind": (
        "Woodwind feature: fluid single-line scales and solos with breath "
        "phrasing, gently articulated chord stabs in harmony movements, "
        "airy register sweeps, light tonguing on staccato material."),
    "synth": (
        "Synthesizer feature: pads or keys for harmony movements per their "
        "character, sharp monophonic leads for scales and solos, sequenced "
        "bass for movement VII, tempo-locked arpeggiator only where the "
        "score notates arpeggios."),
    "other": (
        "Render with the requested instrument as the sole melodic and "
        "harmonic voice: follow the movement map exactly, translate chord "
        "passages into idiomatic voicing, keep every calibration passage "
        "audible."),
}

CATEGORY_REALIZATION_SHORT: dict[str, str] = {
    "vocal": "Sing the lead melody throughout; 'ah' lines for movement VIII; "
             "vocal percussion there too.",
    "percussion": "Rhythmic backbone from movement VIII's groove; map chord "
                  "rhythms to articulated hits across all movements.",
    "bass": "All harmony as bass lines; feature walking bass, octave pops "
            "and the low pedal; stay low.",
    "keyboard": "Block chords/arpeggios for harmony; clean runs for scales; "
                "counterpoint split between hands.",
    "guitar": "Strummed/picked chords for harmony; single-note runs for "
              "scales and solos; dual-voice counterpoint.",
    "strings": "Bowed chords for harmony; legato runs; pizzicato for "
               "staccato; double-stop counterpoint.",
    "brass": "Chorale chords for harmony; fanfare scales; marcato staccato; "
             "smooth legato solos.",
    "woodwind": "Fluid single-line scales and solos; light chord stabs; "
                "airy sweeps; gentle tonguing.",
    "synth": "Pads/keys for harmony; mono leads for scales and solos; "
             "sequenced bass; arpeggiator only where notated.",
    "other": "Requested instrument as the sole melodic and harmonic voice, "
             "following the movement map exactly.",
}

# Specific, musical control directives used to reach the length floor.
DIRECTIVE_POOL: dict[str, list[str]] = {
    "main": [
        "III must contain the full chromatic run and clean 2nd-through-octave "
        "interval pairs ascending and descending.",
        "IV must state ii-V-I in C then F, the I-V-vi-IV and vi-IV-I-V loops "
        "in G, and the A blues over dominant sevenths.",
        "V must keep both counterpoint voices independently audible, plus "
        "dyads, dense five-note voicings, open-fifth sparse voicings, "
        "suspended chords and inverted staccato chords.",
        "IX must climb C to D and land the dense final E-minor cadence at "
        "full length.",
        "Balance: the requested instrument stays clearly in front of any "
        "supporting texture at all times.",
        "Articulation: legato passages connect, staccato passages stay short "
        "and separate, repeated notes are clearly re-attacked.",
        "Registers: keep the low-register bars below middle C and the sweep "
        "to the practical top; do not octave-shift calibration passages.",
        "Timing: hold 100 BPM steady with no ritardando between movements.",
        "Dynamics: keep the two solos expressive but intimate; save the full "
        "dynamic range for the finale climax.",
        "Tone: one continuous instrument color from bar one of movement I to "
        "the final chord.",
        "Clarity: every scale degree and interval step stays distinct; no "
        "wash of reverb over the calibration runs.",
        "VI: the lyrical solo stays intimate over sparse accompaniment; the "
        "virtuoso solo keeps its arpeggios and final high sustained note.",
    ],
    "exclude": [
        "No drum fills or cymbal crashes masking the calibration passages.",
        "No improvised melodies replacing the written ones.",
        "No key changes beyond the notated C-D-E finale journey.",
        "No distortion, tape stops, reversed audio or sweeps that alter the "
        "notation.",
        "No octave doublings that defeat the register tests.",
        "No shuffle or quantization of the even eighth notes outside the "
        "blues movement.",
        "No early fade of the final cadence; let it ring to full length.",
        "No inserted transitions, breakdowns or drops between movements.",
        "No thinning of the dense finale voicings into single lines.",
        "No rushing the scale runs beyond their notated even rhythm.",
        "No background instruments answering the solos; the solos stay "
        "solo.",
    ],
}

EXTRA_EXCLUSIONS: dict[str, list[str]] = {
    "piano": ["electric piano", "harpsichord"],
    "organ": ["electric piano", "accordion"],
    "guitar": ["ukulele", "mandolin", "banjo"],
    "electric_guitar": ["acoustic guitar", "synth lead"],
    "acoustic_guitar": ["electric guitar", "ukulele"],
    "strings": ["synth strings", "orchestra"],
    "synth_pad": ["organ", "strings"],
    "bass": ["synth bass", "eight zero eight"],
    "drums": ["percussion"],
    "lead_vocal": ["choir", "vocoder"],
    "choir": ["lead vocal", "synth pad"],
}


def _confusables(target, all_targets: dict) -> list[str]:
    names = []
    for other in all_targets.values():
        if other.target_id != target.target_id \
                and other.category == target.category:
            names.append(other.name)
    for extra in EXTRA_EXCLUSIONS.get(target.target_id, []):
        if extra not in names:
            names.append(extra)
    return names


def _assemble(blocks: list[str], pool: list[str], *, target_id: str,
              field: str) -> str:
    """Join blocks, then append directives until the prompt is inside
    [MIN_CHARS, MAX_CHARS]. Deterministic; raises if it cannot comply."""
    text = " ".join(b for b in blocks if b)
    i = 0
    while len(text) < MIN_CHARS:
        if i >= len(pool) * 3:
            raise ValueError(f"{target_id}/{field}: directive pool exhausted "
                             f"at {len(text)} chars")
        d = pool[i % len(pool)]
        suffix = "" if i < len(pool) else f" (also apply in every movement)"
        i += 1
        candidate = f"{text} {d}{suffix}"
        if len(candidate) > MAX_CHARS:
            continue
        text = candidate
    if len(text) > MAX_CHARS:
        raise ValueError(f"{target_id}/{field}: base text exceeds "
                         f"{MAX_CHARS} chars ({len(text)}); shorten composer "
                         f"blocks")
    check = check_prompt(text, target_id, field)
    if not check.ok:
        raise ValueError(f"{target_id}/{field}: {check.problems}")
    return text


def build_main(target, identity: str, *,
               family: str = "pitched_harmonic") -> str:
    if family == "percussion_timing":
        blocks = [f"TARGET INSTRUMENT: {target.name}.", identity,
                  PERCUSSION_REALIZATION, INVARIANTS]
    elif family == "vocal_timing":
        blocks = [f"TARGET VOICE: {target.name}.", identity,
                  VOCAL_REALIZATION, INVARIANTS]
    else:
        realization = CATEGORY_REALIZATION.get(
            target.category, CATEGORY_REALIZATION["other"])
        extra = (f" ({target.description})"
                 if target.description
                 and target.description not in target.name else "")
        blocks = [
            f"TARGET INSTRUMENT: {target.name}{extra}.",
            identity,
            realization,
            INVARIANTS,
        ]
    try:
        return _assemble(blocks, DIRECTIVE_POOL["main"],
                         target_id=target.target_id, field="MAIN")
    except ValueError:
        if family != "pitched_harmonic":
            blocks = [b for b in blocks]
            blocks[2] = (PERCUSSION_REALIZATION if family == "percussion_timing"
                         else VOCAL_REALIZATION)
        else:
            blocks = [
                f"TARGET INSTRUMENT: {target.name}{extra}.",
                identity,
                CATEGORY_REALIZATION_SHORT.get(
                    target.category, CATEGORY_REALIZATION_SHORT["other"]),
                SHORT_INVARIANTS,
            ]
        return _assemble(blocks, DIRECTIVE_POOL["main"],
                         target_id=target.target_id, field="MAIN")


def build_exclude(target, all_targets: dict, *,
                  family: str = "pitched_harmonic") -> str:
    confusables = ", ".join(_confusables(target, all_targets)[:8])
    if family == "percussion_timing":
        blocks = [
            f"EXCLUDE for the {target.name} render of 'Percussion Timing "
            f"Reference'.",
            "No realistic drum-kit styling that turns the neutral click into "
            "a kick, snare, hi-hat, conga or cymbal identity; no pitched "
            "melodic material, no lyrics, no vocals.",
            f"Avoid nearby percussion targets dominating: {confusables}.",
            "No groove reinterpretation, ghost-note restyling, tempo drift, "
            "meter re-grouping or simplification of the subdivision, "
            "tuplet, accent and asymmetric-meter calibration passages.",
            "No added reverb tails, room sound or samples that blur onset "
            "timing.",
        ]
    elif family == "vocal_timing":
        blocks = [
            f"EXCLUDE for the {target.name} render of 'Vocal Timing "
            f"Reference'.",
            "No lexical lyrics or words — the non-lexical 'ah' vowel only; "
            "no spoken passages.",
            f"Avoid other voice types taking the lead, especially: "
            f"{confusables}.",
            "No vibrato so heavy that onsets and offsets blur; no pitch "
            "correction artifacts, formant shifts or doubles that move the "
            "written timing; no melisma replacing notated single notes.",
            "No arrangement drift: no added ad-libs, no tempo drift, no "
            "meter re-grouping, no simplification of the contour, register, "
            "stagger and asymmetric-meter passages.",
        ]
    else:
        no_vocals = ("" if target.category == "vocal" else
                     "No sung vocals, lyrics or humming. ")
        no_drums = ("" if target.category == "percussion" else
                    "No drum kit beyond what the score notates. ")
        acoustic = ("No synthesized imitation of this acoustic instrument. "
                    if target.category in ("strings", "brass", "woodwind",
                                           "keyboard", "bass", "other")
                    else "")
        blocks = [
            f"EXCLUDE for the {target.name} render of 'The Steward's "
            f"Calibration'.",
            "No choir or vocal 'ah' pads, no semantic drum-kit percussion, "
            "and no cinematic FX styling anywhere — the transitional/"
            "rhythmic movement is played on the target instrument itself.",
            f"No other instrument takes the lead — especially {confusables}.",
            no_vocals + no_drums + acoustic,
            "No genre transformation away from the neutral reference "
            "arrangement.",
            "No arrangement drift: no added countermelodies, re-harmony, "
            "tempo change, movement reordering, or simplification of "
            "calibration passages.",
        ]
    return _assemble(blocks, DIRECTIVE_POOL["exclude"],
                     target_id=target.target_id, field="EXCLUDE")


