from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ASPECT_16_9 = "16:9"
ASPECT_9_16 = "9:16"
VALID_ASPECTS = {ASPECT_16_9, ASPECT_9_16}

CANVAS_SIZES = {
    ASPECT_16_9: (1920, 1080),
    ASPECT_9_16: (1080, 1920),
}

SAFE_ZONES = {
    ASPECT_16_9: {"top": 0.08, "bottom": 0.92, "left": 0.05, "right": 0.95},
    ASPECT_9_16: {"top": 0.05, "bottom": 0.95, "left": 0.08, "right": 0.92},
}

POS_TO_Y = {"top": 0.2, "center": 0.5, "bottom": 0.8}


def detect_aspect_ratio(project_dir: Path) -> str:
    data_dir = project_dir / "data" if (project_dir / "data").exists() else project_dir
    output_dir = project_dir / "output"

    for name in ["video_9x16.mp4", "video_vertical.mp4"]:
        if (output_dir / name).exists():
            return ASPECT_9_16

    for name in ["video_16x9.mp4", "video_horizontal.mp4"]:
        if (output_dir / name).exists():
            return ASPECT_16_9

    script_path = data_dir / "script.json"
    if script_path.exists():
        try:
            script = json.loads(script_path.read_text(encoding="utf-8"))
            meta = script.get("_aspect_meta", {})
            if meta.get("target_aspect"):
                return meta["target_aspect"]
        except Exception:
            pass

    return ASPECT_16_9


def _is_vertical_image(path: Path) -> bool:
    try:
        from PIL import Image
        with Image.open(path) as img:
            w, h = img.size
            return h > w
    except Exception:
        return False


def _is_horizontal_image(path: Path) -> bool:
    try:
        from PIL import Image
        with Image.open(path) as img:
            w, h = img.size
            return w > h
    except Exception:
        return False


def _image_aspect_label(path: Path) -> str:
    try:
        from PIL import Image
        with Image.open(path) as img:
            w, h = img.size
            if h > w * 1.1:
                return "vertical"
            elif w > h * 1.1:
                return "horizontal"
            return "square"
    except Exception:
        return "unknown"


def find_asset_variant(
    original_path: str,
    target_aspect: str,
    search_dirs: List[Path],
) -> Optional[str]:
    want_vertical = target_aspect == ASPECT_9_16

    orig = Path(original_path)
    if not orig.exists():
        return None

    orig_w, orig_h = 0, 0
    try:
        from PIL import Image
        with Image.open(orig) as img:
            orig_w, orig_h = img.size
    except Exception:
        pass

    candidates: List[Tuple[Path, float, bool]] = []

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for png_file in sorted(search_dir.rglob("*.png")):
            if png_file.resolve() == orig.resolve():
                continue

            label = _image_aspect_label(png_file)
            is_chatgpt = "chatgpt" in png_file.name.lower() or "ChatGPT" in png_file.name

            if want_vertical and label == "vertical":
                score = 100.0 if is_chatgpt else 50.0
                if orig_w > 0 and orig_h > 0:
                    try:
                        from PIL import Image
                        with Image.open(png_file) as img:
                            cw, ch = img.size
                        dim_ratio = min(orig_w / max(1, ch), orig_h / max(1, cw))
                        dim_ratio = min(dim_ratio, 1.0 / max(0.01, dim_ratio))
                        if dim_ratio > 0.95:
                            score += 20.0
                        elif dim_ratio > 0.8:
                            score += 10.0
                    except Exception:
                        pass
                candidates.append((png_file, score, is_chatgpt))
            elif not want_vertical and label == "horizontal":
                score = 100.0 if is_chatgpt else 50.0
                if orig_w > 0 and orig_h > 0:
                    try:
                        from PIL import Image
                        with Image.open(png_file) as img:
                            cw, ch = img.size
                        dim_ratio = min(orig_h / max(1, cw), orig_w / max(1, ch))
                        dim_ratio = min(dim_ratio, 1.0 / max(0.01, dim_ratio))
                        if dim_ratio > 0.95:
                            score += 20.0
                        elif dim_ratio > 0.8:
                            score += 10.0
                    except Exception:
                        pass
                candidates.append((png_file, score, is_chatgpt))

    if not candidates:
        return None

    candidates.sort(key=lambda c: c[1], reverse=True)

    best = candidates[0][0]
    return str(best)


