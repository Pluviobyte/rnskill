---
name: ra-video-production-director
description: >
  End-to-end video production orchestration for the content-creation workspace.
  Use when the user asks to make, recreate, package, render, QC, or archive a
  video; when the user says 制作待制作队列, 按交接稿制作, 制作队列视频, or
  points at a handoff project folder under 01-内容生产/视频工作台/待制作/ (contract file 交接稿.md inside) or an
  image-card handoff under 01-内容生产/图文工作台/待制作/ (its frontmatter is
  the binding production contract); when a request could route
  to HyperFrames, Remotion, captions, TTS, download/transcription,
  website/product videos, motion graphics, or reference replication; or when
  the user needs production planning before editing.
---

# AI 视频创作 Skill

## Role

Act as the director layer above the existing video skills. Route the job, define
the acceptance standard, then coordinate production and QC. Do not replace
`hyperframes`, `remotion`, `ra-audio-to-subtitles`, `skill-captions`, `embedded-captions`, `graphic-overlays`,
`ra-video-download`, `视频转写`, `tts-skill`, `heygen-digital-avatar`, or `ai-video-qc-delivery`; load those
skills only when their lane is selected.

If the user provides a source video URL or local file and asks for `视频洗稿`,
`视频二创`, or `洗稿并制作视频`, route to `ra-video-wash-pipeline` before this
skill so extraction and rewrite happen first.

## 待制作 Queue Intake

If the input is a handoff project folder under
`01-内容生产/视频工作台/待制作/<日期-主题>/` (contract file `交接稿.md` at its
root; or the user says `制作待制作队列`, `按交接稿制作`, or points at a queued
script):

- the 交接稿.md frontmatter is the binding production contract — platform, ratio,
  `duration_target_s`, `word_count`, `voice`, `caption_style`, `visual`,
  `illustration_skill`, `typography` override intake defaults and must never be replaced by an
  execution skill's own defaults (e.g. HyperFrames TTS voices are not a
  substitute for the contract voice)
- before starting work, set `status: 制作中` in 交接稿.md and move the whole
  project folder to `01-内容生产/视频工作台/制作中/<日期-主题>/`, so the other
  machine does not double-produce; all engineering happens inside that folder
- the script segments in the handoff file are the scene units; do not re-split
  or re-flow the narration
- skip intake questions the contract already answers

## Hard Rules

1. Define the output standard before production: original video, pixel-level
   alignment, visual replica, style-inspired creation, captioned footage,
   narrated explainer, product promo, website tour, or motion graphic.
2. Do not claim pixel-level alignment for a hand-authored HyperFrames/Remotion
   rebuild. Pixel-level requires source-stream reuse, original project assets,
   or hard metrics such as matching hash, `cmp`, PSNR infinity, or SSIM 1.0.
3. Keep source projects and intermediates under
   `<WORKSPACE>/01-内容生产/视频工作台/制作中/`; the workbench
   `01-内容生产/视频工作台/` holds only handoffs, transcripts, and archives.
4. Final deliverables stay inside the vault. Every video produced by this
   system — queue or non-queue, transcript-direct, practical long-form,
   translated/repackaged, or ad hoc — delivers to
   `01-内容生产/视频工作台/已制作/<月上旬|月下旬>/<日期-主题>/成片/`, with key QC images in
   the sibling `质检/`. Use the delivery date: days 1-15 go to `X月上旬`
   and days 16 through month-end go to `X月下旬`. `已制作/6月历史成片库/`（封存只读） and the desktop
   `<WORKSPACE>/legacy-archive/` are retired legacy history — do not
   write new deliverables there.
5. Publish titles are not production work for 待制作 queue jobs:
   `ra-video-title` already wrote 8-12 candidates into the handoff 标题候选
   section at wash time, and the final title is chosen manually by the user
   at publish time. Do not generate or apply publish titles and do not create
   `视频标题.md` for queue jobs (on-page scene titles from the script are
   unaffected). Only for non-queue jobs (no handoff contract) generate 8-12
   candidates with `ra-video-title` after QC and let the user choose before
   saving `视频标题.md` next to the final MP4.
