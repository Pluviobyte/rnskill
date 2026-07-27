#!/usr/bin/env python3
"""Build style-aware, ratio-specific prompts for Skill-封面."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE_REGISTRY_PATH = ROOT / "references/style-registry.json"
GESTURE_REGISTRY_PATH = ROOT / "assets/shared/gestures/registry.json"


def load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Skill-封面 prompts")
    parser.add_argument("--style", default=None, help="Style slug, display name or alias")
    parser.add_argument("--title")
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--tag", default="AI 实测")
    parser.add_argument("--highlight", action="append", default=[])
    parser.add_argument("--gesture", default=None)
    parser.add_argument("--ratio", choices=["3:4", "4:3", "both"], default="both")
    parser.add_argument(
        "--reference-cover",
        type=Path,
        help="Use an arbitrary cover as style/layout reference instead of a registered base",
    )
    parser.add_argument(
        "--identity-image",
        type=Path,
        help="Project-specific presenter identity frame; required with --reference-cover",
    )
    parser.add_argument("--list-styles", action="store_true")
    parser.add_argument("--list-gestures", action="store_true")
    return parser.parse_args()


def resolve_style(registry: dict[str, object], requested: str | None) -> tuple[str, dict[str, object]]:
    styles = registry["styles"]
    target = requested or registry["default_style"]
    normalized = target.casefold()
    for slug, style in styles.items():
        candidates = [slug, style["display_name"], *style.get("aliases", [])]
        if normalized in {str(item).casefold() for item in candidates}:
            return slug, style
    choices = ", ".join(f"{slug}({item['display_name']})" for slug, item in styles.items())
    raise SystemExit(f"Unknown cover style: {target}. Registered styles: {choices}")


def load_gesture_manifest(entry: dict[str, object]) -> dict[str, object]:
    manifest_path = ROOT / entry["manifest"]
    if not manifest_path.is_file():
        raise SystemExit(f"Missing gesture manifest: {manifest_path}")
    return load_json(manifest_path)


def resolve_gesture(
    style: dict[str, object],
    gesture_registry: dict[str, object],
    requested: str | None,
) -> tuple[str, dict[str, object]]:
    gestures = gesture_registry["gestures"]
    allowed = set(style.get("allowed_gestures", gestures))
    target = requested or style.get("default_gesture") or gesture_registry["default_gesture"]
    normalized = target.casefold()
    for slug, entry in gestures.items():
        gesture = load_gesture_manifest(entry)
        candidates = [
            slug,
            gesture.get("id", slug),
            gesture["display_name"],
            *gesture.get("aliases", []),
        ]
        if normalized in {str(item).casefold() for item in candidates}:
            if slug not in allowed:
                choices = ", ".join(sorted(allowed))
                raise SystemExit(
                    f"Gesture '{target}' is not enabled for this style. Allowed gestures: {choices}"
                )
            if gesture.get("status") != "approved":
                raise SystemExit(f"Gesture '{target}' is not approved for production use")
            return slug, gesture
    choices = ", ".join(sorted(allowed))
    raise SystemExit(f"Unknown or unapproved gesture: {target}. Registered gestures: {choices}")


def assert_assets(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("Missing Skill-封面 assets:\n" + "\n".join(missing))


def build_prompt(
    args: argparse.Namespace,
    style_slug: str,
    style: dict[str, object],
    gesture_slug: str,
    gesture_spec: dict[str, object],
    ratio: str,
) -> dict[str, object]:
    ratio_spec = style["ratios"][ratio]
    base = ROOT / ratio_spec["base"]
    identity = ROOT / style["identity"]
    gesture_assets = gesture_spec["assets"]
    gesture = ROOT / gesture_assets["gesture_reference"]
    style_reference = ROOT / ratio_spec["style_reference"]
    framing_reference_value = gesture_assets.get("framing_references", {}).get(ratio)
    framing_reference = ROOT / framing_reference_value if framing_reference_value else None
    references = [base, identity, gesture]
    if framing_reference is not None:
        references.append(framing_reference)
    references.append(style_reference)
    assert_assets(references)

    highlights = "、".join(args.highlight) if args.highlight else "the most important result phrase"
    subtitle_line = (
        f'Subtitle: "{args.subtitle}"'
        if args.subtitle
        else "Do not render a subtitle; keep the subtitle zone blank."
    )

    if framing_reference is not None:
        framing_role = (
            "- Image 4 is the approved presenter-framing reference. Match only its presenter position, "
            "scale and visible upper-body range; never copy its title or subtitle.\n"
            "- Image 5 is style calibration only. Never copy its old text."
        )
    else:
        framing_role = "- Image 4 is style calibration only. Never copy its old text."
    framing_rule = gesture_spec.get("framing_rules", {}).get(ratio, "")
    framing_instruction = (
        f"\nApproved presenter framing for {gesture_slug}: {framing_rule}\n"
        if framing_rule
        else ""
    )
    gesture_constraints = "; ".join(gesture_spec.get("constraints", []))

    prompt = f'''Use case: compositing
Asset type: Chinese social-media video cover
Selected style: {style["display_name"]} ({style_slug})

Reference roles:
- Image 1 is the clean {ratio} base. Preserve its layout, background and graphic ornaments.
- Image 2 is the only identity reference. Preserve this exact face, center-parted black hair, skin tone and black T-shirt.
- Image 3 controls gesture only ({gesture_spec["display_name"]}, {gesture_slug}). It must not alter
  identity, clothing or facial structure. Gesture contract: {gesture_spec["description"]}
{framing_role}

{style["prompt_core"]}
{ratio_spec["composition"]}
{framing_instruction}
Place the same black-T presenter at lower-left with a clean realistic cutout. Keep the face unobstructed.
If hands are visible, they must be relaxed, proportional and anatomically correct; no fully spread palms or extra fingers.
Gesture constraints: {gesture_constraints}

Render all text verbatim, with no misspellings and no additional words:
Tag: "{args.tag}"
Title: "{args.title}"
{subtitle_line}

Use large black Chinese brush/editorial lettering for the title. Emphasize "{highlights}" in deep crimson.
Keep mobile-thumbnail legibility and safe margins. No glasses, identity drift, watermark, logo,
platform UI, old text, pseudo-text, random glyphs or unrelated decoration.'''

    return {
        "style": style_slug,
        "style_display_name": style["display_name"],
        "gesture": gesture_slug,
        "gesture_display_name": gesture_spec["display_name"],
        "gesture_asset": str(gesture.resolve()),
        "ratio": ratio,
        "prompt": prompt,
        "referenced_image_paths": [str(path.resolve()) for path in references],
    }


def build_reference_replacement_prompt(
    args: argparse.Namespace,
    ratio: str,
) -> dict[str, object]:
    if args.reference_cover is None or args.identity_image is None:
        raise SystemExit("--reference-cover requires --identity-image")
    reference_cover = args.reference_cover.expanduser().resolve()
    identity = args.identity_image.expanduser().resolve()
    assert_assets([reference_cover, identity])

    highlights = "、".join(args.highlight) if args.highlight else "the key model name and result phrase"
    subtitle_line = (
        f'Subtitle: "{args.subtitle}"'
        if args.subtitle
        else "Do not render a subtitle; keep the subtitle zone blank."
    )
    if ratio == "3:4":
        composition = (
            "Create a true 3:4 portrait redesign, not a crop. Place the presenter at lower-left, "
            "occupying about 36% of the canvas. Rebuild the title area in the center-right and upper area."
        )
    else:
        composition = (
            "Create a true 4:3 horizontal redesign, not a crop of the portrait version. Place the presenter "
            "on the left 34% and rebuild the title area on the center-right 66%."
        )

    prompt = f'''Use case: identity-preserve compositing
Asset type: Chinese social-media video cover, exact {ratio}
Mode: replace the reference-cover person and text

Reference roles:
- Image 1 is style and layout reference only. Preserve its visual language, background, materials,
  color hierarchy and editorial energy. Do not reuse its person, title, subtitle or other old words.
- Image 2 is the only presenter identity reference. Preserve this exact face, hair, skin tone,
  clothing and natural expression. Do not inherit a face, glasses or clothing from Image 1.

{composition}
Use a clean realistic presenter cutout. Keep the face unobstructed and prioritize identity accuracy
over inventing a new hand pose. Keep all text safely away from the presenter.

Render all text verbatim, with no misspellings and no additional words:
Tag: "{args.tag}"
Title: "{args.title}"
{subtitle_line}

Use strong mobile-thumbnail hierarchy. Emphasize "{highlights}" with the reference cover's accent color.
No watermark, logo, platform UI, old text, pseudo-text, random glyphs or unrelated decoration.'''

    return {
        "mode": "reference-cover-replacement",
        "ratio": ratio,
        "prompt": prompt,
        "referenced_image_paths": [str(reference_cover), str(identity)],
    }


def main() -> None:
    args = parse_args()
    style_registry = load_json(STYLE_REGISTRY_PATH)
    gesture_registry = load_json(GESTURE_REGISTRY_PATH)

    if args.list_styles:
        data = [
            {"slug": slug, "display_name": style["display_name"], "aliases": style.get("aliases", [])}
            for slug, style in style_registry["styles"].items()
        ]
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if args.list_gestures:
        data = []
        for slug, entry in gesture_registry["gestures"].items():
            gesture = load_gesture_manifest(entry)
            data.append(
                {
                    "slug": slug,
                    "display_name": gesture["display_name"],
                    "aliases": gesture.get("aliases", []),
                    "status": gesture.get("status"),
                    "supported_ratios": gesture.get("supported_ratios", []),
                }
            )
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if not args.title:
        raise SystemExit("--title is required unless a --list option is used")

    ratios = ["3:4", "4:3"] if args.ratio == "both" else [args.ratio]
    if args.reference_cover is not None:
        result = [build_reference_replacement_prompt(args, ratio) for ratio in ratios]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.identity_image is not None:
        raise SystemExit("--identity-image is currently supported only with --reference-cover")

    style_slug, style = resolve_style(style_registry, args.style)
    gesture_slug, gesture_spec = resolve_gesture(style, gesture_registry, args.gesture)
    result = [build_prompt(args, style_slug, style, gesture_slug, gesture_spec, ratio) for ratio in ratios]
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
