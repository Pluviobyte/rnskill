#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def probe_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(path)
    ], text=True)
    return float(out.strip())


def load_words(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    words = data.get("words", data) if isinstance(data, dict) else data
    if not isinstance(words, list):
        raise SystemExit("ASR JSON must contain a words array")
    return words


def is_gap(item: dict) -> bool:
    return bool(item.get("isGap")) or item.get("type") in {"spacing", "gap"}


def merge_intervals(intervals: list[tuple[float, float]], tolerance: float = 0.02) -> list[tuple[float, float]]:
    merged: list[list[float]] = []
    for start, end in sorted((max(0.0, s), e) for s, e in intervals if e > s):
        if not merged or start > merged[-1][1] + tolerance:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(s, e) for s, e in merged]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("words_json", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--approval", type=Path, required=True)
    ap.add_argument("--decisions", type=Path)
    ap.add_argument("--compress-above", type=float, default=0.55)
    ap.add_argument("--medium-pause", type=float, default=0.38)
    ap.add_argument("--long-pause", type=float, default=0.45)
    ap.add_argument("--long-threshold", type=float, default=1.2)
    args = ap.parse_args()

    if not args.approval.exists():
        raise SystemExit("Subtitle approval missing. Review precut-review.srt before editing.")
    approval = json.loads(args.approval.read_text())
    if approval.get("approved") is not True:
        raise SystemExit("Subtitle approval is pending. Do not build EDL or cut video.")
    if approval.get("unresolved_terms"):
        raise SystemExit("Subtitle approval still has unresolved terms. Resolve them before editing.")

    source = args.source.resolve()
    duration = probe_duration(source)
    words = load_words(args.words_json)
    spoken = [(i, w) for i, w in enumerate(words) if not is_gap(w) and str(w.get("text", "")).strip()]
    if not spoken:
        raise SystemExit("No spoken words in transcript")

    removal: list[tuple[float, float]] = []
    first_start = float(spoken[0][1]["start"])
    last_end = float(spoken[-1][1]["end"])
    removal.append((0.0, max(0.0, first_start - 0.12)))
    removal.append((min(duration, last_end + 0.18), duration))

    for word in words:
        if not is_gap(word):
            continue
        start, end = float(word["start"]), float(word["end"])
        gap = end - start
        if gap <= args.compress_above:
            continue
        target = args.medium_pause if gap <= args.long_threshold else args.long_pause
        target = min(target, gap)
        removal.append((start + target / 2.0, end - target / 2.0))

    fillers = {"呃", "额"}
    spoken_positions = {idx: pos for pos, (idx, _) in enumerate(spoken)}
    auto_deleted: list[int] = []
    for idx, word in spoken:
        if str(word.get("text", "")).strip() not in fillers:
            continue
        pos = spoken_positions[idx]
        prev_end = float(spoken[pos - 1][1]["end"]) if pos > 0 else float(word["start"])
        next_start = float(spoken[pos + 1][1]["start"]) if pos + 1 < len(spoken) else float(word["end"])
        start = min(float(word["start"]), prev_end + 0.02)
        end = max(float(word["end"]), next_start - 0.04)
        removal.append((start, end))
        auto_deleted.append(idx)

    decision_indexes: list[int] = []
    if args.decisions and args.decisions.exists():
        decisions = json.loads(args.decisions.read_text())
        decision_indexes = [int(i) for i in decisions.get("delete_word_indices", [])]
        for idx in decision_indexes:
            if idx < 0 or idx >= len(words) or is_gap(words[idx]):
                continue
            pos = spoken_positions.get(idx)
            if pos is None:
                continue
            prev_end = float(spoken[pos - 1][1]["end"]) if pos > 0 else float(words[idx]["start"])
            next_start = float(spoken[pos + 1][1]["start"]) if pos + 1 < len(spoken) else float(words[idx]["end"])
            start = min(float(words[idx]["start"]), prev_end + 0.02)
            end = max(float(words[idx]["end"]), next_start - 0.04)
            removal.append((start, end))

    merged = merge_intervals(removal)
    keeps: list[tuple[float, float]] = []
    cursor = 0.0
    for start, end in merged:
        start, end = max(0.0, start), min(duration, end)
        if start - cursor >= 0.08:
            keeps.append((cursor, start))
        cursor = max(cursor, end)
    if duration - cursor >= 0.08:
        keeps.append((cursor, duration))

    ranges = [
        {"source": source.stem, "start": round(s, 4), "end": round(e, 4), "reason": "adaptive local talking-head cut"}
        for s, e in keeps
    ]
    total = sum(e - s for s, e in keeps)
    edl = {
        "version": 1,
        "sources": {source.stem: str(source)},
        "ranges": ranges,
        "total_duration_s": round(total, 4),
        "pacing": {
            "compress_above_s": args.compress_above,
            "medium_pause_s": args.medium_pause,
            "long_pause_s": args.long_pause,
            "long_threshold_s": args.long_threshold,
        },
        "automatic_filler_word_indices": auto_deleted,
        "semantic_delete_word_indices": decision_indexes,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(edl, ensure_ascii=False, indent=2) + "\n")
    print(f"ranges={len(ranges)} duration={total:.3f}s removed={duration-total:.3f}s fillers={len(auto_deleted)}")


if __name__ == "__main__":
    main()
