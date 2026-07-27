#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
except ImportError as exc:
    bundled_python = (
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
    )
    if bundled_python.is_file() and Path(sys.executable).resolve() != bundled_python.resolve():
        os.execv(str(bundled_python), [str(bundled_python), *sys.argv])
    raise SystemExit(
        "Pillow is required. Use the Codex bundled Python runtime."
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "references" / "style-registry.json"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=True)


def parse_time(value: str) -> float:
    parts = value.strip().replace(",", ".").split(":")
    if len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return float(value)


def parse_range(value: str) -> tuple[float, float]:
    if "-" in value:
        start_raw, end_raw = value.split("-", 1)
    elif value.count(":") == 1:
        start_raw, end_raw = value.split(":", 1)
    else:
        raise argparse.ArgumentTypeError(
            "Use START-END or START:END seconds, for example 0-23.936."
        )
    start, end = float(start_raw), float(end_raw)
    if start < 0 or end <= start:
        raise argparse.ArgumentTypeError("Excluded range must satisfy 0 <= START < END.")
    return start, end


def parse_srt(path: Path) -> list[dict]:
    cues: list[dict] = []
    content = path.read_text(encoding="utf-8-sig").strip()
    for block in re.split(r"\n\s*\n", content):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        start_raw, end_raw = [
            item.strip() for item in lines[timing_index].split("-->", 1)
        ]
        text = " ".join(lines[timing_index + 1 :]).strip()
        if text:
            cues.append(
                {
                    "start": parse_time(start_raw),
                    "end": parse_time(end_raw),
                    "text": text,
                }
            )
    return cues


def load_cues(path: Path) -> list[dict]:
    if path.suffix.lower() == ".srt":
        cues = parse_srt(path)
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise SystemExit(f"Expected a caption list in {path}")
        cues = [
            {
                "start": float(item["start"]),
                "end": float(item["end"]),
                "text": str(item["text"]).strip(),
            }
            for item in data
            if str(item.get("text", "")).strip()
        ]
    if not cues:
        raise SystemExit(f"No usable caption cues found in {path}")
    previous_end = -1.0
    for index, cue in enumerate(cues, 1):
        if cue["start"] < 0 or cue["end"] <= cue["start"]:
            raise SystemExit(f"Invalid timing in cue {index}: {cue}")
        if cue["start"] < previous_end - 0.001:
            raise SystemExit(f"Overlapping cues at cue {index}")
        previous_end = cue["end"]
    return cues


def exclude_cues(
    cues: list[dict], excluded: list[tuple[float, float]]
) -> list[dict]:
    return [
        cue
        for cue in cues
        if not any(cue["start"] < end and cue["end"] > start for start, end in excluded)
    ]


def load_style(name: str) -> dict:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    styles = registry.get("styles", {})
    if name not in styles:
        raise SystemExit(
            f"Unknown style {name!r}. Available: {', '.join(sorted(styles))}"
        )
    return styles[name]


def validate_qc(path: Path | None, allow_missing: bool) -> dict | None:
    if path is None or not path.is_file():
        if allow_missing:
            return None
        raise SystemExit(
            "Final rendering requires --qc pointing to a PASS caption-qc.json."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if str(data.get("status", "")).lower() != "pass":
        raise SystemExit(f"Caption QC is not PASS: {path}")
    timing_source = data.get("timing_source")
    if timing_source and timing_source != "volcengine-word-timestamps":
        raise SystemExit(f"Unexpected timing source: {timing_source}")
    coverage = data.get("alignment_coverage")
    if coverage is not None and float(coverage) < 0.90:
        raise SystemExit(f"Alignment coverage below 0.90: {coverage}")
    return data


def probe_video(path: Path) -> dict:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate:format=duration",
            "-of",
            "json",
            str(path),
        ]
    )
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    rate_num, rate_den = stream.get("r_frame_rate", "30/1").split("/")
    fps = float(rate_num) / max(float(rate_den), 1.0)
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "fps": fps,
        "duration": float(data["format"]["duration"]),
    }


