import bpy
import os
import sys
import json
import math
import argparse
from datetime import datetime
from mathutils import Vector


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="3D Asset Preview Renderer")
    parser.add_argument("--asset", required=True, help="Path to .glb/.gltf/.obj/.fbx/.blend file")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--material-mode", default="original",
                        choices=["original", "clay", "normal", "wireframe"])
    parser.add_argument("--resolution", type=int, default=1024)
    parser.add_argument("--engine", default="eevee", choices=["eevee", "cycles"])
    parser.add_argument("--transparent", action="store_true")
    parser.add_argument("--save-blend", action="store_true")
    parser.add_argument("--turntable", action="store_true")
    parser.add_argument("--views", default="front,side,back,three_quarter,top",
                        help="Comma-separated view list")
    return parser.parse_args(argv)


def resolve_path(path, project_root):
    if os.path.isabs(path):
        return os.path.normpath(path)
    return os.path.normpath(os.path.join(project_root, path))


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)
    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action)


def import_asset(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=filepath)
    elif ext == ".obj":
        try:
            bpy.ops.wm.obj_import(filepath=filepath)
        except AttributeError:
            bpy.ops.import_scene.obj(filepath=filepath)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=filepath)
    elif ext == ".blend":
        bpy.ops.wm.open_mainfile(filepath=filepath)
    else:
        raise ValueError(f"Unsupported format: {ext}")
    return ext


def get_mesh_objects():
    return [obj for obj in bpy.data.objects if obj.type == "MESH"]


def compute_bounds(mesh_objects):
    all_min = [float("inf")] * 3
    all_max = [float("-inf")] * 3
    for obj in mesh_objects:
        for corner in obj.bound_box:
            world_co = obj.matrix_world @ Vector(corner)
            for i in range(3):
                all_min[i] = min(all_min[i], world_co[i])
                all_max[i] = max(all_max[i], world_co[i])
    return all_min, all_max


def center_and_normalize(mesh_objects, all_min, all_max):
    center = [(all_min[i] + all_max[i]) / 2 for i in range(3)]
    dimensions = [all_max[i] - all_min[i] for i in range(3)]
    max_dim = max(dimensions) if max(dimensions) > 0 else 1.0

    for obj in mesh_objects:
        obj.location.x -= center[0]
        obj.location.y -= center[1]
        obj.location.z -= center[2]

    scale_factor = 2.0 / max_dim
    bpy.ops.object.select_all(action="DESELECT")
    for obj in mesh_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0] if mesh_objects else None
    bpy.ops.transform.resize(value=(scale_factor, scale_factor, scale_factor))
    bpy.ops.object.select_all(action="DESELECT")

    return dimensions, scale_factor


def create_clay_material():
    mat = bpy.data.materials.new(name="Preview_Clay")
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                bsdf = n
                break
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.75, 0.75, 0.75, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.8
    return mat


def create_normal_material():
    mat = bpy.data.materials.new(name="Preview_Normal")
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output_node = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.3, 0.3, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.5

    geo = nodes.new("ShaderNodeNewGeometry")

    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geo.outputs["Normal"], sep.inputs[0])

    comb = nodes.new("ShaderNodeCombineXYZ")
    links.new(sep.outputs[0], comb.inputs[0])
    links.new(sep.outputs[1], comb.inputs[1])
    links.new(sep.outputs[2], comb.inputs[2])

    ramp = nodes.new("ShaderNodeValToRGB")
    links.new(comb.outputs[0], ramp.inputs[0])
    links.new(ramp.outputs[0], bsdf.inputs["Base Color"])

    links.new(bsdf.outputs["BSDF"], output_node.inputs["Surface"])

    return mat


def apply_wireframe_override():
    scene = bpy.context.scene
    scene.render.use_freestyle = True
    settings = scene.view_layers[0].freestyle_settings
    settings.linesets.clear()
    lineset = settings.linesets.new("WireframeLines")
    lineset.select_silhouette = False
    lineset.select_border = False
    lineset.select_crease = False
    lineset.select_suggestive_contour = False
    lineset.select_ridge_valley = False
    lineset.select_edge_mark = False
    lineset.select_contour = True
    lineset.select_external_contour = True
    for line_style in [lineset.linestyle]:
        line_style.color = (0.0, 0.0, 0.0)
    return True


