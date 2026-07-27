#!/usr/bin/env python3
"""Compose exact typography over a no-reference workflow artwork base."""

from __future__ import annotations

import argparse
import base64
import html
import mimetypes
import os
from pathlib import Path
import shutil
import subprocess
import sys


BACKGROUND_COLOR = "#FAF9F5"
GRID_COLOR = "#E2E1DC"
DEFAULT_GRID_CELL_HEIGHT_RATIO = 0.10
DEFAULT_GRID_STROKE = 1.8


def has_cjk(text: str) -> bool:
    return any(ord(char) > 0x2E7F for char in text)


def visual_units(text: str, cjk: bool = False) -> float:
    units = 0.0
    for char in text:
        code = ord(char)
        if char.isspace():
            units += 0.34
        elif char in "+:：·,，.!！—-":
            units += 0.52 if not cjk else 0.62
        elif code > 0x2E7F:
            units += 1.0
        elif char.isupper():
            units += 0.68
        else:
            units += 0.56
    return max(units, 1.0)


def fit_size(text: str, max_width: float, preferred: float, minimum: float, cjk: bool) -> float:
    estimate = max_width / visual_units(text, cjk=cjk) * (0.94 if cjk else 0.98)
    return max(minimum, min(preferred, estimate))


def split_title(text: str) -> list[str]:
    explicit = text.split("\\n")
    if len(explicit) > 1:
        if len(explicit) > 2:
            raise ValueError("Use at most two title lines.")
        return explicit

    midpoint = len(text) / 2
    spaces = [index for index, char in enumerate(text) if char.isspace()]
    if spaces:
        split_at = min(spaces, key=lambda index: abs(index - midpoint))
        return [text[:split_at].strip(), text[split_at:].strip()]

    candidates = [
        index + 1
        for index, char in enumerate(text)
        if char in "·：:，,；;—-"
    ]
    if candidates:
        split_at = min(candidates, key=lambda index: abs(index - midpoint))
    else:
        bad_line_end = set("的了和与及或而也自这那把被让将能可在是")
        bad_line_start = set("的了和与及或而也")
        lower = max(2, round(len(text) * 0.32))
        upper = min(len(text) - 2, round(len(text) * 0.68))
        scored: list[tuple[float, int]] = []
        for index in range(lower, upper + 1):
            score = abs(index - midpoint)
            if text[index - 1] in bad_line_end:
                score += 8
            if text[index] in bad_line_start:
                score += 8
            if text[index - 1].isascii() and text[index].isascii():
                score += 12
            scored.append((score, index))
        split_at = min(scored)[1]
    return [text[:split_at].strip(), text[split_at:].strip()]


def resolve_artwork_start(title: str, requested: float | None) -> float:
    if requested is not None:
        return requested
    if not has_cjk(title):
        return 0.50
    units = visual_units(title, cjk=True)
    return min(0.72, max(0.54, 0.54 + max(0.0, units - 6.5) * 0.02))


def resolve_grid_start(artwork_start: float, requested: float | None) -> float:
    if requested is not None:
        return requested
    return min(0.58, max(0.38, artwork_start - 0.16))


def parse_italic_lines(value: str, line_count: int) -> set[int]:
    if not value.strip():
        return set()
    try:
        result = {int(item.strip()) - 1 for item in value.split(",") if item.strip()}
    except ValueError as exc:
        raise ValueError("--italic-title-lines must be comma-separated line numbers.") from exc
    if any(index < 0 or index >= line_count for index in result):
        raise ValueError("--italic-title-lines references a missing title line.")
    return result


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def alpha_bounds(path: Path) -> tuple[int, int, int, int, int, int] | None:
    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    if not ffprobe or not ffmpeg:
        return None

    probe = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0:s=x",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0 or "x" not in probe.stdout:
        return None
    try:
        image_width, image_height = map(int, probe.stdout.strip().split("x", 1))
    except ValueError:
        return None

    decoded = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-pix_fmt",
            "rgba",
            "-f",
            "rawvideo",
            "-",
        ],
        capture_output=True,
    )
    expected = image_width * image_height * 4
    if decoded.returncode != 0 or len(decoded.stdout) < expected:
        return None

    min_x = image_width
    min_y = image_height
    max_x = -1
    max_y = -1
    rgba = decoded.stdout
    for pixel_index in range(image_width * image_height):
        if rgba[pixel_index * 4 + 3] <= 8:
            continue
        x = pixel_index % image_width
        y = pixel_index // image_width
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)

    if max_x < min_x or max_y < min_y:
        return None

    content_width = max_x - min_x + 1
    content_height = max_y - min_y + 1
    padding = max(2, round(max(content_width, content_height) * 0.025))
    min_x = max(0, min_x - padding)
    min_y = max(0, min_y - padding)
    max_x = min(image_width - 1, max_x + padding)
    max_y = min(image_height - 1, max_y + padding)
    return (
        image_width,
        image_height,
        min_x,
        min_y,
        max_x - min_x + 1,
        max_y - min_y + 1,
    )


