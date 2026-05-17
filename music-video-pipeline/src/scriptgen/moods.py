from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MoodProfile:
    name: str
    base_hue: float
    saturation: tuple[float, float]
    lightness: tuple[float, float]
    texture_default: str
    direction: str
    gradient_likely: bool


MOODS: dict[str, MoodProfile] = {
    "dark_moody": MoodProfile(
        name="Dark & Moody",
        base_hue=240,
        saturation=(0.15, 0.35),
        lightness=(0.08, 0.18),
        texture_default="vignette_heavy",
        direction="diagonal_tl_br",
        gradient_likely=True,
    ),
    "bright_poppy": MoodProfile(
        name="Bright & Poppy",
        base_hue=30,
        saturation=(0.60, 0.80),
        lightness=(0.40, 0.55),
        texture_default="none",
        direction="horizontal_left_right",
        gradient_likely=False,
    ),
    "warm_intimate": MoodProfile(
        name="Warm & Intimate",
        base_hue=20,
        saturation=(0.35, 0.55),
        lightness=(0.20, 0.32),
        texture_default="paper_subtle",
        direction="vertical_top_bottom",
        gradient_likely=True,
    ),
    "cool_ethereal": MoodProfile(
        name="Cool & Ethereal",
        base_hue=200,
        saturation=(0.25, 0.50),
        lightness=(0.12, 0.28),
        texture_default="vignette_soft",
        direction="radial_center",
        gradient_likely=True,
    ),
    "high_energy": MoodProfile(
        name="High Energy",
        base_hue=0,
        saturation=(0.65, 0.90),
        lightness=(0.25, 0.45),
        texture_default="grain_film",
        direction="diagonal_tr_bl",
        gradient_likely=True,
    ),
}

DEFAULT_MOOD = "dark_moody"