6. A video is not complete until media specs, visual checks, and archive
   paths are confirmed. The selected-title-file requirement applies to
   non-queue jobs only; queue jobs finish without `视频标题.md` (title
   selection stays manual with the user).
7. If the user explicitly names a visual or illustration skill, load and follow
   that skill before designing the visual layer. Do not replace a requested
   illustration skill with hand-coded shapes, CSS drawings, or "style-like"
   approximations unless the user explicitly approves that substitution.
8. When full AI narration is required, final deliverables must use local
   IndexTTS2 through `tts-skill`, voice id `pluvio-indextts2-calm-v1`, and the
   canonical lossless WAV declared in `automation/config/tts-routing.json`.
   MiniMax is reserved for public article/tutorial relay examples and is
   forbidden for local video narration. Do not silently fall back to macOS
   `say`, browser speech, MiniMax, or another generic/cloud voice. If the local
   model or canonical WAV is missing, repair the IndexTTS2 lane or stop before
   final render.
9. For jobs taken from the `待制作` queue, delivery is not complete until
   `python3 automation/scripts/check_delivery.py <交接文件> <项目目录> <成片.mp4>`
   exits 0, the 制作端回执 in the handoff file is filled (paths + checker
   output), `status` is set to `已完成`, and the per-project archive folder
   `01-内容生产/视频工作台/已制作/<月上旬|月下旬>/<日期-主题>/` (folder name = the
   project folder name) is assembled by moving the cleaned project folder from
   `制作中/`: `交接稿.md` at its root, the final MP4 in `成片/`, key QC frames
   in `质检/`, minimal engineering in `工程/`. Non-queue jobs
   assemble the same dated archive structure using a clear topic slug; copy a
   production note/script/plan into the archive root when available. No job
   copies a new final into `已制作/6月历史成片库/`（封存只读）.
10. The 图文工作台 queue follows the same contract pattern: take
    `01-内容生产/图文工作台/待制作/<file>.md` (frontmatter contract:
    card_count, ratio, style, illustration_skill, image_skill), set
    `status: 制作中` on start, produce the image cards without rewriting the
    copy and without generating or applying publish titles, deliver to
    `01-内容生产/图文工作台/已制作/<日期-主题>/` (handoff file moved in +
    finished cards under `图/`), set `status: 已完成`, and register the item
    under 待修改 in `01-内容生产/发布看板.md`. The source-privacy wall applies
    unchanged.
11. 实操长片 projects follow the unified engineering layout under
    `01-内容生产/视频工作台/制作中/<日期-主题>/`; do not create a separate planning directory
    under `视频工作台/`.
    the 策划稿 frontmatter `status` is the only handoff signal, and the user
    handles 录制 and 剪映融合 stages personally. Codex owns three stages:
    (a) `status: 待粗剪` — default to `ra-local-talking-head-cut`: Seed ASR
    word timestamps, terminology/uncertainty review, and a source-timeline
    pre-cut SRT. Stop for explicit user approval; no EDL or render is allowed
    before approval. Then perform semantic cleanup, adaptive pauses,
    source-size/source-fps rendering, dialogue loudness, media QC, and final-
    media subtitle generation with caption QC PASS. Use `video-use` as the
    multiple-take evidence/selection layer; use
    `Agentchengfeng/chengfeng-videocut-skills` only for word-level web review or
    an intentionally aggressive comparison; choose `AI剪口播` when the user
    wants waveform review and an FCPXML timeline for 剪映/Final Cut Pro. The
    default MP4 workflow delivers `粗剪/口播-粗剪.mp4` and sets `status: 融合中`;
    the FCPXML workflow moves forward only after the editor timeline is accepted;
    (b) `status: 待字幕` — run `ra-audio-to-subtitles` against the user's
    final merged cut, require word-timestamp QC to pass, then run
    `skill-captions` with the contract `caption_style` (default
    `anchor-dark`) to preview, burn, and validate the phrase captions; save the
    matching `.srt` and passing `caption-render-qc.json`, then set
    `status: 待动画`;
    (c) `status: 待动画` — add Remotion component overlays ONLY to the
    全身出镜 segments listed in the 策划稿 frontmatter, composite, deliver the
    final MP4 to `视频工作台/已制作/<月上旬|月下旬>/<日期-主题>/成片/`, put key QC in the
    sibling `质检/`, register on 发布看板, set `status: 成片`.
    All rough-cut tools are rough-cut-only in this workspace: never use any rough-
    cut tool's subtitle output as the production subtitle timeline.
