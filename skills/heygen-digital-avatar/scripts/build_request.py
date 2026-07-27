#!/usr/bin/env python3
"""Build the locked Pluviobyte HeyGen request without making a network call."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PROFILE_PATH = SKILL_DIR / "references" / "pluviobyte-profile.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-asset-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--engine",
        choices=("avatar_iii", "avatar_iv", "avatar_v"),
        default="avatar_iii",
    )
    parser.add_argument(
        "--allow-premium-engine",
        action="store_true",
        help="Required guard when deliberately selecting Avatar IV or V.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.engine != "avatar_iii" and not args.allow_premium_engine:
        raise SystemExit(
            "Avatar IV/V requires --allow-premium-engine after user approval."
        )

    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    generation = profile["generation"]
    request = {
        "type": "avatar",
        "avatar_id": profile["avatar_look"]["id"],
        "audio_asset_id": args.audio_asset_id,
        "title": args.title,
        "resolution": generation["resolution"],
        "aspect_ratio": generation["aspect_ratio"],
        "fit": generation["fit"],
        "output_format": generation["output_format"],
        "engine": {"type": args.engine},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(args.output)


if __name__ == "__main__":
    main()
