"""Backwards-compatibility shim.

The aspect-ratio transformation now lives canonically in :mod:`transform.aspects`
(part of the Reality Signal groupoid framework). This module re-exports the
complete public + private surface so existing imports
(``render.aspect_transform``, the ``mvp transform`` CLI, and
``tests/test_aspect_transform.py``) keep working unchanged.
"""

from __future__ import annotations

from transform.aspects import (  # noqa: F401
    ASPECT_16_9,
    ASPECT_9_16,
    CANVAS_SIZES,
    POS_TO_Y,
    SAFE_ZONES,
    VALID_ASPECTS,
    _POS_TO_Y,
    _adjust_dual_spot,
    _adjust_y,
    _compute_line_group_widths,
    _effective_font_size,
    _ensure_text_fits,
    _image_aspect_label,
    _is_horizontal_image,
    _is_vertical_image,
    _scale_font_delta,
    _scale_font_size,
    _swap_branded_images,
    check_layout_issues,
    detect_aspect_ratio,
    find_asset_variant,
    transform_script,
)
