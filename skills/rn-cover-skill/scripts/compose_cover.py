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


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


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
    text_right = width * args.artwork_start - gap
    max_text_width = text_right - left

    label_size = (
        args.label_size
        if args.label_size is not None
        else fit_size(args.label, max_text_width, 102 * scale, 68 * scale, cjk=False)
    )
    preferred_title = 146 * scale
    title_size = (
        args.title_size
        if args.title_size is not None
        else fit_size(args.title, max_text_width, preferred_title, 88 * scale, cjk=True)
    )

    title_lines = [args.title]
    if "\\n" in args.title or title_size <= 88 * scale + 0.01:
        title_lines = split_title(args.title)
        title_size = min(
            preferred_title,
            min(
                fit_size(line, max_text_width, preferred_title, 88 * scale, cjk=True)
                for line in title_lines
            ),
        )

    if len(title_lines) == 1:
        label_y = height * 0.38
        title_ys = [height * 0.615]
        underline_y = height * 0.72
    else:
        label_y = height * 0.28
        title_ys = [height * 0.53, height * 0.70]
        underline_y = height * 0.81

    title_nodes = "".join(
        f'<text x="{left:.1f}" y="{title_ys[index]:.1f}" class="title" '
        f'font-size="{title_size:.1f}">{html.escape(line)}</text>'
        for index, line in enumerate(title_lines)
    )
    artwork = data_uri(args.artwork)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <title>{html.escape(args.label)} {html.escape(args.title)}</title>
  <style>
    .label {{
      fill: #171714;
      font-family: Georgia, "Times New Roman", serif;
      font-weight: 700;
      letter-spacing: -0.032em;
    }}
    .title {{
      fill: #191916;
      font-family: "PingFang SC", "Hiragino Sans GB", "Source Han Sans SC", "Microsoft YaHei", sans-serif;
      font-weight: 800;
      letter-spacing: -0.032em;
    }}
  </style>
  <image x="0" y="0" width="{width}" height="{height}" preserveAspectRatio="xMidYMid slice" href="{artwork}"/>
  <text x="{left:.1f}" y="{label_y:.1f}" class="label" font-size="{label_size:.1f}">{html.escape(args.label)}</text>
  {title_nodes}
  <line x1="{left:.1f}" y1="{underline_y:.1f}" x2="{left + 188 * scale:.1f}" y2="{underline_y:.1f}"
        stroke="#BEBBB3" stroke-width="{6 * scale:.1f}" stroke-linecap="square"/>
</svg>
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compose a 5:2 editorial workflow cover from generated artwork and exact text."
    )
    parser.add_argument("--artwork", required=True, type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--title", required=True, help=r"Use literal \\n for an intentional line break.")
    parser.add_argument("--output", required=True, type=Path, help="Self-contained SVG output.")
    parser.add_argument("--png", type=Path, help="Optional PNG output.")
    parser.add_argument("--width", type=int, default=3000)
    parser.add_argument("--height", type=int, default=1200)
    parser.add_argument("--artwork-start", type=float, default=0.68)
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
    if not 0.55 <= args.artwork_start <= 0.75:
        parser.error("--artwork-start must be between 0.55 and 0.75.")
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
