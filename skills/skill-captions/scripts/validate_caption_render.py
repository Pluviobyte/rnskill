#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=index,codec_type,width,height,duration:format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    video = next(
        stream for stream in data["streams"] if stream["codec_type"] == "video"
    )
    return {
        "width": int(video["width"]),
        "height": int(video["height"]),
        "duration": float(data["format"]["duration"]),
        "has_audio": any(
            stream["codec_type"] == "audio" for stream in data["streams"]
        ),
    }


def count_captions(path: Path) -> int:
    if path.suffix.lower() == ".srt":
        content = path.read_text(encoding="utf-8-sig").strip()
        return sum(
            1
            for block in re.split(r"\n\s*\n", content)
            if "-->" in block
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return 0
    return sum(
        1
        for item in data
        if isinstance(item, dict)
        and all(key in item for key in ("start", "end", "text"))
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a burned caption render.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--render", type=Path, required=True)
    parser.add_argument("--captions", type=Path, required=True)
    parser.add_argument("--qc", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--style", default="anchor-dark")
    args = parser.parse_args()

    errors: list[str] = []
    for path in (args.source, args.render, args.captions, args.qc):
        if not path.is_file():
            errors.append(f"missing:{path}")

    source_info = probe(args.source) if args.source.is_file() else {}
    render_info = probe(args.render) if args.render.is_file() else {}
    qc = (
        json.loads(args.qc.read_text(encoding="utf-8"))
        if args.qc.is_file()
        else {}
    )
    caption_count = count_captions(args.captions) if args.captions.is_file() else 0

    if str(qc.get("status", "")).lower() != "pass":
        errors.append("caption-qc-not-pass")
    if qc.get("timing_source") not in (None, "volcengine-word-timestamps"):
        errors.append("unexpected-timing-source")
    coverage = qc.get("alignment_coverage")
    if coverage is not None and float(coverage) < 0.90:
        errors.append("alignment-coverage-below-0.90")
    if source_info and render_info:
        if (source_info["width"], source_info["height"]) != (
            render_info["width"],
            render_info["height"],
        ):
            errors.append("resolution-changed")
        if abs(source_info["duration"] - render_info["duration"]) > 0.10:
            errors.append("duration-changed")
        if source_info["has_audio"] and not render_info["has_audio"]:
            errors.append("audio-stream-missing")
    if caption_count == 0:
        errors.append("captions-empty-or-invalid")

    report = {
        "status": "pass" if not errors else "fail",
        "style": args.style,
        "fixed_bottom_anchor": True,
        "native_resolution_scaling": True,
        "source": str(args.source.resolve()) if args.source.exists() else str(args.source),
        "render": str(args.render.resolve()) if args.render.exists() else str(args.render),
        "source_media": source_info,
        "render_media": render_info,
        "caption_count": caption_count,
        "caption_qc_status": qc.get("status"),
        "alignment_coverage": coverage,
        "errors": errors,
        "manual_checks": [
            "panel-wraps-text",
            "style-surface-matches-registry",
            "shadow-is-none-or-subtle-as-registered",
            "bottom-anchor-consistent",
            "no-content-or-avatar-overlap",
            "longest-cue-within-two-lines",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"status={report['status']} report={args.out}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
