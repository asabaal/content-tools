"""Ontology → calibration-family routing (addendum §4).

Three canonical reference pieces:
  pitched_harmonic  — 4:00 (piano/synth conditioning candidates)
  percussion_timing — 2:00 (neutral click conditioning)
  vocal_timing      — 2:00 (neutral non-lexical ah/vox conditioning)

Every documented Suno target routes to a PRIMARY family; some targets
(pitched percussion like bells/glockenspiel/celesta, vocoder) legitimately
participate in more than one family and carry an explicit multi-family
mapping rather than a forced single category.
"""
from __future__ import annotations

from dataclasses import dataclass

PITCHED = "pitched_harmonic"
PERCUSSION = "percussion_timing"
VOCAL = "vocal_timing"

CATEGORY_PRIMARY: dict[str, str] = {
    "percussion": PERCUSSION,
    "vocal": VOCAL,
    "bass": PITCHED,
    "keyboard": PITCHED,
    "guitar": PITCHED,
    "strings": PITCHED,
    "brass": PITCHED,
    "woodwind": PITCHED,
    "synth": PITCHED,
    "other": PITCHED,
}

# Explicit secondary families for genuinely multi-family targets.
MULTI_FAMILY: dict[str, list[str]] = {
    # pitched percussion also serves the pitched/harmonic reference
    "bells": [PERCUSSION, PITCHED],
    "glockenspiel": [PERCUSSION, PITCHED],
    "celesta": [PERCUSSION, PITCHED],
    "timpani": [PERCUSSION, PITCHED],
    # vocoder is a voice target but realizes pitched material
    "vocoder": [VOCAL, PITCHED],
}


@dataclass(frozen=True)
class FamilyRouting:
    primary: str
    all_families: tuple[str, ...]

    @property
    def multi(self) -> bool:
        return len(self.all_families) > 1


def route(target_id: str, category: str) -> FamilyRouting:
    primary = CATEGORY_PRIMARY.get(category, PITCHED)
    if target_id in MULTI_FAMILY:
        fams = tuple(MULTI_FAMILY[target_id])
        return FamilyRouting(primary=fams[0], all_families=fams)
    return FamilyRouting(primary=primary, all_families=(primary,))


FAMILY_META: dict[str, dict] = {
    PITCHED: {
        "label": "Pitched / Harmonic Reference",
        "duration_seconds": 240.0,
        "conditioning": [
            {"candidate": "multimodal_v2", "leading": True,
             "path": "canonical_reference_piece_multimodal_v2_input.wav",
             "schedule": "multimodal_v2_conditioning_map.json",
             "note": "4 genuinely distinct rendering pipelines: SF2 "
                     "wavetable / additive / Karplus-Strong / formant vox"},
            {"candidate": "multimodal_v1", "leading": False,
             "status": "SUPERSEDED — MULTI-TIMBRAL GM TEST, NOT CANONICAL "
                       "MULTIMODAL INPUT",
             "path": "canonical_reference_piece_multimodal_input.wav",
             "schedule": "multimodal_conditioning_map.json"},
            {"candidate": "neutral_piano",
             "path": "canonical_reference_piece_piano_input.wav"},
            {"candidate": "neutral_synth",
             "path": "canonical_reference_piece_synth_input.wav"},
        ],
    },
    PERCUSSION: {
        "label": "Percussion Timing Reference",
        "duration_seconds": 120.0,
        "conditioning": [
            {"candidate": "neutral_click",
             "path": "percussion_timing_reference_click_input.wav"},
        ],
    },
    VOCAL: {
        "label": "Vocal Timing Reference",
        "duration_seconds": 120.0,
        "conditioning": [
            {"candidate": "neutral_ah_vox",
             "path": "vocal_timing_reference_vox_input.wav"},
        ],
    },
}
