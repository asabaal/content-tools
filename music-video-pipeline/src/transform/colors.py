"""Color helpers for transformations.

Reuses the contrast/luminance math in :mod:`render.readability` so the
transform framework and the audit/readability tooling agree on a single
definition of perceptual contrast.
"""

from __future__ import annotations

import colorsys
from typing import Tuple

from render.readability import contrast_ratio, relative_luminance

# Representative visible gold fill (matches the darkest band of the "elegant_gold"
# / "gold" style generator, so contrast targets are conservative).
GOLD_TEXT_PROXY = "#E6C850"


def hex_to_hls(hex_color: str) -> Tuple[float, float, float]:
    """Return (hue, lightness, saturation) each in [0, 1]."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"Invalid hex color: {hex_color!r}")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return colorsys.rgb_to_hls(r, g, b)


def hls_to_hex(hue: float, lightness: float, saturation: float) -> str:
    hue = hue % 1.0
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return "#%02x%02x%02x" % (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def relative_lum(hex_color: str) -> float:
    return relative_luminance(hex_color)


def contrast(hex_a: str, hex_b: str) -> float:
    return contrast_ratio(hex_a, hex_b)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def darken_to_contrast(
    bg_hex: str,
    text_hex: str = GOLD_TEXT_PROXY,
    min_contrast: float = 4.5,
    lightness_floor: float = 0.04,
) -> str:
    """Lower a background color's lightness until it meets ``min_contrast``
    against ``text_hex``, preserving hue and saturation.

    Returns the original color if it already satisfies the target, or the
    floor-darkened color if the target cannot be reached.
    """
    if contrast_ratio(text_hex, bg_hex) >= min_contrast:
        return bg_hex

    hue, lightness, saturation = hex_to_hls(bg_hex)
    candidate = bg_hex
    lo, hi = lightness_floor, lightness
    # Binary search the highest lightness that still meets contrast.
    for _ in range(24):
        mid = (lo + hi) / 2.0
        candidate = hls_to_hex(hue, mid, saturation)
        if contrast_ratio(text_hex, candidate) >= min_contrast:
            lo = mid  # can afford to be lighter; try higher
        else:
            hi = mid  # too light; go darker
    candidate = hls_to_hex(hue, lo, saturation)
    return candidate


def shift_hue(hex_color: str, delta: float) -> str:
    hue, lightness, saturation = hex_to_hls(hex_color)
    return hls_to_hex(hue + delta, lightness, saturation)


def with_lightness(hex_color: str, lightness: float) -> str:
    hue, _, saturation = hex_to_hls(hex_color)
    return hls_to_hex(hue, clamp(lightness, 0.0, 1.0), saturation)


def with_saturation(hex_color: str, saturation: float) -> str:
    hue, lightness, _ = hex_to_hls(hex_color)
    return hls_to_hex(hue, lightness, clamp(saturation, 0.0, 1.0))


def adjust_lightness(hex_color: str, delta: float) -> str:
    hue, lightness, saturation = hex_to_hls(hex_color)
    return hls_to_hex(hue, clamp(lightness + delta, 0.0, 1.0), saturation)


__all__ = [
    "GOLD_TEXT_PROXY",
    "hex_to_hls",
    "hls_to_hex",
    "relative_lum",
    "contrast",
    "clamp",
    "darken_to_contrast",
    "shift_hue",
    "with_lightness",
    "with_saturation",
    "adjust_lightness",
]
