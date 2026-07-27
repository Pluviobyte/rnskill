# Delivery Gates

Use these gates before calling a video done.

## Handoff Contract Gate (待制作 queue jobs)

When the job came from `01-内容生产/视频工作台/待制作/`, this gate runs first
and is machine-checked:

```bash
python3 automation/scripts/check_delivery.py <交接文件.md> <项目目录> <成片.mp4>
```

- exit code must be 0 (privacy boundary, ratio, duration, audio stream, voice
  provenance, real-timestamp captions when contracted, Xiaohei assets all
  PASS); fix and re-run on any FAIL
- paste the checker output into the handoff file's 制作端回执, fill the
  remaining 回执 fields (project dir, voice_manifest, contact sheet, final
  path), set `status: 已完成`
- assemble `01-内容生产/视频工作台/已制作/<月上旬|月下旬>/<日期-主题>/` (folder name =
  the project folder name): clean regenerable intermediates, then move the whole
  project folder from `制作中/` — `交接稿.md` at its root, the final MP4 in
  `成片/`, key QC frames in `质检/`, minimal engineering in `工程/` (no
  `视频标题.md` — title selection stays manual with the user). Use `X月上旬`
  for delivery days 1-15 and `X月下旬` for days 16 through month-end
- the frontmatter contract values (ratio, duration, voice, visual) are the
  acceptance values; an execution skill's own defaults never override them

## Required Locations

- Workbench project:
  `<WORKSPACE>/01-内容生产/视频工作台/制作中/<日期-主题>/`
- Final delivery for every video production route:
  `<WORKSPACE>/01-内容生产/视频工作台/已制作/<月上旬|月下旬>/<日期-主题>/成片/<file>.mp4`
  (the archive root holds any handoff/script/plan or production note that
  exists, and the sibling `质检/` holds key QC artifacts)
