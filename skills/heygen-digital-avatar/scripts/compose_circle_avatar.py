#!/usr/bin/env python3
"""Overlay a measured, face-centered Pluviobyte circle avatar on a locked edit."""

from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
PROFILE_PATH = SKILL_DIR / "references" / "pluviobyte-profile.json"
FACE_DETECTOR = SKILL_DIR / "scripts" / "measure_face_center.swift"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--avatar", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--layout", choices=("auto", "landscape", "vertical"), default="auto"
    )
    parser.add_argument(
        "--audio-source", choices=("avatar", "base"), default="avatar"
    )
    parser.add_argument("--duration", type=float)
    parser.add_argument(
        "--center-mode",
        choices=("auto", "profile"),
        default="auto",
        help="auto measures the current master; profile uses the fallback crop.",
    )
    parser.add_argument("--crop-x", type=int)
    parser.add_argument("--crop-y", type=int)
    parser.add_argument("--centering-report", type=Path)
    return parser.parse_args()


def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=index,codec_type,width,height",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def has_audio(info: dict) -> bool:
    return any(stream.get("codec_type") == "audio" for stream in info["streams"])


def video_size(info: dict) -> tuple[int, int]:
    for stream in info["streams"]:
        if stream.get("codec_type") == "video":
            return int(stream["width"]), int(stream["height"])
    raise SystemExit("Input has no video stream")


def mean_center(measures: list[dict]) -> tuple[float, float]:
    return (
        sum(float(item["centerX"]) for item in measures) / len(measures),
        sum(float(item["centerY"]) for item in measures) / len(measures),
    )


def measure_video_faces(
    video: Path,
    duration: float,
    fractions: list[float],
    minimum_samples: int,
    crop_region: tuple[int, int, int, int] | None = None,
) -> list[dict]:
    if shutil.which("swift") is None or not FACE_DETECTOR.is_file():
        raise SystemExit("Face centering requires macOS Swift + Vision")
    with tempfile.TemporaryDirectory(prefix="avatar-face-measure-") as temp_dir:
        temp = Path(temp_dir)
        frames: list[Path] = []
        for index, fraction in enumerate(fractions):
            timestamp = max(0.0, min(duration - 0.04, duration * float(fraction)))
            frame = temp / f"sample-{index:02d}.png"
            cmd = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{timestamp:.6f}",
                "-i",
                str(video),
            ]
            if crop_region is not None:
                width, height, x, y = crop_region
                cmd.extend(["-vf", f"crop={width}:{height}:{x}:{y}"])
            cmd.extend(["-frames:v", "1", str(frame)])
            subprocess.run(cmd, check=True)
            frames.append(frame)
        result = subprocess.run(
            ["swift", str(FACE_DETECTOR), *(str(frame) for frame in frames)],
            check=True,
            capture_output=True,
            text=True,
        )
        measures = [json.loads(line) for line in result.stdout.splitlines() if line]
    if len(measures) < minimum_samples:
        raise SystemExit(
            f"Face detection found {len(measures)} samples; need {minimum_samples}"
        )
    return measures


def clamp_crop(crop: dict, frame_width: int, frame_height: int) -> dict:
    width, height = int(crop["width"]), int(crop["height"])
    if width > frame_width or height > frame_height:
        raise SystemExit("Configured avatar crop exceeds the master dimensions")
    return {
        "x": max(0, min(int(crop["x"]), frame_width - width)),
        "y": max(0, min(int(crop["y"]), frame_height - height)),
        "width": width,
        "height": height,
    }


def make_mask(path: Path, diameter: int, radius: float) -> None:
    center = (diameter - 1) / 2
    radius_sq = radius**2
    pixels = bytearray(diameter * diameter)
    for y in range(diameter):
        for x in range(diameter):
            if (x - center) ** 2 + (y - center) ** 2 <= radius_sq:
                pixels[y * diameter + x] = 255
    path.write_bytes(f"P5\n{diameter} {diameter}\n255\n".encode() + pixels)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)


