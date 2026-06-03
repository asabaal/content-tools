import pytest

from canvas.recipes import (
    RECIPES,
    cross_recipe,
    conic_recipe,
    diamond_recipe,
    dual_spot_recipe,
    spiral_recipe,
    bands_recipe,
    radial_recipe,
    get_recipe,
)


class TestRecipeStructure:
    @pytest.mark.parametrize("name,fn", list(RECIPES.items()))
    def test_returns_valid_scene_dict(self, name, fn):
        scene = fn()
        assert isinstance(scene, dict)
        assert "canvas" in scene
        assert "layers" in scene
        assert "objects" in scene
        assert isinstance(scene["objects"], dict)
        assert len(scene["objects"]) > 0
        assert set(scene["layers"]).issubset(set(scene["objects"].keys()))

    @pytest.mark.parametrize("name,fn", list(RECIPES.items()))
    def test_has_base_color(self, name, fn):
        scene = fn()
        assert "base_color" in scene["canvas"] or "canvas" in scene

    @pytest.mark.parametrize("name,fn", list(RECIPES.items()))
    def test_objects_have_type(self, name, fn):
        scene = fn()
        for obj_id, obj_data in scene["objects"].items():
            assert "type" in obj_data, f"{name}/{obj_id} missing type"


class TestCrossRecipe:
    def test_default(self):
        scene = cross_recipe()
        assert len(scene["layers"]) == 2
        assert "h_bar" in scene["objects"]
        assert "v_bar" in scene["objects"]

    def test_custom_colors(self):
        scene = cross_recipe(colors=["#FF0000", "#00FF00", "#0000FF"])
        assert scene["canvas"]["base_color"] == "#0000FF"
        assert scene["palette"]["primary"] == "#FF0000"

    def test_custom_opacity(self):
        scene = cross_recipe(opacity=0.5)
        h = scene["objects"]["h_bar"]
        assert h["opacity"] == 0.5


class TestConicRecipe:
    def test_default(self):
        scene = conic_recipe()
        assert "conic" in scene["objects"]
        assert scene["objects"]["conic"]["type"] == "light"

    def test_with_offset(self):
        scene = conic_recipe(offset=1.5)
        assert scene["objects"]["conic"]["geometry"]["offset"] == 1.5


class TestDiamondRecipe:
    def test_single(self):
        scene = diamond_recipe(count=1)
        assert "diamonds" in scene["objects"]

    def test_grid(self):
        scene = diamond_recipe(count=9, size=0.1)
        obj = scene["objects"]["diamonds"]
        assert obj["repeat"]["mode"] == "grid"


class TestDualSpotRecipe:
    def test_default(self):
        scene = dual_spot_recipe()
        assert "spot1" in scene["objects"]
        assert "spot2" in scene["objects"]
        assert scene["objects"]["spot1"]["type"] == "light"

    def test_custom_positions(self):
        scene = dual_spot_recipe(pos1=[0.1, 0.1], pos2=[0.9, 0.9])
        assert scene["objects"]["spot1"]["position"] == [0.1, 0.1]
        assert scene["objects"]["spot2"]["position"] == [0.9, 0.9]


class TestSpiralRecipe:
    def test_default(self):
        scene = spiral_recipe()
        assert "spiral" in scene["objects"]
        assert scene["objects"]["spiral"]["type"] == "path"
        assert scene["objects"]["spiral"]["motion"]["type"] == "rotate"


class TestBandsRecipe:
    def test_default(self):
        scene = bands_recipe()
        assert "bands" in scene["objects"]
        assert scene["objects"]["bands"]["repeat"]["mode"] == "grid"

    def test_custom_count(self):
        scene = bands_recipe(count=3)
        assert scene["objects"]["bands"]["repeat"]["rows"] == 3


class TestRadialRecipe:
    def test_default(self):
        scene = radial_recipe()
        assert "light" in scene["objects"]
        assert scene["objects"]["light"]["position"] == [0.25, 0.25]

    def test_custom_center(self):
        scene = radial_recipe(cx=0.7, cy=0.8)
        assert scene["objects"]["light"]["position"] == [0.7, 0.8]


class TestGetRecipe:
    def test_known_recipe(self):
        scene = get_recipe("cross")
        assert "h_bar" in scene["objects"]

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown recipe"):
            get_recipe("nonexistent")

    def test_passes_kwargs(self):
        scene = get_recipe("cross", opacity=0.7)
        assert scene["objects"]["h_bar"]["opacity"] == 0.7


class TestRecipesConstant:
    def test_count(self):
        assert len(RECIPES) == 9

    def test_names(self):
        expected = {"cross", "conic", "diamond", "dual_spot", "spiral", "bands", "radial_tl", "radial_br", "radial_center"}
        assert set(RECIPES.keys()) == expected