- Selected publish title (non-queue jobs only; queue jobs keep candidates in
  the handoff file's 标题候选 section and the user selects manually):
  `视频标题.md` next to the final MP4
- `已制作/6月历史成片库/`（封存只读） and the desktop
  `<WORKSPACE>/legacy-archive/` are retired legacy history: read-only,
  no new deliverables go there.

The final MP4 keeps a clear Chinese filename inside its delivery folder.

## Component Library Placement Confirmation

This gate applies whenever a video component, video background, or
reference-video replica has a rendered, QC-passed final. It runs after normal
finished-video archiving and before anything is added to `05-视频组件/`.

- explicitly ask the user whether the final should enter the component library
- ask which existing category should contain it and whether a new category is
  required; do not infer or create a category before the user replies
- if the user declines, stop after the normal `视频工作台/已制作/` delivery
- if the user approves, use the confirmed
  `05-视频组件/<中文分类>/<中文组件名>/` names as the naming authority and make
  the component directory self-contained: portable MP4 + `manifest.json` +
  `质检/` + `工程/` (sole editable source, stripped of node_modules/renders)
- no engineering mirrors, symlinks, or second source copies may be created
  anywhere else; register the component in `05-视频组件/CATALOG.md`
- do not keep two differently named current entries for the same component

## Publish Title Handoff

待制作 queue jobs skip production-side title work entirely: `ra-video-title`
already wrote 8-12 candidates (with a Top 3 recommendation) into the handoff
file's 标题候选 section at wash time, and the final title is chosen manually
by the user at publish time. Do not generate candidates, do not apply a
title, and do not create `视频标题.md` for queue jobs.

For non-queue jobs (no handoff contract): after the final MP4 passes media
and visual checks, generate 8-12 candidate publish titles with
`ra-video-title`.

Title candidates should be大众化 and clickable:

- do not lead with narrow tool names unless the user explicitly wants that
- prefer the audience pain, result gap, curiosity, conflict, or loss
- keep platform titles separate from spoken hooks and on-screen page titles
- offer a short recommendation, then wait for the user's choice

After the user chooses a title (non-queue jobs), create or update
`视频标题.md` next to the selected final MP4. Do not silently overwrite an
existing title unless the user has selected the replacement.

## Media Checks

Run a metadata check on the final file and report:

- width and height
- frame rate
- duration
- video codec
- audio codec
- audio channels
- file size
- non-queue jobs only: selected title file exists in the same `成片/`
  directory as the final MP4 (queue jobs carry title candidates in the
  handoff file instead)
- narration provider and voice id, when narration exists. The recommended
  final must use local IndexTTS2 voice `pluvio-indextts2-calm-v1` and the
  canonical lossless reference SHA-256 from `automation/config/tts-routing.json`.
  MiniMax is an article/relay-demo provider only and fails the local-video gate.
  macOS `say` or any other fallback is acceptable only for previews and must be
  reported as a limitation, not archived as the final deliverable.
- for `captions: asr-word-timestamps`, canonical subtitle artifacts exist,
  `caption-qc.json` passes, alignment coverage is at least 0.90, and the
  renderer consumes `captions.json` without recalculating its timestamps

## Asset-Text And Semantic-Cue Gate

Run this gate for any image, screenshot, footage, or generated illustration
combined with authored labels, badges, stamps, callouts, or other UI chrome.

- inspect each source asset at its delivered scale and inventory visible words,
  labels, badges, stamps, and UI text before authoring overlays
- compare the inventory with authored overlays and chrome; do not repeat the
  same semantic label unless the repetition is intentional, visually useful,
  and recorded in the production note. Required production captions are exempt
  from this overlay-deduplication rule
- for every narrated hero term, name, number, or reveal, take the semantic cue
  from the final word timestamps and capture frames at `cue - 0.1s`, `cue`,
  `cue + 0.3s`, and `cue + 0.7s` (clamped to the media bounds)
- at the cue, the hero must already be identifiable or becoming immediately
  readable; by `cue + 0.7s`, or before the spoken phrase ends when that is
  earlier, its load-bearing text must be fully legible and its supporting
  visual settled enough to read as one composition
- reject incomplete letters, late illustrations, transient text collisions,
  crop/overflow flashes, layout jumps, or accidental duplicate labels even
  when the scene midpoint and automated layout check pass
- keep the cue frames or their contact sheet with the project QC artifacts

## Visual Checks

Always create at least one contact sheet for a new rendered video. For reference
replication, create side-by-side contact sheets at the agreed interval.

Keep full contact sheets and QC frames in the engineering project, and copy
the key contact sheet/representative frames/media probe into the unified
`视频工作台/已制作/<月上旬|月下旬>/<日期-主题>/质检/` archive.

Check for:

- blank or unintended empty areas
- for 16:9 Xiaohei page videos, the whole page skeleton follows the
  `xiaohei-16x9-layout` contract: left-top title, left-middle note card,
  right-middle illustration, and lower caption
- right-side Xiaohei illustrations sitting too high or behaving like
  upper-right decoration instead of the right-middle page subject
- left note cards dropping into the lower-left area or crowding captions
- title or subtitle wrapping that creates orphan characters, short tail lines,
  strange gaps, or broken Chinese phrases
- for 16:9 Xiaohei page videos, typography uses the `mobile-readable` scale
  from `xiaohei-16x9-layout.md` by default: title, subtitle, note card,
  captions, and topbar must stay readable in reduced-size
  contact sheets and representative 1920x1080 single-frame previews. A
  `desktop-compact` exception is allowed only when the project note explicitly
  says the output is for desktop demos, projection, course-screen playback, or
  similarly large-screen viewing.
- captions that are visually heavier than the title, lack a clear bottom
  margin, span the frame instead of wrapping text, or sit too close to the
  note/illustration zones
- repeated blank zones caused by a fixed template, especially lower-left or
  lower-middle areas in right-illustration pages; when present, either add
  useful content such as input/action/output notes, role reminders, or
  acceptance criteria, or record why the blank space is intentional
- text outside containers or off-canvas
- text that is technically inside its container but too small to read on a
  phone; fix by shortening copy or changing the page variant before reducing
  font size
- wrong scene boundary timing
- missing transition frames
- decorative focus frames, scan boxes, or large outlines enclosing over 40%
  of the canvas or multiple content groups: inspect an entrance frame, the
  scene midpoint, and a late frame; reject them when total visibility exceeds
  the shorter of 2 seconds or 15% of the scene, when they remain at midpoint
  without explicit semantic purpose, or when they read as a permanent outer
  container. A semantic detection/selection frame must tightly bound one
  local target instead of boxing the whole layout.
- overly small primary subjects
- accidental repetition between text already embedded in a source asset and
  authored overlays or chrome
- hero terms, names, numbers, or reveal visuals that are still incomplete or
  unsettled after their semantic-cue deadline
- caption/audio desync
- captions covering page content
- caption styling that violates `skill-captions` and the selected registered
  style: full-width bands, heavy shadows, drifting baselines, live blur, or an
  undocumented frameless exception
- page-wide drifting, zooming, or shaking when the intended motion is
  component-level animation
- whether key components appear progressively with the narration
- adjacent pages presenting an identical set of info components, or a page
  with no component-level change within its duration (check the contact sheet
  page by page)
- `standard` pages carrying fewer than two info components besides title and
  illustration without a recorded reason in the project note

## Xiaohei Illustration Checks

When the visual direction mentions Xiaohei, 小黑配图, or the white-first
Xiaohei default system, the video is not complete until these checks pass:

- `ian-xiaohei-illustrations` was loaded and followed before image generation
- each page or scene either has a generated Xiaohei asset or a written reason
  for skipping the illustration
- generated images are copied into the project, usually under
  `assets/xiaohei-illustrations/`
- the render loads those image files directly; CSS/HTML drawings or generic
  hand-coded figures are not accepted as substitutes
- a contact sheet shows the Xiaohei assets in the final rendered scenes
- the project note records the asset list and the selected final MP4 path

## Completion Language

Use "recommended final" only for the file that passed the gate. Keep alternate
drafts visible but do not let them look like the selected deliverable.
