#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


TARGET_I = -16.0
TARGET_TP = -1.5
TARGET_LRA = 7.0


def run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=capture,
        stdout=subprocess.DEVNULL if not capture else subprocess.PIPE,
    )


def audio_prefix(denoise: bool) -> str:
    filters = ["highpass=f=70", "lowpass=f=16000"]
    if denoise:
        filters.append("afftdn=nr=6:nf=-35:tn=1")
    return ",".join(filters)


def measure(path: Path, denoise: bool) -> dict:
    filt = f"{audio_prefix(denoise)},loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json"
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", filt, "-f", "null", "-"],
        text=True,
        capture_output=True,
    )
    start, end = proc.stderr.rfind("{"), proc.stderr.rfind("}")
    if start < 0 or end <= start:
        raise RuntimeError("Unable to parse loudnorm measurement")
    return json.loads(proc.stderr[start:end + 1])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("edl", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--no-denoise", action="store_true")
    ap.add_argument("--keep-prenorm", action="store_true")
    ap.add_argument("--transitions", type=Path, help="visual-cut QC JSON or transition config")
    args = ap.parse_args()

    edl = json.loads(args.edl.read_text())
    if len(edl.get("sources", {})) != 1:
        raise SystemExit("This renderer currently accepts one source asset")
    source = Path(next(iter(edl["sources"].values())))
    ranges = edl["ranges"]
    if not ranges:
        raise SystemExit("EDL has no ranges")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    prenorm = args.out.with_suffix(".prenorm.mp4")

    transition_items = []
    if args.transitions:
        transition_data = json.loads(args.transitions.read_text())
        transition_items = transition_data.get("transitions", transition_data.get("recommended_transitions", []))
    if len(transition_items) > 3:
        raise SystemExit("At most three selective transitions are allowed")
    transitions: dict[int, float] = {}
    for item in transition_items:
        cut_number = int(item["after_range"])
        duration = float(item["duration"])
        if cut_number < 1 or cut_number >= len(ranges):
            raise SystemExit(f"Transition cut {cut_number} is outside the EDL")
        if cut_number in transitions:
            raise SystemExit(f"Duplicate transition after range {cut_number}")
        if not 0.08 <= duration <= 0.12:
            raise SystemExit(f"Transition duration must be 0.08-0.12s, got {duration}s")
        if item.get("transition", "fade") != "fade":
            raise SystemExit("Only the restrained fade transition is supported")
        transitions[cut_number] = duration

    parts = []
    durations = []
    for i, item in enumerate(ranges):
        start, end = float(item["start"]), float(item["end"])
        dur = end - start
        durations.append(dur)
        fade = min(0.015, max(0.003, dur / 4.0))
        parts.append(f"[0:v]trim=start={start:.4f}:end={end:.4f},setpts=PTS-STARTPTS,settb=AVTB[v{i}]")
        parts.append(
            f"[0:a]atrim=start={start:.4f}:end={end:.4f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d={fade:.4f},afade=t=out:st={max(0.0, dur-fade):.4f}:d={fade:.4f}[a{i}]"
        )
    if transitions:
        current_v, current_a = "v0", "a0"
        current_duration = durations[0]
        for i in range(1, len(ranges)):
            cut_number = i
            duration = transitions.get(cut_number, 0.0)
            next_v, next_a = f"v{i}", f"a{i}"
            out_v, out_a = f"vc{i}", f"ac{i}"
            if duration:
                if duration <= 0 or duration >= min(current_duration, durations[i]) / 2:
                    raise SystemExit(f"Invalid transition duration {duration}s after range {cut_number}")
                offset = current_duration - duration
                parts.append(
                    f"[{current_v}][{next_v}]xfade=transition=fade:duration={duration:.4f}:offset={offset:.4f}[{out_v}]"
                )
                parts.append(
                    f"[{current_a}][{next_a}]acrossfade=d={duration:.4f}:c1=tri:c2=tri[{out_a}]"
                )
                current_duration += durations[i] - duration
            else:
                parts.append(f"[{current_v}][{next_v}]concat=n=2:v=1:a=0[{out_v}]")
                parts.append(f"[{current_a}][{next_a}]concat=n=2:v=0:a=1[{out_a}]")
                current_duration += durations[i]
            current_v, current_a = out_v, out_a
        parts.append(f"[{current_v}]null[vout]")
        parts.append(f"[{current_a}]anull[aout]")
    else:
        concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(len(ranges)))
        parts.append(concat_inputs + f"concat=n={len(ranges)}:v=1:a=1[vout][aout]")
    filter_complex = ";".join(parts)

    run([
        "ffmpeg", "-y", "-hide_banner", "-nostats", "-i", str(source),
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", str(prenorm),
    ])

    denoise = not args.no_denoise
    m = measure(prenorm, denoise)
    prefix = audio_prefix(denoise)
    loudnorm = (
        f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}"
        f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
        f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
        f":offset={m['target_offset']}:linear=true"
    )
    run([
        "ffmpeg", "-y", "-hide_banner", "-nostats", "-i", str(prenorm),
        "-c:v", "copy", "-af", f"{prefix},{loudnorm}",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", str(args.out),
    ])
    if not args.keep_prenorm:
        prenorm.unlink(missing_ok=True)
    transition_total = sum(transitions.values())
    print(
        f"output={args.out} measured_before={m['input_i']}LUFS target={TARGET_I}LUFS "
        f"denoise={denoise} transitions={len(transitions)} transition_overlap={transition_total:.3f}s"
    )


if __name__ == "__main__":
    main()
