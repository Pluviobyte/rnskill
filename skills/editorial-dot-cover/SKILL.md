---
name: editorial-dot-cover
description: Create deterministic editorial-style cover images with a warm paper-gray background, oversized black slab-serif/Chinese display typography, generous whitespace, and a dotted vector analysis icon. Use when the user asks for a “点阵编辑风封面”, “暖灰杂志风封面”, “Codex + Hyperframes 同款封面”, or wants to reproduce/adapt the specific minimal left-text/right-icon banner style. Produce editable SVG and a rendered PNG; do not use this skill for generic covers without this visual direction.
---

# Editorial Dot Cover

Create a typographically accurate cover from vectors. Prefer the bundled renderer over image generation so Chinese text and punctuation remain exact.

## Required inputs

Resolve these values from the request or current project:

- `label`: short English/tool label, such as `Codex + Hyperframes:`
- `title`: one concise Chinese headline
- `output`: destination SVG and PNG paths

Default to `3168 × 1267` (about `2.5:1`). If the user provides no label, derive a short tool/topic label. Ask only when the title itself cannot be inferred safely.

## Render

Run:

```bash
python3 <skill-dir>/scripts/render_cover.py \
  --label "Codex + Hyperframes:" \
  --title "拆解抖音爆款·吃上自媒体这碗饭!" \
  --output "/absolute/path/cover.svg" \
  --png "/absolute/path/cover.png"
```

Use `--width` and `--height` only when a different landscape ratio is requested. Use `--font-en` or `--font-cn` when the user specifies a font. Run `--help` for all parameters.

Use `--label-size` or `--title-size` for art-directed pixel sizes when mixed-language font metrics make the automatic fit inaccurate. Preserve the required text-to-icon gap after overriding either value.

Use `assets/style-reference.png` only as a visual comparison target when checking fidelity; generate new covers from the script instead of copying pixels from the sample.

The script keeps an editable SVG as the source of truth and uses an installed Chromium-family browser or `rsvg-convert` for PNG rendering. If neither renderer exists, deliver the SVG and report that PNG rendering remains pending.

## Style contract

Preserve these traits:

- Warm gray paper background near `#D6D0C5`, with subtle grain and a weak center glow/vignette.
- Nearly black foreground near `#050505`; do not introduce accent colors unless requested.
- Left-aligned text block occupying about 68–72% of the canvas.
- Right-side dotted film-and-magnifier symbol occupying about 18–20%.
- English line in a heavy slab serif. Prefer `Roboto Slab Black`; fall back to Rockwell or a heavy serif.
- Chinese line in a very heavy display sans. Prefer a licensed installed display face; fall back to Source Han Sans SC Heavy or PingFang SC Heavy.
- Tight tracking, compact line gap, and large empty top/bottom margins.
- Use `·` or `：` to create an internal headline pause; preserve the user’s final punctuation.
- Render the pictogram as vectors with round dotted strokes. Do not substitute a raster stock icon.

Do not add portraits, stickers, gradients with visible color shifts, badges, drop shadows, or decorative copy. The visual identity comes from typography, whitespace, paper texture, and the dotted pictogram.

## Layout decisions

- Keep one Chinese headline line when it remains legible and fits before the icon.
- For a long headline, first tighten phrasing. If wording must remain unchanged, insert one intentional line break and vertically recenter the full group.
- Keep at least 4% canvas width between the text and pictogram.
- Reduce the English label before reducing the Chinese headline when they compete.
- For ratios narrower than `1.8:1`, preserve the style but allow the icon to move below/right of the text. Do not compress the title until its glyphs look unnaturally narrow.

## Quality gate

Before delivery:

1. Open the PNG at full size and at 25% scale.
2. Confirm every Chinese character and punctuation mark matches the requested text.
3. Confirm no glyph, dotted stroke, or magnifier handle is clipped.
4. Confirm the headline is the first focal point and the icon remains secondary.
5. Confirm background texture is visible only on inspection, not as obvious noise.
6. Confirm the SVG remains editable and the PNG dimensions match the contract.

If the dotted symbol collapses at thumbnail size, increase dot spacing or stroke width and rerender.
