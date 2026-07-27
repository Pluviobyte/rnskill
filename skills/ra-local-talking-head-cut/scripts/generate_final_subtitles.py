#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("media", type=Path)
    ap.add_argument("--script", type=Path, required=True)
    ap.add_argument("--approval", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    approval = json.loads(args.approval.read_text())
    if approval.get("approved") is not True or approval.get("unresolved_terms"):
        raise SystemExit("Approved subtitles with zero unresolved terms are required.")
    if not args.media.exists() or not args.script.exists():
        raise SystemExit("Final media or approved script is missing.")

    skills_root = Path(__file__).resolve().parents[2]
    generator = skills_root / "ra-audio-to-subtitles" / "scripts" / "generate_subtitles.py"
    if not generator.exists():
        raise SystemExit(f"Missing subtitle dependency: {generator}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        sys.executable,
        str(generator),
        str(args.media),
        "--script", str(args.script),
        "--out-dir", str(args.out_dir),
    ], check=True)

    qc_path = args.out_dir / "caption-qc.json"
    if not qc_path.exists():
        raise SystemExit("Subtitle generator did not create caption-qc.json")
    qc = json.loads(qc_path.read_text())
    if str(qc.get("status", "")).lower() != "pass":
        raise SystemExit(f"Caption QC failed: {qc_path}")
    required = ["captions_words.json", "captions.json", "captions.srt", "captions.vtt"]
    missing = [name for name in required if not (args.out_dir / name).exists()]
    if missing:
        raise SystemExit(f"Missing subtitle artifacts: {', '.join(missing)}")
    print(f"caption_qc=pass out_dir={args.out_dir}")


if __name__ == "__main__":
    main()
