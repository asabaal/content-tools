from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


def _srgb_to_linear(c: int) -> float:
    c = c / 255.0
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: #{hex_color}")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return 0.2126 * _srgb_to_linear(r) + 0.7152 * _srgb_to_linear(g) + 0.0722 * _srgb_to_linear(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    l1 = relative_luminance(hex1)
    l2 = relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def wcag_level(ratio: float, large_text: bool = False) -> str:
    if large_text:
        if ratio >= 4.5:
            return "AAA"
        if ratio >= 3.0:
            return "AA"
        return "fail"
    if ratio >= 7.0:
        return "AAA"
    if ratio >= 4.5:
        return "AA"
    return "fail"


_COMPLEX_DIRECTIONS = frozenset({
    "conic", "spiral", "burst", "scatter_field", "grid",
    "rings", "diamond", "bands",
})

_COMPLEX_PRESETS = frozenset({
    "energetic", "psychedelic", "intense",
})

_TEXTURE_BUSY = frozenset({
    "noise_grain", "grain_film", "noise_fine", "noise_coarse",
})


def estimate_busyness(visual: dict) -> str:
    score = 0
    direction = visual.get("gradient_direction", "")
    if any(d in direction for d in _COMPLEX_DIRECTIONS):
        score += 3
    elif direction in ("radial_center", "spot_field", "dual_spot"):
        score += 1
    gparams = visual.get("gradient_params") or {}
    freq = gparams.get("frequency") or gparams.get("freq_x") or 0
    if freq > 6:
        score += 2
    elif freq > 3:
        score += 1
    texture = visual.get("texture_type", "none")
    if texture in _TEXTURE_BUSY:
        score += 1
    tex_opacity = float(visual.get("texture_opacity", 0))
    if tex_opacity > 0.1:
        score += 1
    colors = visual.get("gradient_colors", [])
    if len(colors) > 3:
        score += 1
    bg_preset = visual.get("bg_animation_preset", "")
    if bg_preset in _COMPLEX_PRESETS:
        score += 2
    if score <= 2:
        return "low"
    if score <= 5:
        return "medium"
    return "high"


@dataclass
class ReadabilityReport:
    readability_score: float
    aesthetic_score: float
    contrast_status: str
    contrast_ratio: float
    background_busyness: str
    text_box_recommendation: str
    recommended_text_color: Optional[str]
    recommended_text_box: Optional[dict]
    recommended_color_preset: Optional[str]
    issues: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)

    def asdict(self) -> dict:
        return {
            "readability_score": round(self.readability_score, 1),
            "aesthetic_score": round(self.aesthetic_score, 1),
            "contrast_status": self.contrast_status,
            "contrast_ratio": round(self.contrast_ratio, 2),
            "background_busyness": self.background_busyness,
            "text_box_recommendation": self.text_box_recommendation,
            "recommended_text_color": self.recommended_text_color,
            "recommended_text_box": self.recommended_text_box,
            "recommended_color_preset": self.recommended_color_preset,
            "issues": self.issues,
            "recommendations": self.recommendations,
        }


def _best_text_color_against(bg_hex: str) -> str:
    lum = relative_luminance(bg_hex)
    return "#000000" if lum > 0.4 else "#ffffff"


