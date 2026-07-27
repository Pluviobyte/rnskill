#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from fractions import Fraction
from pathlib import Path


def probe(path: Path) -> dict:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
        "-of", "json", str(path),
    ], text=True)
    data = json.loads(raw)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    return {"video": video, "audio": audio, "format": data["format"]}


def loudness(path: Path) -> tuple[float, float]:
    proc = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
        "-filter_complex", "ebur128=peak=true", "-f", "null", "-",
    ], text=True, capture_output=True)
    integrated = peak = None
    for line in proc.stderr.splitlines()[-20:]:
        text = line.strip()
        if text.startswith("I:"):
            integrated = float(text.split()[1])
        elif text.startswith("Peak:"):
            peak = float(text.split()[1])
    if integrated is None or peak is None:
        raise RuntimeError("Unable to measure EBU R128 loudness")
    return integrated, peak


def fps_value(value: str) -> float:
    return float(Fraction(value))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--edl", type=Path, required=True)
    ap.add_argument("--transitions", type=Path, help="visual-cut QC JSON or transition config")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    src, out = probe(args.source), probe(args.output)
    edl = json.loads(args.edl.read_text())
    measured_i, measured_peak = loudness(args.output)
    transition_items = []
    if args.transitions:
        transition_data = json.loads(args.transitions.read_text())
        transition_items = transition_data.get("transitions", transition_data.get("recommended_transitions", []))
    if len(transition_items) > 3:
        raise SystemExit("At most three selective transitions are allowed")
    transition_keys: set[int] = set()
    for item in transition_items:
        cut_number = int(item["after_range"])
        duration = float(item["duration"])
        if cut_number < 1 or cut_number >= len(edl["ranges"]):
            raise SystemExit(f"Transition cut {cut_number} is outside the EDL")
        if cut_number in transition_keys:
            raise SystemExit(f"Duplicate transition after range {cut_number}")
        if not 0.08 <= duration <= 0.12:
            raise SystemExit(f"Transition duration must be 0.08-0.12s, got {duration}s")
        transition_keys.add(cut_number)
    transition_overlap = sum(float(item["duration"]) for item in transition_items)
    expected_duration = float(edl["total_duration_s"]) - transition_overlap
    actual_duration = float(out["format"]["duration"])
    checks = {
        "has_video": out["video"] is not None,
        "has_audio": out["audio"] is not None,
        "same_dimensions": (
            src["video"]["width"], src["video"]["height"]
        ) == (
            out["video"]["width"], out["video"]["height"]
        ),
        "same_frame_rate": abs(
            fps_value(src["video"]["r_frame_rate"]) - fps_value(out["video"]["r_frame_rate"])
        ) < 0.01,
        "duration_matches_edl": abs(actual_duration - expected_duration) <= 1.0,
        "loudness_in_range": -17.5 <= measured_i <= -14.5,
        "true_peak_safe": measured_peak <= -0.5,
    }
    status = "pass" if all(checks.values()) else "fail"
    report = {
        "status": status,
        "checks": checks,
        "source": src,
        "output": out,
        "expected_duration_s": expected_duration,
        "transition_count": len(transition_items),
        "transition_overlap_s": round(transition_overlap, 3),
        "actual_duration_s": actual_duration,
        "integrated_loudness_lufs": measured_i,
        "true_peak_dbfs": measured_peak,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "cut-qc.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    interval = max(actual_duration / 9.0, 0.5)
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(args.output),
        "-vf", f"fps=1/{interval:.6f},scale=600:-1,tile=3x3:nb_frames=9",
        "-frames:v", "1", str(args.out_dir / "contact-sheet.png"),
    ], check=True)
    print(f"status={status} loudness={measured_i:.1f}LUFS peak={measured_peak:.1f}dBFS duration={actual_duration:.3f}s")
    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
