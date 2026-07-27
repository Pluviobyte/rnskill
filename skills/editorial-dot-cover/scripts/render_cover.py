#!/usr/bin/env python3
"""Render an editable editorial-dot cover as SVG and optionally PNG."""

from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import shutil
import subprocess
import sys


DEFAULT_EN_FONT = "Roboto Slab, Rockwell, Noto Serif, serif"
DEFAULT_CN_FONT = (
    "YouSheBiaoTiHei, ZCOOL KuaiLe, Alimama ShuHeiTi, "
    "Source Han Sans SC, PingFang SC, Microsoft YaHei, sans-serif"
)


def visual_units(text: str) -> float:
    units = 0.0
    for char in text:
        code = ord(char)
        if char.isspace():
            units += 0.34
        elif char in "·:：!！,，.。+—-":
            units += 0.52
        elif code > 0x2E7F:
            units += 1.0
        elif char.isupper():
            units += 0.68
        else:
            units += 0.57
    return max(units, 1.0)


def fit_size(text: str, max_width: float, preferred: float, minimum: float) -> float:
    estimate = max_width / visual_units(text) * 1.06
    return max(minimum, min(preferred, estimate))


def xml_font_stack(value: str) -> str:
    return ", ".join(
        f"'{part.strip()}'" if " " in part.strip() else part.strip()
        for part in value.split(",")
        if part.strip()
    )


def build_svg(args: argparse.Namespace) -> str:
    width = args.width
    height = args.height
    scale = height / 1267.0
    left = width * 0.054
    icon_left = width * 0.755
    icon_width = width * 0.195
    gap = width * 0.04
    max_text_width = icon_left - gap - left

    title_lines = args.title.split("\\n")
    if len(title_lines) > 2:
        raise ValueError("The title supports at most two explicit lines.")

    label_size = (
        float(args.label_size)
        if args.label_size is not None
        else fit_size(args.label, max_text_width, 145 * scale, 94 * scale)
    )
    title_sizes = [
        (
            float(args.title_size)
            if args.title_size is not None
            else fit_size(line, max_text_width, 174 * scale, 92 * scale)
        )
        for line in title_lines
    ]

    label_height = label_size * 0.96
    title_heights = [size * 1.06 for size in title_sizes]
    label_gap = 48 * scale
    title_gap = 20 * scale
    group_height = label_height + label_gap + sum(title_heights)
    if len(title_lines) == 2:
        group_height += title_gap
    group_top = (height - group_height) / 2

    label_y = group_top + label_size * 0.79
    title_y = group_top + label_height + label_gap + title_sizes[0] * 0.84

    title_nodes = []
    current_y = title_y
    for index, line in enumerate(title_lines):
        title_nodes.append(
            f'<text x="{left:.1f}" y="{current_y:.1f}" class="title" '
            f'font-size="{title_sizes[index]:.1f}">{html.escape(line)}</text>'
        )
        current_y += title_heights[index] + title_gap

    icon_center_x = icon_left + icon_width * 0.52
    icon_center_y = height * 0.50
    icon_scale = min(icon_width / 610.0, height * 0.39 / 500.0)
    icon_transform = (
        f"translate({icon_center_x:.1f} {icon_center_y:.1f}) "
        f"scale({icon_scale:.4f}) translate(-305 -250)"
    )

    bg = html.escape(args.background)
    fg = html.escape(args.foreground)
    font_en = html.escape(xml_font_stack(args.font_en))
    font_cn = html.escape(xml_font_stack(args.font_cn))

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <radialGradient id="paperGlow" cx="52%" cy="46%" r="78%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.09"/>
      <stop offset="70%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="100%" stop-color="#5b5144" stop-opacity="0.055"/>
    </radialGradient>
    <filter id="paperGrain" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.011 0.018" numOctaves="3" seed="17" result="noise"/>
      <feColorMatrix in="noise" type="saturate" values="0" result="grayNoise"/>
      <feComponentTransfer in="grayNoise" result="faintNoise">
        <feFuncA type="table" tableValues="0 0.045"/>
      </feComponentTransfer>
      <feBlend in="SourceGraphic" in2="faintNoise" mode="multiply"/>
    </filter>
    <style>
      .label {{
        fill: {fg};
        font-family: {font_en};
        font-weight: 900;
        letter-spacing: -0.035em;
      }}
      .title {{
        fill: {fg};
        font-family: {font_cn};
        font-weight: 900;
        letter-spacing: -0.055em;
      }}
      .dots {{
        fill: none;
        stroke: {fg};
        stroke-width: 10;
        stroke-linecap: round;
        stroke-linejoin: round;
        stroke-dasharray: 1 18;
      }}
      .perforation {{ fill: {fg}; }}
    </style>
  </defs>

  <rect width="{width}" height="{height}" fill="{bg}"/>
  <rect width="{width}" height="{height}" fill="url(#paperGlow)" filter="url(#paperGrain)"/>

  <g aria-label="cover text">
    <text x="{left:.1f}" y="{label_y:.1f}" class="label" font-size="{label_size:.1f}">{html.escape(args.label)}</text>
    {''.join(title_nodes)}
  </g>

  <g aria-label="dotted analysis pictogram" transform="{icon_transform}">
    <path class="dots" d="M34 118 H170 V356 H34 Z"/>
    <path class="dots" d="M440 118 H576 V356 H440 Z"/>
    <path class="dots" d="M34 154 H170 M34 320 H170 M440 154 H576 M440 320 H576"/>

    <g class="perforation">
      <circle cx="62" cy="136" r="5"/><circle cx="100" cy="136" r="5"/><circle cx="138" cy="136" r="5"/>
      <circle cx="62" cy="338" r="5"/><circle cx="100" cy="338" r="5"/><circle cx="138" cy="338" r="5"/>
      <circle cx="468" cy="136" r="5"/><circle cx="506" cy="136" r="5"/><circle cx="544" cy="136" r="5"/>
      <circle cx="468" cy="338" r="5"/><circle cx="506" cy="338" r="5"/><circle cx="544" cy="338" r="5"/>
    </g>

    <circle class="dots" cx="305" cy="226" r="151"/>
    <circle class="dots" cx="305" cy="226" r="118"/>
    <path class="dots" d="M244 226 A61 61 0 0 1 305 165"/>
    <path class="dots" d="M414 335 L535 456 Q551 472 566 456 Q581 441 565 425 L444 304"/>
  </g>
