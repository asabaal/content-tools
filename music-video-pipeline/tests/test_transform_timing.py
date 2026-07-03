from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import transform  # noqa: E402  (registers transforms)
from transform import REGISTRY, Recipe, RecipeStep, ScriptContext  # noqa: E402
from transform.selectors import resolve_line_indices, resolve_line_keys  # noqa: E402
from lyrics.alignment_analyzer import align_words_from_segments  # noqa: E402
from lyrics.synchronizer import snap_to_nearest_beat, reconcile_region_boundaries  # noqa: E402


# --------------------------------------------------------------------------- #
# Fixtures: a tiny "post-hook"-like region that's bunched in synced but clean
# in the backing-vocals stem transcription.
# --------------------------------------------------------------------------- #
def _backing_phrase(t0: float) -> dict:
    return {
        "start": t0,
        "end": t0 + 3.0,
        "text": "The Lord called my name",
        "words": [
            {"word": "The", "start": t0, "end": t0 + 0.5},
            {"word": "Lord", "start": t0 + 0.5, "end": t0 + 1.0},
            {"word": "called", "start": t0 + 1.0, "end": t0 + 1.5},
            {"word": "my", "start": t0 + 1.5, "end": t0 + 2.0},
            {"word": "name", "start": t0 + 2.0, "end": t0 + 3.0},
        ],
    }


def _synced_line(idx: int, text: str, start: float, end: float) -> dict:
    return {
        "index": idx,
        "text": text,
        "start": start,
        "end": end,
        "words": [{"text": w, "start": start, "end": end} for w in text.split()],
    }


def _bunched_synced() -> dict:
    # Five identical post-hook lines mistimed/bunched (mirrors the asabaal bug):
    # first one anchored too early & stretched, rest crammed together.
    lines = [
        _synced_line(0, "You called my name", 350.0, 355.0),
        _synced_line(1, "The LORD called my name", 355.0, 366.0),  # 11s stretch
        _synced_line(2, "The LORD called my name", 366.0, 369.0),
        _synced_line(3, "The LORD called my name", 369.0, 370.0),
        _synced_line(4, "The LORD called my name", 370.0, 372.0),
        _synced_line(5, "The LORD called my name", 372.0, 374.0),
        _synced_line(6, "Shout for joy", 377.0, 379.0),
    ]
    return {"lines": lines}


def _clean_backing_transcription() -> dict:
    return {
        "segments": [
            _backing_phrase(358.0),
            _backing_phrase(362.0),
            _backing_phrase(365.0),
            _backing_phrase(368.0),
            _backing_phrase(372.0),
        ]
    }


def _script_with_posthook() -> dict:
    return {
        "name": "AsabaalTest",
        "defaults": {"font_size": 80},
        "caption_style": {},
        "sections": [
            {"name": "Hook", "type": "hook", "lines": [0], "visual": {}, "lines_overrides": {}},
            {"name": "Post-Hook", "type": "post-hook", "lines": [1, 2, 3, 4, 5],
             "visual": {}, "lines_overrides": {}},
            {"name": "Outro", "type": "outro", "lines": [6], "visual": {}, "lines_overrides": {}},
        ],
    }