def check_readability(
    text_color: str,
    visual: dict,
    has_backdrop: bool = False,
    backdrop_config: Optional[dict] = None,
    text_size: int = 80,
) -> ReadabilityReport:
    issues: list[str] = []
    recommendations: list[str] = []
    large_text = text_size >= 72

    bg_color = visual.get("background_color", "#1a1a2e")
    busyness = estimate_busyness(visual)

    if has_backdrop and backdrop_config:
        box_color = backdrop_config.get("color", "#000000")
        box_opacity = float(backdrop_config.get("opacity", 0.5))
        bg_lum = relative_luminance(bg_color)
        box_lum = relative_luminance(box_color)
        effective_lum = bg_lum * (1 - box_opacity) + box_lum * box_opacity
        effective_bg = "#000000" if effective_lum < 0.5 else "#ffffff"
    else:
        effective_bg = bg_color

    ratio = contrast_ratio(text_color, effective_bg)
    level = wcag_level(ratio, large_text)

    readability = 0.0
    if ratio >= 7.0:
        readability += 40
    elif ratio >= 4.5:
        readability += 30
    elif ratio >= 3.0:
        readability += 20
    else:
        readability += 5
        issues.append(f"Contrast ratio {ratio:.1f} is below WCAG minimum")

    if level == "fail":
        issues.append(f"Contrast fails WCAG {'large text' if large_text else 'normal text'} requirements")

    aesthetic = 0.0

    if busyness == "low":
        readability += 30
        aesthetic += 30
        if has_backdrop:
            aesthetic -= 10
            recommendations.append("Disable text box — background is clean enough for readable text")
    elif busyness == "medium":
        readability += 20
        aesthetic += 20
    else:
        if has_backdrop:
            readability += 25
            aesthetic += 25
        else:
            readability += 5
            aesthetic += 10
            recommendations.append("Enable text backdrop for busy background")

    if level == "fail":
        contrast_status = "fail"
    elif level == "AA":
        contrast_status = "warning"
    else:
        contrast_status = "pass"

    if ratio < 4.5 and text_color not in ("#ffffff", "#000000"):
        best = _best_text_color_against(effective_bg)
        recommendations.append(f"Change text color to {best}")

    box_rec = "optional"
    if busyness == "high":
        box_rec = "use"
    elif busyness == "low":
        box_rec = "avoid"

    rec_text_color = None
    if contrast_status == "fail":
        rec_text_color = _best_text_color_against(effective_bg)

    rec_text_box = None
    if box_rec == "use" and not has_backdrop:
        rec_text_box = {
            "enabled": True,
            "color": "#000000",
            "opacity": 0.5,
            "padding": 12,
            "radius": 10,
        }
    elif box_rec == "avoid" and has_backdrop:
        rec_text_box = {
            "enabled": False,
            "color": "#000000",
            "opacity": 0.5,
            "padding": 12,
            "radius": 10,
        }

    readability = min(100.0, max(0.0, readability))
    aesthetic = min(100.0, max(0.0, aesthetic))

    return ReadabilityReport(
        readability_score=readability,
        aesthetic_score=aesthetic,
        contrast_status=contrast_status,
        contrast_ratio=ratio,
        background_busyness=busyness,
        text_box_recommendation=box_rec,
        recommended_text_color=rec_text_color,
        recommended_text_box=rec_text_box,
        recommended_color_preset=None,
        issues=issues,
        recommendations=recommendations,
    )


def recommend_preset_for_visual(visual: dict) -> Optional[str]:
    from scriptgen.color_presets import list_presets

    bg_color = visual.get("background_color", "#1a1a2e")
    accent_candidates = visual.get("gradient_colors", [])
    if not accent_candidates:
        accent_candidates = [bg_color]

    try:
        bg_lum = relative_luminance(bg_color)
    except (ValueError, IndexError):
        return None

    best_name = None
    best_score = -1.0

    for preset in list_presets():
        score = 0.0
        try:
            p_lum = relative_luminance(preset.background_base)
        except (ValueError, IndexError):
            continue
        lum_diff = abs(bg_lum - p_lum)
        if lum_diff < 0.1:
            score += 5
        elif lum_diff < 0.3:
            score += 2

        busyness = estimate_busyness(visual)
        if busyness == "high" and preset.max_foreground_opacity < 0.7:
            score += 3
        if busyness == "low" and preset.max_foreground_opacity >= 0.8:
            score += 2

        if preset.recommended_text_box and preset.recommended_text_box.enabled:
            if busyness == "high":
                score += 2
        else:
            if busyness == "low":
                score += 2

        if score > best_score:
            best_score = score
            best_name = preset.name

    return best_name
