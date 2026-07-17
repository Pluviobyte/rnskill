#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
SID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}")


def require(obj, path, errors):
    current = obj
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            errors.append(f"missing field: {path}")
            return None
        current = current[key]
    return current


def validate_spec(spec, errors):
    for field in (
        "medium", "craft_style", "aspect_ratio", "style_signature",
        "color_field.background_hex", "color_field.evenness", "color_field.paper_grain",
        "palette_hex", "composition.layout", "composition.depth_layers",
        "composition.negative_space", "composition.balance", "composition.reserved_areas",
        "idea", "label.present", "label.content", "label.font_character",
        "label.weight", "label.placement", "label.treatment", "label.editable",
        "mood", "references_era", "negative_prompt",
    ):
        require(spec, field, errors)
    background = require(spec, "color_field.background_hex", errors)
    if background is not None and not HEX.fullmatch(str(background)):
        errors.append("color_field.background_hex must be #RRGGBB")
    palette = spec.get("palette_hex", [])
    if not isinstance(palette, list) or not palette:
        errors.append("palette_hex must be a non-empty list")
    elif any(not HEX.fullmatch(str(color)) for color in palette):
        errors.append("every palette_hex value must be #RRGGBB")
    elements = spec.get("elements")
    if not isinstance(elements, list) or not elements:
        errors.append("elements must be a non-empty list")
    else:
        required = {"id", "what", "role", "halftone", "cut_edge", "drop_shadow", "color_treatment", "placement"}
        for index, element in enumerate(elements):
            if not isinstance(element, dict):
                errors.append(f"elements[{index}] must be an object")
                continue
            missing = sorted(required - element.keys())
            if missing:
                errors.append(f"elements[{index}] missing: {', '.join(missing)}")


def safe_asset(project: Path, value: str, label: str, errors):
    candidate = (project / value).resolve()
    try:
        candidate.relative_to(project)
    except ValueError:
        errors.append(f"{label} escapes project directory: {value}")
        return None
    if not candidate.is_file():
        errors.append(f"{label} not found: {candidate}")
        return None
    return candidate


def validate_layer_alpha(path: Path, label: str, errors):
    if path.suffix.lower() != ".png":
        errors.append(f"{label} must be a PNG with transparency")
        return
    if not shutil.which("ffmpeg"):
        errors.append("ffmpeg is required to inspect layered PNG alpha")
        return
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
            "-vf", "alphaextract,signalstats,metadata=print:file=-",
            "-frames:v", "1", "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0:
        errors.append(f"{label} must contain an alpha channel")
        return
    minimum = re.search(r"lavfi\.signalstats\.YMIN=(\d+)", output)
    maximum = re.search(r"lavfi\.signalstats\.YMAX=(\d+)", output)
    if not minimum or not maximum:
        errors.append(f"could not inspect alpha range for {label}")
        return
    alpha_min = int(minimum.group(1))
    alpha_max = int(maximum.group(1))
    if alpha_max == 0:
        errors.append(f"{label} is fully transparent")
    elif alpha_min == 255:
        errors.append(f"{label} is fully opaque; layered pieces need transparent pixels")


