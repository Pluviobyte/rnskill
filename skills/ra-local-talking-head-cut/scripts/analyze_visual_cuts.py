#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit("NumPy and Pillow are required. Run with the Codex bundled Python runtime.") from exc


def output_cut_times(ranges: list[dict]) -> list[dict]:
    rows = []
    timeline = 0.0
    for index in range(1, len(ranges)):
        timeline += float(ranges[index - 1]["end"]) - float(ranges[index - 1]["start"])
        rows.append({
            "after_range": index,
            "output_time": timeline,
            "source_gap": float(ranges[index]["start"]) - float(ranges[index - 1]["end"]),
        })
    return rows


def extract_frame(video: Path, at: float, out: Path, width: int) -> None:
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, at):.4f}", "-i", str(video),
         "-frames:v", "1", "-vf", f"scale={width}:-1", str(out)],
        check=True,
    )


def font(size: int):
    for path in ("/System/Library/Fonts/STHeiti Light.ttc", "/System/Library/Fonts/PingFang.ttc"):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path, help="hard-cut preview before burned captions")
    ap.add_argument("--edl", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--sample-offset", type=float, default=0.06)
    ap.add_argument("--threshold", type=float, default=20.0)
    ap.add_argument("--max-transitions", type=int, default=3)
    ap.add_argument("--sheet-count", type=int, default=8)
    args = ap.parse_args()

    if not 0 <= args.max_transitions <= 3:
        raise SystemExit("--max-transitions must be between 0 and 3")
    if args.sample_offset <= 0:
        raise SystemExit("--sample-offset must be positive")
    if args.threshold < 0:
        raise SystemExit("--threshold must be non-negative")

    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            raise SystemExit(f"{binary} is required")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    frame_dir = args.out_dir / "cut-frames"
    frame_dir.mkdir(exist_ok=True)
    ranges = json.loads(args.edl.read_text())["ranges"]
    rows = output_cut_times(ranges)
    width = 480
    for row in rows:
        cut = row["after_range"]
        before = frame_dir / f"cut-{cut:02d}-before.png"
        after = frame_dir / f"cut-{cut:02d}-after.png"
        extract_frame(args.video, row["output_time"] - args.sample_offset, before, width)
        extract_frame(args.video, row["output_time"] + args.sample_offset, after, width)
        left = np.asarray(Image.open(before).convert("RGB"), dtype=np.int16)
        right = np.asarray(Image.open(after).convert("RGB"), dtype=np.int16)
        delta = np.abs(right - left)
        row["mean_abs_diff"] = round(float(delta.mean()), 4)
        row["p95_abs_diff"] = round(float(np.percentile(delta, 95)), 4)

    ranked = sorted(rows, key=lambda item: item["mean_abs_diff"], reverse=True)
    selected = ranked[:max(0, args.max_transitions)]
    transitions = []
    for row in selected:
        if row["mean_abs_diff"] < args.threshold:
            continue
        transitions.append({
            "after_range": row["after_range"],
            "duration": 0.12 if row["mean_abs_diff"] >= 40 else 0.08,
            "transition": "fade",
            "reason": "large visual discontinuity at an otherwise valid semantic cut",
            "mean_abs_diff": row["mean_abs_diff"],
        })

    report = {
        "status": "pass",
        "source_video": str(args.video),
        "cut_count": len(rows),
        "threshold": args.threshold,
        "recommended_transitions": transitions,
        "scores": rows,
    }
    (args.out_dir / "visual-cut-qc.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    top = ranked[:min(args.sheet_count, len(ranked))]
    if top:
        sample = Image.open(frame_dir / f"cut-{top[0]['after_range']:02d}-before.png").convert("RGB")
        w, h = sample.size
        header = 44
        sheet = Image.new("RGB", (w * 2, (h + header) * len(top)), (245, 245, 245))
        draw = ImageDraw.Draw(sheet)
        title_font, small_font = font(20), font(15)
        for row_index, row in enumerate(top):
            cut = row["after_range"]
            y = row_index * (h + header)
            before = Image.open(frame_dir / f"cut-{cut:02d}-before.png").convert("RGB")
            after = Image.open(frame_dir / f"cut-{cut:02d}-after.png").convert("RGB")
            sheet.paste(before, (0, y + header))
            sheet.paste(after, (w, y + header))
            draw.text((10, y + 2), f"Cut {cut}  {row['output_time']:.2f}s  diff {row['mean_abs_diff']:.2f}", font=title_font, fill=(20, 20, 20))
            draw.text((10, y + 24), "左：切前 60ms    右：切后 60ms", font=small_font, fill=(80, 80, 80))
        sheet.save(args.out_dir / "visual-cut-contact-sheet.png")

    print(f"cuts={len(rows)} transitions={len(transitions)} max_diff={ranked[0]['mean_abs_diff'] if ranked else 0}")


if __name__ == "__main__":
    main()