def make_frame(
    path: Path,
    diameter: int,
    inner_radius: float,
    white_radius: float,
    accent_hex: str,
) -> None:
    center = (diameter - 1) / 2
    accent = tuple(bytes.fromhex(accent_hex))
    rows = []
    for y in range(diameter):
        row = bytearray([0])
        for x in range(diameter):
            distance_sq = (x - center) ** 2 + (y - center) ** 2
            if distance_sq <= inner_radius**2:
                row.extend((0, 0, 0, 0))
            elif distance_sq <= white_radius**2:
                row.extend((255, 255, 255, 255))
            elif distance_sq <= center**2:
                row.extend((*accent, 255))
            else:
                row.extend((0, 0, 0, 0))
        rows.append(bytes(row))
    header = struct.pack(">IIBBBBB", diameter, diameter, 8, 6, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + png_chunk(b"IEND", b"")
    )


def main() -> None:
    args = parse_args()
    for path in (args.base, args.avatar):
        if not path.is_file():
            raise SystemExit(f"Missing input: {path}")
    if (args.crop_x is None) != (args.crop_y is None):
        raise SystemExit("--crop-x and --crop-y must be provided together")

    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    layout = profile["default_layout"]
    centering = layout["centering"]
    base_info, avatar_info = probe(args.base), probe(args.avatar)
    width, height = video_size(base_info)
    avatar_width, avatar_height = video_size(avatar_info)
    size_key = f"{width}x{height}"
    expected = {"landscape": "1920x1080", "vertical": "1080x1920"}
    if args.layout != "auto" and size_key != expected[args.layout]:
        raise SystemExit(f"{args.layout} requires {expected[args.layout]}, got {size_key}")
    if size_key not in layout["placements"]:
        raise SystemExit(
            f"No approved circle layout for {size_key}; use 1920x1080 or 1080x1920."
        )
    if not has_audio(avatar_info) and args.audio_source == "avatar":
        raise SystemExit("Avatar master has no audio stream")
    if not has_audio(base_info) and args.audio_source == "base":
        raise SystemExit("Base edit has no audio stream")

    circle = layout["circle"]
    placement = layout["placements"][size_key]
    inner = int(circle["content_diameter"])
    white = int(circle["white_border"])
    accent = int(circle["accent_border"])
    outer = inner + 2 * white + 2 * accent
    inner_offset = white + accent
    output_center = inner_offset + inner / 2.0
    duration = args.duration or float(avatar_info["format"]["duration"])
    avatar_duration = float(avatar_info["format"]["duration"])
    audio_input = 1 if args.audio_source == "avatar" else 0
    fractions = [float(value) for value in centering["sample_fractions"]]
    minimum_samples = int(centering["minimum_detected_samples"])
    tolerance = float(centering["output_tolerance_px"])
    visual_offset = centering.get("visual_offset_output_px", {"x": 0, "y": 0})
    visual_offset_x = float(visual_offset.get("x", 0))
    visual_offset_y = float(visual_offset.get("y", 0))
    fallback_crop = dict(layout["source_crop"])

    master_measures: list[dict] = []
    if args.crop_x is not None:
        mode = "manual"
        crop = {**fallback_crop, "x": args.crop_x, "y": args.crop_y}
    elif args.center_mode == "profile":
        mode = "profile_fallback"
        crop = fallback_crop
    else:
        mode = "auto_face_center"
        master_measures = measure_video_faces(
            args.avatar, avatar_duration, fractions, minimum_samples
        )
        center_x, center_y = mean_center(master_measures)
        source_per_output_x = int(fallback_crop["width"]) / inner
        source_per_output_y = int(fallback_crop["height"]) / inner
        crop = {
            **fallback_crop,
            "x": round(
                center_x
                - int(fallback_crop["width"]) / 2.0
                - visual_offset_x * source_per_output_x
            ),
            "y": round(
                center_y
                - int(fallback_crop["height"]) / 2.0
                - visual_offset_y * source_per_output_y
            ),
        }
    crop = clamp_crop(crop, avatar_width, avatar_height)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="heygen-circle-") as temp_dir:
        mask_path = Path(temp_dir) / "circle-mask.pgm"
        frame_path = Path(temp_dir) / "circle-frame.png"
        make_mask(mask_path, outer, inner / 2 - 1)
        make_frame(
            frame_path,
            outer,
            inner / 2 - 1,
            inner / 2 + white,
            circle["accent_color"],
        )
        filters = [
            (
                "[0:v]tpad=stop_mode=clone:stop_duration=2,"
                f"trim=duration={duration:.6f},setpts=PTS-STARTPTS[base]"
            ),
            (
                f"[1:v]crop={crop['width']}:{crop['height']}:{crop['x']}:{crop['y']},"
                f"scale={inner}:{inner},"
                f"pad={outer}:{outer}:{inner_offset}:{inner_offset}:color=black,"
                "format=rgb24[avatar_rgb]"
            ),
            f"[2:v]format=gray,scale={outer}:{outer}[mask]",
            "[avatar_rgb][mask]alphamerge,format=rgba[avatar_cut]",
            "[3:v]format=rgba[frame]",
            (
                "[avatar_cut][frame]overlay=0:0:format=auto,"
                "fade=t=in:st=0:d=0.35:alpha=1,"
                f"tpad=stop_mode=clone:stop_duration=2,trim=duration={duration:.6f},"
                "setpts=PTS-STARTPTS[avatar]"
            ),
            (
                f"[base][avatar]overlay=x={placement['x']}:y={placement['y']}:"
                "format=auto[vout]"
            ),
            (
                f"[{audio_input}:a]apad=pad_dur=2,atrim=duration={duration:.6f},"
                "asetpts=PTS-STARTPTS[aout]"
            ),
        ]
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-i",
            str(args.base),
            "-i",
            str(args.avatar),
            "-loop",
            "1",
            "-i",
            str(mask_path),
            "-loop",
            "1",
            "-i",
            str(frame_path),
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-t",
            f"{duration:.6f}",
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            str(args.output),
        ]
        subprocess.run(cmd, check=True)

    output_measures = measure_video_faces(
        args.output,
        duration,
        fractions,
        minimum_samples,
        (outer, outer, int(placement["x"]), int(placement["y"])),
    )
    measured_x, measured_y = mean_center(output_measures)
    target_x = output_center + visual_offset_x
    target_y = output_center + visual_offset_y
    circle_offset_x = measured_x - output_center
    circle_offset_y = measured_y - output_center
    target_offset_x = measured_x - target_x
    target_offset_y = measured_y - target_y
    status = (
        "pass"
        if max(abs(target_offset_x), abs(target_offset_y)) <= tolerance
        else "fail"
    )
    report = {
        "status": status,
        "mode": mode,
        "sample_fractions": fractions,
        "minimum_detected_samples": minimum_samples,
        "fallback_source_crop": fallback_crop,
        "applied_source_crop": crop,
        "master_measurements": master_measures,
        "output_measurements": output_measures,
        "output_circle_center": {"x": output_center, "y": output_center},
        "reviewed_visual_offset": {"x": visual_offset_x, "y": visual_offset_y},
        "output_face_target": {"x": target_x, "y": target_y},
        "measured_output_average": {"x": measured_x, "y": measured_y},
        "measured_output_offset_from_circle": {
            "x": circle_offset_x,
            "y": circle_offset_y,
        },
        "measured_output_offset": {"x": target_offset_x, "y": target_offset_y},
        "tolerance_px": tolerance,
    }
    report_path = args.centering_report or args.output.with_suffix(".centering.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if status != "pass":
        raise SystemExit(
            "Visual centering failed: "
            f"target_offset=({target_offset_x:.3f}, {target_offset_y:.3f}), "
            f"tolerance={tolerance:.3f}"
        )
    print(args.output)
    print(report_path)


if __name__ == "__main__":
    main()