def resolve_font(style: dict, explicit: Path | None) -> Path:
    if explicit:
        if not explicit.is_file():
            raise SystemExit(f"Font not found: {explicit}")
        return explicit
    for raw in style.get("font_candidates", []):
        candidate = Path(raw)
        if candidate.is_file():
            return candidate
    raise SystemExit("No registered Chinese font found. Pass --font explicitly.")


ASCII_TOKEN = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._/+:#-]*(?:\s+[A-Za-z0-9][A-Za-z0-9._/+:#-]*)*"
)
TOKEN_RE = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._/+:#-]*(?:\s+[A-Za-z0-9][A-Za-z0-9._/+:#-]*)*"
    r"|[\u3400-\u9fff]|[^\s]"
)


def is_ascii_token(value: str) -> bool:
    return bool(ASCII_TOKEN.fullmatch(value))


def combine(left: str, right: str) -> str:
    if not left:
        return right
    if is_ascii_token(left.split("\n")[-1]) and is_ascii_token(right):
        return f"{left} {right}"
    return f"{left}{right}"


def measure(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, spacing: int) -> tuple[int, int, tuple[int, int, int, int]]:
    bbox = draw.multiline_textbbox(
        (0, 0), text, font=font, spacing=spacing, align="center"
    )
    return bbox[2] - bbox[0], bbox[3] - bbox[1], bbox


def wrap_for_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    max_lines: int,
    spacing: int,
) -> str | None:
    tokens = TOKEN_RE.findall(text.replace("\n", " ").strip())
    lines: list[str] = []
    current = ""
    for token in tokens:
        candidate = combine(current, token)
        width, _, _ = measure(draw, candidate, font, spacing)
        if current and width > max_width:
            lines.append(current)
            current = token
        else:
            current = candidate
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        return None
    return "\n".join(lines)


def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: Path,
    font_size: int,
    min_font_size: int,
    max_width: int,
    max_lines: int,
    line_height: float,
) -> tuple[str, ImageFont.FreeTypeFont, int, tuple[int, int, int, int]]:
    for size in range(font_size, min_font_size - 1, -2):
        font = ImageFont.truetype(str(font_path), size=size)
        spacing = max(0, round(size * (line_height - 1)))
        wrapped = wrap_for_width(
            draw, text, font, max_width, max_lines, spacing
        )
        if wrapped is None:
            continue
        width, _, bbox = measure(draw, wrapped, font, spacing)
        if width <= max_width:
            return wrapped, font, spacing, bbox
    raise SystemExit(f"Caption cannot fit within {max_lines} lines: {text}")


