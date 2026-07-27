# rnskill

[中文](README.md)

AI Agent Skills by 雪踏乌云 for Codex, Claude Code, and other `SKILL.md`-compatible agents.

Currently **54 skills** in two categories:

### 🎬 Content Creation (Video / Image / Article)

With this skill set + Codex + HyperFrames + HeyGen + IndexTTS2, I spent less than 10 hours total over the past month — grew 2k followers on Douyin and landed my first paid brand deal. Covers topic selection, scriptwriting, AI voice cloning, digital avatars, video editing, subtitles, cover design, article-to-image, production orchestration, motion graphics, and business diagnostics.

### 💻 Coding & Development

General-purpose coding skills, more coming soon.

## RN Cover Skill

`rn-cover-skill` creates `5:2` editorial diagram covers from a title and theme—no reference image required. ImageGen invents a new right-side concept for every cover, while the compositor controls exact typography, the warm-white canvas, and editable SVG output. The result keeps a recognizable visual family without repeating one reference layout.

![RN Cover Skill example](docs/assets/rn-cover-skill-example.png)

- Exact `#FAF9F5` warm-white canvas with Chinese and mixed-language headline priority
- Vertically centered left text block; the right visual yields to headline length
- A thumbnail-visible fine grid anchors the right field; its start, spacing, strength, and artwork position remain adjustable
- Fresh isolated artwork per cover, delivered as self-contained SVG and PNG

Example:

```text
Use $rn-cover-skill to create a 5:2 cover titled "Open-source Claude-style Cover Skill"
```

## Requirements

- Codex, Claude Code, or another Agent that supports project-level skills
- A target project that can load `.agents/skills/<skill-name>/SKILL.md`

## Installation

### Claude Code Plugin Marketplace

```bash
claude plugin marketplace add Pluviobyte/rnskill
claude plugin install ra-人话@rnskill
```

### Universal (Codex / Claude Code)

```bash
npx -y skills add Pluviobyte/rnskill -g --all
```

Or install a single skill:

```bash
npx -y skills add Pluviobyte/rnskill --skill ra-人话
```

### Manual Install

```bash
# Codex
mkdir -p <project>/.agents/skills
cp -R skills/ra-人话 <project>/.agents/skills/ra-人话

# Claude Code
mkdir -p <project>/.claude/skills
cp -R skills/ra-人话 <project>/.claude/skills/ra-人话
```

## All Skills