12. For any narrated final video, the final concatenated audio or final merged
    video is the only subtitle timing source. Run `ra-audio-to-subtitles` after
    audio is locked; archive `captions_words.json`, `captions.json`,
    `captions.srt`, and `caption-qc.json`. Character-count interpolation,
    scene-duration interpolation, and fixed-delay caption timing are preview-
    only and must never enter a recommended final.
13. Whenever a video component, video background, or reference-video replica
    reaches a rendered, QC-passed final, stop before adding it to
    `05-视频组件/` and explicitly ask the user: whether it should enter the
    component library, which existing category should contain it, and whether
    a new category is needed. Do not infer placement or create a category before
    the user answers. If the user declines, use only the normal finished-video
    archive. If the user approves, treat the confirmed
    `05-视频组件/<中文分类>/<中文组件名>/` names as canonical and make the
    component directory self-contained in the same task: portable MP4,
    `manifest.json`, `质检/`, and `工程/` (the sole editable source, stripped
    of node_modules/renders). No engineering mirrors, symlinks, or second
    copies exist anywhere else; register the component in
    `05-视频组件/CATALOG.md` before reporting completion.
14. Whenever the user asks for a HeyGen/digital-human/avatar video, or a video
    production contract calls for the existing Pluviobyte digital human, load
    `heygen-digital-avatar` before generation. Its original Digital Twin look,
    CLI OAuth subscription billing, Avatar III default, local IndexTTS2 audio,
    one-master reuse, and approved `headroom_08` lower-left circle layout are
    binding. Only an explicit request for `全屏数字人` may bypass the circle
    layout.
15. Treat any decorative focus frame enclosing over 40% of the canvas or
    multiple content groups as an entrance cue only. Its total visibility must
    not exceed the shorter of 2 seconds or 15% of the scene, and it must exit
    before the steady information state. Persistent frames require explicit
    semantic purpose and must tightly bound one local target.

## Default Visual System

When the user says to make a video with this skill and does not provide a
conflicting visual direction, use a white-first visual system:

- background: pure white or warm white, with generous blank space
- for white-first AI/tool tutorials, page-based explainers, and white motion
  graphics, read `references/perspective-grid-v5.md` and start from the
  workspace component `05-视频组件/视频背景/透视网格背景/`. The bundled
  `assets/perspective-grid-v5/` copy is the same-hash Skill mirror and fallback,
  not a second independently editable baseline. Use the approved V5 loop as
  the bottom-most visual layer at its native playback rate: 1920x1080, 30fps,
  7.3 seconds / 219 frames, three complete grid cells per loop, and a
  2.433-second single-cell period. Preserve its geometry, asymmetric color
  plate, center fog, phase, and seamless-loop timing. Do not rebuild it from an
  older version or an ad-hoc CSS grid.
- disable the V5 grid only when source footage, full-screen talking head, dense
  UI, readability, a handoff contract, or an explicit reference conflicts with
  it. Record the reason in the production note.
- primary marks: black text, black line art, and restrained dark UI elements
- accents: use only small amounts of red, orange, or blue for emphasis,
  warnings, arrows, feedback, or state