def render_layer(
    text: str,
    width: int,
    band_height: int,
    scale: float,
    style: dict,
    font_path: Path,
    out: Path,
) -> None:
    canvas = Image.new("RGBA", (width, band_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    font_size = max(1, round(style["font_size"] * scale))
    min_font_size = max(1, round(style["min_font_size"] * scale))
    max_text_width = min(
        width - round(80 * scale), round(style["max_text_width"] * scale)
    )
    wrapped, font, spacing, bbox = fit_text(
        draw,
        text,
        font_path,
        font_size,
        min_font_size,
        max_text_width,
        int(style["max_lines"]),
        float(style["line_height"]),
    )
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    pad_x = round(style["panel_padding_x"] * scale)
    pad_y = round(style["panel_padding_y"] * scale)
    bottom = round(style["bottom"] * scale)
    panel_width = text_width + pad_x * 2
    panel_height = text_height + pad_y * 2
    panel_x = (width - panel_width) // 2
    panel_y = band_height - bottom - panel_height
    if panel_y < 0:
        raise SystemExit("Caption band is too short for the fitted panel.")
    panel_box = (
        panel_x,
        panel_y,
        panel_x + panel_width,
        panel_y + panel_height,
    )
    panel_radius = round(style["panel_radius"] * scale)
    panel_shadow = style.get("panel_shadow")
    if isinstance(panel_shadow, dict):
        shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        offset_x = round(panel_shadow.get("offset_x", 0) * scale)
        offset_y = round(panel_shadow.get("offset_y", 0) * scale)
        shadow_box = tuple(
            value + offset
            for value, offset in zip(
                panel_box,
                (offset_x, offset_y, offset_x, offset_y),
                strict=True,
            )
        )
        shadow_draw.rounded_rectangle(
            shadow_box,
            radius=panel_radius,
            fill=tuple(panel_shadow["color"]),
        )
        blur = max(0, round(panel_shadow.get("blur", 0) * scale))
        if blur:
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur))
        canvas.alpha_composite(shadow_layer)

    panel_gradient = style.get("panel_gradient")
    if isinstance(panel_gradient, dict):
        panel_size = (panel_width + 1, panel_height + 1)
        panel = Image.new("RGBA", panel_size, (0, 0, 0, 0))
        panel_draw = ImageDraw.Draw(panel)
        top = tuple(panel_gradient["top"])
        bottom_color = tuple(panel_gradient["bottom"])
        denominator = max(panel_height, 1)
        for row in range(panel_height + 1):
            mix = row / denominator
            color = tuple(
                round(start + (end - start) * mix)
                for start, end in zip(top, bottom_color, strict=True)
            )
            panel_draw.line((0, row, panel_width, row), fill=color)
        mask = Image.new("L", panel_size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, panel_width, panel_height),
            radius=panel_radius,
            fill=255,
        )
        panel.putalpha(ImageChops.multiply(panel.getchannel("A"), mask))
        canvas.alpha_composite(panel, (panel_x, panel_y))
    else:
        draw.rounded_rectangle(
            panel_box,
            radius=panel_radius,
            fill=tuple(style["panel_color"]),
        )

    border_color = style.get("panel_border_color")
    border_width = round(style.get("panel_border_width", 0) * scale)
    if border_color and border_width > 0:
        draw.rounded_rectangle(
            panel_box,
            radius=panel_radius,
            outline=tuple(border_color),
            width=border_width,
        )
    text_x = (width - text_width) // 2 - bbox[0]
    text_y = panel_y + pad_y - bbox[1]
    draw.multiline_text(
        (text_x, text_y),
        wrapped,
        font=font,
        fill=tuple(style["text_color"]),
        spacing=spacing,
        align="center",
        stroke_width=int(style.get("text_stroke_width", 0)),
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, optimize=True)


def quote_concat(path: Path) -> str:
    return str(path.resolve()).replace("'", "'\\''")


def build_layers(
    cues: list[dict],
    width: int,
    duration: float,
    band_height: int,
    scale: float,
    style: dict,
    font: Path,
    work: Path,
) -> tuple[Path, dict[int, Path]]:
    work.mkdir(parents=True, exist_ok=True)
    transparent = work / "transparent.png"
    Image.new("RGBA", (width, band_height), (0, 0, 0, 0)).save(transparent)
    layers: dict[int, Path] = {}
    for index, cue in enumerate(cues):
        layer = work / f"cue-{index + 1:04d}.png"
        render_layer(cue["text"], width, band_height, scale, style, font, layer)
        layers[index] = layer

    segments: list[tuple[Path, float]] = []
    cursor = 0.0
    for index, cue in enumerate(cues):
        start = max(cursor, cue["start"])
        if start > cursor + 0.001:
            segments.append((transparent, start - cursor))
        if cue["end"] > start + 0.001:
            segments.append((layers[index], cue["end"] - start))
        cursor = max(cursor, cue["end"])
    if duration > cursor + 0.001:
        segments.append((transparent, duration - cursor))
    if not segments:
        raise SystemExit("No caption timeline remains after exclusions.")

    concat = work / "overlay.ffconcat"
    lines = ["ffconcat version 1.0"]
    for image, seconds in segments:
        lines.extend(
            [f"file '{quote_concat(image)}'", f"duration {seconds:.6f}"]
        )
    lines.extend(
        [
            f"file '{quote_concat(segments[-1][0])}'",
            "duration 0.001000",
        ]
    )
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return concat, layers


def choose_preview_time(cues: list[dict], requested: float | None) -> float:
    if requested is not None:
        return requested
    longest = max(cues, key=lambda cue: len(cue["text"]))
    return (longest["start"] + longest["end"]) / 2


