# Xiaohei 16:9 Layout Contract

Use this reference for white-first page-based Xiaohei explainers rendered in
16:9. The goal is to prevent two common failures: a right-side illustration
stuck too high while the left note card drops too low, and a page that looks
clean on desktop but becomes too small on a phone screen.

The default typography scale is `mobile-readable`. Use the smaller
`desktop-compact` scale only for explicit desktop demos, projection,
course-screen playback, or similarly large-screen viewing.

## Default Geometry

Use a 1920 x 1080 canvas.

| Element | Default placement |
| --- | --- |
| topbar | left 104, right 104, top 96 |
| title block | left 104, top 140, width 780 |
| title type | 72 px, line-height 1.06, weight 950 |
| subtitle | width 740, 32 px, line-height 1.34 |
| accent line | width 440, height 8, margin-top 22 |
| note card | left 104, top 424, width 730, min-height 238 |
| Xiaohei visual | right 72, top 264, width 972, height 547 |
| caption | centered, bottom 96, max-width 1500, STHeiti Medium 56 px; `skill-captions` `anchor-dark` panel |

Do not regress to the older failure shape: right visual near top 190 with a
left note card near top 536. That creates an upper-right/lower-left split and
makes the page feel like four unrelated objects.

## Typography Scale

Choose the scale before writing HTML. Use `mobile-readable` by default. Do not
scale font sizes from viewport width. Use fixed pixel sizes and adjust copy
length, line breaks, and variants when text becomes crowded.

| Element | `mobile-readable` default | `desktop-compact` exception |
| --- | --- | --- |
| topbar | 25 px, weight 700-800 | 22 px, weight 700-800 |
| title block | top 140, width 780 | top 148, width 780 |
| title type | 72 px, line-height 1.06, weight 900-950 | 62 px, line-height 1.08, weight 900-950 |
| subtitle | width 740, 32 px, line-height 1.34 | width 740, 28 px, line-height 1.36 |
| accent line | width 440, height 8, margin-top 22 | width 410, height 7, margin-top 24 |
| note card | top 424, width 730, min-height 238 | top 430, width 700, min-height 214 |
| note kicker / labels | 23 px | 20-24 px |
| note body | 30 px, line-height 1.16 | 25-26 px |
| caption | 44 px, line-height 1.22 | 38 px, line-height 1.25 |

Reject a page instead of shrinking text if the default scale causes collisions;
the fix is usually shorter note rows, manual title/subtitle lines, or a
`long-title` / `wide-visual` / `close` variant.

## Page Variants

- `standard`: normal title, compact subtitle, right-middle illustration.
- `long-title`: manually split the title into two clean lines. Do not allow
  automatic wrapping to create one-character or orphan-word lines.
- `wide-visual`: keep the visual centered vertically and allow it to feel wide,
  but do not move it back to the upper-right corner. Prefer the same visual box
  and object-fit contain before custom coordinates.
- `close`: final action or summary page. Keep the left note card as an action
  checklist and the right visual as the concrete handoff/action.

## Manual Line Break Rules

Plan `title_lines` and `subtitle_lines` before writing HTML.

Good title lines:

- `["热榜背后", "是同一个方向"]`
- `["好工具会留下", "下一步能用的产物"]`
- `["别只收藏工具", "先接一段流程"]`

Bad title lines:

- a single character on its own line
- a functional phrase split in the middle
- a first line with a large unexplained gap

Use block spans or equivalent structured line arrays. Do not use raw `<br>` as
the primary body-text strategy.

## Required Build Gate

Before a full render:

1. Generate the HTML composition.
2. Apply `skill-captions` `anchor-dark`; verify that the panel wraps the text,
   keeps one fixed bottom anchor, and does not use live blur.
3. Run the normal HyperFrames final `check` gate.
4. Capture midpoint frames for every page/scene.
5. Build a contact sheet and inspect it manually.
6. Fix any layout failure before the full render.

Reject the preview when any of these are true:

- right Xiaohei visual sits in the upper-right rather than right-middle
- left note card sits in the lower-left or crowds the caption zone
- title has orphan characters, bad automatic wrapping, or awkward gaps
- subtitle drops a tiny tail line such as one short phrase by itself
- pages use `desktop-compact` without an explicit large-screen reason
- title, note rows, or captions are not legible when the
  contact sheet is viewed at about one-third desktop width
- caption panel is visually heavier than the title, spans the frame, or lacks
  a clear bottom margin
- bottom of the page feels crowded while the middle feels empty
- repeated template leaves persistent useless blank zones

## Template Asset

For HyperFrames projects, copy or adapt the full directory:

`assets/xiaohei-16x9-template/`

It includes `build_index.py` and the repaired skeleton. It supports per-page
layout overrides through
`layout_overrides.json`.
