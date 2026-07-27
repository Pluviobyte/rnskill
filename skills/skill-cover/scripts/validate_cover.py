#!/usr/bin/env python3
"""Validate dimensions and ratios for a Skill-封面 cover pair."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def dimensions(path: Path) -> tuple[int, int]:
    if not path.is_file():
        raise ValueError(f"File not found: {path}")
    command = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", str(path),
    ]
    data = json.loads(subprocess.check_output(command, text=True))
    stream = data["streams"][0]
    return int(stream["width"]), int(stream["height"])


def check(path: Path, expected: float, label: str, min_short_edge: int) -> dict[str, object]:
    width, height = dimensions(path)
    actual = width / height
    ratio_ok = abs(actual - expected) <= 0.002
    resolution_ok = min(width, height) >= min_short_edge
    return {
        "label": label,
        "path": str(path.resolve()),
        "width": width,
        "height": height,
        "ratio": round(actual, 6),
        "ratio_ok": ratio_ok,
        "resolution_ok": resolution_ok,
        "pass": ratio_ok and resolution_ok,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Skill-封面 cover pair")
    parser.add_argument("--three-by-four", required=True, type=Path)
    parser.add_argument("--four-by-three", required=True, type=Path)
    parser.add_argument("--min-short-edge", type=int, default=1000)
    args = parser.parse_args()

    try:
        results = [
            check(args.three_by_four, 3 / 4, "3:4", args.min_short_edge),
            check(args.four_by_three, 4 / 3, "4:3", args.min_short_edge),
        ]
    except (ValueError, subprocess.CalledProcessError, KeyError, IndexError) as error:
        print(json.dumps({"pass": False, "error": str(error)}, ensure_ascii=False, indent=2))
        raise SystemExit(1) from error

    passed = all(item["pass"] for item in results)
    print(json.dumps({"pass": passed, "results": results}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