def apply_material_mode(mode, mesh_objects):
    warnings = []
    if mode == "original":
        return warnings
    elif mode == "clay":
        mat = create_clay_material()
        for obj in mesh_objects:
            for i in range(len(obj.data.materials)):
                obj.data.materials[i] = mat
            if len(obj.data.materials) == 0:
                obj.data.materials.append(mat)
    elif mode == "normal":
        try:
            mat = create_normal_material()
            for obj in mesh_objects:
                for i in range(len(obj.data.materials)):
                    obj.data.materials[i] = mat
                if len(obj.data.materials) == 0:
                    obj.data.materials.append(mat)
        except Exception:
            print("WARNING: Normal material mode not practical, falling back to clay.")
            warnings.append("Normal material mode not practical, fell back to clay.")
            mat = create_clay_material()
            for obj in mesh_objects:
                for i in range(len(obj.data.materials)):
                    obj.data.materials[i] = mat
                if len(obj.data.materials) == 0:
                    obj.data.materials.append(mat)
    elif mode == "wireframe":
        try:
            apply_wireframe_override()
            mat = create_clay_material()
            mat.diffuse_color = (0.95, 0.95, 0.95, 1.0)
            for obj in mesh_objects:
                for i in range(len(obj.data.materials)):
                    obj.data.materials[i] = mat
                if len(obj.data.materials) == 0:
                    obj.data.materials.append(mat)
        except Exception:
            print("WARNING: Wireframe mode not practical, falling back to clay.")
            warnings.append("Wireframe mode not practical, fell back to clay.")
            mat = create_clay_material()
            for obj in mesh_objects:
                for i in range(len(obj.data.materials)):
                    obj.data.materials[i] = mat
                if len(obj.data.materials) == 0:
                    obj.data.materials.append(mat)
    return warnings


def check_missing_textures(mesh_objects):
    has_geometry = len(mesh_objects) > 0
    has_images = False
    for obj in mesh_objects:
        for slot in obj.material_slots:
            if slot.material and slot.material.node_tree:
                for node in slot.material.node_tree.nodes:
                    if node.type == "TEX_IMAGE" and node.image:
                        has_images = True
                        break
            if has_images:
                break
        if has_images:
            break
    warning = None
    if has_geometry and not has_images:
        warning = "Asset appears to have geometry but no texture images/material textures."
        print(f"WARNING: {warning}")
    return warning


