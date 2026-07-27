# Anchor Light

This is the light translucent companion to `anchor-dark`. Its visual surface
is based on the approved caption treatment used in the “AI 会问你问题” video:
dark ink, a warm-white translucent panel, a fine low-contrast border, and a
subtle soft shadow.

Only the surface treatment is borrowed. Do not copy that video's original
44 px type, 120 px bottom offset, 1240 px width, asymmetric padding, or 20 px
radius.

## Canonical 1920 × 1080 measurements

All geometry is deliberately identical to `anchor-dark`.

| Property | Value |
|---|---:|
| Font | STHeiti Medium |
| Font size | 56 px |
| Minimum fitted size | 42 px |
| Text color | RGBA `(21, 32, 42, 255)` |
| Text stroke | none |
| Text shadow | none |
| Panel gradient top | RGBA `(255, 255, 255, 235)` |
| Panel gradient bottom | RGBA `(247, 250, 251, 214)` |
| Panel border | 1 px, RGBA `(21, 32, 42, 26)` |
| Horizontal padding | 22 px per side |
| Vertical padding | 22 px per side |
| Corner radius | 16 px |
| Panel shadow | RGBA `(64, 93, 112, 36)`, Y 12 px, blur 17 px |
| Bottom margin | 96 px |
| Maximum text width | 1500 px |
| Maximum lines | 2 |

The shadow exists only to separate the translucent light panel from white
pages. It must remain soft and low-opacity; do not turn it into a floating
card or add a dark outline.

## Scaling and anchoring

Scale every pixel measurement by `target_height / 1080`. Draw directly at the
target resolution.

Anchor the panel bottom edge to `frame_height - scaled_bottom_margin`. Keep that
edge fixed for every cue. When a cue wraps to two lines, expand the panel
upward. Never move individual cues to imitate the source video.

## Recommended use

Use `anchor-light` on white-first explainers, perspective-grid pages, and clean
editorial layouts when the dark panel feels visually heavy. Keep
`anchor-dark` for mixed footage or backgrounds where a light translucent panel
does not provide reliable separation.

## Reference

Use
`assets/style-reference/anchor-light/anchor-light-render-regression-1080p.png`
for the canonical 1080p composition and
`anchor-light-render-regression-4k.png` for native-resolution scaling.
