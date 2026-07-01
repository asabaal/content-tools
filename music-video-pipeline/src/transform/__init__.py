"""Reality Signal groupoid -- script transformation framework.

Importing this package registers all built-in transformations (visual layout,
background, typography, and the retrofitted aspect-ratio retarget) with the
default :data:`transform.core.REGISTRY`.

See ``transform/core.py`` for the algebra (Journal + universal inverse,
composable/invertible Recipes) and ``transform/recipes.py`` for declarative
recipe loading.
"""

from __future__ import annotations

from .core import (
    REGISTRY,
    Journal,
    JournalEntry,
    Recipe,
    RecipeStep,
    Registry,
    ScriptContext,
    Transformation,
    compose,
    diff,
)
from . import colors, selectors  # noqa: F401
from . import layouts  # noqa: F401  (registers center_text, symmetrize_phrase_rows)
from . import backgrounds  # noqa: F401  (registers darken_for_contrast, vary_line_backgrounds)
from . import typography  # noqa: F401  (registers set_section_font, set_section_visual, shift_section_hue)
from . import branding  # noqa: F401  (registers add_branded_scenes)
from . import geometric  # noqa: F401  (registers geometric_backgrounds)
from . import aspects  # noqa: F401  (registers retarget_aspect)
from . import timing  # noqa: F401  (registers realign_from_stem)
from . import recipes  # noqa: F401

__all__ = [
    "REGISTRY",
    "Journal",
    "JournalEntry",
    "Recipe",
    "RecipeStep",
    "Registry",
    "ScriptContext",
    "Transformation",
    "compose",
    "diff",
    "colors",
    "selectors",
    "layouts",
    "backgrounds",
    "typography",
    "aspects",
    "timing",
    "recipes",
]
