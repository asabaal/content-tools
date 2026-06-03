import pytest

from canvas.models import CanvasObject, CanvasScene, _parse_position, _parse_size, _resolve_color


class TestResolveColor:
    def test_plain_hex(self):
        assert _resolve_color("#FF8C00", {}) == "#FF8C00"

    def test_palette_ref(self):
        assert _resolve_color("$primary", {"primary": "#2E86C1"}) == "#2E86C1"

    def test_missing_palette_key(self):
        assert _resolve_color("$missing", {"primary": "#FF0000"}) == "$missing"

    def test_no_dollar_prefix(self):
        assert _resolve_color("red", {}) == "red"

    def test_empty_palette(self):
        assert _resolve_color("$primary", {}) == "$primary"

    def test_none_palette(self):
        assert _resolve_color("#FFFFFF", None) == "#FFFFFF"

    def test_nested_palette(self):
        palette = {"a": "#111111", "b": "$a"}
        assert _resolve_color("$b", palette) == "$a"


class TestParsePosition:
    def test_none_returns_center(self):
        assert _parse_position(None, 640, 360) == (320.0, 180.0)

    def test_tuple_proportional(self):
        assert _parse_position((0.5, 0.5), 640, 360) == (320.0, 180.0)

    def test_tuple_absolute(self):
        assert _parse_position((100, 200), 640, 360) == (100.0, 200.0)

    def test_tuple_mixed(self):
        x, y = _parse_position((0.5, 200), 640, 360)
        assert x == 0.5
        assert y == 200.0

    def test_tuple_zero(self):
        assert _parse_position((0.0, 0.0), 640, 360) == (0.0, 0.0)

    def test_dict_x_y(self):
        assert _parse_position({"x": 0.25, "y": 0.75}, 640, 360) == (160.0, 270.0)

    def test_scalar_proportional(self):
        x, y = _parse_position(0.5, 640, 360)
        assert x == 320.0
        assert y == 180.0

    def test_scalar_absolute(self):
        x, y = _parse_position(100, 640, 360)
        assert x == 100.0
        assert y == 100.0

    def test_scalar_zero(self):
        x, y = _parse_position(0, 640, 360)
        assert x == 0.0
        assert y == 0.0

    def test_list_input(self):
        assert _parse_position([0.3, 0.7], 640, 360) == (192.0, pytest.approx(252.0))

    def test_full_range(self):
        assert _parse_position((1.0, 1.0), 640, 360) == (640.0, 360.0)


class TestParseSize:
    def test_none_returns_full(self):
        assert _parse_size(None, 640, 360) == (640.0, 360.0)

    def test_proportional(self):
        assert _parse_size((0.5, 0.5), 640, 360) == (320.0, 180.0)

    def test_absolute(self):
        assert _parse_size((100, 200), 640, 360) == (100.0, 200.0)

    def test_dict_w_h(self):
        assert _parse_size({"w": 0.25, "h": 0.75}, 640, 360) == (160.0, 270.0)


class TestCanvasObject:
    def test_from_dict_minimal(self):
        obj = CanvasObject.from_dict({"type": "shape"})
        assert obj.type == "shape"
        assert obj.geometry == {}
        assert obj.position is None
        assert obj.size is None
        assert obj.rotation == 0.0
        assert obj.opacity == 1.0
        assert obj.style == {}
        assert obj.motion == {}
        assert obj.repeat == {}
        assert obj.mask is None
        assert obj.timing == {}
        assert obj.children == []

    def test_from_dict_full(self):
        data = {
            "type": "light",
            "geometry": {"shape": "radial"},
            "position": [0.5, 0.5],
            "size": [0.8, 0.8],
            "rotation": 45.0,
            "opacity": 0.7,
            "style": {"color": "#FF0000", "blend_mode": "screen"},
            "motion": {"type": "drift", "speed": 0.1},
            "repeat": {"mode": "grid", "rows": 3, "cols": 3},
            "mask": "mask1",
            "timing": {"start": 0, "end": 10},
            "children": ["child1", "child2"],
        }
        obj = CanvasObject.from_dict(data)
        assert obj.type == "light"
        assert obj.geometry == {"shape": "radial"}
        assert obj.position == [0.5, 0.5]
        assert obj.size == [0.8, 0.8]
        assert obj.rotation == 45.0
        assert obj.opacity == 0.7
        assert obj.style["color"] == "#FF0000"
        assert obj.motion["type"] == "drift"
        assert obj.repeat["mode"] == "grid"
        assert obj.mask == "mask1"
        assert obj.timing == {"start": 0, "end": 10}
        assert obj.children == ["child1", "child2"]

    def test_from_dict_does_not_mutate_input(self):
        data = {"type": "shape"}
        obj = CanvasObject.from_dict(data)
        obj.style["color"] = "red"
        assert "color" not in data


class TestCanvasScene:
    def test_from_dict_minimal(self):
        scene = CanvasScene.from_dict({"objects": {"x": {"type": "shape"}}})
        assert "x" in scene.objects
        assert isinstance(scene.objects["x"], CanvasObject)
        assert scene.layers == ["x"]

    def test_from_dict_with_layers(self):
        scene = CanvasScene.from_dict({
            "objects": {"a": {"type": "shape"}, "b": {"type": "light"}},
            "layers": ["b", "a"],
        })
        assert scene.layers == ["b", "a"]

    def test_from_dict_with_canvas(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"x": {"type": "shape"}},
        })
        assert scene.canvas == {"base_color": "#000000"}

    def test_from_dict_with_palette(self):
        scene = CanvasScene.from_dict({
            "palette": {"primary": "#FF0000"},
            "objects": {"x": {"type": "shape"}},
        })
        assert scene.palette == {"primary": "#FF0000"}

    def test_default_canvas_empty(self):
        scene = CanvasScene.from_dict({"objects": {}})
        assert isinstance(scene.canvas, dict)

    def test_get_object_found(self):
        scene = CanvasScene.from_dict({"objects": {"x": {"type": "shape"}}})
        assert scene.get_object("x") is not None
        assert scene.get_object("x").type == "shape"

    def test_get_object_missing(self):
        scene = CanvasScene.from_dict({"objects": {}})
        assert scene.get_object("missing") is None

    def test_width_property(self):
        scene = CanvasScene.from_dict({"canvas": {"width": 800}, "objects": {}})
        assert scene.width == 800

    def test_height_property(self):
        scene = CanvasScene.from_dict({"canvas": {"height": 600}, "objects": {}})
        assert scene.height == 600

    def test_base_color_property(self):
        scene = CanvasScene.from_dict({"canvas": {"base_color": "#ABCDEF"}, "objects": {}})
        assert scene.base_color == "#ABCDEF"

    def test_text_safety(self):
        scene = CanvasScene.from_dict({
            "text_safety": {"mode": "dim_center"},
            "objects": {},
        })
        assert scene.text_safety["mode"] == "dim_center"

    def test_from_dict_empty_objects(self):
        scene = CanvasScene.from_dict({"objects": {}})
        assert scene.objects == {}
        assert scene.layers == []


class TestParseSizeScalar:
    def test_scalar_proportional(self):
        x, y = _parse_size(0.5, 640, 360)
        assert x == 320.0
        assert y == 180.0

    def test_scalar_absolute(self):
        x, y = _parse_size(200, 640, 360)
        assert x == 200.0
        assert y == 200.0
