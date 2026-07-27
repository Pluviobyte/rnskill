---
name: skill-captions
description: Render, preview, validate, and burn consistent production subtitles from QC-passed real-timestamp caption artifacts. Use for AI-video production, washed-video production, IndexTTS2 explainers, practical long-form videos, talking-head edits, Kimi-style dark rounded captions, warm-white translucent captions, subtitle styling, subtitle overlays, or fixing caption size, position, shadow, drift, and 4K scaling. Always pair with ra-audio-to-subtitles when final word timestamps do not already exist.
---

# Skill-字幕

Separate subtitle timing from subtitle appearance:

- Let `ra-audio-to-subtitles` own ASR, phrase grouping, timestamps, SRT/VTT, and
  `caption-qc.json`.
- Let this skill own typography, panel geometry, fixed anchoring, preview,
  overlay rendering, burn-in, and render QC.
- Never estimate production timing from character count, scene duration, or
  TTS segment duration.

## Required workflow

1. Lock the final narration audio or final merged video.
2. Run `ra-audio-to-subtitles` unless the project already has the canonical
   caption artifacts described in `references/timing-contract.md`.
3. Require `caption-qc.json` to report `status: pass`.
4. Select a style from `references/style-registry.json`. Use `anchor-dark`
   when the contract does not specify another style.
5. Generate a representative still preview before rendering a full video.
6. Inspect the preview against `references/layout-qc.md`.
7. Render the captioned derivative. Preserve the clean video and portable
   SRT/VTT.
8. Run `scripts/validate_caption_render.py` and archive its JSON report.

## Registered styles

`anchor-dark` reproduces the approved Kimi K3 subtitle treatment: STHeiti
Medium, warm white text, a tight charcoal translucent rounded panel, no text
stroke, no text shadow, no large panel shadow, and a fixed bottom-center
anchor. Read `references/style-anchor-dark.md` before changing its values.

`anchor-light` keeps the exact same typography, size, padding, width, bottom
anchor, line fitting, and resolution scaling as `anchor-dark`. Only its surface
changes: dark ink on a warm-white translucent panel with a fine border and
subtle soft shadow. Read `references/style-anchor-light.md` before changing its
values. This is the second registered style; `anchor-dark` remains the default.

Scale every 1080p metric by `target_height / 1080`. Render 4K captions at 2×
their 1080p measurements; never upscale a rasterized 1080p subtitle layer.

## Commands

Preview a QC-passed project:

```bash
python3 .claude/skills/skill-captions/scripts/render_captions.py \
  final.mp4 media/captions/captions.json \
  --qc media/captions/caption-qc.json \
  --preview qc/caption-preview.png \
  --preview-only
```

Burn the default style:

```bash
python3 .claude/skills/skill-captions/scripts/render_captions.py \
  final-clean.mp4 media/captions/captions.json \
  --qc media/captions/caption-qc.json \
  --out renders/final-captioned.mp4 \
  --preview qc/caption-preview.png
```

Burn the light translucent style:

```bash
python3 .claude/skills/skill-captions/scripts/render_captions.py \
  final-clean.mp4 media/captions/captions.json \
  --qc media/captions/caption-qc.json \
  --style anchor-light \
  --out renders/final-captioned.mp4 \
  --preview qc/caption-preview.png
```

Skip an interval that already contains burned captions:

```bash
python3 .claude/skills/skill-captions/scripts/render_captions.py \
  final-clean.mp4 media/captions/captions.json \
  --qc media/captions/caption-qc.json \
  --exclude 0:23.936 \
  --out renders/final-captioned.mp4
```

Create a reusable transparent caption band:

```bash
python3 .claude/skills/skill-captions/scripts/render_captions.py \
  final-clean.mp4 media/captions/captions.json \
  --qc media/captions/caption-qc.json \
  --overlay-out renders/caption-band.mov
```

Validate the result:

```bash
python3 .claude/skills/skill-captions/scripts/validate_caption_render.py \
  --source final-clean.mp4 \
  --render renders/final-captioned.mp4 \
  --captions media/captions/captions.json \
  --qc media/captions/caption-qc.json \
  --out qc/caption-render-qc.json
```

## Hard rules

- Use the final audio/video as the only timing source.
- Consume `captions.json` start/end values directly.
- Refuse final burn-in when caption QC is missing or failed.
- Keep a fixed bottom anchor. Let multiline panels grow upward.
- Keep captions inside the frame and clear of titles, UI, faces, and PiP.
- Keep English model/product tokens intact.
- Preserve one canonical caption timeline across renderers.
- Keep the clean master; a burned-caption MP4 is a derivative.
- For a new or materially changed style, show a short preview before the full
  render.
- Do not add karaoke, behind-person typography, VFX captions, or animated hero
  words unless the user explicitly requests the separate `embedded-captions`
  lane.

## Integration contract

Video orchestrators should call this skill after `ra-audio-to-subtitles`.
Handoff contracts may set `caption_style` to `anchor-dark` or `anchor-light`;
otherwise use `anchor-dark`.
Renderers may reproduce the registered CSS in Remotion or HyperFrames, but
must preserve the style metrics and fixed-anchor behavior.