def validate_plan(plan, project, errors):
    if plan.get("version") != 1:
        errors.append("plan version must be 1")
    canvas = plan.get("canvas")
    if not isinstance(canvas, dict):
        errors.append("canvas must be an object")
    else:
        for key in ("width", "height", "fps"):
            value = canvas.get(key)
            if not isinstance(value, int) or value <= 0:
                errors.append(f"canvas.{key} must be a positive integer")
    provenance = plan.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
    else:
        for key in ("actual_still_provider", "actual_motion_provider", "external_uploads"):
            if key not in provenance:
                errors.append(f"provenance.{key} is required")
        if provenance.get("actual_motion_provider") != "local-ffmpeg":
            errors.append("this renderer requires provenance.actual_motion_provider=local-ffmpeg")
    scenes = plan.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes must be a non-empty list")
        return
    ids = set()
    for index, scene in enumerate(scenes):
        prefix = f"scenes[{index}]"
        if not isinstance(scene, dict):
            errors.append(f"{prefix} must be an object")
            continue
        scene_id = scene.get("id")
        if not isinstance(scene_id, str) or not SID.fullmatch(scene_id):
            errors.append(f"{prefix}.id must be file-safe")
        elif scene_id in ids:
            errors.append(f"duplicate scene id: {scene_id}")
        else:
            ids.add(scene_id)
        duration = scene.get("duration_s")
        if not isinstance(duration, (int, float)) or duration <= 0:
            errors.append(f"{prefix}.duration_s must be positive")
        background = scene.get("background_hex")
        if not isinstance(background, str) or not HEX.fullmatch(background):
            errors.append(f"{prefix}.background_hex must be #RRGGBB")
        mode = scene.get("mode")
        if mode == "layered":
            pieces = scene.get("pieces")
            if not isinstance(pieces, list) or not pieces:
                errors.append(f"{prefix}.pieces must be a non-empty list")
                continue
            previous_start = -1.0
            for piece_index, piece in enumerate(pieces):
                pp = f"{prefix}.pieces[{piece_index}]"
                if not isinstance(piece, dict):
                    errors.append(f"{pp} must be an object")
                    continue
                source = piece.get("source")
                if not isinstance(source, str) or not source:
                    errors.append(f"{pp}.source must be a project-relative PNG path")
                elif project:
                    source_path = safe_asset(project, source, f"{pp}.source", errors)
                    if source_path:
                        validate_layer_alpha(source_path, f"{pp}.source", errors)
                for axis in ("x", "y"):
                    if not isinstance(piece.get(axis), (int, float)):
                        errors.append(f"{pp}.{axis} must be numeric")
                entry = piece.get("entry")
                if not isinstance(entry, dict):
                    errors.append(f"{pp}.entry must be an object")
                    continue
                if entry.get("from") not in {"left", "right", "top", "bottom"}:
                    errors.append(f"{pp}.entry.from is invalid")
                start = entry.get("start_s")
                end = entry.get("end_s")
                if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or not 0 <= start < end:
                    errors.append(f"{pp}.entry requires 0 <= start_s < end_s")
                elif isinstance(duration, (int, float)) and end > duration:
                    errors.append(f"{pp}.entry.end_s exceeds scene duration")
                if isinstance(start, (int, float)) and start < previous_start:
                    errors.append(f"{pp}.entry.start_s must not go backwards")
                if isinstance(start, (int, float)):
                    previous_start = start
                has_width = "width" in piece
                has_height = "height" in piece
                if has_width != has_height:
                    errors.append(f"{pp} must provide both width and height or neither")
                elif has_width:
                    if not isinstance(piece["width"], (int, float)) or piece["width"] <= 0:
                        errors.append(f"{pp}.width must be positive")
                    if not isinstance(piece["height"], (int, float)) or piece["height"] <= 0:
                        errors.append(f"{pp}.height must be positive")
                if "distance_px" in entry and (
                    not isinstance(entry["distance_px"], (int, float)) or entry["distance_px"] <= 0
                ):
                    errors.append(f"{pp}.entry.distance_px must be positive")
        elif mode == "bands":
            still = scene.get("still")
            if not isinstance(still, str) or not still:
                errors.append(f"{prefix}.still must be a project-relative image path")
            elif project:
                safe_asset(project, still, f"{prefix}.still", errors)
            bands = scene.get("bands", 3)
            if not isinstance(bands, int) or not 2 <= bands <= 8:
                errors.append(f"{prefix}.bands must be an integer from 2 to 8")
            if scene.get("first_from", "left") not in {"left", "right"}:
                errors.append(f"{prefix}.first_from must be left or right")
        else:
            errors.append(f"{prefix}.mode must be layered or bands")


def main():
    parser = argparse.ArgumentParser(description="Validate editorial collage specs and assembly plans")
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--project", type=Path)
    args = parser.parse_args()
    if not args.spec and not args.plan:
        parser.error("provide --spec, --plan, or both")
    errors = []
    try:
        if args.spec:
            validate_spec(load_json(args.spec.resolve()), errors)
        if args.plan:
            project = args.project.resolve() if args.project else None
            validate_plan(load_json(args.plan.resolve()), project, errors)
    except ValueError as exc:
        errors.append(str(exc))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
