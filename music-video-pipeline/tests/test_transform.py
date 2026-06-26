from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import transform  # noqa: E402  (registers transforms)
from transform import REGISTRY, Recipe, RecipeStep, ScriptContext  # noqa: E402
from transform.core import Journal, JournalEntry, diff, get_at, has_at, set_at, delete_at  # noqa: E402
from transform.colors import hex_to_hls, contrast as contrast_ratio  # noqa: E402
from transform.layouts import _rows_for  # noqa: E402
from render.readability import contrast_ratio as readability_contrast  # noqa: E402


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _synced():
    return {
        "lines": [
            {"index": 0, "text": "hello, world foo bar baz", "start": 0.0, "end": 2.0,
             "words": [{"text": "hello,", "start": 0.0, "end": 0.4},
                       {"text": "world", "start": 0.4, "end": 0.8},
                       {"text": "foo", "start": 0.8, "end": 1.2},
                       {"text": "bar", "start": 1.2, "end": 1.6},
                       {"text": "baz", "start": 1.6, "end": 2.0}]},
            {"index": 1, "text": "one two three", "start": 2.0, "end": 3.0,
             "words": [{"text": "one", "start": 2.0, "end": 2.3},
                       {"text": "two", "start": 2.3, "end": 2.6},
                       {"text": "three", "start": 2.6, "end": 3.0}]},
            {"index": 2, "text": "alpha beta gamma, delta epsilon zeta", "start": 3.0, "end": 5.0,
             "words": [{"text": "alpha", "start": 3.0, "end": 3.3},
                       {"text": "beta", "start": 3.3, "end": 3.6},
                       {"text": "gamma,", "start": 3.6, "end": 4.0},
                       {"text": "delta", "start": 4.0, "end": 4.3},
                       {"text": "epsilon", "start": 4.3, "end": 4.6},
                       {"text": "zeta", "start": 4.6, "end": 5.0}]},
            {"index": 3, "text": "you called my name", "start": 5.0, "end": 6.0,
             "words": [{"text": "you", "start": 5.0, "end": 5.3},
                       {"text": "called", "start": 5.3, "end": 5.6},
                       {"text": "my", "start": 5.6, "end": 5.8},
                       {"text": "name", "start": 5.8, "end": 6.0}]},
            {"index": 4, "text": "single phrase line", "start": 6.0, "end": 7.0,
             "words": [{"text": "single", "start": 6.0, "end": 6.3},
                       {"text": "phrase", "start": 6.3, "end": 6.6},
                       {"text": "line", "start": 6.6, "end": 7.0}]},
        ]
    }


def _script():
    return {
        "name": "Test",
        "defaults": {"font_size": 80, "background_type": "gradient",
                     "background_color": "#0B1020", "gradient_colors": ["#0B1020", "#2A1712"]},
        "caption_style": {"font_family": 0, "highlight_color": "#4cc9f0", "text_position": "center"},
        "sections": [
            {"name": "Intro", "type": "intro", "lines": [0],
             "visual": {"text_style": "clean_white", "text_position": "top", "font_size": 60,
                        "background_color": "#0B1020", "gradient_colors": ["#0B1020", "#2A1712"]},
             "lines_overrides": {"0": {"text_position": "bottom", "font_size": 60}},
             "words_overrides": {}},
            {"name": "Chorus", "type": "chorus", "lines": [2],
             "visual": {"text_style": "elegant_gold", "text_position": "bottom", "font_size": 60,
                        "background_color": "#F3E6CF",
                        "gradient_colors": ["#F3E6CF", "#E0B75A"]},
             "lines_overrides": {"2": {"font_size": 60}},
             "words_overrides": {}},
            {"name": "Hook", "type": "hook", "lines": [3],
             "visual": {"text_style": "elegant_gold", "text_position": "bottom", "font_size": 62,
                        "background_color": "#F3E6CF",
                        "gradient_colors": ["#F3E6CF", "#E0B75A"]},
             "lines_overrides": {"3": {"font_size": 62}},
             "words_overrides": {}},
            {"name": "Verse", "type": "verse", "lines": [4],
             "visual": {"text_style": "clean_white", "text_position": "center", "font_size": 72,
                        "background_color": "#0B1020", "gradient_colors": ["#0B1020", "#2A1712"]},
             "lines_overrides": {"4": {"font_size": 71}},
             "words_overrides": {}},
        ],
    }