def make_preview(
    video: Path,
    cues: list[dict],
    layers: dict[int, Path],
    at: float,
    height: int,
    band_height: int,
    work: Path,
    out: Path,
) -> None:
    base_path = work / "preview-base.png"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-ss",
            f"{at:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            str(base_path),
        ],
        check=True,
    )
    base = Image.open(base_path).convert("RGBA")
    cue_index = next(
        (
            index
            for index, cue in enumerate(cues)
            if cue["start"] <= at <= cue["end"]
        ),
        None,
    )
    if cue_index is not None:
        base.alpha_composite(
            Image.open(layers[cue_index]).convert("RGBA"),
            (0, height - band_height),
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out, quality=95)


def render_overlay(
    concat: Path, fps: float, duration: float, out: Path
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-vf",
            f"fps={fps:.6f},format=argb",
            "-t",
            f"{duration:.6f}",
            "-an",
            "-c:v",
            "qtrle",
            str(out),
        ],
        check=True,
    )


def burn(
    video: Path,
    concat: Path,
    out: Path,
    crf: int,
    preset: str,
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    filter_graph = (
        "[1:v]format=rgba,setpts=PTS-STARTPTS[cap];"
        "[0:v][cap]overlay=0:H-h:shortest=1:eof_action=pass[v]"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(video),
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-filter_complex",
            filter_graph,
            "-map",
            "[v]",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            preset,
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(out),
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render fixed-anchor production captions."
    )
    parser.add_argument("video", type=Path)
    parser.add_argument("captions", type=Path)
    parser.add_argument("--qc", type=Path)
    parser.add_argument("--style", default="anchor-dark")
    parser.add_argument("--font", type=Path)
    parser.add_argument("--exclude", action="append", default=[], type=parse_range)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--overlay-out", type=Path)
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--preview-at", type=float)
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--allow-missing-qc", action="store_true")
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--crf", type=int, default=17)
    parser.add_argument("--preset", default="medium")
    args = parser.parse_args()

    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            raise SystemExit(f"{binary} is required.")
    if not args.video.is_file():
        raise SystemExit(f"Video not found: {args.video}")
    if not args.captions.is_file():
        raise SystemExit(f"Captions not found: {args.captions}")
    if not any((args.out, args.overlay_out, args.preview)):
        raise SystemExit("Choose --preview, --overlay-out, or --out.")

    validate_qc(args.qc, args.allow_missing_qc and args.preview_only)
    style = load_style(args.style)
    video_info = probe_video(args.video)
    scale = video_info["height"] / float(style["reference_height"])
    band_height = round(style["band_height"] * scale)
    font = resolve_font(style, args.font)
    cues = exclude_cues(load_cues(args.captions), args.exclude)
    cues = [
        {**cue, "end": min(cue["end"], video_info["duration"])}
        for cue in cues
        if cue["start"] < video_info["duration"]
    ]
    if not cues:
        raise SystemExit("All cues were removed by --exclude.")
    work = args.work_dir or (
        (args.out or args.overlay_out or args.preview).parent
        / f"{(args.out or args.overlay_out or args.preview).stem}-caption-work"
    )
    concat, layers = build_layers(
        cues,
        video_info["width"],
        video_info["duration"],
        band_height,
        scale,
        style,
        font,
        work,
    )

    if args.preview:
        preview_at = choose_preview_time(cues, args.preview_at)
        make_preview(
            args.video,
            cues,
            layers,
            preview_at,
            video_info["height"],
            band_height,
            work,
            args.preview,
        )
        print(f"preview={args.preview} at={preview_at:.3f}")
    if args.preview_only:
        return
    if args.overlay_out:
        render_overlay(
            concat, video_info["fps"], video_info["duration"], args.overlay_out
        )
        print(f"overlay={args.overlay_out}")
    if args.out:
        burn(args.video, concat, args.out, args.crf, args.preset)
        print(f"output={args.out}")
    print(
        f"style={args.style} cues={len(cues)} "
        f"scale={scale:.3f} font={font}"
    )


if __name__ == "__main__":
    main()