@pytest.fixture
def project(tmp_path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    (data / "vocal_transcription_backing_vocals.json").write_text(
        json.dumps(_clean_backing_transcription()), encoding="utf-8"
    )
    (data / "analysis.json").write_text(
        json.dumps({"beat_times": [358.0, 361.0, 362.0, 365.0, 368.0, 372.0]}), encoding="utf-8"
    )
    (data / "vocal_onsets.json").write_text(
        json.dumps({"onset_times": [358.0, 362.0, 365.0, 368.0, 372.0]}), encoding="utf-8"
    )
    return tmp_path


def _ctx(project: Path) -> ScriptContext:
    return ScriptContext(
        script=_script_with_posthook(),
        lyrics_synced=_bunched_synced(),
        project_dir=project,
    )


# --------------------------------------------------------------------------- #
# Selectors
# --------------------------------------------------------------------------- #
class TestLineSelectors:
    def test_explicit_lines(self):
        assert resolve_line_indices([], {"lines": [5, 1, 3]}) == [1, 3, 5]

    def test_section_union(self):
        sections = _script_with_posthook()["sections"]
        assert resolve_line_indices(sections, {"section": "post-hook"}) == [1, 2, 3, 4, 5]

    def test_all(self):
        sections = _script_with_posthook()["sections"]
        assert resolve_line_indices(sections, {}) == [0, 1, 2, 3, 4, 5, 6]

    def test_resolve_line_keys(self):
        assert resolve_line_keys(_script_with_posthook()["sections"][1]) == [1, 2, 3, 4, 5]


# --------------------------------------------------------------------------- #
# Reused helpers
# --------------------------------------------------------------------------- #
class TestPureHelpers:
    def test_snap_to_nearest_beat(self):
        beats = np.array([1.0, 1.5, 2.0])
        assert snap_to_nearest_beat(1.07, beats) == 1.0
        assert snap_to_nearest_beat(2.5, beats) == 2.5  # out of tolerance -> unchanged

    def test_snap_no_beats(self):
        assert snap_to_nearest_beat(3.0, []) == 3.0

    def test_reconcile_splits_overlap(self):
        lines = [
            {"start": 0.0, "end": 1.4, "words": [{"start": 0.0, "end": 1.4}]},
            {"start": 1.1, "end": 2.5, "words": [{"start": 1.1, "end": 2.5}]},
        ]
        reconcile_region_boundaries(lines, prev_end=0.0, next_start=3.0)
        assert lines[0]["end"] == lines[1]["start"]
        assert lines[0]["end"] < 1.4

    def test_reconcile_clamps_to_neighbours(self):
        lines = [{"start": 5.0, "end": 12.0, "words": []}]
        reconcile_region_boundaries(lines, prev_end=6.0, next_start=10.0)
        assert lines[0]["start"] == 6.0
        assert lines[0]["end"] == 10.0

    def test_align_words_from_segments_matches(self):
        words = align_words_from_segments(
            "The LORD called my name",
            matched_segments=[0],
            segments=[_backing_phrase(358.0)],
            line_start=358.0,
            line_end=361.0,
        )
        assert [w["word"] for w in words] == ["The", "LORD", "called", "my", "name"]
        assert words[0]["start"] == 358.0
        assert words[-1]["end"] == 361.0
        assert all(w["source"] == "transcription" for w in words)

    def test_align_words_empty(self):
        assert align_words_from_segments("hi", [], []) == []


# --------------------------------------------------------------------------- #
# RealignFromStem transform
# --------------------------------------------------------------------------- #
class TestRealignFromStem:
    def test_debunches_post_hook(self, project):
        ctx = _ctx(project)
        REGISTRY.get("realign_from_stem").apply(
            ctx, {"section": "post-hook"}, {"stem": "backing_vocals"}
        )
        ov = ctx.script["timing_overrides"]
        # exactly the 5 post-hook lines realigned
        assert sorted(k for k in ov if k != "_provenance") == ["1", "2", "3", "4", "5"]

        starts = [ov[str(i)]["start"] for i in range(1, 6)]
        # no longer bunched: monotonic increasing with sane gaps
        assert starts == sorted(starts)
        assert starts[0] >= 357.0  # moved off the 355 mis-anchor
        assert all(ov[str(i)]["end"] > ov[str(i)]["start"] for i in range(1, 6))
        # each override carries 5 words with the right text
        for i in range(1, 6):
            assert [w["word"] for w in ov[str(i)]["words"]] == [
                "The", "LORD", "called", "my", "name"
            ]

    def test_provenance_recorded(self, project):
        ctx = _ctx(project)
        REGISTRY.get("realign_from_stem").apply(
            ctx, {"section": "post-hook"}, {"stem": "backing_vocals"}
        )
        prov = ctx.script["timing_overrides"]["_provenance"]
        assert prov["stem"] == "backing_vocals"
        assert all(prov["lines"][str(i)]["match_ratio"] >= 0.5 for i in range(1, 6))

    def test_lines_selector(self, project):
        ctx = _ctx(project)
        REGISTRY.get("realign_from_stem").apply(
            ctx, {"lines": [1, 2]}, {"stem": "backing_vocals"}
        )
        ov = ctx.script["timing_overrides"]
        assert sorted(k for k in ov if k != "_provenance") == ["1", "2"]

    def test_missing_stem_raises(self, project):
        ctx = _ctx(project)
        with pytest.raises(FileNotFoundError):
            REGISTRY.get("realign_from_stem").apply(
                ctx, {"section": "post-hook"}, {"stem": "lead_vocals"}
            )

    def test_no_stem_param_raises(self, project):
        ctx = _ctx(project)
        with pytest.raises(ValueError):
            REGISTRY.get("realign_from_stem").apply(ctx, {"section": "post-hook"}, {})

    def test_region_clamped_to_neighbours(self, project):
        ctx = _ctx(project)
        REGISTRY.get("realign_from_stem").apply(
            ctx, {"section": "post-hook"}, {"stem": "backing_vocals"}
        )
        ov = ctx.script["timing_overrides"]
        # outro line 6 starts at 377 -> last override must not exceed it
        assert ov["5"]["end"] <= 377.0

    def test_low_match_line_skipped(self, project):
        # Replace one synced line with text the stem never says -> low match.
        synced = _bunched_synced()
        synced["lines"][3]["text"] = "completely unrelated gibberish words here"
        ctx = ScriptContext(script=_script_with_posthook(), lyrics_synced=synced, project_dir=project)
        REGISTRY.get("realign_from_stem").apply(
            ctx, {"section": "post-hook"}, {"stem": "backing_vocals", "min_match_ratio": 0.9}
        )
        ov = ctx.script["timing_overrides"]
        prov = ov["_provenance"]["lines"]
        assert prov["3"]["skipped"] is True
        assert "3" not in {k for k in ov if k != "_provenance"}


# --------------------------------------------------------------------------- #
# Groupoid laws for the timing transform
# --------------------------------------------------------------------------- #
class TestTimingGroupoid:
    def _recipe(self):
        return Recipe(
            name="realign",
            steps=[RecipeStep(
                "realign_from_stem", {"section": "post-hook"}, {"stem": "backing_vocals"}
            )],
        )

    def test_invert_restores(self, project):
        ctx = _ctx(project)
        original = copy.deepcopy(ctx.script)
        recipe = self._recipe()
        recipe.apply(ctx, REGISTRY)
        assert "timing_overrides" in ctx.script
        recipe.invert(ctx)
        assert "timing_overrides" not in ctx.script
        assert "_transforms" not in ctx.script
        assert ctx.script == original

    def test_idempotent(self, project):
        ctx = _ctx(project)
        recipe = self._recipe()
        recipe.apply(ctx, REGISTRY)
        once = copy.deepcopy(ctx.script.get("timing_overrides"))
        recipe.apply(ctx, REGISTRY)  # inverts prior journal, re-applies
        twice = ctx.script.get("timing_overrides")
        assert once == twice


# --------------------------------------------------------------------------- #
# DistributeTimingGroups
# --------------------------------------------------------------------------- #
def _groups_project(tmp_path: Path, onsets=None) -> Path:
    """A project with a 3-word line and a timing_groups.json for it."""
    data = tmp_path / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "lyrics_synced.json").write_text(json.dumps({
        "lines": [{
            "text": "Holy is the LORD",
            "start": 4.78, "end": 7.34,
            "words": [
                {"text": "Holy", "start": 4.78, "end": 5.0},
                {"text": "is", "start": 5.0, "end": 5.5},
                {"text": "the", "start": 5.5, "end": 6.0},
                {"text": "LORD", "start": 6.0, "end": 7.34},
            ],
        }]
    }), encoding="utf-8")
    groups = {
        "kind": "human_assigned_timing_groups", "schema_version": 1,
        "groups": [
            {"synced_line_idx": 0, "word_indices": [0], "text": "Holy",
             "start": 4.78, "end": 5.0, "source": "lead_vocals", "provenance": None},
            {"synced_line_idx": 0, "word_indices": [1, 2, 3], "text": "is the LORD",
             "start": 5.0, "end": 7.34, "source": "combined_vocals", "provenance": None},
        ],
    }
    (data / "timing_groups.json").write_text(json.dumps(groups), encoding="utf-8")
    (data / "analysis.json").write_text(json.dumps({"beat_times": []}), encoding="utf-8")
    if onsets is not None:
        (data / "vocal_onsets.json").write_text(
            json.dumps({"onset_times": onsets}), encoding="utf-8")
    return tmp_path