Skills marked `⬡` are from or adapted from external open-source projects — see the Source column and [Credits](#credits-and-adaptations) below.

### Topic & Planning

| Skill | Description | Source |
|-------|-------------|--------|
| [`ra-选题`](skills/ra-选题/) | Full topic lifecycle: create cards, deepen research, recommend (benchmark + own data), route to video/article/image workbench | Original |
| [`ra-实操策划`](skills/ra-实操策划/) | Practical long-form planning: test prompts, timeline structure, on-camera script, screen-recording checklist | Original |
| [`ra-hook`](skills/ra-hook/) | Short video hook selection: 7 types × 3 categories, with prerequisites, templates, and common mistakes | Original |
| [`ra-video-title`](skills/ra-video-title/) | Video title generation: lock theme → analyze benchmarks → 8-12 two-part candidates + Top 3 picks | Original |

### Content Writing

| Skill | Description | Source |
|-------|-------------|--------|
| [`ra-video-wash-pipeline`](skills/ra-video-wash-pipeline/) | Video script-wash orchestrator: download → transcript → rewrite → QC → queue for production | Original |
| [`ra-逐字稿提取skill`](skills/ra-逐字稿提取skill/) | Extract verbatim transcript from Douyin/Xiaohongshu videos via watermark removal + Paraformer ASR | Original |
| [`ra-洗稿`](skills/ra-洗稿/) | Script rewrite: chains ra-人话 → dbs-ai-check → dbs-hook → dbs-resonate → ra-video-title | Original |
| [`ra-人话`](skills/ra-人话/) | Chinese de-AI writing: bans binary contrast shells, fake insight markers, lecture colons; preserves author judgment | Original |
| [`ra-公众号提取`](skills/ra-公众号提取/) | WeChat article full-text extraction via MicroMessenger UA spoofing, stdlib only | Original |

### Video Download

| Skill | Description | Source |
|-------|-------------|--------|
| [`ra-video-download`](skills/ra-video-download/) | Download from Douyin/YouTube/Bilibili/Twitter/Xiaohongshu via yt-dlp + TikHub | Original |

### Voice

| Skill | Description | Source |
|-------|-------------|--------|
| [`tts-skill`](skills/tts-skill/) | Local IndexTTS2 voice cloning with locked lossless reference, no cloud fallback, voice_manifest.json audit trail | Original |

### Digital Avatar

| Skill | Description | Source |
|-------|-------------|--------|
| [`heygen-digital-avatar`](skills/heygen-digital-avatar/) | HeyGen Digital Twin generation & compositing: CLI OAuth, circle crop layout, audio approval gate | Original |

### Video Editing

| Skill | Description | Source |
|-------|-------------|--------|
| [`ra-local-talking-head-cut`](skills/ra-local-talking-head-cut/) | Local talking-head rough cut: ASR → pre-cut review → user approval → semantic edit → loudness/cut QC | Original |
| [`video-use`](skills/video-use/) | Conversational video editing: transcribe, cut, color grade, overlay animations, burn subtitles | ⬡ [Browser Use](https://cloud.browser-use.com) · MIT |
| [`ai-jian-koubo`](skills/ai-jian-koubo/) | Talking-head transcription + AI stutter detection + waveform review UI + FCPXML export | ⬡ Inspired by [chengfeng/videocut-skills](https://github.com/Agentchengfeng/chengfeng-videocut-skills), rewritten · AGPL-3.0 |
| [`chengfeng-videocut-skills`](skills/chengfeng-videocut-skills/) | Chengfeng's original talking-head cutter: transcription → stutter detection → review page → FCPXML | ⬡ [chengfeng / AI产品自由](https://github.com/Agentchengfeng/chengfeng-videocut-skills) · Apache-2.0 |

### Subtitles

| Skill | Description | Source |
|-------|-------------|--------|
| [`ra-audio-to-subtitles`](skills/ra-audio-to-subtitles/) | Volcengine Doubao-ASR word-level timestamps + alignment/fragment/connector/reading-speed QC | Original |
| [`skill-captions`](skills/skill-captions/) | Subtitle styling & burn-in: anchor-dark / anchor-light styles, 4K native rendering, render QC | Original |

### Visual & Cover

| Skill | Description | Source |
|-------|-------------|--------|
| [`ian-xiaohei-illustrations`](skills/ian-xiaohei-illustrations/) | Ian's original Xiaohei article illustrations: white hand-drawn 16:9 visuals with restrained red/orange/blue annotations for judgments, processes, and metaphors | ⬡ Original author [Ian / helloianneo](https://github.com/helloianneo/ian-xiaohei-illustrations) · MIT |
| [`skill-cover`](skills/skill-cover/) | Cover generation with registered styles and dual-ratio assets | Original |
| [`editorial-dot-cover`](skills/editorial-dot-cover/) | Editorial dot-grid cover: warm gray paper + oversized Chinese title + whitespace + dotted vector icon → SVG + PNG | Original |
| [`editorial-collage-motion`](skills/editorial-collage-motion/) | Halftone paper collage motion: decode reference → generate stills → assemble-from-empty animation | ⬡ Inspired by [Vikash Kumar / Arcads Collage Motion](https://buldrr.com/arcads-collage-motion-skill/), local free edition |

### Article to Image

| Skill | Description | Source |
|-------|-------------|--------|
| [`xhs-article-to-images`](skills/xhs-article-to-images/) | Markdown article → Xiaohongshu 3:4 image cards, 5 design skins + 3 feminine themes | Original |

### Production & QC

| Skill | Description | Source |
|-------|-------------|--------|
| [`ra-video-production-director`](skills/ra-video-production-director/) | Production director: reads handoff contract → dispatches downstream skills → manages state/archive/QC | Original |
| [`ra-复盘`](skills/ra-复盘/) | Content review: collect data → viral grading (R/M) → attribution → asset archiving → topic card writeback | Original |

### Motion Graphics (HyperFrames)

| Skill | Description | Source |
|-------|-------------|--------|
| [`rn-motion-director`](skills/rn-motion-director/) | Motion-first AI video director: topic → motion concept, visual metaphors, beat graph, anti-PPT QC | Original |
| [`rn-motion-replica`](skills/rn-motion-replica/) | Reference motion study: builds original editable HyperFrames project from authorized reference + QC | Original |
| [`rn-dark-saas-video`](skills/rn-dark-saas-video/) | Dark cinematic SaaS product video: 8 scene blueprints, 3 timing presets | Original |
| [`rn-bw-text-opener`](skills/rn-bw-text-opener/) | Black-white typed text opener with synced SFX, 3 timing presets, Python timing planner | Original |
| [`rn-replica-qc`](skills/rn-replica-qc/) | Replica QA: 5 fidelity levels + asset/runtime/delivery full-frame gates | Original |
| [`rn-cover-skill`](skills/rn-cover-skill/) | Reference-free editorial diagram covers with adaptive left text, fresh right-side artwork, editable SVG + PNG | Original |

### dbs Business Toolkit (22 skills)

From [@dontbesilent](https://x.com/dontbesilent)'s open-source [dbskill](https://github.com/dontbesilent2025/dbskill), CC BY-NC 4.0. Used as automated quality gates in the video production pipeline; also available standalone.

| Skill | Description |
|-------|-------------|
| [`dbs`](skills/dbs/) | Main router: pre-task routing + post-task navigation |
| [`dbs-hook`](skills/dbs-hook/) | Hook diagnosis: pairs with ra-hook (ra-hook picks type, dbs-hook polishes execution) |
| [`dbs-resonate`](skills/dbs-resonate/) | Draft resonance diagnosis via communication psychology framework |
| [`dbs-ai-check`](skills/dbs-ai-check/) | AI writing fingerprint detection |
| [`dbs-content`](skills/dbs-content/) | Content creation diagnosis |
| [`dbs-spread`](skills/dbs-spread/) | Transmission psychology decoder: 5 communication theories |
| [`dbs-diagnosis`](skills/dbs-diagnosis/) | Business model diagnosis: consultation + checkup modes |
| [`dbs-benchmark`](skills/dbs-benchmark/) | Benchmark analysis: five-filter method |
| [`dbs-goal`](skills/dbs-goal/) | Goal clarification via Wittgenstein's philosophy of language |
| [`dbs-deconstruct`](skills/dbs-deconstruct/) | Concept deconstruction to atomic level |
| [`dbs-action`](skills/dbs-action/) | Execution block diagnosis via Adlerian psychology |
| [`dbs-slowisfast`](skills/dbs-slowisfast/) | Slow-is-fast diagnosis: find seemingly slower methods that build lasting assets |
| [`dbs-good-question`](skills/dbs-good-question/) | Fuzzy problems → agent-solvable problem briefs |
| [`dbs-learning`](skills/dbs-learning/) | Interactive learning with feedback-driven depth/pace adjustment |
| [`dbs-chatroom`](skills/dbs-chatroom/) | Topic-based expert chatroom with multi-role dialogue |
| [`dbs-chatroom-austrian`](skills/dbs-chatroom-austrian/) | Austrian economics chatroom: Hayek × Mises × Claude |
| [`dbs-content-system`](skills/dbs-content-system/) | Content structuring system: turn archives into reusable assets |
| [`dbs-decision`](skills/dbs-decision/) | Personal decision system: local knowledge project for long-running domains |
| [`dbs-xhs-title`](skills/dbs-xhs-title/) | Xiaohongshu article titles: 75 proven viral formulas |
| [`dbs-save`](skills/dbs-save/) | Save diagnosis state to disk |
| [`dbs-restore`](skills/dbs-restore/) | Restore last saved diagnosis state |
| [`dbs-report`](skills/dbs-report/) | Package multiple diagnoses into a deliverable Markdown report |
| [`dbs-agent-migration`](skills/dbs-agent-migration/) | Agent workspace migration: Claude Code / Codex / Grok three-host consistency |

## Credits and Adaptations

### dbs Business Toolkit

`dbs` and all `dbs-*` skills are from [@dontbesilent](https://x.com/dontbesilent)'s open-source [dbskill](https://github.com/dontbesilent2025/dbskill), CC BY-NC 4.0. Adapted for use as content quality gates in the video production pipeline.

### Ian's Original Xiaohei Illustrations

`ian-xiaohei-illustrations` directly includes the original [Ian Xiaohei Illustrations](https://github.com/helloianneo/ian-xiaohei-illustrations) by **Ian**. The Xiaohei character IP is unmodified and redistributed under the MIT license. Original author: [GitHub @helloianneo](https://github.com/helloianneo) · [X @ianneo_ai](https://x.com/ianneo_ai) · [www.ianneo.xyz](https://www.ianneo.xyz/opc).

### Halftone Collage Motion

`editorial-collage-motion` is inspired by Vikash Kumar's [Arcads Collage Motion Skill](https://buldrr.com/arcads-collage-motion-skill/). Original requires Arcads MCP + Nano Banana + Seedance; this edition uses Codex built-in image generation + local FFmpeg/HyperFrames rendering.

### Chengfeng Videocut

`chengfeng-videocut-skills` is from chengfeng / AI产品自由's [chengfeng-videocut-skills](https://github.com/Agentchengfeng/chengfeng-videocut-skills), Apache-2.0.

### AI Jian Koubo

`ai-jian-koubo` was inspired by chengfeng's videocut-skills, then rewritten with expanded FCPXML export, frontend interaction, video preview, editing logic, and ASR support. AGPL-3.0.

### Video Use

`video-use` is from [Browser Use](https://cloud.browser-use.com)'s video-use project, MIT license. Content-system variant with Volcengine Doubao ASR word timestamps.

## License

CC BY-NC 4.0 unless otherwise noted. See [LICENSE](LICENSE). Third-party components retain their upstream licenses.

## Author

雪踏乌云 · [@Pluvio9yte](https://x.com/Pluvio9yte)