def add_camera():
    cam_data = bpy.data.cameras.new("PreviewCamera")
    cam_obj = bpy.data.objects.new("PreviewCamera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    return cam_obj


def add_studio_lights():
    key = bpy.data.lights.new("KeyLight", type="AREA")
    key.energy = 800
    key.size = 5.0
    key_obj = bpy.data.objects.new("KeyLight", key)
    key_obj.location = (3, -3, 4)
    bpy.context.collection.objects.link(key_obj)

    fill = bpy.data.lights.new("FillLight", type="AREA")
    fill.energy = 400
    fill.size = 5.0
    fill_obj = bpy.data.objects.new("FillLight", fill)
    fill_obj.location = (-3, -2, 2)
    bpy.context.collection.objects.link(fill_obj)

    rim = bpy.data.lights.new("RimLight", type="AREA")
    rim.energy = 300
    rim.size = 3.0
    rim_obj = bpy.data.objects.new("RimLight", rim)
    rim_obj.location = (0, 4, 3)
    bpy.context.collection.objects.link(rim_obj)


def set_camera_for_view(cam_obj, view_name, distance=3.5):
    if view_name == "front":
        cam_obj.location = (0, -distance, 0)
        cam_obj.rotation_euler = (math.radians(90), 0, 0)
    elif view_name == "side":
        cam_obj.location = (distance, 0, 0)
        cam_obj.rotation_euler = (math.radians(90), 0, math.radians(-90))
    elif view_name == "back":
        cam_obj.location = (0, distance, 0)
        cam_obj.rotation_euler = (math.radians(90), 0, math.radians(180))
    elif view_name == "three_quarter":
        cam_obj.location = (distance * 0.7, -distance * 0.7, distance * 0.5)
        direction = -cam_obj.location.normalized()
        cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    elif view_name == "top":
        cam_obj.location = (0, 0, distance)
        cam_obj.rotation_euler = (0, 0, 0)


def render_view(cam_obj, view_name, output_dir, resolution, engine, transparent):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if engine == "eevee" else "CYCLES"
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.filepath = os.path.join(output_dir, f"{view_name}.png")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    if transparent:
        scene.render.film_transparent = True
    else:
        scene.render.film_transparent = False
    scene.render.use_freestyle = False
    try:
        bpy.ops.render.render(write_still=True)
    except RuntimeError as e:
        print(f"WARNING: Render failed for view {view_name}: {e}")
        return None
    filepath = scene.render.filepath
    if os.path.exists(filepath):
        print(f"  Rendered: {view_name}.png")
        return filepath
    return None


def create_contact_sheet(output_dir, view_paths, resolution):
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not available, skipping contact sheet.")
        return None

    valid_paths = [(name, p) for name, p in view_paths.items() if p and os.path.exists(p)]
    if not valid_paths:
        return None

    n = len(valid_paths)
    cols = min(n, 3)
    rows = math.ceil(n / cols)
    thumb_size = resolution // 2
    sheet_w = cols * thumb_size
    sheet_h = rows * thumb_size
    sheet = Image.new("RGBA" if bpy.context.scene.render.film_transparent else "RGB",
                      (sheet_w, sheet_h), (40, 40, 40, 255) if bpy.context.scene.render.film_transparent else (40, 40, 40))

    for idx, (name, path) in enumerate(valid_paths):
        img = Image.open(path).convert("RGBA" if bpy.context.scene.render.film_transparent else "RGB")
        img = img.resize((thumb_size, thumb_size), Image.LANCZOS)
        col = idx % cols
        row = idx // cols
        sheet.paste(img, (col * thumb_size, row * thumb_size))

    contact_path = os.path.join(output_dir, "contact_sheet.png")
    sheet.save(contact_path)
    print(f"  Contact sheet: contact_sheet.png")
    return contact_path


def render_turntable(cam_obj, output_dir, resolution, engine, transparent):
    frames_dir = os.path.join(output_dir, "turntable")
    os.makedirs(frames_dir, exist_ok=True)
    num_frames = 36
    distance = 3.5
    rendered = []
    for i in range(num_frames):
        angle = 2 * math.pi * i / num_frames
        cam_obj.location = (distance * math.sin(angle), -distance * math.cos(angle), distance * 0.3)
        direction = -cam_obj.location.normalized()
        cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

        scene = bpy.context.scene
        scene.render.engine = "BLENDER_EEVEE" if engine == "eevee" else "CYCLES"
        scene.render.resolution_x = resolution
        scene.render.resolution_y = resolution
        scene.render.filepath = os.path.join(frames_dir, f"frame_{i:03d}.png")
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
        scene.render.film_transparent = transparent
        scene.render.use_freestyle = False
        try:
            bpy.ops.render.render(write_still=True)
            if os.path.exists(scene.render.filepath):
                rendered.append(scene.render.filepath)
        except RuntimeError:
            pass

    print(f"  Turntable: {len(rendered)} frames rendered to turntable/")
    return rendered


def gather_asset_info(filepath, resolved_path, ext, mesh_objects, all_min, all_max, dimensions,
                      view_paths, blend_path, warnings):
    vertex_count = sum(len(obj.data.vertices) for obj in mesh_objects)
    face_count = sum(len(obj.data.polygons) for obj in mesh_objects)

    materials = set()
    images = set()
    for obj in mesh_objects:
        for slot in obj.material_slots:
            if slot.material:
                materials.add(slot.material.name)
                if slot.material.node_tree:
                    for node in slot.material.node_tree.nodes:
                        if node.type == "TEX_IMAGE" and node.image:
                            images.add(node.image.name)

    has_armature = any(obj.type == "ARMATURE" for obj in bpy.data.objects)
    has_animations = len(bpy.data.actions) > 0 or any(
        obj.animation_data and obj.animation_data.action for obj in bpy.data.objects
    )

    file_size = os.path.getsize(resolved_path) if os.path.exists(resolved_path) else 0

    report = {
        "input_asset_path": filepath,
        "resolved_asset_path": resolved_path,
        "file_extension": ext,
        "file_size_bytes": file_size,
        "file_size_human": f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024*1024):.1f} MB",
        "mesh_object_count": len(mesh_objects),
        "material_count": len(bpy.data.materials),
        "texture_image_count": len(images),
        "vertex_count": vertex_count,
        "face_polygon_count": face_count,
        "bounding_box_dimensions": {
            "x": round(dimensions[0], 4),
            "y": round(dimensions[1], 4),
            "z": round(dimensions[2], 4),
        },
        "has_armature": has_armature,
        "has_animations": has_animations,
        "material_names": sorted(materials),
        "image_names": sorted(images),
        "rendered_views": {k: os.path.basename(v) if v else None for k, v in view_paths.items()},
        "saved_blend_path": blend_path,
        "warnings": [w for w in warnings if w],
    }
    return report


