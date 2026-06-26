"""Declarative recipe loading and application.

A recipe is a JSON document of shape::

    {
      "name": "reality_signal_slate",
      "description": "...",
      "steps": [
        {"transform": "center_text", "selector": {}, "params": {}},
        ...
      ]
    }

Recipes live in ``<pipeline>/recipes/*.json``. ``load_recipe`` accepts a name
(resolved against that directory), an explicit path, or an already-parsed dict.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from .core import REGISTRY, Recipe, Registry, ScriptContext

DEFAULT_RECIPES_DIR = Path(__file__).resolve().parent.parent.parent / "recipes"


def load_recipe(source: Union[str, Path, dict], registry: Registry = REGISTRY) -> Recipe:
    """Load a recipe from a name, file path, or dict, validating against ``registry``."""
    if isinstance(source, dict):
        recipe = Recipe.from_dict(source)
    else:
        text = str(source)
        path: Optional[Path] = None
        candidate = Path(text)
        if candidate.exists():
            path = candidate
        else:
            named = DEFAULT_RECIPES_DIR / f"{text}.json"
            if named.exists():
                path = named
        if path is None:
            raise FileNotFoundError(
                f"Recipe not found: {text!r} (looked in {DEFAULT_RECIPES_DIR})"
            )
        import json

        recipe = Recipe.from_dict(json.loads(path.read_text(encoding="utf-8")))

    errors = recipe.validate(registry)
    if errors:
        raise ValueError(f"Recipe {recipe.name!r} invalid: {'; '.join(errors)}")
    return recipe


def apply_recipe(
    source: Union[str, Path, dict, Recipe],
    ctx: ScriptContext,
    registry: Registry = REGISTRY,
) -> Recipe:
    """Apply a recipe (name/path/dict/Recipe) to ``ctx`` and return the Recipe."""
    recipe = source if isinstance(source, Recipe) else load_recipe(source, registry)
    recipe.apply(ctx, registry)
    return recipe


__all__ = ["DEFAULT_RECIPES_DIR", "load_recipe", "apply_recipe"]