def _ctx():
    return ScriptContext(script=_script(), lyrics_synced=_synced())


# --------------------------------------------------------------------------- #
# Address navigation + diff + journal
# --------------------------------------------------------------------------- #
class TestNavigation:
    def test_get_has_set_delete(self):
        d = {"a": [{"b": 1}]}
        assert get_at(d, ("a", 0, "b")) == 1
        assert has_at(d, ("a", 0, "b"))
        assert not has_at(d, ("a", 0, "c"))
        set_at(d, ("a", 0, "b"), 9)
        assert d["a"][0]["b"] == 9
        delete_at(d, ("a", 0, "b"))
        assert "b" not in d["a"][0]


class TestDiff:
    def test_detects_leaf_change(self):
        a = {"x": 1, "y": [1, 2]}
        b = {"x": 2, "y": [1, 2]}
        entries = diff(a, b)
        assert len(entries) == 1
        assert entries[0].address == ("x",)
        assert entries[0].before == 1 and entries[0].after == 2

    def test_detects_added_and_removed_keys(self):
        a = {"x": 1}
        b = {"y": 2}
        entries = diff(a, b)
        addr = {e.address[0] for e in entries}
        assert ("x" in addr) and ("y" in addr)

    def test_ignores_provenance(self):
        a = {"x": 1}
        b = {"x": 1, "_transforms": {"recipe": "r"}}
        assert diff(a, b) == []

    def test_journal_invert_restores(self):
        original = {"a": {"b": [1, 2, 3]}, "c": "keep"}
        work = copy.deepcopy(original)
        work["a"]["b"][1] = 99
        work["a"]["new"] = "added"
        del work["c"]
        entries = diff(original, work)
        Journal(entries=entries).invert(work)
        assert work == original


# --------------------------------------------------------------------------- #
# Selectors
# --------------------------------------------------------------------------- #
class TestSelectors:
    def test_all_sections(self):
        ctx = _ctx()
        assert ctx.section_indices(None) == [0, 1, 2, 3]

    def test_by_type(self):
        ctx = _ctx()
        assert ctx.section_indices({"section": "hook"}) == [2]
        assert ctx.section_indices({"section": "chorus"}) == [1]

    def test_by_style_gold(self):
        ctx = _ctx()
        assert ctx.section_indices({"style": "gold"}) == [1, 2]

    def test_by_name_contains(self):
        ctx = _ctx()
        assert ctx.section_indices({"name_contains": "Hook"}) == [2]


# --------------------------------------------------------------------------- #
# Individual transforms
# --------------------------------------------------------------------------- #
class TestCenterText:
    def test_centers_and_clears_per_line(self):
        ctx = _ctx()
        REGISTRY.get("center_text").apply(ctx)
        for sec in ctx.sections:
            assert sec["visual"]["text_position"] == "center"
        assert "text_position" not in ctx.sections[0]["lines_overrides"]["0"]


class TestSymmetrize:
    def test_rows_helper(self):
        assert _rows_for(2) == [0.42, 0.58]
        assert _rows_for(3) == [0.34, 0.5, 0.66]

    def test_two_phrase_line_symmetric(self):
        ctx = _ctx()
        REGISTRY.get("symmetrize_phrase_rows").apply(ctx)
        wo = ctx.sections[0]["words_overrides"]
        # line 0 splits into [[0],[1,2,3,4]]
        assert wo["0.0"]["y"] == 0.42
        assert wo["0.1"]["y"] == 0.58
        assert wo["0.4"]["y"] == 0.58

    def test_single_phrase_no_explicit_y(self):
        ctx = _ctx()
        REGISTRY.get("symmetrize_phrase_rows").apply(ctx)
        wo = ctx.sections[3]["words_overrides"]
        # verse line 4 is single phrase -> no y overrides
        for key in ("4.0", "4.1", "4.2"):
            assert key not in wo or "y" not in wo.get(key, {})


class TestDarkenForContrast:
    def test_gold_bg_meets_contrast(self):
        ctx = _ctx()
        REGISTRY.get("darken_for_contrast").apply(ctx, {"style": "gold"},
                                                   {"min_contrast": 4.5, "text_color": "#E6C850"})
        for idx in (1, 2):
            bg = ctx.sections[idx]["visual"]["background_color"]
            assert readability_contrast("#E6C850", bg) >= 4.5
            # darker than the original light cream
            assert bg != "#F3E6CF"


