#!/usr/bin/env python3
"""Extract reusable presenter identity candidates from a raw avatar master."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path


def media_duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path),
    ], text=True).strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="Raw digital-human master, not a circular final composite")
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--timestamp", action="append", type=float, default=[])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    video = args.video.expanduser().resolve()
    if not video.is_file():
        raise SystemExit(f"Missing avatar video: {video}")
    duration = media_duration(video)
    timestamps = args.timestamp or [duration * ratio for ratio in (0.2, 0.4, 0.6, 0.8)]
    timestamps = [min(max(0.0, value), max(0.0, duration - 0.05)) for value in timestamps]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    frames: list[Path] = []
    for index, timestamp in enumerate(timestamps, start=1):
        output = args.out_dir / f"avatar-candidate-{index:02d}-{timestamp:07.3f}s.png"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-ss", f"{timestamp:.6f}",
            "-i", str(video), "-frames:v", "1", str(output),
        ], check=True)
        frames.append(output.resolve())

    columns = 2
    rows = math.ceil(len(frames) / columns)
    contact = (args.out_dir / "avatar-candidates-contact.jpg").resolve()
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-pattern_type", "glob",
        "-i", str(args.out_dir / "avatar-candidate-*.png"),
        "-vf", f"scale=640:360,tile={columns}x{rows}:padding=4:margin=4:color=white",
        "-frames:v", "1", str(contact),
    ], check=True)
    print(json.dumps({
        "video": str(video),
        "duration": duration,
        "frames": [str(path) for path in frames],
        "contact_sheet": str(contact),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