def _scale_font_size(size: int, source_aspect: str, target_aspect: str) -> int:
    src_w, _ = CANVAS_SIZES[source_aspect]
    tgt_w, _ = CANVAS_SIZES[target_aspect]
    ratio = tgt_w / src_w
    return max(16, round(size * ratio))


def _scale_font_delta(delta: int, source_aspect: str, target_aspect: str) -> int:
    src_w, _ = CANVAS_SIZES[source_aspect]
    tgt_w, _ = CANVAS_SIZES[target_aspect]
    ratio = tgt_w / src_w
    return round(delta * ratio)


def _adjust_y(y: float, source_aspect: str, target_aspect: str) -> float:
    src_safe = SAFE_ZONES[source_aspect]
    tgt_safe = SAFE_ZONES[target_aspect]

    src_range = src_safe["bottom"] - src_safe["top"]
    tgt_range = tgt_safe["bottom"] - tgt_safe["top"]

    normalized = (y - src_safe["top"]) / src_range
    normalized = max(0.0, min(1.0, normalized))

    return round(tgt_safe["top"] + normalized * tgt_range, 3)


def _adjust_dual_spot(direction: str, source_aspect: str, target_aspect: str) -> str:
    if not direction.startswith("dual_spot"):
        return direction

    parts = direction.split("_")
    if len(parts) < 6:
        return direction

    try:
        sx1 = float(parts[2])
        sy1 = float(parts[3])
        sx2 = float(parts[4])
        sy2 = float(parts[5])
    except (ValueError, IndexError):
        return direction

    src_w, src_h = CANVAS_SIZES[source_aspect]
    tgt_w, tgt_h = CANVAS_SIZES[target_aspect]

    if source_aspect == ASPECT_16_9 and target_aspect == ASPECT_9_16:
        new_sx1 = sy1
        new_sy1 = 1.0 - sx1
        new_sx2 = sy2
        new_sy2 = 1.0 - sx2
    elif source_aspect == ASPECT_9_16 and target_aspect == ASPECT_16_9:
        new_sx1 = 1.0 - sy1
        new_sy1 = sx1
        new_sx2 = 1.0 - sy2
        new_sy2 = sx2
    else:
        new_sx1, new_sy1, new_sx2, new_sy2 = sx1, sy1, sx2, sy2

    new_sx1 = max(0.1, min(0.9, new_sx1))
    new_sy1 = max(0.1, min(0.9, new_sy1))
    new_sx2 = max(0.1, min(0.9, new_sx2))
    new_sy2 = max(0.1, min(0.9, new_sy2))

    return f"dual_spot_{new_sx1:.1f}_{new_sy1:.1f}_{new_sx2:.1f}_{new_sy2:.1f}"


def _swap_branded_images(
    script: Dict[str, Any],
    source_aspect: str,
    target_aspect: str,
    project_dir: Path,
) -> Dict[str, Any]:
    search_dirs = [
        project_dir / "data" / "assets",
        project_dir,
        project_dir.parent,
        project_dir.parent.parent,
    ]

    for img_key in ["image"]:
        intro = script.get("intro")
        if intro and intro.get(img_key):
            original = intro[img_key]
            variant = find_asset_variant(original, target_aspect, search_dirs)
            if variant:
                intro[img_key] = variant

        outro = script.get("outro")
        if outro and outro.get(img_key):
            original = outro[img_key]
            variant = find_asset_variant(original, target_aspect, search_dirs)
            if variant:
                outro[img_key] = variant

    return script