</svg>
'''


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

    raise RuntimeError(
        "No PNG renderer found. Install Chromium/Google Chrome or rsvg-convert; the SVG is complete."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a warm-gray editorial cover with dotted analysis artwork."
    )
    parser.add_argument("--label", required=True, help="English or tool label.")
    parser.add_argument(
        "--title",
        required=True,
        help=r"Chinese headline. Use a literal \\n for one intentional line break.",
    )
    parser.add_argument("--output", required=True, type=Path, help="Editable SVG output path.")
    parser.add_argument("--png", type=Path, help="Optional rendered PNG output path.")
    parser.add_argument("--width", type=int, default=3168)
    parser.add_argument("--height", type=int, default=1267)
    parser.add_argument("--background", default="#D6D0C5")
    parser.add_argument("--foreground", default="#050505")
    parser.add_argument("--font-en", default=DEFAULT_EN_FONT)
    parser.add_argument("--font-cn", default=DEFAULT_CN_FONT)
    parser.add_argument("--label-size", type=float, help="Optional label font size in output pixels.")
    parser.add_argument("--title-size", type=float, help="Optional title font size in output pixels.")
    args = parser.parse_args()
    if args.width < 1000 or args.height < 500:
        parser.error("Use a canvas of at least 1000 × 500 for reliable typography.")
    if args.width / args.height < 1.5:
        parser.error("This renderer supports landscape covers with a ratio of at least 1.5:1.")
    if args.output.suffix.lower() != ".svg":
        parser.error("--output must use the .svg extension.")
    if args.png and args.png.suffix.lower() != ".png":
        parser.error("--png must use the .png extension.")
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
