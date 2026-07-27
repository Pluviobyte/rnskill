#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit("Pillow is required. Run this script with the Codex bundled Python runtime.") from exc


def parse_time(value: str) -> float:
    hours, minutes, tail = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(tail)


def parse_srt(path: Path) -> list[dict]:
    cues = []
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8-sig").strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        start_raw, end_raw = [item.strip() for item in lines[timing_index].split("-->", 1)]
        text = " ".join(lines[timing_index + 1:]).strip()
        if text:
            cues.append({"start": parse_time(start_raw), "end": parse_time(end_raw), "text": text})
    if not cues:
        raise SystemExit(f"No usable subtitle cues found in {path}")
    return cues


def probe(path: Path) -> tuple[int, int, float]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=width,height:format=duration",
         "-select_streams", "v:0", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    return int(stream["width"]), int(stream["height"]), float(data["format"]["duration"])


def default_font() -> Path:
    for candidate in (
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
        Path("/System/Library/Fonts/STHeiti Light.ttc"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ):
        if candidate.is_file():
            return candidate
    raise SystemExit("No suitable Chinese font found; pass --font explicitly.")


def render_layer(text: str, width: int, band_height: int, font_path: Path, font_size: int, out: Path) -> None:
    canvas = Image.new("RGBA", (width, band_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    size = font_size
    while True:
        font = ImageFont.truetype(str(font_path), size=size)
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=1)
        if bbox[2] - bbox[0] <= width - 120 or size <= 30:
            break
        size -= 2
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (band_height - text_height) // 2 - bbox[1]
    pad_x, pad_y = 24, 13
    draw.rounded_rectangle(
        (x - pad_x, y + bbox[1] - pad_y, x + text_width + pad_x, y + bbox[3] + pad_y),
        radius=12, fill=(0, 0, 0, 145),
    )
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255),
              stroke_width=1, stroke_fill=(0, 0, 0, 220))
    canvas.save(out)


def quote_concat(path: Path) -> str:
    return str(path.resolve()).replace("'", "'\\''")


def build_layers(cues: list[dict], width: int, duration: float, band_height: int,
                 font: Path, font_size: int, work: Path) -> tuple[Path, dict[int, Path]]:
    work.mkdir(parents=True, exist_ok=True)
    transparent = work / "transparent.png"
    Image.new("RGBA", (width, band_height), (0, 0, 0, 0)).save(transparent)
    layers: dict[int, Path] = {}
    for index, cue in enumerate(cues):
        layer = work / f"cue-{index + 1:04d}.png"
        render_layer(cue["text"], width, band_height, font, font_size, layer)
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

    concat = work / "overlay.ffconcat"
    lines = ["ffconcat version 1.0"]
    for image, seconds in segments:
        lines += [f"file '{quote_concat(image)}'", f"duration {seconds:.6f}"]
    lines.append(f"file '{quote_concat(segments[-1][0])}'")
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return concat, layers


def make_preview(video: Path, cues: list[dict], layers: dict[int, Path], at: float,
                 height: int, band_height: int, work: Path, out: Path) -> None:
    base_path = work / "preview-base.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", str(video),
                    "-frames:v", "1", str(base_path)], check=True)
    base = Image.open(base_path).convert("RGBA")
    cue_index = next((i for i, cue in enumerate(cues) if cue["start"] <= at <= cue["end"]), None)
    if cue_index is not None:
        base.alpha_composite(Image.open(layers[cue_index]).convert("RGBA"), (0, height - band_height))
    out.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("srt", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--work-dir", type=Path)
    ap.add_argument("--font", type=Path)
    ap.add_argument("--font-size", type=int, default=44)
    ap.add_argument("--band-height", type=int, default=150)
    ap.add_argument("--preview", type=Path)
    ap.add_argument("--preview-at", type=float, default=15.0)
    ap.add_argument("--preview-only", action="store_true")
    args = ap.parse_args()

    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            raise SystemExit(f"{binary} is required")
    width, height, duration = probe(args.video)
    cues = parse_srt(args.srt)
    font = args.font or default_font()
    work = args.work_dir or args.out.parent / f"{args.out.stem}-caption-work"
    concat, layers = build_layers(cues, width, duration, args.band_height, font, args.font_size, work)

    if args.preview:
        make_preview(args.video, cues, layers, args.preview_at, height, args.band_height, work, args.preview)
        print(f"preview={args.preview}")
    if args.preview_only:
        return

    args.out.parent.mkdir(parents=True, exist_ok=True)
    filter_graph = "[1:v]format=rgba,setpts=PTS-STARTPTS[cap];[0:v][cap]overlay=0:H-h:shortest=1:eof_action=pass[v]"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(args.video), "-f", "concat", "-safe", "0", "-i", str(concat),
         "-filter_complex", filter_graph, "-map", "[v]", "-map", "0:a?", "-c:v", "libx264",
         "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy",
         "-movflags", "+faststart", str(args.out)],
        check=True,
    )
    print(f"output={args.out} cues={len(cues)}")


if __name__ == "__main__":
    main()