def main():
    args = parse_args()
    project_root = os.getcwd()

    resolved_asset = resolve_path(args.asset, project_root)
    if not os.path.exists(resolved_asset):
        print(f"ERROR: Asset not found: {resolved_asset}")
        sys.exit(1)

    ext = os.path.splitext(resolved_asset)[1].lower()
    if ext not in (".glb", ".gltf", ".obj", ".fbx", ".blend"):
        print(f"ERROR: Unsupported format: {ext}")
        sys.exit(1)

    if args.output_dir:
        output_dir = resolve_path(args.output_dir, project_root)
    else:
        stem = os.path.splitext(os.path.basename(resolved_asset))[0]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(project_root, "outputs", f"{stem}_{ts}")

    os.makedirs(output_dir, exist_ok=True)
    print(f"Asset: {resolved_asset}")
    print(f"Output: {output_dir}")

    if ext == ".blend":
        bpy.ops.wm.open_mainfile(filepath=resolved_asset)
    else:
        clear_scene()
        import_asset(resolved_asset)

    mesh_objects = get_mesh_objects()
    if not mesh_objects:
        print("ERROR: No mesh objects found in asset.")
        sys.exit(1)

    print(f"Found {len(mesh_objects)} mesh object(s)")

    all_min, all_max = compute_bounds(mesh_objects)
    dimensions, scale_factor = center_and_normalize(mesh_objects, all_min, all_max)
    print(f"Dimensions: {dimensions[0]:.3f} x {dimensions[1]:.3f} x {dimensions[2]:.3f}")
    print(f"Normalized by scale factor: {scale_factor:.4f}")

    warnings = []
    tex_warning = check_missing_textures(mesh_objects)
    if tex_warning:
        warnings.append(tex_warning)

    material_warnings = apply_material_mode(args.material_mode, mesh_objects)
    warnings.extend(material_warnings)
    print(f"Material mode: {args.material_mode}")

    cam_obj = add_camera()
    add_studio_lights()

    views = [v.strip() for v in args.views.split(",")]
    view_paths = {}
    print(f"\nRendering {len(views)} view(s) at {args.resolution}px...")
    for view_name in views:
        set_camera_for_view(cam_obj, view_name)
        path = render_view(cam_obj, view_name, output_dir, args.resolution, args.engine, args.transparent)
        view_paths[view_name] = path

    contact_path = create_contact_sheet(output_dir, view_paths, args.resolution)

    if args.turntable:
        print("\nRendering turntable (36 frames)...")
        render_turntable(cam_obj, output_dir, args.resolution, args.engine, args.transparent)

    blend_path = None
    if args.save_blend:
        blend_path = os.path.join(output_dir, "imported_asset.blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
        print(f"\nSaved .blend: {blend_path}")

    report = gather_asset_info(
        args.asset, resolved_asset, ext, mesh_objects, all_min, all_max,
        dimensions, view_paths, blend_path, warnings
    )

    report_path = os.path.join(output_dir, "asset_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {report_path}")
    print("Done.")


if __name__ == "__main__":
    main()
