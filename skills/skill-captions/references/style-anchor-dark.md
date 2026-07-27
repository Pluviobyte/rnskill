# Anchor Dark

This is the approved Kimi K3 production-caption style.

## Canonical 1920 × 1080 measurements

| Property | Value |
|---|---:|
| Font | STHeiti Medium |
| Font size | 56 px |
| Minimum fitted size | 42 px |
| Text color | RGBA `(252, 252, 249, 255)` |
| Text stroke | none |
| Text shadow | none |
| Panel color | RGBA `(45, 51, 50, 213)` |
| Horizontal padding | 22 px per side |
| Vertical padding | 22 px per side |
| Corner radius | 16 px |
| Panel shadow | none |
| Bottom margin | 96 px |
| Maximum text width | 1500 px |
| Maximum lines | 2 |

The apparent depth comes from the translucent charcoal panel over the footage,
not from a large drop shadow. Do not add a heavy blur, outline, black text
stroke, or offset shadow.

## Scaling

Scale all pixel measurements by `target_height / 1080`.

- 1080p: 56 px type, 16 px radius, 96 px bottom margin.
- 2160p: 112 px type, 32 px radius, 192 px bottom margin.

Redraw at the target resolution. Do not rasterize at 1080p and enlarge.

## Anchoring

Anchor the panel bottom edge to `frame_height - scaled_bottom_margin`. Keep that
edge fixed for every cue. When a cue wraps to two lines, expand the panel
upward. Never assign a different absolute Y coordinate per cue.

## Reference

Use `assets/style-reference/anchor-dark/kimi-reference-32s.png` for the full
composition and `anchor-dark-caption-crop.png` for the panel proportions.