- captions: for narrated explainers over footage, screenshots, the V5 grid, or
  variable backgrounds, run `skill-captions` and use its `anchor-dark`
  shrink-wrapped panel by default. A handoff `caption_style` or explicit user
  style overrides it; frameless captions require a controlled uniform light
  caption zone and a recorded reason.
- avoid defaulting to dark, purple, neon, or SaaS-magic styling unless the user
  explicitly asks for it or the selected route requires it
- use `ian-xiaohei-illustrations`
  as the default illustration source for page-based or scene-based videos.
  Prefer the active project-local copies under
  `.agents/skills/ian-xiaohei-illustrations/`,
  `.codex/skills/ian-xiaohei-illustrations/`, and
  `.claude/skills/ian-xiaohei-illustrations/`; the shared library path
  `<WORKSPACE>/.claude/skills/ian-xiaohei-illustrations` is only a source of
  truth to repair from when the project copy is missing.
- give every page or scene a meaningful Xiaohei illustration whenever possible;
  skip only when footage, screenshots, dense UI, or readability would clearly be
  harmed
- each illustration must explain the page's core claim, process, contrast, or
  state; Xiaohei should perform the core action, not appear as decoration
- if the plan says "Xiaohei" or "小黑配图", create real image assets with
  `ian-xiaohei-illustrations` and save them into the project. A CSS/HTML
  approximation of Xiaohei does not satisfy this requirement.
- for page-based 16:9 Xiaohei videos, use the `xiaohei-16x9-layout` contract
  before writing the composition. The contract fixes the page skeleton first:
  left-top title, left-middle note card, right-middle Xiaohei illustration,
  and lower caption. Do not invent a fresh layout unless the user asks for a
  different visual system.

## Page-Based Explainer Defaults

For AI/tool tutorials, page-based narrated explainers, and long-form Chinese
teaching videos, apply these defaults unless the user gives a conflicting
reference:

- For 16:9 Xiaohei explainers, read
  `references/xiaohei-16x9-layout.md` before building. Copy or adapt the
  template asset in `assets/xiaohei-16x9-template/` when the project is a
  HyperFrames page-based video.
- Treat the layout as a contract, not a loose suggestion. The right-side
  Xiaohei image belongs to the right-middle area, not the upper-right corner.
  The left note card belongs to the left-middle area, not the lower-left area.
  Captions must stay below the content zones with a clear bottom safe margin.
- Select a page variant before writing HTML: `standard`, `long-title`,
  `wide-visual`, or `close`. Use `long-title` for titles that would produce
  awkward automatic breaks; use `wide-visual` for horizontal illustrations;
  use `close` for final action or summary pages.
- Manually plan title and subtitle line breaks for every page. Do not rely on
  automatic wrapping when a Chinese title is long enough to create orphan
  characters, single-word lines, or large gaps.
- Use the `mobile-readable` typography scale in
  `references/xiaohei-16x9-layout.md` as the default for 16:9 Xiaohei page
  videos. Most distribution is phone-first, and horizontal pages become small
  on mobile. Only use the smaller `desktop-compact` exception for explicit
  desktop demos, projection, course-screen playback, or similarly large-screen
  viewing. Do not shrink all text to make crowded pages fit; first shorten
  copy, split lines manually, or choose a layout variant.
- Use a light white-first layout by default: white background, black text,
  meaningful Xiaohei illustrations, and small red/orange/blue accents only for
  emphasis, warnings, arrows, feedback, or state. Do not drift into dark,
  neon, purple, or SaaS-promo styling by default.
- Treat Xiaohei illustrations as explanation, not decoration. Each page's
  illustration must show the core action or concept being explained, such as
  fact-checking, division of labor, orchestration, memory, handoff, or
  acceptance.
- Do not let a repeated page template leave a persistent empty lower-left or
  lower-middle area just because the Xiaohei illustration sits on the right.
  For teaching videos, first consider adding useful light content there rather
  than simply scaling the illustration larger. Good fillers are role notes,
  input/action/output cards, anti-pattern reminders, acceptance criteria,
  priority lists, or "next time use this" prompts.
