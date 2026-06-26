"""Reality Signal groupoid -- script transformation framework.

A composable, invertible algebra of transformations over a render ``script.json``.

Each :class:`Transformation` acts on a :class:`ScriptContext` and produces a
:class:`Journal` of the exact key-level changes it made. Because every change is
recorded, any transformation (and any :class:`Recipe` composed of them) has a
universal inverse -- replay the journal backwards. With associative composition
and identities, the recipes form a *groupoid* (composition is partial: not every
recipe applies to every script state).

The first citizen is the pre-existing aspect-ratio transform (16:9 <-> 9:16),
retrofitted here as the ``retarget_aspect`` transformation. Additional visual
transforms (centering, contrast, per-line background variety, typography) are
registered alongside it and composed declaratively via JSON recipes.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .selectors import resolve_section_indices

Address = Tuple[Any, ...]

# Keys that are framework bookkeeping, never diffed as content.
_PROVENANCE_KEYS = {"_transforms"}

_SENTINEL = object()


class _MissingType:
    """Sentinel marking an absent value in a :class:`Journal` entry."""

    _instance: Optional["_MissingType"] = None

    def __new__(cls) -> "_MissingType":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "<MISSING>"

    def __bool__(self) -> bool:
        return False


MISSING = _MissingType()


# --------------------------------------------------------------------------- #
# Address navigation
# --------------------------------------------------------------------------- #
def get_at(root: Any, address: Address) -> Any:
    cur = root
    for key in address:
        cur = cur[key]
    return cur


def has_at(root: Any, address: Address) -> bool:
    cur = root
    for key in address:
        if not isinstance(cur, (dict, list)):
            return False
        if isinstance(cur, list):
            if not isinstance(key, int) or key < 0 or key >= len(cur):
                return False
        else:
            if key not in cur:
                return False
        cur = cur[key]
    return True


def set_at(root: Any, address: Address, value: Any) -> None:
    if not address:
        raise ValueError("cannot set root via empty address")
    cur = root
    for key in address[:-1]:
        cur = cur[key]
    last = address[-1]
    cur[last] = value


def delete_at(root: Any, address: Address) -> None:
    if not address:
        raise ValueError("cannot delete root via empty address")
    cur = root
    for key in address[:-1]:
        cur = cur[key]
    last = address[-1]
    if isinstance(cur, list):
        # shift-preserving delete only when safe; otherwise no-op
        if 0 <= last < len(cur):
            cur.pop(last)
    else:
        cur.pop(last, None)


# --------------------------------------------------------------------------- #
# Journal
# --------------------------------------------------------------------------- #
@dataclass
class JournalEntry:
    address: Address
    before: Any = MISSING
    after: Any = MISSING

    def to_dict(self) -> dict:
        bm = self.before is MISSING
        am = self.after is MISSING
        return {
            "addr": list(self.address),
            "before": None if bm else self.before,
            "after": None if am else self.after,
            "before_missing": bm,
            "after_missing": am,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "JournalEntry":
        return cls(
            address=tuple(d["addr"]),
            before=MISSING if d.get("before_missing") else d.get("before"),
            after=MISSING if d.get("after_missing") else d.get("after"),
        )


@dataclass
class Journal:
    entries: List[JournalEntry] = field(default_factory=list)

    def extend(self, entries: Sequence[JournalEntry]) -> None:
        self.entries.extend(entries)

    def to_list(self) -> List[dict]:
        return [e.to_dict() for e in self.entries]

    @classmethod
    def from_list(cls, items: List[dict]) -> "Journal":
        return cls(entries=[JournalEntry.from_dict(d) for d in items])

    def invert(self, script: dict) -> None:
        """Replay this journal in reverse, restoring the pre-transform state."""
        for entry in reversed(self.entries):
            if entry.before is MISSING:
                if has_at(script, entry.address[:-1] if entry.address else ()):
                    # value was added by the transform -> remove it
                    try:
                        delete_at(script, entry.address)
                    except (KeyError, IndexError, TypeError):
                        pass
            else:
                # restore original value (creating the path if needed)
                _ensure_parent(script, entry.address)
                try:
                    set_at(script, entry.address, copy.deepcopy(entry.before))
                except (KeyError, IndexError, TypeError):
                    pass


def _ensure_parent(script: dict, address: Address) -> None:
    cur = script
    for key in address[:-1]:
        if isinstance(cur, list):
            if not isinstance(key, int) or key < 0 or key >= len(cur):
                return
            cur = cur[key]
        else:
            if key not in cur:
                return
            cur = cur[key]


def diff(before: Any, after: Any, prefix: Address = ()) -> List[JournalEntry]:
    """Compute leaf-level :class:`JournalEntry` differences between two values."""
    entries: List[JournalEntry] = []

    if isinstance(before, dict) and isinstance(after, dict):
        keys: List[Any] = []
        seen = set()
        for k in list(before.keys()) + list(after.keys()):
            if k in seen or k in _PROVENANCE_KEYS:
                continue
            seen.add(k)
            keys.append(k)
        for k in keys:
            sub = prefix + (k,)
            in_b = k in before
            in_a = k in after
            if in_b and not in_a:
                entries.append(JournalEntry(sub, before=before[k], after=MISSING))
            elif in_a and not in_b:
                entries.append(JournalEntry(sub, before=MISSING, after=after[k]))
            else:
                entries.extend(diff(before[k], after[k], sub))
    elif isinstance(before, list) and isinstance(after, list):
        if len(before) == len(after):
            for i in range(len(before)):
                entries.extend(diff(before[i], after[i], prefix + (i,)))
        else:
            if before != after:
                entries.append(JournalEntry(prefix, before=before, after=after))
    else:
        if before != after:
            entries.append(JournalEntry(prefix, before=before, after=after))

    return entries


# --------------------------------------------------------------------------- #
# Script context
# --------------------------------------------------------------------------- #
@dataclass
class ScriptContext:
    script: dict
    lyrics_synced: Optional[dict] = None
    project_dir: Optional[Path] = None

    @property
    def sections(self) -> List[dict]:
        return self.script.get("sections", [])

    @property
    def synced_lines(self) -> List[dict]:
        return (self.lyrics_synced or {}).get("lines", [])

    def section_indices(self, selector: Optional[dict]) -> List[int]:
        return resolve_section_indices(self.sections, selector)


# --------------------------------------------------------------------------- #
# Transformations + Registry
# --------------------------------------------------------------------------- #
class Transformation:
    """A single, journaled operation over a script.

    Subclasses implement :meth:`run`, mutating ``ctx.script`` freely. The
    framework deep-copies before/after to produce an exact :class:`Journal`,
    which yields a universal inverse -- no per-transform undo code required.
    """

    name: str = ""
    description: str = ""
    params_schema: dict = field(default_factory=dict)

    def run(self, ctx: ScriptContext, selector: dict, params: dict) -> None:
        raise NotImplementedError

    def apply(
        self,
        ctx: ScriptContext,
        selector: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Journal:
        selector = selector or {}
        params = params or {}
        before = copy.deepcopy(ctx.script)
        self.run(ctx, selector, params)
        return Journal(entries=diff(before, ctx.script))


class Registry:
    def __init__(self) -> None:
        self._transforms: Dict[str, Transformation] = {}

    def register(self, transform: Transformation) -> Transformation:
        if not transform.name:
            raise ValueError("Transformation must define a non-empty name")
        self._transforms[transform.name] = transform
        return transform

    def register_instance(self, transform: Transformation) -> Transformation:
        return self.register(transform)

    def get(self, name: str) -> Transformation:
        if name not in self._transforms:
            raise KeyError(f"Unknown transformation: {name!r}")
        return self._transforms[name]

    def has(self, name: str) -> bool:
        return name in self._transforms

    def names(self) -> List[str]:
        return sorted(self._transforms)


REGISTRY = Registry()


# --------------------------------------------------------------------------- #
# Recipes
# --------------------------------------------------------------------------- #
@dataclass
class RecipeStep:
    transform: str
    selector: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"transform": self.transform, "selector": self.selector, "params": self.params}

    @classmethod
    def from_dict(cls, d: dict) -> "RecipeStep":
        if "transform" not in d:
            raise ValueError("Recipe step missing 'transform' name")
        return cls(
            transform=d["transform"],
            selector=d.get("selector") or {},
            params=d.get("params") or {},
        )


@dataclass
class Recipe:
    """An ordered composition of transformations -- a declarative desired version.

    ``apply`` is an idempotent projection: if the script already carries a
    transform journal, it is inverted first, then the recipe re-applied. Thus
    ``apply . apply == apply`` and ``invert . apply == identity`` (groupoid).
    """

    name: str
    steps: List[RecipeStep] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Recipe":
        if "name" not in d:
            raise ValueError("Recipe missing 'name'")
        steps = [RecipeStep.from_dict(s) for s in d.get("steps", [])]
        return cls(name=d["name"], description=d.get("description", ""), steps=steps)

    def validate(self, registry: Registry = REGISTRY) -> List[str]:
        errors: List[str] = []
        for i, step in enumerate(self.steps):
            if not registry.has(step.transform):
                errors.append(f"step {i}: unknown transform {step.transform!r}")
        return errors

    def apply(self, ctx: ScriptContext, registry: Registry = REGISTRY) -> Journal:
        # idempotent reset: undo any prior transform journal before re-applying
        existing = ctx.script.get("_transforms")
        if isinstance(existing, dict) and existing.get("journal"):
            Journal.from_list(existing["journal"]).invert(ctx.script)
            ctx.script.pop("_transforms", None)

        composite: List[JournalEntry] = []
        step_records: List[dict] = []
        for step in self.steps:
            transform = registry.get(step.transform)
            journal = transform.apply(ctx, step.selector, step.params)
            composite.extend(journal.entries)
            step_records.append(step.to_dict())

        ctx.script["_transforms"] = {
            "version": 1,
            "recipe": self.name,
            "steps": step_records,
            "journal": [e.to_dict() for e in composite],
        }
        return Journal(entries=composite)

    def invert(self, ctx: ScriptContext) -> Journal:
        existing = ctx.script.get("_transforms")
        if not isinstance(existing, dict) or not existing.get("journal"):
            return Journal()
        journal = Journal.from_list(existing["journal"])
        journal.invert(ctx.script)
        ctx.script.pop("_transforms", None)
        return journal


def compose(left: Recipe, right: Recipe, name: Optional[str] = None) -> Recipe:
    """Associative composition: apply ``left`` then ``right`` (right after left)."""
    return Recipe(
        name=name or f"{left.name}+{right.name}",
        steps=list(left.steps) + list(right.steps),
    )


__all__ = [
    "MISSING",
    "Address",
    "Journal",
    "JournalEntry",
    "diff",
    "get_at",
    "has_at",
    "set_at",
    "delete_at",
    "ScriptContext",
    "Transformation",
    "Registry",
    "REGISTRY",
    "RecipeStep",
    "Recipe",
    "compose",
]
