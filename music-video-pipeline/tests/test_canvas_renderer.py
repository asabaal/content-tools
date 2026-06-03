import numpy as np
import pytest
from PIL import Image

from canvas.renderer import CanvasRenderer, render_canvas
from canvas.models import CanvasScene


class TestRenderCanvasConvenience:
    def test_basic(self):
        img = render_canvas({"objects": {"x": {
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [1.0, 1.0],
            "style": {"fill": "#FF8C00"},
        }}}, 64, 64)
        assert isinstance(img, Image.Image)
        assert img.size == (64, 64)

    def test_custom_dimensions(self):
        img = render_canvas({"objects": {}}, 320, 240)
        assert img.size == (320, 240)


class TestCanvasRendererBasic:
    def test_empty_scene(self):
        scene = CanvasScene.from_dict({"objects": {}})
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_single_shape(self):
        scene = CanvasScene.from_dict({"objects": {"rect": {
            "type": "shape", "geometry": {"shape": "rectangle"},
            "position": [0.5, 0.5], "size": [0.5, 0.5],
            "style": {"fill": "#FF8C00"},
        }}})
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        im = np.array(img)
        assert np.count_nonzero(im) > 0

    def test_base_color(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#FF0000"},
            "objects": {},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        im = np.array(img)
        assert im[0, 0, 0] > 200
        assert im[0, 0, 1] < 50
        assert im[0, 0, 2] < 50


class TestCanvasRendererLights:
    def test_single_light(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"light": {
                "type": "light", "geometry": {"shape": "radial"},
                "position": [0.5, 0.5], "size": [0.8, 0.8],
                "opacity": 1.0,
                "style": {"color": "#2E86C1", "intensity": 1.5, "softness": 1.0, "blend_mode": "add"},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        im = np.array(img)
        assert np.max(im) > 0

    def test_add_blend(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#060a14"},
            "objects": {
                "s1": {
                    "type": "light", "geometry": {"shape": "radial"},
                    "position": [0.3, 0.3], "size": [0.7, 0.7], "opacity": 0.7,
                    "style": {"color": "#2E86C1", "intensity": 1.2, "softness": 1.0, "blend_mode": "add"},
                },
                "s2": {
                    "type": "light", "geometry": {"shape": "radial"},
                    "position": [0.7, 0.7], "size": [0.7, 0.7], "opacity": 0.7,
                    "style": {"color": "#8E44AD", "intensity": 1.2, "softness": 1.0, "blend_mode": "add"},
                },
            },
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        im = np.array(img)
        assert np.max(im) > 0


class TestCanvasRendererShapeTypes:
    @pytest.mark.parametrize("shape", ["rectangle", "circle", "diamond", "polygon", "hexagon", "triangle"])
    def test_shape_types_render(self, shape):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"s": {
                "type": "shape",
                "geometry": {"shape": shape, "sides": 6},
                "position": [0.5, 0.5], "size": [0.5, 0.5],
                "style": {"fill": "#FF8C00", "blend_mode": "add"},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        im = np.array(img)
        assert np.max(im) > 0


class TestCanvasRendererMotion:
    def test_motion_changes_over_time(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"light": {
                "type": "light", "geometry": {"shape": "radial"},
                "position": [0.5, 0.5], "size": [0.5, 0.5], "opacity": 1.0,
                "style": {"color": "#2E86C1", "intensity": 1.0, "softness": 1.0, "blend_mode": "add"},
                "motion": {"type": "drift", "speed": 1.0, "amplitude": 0.1},
            }},
        })
        r = CanvasRenderer(64, 64)
        img0 = np.array(r.render_scene(scene, t=0.0))
        img1 = np.array(r.render_scene(scene, t=1.0))
        assert not np.array_equal(img0, img1)


class TestCanvasRendererRepetition:
    def test_grid_repeat(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"dots": {
                "type": "shape", "geometry": {"shape": "circle"},
                "position": [0.5, 0.5], "size": [0.05, 0.05],
                "style": {"fill": "#FF8C00", "blend_mode": "add"},
                "repeat": {"mode": "grid", "rows": 3, "cols": 3, "spacing": 0.15},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        im = np.array(img)
        assert np.max(im) > 0


class TestCanvasRendererGlow:
    def test_glow_produces_output(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"s": {
                "type": "shape", "geometry": {"shape": "rectangle"},
                "position": [0.5, 0.5], "size": [0.2, 0.2],
                "style": {"fill": "#FF8C00", "blend_mode": "add",
                          "glow": "#FF8C00", "glow_radius": 15, "glow_intensity": 1.0},
            }},
        })
        r = CanvasRenderer(128, 128)
        img = r.render_scene(scene)
        im = np.array(img)
        assert np.max(im) > 0


class TestCanvasRendererBlur:
    def test_blur_smooths(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"s": {
                "type": "shape", "geometry": {"shape": "rectangle"},
                "position": [0.5, 0.5], "size": [0.1, 0.1],
                "style": {"fill": "#FFFFFF", "blend_mode": "add", "blur": 5.0},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)


class TestCanvasRendererGroups:
    def test_group_renders_children(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {
                "g": {"type": "group", "children": ["a", "b"]},
                "a": {
                    "type": "shape", "geometry": {"shape": "circle"},
                    "position": [0.3, 0.5], "size": [0.1, 0.1],
                    "style": {"fill": "#FF0000", "blend_mode": "add"},
                },
                "b": {
                    "type": "shape", "geometry": {"shape": "circle"},
                    "position": [0.7, 0.5], "size": [0.1, 0.1],
                    "style": {"fill": "#0000FF", "blend_mode": "add"},
                },
            },
            "layers": ["g"],
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        im = np.array(img)
        assert np.max(im) > 0


class TestCanvasRendererGroup:
    def test_group_with_missing_child(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {
                "g": {
                    "type": "group",
                    "children": ["missing_child"],
                    "position": [0.5, 0.5], "size": [0.5, 0.5],
                    "style": {},
                },
            },
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)


class TestCanvasRendererPath:
    def test_path_type_renders(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"p": {
                "type": "path",
                "geometry": {"points": [[0.2, 0.2], [0.8, 0.8]], "closed": False},
                "position": [0.5, 0.5], "size": [1.0, 1.0],
                "style": {"stroke": "#FFFFFF", "stroke_width": 2, "fill": "none"},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)


class TestCanvasRendererUnknownObject:
    def test_unknown_type_skipped(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#FF0000"},
            "objects": {"x": {"type": "nonexistent"}},
            "layers": ["x"],
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        im = np.array(img)
        assert np.all(im[:, :, 0] > 200)


class TestCanvasRendererGradient:
    def test_gradient_object(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"g": {
                "type": "gradient",
                "geometry": {"direction": "horizontal"},
                "position": [0.5, 0.5], "size": [1.0, 1.0], "opacity": 1.0,
                "style": {"colors": ["#FF0000", "#0000FF"]},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        im = np.array(img)
        assert np.max(im) > 0


class TestCanvasRendererSceneDimensions:
    def test_scene_override_dimensions(self):
        scene = CanvasScene.from_dict({
            "canvas": {"width": 320, "height": 240},
            "objects": {},
        })
        r = CanvasRenderer(640, 480)
        img = r.render_scene(scene)
        assert img.size == (320, 240)

    def test_renderer_default_dimensions(self):
        scene = CanvasScene.from_dict({"objects": {}})
        r = CanvasRenderer(100, 100)
        img = r.render_scene(scene)
        assert img.size == (100, 100)


class TestCanvasRendererTexture:
    def test_noise_texture(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"t": {
                "type": "texture",
                "geometry": {"noise_type": "noise", "seed": 42},
                "opacity": 0.5,
                "style": {},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_paper_texture(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"t": {
                "type": "texture",
                "geometry": {"noise_type": "paper", "seed": 1},
                "opacity": 0.5,
                "style": {},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_film_texture(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"t": {
                "type": "texture",
                "geometry": {"noise_type": "film", "seed": 7},
                "opacity": 0.5,
                "style": {},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_grain_texture(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"t": {
                "type": "texture",
                "geometry": {"noise_type": "grain", "seed": 3},
                "opacity": 0.5,
                "style": {},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_int_opacity(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"t": {
                "type": "texture",
                "geometry": {"noise_type": "noise", "seed": 42},
                "opacity": 1,
                "style": {},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)


class TestCanvasRendererMask:
    def test_rect_mask(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {
                "rect": {
                    "type": "shape", "geometry": {"shape": "rectangle"},
                    "position": [0.5, 0.5], "size": [0.8, 0.8],
                    "style": {"fill": "#FF8C00", "blend_mode": "add"},
                    "mask": "m",
                },
                "m": {
                    "type": "mask", "geometry": {"shape": "rectangle"},
                    "position": [0.5, 0.5], "size": [0.3, 0.3],
                    "opacity": 1.0, "style": {},
                },
            },
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_circle_mask(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {
                "rect": {
                    "type": "shape", "geometry": {"shape": "rectangle"},
                    "position": [0.5, 0.5], "size": [0.8, 0.8],
                    "style": {"fill": "#FF8C00", "blend_mode": "add"},
                    "mask": "m",
                },
                "m": {
                    "type": "mask", "geometry": {"shape": "circle"},
                    "position": [0.5, 0.5], "size": [0.3, 0.3],
                    "opacity": 1.0, "style": {},
                },
            },
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_gradient_mask_vertical(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {
                "rect": {
                    "type": "shape", "geometry": {"shape": "rectangle"},
                    "position": [0.5, 0.5], "size": [0.8, 0.8],
                    "style": {"fill": "#FF8C00", "blend_mode": "add"},
                    "mask": "m",
                },
                "m": {
                    "type": "mask", "geometry": {"shape": "gradient", "direction": "vertical"},
                    "position": [0.5, 0.5], "size": [1.0, 1.0],
                    "opacity": 1.0, "style": {},
                },
            },
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_gradient_mask_horizontal(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {
                "rect": {
                    "type": "shape", "geometry": {"shape": "rectangle"},
                    "position": [0.5, 0.5], "size": [0.8, 0.8],
                    "style": {"fill": "#FF8C00", "blend_mode": "add"},
                    "mask": "m",
                },
                "m": {
                    "type": "mask", "geometry": {"shape": "gradient", "direction": "horizontal"},
                    "position": [0.5, 0.5], "size": [1.0, 1.0],
                    "opacity": 1.0, "style": {},
                },
            },
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_mask_with_opacity(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {
                "rect": {
                    "type": "shape", "geometry": {"shape": "rectangle"},
                    "position": [0.5, 0.5], "size": [0.8, 0.8],
                    "style": {"fill": "#FF8C00", "blend_mode": "add"},
                    "mask": "m",
                },
                "m": {
                    "type": "mask", "geometry": {"shape": "rectangle"},
                    "position": [0.5, 0.5], "size": [0.5, 0.5],
                    "opacity": 0.5, "style": {},
                },
            },
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_mask_ref_missing_skips(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {
                "rect": {
                    "type": "shape", "geometry": {"shape": "rectangle"},
                    "position": [0.5, 0.5], "size": [0.8, 0.8],
                    "style": {"fill": "#FF8C00", "blend_mode": "add"},
                    "mask": "nonexistent",
                },
            },
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)


class TestCanvasRendererImage:
    def test_missing_path_returns_none(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"img": {
                "type": "image",
                "geometry": {"src": "/nonexistent/path.png"},
                "style": {},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_empty_path_returns_none(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"img": {
                "type": "image",
                "geometry": {},
                "style": {},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_valid_image(self, tmp_path):
        img_path = tmp_path / "test.png"
        Image.new("RGBA", (32, 32), (255, 128, 0, 255)).save(img_path)
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"img": {
                "type": "image",
                "geometry": {"src": str(img_path)},
                "style": {},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)

    def test_corrupt_image_returns_none(self, tmp_path):
        img_path = tmp_path / "corrupt.png"
        img_path.write_bytes(b"NOT A REAL IMAGE DATA")
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"img": {
                "type": "image",
                "geometry": {"src": str(img_path)},
                "style": {},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)
    def test_rotated_shape(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#000000"},
            "objects": {"s": {
                "type": "shape", "geometry": {"shape": "rectangle"},
                "position": [0.5, 0.5], "size": [0.3, 0.1],
                "rotation": 45.0,
                "style": {"fill": "#FF8C00", "blend_mode": "add"},
            }},
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        assert img.size == (64, 64)


class TestCanvasRendererMissingLayer:
    def test_missing_layer_object_skipped(self):
        scene = CanvasScene.from_dict({
            "canvas": {"base_color": "#FF0000"},
            "objects": {},
            "layers": ["missing"],
        })
        r = CanvasRenderer(64, 64)
        img = r.render_scene(scene)
        im = np.array(img)
        assert np.all(im[:, :, 0] > 200)


class TestHexToRgb:
    def test_6char(self):
        from canvas.renderer import _hex_to_rgb
        assert _hex_to_rgb("#FF8C00") == (255, 140, 0)

    def test_3char(self):
        from canvas.renderer import _hex_to_rgb
        assert _hex_to_rgb("#F80") == (255, 136, 0)

    def test_no_hash(self):
        from canvas.renderer import _hex_to_rgb
        assert _hex_to_rgb("FF8C00") == (255, 140, 0)


class TestMergeGroupTransform:
    def test_merges_rotation_and_opacity(self):
        from canvas.renderer import _merge_group_transform
        from canvas.models import CanvasObject
        child = CanvasObject.from_dict({
            "type": "shape", "geometry": {"shape": "rectangle"},
            "rotation": 10.0, "opacity": 0.8,
        })
        group_motion = {"rotation": 5.0, "opacity": 0.5}
        merged = _merge_group_transform(child, group_motion, 640, 360)
        assert merged.rotation == 15.0
        assert abs(merged.opacity - 0.4) < 0.001
