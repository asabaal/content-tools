import bpy
import os
import sys
import json
import argparse
from mathutils import Vector


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="3D Asset Inspector")
    parser.add_argument("--asset", required=True, help="Path to .glb/.gltf/.obj/.fbx/.blend file")
    parser.add_argument("--output-json", default=None, help="Optional path to write JSON report")
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


def inspect_asset(filepath, resolved_path, ext):
    mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]

    all_min = [float("inf")] * 3
    all_max = [float("-inf")] * 3
    for obj in mesh_objects:
        for corner in obj.bound_box:
            world_co = obj.matrix_world @ Vector(corner)
            for i in range(3):
                all_min[i] = min(all_min[i], world_co[i])
                all_max[i] = max(all_max[i], world_co[i])

    if all_min[0] == float("inf"):
        dimensions = [0.0, 0.0, 0.0]
    else:
        dimensions = [all_max[i] - all_min[i] for i in range(3)]

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

    has_textures = len(images) > 0
    file_size = os.path.getsize(resolved_path) if os.path.exists(resolved_path) else 0

    warnings = []
    if len(mesh_objects) > 0 and not has_textures:
        warnings.append("Asset appears to have geometry but no texture images/material textures.")

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
        "warnings": warnings,
    }
    return report


def print_report(report):
    print("\n" + "=" * 60)
    print("3D ASSET INSPECTION REPORT")
    print("=" * 60)
    print(f"  Input path:      {report['input_asset_path']}")
    print(f"  Resolved path:   {report['resolved_asset_path']}")
    print(f"  Extension:       {report['file_extension']}")
    print(f"  File size:       {report['file_size_human']}")
    print()
    print("GEOMETRY")
    print(f"  Mesh objects:    {report['mesh_object_count']}")
    print(f"  Vertices:        {report['vertex_count']}")
    print(f"  Faces:           {report['face_polygon_count']}")
    dims = report['bounding_box_dimensions']
    print(f"  Bounding box:    {dims['x']:.4f} x {dims['y']:.4f} x {dims['z']:.4f}")
    print()
    print("MATERIALS & TEXTURES")
    print(f"  Material count:  {report['material_count']}")
    print(f"  Texture images:  {report['texture_image_count']}")
    if report['material_names']:
        print(f"  Materials:       {', '.join(report['material_names'])}")
    if report['image_names']:
        print(f"  Images:          {', '.join(report['image_names'])}")
    print()
    print("ANIMATION")
    print(f"  Has armature:    {report['has_armature']}")
    print(f"  Has animations:  {report['has_animations']}")
    if report['warnings']:
        print()
        print("WARNINGS")
        for w in report['warnings']:
            print(f"  - {w}")
    print("=" * 60)


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

    if ext == ".blend":
        bpy.ops.wm.open_mainfile(filepath=resolved_asset)
    else:
        clear_scene()
        import_asset(resolved_asset)

    report = inspect_asset(args.asset, resolved_asset, ext)
    print_report(report)

    if args.output_json:
        json_path = resolve_path(args.output_json, project_root)
        os.makedirs(os.path.dirname(json_path) if os.path.dirname(json_path) else ".", exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nJSON report written to: {json_path}")


if __name__ == "__main__":
    main()