- Keep these filler modules compact and information-bearing. They should help
  the viewer remember or apply the current page, not act as decorative labels.
  If the content does not add a useful judgment, leave the space intentional
  instead of filling it mechanically.
- Reserve non-overlapping zones for narrated pages: upper content and lower
  captions. Captions must not cover body content.
- Use `skill-captions` and its `anchor-dark` panel by default. It must wrap the
  text rather than span the frame, keep one fixed bottom anchor, scale from the
  1080p baseline, and avoid text stroke, heavy shadow, and live blur.
- Avoid moving, zooming, drifting, or shaking the entire page just to create
  motion. A stable page base is more important than constant camera movement.
- Put motion on components: title, eyebrow, accent line, cards, bullets,
  Xiaohei image, and captions may enter or settle while the page base,
  and content frame remain fixed.
- Reveal necessary components progressively with the narration. Do not show
  all page content at once when the voiceover is still introducing pieces.
  Prefer a sequence such as eyebrow -> title -> accent -> illustration ->
  bullets/cards.
- For every narrated hero term, name, number, or reveal, derive its semantic
  cue from the final word timestamps and apply the semantic-cue micro-sweep in
  `references/delivery-gates.md`. The hero must become readable on the spoken
  cue and finish settling while that phrase is still active; a scene midpoint
  alone is not enough evidence.
- Prefer reveal, wipe, fade-in, and subtle settle motion. Motion should make
  the explanation feel spoken into view, not make the page perform for its own
  sake.
- Element variation is a hard requirement, not taste: adjacent pages must not
  present an identical set of info components, and every page must show at
  least one component-level change (a new element entering, an emphasis, or a
  state switch) within its own duration. Long videos must avoid extended
  PPT-like stillness.
- Page density floor: a `standard` page carries at least two info components
  besides the title and the Xiaohei illustration (note card, bullets, cards,
  labels, chapter cue). If a page intentionally stays sparser, record the
  reason in the project note.
- For substantial style, caption, or motion changes, render a 10-second sample
  first and get approval before rendering the full video.
- For any page-based Xiaohei video, create a pre-render contact sheet from
  page midpoints before the final full render. Fix layout failures at this
  stage, not after the final MP4. The contact sheet must be checked for visual
  center, title breaks, note-card position, illustration position, caption
  weight, and content/caption clearance.
- Generate subtitles only after the final narration has been concatenated.
  Page renderers must consume `media/captions/captions.json` directly and must
  refuse a final build when `caption-qc.json` is absent or failed.

## Workflow

### 1. Intake

Capture these decisions in plain language:

- goal: teach, promote, recreate, translate, caption, package, or test
- source: brief, script, URL, reference video, existing footage, audio, deck, PR
- platform and ratio: 16:9, 9:16, 1:1, or user-specified; when neither the
  user nor a handoff contract specifies one, default to Douyin horizontal 16:9
- required tool: HyperFrames, Remotion, ffmpeg, or no preference
- fidelity: pixel-level, visual-level, style-level, or original creative
- visual direction, defaulting to the white-first Xiaohei system above
- final archive slug and expected delivery path

Ask only if the missing answer changes the production path. Otherwise make a
conservative assumption and proceed.

### 2. Route

Read `references/routing.md` and select the narrowest workflow. Prefer an
existing specialized skill over a broad one.

Common routes:

- custom multi-scene HyperFrames video -> `general-video` + `hyperframes`
- short unnarrated motion piece -> `motion-graphics`
- product or SaaS promo -> `product-launch-video`
- website showcase -> `website-to-video`
- final-audio subtitle timeline / SRT / VTT -> `ra-audio-to-subtitles`
- existing Pluviobyte digital human / HeyGen avatar -> `heygen-digital-avatar`
- designed captions on talking-head footage -> `embedded-captions`
- designed overlay cards on footage -> `graphic-overlays`
- source download -> `ra-video-download`
- transcription or translation -> `视频转写`
- final archive and QC -> `ai-video-qc-delivery`

