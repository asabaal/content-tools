import numpy as np
import pytest

from canvas.loader import (
    VALID_OBJECT_TYPES,
    VALID_BLEND_MODES,
    VALID_MOTION_TYPES,
    VALID_REPEAT_MODES,
    validate_scene,
    load_scene,
    ValidationError,
)


class TestValidateSceneValid:
    def test_minimal_valid(self):
        errors = validate_scene({"objects": {"x": {"type": "shape"}}})
        assert errors == []

    def test_full_valid(self):
        errors = validate_scene({
            "canvas": {"base_color": "#000"},
            "palette": {"primary": "#FF0000"},
            "layers": ["obj1"],
            "objects": {
                "obj1": {
                    "type": "shape",
                    "style": {"blend_mode": "screen"},
                    "motion": {"type": "drift"},
                    "repeat": {"mode": "grid"},
                },
            },
        })
        assert errors == []


class TestValidateSceneInvalidInput:
    def test_non_dict(self):
        errors = validate_scene("not a dict")
        assert len(errors) > 0
        assert "dictionary" in errors[0].lower()

    def test_objects_not_dict(self):
        errors = validate_scene({"objects": "not a dict"})
        assert len(errors) > 0
        assert "objects" in errors[0].lower()

    def test_missing_objects_passes(self):
        errors = validate_scene({"layers": []})
        assert isinstance(errors, list)

    def test_missing_type_passes(self):
        errors = validate_scene({"objects": {"x": {}}})
        assert isinstance(errors, list)


class TestValidateSceneObjectTypes:
    @pytest.mark.parametrize("obj_type", VALID_OBJECT_TYPES)
    def test_valid_object_types(self, obj_type):
        errors = validate_scene({"objects": {"x": {"type": obj_type}}})
        assert errors == []

    def test_invalid_object_type(self):
        errors = validate_scene({"objects": {"x": {"type": "nonexistent"}}})
        assert any("type" in e.lower() for e in errors)

    def test_missing_type_validates(self):
        errors = validate_scene({"objects": {"x": {}}})
        assert isinstance(errors, list)


class TestValidateSceneBlendModes:
    @pytest.mark.parametrize("mode", VALID_BLEND_MODES)
    def test_valid_blend_modes(self, mode):
        errors = validate_scene({
            "objects": {"x": {"type": "shape", "style": {"blend_mode": mode}}},
        })
        assert errors == []

    def test_invalid_blend_mode(self):
        errors = validate_scene({
            "objects": {"x": {"type": "shape", "style": {"blend_mode": "bad_mode"}}},
        })
        assert any("blend" in e.lower() for e in errors)


class TestValidateSceneMotionTypes:
    @pytest.mark.parametrize("mtype", VALID_MOTION_TYPES)
    def test_valid_motion_types(self, mtype):
        errors = validate_scene({
            "objects": {"x": {"type": "shape", "motion": {"type": mtype}}},
        })
        assert errors == []

    def test_invalid_motion_type(self):
        errors = validate_scene({
            "objects": {"x": {"type": "shape", "motion": {"type": "fly"}}},
        })
        assert any("motion" in e.lower() for e in errors)


class TestValidateSceneRepeatModes:
    @pytest.mark.parametrize("mode", VALID_REPEAT_MODES)
    def test_valid_repeat_modes(self, mode):
        errors = validate_scene({
            "objects": {"x": {"type": "shape", "repeat": {"mode": mode}}},
        })
        assert errors == []

    def test_invalid_repeat_mode(self):
        errors = validate_scene({
            "objects": {"x": {"type": "shape", "repeat": {"mode": "spiral_repeat"}}},
        })
        assert any("repeat" in e.lower() for e in errors)


class TestValidateSceneReferences:
    def test_layer_missing_object(self):
        errors = validate_scene({
            "objects": {"x": {"type": "shape"}},
            "layers": ["x", "missing"],
        })
        assert any("missing" in e for e in errors)

    def test_mask_reference_missing(self):
        errors = validate_scene({
            "objects": {"x": {"type": "shape", "mask": "no_such_mask"}},
        })
        assert any("mask" in e.lower() for e in errors)

    def test_children_reference_missing(self):
        errors = validate_scene({
            "objects": {"g": {"type": "group", "children": ["missing_child"]}},
        })
        assert any("child" in e.lower() for e in errors)

    def test_valid_references(self):
        errors = validate_scene({
            "objects": {
                "m": {"type": "mask"},
                "x": {"type": "shape", "mask": "m"},
                "g": {"type": "group", "children": ["x"]},
            },
            "layers": ["g"],
        })
        assert errors == []


class TestLoadScene:
    def test_valid_returns_scene(self):
        from canvas.models import CanvasScene
        scene = load_scene({"objects": {"x": {"type": "shape"}}})
        assert isinstance(scene, CanvasScene)

    def test_invalid_raises(self):
        with pytest.raises(ValidationError):
            load_scene("not a dict")


class TestConstants:
    def test_object_types(self):
        assert "shape" in VALID_OBJECT_TYPES
        assert "light" in VALID_OBJECT_TYPES
        assert "group" in VALID_OBJECT_TYPES

    def test_blend_modes(self):
        assert "normal" in VALID_BLEND_MODES
        assert "screen" in VALID_BLEND_MODES

    def test_motion_types(self):
        assert "drift" in VALID_MOTION_TYPES
        assert "rotate" in VALID_MOTION_TYPES

    def test_repeat_modes(self):
        assert "grid" in VALID_REPEAT_MODES
        assert "none" in VALID_REPEAT_MODES


class TestValidateSceneObjectFormat:
    def test_non_dict_object_value(self):
        errors = validate_scene({"objects": {"x": "not a dict"}})
        assert any("must be a dictionary" in e for e in errors)