def chromium_binary() -> str | None:
    candidates = [
        os.environ.get("CHROME_BIN"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    return next((item for item in candidates if item and Path(item).exists()), None)


def render_png(svg_path: Path, png_path: Path, width: int, height: int) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    chrome = chromium_binary()
    if chrome:
        command = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            f"--window-size={width},{height}",
            f"--screenshot={png_path}",
            svg_path.resolve().as_uri(),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0 and png_path.exists():
            return
        raise RuntimeError(result.stderr.strip() or "Chromium PNG render failed.")

    rsvg = shutil.which("rsvg-convert")
    if rsvg:
        subprocess.run(
            [rsvg, "-w", str(width), "-h", str(height), "-o", str(png_path), str(svg_path)],
            check=True,
        )
        return

    raise RuntimeError("No Chromium-family browser or rsvg-convert renderer found.")


def build_svg(args: argparse.Namespace) -> str:
    width = args.width
    height = args.height
    scale = height / 1200.0
    left = width * 0.055
    gap = width * 0.04
    artwork_start = resolve_artwork_start(args.title, args.artwork_start)
    text_right = width * artwork_start - gap
    max_text_width = text_right - left

    label_size = (
        args.label_size
        if args.label_size is not None
        else fit_size(args.label, max_text_width, 88 * scale, 58 * scale, cjk=False)
    )
    title_is_cjk = has_cjk(args.title)
    preferred_title = (158 if title_is_cjk else 150) * scale
    minimum_title = 96 * scale
    title_size = (
        args.title_size
        if args.title_size is not None
        else fit_size(
            args.title,
            max_text_width,
            preferred_title,
            minimum_title,
            cjk=title_is_cjk,
        )
    )

    title_lines = [args.title]
    if (
        "\\n" in args.title
        or title_size <= minimum_title + 0.01
        or (not title_is_cjk and visual_units(args.title) > 10)
    ):
        title_lines = split_title(args.title)
        title_size = min(
            preferred_title,
            min(
                fit_size(
                    line,
                    max_text_width,
                    preferred_title,
                    minimum_title,
                    cjk=title_is_cjk,
                )
                for line in title_lines
            ),
        )

    subtitle_lines = [line for line in args.subtitle.split("\\n") if line.strip()]
    subtitle_size = (
        fit_size(
            max(subtitle_lines, key=visual_units),
            max_text_width,
            66 * scale,
            46 * scale,
            cjk=has_cjk(args.subtitle),
        )
        if subtitle_lines
        else 0.0
    )
    italic_title_lines = parse_italic_lines(args.italic_title_lines, len(title_lines))
    has_label = bool(args.label.strip())
    title_leading = title_size * 1.08
    title_block_height = title_size + (len(title_lines) - 1) * title_leading
    label_block_height = label_size if has_label else 0.0
    label_title_gap = title_size * 0.30 if has_label else 0.0
    subtitle_leading = subtitle_size * 1.34
    subtitle_block_height = (
        subtitle_size + (len(subtitle_lines) - 1) * subtitle_leading
        if subtitle_lines
        else 0.0
    )
    title_subtitle_gap = title_size * 0.45 if subtitle_lines else 0.0
    text_block_height = (
        label_block_height
        + label_title_gap
        + title_block_height
        + title_subtitle_gap
        + subtitle_block_height
    )
    text_block_top = (height - text_block_height) / 2

    if has_label:
        label_y = text_block_top + label_size * 0.78
        title_block_top = text_block_top + label_block_height + label_title_gap
        label_node = (
            f'<text x="{left:.1f}" y="{label_y:.1f}" class="label" '
            f'font-size="{label_size:.1f}">{html.escape(args.label)}</text>'
        )
    else:
        title_block_top = text_block_top
        label_node = ""

    title_ys = [
        title_block_top + title_size * 0.82 + index * title_leading
        for index in range(len(title_lines))
    ]

    title_nodes = "".join(
        f'<text x="{left:.1f}" y="{title_ys[index]:.1f}" '
        f'class="{"title-cjk" if title_is_cjk else "title-latin"}'
        f'{" title-italic" if index in italic_title_lines else ""}" '
        f'font-size="{title_size:.1f}">{html.escape(line)}</text>'
        for index, line in enumerate(title_lines)
    )
    subtitle_top = title_block_top + title_block_height + title_subtitle_gap
    subtitle_nodes = "".join(
        f'<text x="{left:.1f}" y="{subtitle_top + subtitle_size * 0.78 + index * subtitle_leading:.1f}" '
        f'class="subtitle" font-size="{subtitle_size:.1f}">{html.escape(line)}</text>'
        for index, line in enumerate(subtitle_lines)
    )
    artwork = data_uri(args.artwork)
    grid_start = width * resolve_grid_start(artwork_start, args.grid_start)
    grid_cell = height * args.grid_cell_ratio
    artwork_x = width * artwork_start
    artwork_y = height * args.artwork_y
    artwork_width = width * 0.985 - artwork_x
    artwork_height = height * args.artwork_height
    artwork_bounds = alpha_bounds(args.artwork)
    if artwork_bounds:
        (
            source_width,
            source_height,
            crop_x,
            crop_y,
            crop_width,
            crop_height,
        ) = artwork_bounds
        artwork_node = f'''
  <svg x="{artwork_x:.1f}" y="{artwork_y:.1f}" width="{artwork_width:.1f}" height="{artwork_height:.1f}"
       viewBox="{crop_x} {crop_y} {crop_width} {crop_height}" preserveAspectRatio="xMidYMid meet"
       overflow="visible">
    <image x="0" y="0" width="{source_width}" height="{source_height}" href="{artwork}"/>
  </svg>'''
    else:
        artwork_node = f'''
  <image x="{artwork_x:.1f}" y="{artwork_y:.1f}" width="{artwork_width:.1f}" height="{artwork_height:.1f}"
         preserveAspectRatio="xMidYMid meet" href="{artwork}"/>'''

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <title>{html.escape(args.label)} {html.escape(args.title)} {html.escape(args.subtitle)}</title>
  <defs>
    <pattern id="editorial-grid" width="{grid_cell:.1f}" height="{grid_cell:.1f}" patternUnits="userSpaceOnUse">
      <path d="M {grid_cell:.1f} 0 L 0 0 0 {grid_cell:.1f}" fill="none"
            stroke="{args.grid_color}" stroke-width="{args.grid_stroke * scale:.1f}"/>
    </pattern>
  </defs>
  <style>
    .label {{
      fill: #171714;
      font-family: Georgia, "Times New Roman", serif;
      font-weight: 700;
      letter-spacing: -0.032em;
    }}
    .title-cjk {{
      fill: #191916;
      font-family: "PingFang SC", "Hiragino Sans GB", "Source Han Sans SC", "Microsoft YaHei", sans-serif;
      font-weight: 800;
      letter-spacing: -0.032em;
    }}
    .title-latin {{
      fill: #191916;
      font-family: Georgia, "Times New Roman", serif;
      font-weight: 700;
      letter-spacing: -0.035em;
    }}
    .title-italic {{
      font-style: italic;
    }}
    .subtitle {{
      fill: #3F3E39;
      font-family: Georgia, "Times New Roman", serif;
      font-style: italic;
      font-weight: 700;
      letter-spacing: -0.025em;
    }}
  </style>
  <rect x="0" y="0" width="{width}" height="{height}" fill="{BACKGROUND_COLOR}"/>
  {"" if args.no_grid else f'<rect x="{grid_start:.1f}" y="0" width="{width - grid_start:.1f}" height="{height}" fill="url(#editorial-grid)"/>'}
  {artwork_node}
  {label_node}
  {title_nodes}
  {subtitle_nodes}
</svg>
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compose a 5:2 editorial cover from transparent artwork and exact text."
    )
    parser.add_argument("--artwork", required=True, type=Path)
    parser.add_argument("--label", default="", help="Optional short Latin/tool line.")
    parser.add_argument("--title", required=True, help=r"Use literal \\n for an intentional line break.")
    parser.add_argument("--subtitle", default="", help=r"Optional subtitle; use literal \\n for two lines.")
    parser.add_argument(
        "--italic-title-lines",
        default="",
        help="Optional comma-separated 1-based title line numbers to italicize.",
    )
    parser.add_argument("--output", required=True, type=Path, help="Self-contained SVG output.")
    parser.add_argument("--png", type=Path, help="Optional PNG output.")
    parser.add_argument("--width", type=int, default=3000)
    parser.add_argument("--height", type=int, default=1200)
    parser.add_argument(
        "--artwork-start",
        type=float,
        help="Artwork x-position as a canvas fraction; defaults adapt to title language and length.",
    )
    parser.add_argument(
        "--grid-start",
        type=float,
        help="Grid x-position as a canvas fraction; defaults adapt to the text/artwork split.",
    )
    parser.add_argument(
        "--grid-cell-ratio",
        type=float,
        default=DEFAULT_GRID_CELL_HEIGHT_RATIO,
        help="Grid-cell size as a fraction of canvas height.",
    )
    parser.add_argument(
        "--grid-color",
        default=GRID_COLOR,
        help="Grid stroke color as a hex value.",
    )
    parser.add_argument(
        "--grid-stroke",
        type=float,
        default=DEFAULT_GRID_STROKE,
        help="Grid stroke width at the default 3000 × 1200 canvas.",
    )
    parser.add_argument("--no-grid", action="store_true", help="Disable the grid.")
    parser.add_argument(
        "--artwork-y",
        type=float,
        default=0.07,
        help="Artwork box y-position as a canvas fraction.",
    )
    parser.add_argument(
        "--artwork-height",
        type=float,
        default=0.86,
        help="Artwork box height as a canvas fraction.",
    )
    parser.add_argument("--label-size", type=float)
    parser.add_argument("--title-size", type=float)
    args = parser.parse_args()

    if not args.artwork.is_file():
        parser.error("--artwork must point to an existing image.")
    if args.output.suffix.lower() != ".svg":
        parser.error("--output must use .svg.")
    if args.png and args.png.suffix.lower() != ".png":
        parser.error("--png must use .png.")
    if args.width < 1200 or args.height < 480 or args.width / args.height < 1.8:
        parser.error("Use a landscape canvas of at least 1200 × 480 and ratio >= 1.8:1.")
    if args.artwork_start is not None and not 0.48 <= args.artwork_start <= 0.75:
        parser.error("--artwork-start must be between 0.48 and 0.75.")
    if args.grid_start is not None and not 0.30 <= args.grid_start <= 0.65:
        parser.error("--grid-start must be between 0.30 and 0.65.")
    if not 0.045 <= args.grid_cell_ratio <= 0.16:
        parser.error("--grid-cell-ratio must be between 0.045 and 0.16.")
    if not (
        len(args.grid_color) == 7
        and args.grid_color.startswith("#")
        and all(char in "0123456789abcdefABCDEF" for char in args.grid_color[1:])
    ):
        parser.error("--grid-color must be a six-digit hex color.")
    if not 0.5 <= args.grid_stroke <= 4.0:
        parser.error("--grid-stroke must be between 0.5 and 4.0.")
    if not 0.0 <= args.artwork_y <= 0.30:
        parser.error("--artwork-y must be between 0 and 0.30.")
    if not 0.45 <= args.artwork_height <= 1.0:
        parser.error("--artwork-height must be between 0.45 and 1.0.")
    if args.artwork_y + args.artwork_height > 1.02:
        parser.error("--artwork-y plus --artwork-height must not exceed 1.02.")
    if args.label_size is not None and args.label_size <= 0:
        parser.error("--label-size must be positive.")
    if args.title_size is not None and args.title_size <= 0:
        parser.error("--title-size must be positive.")
    return args


def main() -> int:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_svg(args), encoding="utf-8")
    print(f"SVG: {args.output}")
    if args.png:
        try:
            render_png(args.output, args.png, args.width, args.height)
        except RuntimeError as exc:
            print(f"PNG pending: {exc}", file=sys.stderr)
            return 2
        print(f"PNG: {args.png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