### 3. Plan Before Build

Create a production note in the project directory for non-trivial work. Include:

- scene list and timing
- asset list and source paths
- page-by-page Xiaohei illustration plan, unless the route does not use pages
  or illustrations
- page-by-page layout variant plan, including `standard`, `long-title`,
  `wide-visual`, or `close`, plus manual title/subtitle line breaks where
  needed
- page-by-page content-density plan, including how persistent blank areas such
  as the left-lower quadrant will be used or intentionally preserved
- illustration provenance: which skill will generate each image, where the
  generated originals live, and where the project-local copies will be saved
- asset-text inventory: visible words, labels, badges, stamps, and UI text
  already embedded in images, screenshots, and footage; planned overlays must
  not repeat the same semantic label unless the repetition is intentional and
  documented
- audio/caption plan, including the exact final media passed to
  `ra-audio-to-subtitles` and the canonical caption artifact directory
- voice plan: exact provider, voice id, script path, and whether fallback is
  forbidden for the final render. The workspace default is local IndexTTS2
  voice `pluvio-indextts2-calm-v1` using the canonical lossless WAV in
  `automation/config/tts-routing.json`; MiniMax `.env` values never override
  this local-video route.
- platform typography plan: use `mobile-readable` by default, or document the
  explicit large-screen reason for `desktop-compact`; list pages that need
  shorter copy or manual line breaks
- caption safe zones and the selected caption mode; default to `anchor-dark`
  from `skill-captions`, or record the reason for a frameless exception
- chapter grouping and real start-time boundaries for scene planning
- component-level animation plan for each page, including the order in which
  key components appear with the narration
- semantic-cue plan for every hero term, name, number, or reveal, using final
  word timestamps rather than estimated scene timing
- pre-render layout preview plan: exact timestamps or scene midpoints for a
  contact sheet before full rendering
- 10-second sample plan before full rendering when the visual or motion style
  is not yet approved
- acceptance checks
- known risks or unavailable source assets

For reference-video work, the timing table must come from extracted frames, not
from memory.

### 4. Build

Use the selected execution skill. Keep edits scoped to the project. Do not add
music, captions, scenes, or visual embellishment unless the user's goal needs
them or the selected workflow requires them.

Before building a page-based Xiaohei video, generate the Xiaohei images first,
store them under a project asset directory such as
`assets/xiaohei-illustrations/`, then make the HyperFrames/Remotion layer load
those image files directly. Do not start from a CSS-drawn Xiaohei placeholder
when the requested deliverable is a Xiaohei-skill illustration video.

For 16:9 HyperFrames Xiaohei explainers, start from the template asset in
`assets/xiaohei-16x9-template/` or reproduce its same layout contract. Keep the
template coordinates stable unless a page variant needs a documented
adjustment. If you adjust them, generate a fresh midpoint contact sheet and
verify the page still passes the layout gate before rendering the final MP4.

For ordinary use of the V5 perspective-grid background, copy the canonical
rendered loop from `05-视频组件/视频背景/透视网格背景/` into the project's own
assets and loop it continuously as the bottom layer. Verify its SHA-256 against
the bundled `assets/perspective-grid-v5/` mirror. Keep playback at `1×` and
retain one continuous phase across scene boundaries; do not restart the loop on
every page. Fork the editable source only when ratio, palette, geometry, or
speed must change. A fork is a new background version and must repeat seam,
geometry, contact-sheet, and media-spec QC before becoming a recommended
baseline.

For page-based explainers, keep the base page stable and animate only the
necessary components. If the result feels like the whole page is floating,
drifting, or shaking, revise before rendering the full video.

After the final narration is concatenated, run `ra-audio-to-subtitles` before
building the final composition. Render captions from its `captions.json`; do
not derive subtitle timing from `voice_manifest.json` segment durations. A
missing or failed `caption-qc.json` blocks the final render.