class TestVaryLineBackgrounds:
    def test_escalate_monotonic_lightness(self):
        script = _script()
        # make intro span several lines for a real escalation curve
        script["sections"][0]["lines"] = [0, 1, 4]
        ctx = ScriptContext(script=script, lyrics_synced=_synced())
        REGISTRY.get("vary_line_backgrounds").apply(
            ctx, {"section": "intro"}, {"mode": "escalate", "hue_span": 0.12, "lit_osc": 0.06}
        )
        lo = ctx.sections[0]["lines_overrides"]
        lits = [hex_to_hls(lo[str(li)]["background_color"])[1] for li in (0, 1, 4)]
        assert lits[-1] > lits[0]
        # distinct directions present
        dirs = {lo[str(li)]["gradient_direction"] for li in (0, 1, 4)}
        assert len(dirs) >= 2


class TestTypography:
    def test_set_section_font_uniform(self):
        ctx = _ctx()
        REGISTRY.get("set_section_font").apply(ctx, {"section": "hook"}, {"size": 92})
        assert ctx.sections[2]["visual"]["font_size"] == 92
        assert ctx.sections[2]["lines_overrides"]["3"]["font_size"] == 92

    def test_set_section_visual_merges(self):
        ctx = _ctx()
        REGISTRY.get("set_section_visual").apply(
            ctx, {"section": "chorus"}, {"gradient_direction": "diamond"}
        )
        assert ctx.sections[1]["visual"]["gradient_direction"] == "diamond"

    def test_shift_section_hue_changes_color(self):
        ctx = _ctx()
        before = ctx.sections[0]["visual"]["background_color"]
        REGISTRY.get("shift_section_hue").apply(ctx, {"section": "intro"}, {"delta": 0.25})
        after = ctx.sections[0]["visual"]["background_color"]
        assert before != after


# --------------------------------------------------------------------------- #
# Groupoid laws
# --------------------------------------------------------------------------- #
class TestGroupoid:
    def test_identity_recipe_no_change(self):
        ctx = _ctx()
        before = copy.deepcopy(ctx.script)
        Recipe(name="identity", steps=[]).apply(ctx)
        # content identical (only _transforms added)
        ctx.script.pop("_transforms", None)
        assert ctx.script == before

    def test_invert_restores_original(self):
        ctx = _ctx()
        original = copy.deepcopy(ctx.script)
        recipe = Recipe(
            name="t",
            steps=[
                RecipeStep("center_text"),
                RecipeStep("darken_for_contrast", {"style": "gold"}),
                RecipeStep("set_section_font", {"section": "hook"}, {"size": 92}),
            ],
        )
        recipe.apply(ctx)
        assert ctx.script != original
        recipe.invert(ctx)
        assert "_transforms" not in ctx.script
        assert ctx.script == original

    def test_apply_is_idempotent(self):
        ctx = _ctx()
        recipe = Recipe(name="t", steps=[RecipeStep("center_text"),
                                          RecipeStep("set_section_font", {"section": "hook"}, {"size": 92})])
        recipe.apply(ctx)
        once = copy.deepcopy(ctx.script)
        # re-run with a fresh context carrying the journal
        ctx2 = ScriptContext(script=copy.deepcopy(once), lyrics_synced=_synced())
        recipe.apply(ctx2)
        # drop provenance for comparison
        once.pop("_transforms", None)
        ctx2.script.pop("_transforms", None)
        assert ctx2.script == once

    def test_compose_associative(self):
        a = Recipe(name="a", steps=[RecipeStep("center_text")])
        b = Recipe(name="b", steps=[RecipeStep("set_section_font", {"section": "hook"}, {"size": 80})])
        c = Recipe(name="c", steps=[RecipeStep("shift_section_hue", {"section": "intro"}, {"delta": 0.1})])
        left_then_c = compose(compose(a, b), c)
        a_then_right = compose(a, compose(b, c))
        assert [s.transform for s in left_then_c.steps] == [s.transform for s in a_then_right.steps]


