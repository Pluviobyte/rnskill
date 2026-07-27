---
name: rn-cover-skill
description: Create reference-free 5:2 editorial technology covers with exact #FAF9F5 backgrounds, large left-aligned typography, adaptable grid geometry, and a newly generated right-side diagram. Use when the user asks for “RN封面”, “编辑图解风格封面”, “左文右图暖白封面”, “无参考图生成同类封面”, or a premium AI research/editorial cover with charcoal paths and a restrained coral accent. Generate fresh transparent right-side artwork for each new cover, then compose exact text and a flexible editorial layout into editable SVG and PNG.
---

# RN Cover Skill

Create each cover from a written style contract, not an image reference. Use ImageGen only for fresh right-side artwork. Use the bundled compositor for the exact background and controlled but adjustable grid, geometry, and typography.

## Inputs

Resolve:

- `label`: optional short Latin/tool line, such as `Codex + Hyperframes + HeyGen:`
- `title`: Chinese benefit or topic headline
- `subtitle`: optional one- or two-line supporting sentence
- `theme`: semantic concept for the right-side diagram
- `output directory`

Default to `3000 × 1200` (`5:2`). Split a combined title at `：` or `:` when the left part is mostly Latin/tool names and the right part is Chinese.

## Workflow

1. Plan the text before generating artwork.
   - Keep the Chinese title on one line whenever it fits at `96px` or larger.
   - Begin from an asymmetric left-text/right-visual composition, then adjust by optical balance.
   - Let Chinese and mixed-language titles expand; move or resize the artwork only as much as needed.
   - Make Chinese the primary focal point; keep the Latin label smaller.
   - Vertically center the complete left text group, whether it contains a title only or a label plus title.
2. Read [references/style-contract.md](references/style-contract.md).
3. Choose a fresh right-side visual family and topology from the topic semantics.
4. Call built-in ImageGen in **generate** mode for an isolated diagram asset on a flat `#00FF00` chroma-key background.
   - Omit `referenced_image_paths`.
   - Omit `num_last_images_to_include`.
   - Generate new artwork for every new cover; never reuse a previous cover’s right-side artwork unless the user explicitly asks.
   - Request no canvas background, grid, title, letters, numbers, logos, or watermark.
   - Keep the diagram tightly cropped and fully separated from the chroma background.
5. Remove the chroma key:

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \
  --input "/absolute/path/cover-artwork-chroma.png" \
  --out "/absolute/path/cover-artwork-transparent.png" \
  --auto-key border \
  --soft-matte \
  --transparent-threshold 12 \
  --opaque-threshold 220 \
  --despill
```

6. Inspect the transparent artwork. Require transparent corners, clean line edges, no green fringe, and no pseudo-text.
7. Compose exact text and deterministic geometry:

```bash
python3 <skill-dir>/scripts/compose_cover.py \
  --artwork "/absolute/path/cover-artwork-transparent.png" \
  --label "Codex + Hyperframes + HeyGen:" \
  --title "开源自媒体涨粉的秘诀" \
  --output "/absolute/path/cover.svg" \
  --png "/absolute/path/cover.png"
```

Use `--subtitle`, `--italic-title-lines`, `--artwork-start`, or the grid/artwork geometry overrides only when the content calls for them. Run `--help` for overrides.

## Non-negotiable style

- Fix the canvas background to `#FAF9F5`; never take the background color from ImageGen.
- Draw a visible but quiet square grid in SVG across the right visual field. Keep its start, density, and strength adaptable instead of copying one template; omit it only when the user explicitly asks for no grid.
- Keep the diagram on the right while allowing it to approach the center or move farther right according to headline length.
- Use charcoal diagram strokes and one restrained muted-coral signal; no broad orange fills.
- Left typography expands horizontally; the illustration shrinks or moves right to yield space.
- Vertically center the complete left text group.
- Use a heavy editorial serif for Latin headlines and italicize only an intentional emphasis line.
- Chinese title uses a near-black heavy sans and carries more visual weight.
- Use a smaller heavy italic serif for optional supporting copy.
- Do not add an underline, divider, rule, or decorative line beneath the text.
- No portraits, stickers, neon, glossy 3D, dense UI, or decorative copy.
- Treat reference covers as aesthetic calibration only. Do not copy their node count, exact loop, object placement, labels, or decorative details.

Do not ask the image model to render final title text. Keep all real text in SVG.

## Regeneration rule

- **New cover:** always generate a new right-side illustration from scratch with no reference inputs.
- **Concept or layout revision:** regenerate the right-side illustration.
- **Minor typography-only correction:** reuse the current illustration unless the user asks for a new one.

Vary visual family, topology, node count, connector route, central object, curve, and coral signal placement while preserving the style contract. Do not make a series look like the same diagram with only text swapped.

## Quality gate

1. Inspect the transparent artwork before composition. Reject pseudo-text, green fringe, clipped geometry, excessive padding, or an oversized diagram.
2. Inspect final PNG at full size and 25%.
3. Confirm every requested character and punctuation mark is exact.
4. Confirm Chinese remains readable first, Latin second, diagram third.
5. Confirm at least 4% canvas-width clearance between text and artwork.
6. Confirm the left text group is vertically centered and has no decorative underline.
7. Sample clean background pixels and confirm they are exactly `#FAF9F5`.
8. Confirm the right-side grid remains perceptible at 25% scale without competing with the artwork, and that both are optically balanced rather than mechanically matched to a reference.
9. Confirm SVG is editable/self-contained and PNG dimensions match.
10. Report the final paths, the no-reference ImageGen prompt, and that built-in ImageGen was used.
