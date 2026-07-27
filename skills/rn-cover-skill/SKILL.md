---
name: rn-cover-skill
description: Create warm-ivory editorial technology covers with large left-aligned typography and a newly generated compact workflow illustration on the far right, without requiring or passing any reference image. Use when the user asks for “编辑工作流风格封面”, “左文右图暖白封面”, “无参考图生成同类封面”, or wants a new cover resembling a premium AI research/editorial diagram style with charcoal dashed paths and a restrained coral accent. Generate fresh right-side artwork for every new cover, then compose exact text into editable SVG and PNG.
---

# RN Cover Skill

Create each cover from a written style contract, not an image reference. Use ImageGen for fresh right-side artwork and the bundled compositor for exact typography.

## Inputs

Resolve:

- `label`: short Latin/tool line, such as `Codex + Hyperframes + HeyGen:`
- `title`: Chinese benefit or topic headline
- `theme`: semantic concept for the right-side diagram
- `output directory`

Default to `3000 × 1200` (`5:2`). Split a combined title at `：` or `:` when the left part is mostly Latin/tool names and the right part is Chinese.

## Workflow

1. Plan the text before generating artwork.
   - Keep the Chinese title on one line whenever it fits at `96px` or larger.
   - Reserve 58–70% of the canvas for typography.
   - Make Chinese the primary focal point; keep the Latin label smaller.
2. Read [references/style-contract.md](references/style-contract.md).
3. Choose a fresh diagram topology from the topic semantics.
4. Call built-in ImageGen in **generate** mode with the assembled prompt only.
   - Omit `referenced_image_paths`.
   - Omit `num_last_images_to_include`.
   - Generate new artwork for every new cover. Never reuse a previous cover’s right-side artwork unless the user explicitly asks.
   - Request no text, letters, numbers, logos, or watermark in the generated base.
5. Copy the generated base into the output directory as `cover-artwork.png`.
6. Compose exact text:

```bash
python3 <skill-dir>/scripts/compose_cover.py \
  --artwork "/absolute/path/cover-artwork.png" \
  --label "Codex + Hyperframes + HeyGen:" \
  --title "开源自媒体涨粉的秘诀" \
  --output "/absolute/path/cover.svg" \
  --png "/absolute/path/cover.png"
```

Use `--artwork-start` to match the blank area requested from ImageGen. Run `--help` for overrides.

## Non-negotiable style

- Warm ivory paper-like background, never clinical pure white.
- Faint square grid only behind the right-side illustration.
- Charcoal dashed connectors, empty rounded nodes, one floating interface card.
- One restrained muted-coral outline or signal; no broad orange fills.
- Left typography expands horizontally; the illustration shrinks or moves right to yield space.
- Latin label uses one consistent heavy editorial serif.
- Chinese title uses a near-black heavy sans and carries more visual weight.
- No portraits, stickers, neon, glossy 3D, dense UI, or decorative copy.

Do not ask the image model to render final title text. Keep all real text in SVG.

## Regeneration rule

- **New cover:** always generate a new right-side illustration from scratch with no reference inputs.
- **Concept or layout revision:** regenerate the right-side illustration.
- **Minor typography-only correction:** reuse the current illustration unless the user asks for a new one.

Vary topology, node count, connector route, central object, and orange signal placement while preserving the style contract. Do not make a series look like the same diagram with only text swapped.

## Quality gate

1. Inspect the generated base before adding text. Reject pseudo-text, left-zone intrusion, clipped nodes, or an oversized diagram.
2. Inspect final PNG at full size and 25%.
3. Confirm every requested character and punctuation mark is exact.
4. Confirm Chinese remains readable first, Latin second, diagram third.
5. Confirm at least 4% canvas-width clearance between text and artwork.
6. Confirm SVG is editable/self-contained and PNG dimensions match.
7. Report the final paths, the no-reference ImageGen prompt, and that built-in ImageGen was used.