def transform_script(
    script: Dict[str, Any],
    source_aspect: str,
    target_aspect: str,
    project_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    if source_aspect not in VALID_ASPECTS:
        raise ValueError(f"Invalid source aspect ratio: {source_aspect}")
    if target_aspect not in VALID_ASPECTS:
        raise ValueError(f"Invalid target aspect ratio: {target_aspect}")
    if source_aspect == target_aspect:
        raise ValueError(f"Source and target aspect ratios are the same: {target_aspect}")

    transformed = copy.deepcopy(script)

    if "defaults" in transformed:
        defaults = transformed["defaults"]
        if "font_size" in defaults:
            defaults["font_size"] = _scale_font_size(defaults["font_size"], source_aspect, target_aspect)

    for section in transformed.get("sections", []):
        visual = section.get("visual", {})
        if visual.get("font_size"):
            visual["font_size"] = _scale_font_size(visual["font_size"], source_aspect, target_aspect)

        if visual.get("gradient_direction", "").startswith("dual_spot"):
            visual["gradient_direction"] = _adjust_dual_spot(
                visual["gradient_direction"], source_aspect, target_aspect
            )

        for key, override in section.get("lines_overrides", {}).items():
            if "font_size" in override:
                override["font_size"] = _scale_font_size(override["font_size"], source_aspect, target_aspect)

        for wkey, woverride in section.get("words_overrides", {}).items():
            if "y" in woverride:
                woverride["y"] = _adjust_y(woverride["y"], source_aspect, target_aspect)
            if "font_size_delta" in woverride:
                woverride["font_size_delta"] = _scale_font_delta(
                    woverride["font_size_delta"], source_aspect, target_aspect
                )

    if project_dir is not None:
        _swap_branded_images(transformed, source_aspect, target_aspect, project_dir)

        data_dir = project_dir / "data" if (project_dir / "data").exists() else project_dir
        synced_path = data_dir / "lyrics_synced.json"
        if synced_path.exists():
            try:
                synced = json.loads(synced_path.read_text(encoding="utf-8"))
                synced_lines = synced.get("lines", [])
                if synced_lines:
                    _ensure_text_fits(transformed, target_aspect, synced_lines)
            except Exception:
                pass

    tgt_w, tgt_h = CANVAS_SIZES[target_aspect]
    transformed["_aspect_meta"] = {
        "source_aspect": source_aspect,
        "target_aspect": target_aspect,
        "target_width": tgt_w,
        "target_height": tgt_h,
    }

    return transformed


def _effective_font_size(script_font_size: int, render_height: int) -> int:
    return int(script_font_size * (render_height / 1080))


_POS_TO_Y = {"top": 0.2, "center": 0.5, "bottom": 0.8}


def _compute_line_group_widths(
    words: list,
    words_overrides: Dict[str, Any],
    line_idx: int,
    base_font_size: int,
    font_family: int,
    render_height: int,
    section_pos: str,
    caption_style: Dict[str, Any],
) -> List[Tuple[List[int], float]]:
    sf = render_height / 1080
    use_styled = caption_style.get("text_style", "") != ""

    resolved = []
    for wi in range(len(words)):
        wkey = f"{line_idx}.{wi}"
        wv = words_overrides.get(wkey, {})
        if "y" in wv:
            word_y = wv["y"]
        else:
            tp = wv.get("text_position", section_pos)
            word_y = _POS_TO_Y.get(tp, 0.5)
        delta = wv.get("font_size_delta", 0)
        effective_base = int(base_font_size * sf)
        word_size = max(24, effective_base + int(delta * sf))

        try:
            from render.renderer import _find_font
            f = _find_font(word_size, family=font_family)
            wW = f.getbbox(words[wi]["text"])[2]
        except Exception:
            wW = word_size * len(words[wi]["text"]) * 0.6

        resolved.append({"px_y": int(word_y * render_height), "wW": wW})

    groups = []
    cur = [0]
    for k in range(1, len(resolved)):
        if resolved[k]["px_y"] == resolved[k - 1]["px_y"]:
            cur.append(k)
        else:
            groups.append(cur)
            cur = [k]
    groups.append(cur)

    effective_base = int(base_font_size * sf)
    spacing = caption_style.get("letter_spacing", 1) * sf * max(8, effective_base * 0.08)
    if use_styled:
        spacing = max(spacing, base_font_size * 0.35)

    result = []
    for group in groups:
        total_w = sum(resolved[i]["wW"] for i in group) + spacing * max(0, len(group) - 1)
        result.append((group, total_w))
    return result


def _ensure_text_fits(
    script: Dict[str, Any],
    target_aspect: str,
    synced_lines: list,
) -> None:
    tgt_w, tgt_h = CANVAS_SIZES[target_aspect]
    safe = SAFE_ZONES[target_aspect]
    max_width = int((safe["right"] - safe["left"]) * tgt_w)
    caption_style = script.get("caption_style", {})
    defaults = script.get("defaults", {})
    base_font = defaults.get("font_size", 82)

    for section in script.get("sections", []):
        visual = section.get("visual", {})
        sec_font = visual.get("font_size", base_font)
        font_family = visual.get("font_family", 0)
        section_pos = visual.get("text_position", caption_style.get("text_position", "center"))
        words_overrides = section.get("words_overrides", {})
        lines_overrides = section.get("lines_overrides", {})

        for line_key in section.get("lines", []):
            if line_key >= len(synced_lines):
                continue
            line_data = synced_lines[line_key]
            words = line_data.get("words", [])
            if not words:
                continue

            lo = lines_overrides.get(str(line_key), {})
            line_font = lo.get("font_size", sec_font)

            groups = _compute_line_group_widths(
                words, words_overrides, line_key, line_font, font_family,
                tgt_h, section_pos, caption_style,
            )

            max_group_w = max(gw for _, gw in groups)
            if max_group_w <= max_width:
                continue

            reduction_steps = 0
            while max_group_w > max_width and line_font > 20 and reduction_steps < 30:
                line_font -= 1
                reduction_steps += 1
                groups = _compute_line_group_widths(
                    words, words_overrides, line_key, line_font, font_family,
                    tgt_h, section_pos, caption_style,
                )
                max_group_w = max(gw for _, gw in groups)

            if str(line_key) in lines_overrides:
                lines_overrides[str(line_key)]["font_size"] = line_font
            else:
                lines_overrides[str(line_key)] = {"font_size": line_font}

        section["lines_overrides"] = lines_overrides


def check_layout_issues(
    script: Dict[str, Any],
    target_aspect: str,
    source_script: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    tgt_w, tgt_h = CANVAS_SIZES[target_aspect]
    safe = SAFE_ZONES[target_aspect]

    meta = script.get("_aspect_meta", {})
    if not meta.get("target_aspect"):
        return [{"check": "meta", "issue": "Script missing _aspect_meta", "severity": "warning"}]

    defaults = script.get("defaults", {})
    base_font = defaults.get("font_size", 112)
    effective_base = _effective_font_size(base_font, tgt_h)

    if effective_base < 24:
        issues.append({
            "check": "font_size",
            "issue": f"Base font effective size {effective_base}px is below minimum 24px",
            "severity": "error",
            "effective_size": effective_base,
        })

    for section in script.get("sections", []):
        visual = section.get("visual", {})
        sec_name = section.get("name", "unknown")
        sec_font = visual.get("font_size", base_font)
        sec_effective = _effective_font_size(sec_font, tgt_h)

        if sec_effective < 24:
            issues.append({
                "check": "font_size",
                "section": sec_name,
                "issue": f"Section font effective size {sec_effective}px is below minimum 24px",
                "severity": "error",
                "effective_size": sec_effective,
            })

        for wkey, woverride in section.get("words_overrides", {}).items():
            y = woverride.get("y")
            if y is not None:
                if y < safe["top"]:
                    issues.append({
                        "check": "safe_zone",
                        "section": sec_name,
                        "word_key": wkey,
                        "issue": f"Word y={y} is above safe zone top {safe['top']}",
                        "severity": "warning",
                        "y": y,
                    })
                elif y > safe["bottom"]:
                    issues.append({
                        "check": "safe_zone",
                        "section": sec_name,
                        "word_key": wkey,
                        "issue": f"Word y={y} is below safe zone bottom {safe['bottom']}",
                        "severity": "warning",
                        "y": y,
                    })

            delta = woverride.get("font_size_delta", 0)
            if delta != 0:
                word_effective = _effective_font_size(sec_font + delta, tgt_h)
                if word_effective < 24:
                    issues.append({
                        "check": "font_size",
                        "section": sec_name,
                        "word_key": wkey,
                        "issue": f"Word effective size {word_effective}px after delta {delta} is below minimum",
                        "severity": "warning",
                        "effective_size": word_effective,
                    })

        direction = visual.get("gradient_direction", "")
        if direction.startswith("dual_spot"):
            parts = direction.split("_")
            if len(parts) >= 6:
                try:
                    coords = [float(parts[i]) for i in range(2, min(6, len(parts)))]
                    for i, c in enumerate(coords):
                        if c < 0.05 or c > 0.95:
                            issues.append({
                                "check": "background_geometry",
                                "section": sec_name,
                                "issue": f"Dual spot coord {i} value {c} is near edge, may clip",
                                "severity": "info",
                            })
                except (ValueError, IndexError):
                    pass

    for img_section_key in ["intro", "outro"]:
        section_data = script.get(img_section_key)
        if section_data and section_data.get("image"):
            img_path = Path(section_data["image"])
            if img_path.exists():
                img_label = _image_aspect_label(img_path)
                want_vertical = target_aspect == ASPECT_9_16
                if want_vertical and img_label == "horizontal":
                    issues.append({
                        "check": "image_mismatch",
                        "section": img_section_key,
                        "issue": f"{img_section_key} image is horizontal but render is vertical",
                        "severity": "error",
                        "image": section_data["image"],
                    })
                elif not want_vertical and img_label == "vertical":
                    issues.append({
                        "check": "image_mismatch",
                        "section": img_section_key,
                        "issue": f"{img_section_key} image is vertical but render is horizontal",
                        "severity": "error",
                        "image": section_data["image"],
                    })

    if source_script is not None:
        src_sections = source_script.get("sections", [])
        tgt_sections = script.get("sections", [])

        if len(src_sections) != len(tgt_sections):
            issues.append({
                "check": "scene_order",
                "issue": f"Section count changed: {len(src_sections)} -> {len(tgt_sections)}",
                "severity": "error",
            })
        else:
            for i, (src, tgt) in enumerate(zip(src_sections, tgt_sections)):
                src_lines = src.get("lines", [])
                tgt_lines = tgt.get("lines", [])
                if src_lines != tgt_lines:
                    issues.append({
                        "check": "scene_order",
                        "section": tgt.get("name", f"section_{i}"),
                        "issue": f"Lines changed: {src_lines} -> {tgt_lines}",
                        "severity": "error",
                    })
                if src.get("name") != tgt.get("name"):
                    issues.append({
                        "check": "scene_order",
                        "section_index": i,
                        "issue": f"Section name changed: {src.get('name')} -> {tgt.get('name')}",
                        "severity": "warning",
                    })
                if src.get("type") != tgt.get("type"):
                    issues.append({
                        "check": "scene_order",
                        "section_index": i,
                        "issue": f"Section type changed: {src.get('type')} -> {tgt.get('type')}",
                        "severity": "error",
                    })

        src_name = source_script.get("name", "")
        tgt_name = script.get("name", "")
        if src_name != tgt_name:
            issues.append({
                "check": "semantic_preservation",
                "issue": f"Project name changed: {src_name} -> {tgt_name}",
                "severity": "warning",
            })

    return issues