# --------------------------------------------------------------------------- #
# Aspect transform via framework
# --------------------------------------------------------------------------- #
class TestRetargetAspect:
    def test_apply_and_invert(self):
        ctx = _ctx()
        original = copy.deepcopy(ctx.script)
        recipe = Recipe(name="retarget", steps=[RecipeStep(
            "retarget_aspect", params={"source_aspect": "16:9", "target_aspect": "9:16"}
        )])
        recipe.apply(ctx)
        meta = ctx.script.get("_aspect_meta", {})
        assert meta.get("target_aspect") == "9:16"
        # font sizes scaled down
        assert ctx.script["defaults"]["font_size"] < original["defaults"]["font_size"]
        # invert restores exactly
        recipe.invert(ctx)
        assert "_transforms" not in ctx.script
        assert ctx.script == original


# --------------------------------------------------------------------------- #
# Recipe loading
# --------------------------------------------------------------------------- #
class TestRecipes:
    def test_load_named_recipe(self):
        from transform.recipes import load_recipe, DEFAULT_RECIPES_DIR
        assert (DEFAULT_RECIPES_DIR / "reality_signal_slate.json").exists()
        recipe = load_recipe("reality_signal_slate")
        assert recipe.name == "reality_signal_slate"
        assert len(recipe.steps) > 0

    def test_slate_recipe_applies_and_inverts(self):
        ctx = _ctx()
        original = copy.deepcopy(ctx.script)
        from transform.recipes import load_recipe
        recipe = load_recipe("reality_signal_slate")
        recipe.apply(ctx)
        assert ctx.script["_transforms"]["recipe"] == "reality_signal_slate"
        recipe.invert(ctx)
        assert ctx.script == original


def compose(a, b, name=None):
    from transform.core import compose as _compose
    return _compose(a, b, name=name)


class TestAddBrandedScenes:
    def test_writes_intro_and_outro(self):
        ctx = _ctx()
        REGISTRY.get("add_branded_scenes").apply(
            ctx, {}, {"branding_image": "/x.png", "logo_path": "/y.png", "title": "ASABAAL"}
        )
        intro = ctx.script["intro"]
        assert intro["image"] == "/x.png"
        assert intro["title"] == "ASABAAL"
        assert intro["subtitle"] == "A Reality Signal"
        assert isinstance(intro["duration"], float)  # derived from synced first-word start
        outro = ctx.script["outro"]
        assert outro["logo"] == "/y.png"
        assert outro["text"] == "Presented by"

    def test_title_falls_back_to_script_name(self):
        ctx = _ctx()
        REGISTRY.get("add_branded_scenes").apply(ctx, {}, {"branding_image": "/x.png", "logo_path": "/y.png"})
        assert ctx.script["intro"]["title"] == "Test"  # script name title-cased


class TestGeometricBackgrounds:
    def test_five_stop_palette_and_direction(self):
        ctx = _ctx()
        REGISTRY.get("geometric_backgrounds").apply(ctx)
        for sec in ctx.sections:
            gc = sec["visual"]["gradient_colors"]
            assert len(gc) == 5
            assert sec["visual"]["gradient_direction"]

    def test_strips_per_line_background_keys(self):
        ctx = _ctx()
        # give the chorus section a per-line background override to be stripped
        ctx.sections[1]["lines_overrides"]["99"] = {
            "background_color": "#ffffff", "gradient_colors": ["#fff", "#000"],
            "gradient_direction": "cross", "font_size": 60,
        }
        REGISTRY.get("geometric_backgrounds").apply(ctx)
        entry = ctx.sections[1]["lines_overrides"]["99"]
        assert "background_color" not in entry and "gradient_colors" not in entry
        assert "gradient_direction" not in entry
        assert entry.get("font_size") == 60  # non-background keys preserved

    def test_accents_are_visible_midtones(self):
        from transform.geometric import _enrich_to_5
        from render.readability import relative_luminance
        palette = _enrich_to_5(["#0B1020", "#C68A2E", "#F3E6CF"])  # chorus-ish
        accents = [palette[1], palette[3]]
        for a in accents:
            assert 0.02 <= relative_luminance(a) <= 0.16  # visible, not blinding

    def test_directions_varied_across_sections(self):
        ctx = _ctx()
        REGISTRY.get("geometric_backgrounds").apply(ctx)
        dirs = [sec["visual"]["gradient_direction"] for sec in ctx.sections]
        assert len(set(dirs)) > 1
