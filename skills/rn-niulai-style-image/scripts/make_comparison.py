#!/usr/bin/env python3
"""Create a labeled source/reference/generated comparison sheet."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def panel(path: Path, label: str, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    canvas = Image.new("RGB", size, "#eeeeee")
    fitted = ImageOps.contain(image, (size[0] - 24, size[1] - 60))
    x = (size[0] - fitted.width) // 2
    y = 16 + (size[1] - 60 - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    ImageDraw.Draw(canvas).text((12, size[1] - 34), label, fill="#111111")
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--generated", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=460)
    args = parser.parse_args()

    size = (args.width, args.height)
    sheet = Image.new("RGB", (size[0] * 3, size[1]), "#ffffff")
    for index, (path, label) in enumerate(
        ((args.source, "SOURCE"), (args.reference, "STYLE REFERENCE"), (args.generated, "GENERATED"))
    ):
        sheet.paste(panel(path, label, size), (index * size[0], 0))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, quality=92)


if __name__ == "__main__":
    main()
