# V5 Perspective Grid Background

## Purpose

Use this as the default bottom canvas for white-first AI/tool tutorials,
page-based explainers, and short white motion graphics when no handoff contract,
source footage, or explicit reference requires another background.

This is an approved background asset, not a loose style reference. Reuse it
instead of rebuilding a perspective grid from CSS, a 3D plane, or an older
project version.

## Canonical Assets

The workspace-facing component is fully self-contained:

- portable component: `05-视频组件/视频背景/透视网格背景/`
- sole editable source: `05-视频组件/视频背景/透视网格背景/工程/`
  (main composition `工程/index.html`)

The following paths are relative to `ra-video-production-director/` and are
same-hash Skill mirrors/fallbacks:

- loop MP4: `assets/perspective-grid-v5/perspective-grid-v5-loop.mp4`
- manifest and checksum: `assets/perspective-grid-v5/manifest.json`
- editable HyperFrames source: `assets/perspective-grid-v5/source/`
- visual preview: `assets/perspective-grid-v5/preview/contact-sheet.png`

The accepted MP4 SHA-256 is
`4aa1d98d5a00d4ce0039e8ec71cdae6fe3ecccfedcfa777ddf583df0489ad4cf`.

## Locked Baseline

- canvas: `1920×1080`, `30fps`
- loop: `7.3s`, `219` end-exclusive frames
- movement: three complete grid cells per loop
- grid step: `61.98664px`
- measured speed: `25.4723px/s`
- single-cell period: `2.43349s`
- model: static ray fan + independently moving horizontal lines + static
  low-frequency color plate
- look: cool-left / warm-right asymmetric wash, central white fog, weaker
  left-side rays, large clean center workspace

Do not change geometry, phase, color plate, center fog, speed, or seam timing in
ordinary production work.

## Reuse Modes

### Default: use the rendered loop

1. Copy `05-视频组件/视频背景/透视网格背景/透视网格背景-V5-7.3秒循环.mp4`
   into the new project's local assets. If the workspace component is absent,
   use the Skill mirror `assets/perspective-grid-v5/perspective-grid-v5-loop.mp4`.
2. Place it at the bottom of the composition and scale it to the full 16:9
   canvas without cropping.
3. Play at `1×` and loop continuously for the whole composition.
4. Keep one continuous phase across page and scene boundaries. Never restart
   the MP4 at every scene.
5. Put titles, cards, Xiaohei illustrations, captions, and progress UI above it.

This mode is preferred because it preserves the accepted geometry and motion
without re-render drift.

### Exception: fork the editable source

Fork `source/` only when the output needs a different ratio, palette, geometry,
or speed. Copy it into the new engineering project, rename its `meta.json` and
package name, then treat the result as a new background version.

A fork cannot replace V5 as the recommended baseline until it passes:

- HyperFrames lint, validate, and inspect
- media probe for codec, dimensions, frame rate, duration, and frame count
- start/mid/end contact sheet review
- geometry and color comparison against its declared reference
- final-frame-to-first-frame seam measurement against ordinary adjacent frames
- archive delivery with a production note and QC artifacts

## When To Disable

Disable the grid when the foreground is full-screen source footage, a
full-screen talking head, dense UI, a screen recording whose details need the
whole canvas, an explicit pure-white request, or any case where text/readability
suffers. Record the reason in the project production note.

Do not place it mechanically behind every frame. It is the white-first design
baseline for suitable generated scenes, not a replacement for source footage.

## Acceptance Evidence

The approved V5 render measured `25.4723px/s`, or `0.74995×` the previous V4.1
motion. Its top and bottom loop seams were `1.0419×` and `1.0455×` ordinary
adjacent-frame medians, both inside the natural adjacent-frame distribution,
with forward phase and no reverse jump.
