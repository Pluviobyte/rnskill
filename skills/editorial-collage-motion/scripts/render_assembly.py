#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def run(command):
    subprocess.run(command, check=True)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inside(project, relative):
    if not isinstance(relative, str) or not relative:
        raise ValueError("asset path must be a non-empty string")
    path = (project / relative).resolve()
    try:
        path.relative_to(project)
    except ValueError as exc:
        raise ValueError(f"asset escapes project directory: {relative}") from exc
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def motion_expr(final, before, start, end):
    moving = f"{before}+(t-{start:.6f})/({end-start:.6f})*({final-before})"
    return f"if(lt(t,{start:.6f}),{before},if(lt(t,{end:.6f}),{moving},{final}))"


def encode_args(fps):
    return [
        "-r", str(fps), "-an", "-c:v", "libx264", "-preset", "fast",
        "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    ]


def render_layered(project, scene, canvas, output):
    width, height, fps = canvas["width"], canvas["height"], canvas["fps"]
    duration = float(scene["duration_s"])
    color = scene["background_hex"]
    if not HEX.fullmatch(color):
        raise ValueError(f"invalid background color: {color}")
    pieces = scene.get("pieces") or []
    if not pieces:
        raise ValueError(f"{scene['id']} has no pieces")
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", f"color=c={color}:s={width}x{height}:r={fps}:d={duration}",
    ]
    for piece in pieces:
        source = inside(project, piece["source"])
        command += ["-loop", "1", "-framerate", str(fps), "-t", str(duration), "-i", str(source)]
    filters = ["[0:v]format=rgba[base]"]
    previous = "base"
    for index, piece in enumerate(pieces, start=1):
        source_label = f"p{index}"
        if "width" in piece and "height" in piece:
            filters.append(f"[{index}:v]scale={int(piece['width'])}:{int(piece['height'])},format=rgba[{source_label}]")
            piece_width = int(piece["width"])
            piece_height = int(piece["height"])
        else:
            filters.append(f"[{index}:v]format=rgba[{source_label}]")
            piece_width = width
            piece_height = height
        x = float(piece["x"])
        y = float(piece["y"])
        entry = piece["entry"]
        start = float(entry["start_s"])
        end = float(entry["end_s"])
        direction = entry["from"]
        default_distance = width + piece_width if direction in {"left", "right"} else height + piece_height
        distance = float(entry.get("distance_px", default_distance))
        if direction == "left":
            ox, oy = motion_expr(x, x - distance, start, end), f"{y:.3f}"
        elif direction == "right":
            ox, oy = motion_expr(x, x + distance, start, end), f"{y:.3f}"
        elif direction == "top":
            ox, oy = f"{x:.3f}", motion_expr(y, y - distance, start, end)
        elif direction == "bottom":
            ox, oy = f"{x:.3f}", motion_expr(y, y + distance, start, end)
        else:
            raise ValueError(f"invalid entry direction: {direction}")
        out = f"v{index}"
        filters.append(f"[{previous}][{source_label}]overlay=x='{ox}':y='{oy}':eval=frame:format=auto[{out}]")
        previous = out
    filters.append(f"[{previous}]format=yuv420p[out]")
    command += ["-filter_complex", ";".join(filters), "-map", "[out]", "-t", f"{duration:.6f}"]
    command += encode_args(fps) + [str(output)]
    run(command)


def render_bands(project, scene, canvas, output):
    width, height, fps = canvas["width"], canvas["height"], canvas["fps"]
    duration = float(scene["duration_s"])
    color = scene["background_hex"]
    still = inside(project, scene["still"])
    bands = int(scene.get("bands", 3))
    entry_s = float(scene.get("entry_s", 0.72))
    stagger_s = float(scene.get("stagger_s", 0.18))
    first_from = scene.get("first_from", "left")
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", f"color=c={color}:s={width}x{height}:r={fps}:d={duration}",
        "-loop", "1", "-framerate", str(fps), "-t", str(duration), "-i", str(still),
    ]
    labels = "".join(f"[s{i}]" for i in range(bands))
    filters = [
        f"[0:v]format=rgba[base]",
        f"[1:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,format=rgba,split={bands}{labels}",
    ]
    previous = "base"
    y = 0
    for index in range(bands):
        band_height = height // bands if index < bands - 1 else height - y
        filters.append(f"[s{index}]crop={width}:{band_height}:0:{y}[b{index}]")
        start = index * stagger_s
        end = start + entry_s
        from_left = (index % 2 == 0) == (first_from == "left")
        before = -width if from_left else width
        ox = motion_expr(0, before, start, end)
        out = f"v{index}"
        filters.append(f"[{previous}][b{index}]overlay=x='{ox}':y={y}:eval=frame:format=auto[{out}]")
        previous = out
        y += band_height
    filters.append(f"[{previous}]format=yuv420p[out]")
    command += ["-filter_complex", ";".join(filters), "-map", "[out]", "-t", f"{duration:.6f}"]
    command += encode_args(fps) + [str(output)]
    run(command)


def main():
    parser = argparse.ArgumentParser(description="Render deterministic editorial collage assembly motion")
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("ffmpeg and ffprobe are required")
    project = args.project.resolve()
    plan_path = args.plan.resolve()
    output = args.output.resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("version") != 1:
        raise SystemExit("unsupported plan version")
    canvas = plan["canvas"]
    scenes = plan.get("scenes") or []
    if not scenes:
        raise SystemExit("plan has no scenes")
    scene_dir = output.parent / "scene-clips"
    scene_dir.mkdir(parents=True, exist_ok=True)
    clips = []
    for scene in scenes:
        clip = scene_dir / f"{scene['id']}.mp4"
        if scene.get("mode") == "layered":
            render_layered(project, scene, canvas, clip)
        elif scene.get("mode") == "bands":
            render_bands(project, scene, canvas, clip)
        else:
            raise SystemExit(f"unknown mode for {scene.get('id')}: {scene.get('mode')}")
        clips.append(clip)
    output.parent.mkdir(parents=True, exist_ok=True)
    concat = scene_dir / "concat.txt"
    concat.write_text("".join(f"file '{clip.as_posix()}'\n" for clip in clips), encoding="utf-8")
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", str(concat), "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ])
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,width,height,r_frame_rate,pix_fmt",
        "-of", "json", str(output),
    ], check=True, capture_output=True, text=True)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "renderer": "local-ffmpeg",
        "actual_still_provider": plan.get("provenance", {}).get("actual_still_provider", "unknown"),
        "actual_motion_provider": "local-ffmpeg",
        "external_uploads": bool(plan.get("provenance", {}).get("external_uploads", False)),
        "compatible_render": bool(plan.get("provenance", {}).get("compatible_render", True)),
        "compatible_with": plan.get("provenance", {}).get("compatible_with", "editorial-collage-motion visual contract"),
        "plan": str(plan_path),
        "plan_sha256": sha256(plan_path),
        "output": str(output),
        "output_sha256": sha256(output),
        "scene_modes": {scene["id"]: scene["mode"] for scene in scenes},
        "probe": json.loads(probe.stdout),
    }
    manifest_path = output.parent / "render-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)
    print(manifest_path)


if __name__ == "__main__":
    main()