Before authoring the caption layer, load `skill-captions`, read its registered
style contract, and consume the approved `captions.json` timestamps directly.
Use `anchor-dark` unless the handoff or user selects another style. Preserve
its shrink-wrap, fixed bottom anchor, native 4K redraw, and no-heavy-shadow
constraints, and test it over both source footage and the lightest page
background. A substantial caption-style change requires a short sample before
the full render.

### 5. QC And Archive

Read `references/delivery-gates.md`. At minimum verify:

- for 待制作 queue jobs: `automation/scripts/check_delivery.py` exits 0
  against the handoff file, project dir, and final MP4; its output is pasted
  into the handoff file's 制作端回执, `status` becomes `已完成`, and
  `01-内容生产/视频工作台/已制作/<月上旬|月下旬>/<日期-主题>/` is assembled with the handoff
  file, the final MP4 copy under `成片/`, and key QC frames under `质检/`
- final MP4 exists in the unified workbench delivery location:
  `视频工作台/已制作/<月上旬|月下旬>/<日期-主题>/成片/` for every production route
- width, height, frame rate, duration, video codec, audio codec, channels
- representative contact sheets or side-by-side comparisons
- page/scene coverage: every page has a useful illustration or a stated reason
  for skipping it
- for page-based 16:9 Xiaohei videos, the pre-render contact sheet passes the
  `xiaohei-16x9-layout` gate: right visual centered, left note card centered,
  no awkward title wrapping, captions below content, and no persistent
  bottom-heavy page
- for 16:9 Xiaohei page videos, the contact sheet and representative single
  frames use the `mobile-readable` typography scale by default and remain
  readable without zooming when reviewed at reduced size; any `desktop-compact`
  exception must be explicitly justified in the project note
- Xiaohei provenance: when Xiaohei is requested or selected by default, the
  project contains the generated image assets, the render references those
  assets directly, and a contact sheet confirms the assets appear in the final
  scenes
- captions do not cover content; the default `anchor-dark` panel from
  `skill-captions` wraps the text, preserves one fixed baseline, remains inside
  the lower safe zone, and introduces no heavy-filter warning or full-width
  lower-third
- caption artifacts come from `ra-audio-to-subtitles`, `caption-qc.json`
  reports `status: pass`, timing source is `volcengine-word-timestamps`, and
  alignment coverage meets the contract (0.90 by default)
- component order and animation are visible in extracted frames
- asset-embedded text has been compared with authored overlays/chrome and no
  accidental duplicate semantic label remains
- every narrated hero term, name, number, or reveal passes the semantic-cue
  micro-sweep defined in `references/delivery-gates.md`
- subtitles/audio sync when captions or narration exist
- voice provenance: final narration must identify local IndexTTS2, voice id
  `pluvio-indextts2-calm-v1`, and the canonical reference WAV SHA-256. If the
  manifest shows `say`, browser/generic speech, MiniMax, another cloud provider,
  or any fallback segment, the MP4 is a draft and must not be archived as the
  recommended final.
- reference alignment report when a reference video exists
- when the V5 perspective grid is active: the project uses the canonical loop
  at `1×`, the phase remains continuous across scene boundaries, and foreground
  content does not destroy the intentional center whitespace or reduce text
  readability
- publish-title handoff: queue jobs skip this entirely — candidates already
  live in the handoff file's 标题候选 section and the user picks manually at
  publish time; do not create `视频标题.md`. Only for non-queue jobs, use
  `ra-video-title` to produce 8-12 candidates after QC, return them for user
  selection, then create or update `视频标题.md` next to the final MP4. Do not
  silently overwrite an existing title unless the user has selected the
  replacement.

Contact sheets and QC frames are required for review. Keep full QC in the
engineering project and copy the key frames into the unified archive at
`已制作/<月上旬|月下旬>/<日期-主题>/质检/` for every production route.

## Output

Return the recommended final MP4 path, the key QC artifact path, confirmed
specs, and any limitation that remains. For 待制作 queue jobs, also return the
updated handoff file path under `已制作/` with the checker result. Keep the
response concise.