class TestDistributeTimingGroups:
    def _ctx(self, project: Path) -> ScriptContext:
        return ScriptContext(
            script={"defaults": {}, "sections": []},
            lyrics_synced=json.loads(
                (project / "data" / "lyrics_synced.json").read_text(encoding="utf-8")),
            project_dir=project,
        )

    def test_distributes_groups_into_per_word_overrides(self, tmp_path):
        project = _groups_project(tmp_path)
        ctx = self._ctx(project)
        REGISTRY.get("distribute_timing_groups").run(ctx, None, {})

        ov = ctx.script["timing_overrides"]
        assert "0" in ov
        words = ov["0"]["words"]
        # 1 word from the single-word group + 3 from the multi-word group
        assert [w["word"] for w in words] == ["Holy", "is", "the", "LORD"]

    def test_single_word_group_keeps_its_exact_range(self, tmp_path):
        project = _groups_project(tmp_path)
        ctx = self._ctx(project)
        REGISTRY.get("distribute_timing_groups").run(ctx, None, {})

        holy = ctx.script["timing_overrides"]["0"]["words"][0]
        assert holy["start"] == 4.78 and holy["end"] == 5.0

    def test_multi_word_group_gets_distinct_per_word_ranges(self, tmp_path):
        # no onsets -> even split
        project = _groups_project(tmp_path)
        ctx = self._ctx(project)
        REGISTRY.get("distribute_timing_groups").run(ctx, None, {"snap_onsets": False})

        multi = ctx.script["timing_overrides"]["0"]["words"][1:]
        # each word has its own start; the group's end is preserved on the last word
        assert multi[-1]["end"] == 7.34
        assert len({(w["start"], w["end"]) for w in multi}) == 3
        # last word's end == group end (not an even-split boundary)
        assert multi[-1]["end"] == 7.34

    def test_onset_snapping_engages(self, tmp_path):
        # even-split points for the 3-word group 5.0-7.34 are 5.0, 5.78, 6.56.
        # place onsets just off those points but within the 0.08 tolerance.
        project = _groups_project(tmp_path, onsets=[5.05, 5.82, 6.60])
        ctx = self._ctx(project)
        REGISTRY.get("distribute_timing_groups").run(ctx, None, {"snap_onsets": True})

        multi = ctx.script["timing_overrides"]["0"]["words"][1:]
        # starts should have snapped to the onsets, away from even 5.0/5.78/6.56
        starts = [w["start"] for w in multi]
        assert starts[0] == 5.05
        assert starts[1] == 5.82
        assert starts[2] == 6.60

    def test_chronological_and_positive_duration(self, tmp_path):
        project = _groups_project(tmp_path, onsets=[5.4, 5.3, 6.9])  # 5.3 < 5.4 inversion
        ctx = self._ctx(project)
        REGISTRY.get("distribute_timing_groups").run(ctx, None, {})

        words = ctx.script["timing_overrides"]["0"]["words"]
        for i in range(1, len(words)):
            assert words[i]["start"] >= words[i - 1]["end"]
        for w in words:
            assert w["end"] > w["start"]

    def test_provenance_records_source_groups(self, tmp_path):
        project = _groups_project(tmp_path)
        ctx = self._ctx(project)
        REGISTRY.get("distribute_timing_groups").run(ctx, None, {})

        prov = ctx.script["timing_overrides"]["_provenance"]
        assert prov["source"] == "timing_groups"
        assert "0" in prov["lines"]
        assert len(prov["lines"]["0"]["groups"]) == 2

    def test_missing_groups_file_raises(self, tmp_path):
        project = tmp_path / "data"
        project.mkdir(parents=True)
        (project / "lyrics_synced.json").write_text(
            json.dumps({"lines": [{"text": "a", "start": 0, "end": 1, "words": []}]}),
            encoding="utf-8")
        ctx = ScriptContext(
            script={"defaults": {}}, lyrics_synced={"lines": [
                {"text": "a", "start": 0, "end": 1, "words": []}]},
            project_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            REGISTRY.get("distribute_timing_groups").run(ctx, None, {})
